"""Exact implementation of the competition's distance-weighted Tversky index (DTI).

Official definition, quoted from the problem description
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/,
section "Performance metric"):

    k(d)  = max(1 - d/R, 0),                       R = 300 m  (3 px at 100 m)
    TP_w  = sum_{g in G}      max_{x: d(x,g)<=R} p(x) k(d(x,g))
    FP_w  = sum_{x: p(x)>0}   p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w  = sum_{g in G}      [1 - max_{x: d(x,g)<=R} p(x) k(d(x,g))]
    DTI   = TP_w / (TP_w + alpha*FP_w + beta*FN_w + eps),   alpha=0.2, beta=0.8

Two exact algebraic reductions are used by the fast path.  Both are proven in
``tests/test_metric.py`` against a literal O(N^2) transcription of the four
formulas above (``dti_bruteforce``), and against the organisers' own worked
example (TP_w = 3.00, FP_w = 1.89, FN_w = 2.00 -> 0.60):

  (R1) FN_w = |G| - TP_w                      (the two sums are term-wise complements)
  (R2) FP_w = S - Phi,  S = sum_x p(x),  Phi = sum_x p(x) * kappa(x),
       kappa(x) = max_{g in G} k(d(x,g))      (k is decreasing, so the max over g
                                               is the kernel at the *nearest* truth pixel)

  =>  DTI = T / ( alpha*(T + S - Phi) + beta*|G| )                          (DESIGN EQ.)
  =>  1/DTI = (1-beta)/beta*... ; with alpha=0.2, beta=0.8:
      1/DTI = alpha + alpha*(F/T) + beta*(K/T)

Masking (DrivenData staff, community thread 11516, chrisk-dd, 2026-09-16):
"Pixels corresponding to known USGS/INGENIOUS faults are masked / excluded from
evaluation, so they do not count towards penalty terms."  ``evaluated`` therefore
excludes catalogue pixels from the FP sum.  ``G`` (the hidden new-fault set) is
disjoint from the catalogue by definition (thread 11536, chrisk-dd, 2026-09-23:
"'new fault' means 'any fault pixel not already captured by USGS/INGENIOUS'").
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ALPHA = 0.2
BETA = 0.8
RANGE_M = 300.0
RANGE_PX = 3.0
EPS = 0.0  # the published example reproduces exactly with eps = 0

# ---------------------------------------------------------------------------
# kernel
# ---------------------------------------------------------------------------


def _offsets() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """All integer pixel offsets with k(d) > 0, plus their kernel values."""
    dy, dx, kv = [], [], []
    r = int(np.floor(RANGE_PX))
    for iy in range(-r, r + 1):
        for ix in range(-r, r + 1):
            d = float(np.hypot(iy, ix))
            k = max(1.0 - d / RANGE_PX, 0.0)
            if k > 0.0:
                dy.append(iy)
                dx.append(ix)
                kv.append(k)
    return np.array(dy), np.array(dx), np.array(kv, dtype=np.float64)


OFF_DY, OFF_DX, OFF_K = _offsets()
N_OFFSETS = len(OFF_K)
KERNEL_SUM = float(OFF_K.sum())  # 9.3802978105 - max credit one dot can deliver
# Distinct kernel levels, descending.  Used by the Bernoulli expectation in lati.py.
LEVELS: tuple[float, ...] = tuple(sorted({round(float(v), 12) for v in OFF_K}, reverse=True))


def kernel_value(d_px: float) -> float:
    """k(d) for a distance in pixels (1 px = 100 m)."""
    return max(1.0 - d_px / RANGE_PX, 0.0)


def _shift(a: np.ndarray, dy: int, dx: int, fill: float = 0.0) -> np.ndarray:
    """a shifted so that out[y, x] = a[y + dy, x + dx]; out-of-range -> fill."""
    out = np.full(a.shape, fill, dtype=a.dtype)
    H, W = a.shape
    ys0, ys1 = max(0, -dy), min(H, H - dy)
    xs0, xs1 = max(0, -dx), min(W, W - dx)
    if ys0 >= ys1 or xs0 >= xs1:
        return out
    out[ys0:ys1, xs0:xs1] = a[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def max_kernel_filter(field: np.ndarray) -> np.ndarray:
    """M(x) = max_{delta: k>0} k(delta) * field(x + delta).

    With a binary ``field`` this is ``kappa(x) = max_{g in G} k(d(x,g))``.
    With a binary ``field`` of dots this is ``w(x) = max_{y in dots} k(d(x,y))``,
    i.e. the credit a truth pixel at x would receive.
    """
    a = np.asarray(field, dtype=np.float64)
    out = np.zeros(a.shape, dtype=np.float64)
    for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):
        np.maximum(out, k * _shift(a, dy, dx), out=out)
    return out


# ---------------------------------------------------------------------------
# brute-force reference (literal transcription, slow, for tests only)
# ---------------------------------------------------------------------------


def dti_bruteforce(pred: np.ndarray, truth: np.ndarray, evaluated: np.ndarray | None = None,
                   alpha: float = ALPHA, beta: float = BETA) -> dict:
    """O(N^2) literal transcription of the four published formulas."""
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth, dtype=np.float64) > 0
    H, W = p.shape
    ev = np.ones(p.shape, bool) if evaluated is None else np.asarray(evaluated, bool)
    g = g & ev                     # same masking convention as score()
    p = np.where(ev, p, 0.0)       # mask_mode="zero"
    gy, gx = np.nonzero(g)

    # nearest-kernel value from every pixel to the truth set
    kappa = np.zeros(p.shape)
    # credit available to every truth pixel from the prediction
    w = np.zeros(p.shape)
    py, px = np.nonzero(p > 0)
    if len(gy) and len(py):
        # pairwise over offsets only (exact, because k(d)=0 beyond 3 px)
        for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):
            for yy, xx in zip(gy, gx):
                y, x = yy - dy, xx - dx
                if 0 <= y < H and 0 <= x < W and p[y, x] > 0:
                    w[yy, xx] = max(w[yy, xx], k * p[y, x])
        for yy, xx in zip(py, px):
            best = 0.0
            for dy, dx, k in zip(OFF_DY, OFF_DX, OFF_K):
                y, x = yy + dy, xx + dx
                if 0 <= y < H and 0 <= x < W and g[y, x]:
                    best = max(best, k)
            kappa[yy, xx] = best
    tp = float(w[g].sum())
    fn = float((1.0 - w[g]).sum())
    m = p > 0
    fp = float((p[m] * (1.0 - kappa[m])).sum())
    den = tp + alpha * fp + beta * fn + EPS
    return {"TP_w": tp, "FP_w": fp, "FN_w": fn, "|G|": int(g.sum()),
            "S": float(p[m].sum()), "Phi": float((p[m] * kappa[m]).sum()),
            "DTI": (tp / den) if den > 0 else 0.0}


# ---------------------------------------------------------------------------
# fast exact path
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Score:
    T: float          # TP_w
    F: float          # FP_w
    K: int            # |G|
    S: float          # evaluated predicted mass
    Phi: float        # sum_x p(x) kappa(x)
    FN: float         # FN_w = K - T
    DTI: float

    def as_dict(self) -> dict:
        return {"TP_w": self.T, "FP_w": self.F, "FN_w": self.FN, "|G|": self.K,
                "S": self.S, "Phi": self.Phi, "DTI": self.DTI,
                "credit_per_unit_mass": (self.T / self.S) if self.S else 0.0,
                "weighted_recall": (self.T / self.K) if self.K else 0.0,
                "F_over_T": (self.F / self.T) if self.T else np.inf,
                "inv_dti": (1.0 / self.DTI) if self.DTI else np.inf}


def score(pred: np.ndarray, truth: np.ndarray, evaluated: np.ndarray | None = None,
          alpha: float = ALPHA, beta: float = BETA, mask_mode: str = "zero") -> Score:
    """Exact DTI via reductions (R1)/(R2).  Verified against ``dti_bruteforce``.

    ``mask_mode`` controls how the organiser's masking of known USGS/INGENIOUS
    fault pixels enters the arithmetic:

    ``"zero"`` (default; implementation of the official exclusion rule)
        The prediction is zeroed on masked pixels before either sum. Official
        DrivenData staff says known USGS/INGENIOUS pixels are masked/excluded from
        evaluation and do not count toward penalty terms; the local scorer models
        that exclusion by removing masked predictions from the evaluated domain.
        The owner-reported Hedge-v2 / ens12 comparison is descriptive, not a
        controlled causal ablation, and is not used to infer a gain from deleting
        masked pixels.

    ``"fp_only"``
        Retained as an explicit alternate arithmetic for regression/audit use:
        masked pixels are omitted from the FP sum but their predictions can still
        contribute to nearby truth credit. This is not the official scoring
        interpretation; do not use it for reported DTI results.
    """
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth) > 0
    ev = np.ones(p.shape, bool) if evaluated is None else np.asarray(evaluated, bool)
    g = g & ev                      # the hidden new-fault set is disjoint from the mask
    if mask_mode == "zero":
        p = np.where(ev, p, 0.0)
        m = p > 0
    elif mask_mode == "fp_only":
        m = (p > 0) & ev
    else:
        raise ValueError(f"unknown mask_mode {mask_mode!r}")
    w = max_kernel_filter(p)                     # credit available to a truth pixel
    kappa = max_kernel_filter(g.astype(np.float64))  # nearest-truth kernel for a prediction
    T = float(w[g].sum())
    K = int(g.sum())
    S = float(p[m].sum())
    Phi = float((p[m] * kappa[m]).sum())
    F = S - Phi
    den = T + alpha * F + beta * (K - T) + EPS
    return Score(T=T, F=F, K=K, S=S, Phi=Phi, FN=float(K - T),
                 DTI=(T / den) if den > 0 else 0.0)


def dti_from_TFK(T: float, F: float, K: float, alpha: float = ALPHA, beta: float = BETA) -> float:
    """The design equation: DTI = T / (alpha*(T+F) + beta*K)."""
    den = alpha * (T + F) + beta * K + EPS
    return float(T / den) if den > 0 else 0.0


def scale_identity(pred: np.ndarray, lam: float, truth: np.ndarray,
                   evaluated: np.ndarray | None = None) -> tuple[float, float]:
    """DTI(lam*p) = lam*T / (lam*alpha*(T+F) + beta*K); returns (direct, closed-form).

    Exact (both T and F are homogeneous of degree 1 in p).  Used as a test.
    """
    s1 = score(pred, truth, evaluated)
    s2 = score(lam * np.asarray(pred, float), truth, evaluated)
    closed = dti_from_TFK(lam * s1.T, lam * s1.F, s1.K)
    return s2.DTI, closed


# ---------------------------------------------------------------------------
# marginal (decision) rule
# ---------------------------------------------------------------------------


def marginal_gain(dT: float, dF: float, dti: float, alpha: float = ALPHA) -> float:
    """d(DTI) from adding a unit of prediction with credit dT and false-positive dF.

    DTI = T/Den, Den = alpha*(T+F) + beta*K  =>  dDen = alpha*(dT+dF)
    d(DTI) > 0  <=>  dT * Den > T * alpha * (dT + dF)
                 <=>  dT * (1/DTI - alpha) > alpha * dF                      (*)
    For the common case dT = k, dF = 1 - k this reduces to  k > alpha * DTI.
    """
    if dti <= 0:
        return float(dT - alpha * dF)
    return float(dT * (1.0 / dti - alpha) - alpha * dF)


def accept(dT: float, dF: float, dti: float, alpha: float = ALPHA) -> bool:
    return marginal_gain(dT, dF, dti, alpha) > 0.0


def breakeven_k(dti: float, alpha: float = ALPHA) -> float:
    """Kernel value at which a lone dot exactly pays for itself: k = alpha*DTI."""
    return alpha * dti


def required_recall(dti: float, f_over_k: float, alpha: float = ALPHA, beta: float = BETA) -> float:
    """Return ``x = T/K`` for a target DTI and ``rho = F/K``.

    Inverting ``DTI = T / (alpha*(T + F) + beta*K)`` gives
    ``x = (alpha*rho + beta) / (1/DTI - alpha)``. Here ``rho`` is
    specifically ``F/K``; it is not the distinct ratio ``F/T``. A result
    above 1 is returned unchanged and means the target is infeasible at that
    ``F/K`` if weighted recall is constrained to ``T/K <= 1``. The function
    is an algebraic scenario calculation and does not estimate an incumbent's
    actual ratios.
    """
    values = (dti, f_over_k, alpha, beta)
    if not all(np.isfinite(value) for value in values):
        raise ValueError("dti, F/K, alpha, and beta must be finite")
    if dti <= 0.0:
        raise ValueError("dti must be positive")
    if f_over_k < 0.0:
        raise ValueError("F/K must be non-negative")
    if alpha < 0.0 or beta < 0.0:
        raise ValueError("alpha and beta must be non-negative")

    denominator = 1.0 / dti - alpha
    if denominator <= 0.0:
        raise ValueError("target DTI gives a non-positive inverse-formula denominator")
    return float((alpha * f_over_k + beta) / denominator)


def worked_example() -> dict:
    """The organisers' published scoring example (page 967): must give 0.60.

    Ground truth = a single vertical line; the published component values are
    TP_w = 3.00, FP_w = 1.89, FN_w = 2.00 -> TI_w(0.2, 0.8) = 0.60.
    """
    return {"TP_w": 3.00, "FP_w": 1.89, "FN_w": 2.00,
            "DTI": dti_from_TFK(3.00, 1.89, 3.00 + 2.00),
            "published": 0.60}
