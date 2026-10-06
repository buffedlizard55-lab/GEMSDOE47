"""Optimal emission: turn a belief field q(x) into a submission raster.

The metric's own first-order condition (see metric.marginal_gain) says that
adding a unit of prediction mass at x is profitable iff

    dT(x) * (1/DTI - alpha)  >  alpha * dF(x)                                  (*)

with, under a belief field q,

    E[dT(x)] = sum_{|delta|<3px} q(x+delta) * max(0, k(delta) - C(x+delta))
    E[dF(x)] = 1 - kappa_q(x),   kappa_q(x) = E[max_g k(d(x,g))] ~ sum_delta q(x+delta) k(delta)

``C`` is the credit already delivered to each truth pixel by previously placed
dots, so overlapping dots are never double-counted.  Greedy on the exact
marginal gain is the standard (1-1/e) approximation to the maximum-coverage
objective that T *is*.

Two hard rules, learned from a documented 10x failure in GEMSDOE32 (its shipped
`smoothmaxcov` file put 57.8% of its dots off the belief field it claimed to
pack and collapsed the catalogue-proxy DTI from 0.162 to 0.016):

  R1  support confinement - a dot may only be placed where the belief field
      nominates a fault (q above the support threshold);
  R2  live coverage deduction - the marginal gain must be recomputed against the
      credit already delivered, never against a static upper bound.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import metric as M


def credit_field(dots: np.ndarray) -> np.ndarray:
    """w(x) = max_{y in dots} k(d(x,y)): credit a truth pixel at x would receive."""
    return M.max_kernel_filter(dots.astype(np.float64))


def delivered_credit(dots: np.ndarray) -> np.ndarray:
    """C(x) = w(x) for the dots placed so far - the credit already delivered to x."""
    return credit_field(dots)


def expected_new_credit(q: np.ndarray, dots: np.ndarray) -> np.ndarray:
    """E[dT(x)] for adding one unit dot at x, given the dots already placed.

    A truth pixel at x+delta currently receives C(x+delta); the new dot would
    offer k(delta), so the *increment* is max(0, k(delta) - C(x+delta)).
    """
    C = delivered_credit(dots)
    gain = np.zeros(q.shape, np.float64)
    for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        inc = np.maximum(0.0, k - _shift(C, dy, dx))
        gain += _shift(q * inc, -dy, -dx)
    return gain


def expected_new_fp(q: np.ndarray) -> np.ndarray:
    """E[dF(x)] = 1 - E[max_g k(d(x,g))], exact for independent Bernoulli q.

    See ``expected_kappa_dense``: the first-order version (1 - <q, kernel>) is an
    upper bound on E[kappa], not an estimate, and it drove FP_w negative on
    concentrated belief fields.
    """
    return np.maximum(0.0, 1.0 - expected_kappa_dense(q))


def _shift(a: np.ndarray, dy: int, dx: int, fill: float = 0.0) -> np.ndarray:
    """out[y, x] = a[y + dy, x + dx]; positions outside the grid take ``fill``."""
    out = np.full(a.shape, fill, dtype=a.dtype)
    H, W = a.shape
    y0, y1 = max(0, -dy), min(H, H - dy)
    x0, x1 = max(0, -dx), min(W, W - dx)
    if y0 >= y1 or x0 >= x1:
        return out
    out[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
    return out


@dataclass
class EmissionResult:
    dots: np.ndarray          # bool, full grid
    n_dots: int
    dti_trace: list[float]
    stopped_by: str
    budget: int


def emit_greedy(q: np.ndarray, allowed: np.ndarray, budget: int,
                dti_start: float = 0.0, alpha: float = M.ALPHA,
                batch: int = 2000, max_dti: float = 0.95,
                patience: int = 2, verbose: bool = False) -> EmissionResult:
    """Greedy emission under the exact marginal rule (*), in ranked batches.

    Starting from DTI = 0 is the correct initialisation: with no dots the rule
    accepts everything (1/DTI -> inf), and as the emission improves the bar
    alpha*DTI rises until the rule starts refusing.  The DTI actually achieved by
    the current dot set is recomputed exactly after every batch, and the
    best-scoring prefix is returned, so the budget is chosen by the metric
    itself rather than by hand.

    ``allowed`` is the support mask (rule R1: never emit off the belief field).
    """
    H, W = q.shape
    dots = np.zeros((H, W), bool)
    K = float(q.sum())
    dF = expected_new_fp(q)          # exact Bernoulli E[kappa]; independent of dots
    inv_dti = 1e12 if dti_start <= 0 else 1.0 / dti_start
    trace: list[float] = [0.0]
    best_dti, best_dots, n_best = 0.0, dots.copy(), 0
    bad = 0
    n = 0
    stopped = "budget"
    while n < budget:
        dT = expected_new_credit(q, dots)
        gain = dT * (inv_dti - alpha) - alpha * dF
        gain = np.where(allowed & ~dots, gain, -np.inf)
        take = min(batch, budget - n)
        flat = np.argpartition(-gain.ravel(), take - 1)[:take]
        gsel = gain.ravel()[flat]
        keep = gsel > 0
        if not keep.any():
            stopped = "marginal_rule_exhausted"
            break
        flat = flat[keep]
        dots.ravel()[flat] = True
        n += int(keep.sum())
        T = float((credit_field(dots) * q).sum())
        S = float(dots.sum())
        Phi = expected_phi(q, dots)
        F = S - Phi
        if F < -1e-9:
            raise AssertionError(f"FP_w negative ({F}); exact kappa must keep Phi <= S")
        new = M.dti_from_TFK(T, F, K)
        if verbose:
            print(f"   n={n:>7} T={T:9.1f} F={F:10.1f} Phi={Phi:9.1f} DTI={new:.4f}", flush=True)
        trace.append(new)
        if new > best_dti:
            best_dti, best_dots, n_best, bad = new, dots.copy(), n, 0
        else:
            bad += 1
            if bad >= patience:
                stopped = f"dti_argmax_reached_at_n={n_best}"
                break
        inv_dti = 1.0 / min(max(new, 1e-9), max_dti)
    return EmissionResult(dots=best_dots, n_dots=int(best_dots.sum()), dti_trace=trace,
                          stopped_by=stopped, budget=budget)


def emit_topk(q: np.ndarray, allowed: np.ndarray, k: int) -> np.ndarray:
    """Simple rank emission: the top-k belief pixels inside ``allowed``."""
    v = np.where(allowed, q, -np.inf)
    flat = np.argpartition(-v.ravel(), k - 1)[:k]
    out = np.zeros(q.size, bool)
    out[flat] = True
    return out.reshape(q.shape)


def emit_poisson_thin(field: np.ndarray, min_dist_px: float, rank_order: bool = True,
                      seed: int = 0) -> np.ndarray:
    """Poisson-disc thinning of a binary field, in geology-ranked or raster order.

    Reproduces the *family* of the owner-reported d2.8 reference (a raster-order
    thin at d = 2.8 px) so emission rules can be compared at matched budget. It
    is not the established spatially blocked holdout best.
    """
    ys, xs = np.nonzero(field > 0)
    if ys.size == 0:
        return np.zeros(field.shape, bool)
    if rank_order:
        order = np.argsort(-field[ys, xs], kind="stable")
    else:
        order = np.arange(ys.size)  # raster order (np.nonzero is row-major)
    keep = np.zeros(field.shape, bool)
    taken = np.zeros(field.shape, bool)
    r = int(np.ceil(min_dist_px))
    for i in order:
        y, x = ys[i], xs[i]
        if taken[y, x]:
            continue
        keep[y, x] = True
        y0, y1 = max(0, y - r), min(field.shape[0], y + r + 1)
        x0, x1 = max(0, x - r), min(field.shape[1], x + r + 1)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        taken[y0:y1, x0:x1] |= ((yy - y) ** 2 + (xx - x) ** 2) <= min_dist_px ** 2
    return keep


# ---------------------------------------------------------------------------
# exact Bernoulli expectation of kappa  (fixes an over-estimate bug)
# ---------------------------------------------------------------------------
#
# BUG FOUND AND FIXED (pass 2 review).  The first-order approximation
#     Phi = sum_{x in dots} kappa(x)  ~  sum_x q(x) * a(x),  a = kernel-SUM filter
# is only valid while c(x) = sum_y q(y) k(d(x,y)) << 1.  It is an upper bound on
# the truth, not an estimate: kappa(x) = max_g k(d(x,g)) <= 1 for every x, so
# Phi <= S always, whereas <q, a> is unbounded.  When the belief field is
# *concentrated* (exactly what the LATI fit produces) and the emission is dense,
# <q, a> exceeds S and the reported FP_w goes NEGATIVE, which in turn makes the
# predicted DTI exceed 1 - mathematically impossible for the real metric.  The
# first run of scripts/build_candidate.py did exactly that (F = -47,502,
# DTI = 1.6459).  Everything below is the exact expectation instead.

_RINGS: list[tuple[float, list[tuple[int, int]]]] | None = None


def kernel_rings() -> list[tuple[float, list[tuple[int, int]]]]:
    """The 25 kernel offsets grouped by kernel value, in descending order."""
    global _RINGS
    if _RINGS is None:
        d: dict[float, list[tuple[int, int]]] = {}
        for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
            d.setdefault(round(float(k), 12), []).append((int(dy), int(dx)))
        _RINGS = sorted(d.items(), key=lambda kv: -kv[0])
    return _RINGS


def expected_kappa_dense(q: np.ndarray) -> np.ndarray:
    """E_q[max_g k(d(x,g))] at every pixel, exactly, for independent Bernoulli q.

    With rings ordered by descending kernel value k_1 > ... > k_6 and
    Q_m(x) = prod_{rings 1..m} prod_{delta in ring} (1 - q(x+delta))
    = P(no hidden truth pixel within ring m of x), Q_0 = 1:

        E[max] = sum_{j=1..6} k_j (Q_{j-1} - Q_j)
               = 1 - sum_{m=1..6} (k_m - k_{m+1}) Q_m,     k_7 := 0            (STABLE)

    The second form is used because the first subtracts nearly equal products:
    at q ~ 2e-3 it lost ~2e-4 per pixel to float64 cancellation, which summed
    over 1.5e5 dots and drove the reported FP_w to -28.2 (impossible, since
    kappa <= 1 forces Phi <= S).  The stable form only ever *subtracts
    non-negative terms from 1*, so E[kappa] is in [0, 1] by construction.
    """
    q = np.asarray(q, np.float64)
    one_minus = 1.0 - q
    rings = kernel_rings()
    ks = [r[0] for r in rings] + [0.0]
    Q = np.ones_like(q)
    acc = np.ones_like(q)
    for m, (kj, offs) in enumerate(rings):
        P = np.ones_like(q)
        for dy, dx in offs:
            # fill = 1.0, i.e. q = 0 outside the grid: an out-of-bounds pixel
            # cannot be hidden truth.  Filling with 0.0 would mean q = 1 there
            # and inflates E[kappa] along every border (found in pass 2 review).
            P *= _shift(one_minus, dy, dx, fill=1.0)
        Q = Q * P
        acc -= (kj - ks[m + 1]) * Q
    return np.clip(acc, 0.0, 1.0)


def expected_phi(q: np.ndarray, dots: np.ndarray) -> float:
    """Phi = sum_{x in dots} E_q[kappa(x)], sparse over the dot positions.

    Uses the numerically stable form documented on ``expected_kappa_dense``; each
    per-dot term is in [0, 1], so Phi <= S is guaranteed and FP_w = S - Phi >= 0.
    """
    ys, xs = np.nonzero(dots)
    if ys.size == 0:
        return 0.0
    H, W = q.shape
    one_minus = 1.0 - q
    rings = kernel_rings()
    ks = [r[0] for r in rings] + [0.0]
    Q = np.ones(ys.size)
    acc = np.ones(ys.size)
    for m, (kj, offs) in enumerate(rings):
        P = np.ones(ys.size)
        for dy, dx in offs:
            yy = ys + dy
            xx = xs + dx
            ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
            v = np.ones(ys.size)
            v[ok] = one_minus[yy[ok], xx[ok]]
            P *= v
        Q = Q * P
        acc -= (kj - ks[m + 1]) * Q
    return float(np.clip(acc, 0.0, 1.0).sum())


def predicted_score(q: np.ndarray, dots: np.ndarray) -> dict:
    """Exact-under-q prediction of (T, F, K, DTI) for a candidate dot set."""
    T = float((credit_field(dots.astype(np.float64)) * q).sum())
    Phi = expected_phi(q, dots)
    S = float(dots.sum())
    F = S - Phi
    K = float(q.sum())
    return dict(T=T, Phi=Phi, S=S, F=F, K=K, DTI=M.dti_from_TFK(T, F, K),
                weighted_recall=T / K if K else 0.0,
                credit_per_dot=T / S if S else 0.0,
                fp_fraction=F / S if S else 0.0)
