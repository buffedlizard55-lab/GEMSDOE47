"""Emitters: how a detector field becomes a legal 0/1 prediction raster.

The decision rule is analytic.  With ``D = 0.2*(T + S - M) + 0.8*|G|`` (see metric.py),
adding one unit of prediction mass whose realised kernel weight is ``w`` and which becomes
the sole best cover of a truth pixel changes ``D`` by exactly ``alpha = 0.2``, so

    dDTI > 0  <=>  w > 0.2 * DTI                                            (CREDIT BAR)

and a dot whose truth pixel is already better covered changes ``D`` by ``0.2*(1-w) >= 0``
and ``T`` by 0, so **redundant mass never helps**.  Two structural consequences drive
every emitter here:

  * mass that is not the best covering pixel of some hidden truth pixel is pure cost, so
    duplicates along a trace must be suppressed -- this is what the spacing parameter does;
  * one pixel can be the best cover of several truth pixels (a trace is 1 px wide and the
    kernel reaches 3 px), so credit is not proportional to emitted count.

Emitters
--------
``poisson_disk``      field-ordered Poisson-disk thinning: candidates are visited in
                      DESCENDING field order and accepted iff no accepted pixel is within
                      ``min_dist``.  Field ordering matters -- the family's incumbent rule
                      (GEMSDOE10 ``placement.dot_nms``, GEMSDOE32 ``emission.dot_thin``)
                      walks candidates in ascending RASTER index, so the layout is decided
                      by pixel address rather than by evidence.  Verified different here.
``dot_thin_raster``   the incumbent raster-order rule, re-implemented for comparison only.
``greedy_coverage``   exact greedy maximisation of expected kernel coverage of a blurred
                      field (lazy priority queue).  Optimal-ish but O(N * 28) with a heap.
``oriented_blur``     blur the field along the LOCAL STRIKE only.  An isotropic Gaussian
                      (what GEMSDOE32's "scatter-smoothed" arm used) smears mass ACROSS the
                      trace, where the metric charges 0.2 per unit and pays nothing.
``flank_prune``       delete emitted pixels within ``b`` of the given catalogue.  Historical
                      participant-level 0.2708/0.2778 labels are not authenticated to specific
                      rasters; the d2.8 raster is an owner-reported reference, not an established
                      incumbent. No causal score gain from flank pruning is claimed here.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import metric as M


# --------------------------------------------------------------------------- support
def threshold_field(field: np.ndarray, q: float, mask: np.ndarray) -> np.ndarray:
    """Boolean support at the ``q`` upper-quantile of ``field`` inside ``mask``."""
    f = np.asarray(field, np.float32)
    vals = f[mask & np.isfinite(f)]
    if vals.size == 0:
        return np.zeros(f.shape, bool)
    tau = float(np.quantile(vals, 1.0 - q))
    return mask & np.isfinite(f) & (f >= tau)


def topk_mask(field: np.ndarray, n: int, mask: np.ndarray) -> np.ndarray:
    """Exactly ``n`` highest-field pixels inside ``mask`` (ties by raster index)."""
    f = np.asarray(field, np.float32).copy()
    f[~mask] = -np.inf
    flat = f.ravel()
    n = min(int(n), int(mask.sum()))
    if n <= 0:
        return np.zeros(f.shape, bool)
    idx = np.argpartition(flat, -n)[-n:]
    out = np.zeros(flat.size, bool)
    out[idx] = True
    return out.reshape(f.shape)


# --------------------------------------------------------------------------- emitters
def poisson_disk(field: np.ndarray, support: np.ndarray, min_dist: float) -> np.ndarray:
    """Field-ordered Poisson-disk thinning of ``support``.

    Candidates are visited in descending field value; a candidate is accepted iff no
    already-accepted pixel lies within ``min_dist`` (Euclidean, pixels).  A uniform grid
    bucket index makes the neighbourhood test O(1) amortised.
    """
    ys, xs = np.nonzero(support)
    if ys.size == 0:
        return np.zeros(field.shape, bool)
    vals = field[ys, xs]
    order = np.argsort(-vals, kind="stable")
    ys, xs = ys[order], xs[order]
    cell = max(1.0, float(min_dist))
    r2 = float(min_dist) ** 2
    reach = int(np.ceil(min_dist / cell)) + 1
    grid: dict[tuple[int, int], list[int]] = {}
    keep = np.zeros(ys.size, bool)
    for i in range(ys.size):
        y, x = int(ys[i]), int(xs[i])
        cy, cx = int(y // cell), int(x // cell)
        ok = True
        for gy in range(cy - reach, cy + reach + 1):
            bucket_row = grid.get(gy)
            if bucket_row is None:
                continue
            for gx in range(cx - reach, cx + reach + 1):
                lst = bucket_row.get(gx)
                if not lst:
                    continue
                for j in lst:
                    dy = y - ys[j]; dx = x - xs[j]
                    if dy * dy + dx * dx < r2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            keep[i] = True
            grid.setdefault(cy, {}).setdefault(cx, []).append(i)
    out = np.zeros(field.shape, bool)
    out[ys[keep], xs[keep]] = True
    return out


def dot_thin_raster(support: np.ndarray, min_dist: float) -> np.ndarray:
    """Incumbent raster-order Poisson-disk thinning (comparison control only)."""
    field = np.zeros(support.shape, np.float32)
    return poisson_disk(field, support, min_dist)


def greedy_coverage(field: np.ndarray, mask: np.ndarray, n: int,
                    radius: float = M.RADIUS_PX) -> np.ndarray:
    """Exact greedy maximisation of sum_y field[y] * max(0, k(|x-y|) - C[y]).

    ``C`` is the coverage already supplied.  A lazy max-heap recomputes a candidate's gain
    only when it is popped, which is exact for this monotone submodular objective (the
    stored key is always an upper bound on the current gain).
    """
    import heapq

    dy, dx, kw = M.kernel_offsets(radius)
    f = np.where(mask, np.asarray(field, np.float32), 0.0)
    C = np.zeros(f.shape, np.float32)

    def gain_of(y: int, x: int) -> float:
        tot = 0.0
        h, w = f.shape
        for d, e, k in zip(dy, dx, kw):
            ny, nx = y + int(d), x + int(e)
            if 0 <= ny < h and 0 <= nx < w:
                rem = k - C[ny, nx]
                if rem > 0.0:
                    tot += float(f[ny, nx]) * rem
        return tot

    # seed the heap with the top-quantile of the kernel-correlated field
    corr = np.zeros(f.shape, np.float32)
    for d, e, k in zip(dy, dx, kw):
        corr += float(k) * ndi.shift(f, (-int(d), -int(e)), order=0, mode="constant", cval=0.0)
    corr[~mask] = -np.inf
    nseed = min(int(max(n * 8, 20000)), int(mask.sum()))
    seed_idx = np.argpartition(corr.ravel(), -nseed)[-nseed:]
    heap = [(-float(corr.ravel()[i]), int(i)) for i in seed_idx]
    heapq.heapify(heap)

    out = np.zeros(f.shape, bool)
    w = f.shape[1]
    chosen = 0
    stale: set[int] = set()
    while heap and chosen < n:
        neg, flat = heapq.heappop(heap)
        if flat in stale:
            continue
        y, x = divmod(flat, w)
        g = gain_of(y, x)
        if g <= 0.0:
            break
        # lazily re-insert neighbours whose gain may now be the largest
        if -neg - g > 1e-6 and chosen < n:
            stale.add(flat)
            heapq.heappush(heap, (-g, flat))
            # also push the neighbourhood once, so better candidates can surface
            for d, e, _ in zip(dy, dx, kw):
                ny, nx = y + int(d), x + int(e)
                if 0 <= ny < f.shape[0] and 0 <= nx < f.shape[1]:
                    nf = ny * w + nx
                    if not out[ny, nx] and nf not in stale:
                        heapq.heappush(heap, (-gain_of(ny, nx), nf))
                        stale.add(nf)
            continue
        out[y, x] = True
        chosen += 1
        for d, e, k in zip(dy, dx, kw):
            ny, nx = y + int(d), x + int(e)
            if 0 <= ny < f.shape[0] and 0 <= nx < f.shape[1]:
                C[ny, nx] = max(C[ny, nx], float(k))
    return out


# --------------------------------------------------------------------------- field shaping
def isotropic_blur(field: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0:
        return np.asarray(field, np.float32)
    return ndi.gaussian_filter(np.nan_to_num(field.astype(np.float32)), sigma,
                               mode="nearest").astype(np.float32)


def oriented_blur(field: np.ndarray, sigma_along: float, sigma_across: float,
                  coherence: np.ndarray | None = None, theta: np.ndarray | None = None) -> np.ndarray:
    """Anisotropic blur: ``sigma_along`` along the local strike, ``sigma_across`` across it.

    Implemented exactly (no interpolation of the field) as the max over four fixed
    orientations of a separable 1-D smoothing along that orientation, weighted by the
    structure-tensor coherence.  An isotropic blur of the same total mass pushes prediction
    OFF the trace, where the metric charges 0.2 per unit and pays nothing; the truth is a
    1-px-wide curve, so the correct smoothing of the expected-credit density is along it.
    """
    f = np.nan_to_num(np.asarray(field, np.float32))
    if sigma_along <= 0 and sigma_across <= 0:
        return f
    if sigma_across > 0:
        f = ndi.gaussian_filter(f, sigma_across, mode="nearest").astype(np.float32)
    if sigma_along <= 0:
        return f
    # 1-D smoothing along axis 0 (N-S strike) and axis 1 (E-W strike), plus the two
    # diagonals obtained by shearing with integer shifts (exact, no resampling).
    a0 = ndi.uniform_filter1d(f, max(3, int(round(2 * sigma_along)) + 1), axis=0, mode="nearest")
    a1 = ndi.uniform_filter1d(f, max(3, int(round(2 * sigma_along)) + 1), axis=1, mode="nearest")
    L = max(3, int(round(2 * sigma_along)) + 1)
    diag1 = np.zeros_like(f); diag2 = np.zeros_like(f)
    acc = np.zeros_like(f)
    for t in range(-(L // 2), L // 2 + 1):
        s = ndi.shift(f, (t, t), order=0, mode="nearest")
        diag1 += s
        s2 = ndi.shift(f, (t, -t), order=0, mode="nearest")
        diag2 += s2
        acc += s
    diag1 /= L; diag2 /= L
    if theta is None:
        return np.maximum.reduce([a0, a1, diag1, diag2]).astype(np.float32)
    # select the orientation whose strike best matches the local structure tensor
    cos2 = np.cos(2 * theta); sin2 = np.sin(2 * theta)
    w_ns = np.maximum(cos2, 0.0)          # strike N-S  <=> 2theta ~ 0
    w_ew = np.maximum(-cos2, 0.0)         # strike E-W  <=> 2theta ~ pi
    w_d1 = np.maximum(sin2, 0.0)
    w_d2 = np.maximum(-sin2, 0.0)
    tot = w_ns + w_ew + w_d1 + w_d2 + 1e-9
    out = (w_ns * a0 + w_ew * a1 + w_d1 * diag1 + w_d2 * diag2) / tot
    if coherence is not None:
        out = coherence * out + (1.0 - coherence) * f
    return out.astype(np.float32)


def disk_footprint(radius: float) -> np.ndarray:
    """Boolean disk of pixels at Euclidean distance <= radius (exact, no approximation)."""
    r = int(np.ceil(radius))
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    return (dy * dy + dx * dx) <= radius * radius + 1e-9


def nms_disk(field: np.ndarray, support: np.ndarray, min_dist: float) -> np.ndarray:
    """Vectorised field-ordered thinning: keep pixels that are the maximum of their own
    closed disk of radius ``min_dist`` restricted to ``support``.

    Two kept pixels cannot lie within ``min_dist`` of each other (each is the maximum of the
    other's disk), so this enforces exactly the spacing constraint the Poisson-disk rule
    does -- but in O(n) array operations instead of a Python candidate loop, which is what
    makes a several-hundred-point sweep affordable.  Plateaus are broken by raster index
    through ``maximum_filter``'s tie handling plus an explicit equality test.
    """
    f = np.where(support, np.asarray(field, np.float32), np.float32(-np.inf))
    if min_dist <= 0:
        return support.copy()
    fp = disk_footprint(min_dist)
    mx = ndi.maximum_filter(f, footprint=fp, mode="constant", cval=-np.inf)
    out = support & (f >= mx)
    if not out.any():
        return out
    # Deterministic, RADIUS-AWARE tie breaking.  Exact float32 ties are common in a smoothed
    # geophysical field, and two tied pixels inside each other's disc both satisfy f >= mx, so
    # without this step the spacing constraint is violated.  An earlier version broke ties by
    # 8-connected labelling, which only worked for adjacent ties and silently let tied pixels
    # at 1 < d <= min_dist both survive.  Taking the minimum raster index inside the same disc
    # footprint is correct at every separation.
    tied = out & (mx == f)
    if tied.sum() > 1:
        big = np.int64(f.size) + 1
        idx = np.arange(f.size, dtype=np.int64).reshape(f.shape)
        keyed = np.where(tied, idx, big)
        first = ndi.minimum_filter(keyed, footprint=fp, mode="constant", cval=big)
        out = out & (idx == first)
    return out


_STRIKE_DIRS = ((1, 0), (0, 1), (1, 1), (1, -1))


def strike_classes(theta: np.ndarray) -> np.ndarray:
    """Quantise a strike direction to one of four classes, in the ``geomorph.orientation`` frame.

    ``geomorph.orientation`` returns theta = 0.5*atan2(2*Jxy, Jxx - Jyy) computed with the row
    derivative as y and the column derivative as x.  Measured on synthetic straight ridges in
    ``tests/test_h49.py``: a north-south trace gives theta = 0, east-west pi/2, the y = x diagonal
    -pi/4 and the y = -x diagonal +pi/4.  So the trace direction is ``(cos theta, -sin theta)`` in
    (row, column) offsets, and the class weights below are exactly ``oriented_blur``'s.
    """
    cos2 = np.cos(2.0 * theta)
    sin2 = np.sin(2.0 * theta)
    w = np.stack([np.maximum(cos2, 0.0),         # (dy, dx) = (1, 0)  north-south
                  np.maximum(-cos2, 0.0),        # (0, 1)            east-west
                  np.maximum(-sin2, 0.0),        # (1, 1)            y = x diagonal
                  np.maximum(sin2, 0.0)])        # (1, -1)           y = -x diagonal
    return np.argmax(w, axis=0).astype(np.int8)


def ellipse_footprint(along: float, across: float, dy: int, dx: int) -> np.ndarray:
    """Boolean ellipse with semi-axes ``along`` (along (dy, dx)) and ``across`` (perpendicular),
    in true pixel units, used as an ``ndimage`` footprint."""
    r = int(np.ceil(max(along, across)))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    nrm = float(np.hypot(dy, dx))
    uy, ux = dy / nrm, dx / nrm
    s = yy * uy + xx * ux
    t = -yy * ux + xx * uy
    return (s / max(along, 1e-6)) ** 2 + (t / max(across, 1e-6)) ** 2 <= 1.0 + 1e-9


def _footprint_nms(f: np.ndarray, m: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Pixels of ``m`` that are the maximum of their own ``fp``-neighbourhood, ties by raster index.

    Same construction as ``nms_disk``: the maximum filter certifies the spacing, and the index
    tie-break is what makes it exact when two equal values share one footprint.
    """
    fm = np.where(m, f, np.float32(-np.inf))
    mx = ndi.maximum_filter(fm, footprint=fp, mode="constant", cval=-np.inf)
    out = m & (fm >= mx)
    tied = out & (mx == fm)
    if int(tied.sum()) > 1:
        big = np.int64(f.size) + 1
        idx = np.arange(f.size, dtype=np.int64).reshape(f.shape)
        keyed = np.where(tied, idx, big)
        first = ndi.minimum_filter(keyed, footprint=fp, mode="constant", cval=big)
        out = out & (idx == first)
    return out


def nms_oriented(field: np.ndarray, support: np.ndarray, along: float, across: float,
                 theta: np.ndarray) -> np.ndarray:
    """Field-ordered thinning with an ELLIPTICAL, strike-aligned exclusion zone (H49-A).

    A pixel survives iff it is the maximum of its own ellipse of semi-axis ``along`` along the local
    strike and ``across`` across it.  Two survivors can therefore never lie inside each other's
    ellipse, so the spacing is enforced exactly (with a raster-index tie-break for equal values).

    Why the axis assignment matters: the exclusion is a DISK for ``along == across`` (the incumbent
    rule) and an ellipse elongated ACROSS the trace when ``across > along``.  A 1-D trace does not
    need cross-strike sampling: the metric pays for the single best cover of a truth pixel, so a
    second or third pixel sampled across the same ridge adds cost (0.2 per unit) and no credit.  Its
    budget is better spent further along the trace, where the next dot can be the best cover of a
    DIFFERENT truth pixel.  This is the emission analogue of ``oriented_blur`` -- that reshapes the
    field, this reshapes the sampling geometry -- and every incumbent emitter in this repository and
    in the score history (``nms_disk``, ``poisson_disk``, GEMSDOE10 ``dot_nms``, GEMSDOE32
    ``dot_thin``) is isotropic.

    Approximation, stated: each pixel is tested against the ellipse of ITS OWN orientation class, so
    a neighbouring pixel of a different class (45 degrees away) is not counted as a blocker inside
    the footprint.  Four classes therefore under-sample the corners; the effect is measured in
    ``tests/test_h49.py`` as the difference between the oriented and isotropic survivor counts.
    """
    f = np.where(support, np.asarray(field, np.float32), np.float32(-np.inf))
    cls = strike_classes(theta)
    out = np.zeros(f.shape, bool)
    for k, (dy, dx) in enumerate(_STRIKE_DIRS):
        m = support & (cls == k)
        if not m.any():
            continue
        out |= _footprint_nms(f, m, ellipse_footprint(along, across, dy, dx))
    return out


def emit_oriented(field: np.ndarray, mask: np.ndarray, along: float, across: float,
                  theta: np.ndarray, budget: int | None = None,
                  d_catalogue: np.ndarray | None = None, flank_b: float = 0.0) -> dict:
    """H49-A operating point: strike-aligned thinning, then the same budget/flank rules as ``emit``."""
    f = np.asarray(field, np.float32)
    out = nms_oriented(f, mask, along, across, theta)
    n_thinned = int(out.sum())
    if budget is not None and n_thinned > int(budget):
        out = topk_mask(np.where(out, f, -np.inf), int(budget), out)
    n_before = int(out.sum())
    if d_catalogue is not None:
        out = flank_prune(out, d_catalogue, flank_b)
    return dict(mask=out, shaped=f, support=mask, n_support=int(mask.sum()),
                n_thinned=n_thinned, n_before_flank=n_before, n_after_flank=int(out.sum()),
                min_dist=float(along), along=float(along), across=float(across),
                support_q=1.0, flank_b=float(flank_b),
                budget=(int(budget) if budget is not None else None),
                blur="none", engine="oriented")


def flank_prune(emitted: np.ndarray, d_catalogue: np.ndarray, b: float) -> np.ndarray:
    """Delete emitted pixels within ``b`` pixels of the given catalogue."""
    if b <= 0:
        return emitted
    return emitted & (d_catalogue > b)


# --------------------------------------------------------------------------- operating point
def emit(field: np.ndarray, mask: np.ndarray, min_dist: float, support_q: float,
         d_catalogue: np.ndarray | None = None, flank_b: float = 0.0,
         blur: str = "oriented", sigma_along: float = 0.0, sigma_across: float = 0.0,
         theta: np.ndarray | None = None, coherence: np.ndarray | None = None,
         engine: str = "nms", budget: int | None = None) -> dict:
    """Apply one operating point and return the emitted mask plus its bookkeeping.

    Operating point = (support quantile ``support_q``, spacing ``min_dist``, catalogue-flank
    buffer ``flank_b``, blur geometry).  ``budget`` optionally caps the emitted count by
    taking the highest-field survivors, which is how a matched-mass comparison is run.
    """
    f = np.asarray(field, np.float32)
    if blur == "oriented":
        shaped = oriented_blur(f, sigma_along, sigma_across, coherence, theta)
    elif blur == "isotropic":
        shaped = isotropic_blur(f, max(sigma_along, sigma_across))
    elif blur == "none":
        shaped = f
    else:
        raise ValueError(f"unknown blur {blur!r}")
    support = threshold_field(shaped, support_q, mask)
    if engine == "greedy":
        n = int(budget) if budget else int(support.sum())
        out = greedy_coverage(shaped, support, n)
    elif engine == "poisson":
        out = poisson_disk(shaped, support, min_dist)
    else:
        out = nms_disk(shaped, support, min_dist)
    n_thinned = int(out.sum())
    if budget is not None and n_thinned > int(budget):
        out = topk_mask(np.where(out, shaped, -np.inf), int(budget), out)
    n_before = int(out.sum())
    if d_catalogue is not None:
        out = flank_prune(out, d_catalogue, flank_b)
    return dict(mask=out, shaped=shaped, support=support,
                n_support=int(support.sum()), n_thinned=n_thinned,
                n_before_flank=n_before, n_after_flank=int(out.sum()),
                min_dist=float(min_dist), support_q=float(support_q), flank_b=float(flank_b),
                budget=(int(budget) if budget is not None else None),
                blur=blur, sigma_along=float(sigma_along), sigma_across=float(sigma_across),
                engine=engine)
