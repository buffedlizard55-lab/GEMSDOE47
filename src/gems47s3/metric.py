"""Exact Distance-Weighted Tversky Index (DTI) for the DOE GEMS Prize Challenge.

Verified line-by-line against the official problem description:
  https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric
and the official scoring-clarification thread (DrivenData staff, posts #2 and #4):
  https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516

Published equations (verbatim structure)
----------------------------------------
    k(d)   = max(1 - d/R, 0),                R = 300 m = 3 px at 100 m
    TP_w   = sum_{g in G} max_{x: d(x,g)<=R}  p(x) * k(d(x,g))
    FP_w   = sum_{x: p(x)>0}                  p(x) * [1 - max_{g in G} k(d(x,g))]
    FN_w   = sum_{g in G} [1 - max_{x: d(x,g)<=R} p(x) * k(d(x,g))]
    DTI    = TP_w / (TP_w + alpha*FP_w + beta*FN_w + eps),   alpha=0.2, beta=0.8

Official worked example (used as a regression test in tests/test_metric_s3.py):
    TP_w = 3.00, FP_w = 1.89, FN_w = 2.00  ->  DTI = 0.60

Algebraic identity used throughout this repository (proved in tests/test_metric_s3.py by
brute-force comparison against the literal transcription above):
    FN_w = |G| - TP_w  exactly, so with T = TP_w, S = sum_x p(x), M = sum_x p(x)*max_g k,
        DTI = T / ( 0.2*(T + S - M) + 0.8*|G| )                       (IDENTITY)
    dDTI > 0 for one added unit of mass whose realised kernel weight is w and whose
    new credit is exactly w  <=>  w > 0.2 * DTI                        (CREDIT BAR)
because d(denominator) = alpha*(dT + dFP_w) = alpha*(w + 1 - w) = alpha = 0.2.

Masking (official staff answer, thread 11516 post #2, 2026-09-16):
    "Pixels corresponding to known USGS/INGENIOUS faults are masked / excluded from
     evaluation, so they do not count towards penalty terms."  and post #4: a predicted
    pixel near a known fault but far from new-fault truth IS fully penalised (there is no
    buffer around known faults); new-fault pixels may lie within 300 m of a known trace.
So `known` removes pixels from BOTH the prediction sum and the truth sum, pixel-exactly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt

from .spec import ALPHA, BETA, EPS_METRIC, RADIUS_PX

# --------------------------------------------------------------------------- kernel


def kernel(d, radius: float = RADIUS_PX) -> np.ndarray:
    """Triangular kernel k(d) = max(1 - d/R, 0); d and radius in pixels (1 px = 100 m)."""
    return np.maximum(1.0 - np.asarray(d, dtype=np.float64) / radius, 0.0)


def kernel_offsets(radius: float = RADIUS_PX) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Integer offsets inside the kernel support and their weights."""
    r = int(np.ceil(radius))
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    d = np.hypot(dy, dx)
    keep = (d <= radius) & (d > 0) | (d == 0)
    keep &= d <= radius
    return dy[keep].astype(np.int64), dx[keep].astype(np.int64), kernel(d[keep], radius)


_OFFS = kernel_offsets()
# Distinct non-zero kernel weights on the 100 m lattice, descending.  Used by the
# emission modules: only these values can ever be realised as credit.
LATTICE_WEIGHTS = tuple(sorted({round(float(w), 12) for w in _OFFS[2] if w > 0}, reverse=True))


def _shift(arr: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Shift ``arr`` by (dy, dx) with zero fill (valid: every array here is >= 0)."""
    out = np.zeros_like(arr)
    h, w = arr.shape
    ys0, ys1 = max(0, dy), min(h, h + dy)
    xs0, xs1 = max(0, dx), min(w, w + dx)
    out[ys0:ys1, xs0:xs1] = arr[max(0, -dy):min(h, h - dy), max(0, -dx):min(w, w - dx)]
    return out


# --------------------------------------------------------------------------- masks


def prepare(pred, truth, valid=None, known=None):
    """Normalise inputs to (p, g, active) float64/bool arrays on the scored domain."""
    p_in = np.asarray(pred, dtype=np.float64)
    t_in = np.asarray(truth)
    if p_in.ndim != 2 or p_in.shape != t_in.shape:
        raise ValueError("prediction and truth must be equal-shaped 2-D grids")
    valid = np.ones(p_in.shape, bool) if valid is None else np.asarray(valid, bool)
    known = np.zeros(p_in.shape, bool) if known is None else np.asarray(known, bool)
    if valid.shape != p_in.shape or known.shape != p_in.shape:
        raise ValueError("mask grid mismatch")
    active = valid & ~known
    vals = p_in[active]
    if vals.size and (not np.isfinite(vals).all() or vals.min() < 0.0 or vals.max() > 1.0):
        raise ValueError("predictions inside the scored domain must be finite and in [0, 1]")
    p = np.where(active & np.isfinite(p_in), p_in, 0.0)
    g = active & (t_in > 0)
    return p, g, active


# --------------------------------------------------------------------------- DTI


def dti(pred, truth, valid=None, known=None, alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Exact DTI for arbitrary soft or binary predictions in [0, 1]."""
    p, g, _ = prepare(pred, truth, valid, known)
    dy, dx, kw = _OFFS
    best = np.zeros(p.shape)
    for d, e, k in zip(dy, dx, kw):
        np.maximum(best, _shift(p, int(d), int(e)) * float(k), out=best)
    tp = float(best[g].sum())
    n = int(g.sum())
    fn = float(n) - tp
    if n:
        k_near = kernel(distance_transform_edt(~g))
    else:
        k_near = np.zeros(p.shape)
    fp = float((p * (1.0 - k_near)).sum())
    denom = tp + alpha * fp + beta * fn + EPS_METRIC
    s = float(p.sum())
    m = float((p * k_near).sum())
    return dict(
        tp=tp, fp=fp, fn=fn, n_truth=n, dti=float(tp / denom), coverage=(tp / n if n else 0.0),
        S=s, M=m, wasted=s - m,
        dti_identity=float(tp / (alpha * (tp + s - m) + beta * n + EPS_METRIC)),
    )


def dti_binary(pred_bool, truth, valid=None, known=None, alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Exact DTI via distance transforms when predictions are binary {0, 1}."""
    pb = np.asarray(pred_bool, bool)
    t = np.asarray(truth)
    valid = np.ones(pb.shape, bool) if valid is None else np.asarray(valid, bool)
    known = np.zeros(pb.shape, bool) if known is None else np.asarray(known, bool)
    active = valid & ~known
    p = pb & active
    g = (t > 0) & active
    n = int(g.sum())
    s = float(p.sum())
    if n == 0 or s == 0.0:
        return dict(tp=0.0, fp=s, fn=float(n), n_truth=n, dti=0.0, coverage=0.0,
                    S=s, M=0.0, wasted=s,
                    dti_identity=(0.0 if n else 0.0))
    k_near = kernel(distance_transform_edt(~g))
    # TP_w = sum over truth of max_x p(x) k(d(x,g)); for binary p this is k(d(p, g)).
    tp = float(kernel(distance_transform_edt(~p))[g].sum())
    fp = float((1.0 - k_near[p]).sum())
    m = float(k_near[p].sum())
    fn = float(n) - tp
    denom = tp + alpha * fp + beta * fn + EPS_METRIC
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n, dti=float(tp / denom), coverage=tp / n,
                S=s, M=m, wasted=s - m,
                dti_identity=float(tp / (alpha * (tp + s - m) + beta * n + EPS_METRIC)))


def dti_bruteforce(pred, truth, alpha: float = ALPHA, beta: float = BETA, radius: float = RADIUS_PX) -> dict:
    """Literal O(|G|*|P|) transcription of the published equations — test oracle only."""
    pred = np.asarray(pred, float)
    truth = np.asarray(truth) > 0
    gs = np.argwhere(truth)
    xs = np.argwhere(pred > 0)
    tp = fn = 0.0
    for g in gs:
        best = 0.0
        for x in xs:
            d = float(np.hypot(*(x - g)))
            if d <= radius:
                best = max(best, pred[tuple(x)] * max(1.0 - d / radius, 0.0))
        tp += best
        fn += 1.0 - best
    fp = 0.0
    for x in xs:
        kmax = 0.0
        for g in gs:
            kmax = max(kmax, max(1.0 - float(np.hypot(*(x - g))) / radius, 0.0))
        fp += pred[tuple(x)] * (1.0 - kmax)
    return dict(tp=tp, fp=fp, fn=fn, dti=tp / (tp + alpha * fp + beta * fn + EPS_METRIC))


def official_worked_example() -> dict:
    """Reproduce the published scoring example: TP_w 3.00, FP_w 1.89, FN_w 2.00 -> 0.60."""
    tp, fp, fn = 3.00, 1.89, 2.00
    return dict(tp=tp, fp=fp, fn=fn, dti=tp / (tp + ALPHA * fp + BETA * fn + EPS_METRIC))


# --------------------------------------------------------------------------- decision theory


def credit_bar(current_dti: float, alpha: float = ALPHA) -> float:
    """Break-even kernel weight for one added unit of mass: w > alpha * DTI.

    Derivation is in the module docstring.  NOTE: the alternative form
    ``alpha*s/(1-alpha*s)`` that circulated in earlier team repositories does NOT
    follow from the metric and materially mis-prunes at s ~ 0.27.
    """
    return alpha * current_dti


def dti_from_TSM(T: float, S: float, M: float, n_truth: float,
                 alpha: float = ALPHA, beta: float = BETA) -> float:
    """Forward model: DTI from credit T, emitted mass S, covering mass M and |G|."""
    return float(T / (alpha * (T + S - M) + beta * n_truth + EPS_METRIC))


@dataclass
class ScoreBudget:
    """The three quantities that fully determine DTI for a binary submission."""
    T: float          # TP_w: credit captured from the hidden truth
    S: float          # emitted mass (number of positive pixels for a 0/1 file)
    M: float          # mass that is the best cover of some truth pixel
    n_truth: float    # |G|

    @property
    def wasted(self) -> float:
        return self.S - self.M

    @property
    def dti(self) -> float:
        return dti_from_TSM(self.T, self.S, self.M, self.n_truth)

    @property
    def credit_per_pixel(self) -> float:
        return self.T / self.S if self.S else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(dti=self.dti, wasted=self.wasted, credit_per_pixel=self.credit_per_pixel)
        return d
