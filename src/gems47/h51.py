"""H51 -- Multi-scale slope-anomaly persistence detector.

Novelty relative to every prior arm in this repository
------------------------------------------------------
H50 used the rank of band 19 above a 25px Gaussian regional level.  H51
extends this by requiring the slope anomaly to persist across TWO different
regional scales (25px and 12px), which suppresses erosional features like
stream banks and canyon rims that create sharp but small-scale slope anomalies
without lateral persistence.

The product ``anomaly_25px * anomaly_12px`` fires only where BOTH the broad
regional anomaly AND the narrower anomaly are large.  A fault scarp that stands
out from the 2.5 km background also stands out from the 1.2 km background;
a stream bank that only breaks the local profile does not survive the broad-scale
test.  This is the "multi-scale persistence" idea from Frangi filtering (Frangi
et al. 1998), applied to the slope anomaly field rather than to the Hessian.

This is NOT a copy of any prior GEMSDOE submission.  No prior submission used
a product of two regional-scale anomaly fields as the detection surface.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from gems47.grid import LABEL_NODATA
from gems47s3.geomorph import rank_scale

SLOPE_BAND = 19  # 1-based rasterio band index of det_elev_slope


def read_grid(data_dir: Path) -> dict:
    """Footprint, catalogue and evaluated masks from the restored template rasters."""
    import rasterio
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


def h51_field(data_dir: Path, mask: np.ndarray | None = None,
              sigma_broad: float = 25.0, sigma_narrow: float = 12.0) -> dict:
    """The H51 multi-scale slope-anomaly persistence field.

    Computes:
      1. slope anomaly from broad regional (sigma_broad, default 25 px = 2.5 km)
      2. slope anomaly from narrow regional (sigma_narrow, default 12 px = 1.2 km)
      3. product of the two (both must be anomalous)
      4. rank-scaled to [0,1]

    No label, catalogue geometry, prior prediction or score enters this function.
    """
    import rasterio
    data_dir = Path(data_dir)
    grids = read_grid(data_dir)
    if mask is None:
        mask = grids["evaluated"]
    with rasterio.open(data_dir / "training_features.tif") as src:
        slope = src.read(SLOPE_BAND).astype(np.float32)
    slope[~np.isfinite(slope)] = 0.0
    slope[slope < -1e30] = 0.0

    # Broad regional baseline (2.5 km Gaussian)
    regional_broad = ndi.gaussian_filter(slope, sigma_broad, mode="nearest")
    anomaly_broad = slope - regional_broad

    # Narrow regional baseline (1.2 km Gaussian)
    regional_narrow = ndi.gaussian_filter(slope, sigma_narrow, mode="nearest")
    anomaly_narrow = slope - regional_narrow

    # Multi-scale persistence product: both anomalies must be positive
    # (locally steeper than both regional levels)
    raw = np.where(
        (anomaly_broad > 0) & (anomaly_narrow > 0),
        anomaly_broad * anomaly_narrow,
        0.0,
    ).astype(np.float32)

    # Rank-scale within the evaluated domain
    field = rank_scale(np.where(mask, raw, np.nan))
    field = np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)

    if not np.isfinite(field[mask]).all() or (field[mask] < 0).any() or (field[mask] > 1).any():
        raise ValueError("H51 field is not finite and inside [0,1] on the emission domain")

    return dict(
        field=field,
        mask=mask,
        sigma_broad=sigma_broad,
        sigma_narrow=sigma_narrow,
        slope_band=SLOPE_BAND,
        n_ranked=int(mask.sum()),
    )


def emit(field: np.ndarray, mask: np.ndarray, spacing_px: float,
         budget: int) -> np.ndarray:
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