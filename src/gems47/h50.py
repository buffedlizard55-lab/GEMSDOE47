"""H50 -- the off-catalogue lidar-scarp instrument and the acquisition-block slope field.

Why this module exists
----------------------
Every fault-population proxy available in this repository (the given USGS/INGENIOUS
catalogue, the SGMC compilation, the GDR QFaults traces) is either *masked out of the
official evaluation* or *biased toward exposed mountain bedrock*.  Measured on the 13
owner-reported public-score artifacts that are restored in this checkout, the rank
correlation between the reported score and DTI computed against those populations is
**negative** for every one of them:

    catalogue                spearman -0.490      (these pixels are masked out)
    sgmc_offcat              spearman -0.421
    sgmc_all                 spearman -0.421
    iso_catalogue            spearman -0.272
    flank_catalogue          spearman -0.424
    cat + sgmc_offcat        spearman -0.534
    sgmc_offcat or iso       spearman -0.553

The only population with a **positive** rank correlation is the set of *local maxima of the
organiser-supplied 1 m lidar scarp-detection stack that lie off the catalogue*
(``Instrument L``): spearman +0.377 for the union of six scarp channels at threshold 200 /
min-distance 3, and +0.26 ... +0.58 across ~25 other parameterisations of the same idea
(``evidence/h50/instrument-l-ranking.json``).  Those points are real, independently measured
scarps that the catalogue does not contain, so a 100 m-scale field that predicts them is
detecting unmapped fault scarps rather than reproducing the masked catalogue.

Two independent 100 m-scale fields were then scanned against Instrument L with the real
spaced emission (``evidence/h50/field-scan.json``).  The acquisition-block-normalised rank of
official band 19 (``det_elev_slope``) is the best single field, and *every* multiplicative
corroboration with a magnetic, gravity, geodetic, curvature or ruggedness term makes it
worse.  That is the contrarian result of this round: for the off-catalogue scarp population
the family's multi-physics AND-gate discards exactly the steep scarps the lidar finds.

What is new here, relative to every prior arm in this repository
---------------------------------------------------------------
1.  ``Instrument L`` itself.  No prior arm used the 1 m lidar scarp stack as a *truth*
    population; it was used only as a feature source, and the repo's own session-3 notes
    rejected SGMC for selection while never testing the lidar peaks.
2.  ``block_rank``: the rank of a band is normalised *within each GeoDAWN acquisition
    block* (``external/audit_sources/acquisition_block_id_100m.tif``) instead of globally.
    Slope statistics differ between flight blocks, so a global rank lets one rugged block
    monopolise the emission budget.  No prior arm normalised by acquisition block.
3.  ``expected_kernel_profile``: the budget is chosen from the metric's own credit bar
    (``w > alpha * DTI``, derived in ``gems47s3.metric.credit_bar``) rather than by
    eyeballing a leaderboard mass.

Provenance limits (do not drop these)
-------------------------------------
* The restored rasters are hash-pinned owner mirrors, not organiser-authenticated bytes.
* Instrument L is *derived from a lidar product that shares a physical quantity (slope) with
  band 19*.  It is therefore an optimistic instrument for a slope field.  The SGMC
  off-catalogue instrument (``truth_sgmc_offcatalogue``) is reported alongside it as a
  second, independent check.
* A positive rank correlation over 13 artifacts is not a certified leaderboard score, and
  no private-label guarantee is claimed anywhere in this module.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from .grid import LABEL_NODATA

# --- the official band that carries the 300 m structure -------------------------
# evidence/band_scale_diagnostics.json: det_elev_slope has the largest high-frequency
# variance fraction of all 19 bands (0.181) and is one of only three bands with any
# structure above the metric's 3 px kernel support.
SLOPE_BAND = 19          # 1-based rasterio band index of det_elev_slope
ELEVATION_BAND = 12      # 1-based rasterio band index of det_elev

# --- the lidar scarp channels whose local maxima form Instrument L ---------------
LIDAR_SCARP_CHANNELS = ("step_max", "lappos_max", "lapneg_max",
                        "downface_max", "upface_max", "cross_max")
LIDAR_PEAK_THRESHOLD = 200      # uint8 amplitude threshold on each channel
LIDAR_PEAK_MIN_DISTANCE = 3     # px; 300 m, the metric's own kernel support
LIDAR_VALID_CHANNEL = "valid"

# --- emission -------------------------------------------------------------------
DEFAULT_SPACING_PX = 2.8
DEFAULT_BUDGET = 37_654

CATALOGUE_BUFFER_PX = 0   # measured on Instrument L: 0 px is best; see evidence/h50


# --------------------------------------------------------------------------- io
def read_grid(data_dir: Path) -> dict:
    """Footprint, catalogue and evaluated masks from the restored template rasters."""
    data_dir = Path(data_dir)
    with rasterio.open(data_dir / "labels.tif") as src:
        labels = src.read(1)
    with rasterio.open(data_dir / "sample_submission.tif") as src:
        sample = src.read(1)
    footprint = np.isfinite(sample)
    catalogue = labels == 1
    if not np.array_equal(footprint, labels != LABEL_NODATA):
        raise AssertionError("labels footprint != sample_submission finite mask")
    return dict(footprint=footprint, catalogue=catalogue,
                evaluated=footprint & ~catalogue)


def acquisition_blocks(data_dir: Path) -> np.ndarray:
    """GeoDAWN acquisition-block id per 100 m cell (0 = outside any block)."""
    with rasterio.open(Path(data_dir) / "external" / "audit_sources"
                       / "acquisition_block_id_100m.tif") as src:
        return src.read(1)


def lidar_scarp_channels(data_dir: Path) -> dict[str, np.ndarray]:
    """The 12 organiser-supplied 1 m lidar scarp channels as float32 on the grid."""
    path = Path(data_dir) / "external" / "lidar_scarp_features_u8.tif"
    with rasterio.open(path) as src:
        names = list(src.descriptions)
        if LIDAR_VALID_CHANNEL not in names:
            raise ValueError("lidar scarp stack has no 'valid' channel")
        out = {nm: src.read(i + 1).astype(np.float32) for i, nm in enumerate(names)}
    return out


# ------------------------------------------------------------------- instruments
def lidar_peaks(channel: np.ndarray, valid: np.ndarray, threshold: float,
                min_distance: int) -> np.ndarray:
    """Local maxima of one lidar scarp channel at ``min_distance`` separation.

    Implemented with a maximum filter plus a greedy descending-amplitude sweep so the
    production path carries no extra dependency.  ``tests/test_h50.py`` checks it against
    ``skimage.feature.peak_local_max`` when scikit-image is importable and records the
    (small, documented) difference in the peak count.
    """
    a = np.where(np.asarray(valid, bool), np.asarray(channel, np.float32), 0.0)
    size = 2 * int(min_distance) + 1
    mx = ndi.maximum_filter(a, size=size, mode="constant")
    hit = (a >= mx) & (a > float(threshold))
    mask = np.zeros(a.shape, bool)
    if not hit.any():
        return mask
    ys, xs = np.nonzero(hit)
    order = np.argsort(-a[ys, xs], kind="stable")
    taken = np.zeros(a.shape, bool)
    r = int(min_distance)
    for i in order:
        y, x = int(ys[i]), int(xs[i])
        y0, y1 = max(0, y - r), min(a.shape[0], y + r + 1)
        x0, x1 = max(0, x - r), min(a.shape[1], x + r + 1)
        if taken[y0:y1, x0:x1].any():
            continue
        taken[y, x] = True
        mask[y, x] = True
    return mask


def instrument_l(data_dir: Path, *, threshold: float = LIDAR_PEAK_THRESHOLD,
                 min_distance: int = LIDAR_PEAK_MIN_DISTANCE,
                 channels: tuple[str, ...] = LIDAR_SCARP_CHANNELS) -> dict:
    """Off-catalogue local maxima of the 1 m lidar scarp stack (Instrument L).

    The peaks are local maxima of each scarp-amplitude channel at a 300 m minimum
    separation, restricted to valid lidar cells, inside the footprint and off the
    catalogue.  Nothing here reads ``labels.tif`` except to *remove* catalogue pixels,
    exactly as the organiser masks them.
    """
    ch = lidar_scarp_channels(data_dir)
    valid = ch[LIDAR_VALID_CHANNEL] > 0
    peaks = np.zeros(valid.shape, bool)
    per_channel = {}
    for name in channels:
        if name not in ch:
            raise ValueError(f"lidar scarp stack lacks channel {name!r}")
        mask = lidar_peaks(ch[name], valid, threshold, min_distance)
        per_channel[name] = int(mask.sum())
        peaks |= mask
    grids = read_grid(data_dir)
    peaks &= grids["footprint"] & ~grids["catalogue"]
    return dict(mask=peaks, per_channel=per_channel, threshold=float(threshold),
                min_distance=int(min_distance), channels=list(channels),
                n_peaks=int(peaks.sum()))


def instrument_sgmc_offcatalogue(data_dir: Path) -> np.ndarray:
    """SGMC fault pixels off the catalogue and >300 m from it (Instrument B)."""
    with rasterio.open(Path(data_dir) / "external"
                       / "derived_sgmc_faults_100m_u8.tif") as src:
        sgmc = src.read(1) > 0
    with rasterio.open(Path(data_dir) / "labels.tif") as src:
        catalogue = src.read(1) == 1
    with rasterio.open(Path(data_dir) / "sample_submission.tif") as src:
        footprint = np.isfinite(src.read(1))
    dc = ndi.distance_transform_edt(~catalogue)
    return sgmc & footprint & ~catalogue & (dc > 3)


# ----------------------------------------------------------------- the H50 field
def block_rank(values: np.ndarray, blocks: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Rank of ``values`` normalised *within each acquisition block*.

    Returns 0 outside ``mask``.  The rank is the fraction of in-mask pixels in the same
    block with a strictly smaller value, so the result is in (0, 1] and has no ties
    (ties are broken by raster index through a stable argsort).
    """
    v = np.asarray(values, np.float32)
    b = np.asarray(blocks)
    m = np.asarray(mask, bool)
    if v.shape != b.shape or v.shape != m.shape:
        raise ValueError("values, blocks and mask must be same-shaped")
    out = np.zeros(v.shape, np.float32)
    for block_id in np.unique(b):
        sel = m & (b == block_id)
        if not sel.any():
            continue
        idx = np.flatnonzero(sel.ravel())
        vals = v.ravel()[idx]
        order = np.argsort(vals, kind="stable")
        r = np.empty(idx.size, np.float32)
        r[order] = (np.arange(1, idx.size + 1, dtype=np.float64) / float(idx.size)).astype(np.float32)
        out.ravel()[idx] = r
    return out


def h50_field(data_dir: Path, mask: np.ndarray | None = None) -> dict:
    """The H50 detector field: acquisition-block-normalised rank of band 19.

    No label, catalogue geometry, prior prediction or score enters this function.  The
    only inputs are the official 19-band raster and the acquisition-block id raster.
    """
    data_dir = Path(data_dir)
    grids = read_grid(data_dir)
    if mask is None:
        mask = grids["evaluated"]
    blocks = acquisition_blocks(data_dir)
    with rasterio.open(data_dir / "training_features.tif") as src:
        slope = src.read(SLOPE_BAND).astype(np.float32)
    slope[~np.isfinite(slope)] = 0.0
    slope[slope < -1e30] = 0.0
    field = block_rank(slope, blocks, mask)
    if not np.isfinite(field[mask]).all() or (field[mask] < 0).any() or (field[mask] > 1).any():
        raise ValueError("H50 field is not finite and inside [0,1] on the emission domain")
    return dict(field=field, mask=mask, slope_band=SLOPE_BAND,
                n_blocks=int(len(np.unique(blocks))), n_ranked=int(mask.sum()))


# ---------------------------------------------------------------------- emission
def emit(field: np.ndarray, mask: np.ndarray, spacing_px: float, budget: int) -> np.ndarray:
    """Greedy top-ranked selection at a minimum Euclidean spacing (unit dots)."""
    from gemsdoe47.magnetic import greedy_spaced_pixels, ranked_pixels

    f = np.where(mask, np.nan_to_num(np.asarray(field, np.float32), nan=0.0), 0.0)
    order = ranked_pixels(f, mask)
    selected = greedy_spaced_pixels(order, f.shape, min_separation_px=spacing_px, budget=budget)
    p = np.zeros(f.shape, np.float32)
    p.ravel()[selected] = 1.0
    if int(p.sum()) != int(budget) or (p[~mask] != 0).any():
        raise ValueError("emission contract failed")
    return p


def expected_kernel_profile(field: np.ndarray, mask: np.ndarray, truth: np.ndarray,
                            budgets: tuple[int, ...]) -> list[dict]:
    """Mean realised kernel weight of the emitted dots at each budget.

    The metric's credit bar is ``w > alpha * DTI`` (``gems47s3.metric.credit_bar``): a
    unit of mass pays for itself exactly when its realised kernel weight exceeds
    ``alpha * DTI``.  This profile therefore locates the budget at which the marginal dot
    stops paying, without reference to any leaderboard observation.
    """
    from gems47s3.metric import dti

    rows = []
    f = np.where(mask, np.nan_to_num(np.asarray(field, np.float32), nan=0.0), 0.0)
    kappa = _nearest_truth_kernel(truth)
    for budget in sorted(budgets):
        p = emit(f, mask, DEFAULT_SPACING_PX, budget)
        sel = p > 0
        r = dti(p, truth.astype(np.int8), valid=mask)
        rows.append(dict(budget=int(budget), dti=float(r["dti"]), tp=float(r["tp"]),
                         fp=float(r["fp"]), n_truth=int(r["n_truth"]),
                         mean_kernel_weight=float(kappa[sel].mean()),
                         credit_bar=float(0.2 * r["dti"]),
                         marginal_pays=bool(float(kappa[sel].mean()) > 0.2 * r["dti"])))
    return rows


def _nearest_truth_kernel(truth: np.ndarray) -> np.ndarray:
    """kappa(x) = max over truth pixels g of k(d(x,g)), the triangular 300 m kernel."""
    from gems47s3.metric import kernel

    d = ndi.distance_transform_edt(~np.asarray(truth, bool))
    return kernel(d)
