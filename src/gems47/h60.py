"""H60-H64 -- the lidar scarp-crest amplitude field, per-trace emission, and the
H64 instrument refinement study.

Preregistration
---------------
``docs/research/h60-hypotheses-preregistered.md`` (committed before any score in this
round was computed) freezes the fields, the blocked-holdout design, the instruments,
the controls and the promotion gate.  This module implements the frozen definitions
and nothing else; every deviation is recorded in the screen receipt.

What is scientifically new
--------------------------
1.  **H60** emits on the owner-derived 1 m lidar scarp stack's *own amplitude* -- the
    per-cell maximum of the emission-domain ranks of six scarp channels
    (``step_max, lappos_max, lapneg_max, upface_max, downface_max, cross_max``) --
    masked for the two loudest non-tectonic step sources that have on-grid distance
    rasters (US Census TIGER roads < 250 m; BLM closed mining claims < 150 m).  No arm
    in the GEMSDOE1-54 family has ever emitted on the lidar channels as a field: they
    were used only as a truth population (Instrument L), as multiplicative
    corroborators that degraded the slope field (H50-E), or as layers of the retired
    LATI leaderboard fit.
2.  **H61** is the per-trace budget reallocation of the H50 slope-anomaly field -- the
    untested emission variant named in the previous session's handoff (the tested
    H50-D arm was a per-pixel anisotropic *exclusion* rule, a different mechanism).
3.  **H62** is an additive 50/50 rank mixture of the H50 field and the H60 field.
    Every previous combination in the family was multiplicative (an AND gate), which
    discards; an additive mixture has never been tried.
4.  **H63** is the H60 field restricted to within 10 px (1 km) of the catalogue -- the
    "newly mapped geometry of existing fault systems" pole, opposite to H60's
    "everywhere the lidar says" pole.
5.  **H64** builds stratified / noise-filtered variants of the lidar-peak instruments
    (catalogue distance <= 3 px vs > 3 px; road/claim filtered; ``ex_max`` and
    ``coh100`` peaks) for the 13-artifact score-correlation study.

Provenance limits (do not drop)
-------------------------------
* The lidar stack is **owner-derived** from USGS 3DEP 1 m DEM tiles (706/716; work
  resolution 2 m; quantisation and per-channel meanings pinned in
  ``registry/data_manifest.json``), NOT organiser-supplied.  It shares its terrain
  modality with band 19, so the primary lidar-peak instrument is optimistic for the
  lidar-reading fields (H60/H62/H63); the preregistered gate therefore carries an
  independent-instrument floor on the SGMC off-catalogue population.
* The restored rasters are hash-pinned owner mirrors, not organiser-authenticated
  bytes, and the owner-reported public scores are not organiser receipts.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems47s3.geomorph import rank_scale

from . import h50

#: the six amplitude channels of the owner-derived lidar scarp stack (frozen)
H60_CHANNELS = ("step_max", "lappos_max", "lapneg_max",
                "upface_max", "downface_max", "cross_max")
#: fixed noise-mask radii (metres), chosen in the preregistration, never tuned
ROAD_MASK_M = 250.0
CLAIM_MASK_M = 150.0
#: H63 catalogue-adjacency radius (pixels)
CATALOGUE_ADJACENCY_PX = 10.0
#: H61 per-trace threshold: emission-domain quantile of the H50 field
H61_TRACE_QUANTILE = 0.90
#: H62 mixture weight (additive; frozen at 1/2)
H62_LAMBDA = 0.5


# --------------------------------------------------------------------- io
def read_grid(data_dir: Path) -> dict:
    """Footprint / catalogue / evaluated masks (same contract as ``h50.read_grid``)."""
    return h50.read_grid(data_dir)


def noise_ok(data_dir: Path) -> np.ndarray:
    """True where the cell is >= ROAD_MASK_M from a TIGER road and >= CLAIM_MASK_M
    from a BLM closed mining claim (NaN distance = outside footprint -> False)."""
    with rasterio.open(Path(data_dir) / "external" / "audit_sources"
                       / "tiger_road_distance_m.tif") as src:
        road = src.read(1)
    with rasterio.open(Path(data_dir) / "external" / "audit_sources"
                       / "blm_closed_claim_distance_m.tif") as src:
        claim = src.read(1)
    ok = (np.nan_to_num(road, nan=-1.0) >= ROAD_MASK_M) & \
         (np.nan_to_num(claim, nan=-1.0) >= CLAIM_MASK_M)
    return ok


def h60_emission_domain(data_dir: Path) -> np.ndarray:
    """Emission domain of the lidar arms: evaluated & valid-lidar & noise-ok."""
    grids = read_grid(data_dir)
    ch = h50.lidar_scarp_channels(data_dir)
    valid = ch["valid"] > 0
    del ch
    return grids["evaluated"] & valid & noise_ok(data_dir)


# ------------------------------------------------------------------ fields
def h50_field(data_dir: Path, mask: np.ndarray) -> np.ndarray:
    """The H50 field, reproduced exactly: global rank of band 19 above its 25 px
    Gaussian regional level (``scripts/build_submission_h50.py::build_field``)."""
    with rasterio.open(Path(data_dir) / "training_features.tif") as src:
        slope = src.read(h50.SLOPE_BAND).astype(np.float32)
    slope[~np.isfinite(slope)] = 0.0
    slope[slope < -1e30] = 0.0
    regional = ndi.gaussian_filter(slope, 25.0, mode="nearest")
    field = rank_scale(np.where(mask, slope - regional, np.nan))
    return np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)


def channel_rank_max(data_dir: Path, mask: np.ndarray) -> np.ndarray:
    """Per-cell maximum of the emission-domain ranks of the six scarp channels."""
    ch = h50.lidar_scarp_channels(data_dir)
    acc = np.zeros(mask.shape, np.float32)
    for name in H60_CHANNELS:
        r = rank_scale(np.where(mask, ch[name], np.nan)).astype(np.float32)
        np.maximum(acc, r, out=acc)
    return acc


def h60_field(data_dir: Path, mask: np.ndarray) -> np.ndarray:
    """H60: rank_scale of the channel-rank maximum over the emission domain."""
    acc = channel_rank_max(data_dir, mask)
    field = rank_scale(np.where(mask, acc, np.nan))
    return np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)


def h62_field(h50f: np.ndarray, h60f: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """H62: additive 50/50 rank mixture of the H50 and H60 fields, re-ranked."""
    mix = H62_LAMBDA * h50f + (1.0 - H62_LAMBDA) * h60f
    field = rank_scale(np.where(mask, mix, np.nan))
    return np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)


def h63_domain(data_dir: Path, base_domain: np.ndarray) -> np.ndarray:
    """H63 emission domain: H60 domain AND within 10 px of the catalogue."""
    with rasterio.open(Path(data_dir) / "labels.tif") as src:
        catalogue = src.read(1) == 1
    dcat = ndi.distance_transform_edt(~catalogue)
    return base_domain & (dcat <= CATALOGUE_ADJACENCY_PX)


# ------------------------------------------------------------------ H61 emission
def _greedy_up_to(order: np.ndarray, shape: tuple[int, int], spacing_px: float,
                  budget: int) -> np.ndarray:
    """Greedy spaced selection capped at what the candidate set can actually hold.

    ``greedy_spaced_pixels`` raises when the ranked candidates cannot supply
    ``budget`` points at ``spacing_px``; inside a small trace component that is a
    normal, expected outcome (measured: a 174-dot allocation fits only 173).  This
    helper binary-searches the largest feasible budget <= ``budget`` so the caller's
    leftover pass can spend the difference elsewhere.  Deterministic.
    """
    from gemsdoe47.magnetic import greedy_spaced_pixels
    try:
        return greedy_spaced_pixels(order, shape, min_separation_px=spacing_px,
                                    budget=int(budget))
    except ValueError:
        pass
    lo, hi = 0, int(budget) - 1   # hi is known feasible-or-not; lo always feasible
    best = np.empty(0, dtype=np.int64)
    while lo <= hi:
        mid = (lo + hi) // 2
        if mid == 0:
            break
        try:
            sel = greedy_spaced_pixels(order, shape, min_separation_px=spacing_px,
                                       budget=mid)
            best = sel
            lo = mid + 1
        except ValueError:
            hi = mid - 1
    return best


def emit_trace(field: np.ndarray, valid: np.ndarray, spacing_px: float, budget: int,
               trace_threshold: float) -> np.ndarray:
    """H61 per-trace budget reallocation (frozen definition).

    Candidate trace cells are the valid cells with ``field > trace_threshold``; they
    are labelled with 8-connectivity; each component receives
    ``max(1, round(budget * area_k / total_trace_area))`` dots, emitted by greedy
    spaced selection *inside* the component ranked by within-component field order.
    Any leftover budget (component exhaustion, rounding) is spent by one greedy pass
    over the remaining valid cells that are at least ``spacing_px`` from every
    already-emitted dot, ranked by the field.  Emits exactly ``budget`` dots or
    raises.
    """
    from gemsdoe47.magnetic import greedy_spaced_pixels, ranked_pixels

    f = np.where(valid, np.nan_to_num(np.asarray(field, np.float32), nan=0.0), 0.0)
    p = np.zeros(f.shape, np.float32)
    cand = valid & (f > float(trace_threshold))
    lab, n = ndi.label(cand, structure=np.ones((3, 3), dtype=int))
    if n > 0:
        areas = np.bincount(lab.ravel())
        areas[0] = 0
        total = float(areas.sum())
        # Deterministic largest-remainder allocation with cycling.  The
        # preregistration's min-1 floor is NOT implementable without over-emission
        # when the trace components outnumber the budget or when many components
        # have exact share < 1 (measured: 2357 dots for a 1400 budget on block 5),
        # so the floor is dropped and the surplus is distributed by largest
        # fractional part, cycling deterministically.  sum(alloc) == budget always.
        # Deviation recorded in the screen receipt.
        exact = np.zeros(n + 1, np.float64)
        exact[1:] = int(budget) * areas[1:] / total
        alloc = np.floor(exact).astype(int)
        alloc[0] = 0
        surplus = int(budget) - int(alloc.sum())
        frac = exact - np.floor(exact)
        frac[0] = -1.0
        order = np.argsort(-frac, kind="stable")
        i = 0
        while surplus > 0:
            k = int(order[i % n])
            if k != 0:
                alloc[k] += 1
                surplus -= 1
            i += 1
        for k in range(1, n + 1):
            if alloc[k] <= 0:
                continue
            comp = lab == k
            order = ranked_pixels(np.where(comp, f, 0.0), comp)
            if order.size == 0:
                continue
            p.ravel()[_greedy_up_to(order, f.shape, spacing_px,
                                    int(alloc[k]))] = 1.0
    # leftover pass: respect the spacing against every already-emitted dot
    leftover = int(budget) - int(p.sum())
    if leftover > 0:
        occupied = p > 0
        if occupied.any():
            dist = ndi.distance_transform_edt(~occupied)
            allowed = valid & (dist >= spacing_px)
        else:
            allowed = valid
        order = ranked_pixels(np.where(allowed, f, 0.0), allowed)
        if order.size:
            sel = greedy_spaced_pixels(order, f.shape, min_separation_px=spacing_px,
                                       budget=leftover)
            p.ravel()[sel] = 1.0
    if int(p.sum()) != int(budget):
        raise ValueError(f"H61 emission contract failed: {int(p.sum())} != {int(budget)}")
    if (p[~valid] != 0).any():
        raise ValueError("H61 emitted outside the valid domain")
    return p


def h61_trace_threshold(h50f: np.ndarray, domain: np.ndarray) -> float:
    """Global emission-domain quantile of the H50 field (frozen at 0.90)."""
    vals = h50f[domain]
    if vals.size == 0:
        raise ValueError("empty emission domain")
    return float(np.quantile(vals, H61_TRACE_QUANTILE))


# ------------------------------------------------------------------ H64 instruments
def catalogue_distance(data_dir: Path) -> np.ndarray:
    with rasterio.open(Path(data_dir) / "labels.tif") as src:
        catalogue = src.read(1) == 1
    return ndi.distance_transform_edt(~catalogue)


def instrument_lidar_stratified(data_dir: Path, *, channel: str, threshold: float,
                                min_distance: int, near_px: float = 3.0) -> dict:
    """Off-catalogue lidar peaks of one channel split by catalogue distance.

    Returns ``(near_mask, far_mask)``: peaks within ``near_px`` of the catalogue and
    peaks farther than ``near_px``.  Both are restricted to valid lidar, inside the
    footprint and off the catalogue, exactly like Instrument L.
    """
    ch = h50.lidar_scarp_channels(data_dir)
    valid = ch["valid"] > 0
    peaks = h50.lidar_peaks(ch[channel], valid, threshold, min_distance)
    grids = read_grid(data_dir)
    peaks &= grids["footprint"] & ~grids["catalogue"]
    dcat = catalogue_distance(data_dir)
    return dict(near=peaks & (dcat <= near_px), far=peaks & (dcat > near_px),
                channel=channel, threshold=float(threshold),
                min_distance=int(min_distance), near_px=float(near_px))


def instrument_lidar_masked(data_dir: Path, *, channel: str, threshold: float,
                            min_distance: int) -> np.ndarray:
    """Off-catalogue lidar peaks restricted to noise-ok cells (H64 variant)."""
    ch = h50.lidar_scarp_channels(data_dir)
    valid = ch["valid"] > 0
    peaks = h50.lidar_peaks(ch[channel], valid, threshold, min_distance)
    grids = read_grid(data_dir)
    return peaks & grids["footprint"] & ~grids["catalogue"] & noise_ok(data_dir)
