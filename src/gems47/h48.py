"""H48 - multi-scale curvature lineament consensus (MSCL), and the emission sweep.

The scientific claim being tested
---------------------------------
Every published arm of this project scored pixels *independently band by band*:
each 100 m cell was ranked by a band value (or by the magnitude of its gradient)
and high-ranking cells were painted.  Rank-per-pixel scoring is **geometry-blind**
- a compact blob, a speckle field and a 200 km curvilinear trace with the same
gradient magnitude score identically - even though the target (a fault) is by
definition a *curvilinear* structure, and the scoring kernel is a 300 m triangle.

H48 replaces "is this pixel anomalous?" with "is this pixel on a **lineament**?",
using the classical structural interpretation operators:

  * structure tensor / Hessian coherence at three apertures, which is a
    *curvature transform*: it responds to elongated (fault-like) structure and
    is suppressed on isotropic texture and point noise;
  * a **cross-domain consensus**: a cell must be a lineament in the topography
    domain *and* in the potential-field domain.  A Quaternary fault that has been
    mapped as new geometry is normally expressed in more than one physical field
    (scarp in elevation, lineament in magnetics / gravity / radiometrics), while
    a speckle artefact lives in one field only.

Why this targets faults that are missing from the USGS/INGENIOUS catalogue
-------------------------------------------------------------------------
The competition's own staff statement is that "new fault" can include *newly
mapped geometry of an existing fault system*
(https://community.drivendata.org/t/where-do-you-draw-the-line/11536).  New
geometry of an existing system is the *continuation and splay* population: it is
off-catalogue but on the same lineament trend.  A lineament operator evaluated
at a 300 m aperture is the matched filter for exactly that population, and it is
the operator family that lidar/potential-field interpreters use in practice
(USGS GeoDAWN products are magnetic/radiometric lineament interpretations:
https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7).

How it differs from everything already built here
-------------------------------------------------
``gems47.features`` produces 72 rank-per-pixel layers, including first-order
``*_grad`` magnitudes, ``lidar_scarp_composite`` and distance/band layers.  None
of them is a Hessian/structure-tensor operator, none combines bands *before*
ranking, and none requires cross-domain agreement.  H48 also differs from the
sibling repositories' ``edge_coherence`` arm (GEMSDOE28), which used a *single
band* edge-coherence field; H48 is multi-scale and multi-domain.

Honest scope
------------
The detector is *not* claimed to be validated.  Whether the hidden expert labels
follow lineaments more than they follow band ranks is exactly what the 13
leaderboard returns are used to test (see ``scripts/build_h48.py``).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from . import metric as M

# ---------------------------------------------------------------------------
# a priori configuration (declared before any score was looked at)
# ---------------------------------------------------------------------------

#: apertures in pixels (100 m cells); 1.2 px matches the 300 m scoring kernel
SIGMAS: tuple[float, ...] = (1.2, 2.5, 5.0)

#: topography domain - scarps and range-fronts live in the detrended surface
TOPO_BANDS: tuple[str, ...] = ("det_elev",)

#: potential-field domains - faults appear as magnetic / gravity lineaments
GEOPHYS_BANDS: tuple[str, ...] = ("tmi", "mag_anom", "iso_grav_anom", "rad_TC")

#: the soft-max over the potential-field bands keeps a magnetic-only structure
TOPK_GEOPHYS = 2

EPS = 1e-12


def structure_saliency(v: np.ndarray, sigma: float, mask: np.ndarray | None = None,
                       clip: float = 6.0) -> np.ndarray:
    """Sign-agnostic lineament saliency from the structure tensor at one aperture.

    ``J = G_sigma * (grad z)(grad z)^T`` is smoothed again at ``2 sigma`` so the
    tensor describes a neighbourhood, not a pixel.  With eigenvalues
    ``l1 >= l2 >= 0`` of ``J``,

        coherence c = (l1 - l2) / (l1 + l2)     in [0, 1]
        saliency  R = sqrt(l1) * c

    ``R`` is large on elongated ridges *and* valleys and small on isotropic
    texture, point noise and flat ground.  No threshold or tuning is involved.

    ``z`` is the input robustly standardised to the evaluated set (median and
    inter-quartile range) and **clipped at +-clip** before any product is formed.
    The raw GeoDAWN bands span many orders of magnitude, and forming ``gx * gx``
    in float32 overflowed to inf/NaN on the first run of this module - clipping a
    standardised field removes that failure mode by construction.  ``mask`` is
    the evaluated pixel set; cells outside it are zeroed so neither the statistics
    nor the convolution can see the float32-min nodata sentinel (IR-47-001).
    """
    x = np.asarray(v, np.float64)
    finite = np.isfinite(x)
    sel = finite if mask is None else (finite & mask)
    if not sel.any():
        return np.zeros(x.shape, np.float32)
    vals = x[sel]
    med = float(np.median(vals))
    q75, q25 = np.percentile(vals, [75.0, 25.0])
    iqr = float(q75 - q25)
    scale = iqr if iqr > 0 else (float(np.std(vals)) or 1.0)
    z = np.clip((x - med) / scale, -clip, clip)
    if mask is not None:
        z = np.where(mask, z, 0.0)
    z = np.nan_to_num(z, nan=0.0, posinf=clip, neginf=-clip).astype(np.float32)
    del x, vals
    sm = ndimage.gaussian_filter(z, sigma=float(sigma), mode="constant", cval=0.0)
    del z
    gy, gx = np.gradient(sm)
    del sm
    s2 = float(2.0 * sigma)
    jxx = ndimage.gaussian_filter(gx * gx, sigma=s2, mode="constant", cval=0.0)
    jyy = ndimage.gaussian_filter(gy * gy, sigma=s2, mode="constant", cval=0.0)
    jxy = ndimage.gaussian_filter(gx * gy, sigma=s2, mode="constant", cval=0.0)
    del gx, gy
    half = 0.5 * (jxx + jyy)
    disc = np.sqrt(np.maximum(0.25 * (jxx - jyy) ** 2 + jxy ** 2, 0.0))
    l1 = half + disc
    l2 = half - disc
    del disc, jyy, jxy
    coh = (l1 - l2) / np.maximum(l1 + l2, EPS)
    del l2
    out = np.sqrt(np.maximum(l1, 0.0), dtype=np.float32) * coh.astype(np.float32)
    del l1, coh
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)


@dataclass
class MsclResult:
    topo_u8: np.ndarray      # (n_eval,) uint8 rank of the topography-domain lineament response
    geophys_u8: np.ndarray   # (n_eval,) uint8 rank of the potential-field-domain response
    consensus_u8: np.ndarray  # (n_eval,) uint8 rank of sqrt(rank_topo * rank_geophys)
    per_band: dict


def _rank_u8_full(v: np.ndarray, ev_flat: np.ndarray) -> np.ndarray:
    """Rank percentile (0..255) of ``v`` over the evaluated pixels, ties averaged."""
    x = np.asarray(v, np.float64).ravel()[ev_flat]
    order = np.argsort(x, kind="stable")
    r = np.empty(x.size, np.float64)
    r[order] = np.arange(x.size, dtype=np.float64)
    sx = x[order]
    i = 0
    n = sx.size
    while i < n:
        j = i + 1
        while j < n and sx[j] == sx[i]:
            j += 1
        if j - i > 1:
            r[order[i:j]] = 0.5 * (i + j - 1)
        i = j
    return np.clip(np.rint(r / max(n - 1, 1) * 255.0), 0, 255).astype(np.uint8)


def multi_scale_consensus(reader, ev: np.ndarray, verbose: bool = True) -> MsclResult:
    """Build the H48 lineament-consensus feature on the evaluated pixel set.

    ``reader(name)`` returns the full-grid float32 layer for a band name.  All
    rank normalisation happens *inside* the evaluated set, so the float32-min
    nodata sentinel (-3.4028234663852886e+38, flagged as IR-47-001) can never
    pollute a rank.
    """
    ev_flat = np.flatnonzero(np.asarray(ev, bool).ravel())
    per_band: dict[str, np.ndarray] = {}

    def domain_u8(bands) -> np.ndarray:
        acc = []
        ev_bool = np.asarray(ev, bool)
        for name in bands:
            v = reader(name)
            best = None
            for s in SIGMAS:
                r = _rank_u8_full(structure_saliency(v, s, mask=ev_bool), ev_flat)
                best = r if best is None else np.maximum(best, r)
                if verbose:
                    print(f"[h48] {name:<14} sigma={s:<4} ranked", flush=True)
            per_band[name] = best
            acc.append(best)
            del v
        return acc

    topo = domain_u8(TOPO_BANDS)
    geo = domain_u8(GEOPHYS_BANDS)

    # soft-max: mean of the top-K geophysical ranks keeps single-domain lineaments
    k = min(TOPK_GEOPHYS, len(geo))
    G = np.stack(geo)
    G.sort(axis=0)
    geophys = G[-k:].mean(axis=0)
    topo_u8 = topo[0]

    t = topo_u8.astype(np.float64) / 255.0
    g = geophys / 255.0
    consensus = np.sqrt(np.maximum(t, 0.0) * np.maximum(g, 0.0))
    consensus_u8 = _rank_u8_full(consensus, np.arange(consensus.size))
    return MsclResult(topo_u8=topo_u8, geophys_u8=np.clip(np.rint(geophys), 0, 255).astype(np.uint8),
                      consensus_u8=consensus_u8, per_band=per_band)


# ---------------------------------------------------------------------------
# emission: the spacing sweep
# ---------------------------------------------------------------------------


def _shift(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    out = np.zeros(a.shape, a.dtype)
    H, W = a.shape
    y0, y1 = max(0, -dy), min(H, H - dy)
    x0, x1 = max(0, -dx), min(W, W - dx)
    if y0 < y1 and x0 < x1:
        out[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
    return out


def max_kernel(field: np.ndarray) -> np.ndarray:
    """Exact ``max_delta k(delta) * field(x + delta)`` over the 25 live offsets."""
    a = np.asarray(field, np.float64)
    out = np.zeros(a.shape, np.float64)
    for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        np.maximum(out, k * _shift(a, dy, dx), out=out)
    return out


def sum_kernel(field: np.ndarray) -> np.ndarray:
    """``sum_delta k(delta) * field(x + delta)`` - the first-order halo (``a``)."""
    a = np.asarray(field, np.float64)
    out = np.zeros(a.shape, np.float64)
    for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        out += k * _shift(a, dy, dx)
    return out


def max_positions(field: np.ndarray, radius: int, allowed: np.ndarray) -> np.ndarray:
    """Cells that are the maximum of ``field`` inside a (2r+1)^2 window and allowed.

    The reduction is written as an in-place loop rather than
    ``np.maximum.reduce([...])``: the list form materialises one full grid per
    offset (25 x 49 MB here) and was what pushed this pipeline into the
    container's OOM killer on its first full run.
    """
    m = _shift(field, -radius, -radius).copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dy == -radius and dx == -radius:
                continue
            np.maximum(m, _shift(field, dy, dx), out=m)
    return (field >= m) & allowed


def min_sep_select(pts_yx: tuple[np.ndarray, np.ndarray], key: np.ndarray,
                   spacing_px: float) -> np.ndarray:
    """Greedy subset of points with minimum pairwise separation ``spacing_px``.

    Points are visited in order of descending ``key`` (the belief), so the
    surviving set is the *strongest* set of dots at that aperture - the
    repacking rule that took the family from the 1.5 px lattice (0.2477) to the
    2.4 px lattice (0.2600) and then to the flank-pruned field (0.2778), applied
    as a decision rule instead of by hand.
    """
    ys, xs = pts_yx
    order = np.argsort(-np.asarray(key, np.float64), kind="stable")
    r = float(spacing_px)
    r2 = r * r
    cell = max(r, 1.0)
    grid: dict[tuple[int, int], list] = {}
    keep = np.zeros(ys.size, bool)
    for idx in order:
        y = int(ys[idx]); x = int(xs[idx])
        cy, cx = int(y // cell), int(x // cell)
        ok = True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for (yy, xx) in grid.get((cy + dy, cx + dx), ()):
                    if (yy - y) ** 2 + (xx - x) ** 2 < r2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            keep[idx] = True
            grid.setdefault((cy, cx), []).append((y, x))
    return keep


@dataclass
class SweepPoint:
    spacing_px: float
    n_dots: int
    dots: np.ndarray          # bool, full grid
    predicted_dti: float      # under the fitted belief q
    T: float
    F: float
    Phi: float
    S: float
    K: float
    marginal_bar: float       # alpha * DTI used by the stopping rule
    n_kept: int = 0
    n_added: int = 0


def sweep_point_from_dots(dots: np.ndarray, q: np.ndarray, spacing_px: float,
                          dti_bar: float, alpha: float = M.ALPHA,
                          n_kept: int = 0, n_added: int = 0) -> SweepPoint:
    """Exact belief-model metrics for a finished dot set."""
    qv = np.asarray(q, np.float64)
    K = float(qv.sum())
    S = float(dots.sum())
    if S == 0:
        return SweepPoint(spacing_px=spacing_px, n_dots=0, dots=dots, predicted_dti=0.0,
                          T=0.0, F=0.0, Phi=0.0, S=0.0, K=K,
                          marginal_bar=alpha * dti_bar, n_kept=n_kept, n_added=n_added)
    d = dots.astype(np.float64)
    w = max_kernel(d)
    a = sum_kernel(d)
    T = float((qv * w).sum())
    Phi = float((qv * a).sum())
    F = S - Phi
    return SweepPoint(spacing_px=spacing_px, n_dots=int(S), dots=dots,
                      predicted_dti=M.dti_from_TFK(T, F, K), T=T, F=F, Phi=Phi, S=S, K=K,
                      marginal_bar=alpha * dti_bar, n_kept=n_kept, n_added=n_added)


def emit_repack(base: np.ndarray, consensus_u8: np.ndarray, q: np.ndarray,
                allowed: np.ndarray, spacing_px: float, dti_bar: float,
                alpha: float = M.ALPHA, snap_radius: int = 2, add_frac: float = 0.15,
                add_candidates: np.ndarray | None = None, snap: bool = True,
                verbose: bool = False) -> SweepPoint:
    """Aperture repack of a measured base field, with lineament snap and additions.

    Three moves, in order; each is a decision rule with a stated reason.

    1. **Assignment (snap).**  The base field's dots are visited in descending
       belief order.  Each dot is placed on the highest-scoring free cell within
       ``snap_radius`` px, where the score is the *lineament consensus* (H48's new
       curvature signature) with the belief as tie-break.  A fault is a
       curvilinear object, so a dot on the local ridge earns more kernel credit
       than a dot 200 m off it.  Crucially the move is **one-to-one**: a cell can
       be claimed once, so the dot count is preserved instead of collapsing onto
       the field's few local maxima (the first version of this function did
       collapse, kept 2,689 of 44,090 dots and drove the model DTI from 0.196 to
       0.056 - recorded in ``evidence/h48_build.json`` history).

    2. **Aperture sweep.**  A cell is refused if a dot already sits within
       ``spacing_px``.  Neighbouring dots closer than the 300 m kernel duplicate
       credit instead of adding it: that is why the family's 1.5 px lattice
       (0.2477) lost to its 2.4 px lattice (0.2600).  ``spacing_px`` is the swept
       operating point; the belief decides which member of a cluster survives.

    3. **Add.**  ``add_frac`` of the base mass may be spent on new ground that
       (a) sits on a top-decile lineament-consensus ridge, (b) is outside the
       separation margin, and (c) passes the metric's own first-order marginal
       rule ``sum_delta q(x+delta) k(delta) > alpha * DTI``.  Nothing else is
       added, so additions cannot silently increase waste away from truth.
    """
    H, W = q.shape
    qv = np.asarray(q, np.float32)
    cons = np.asarray(consensus_u8, np.float32) * np.float32(1.0 / 255.0)
    allowed_b = np.asarray(allowed, bool)
    r = float(spacing_px)
    r2 = r * r
    cell = max(r, 1.0)
    grid: dict[tuple[int, int], list] = {}
    dots = np.zeros((H, W), bool)
    taken = np.zeros((H, W), bool)

    by, bx = np.nonzero(np.asarray(base, bool))
    order = np.argsort(-qv[by, bx], kind="stable")
    rad = int(snap_radius)
    rng_y = range(-rad, rad + 1)
    rng_x = range(-rad, rad + 1)
    for i in order:
        y0, x0 = int(by[i]), int(bx[i])
        best = None
        best_score = -np.inf
        for dy in rng_y:
            y = y0 + dy
            if y < 0 or y >= H:
                continue
            for dx in rng_x:
                x = x0 + dx
                if x < 0 or x >= W or taken[y, x]:
                    continue
                if snap and not allowed_b[y, x] and not (dy == 0 and dx == 0):
                    continue
                cy, cx = int(y // cell), int(x // cell)
                ok = True
                for gy in (cy - 1, cy, cy + 1):
                    for gx in (cx - 1, cx, cx + 1):
                        for (yy, xx) in grid.get((gy, gx), ()):
                            if (yy - y) ** 2 + (xx - x) ** 2 < r2:
                                ok = False
                                break
                        if not ok:
                            break
                    if not ok:
                        break
                if not ok:
                    continue
                s = float(cons[y, x]) + 1e-6 * float(qv[y, x])
                if s > best_score:
                    best_score = s
                    best = (y, x)
        if best is None:
            continue
        y, x = best
        dots[y, x] = True
        taken[y, x] = True
        grid.setdefault((int(y // cell), int(x // cell)), []).append((y, x))
    n_kept = int(dots.sum())

    kept_dots = dots.copy()
    n_add = 0
    if add_frac > 0 and add_candidates is not None:
        cap = round(add_frac * float(np.asarray(base, bool).sum()))
        cand = np.asarray(add_candidates, bool) & allowed_b & ~taken
        if cap > 0 and cand.any():
            halo = np.where(allowed_b, qv, np.float32(0.0))
            a = sum_kernel(halo)
            del halo
            bar = alpha * max(dti_bar, 0.0)
            cy, cx = np.nonzero(cand)
            gain0 = a[cy, cx] - bar
            ok = gain0 > 0.0
            cy, cx, gain0 = cy[ok], cx[ok], gain0[ok]
            sel_y = sel_x = np.zeros(0, np.int64)
            if cy.size:
                free = min_sep_select((cy, cx), gain0, r)
                cy, cx, gain0 = cy[free], cx[free], gain0[free]
                ig = dict(grid)
                keep_y, keep_x = [], []
                for y, x in zip(cy, cx):
                    g = int(y // cell), int(x // cell)
                    ok2 = True
                    for gy in (g[0] - 1, g[0], g[0] + 1):
                        for gx in (g[1] - 1, g[1], g[1] + 1):
                            for (yy, xx) in ig.get((gy, gx), ()):
                                if (yy - y) ** 2 + (xx - x) ** 2 < r2:
                                    ok2 = False
                                    break
                            if not ok2:
                                break
                        if not ok2:
                            break
                    if ok2:
                        ig.setdefault(g, []).append((y, x))
                        keep_y.append(y)
                        keep_x.append(x)
                        if len(keep_y) >= cap:
                            break
                sel_y = np.asarray(keep_y, np.int64)
                sel_x = np.asarray(keep_x, np.int64)
            if sel_y.size:
                dots[sel_y, sel_x] = True
                n_add = int(sel_y.size)
                if verbose:
                    print(f"[h48]   added {n_add} new-ground dots (cap {cap})", flush=True)
    sp_all = sweep_point_from_dots(dots, q, spacing_px, dti_bar, alpha,
                                   n_kept=n_kept, n_added=n_add)
    if n_add:
        # The first-order halo is an UPPER bound on E[kappa] (Trap A of the
        # project's metric notes), so a first-order test can accept dots the
        # exact objective rejects.  Keep the additions only if the exact model
        # DTI improves - the additions must pay for themselves, measured.
        sp_kept = sweep_point_from_dots(kept_dots, q, spacing_px, dti_bar, alpha,
                                        n_kept=n_kept, n_added=0)
        if sp_kept.predicted_dti >= sp_all.predicted_dti:
            if verbose:
                print(f"[h48]   additions rejected by the exact objective "
                      f"({sp_all.predicted_dti:.4f} < {sp_kept.predicted_dti:.4f})", flush=True)
            return sp_kept
    return sp_all


def run_snap_sweep(base: np.ndarray, consensus_u8: np.ndarray, q: np.ndarray,
                   allowed: np.ndarray, spacings, dti_bar: float,
                   add_candidates: np.ndarray | None = None, snap: bool = True,
                   verbose: bool = True):
    out = []
    for r in spacings:
        t0 = time.time()
        sp = emit_repack(base, consensus_u8, q, allowed, r, dti_bar,
                         add_candidates=add_candidates, snap=snap, verbose=verbose)
        out.append(sp)
        if verbose:
            print(f"[h48] sweep r={r}: dots={sp.n_dots} (kept {sp.n_kept}, added {sp.n_added}) "
                  f"predicted={sp.predicted_dti:.4f} ({time.time()-t0:.0f}s)", flush=True)
    return out
