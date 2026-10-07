"""H48-APEX - emit the *apex* of the multi-scale lineament consensus.

Why this exists
---------------
The first H48 emission repacked the family's measured-best field (``d2.8``,
44,090 px, public DTI 0.2600).  The audit of that emission found a fatal property
that had nothing to do with its predicted score: **59.2 % of its pixels are
d2.8's pixels and 66.9 % of them are the pixels of the reported 0.2778 field
``h33-2-b2``** (``evidence/h48_build.json`` -> ``artifact.uniqueness``).  The
family's scored fields are a *nested thinning chain* - measured here, exactly:

    227,507 px hedge-v2 (0.1563)  ⊃  172,974 px ens12 (0.1563)
    121,131 px h19-5  (0.1922)    ⊃   44,090 px d2.8  (0.2600)
     44,090 px d2.8  (0.2600)    ⊃   37,654 px h33-2-b2 (0.2778)   containment 1.000

so any emission that starts from d2.8 is a re-issue of a prior submission, which
the standing brief forbids as a deliverable.

The emission implemented here therefore starts from **H48's own detector**.  The
MSCL consensus is a percentile rank over the evaluated pixels of
``sqrt(rank_topo * rank_geophys)`` (see :mod:`gems47.h48`).  Its ``rank == 255``
class is the cells that are simultaneously at the top of the *topography*
lineament ranking and at the top of the *potential-field* lineament ranking -
the strongest possible expression of the H48 hypothesis ("a new fault is a
lineament in more than one physical field").  Taking the 3x3 local maxima of the
consensus inside that class gives the set used here, the **apex set**.

Measured, this set is essentially disjoint from every prior artifact:

    |apex| = 264,854 maxima overall, 25,809 in the rank-255 class
    Jaccard(apex, d2.8)     = 0.0078     Jaccard(apex, h33-2-b2) = 0.0054

which is 30x below the project's best previous novelty record (0.0457) and 80x
below the H48 repack (0.4400).

The operating point
-------------------
Mass is the family's only measured axis: inside the scored chain, thinning raised
the score monotonically (121,131 -> 0.1922, 44,090 -> 0.2600, 37,654 -> 0.2778),
so the apex set is swept over **nested consensus-rank thresholds**, which is the
detector's own confidence axis.  The spacing is held at the family's measured-best
separation (2.5 px) instead of being swept as well, so the conformal family has
seven members rather than forty-nine and the Bonferroni cost stays honest.

Nothing here is a claim about the private label set.  The threshold that is
actually emitted is chosen by the split-conformal lower bound in
``scripts/build_h48.py``, and the receipt records the level, the rank and the
exchangeability caveat next to it.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from . import lati
from . import metric as M
from .h48 import min_sep_select

#: nested thresholds on the MSCL consensus percentile rank (0..255).  Declared
#: before any DTI was looked at; 255 is the top rank of BOTH domains.
APEX_THRESHOLDS: tuple[int, ...] = (255, 254, 252, 248, 240, 224, 192)

#: dot separation held fixed at the family's measured-best operating point
#: (1.5 px lattice scored 0.2477, 2.4 px lattice 0.2600 - see knowledge/03).
APEX_SPACING: float = 2.5


def consensus_apex(consensus_u8: np.ndarray, allowed: np.ndarray, rank_min: int,
                   spacing_px: float = APEX_SPACING, budget: int = 60_000) -> np.ndarray:
    """The apex set: local maxima of the consensus at or above ``rank_min``.

    ``allowed`` carries the catalogue-clearance rule (the only *provable*
    pruning available: a prediction on a masked known fault can earn no
    private-label credit and still costs ``beta*K``).  Dots are taken in
    descending consensus and thinned by ``min_sep_select`` at ``spacing_px``,
    then capped at ``budget``.
    """
    cons = np.asarray(consensus_u8, np.float64)
    mx = ndimage.maximum_filter(cons, size=3, mode="constant")
    cand = (cons == mx) & (cons >= float(rank_min)) & np.asarray(allowed, bool)
    ys, xs = np.nonzero(cand)
    out = np.zeros(cons.shape, bool)
    if ys.size == 0:
        return out
    w = cons[ys, xs]
    order = np.argsort(-w, kind="stable")
    ys, xs, w = ys[order], xs[order], w[order]
    keep = np.asarray(min_sep_select((ys, xs), w, float(spacing_px)))
    ys, xs = ys[keep], xs[keep]
    if ys.size > int(budget):
        ys, xs = ys[:int(budget)], xs[:int(budget)]
    out[ys, xs] = True
    return out


def candidate_obs(name: str, dots: np.ndarray, template, ev_idx: np.ndarray) -> lati.Obs:
    """A candidate emission expressed as an observation, for the belief model.

    The belief model is fitted on ``lati.Obs`` objects, and each observation
    enters it through three sufficient statistics: the emitted mass ``S``, the
    exact max-filter credit ``w`` and the first-order halo ``a`` (the same
    quantities ``scripts/lati_fit.py`` builds from the scored rasters).  Building
    them for a candidate puts its prediction on **the same scale as the
    calibration residuals**, which is what makes the conformal lower bound a
    bound on a DTI rather than on an unrelated surrogate.
    """
    ev = np.asarray(template.evaluated, bool)
    pred = np.where(ev, np.asarray(dots, bool).astype(np.float64), 0.0)
    dmask = pred > 0
    dflat = np.flatnonzero(dmask.ravel())
    w_full = M.max_kernel_filter(pred)
    a_full = np.zeros(pred.shape, np.float64)
    for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        a_full += k * _shift_in(dmask.astype(np.float64), dy, dx)
    pos = np.full(pred.size, -1, np.int64)
    pos[ev_idx] = np.arange(ev_idx.size, dtype=np.int64)
    o = lati.Obs(id=name, dti=float("nan"), site="-", family="H48-APEX", sha256="-",
                 S=float(dmask.sum()), n_dots=int(np.asarray(dots, bool).sum()),
                 n_on_catalogue=int((np.asarray(dots, bool) & template.catalogue).sum()),
                 w=w_full.ravel()[ev_idx].astype(np.float32),
                 a=a_full.ravel()[ev_idx].astype(np.float32),
                 dot_pos=pos[dflat], dot_flat=dflat)
    o.extras = {"halo_sum_w": float(o.w.sum()), "halo_sum_a": float(o.a.sum())}
    return o


def _shift_in(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    out = np.zeros(a.shape, a.dtype)
    H, W = a.shape
    y0, y1 = max(0, -dy), min(H, H - dy)
    x0, x1 = max(0, -dx), min(W, W - dx)
    if y0 >= y1 or x0 >= x1:
        return out
    out[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
    return out


__all__ = ["APEX_SPACING", "APEX_THRESHOLDS", "candidate_obs", "consensus_apex"]
