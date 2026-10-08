"""H65-H70 -- step-only / consensus lidar fields, the tip-proximity field, mask
ablation, and the H70 instrument study.

Preregistration
---------------
``docs/research/h65-hypotheses-preregistered.md`` (committed before any score in this
round was computed) freezes the fields, the blocked-holdout design, the instruments,
the controls and the promotion gate.  This module implements the frozen definitions
and nothing else; every deviation is recorded in the screen receipt.

What is scientifically new
--------------------------
1.  **H65** emits on the rank of the single ``step_max`` channel of the owner-derived
    1 m lidar scarp stack.  H64 measured masked step peaks as the population most
    rank-correlated with the owner-reported leaderboard ordering (+0.592); H60's
    max-of-six may dilute that channel with the noisiest ones (upface +0.328).
2.  **H66** emits on the per-cell *mean* of the six channel ranks (Borda consensus),
    re-ranked: the "corroborated evidence" pole opposite to H60's "any evidence" max.
3.  **H67** emits on catalogue-tip proximity -- rank of ``1/(1+d_tip)`` over the plain
    evaluated domain.  Fault systems grow at their tips; tips have zero shared code
    path with the lidar stack, so this arm carries no circularity warning.
4.  **H68/H69** recompute the H60 field definition over relaxed (road 150 m / claim
    100 m) and strict (road 400 m / claim 250 m) noise-mask domains.  H64 proved the
    masks help but the radii were never swept.
5.  **H70** extends the H64 instrument study to ``downface_max`` peaks, SGMC
    threshold/stratification variants, and the 21 INGENIOUS volcanic-vent pixels
    (exploratory diagnostic only).

Provenance limits (do not drop)
-------------------------------
* The lidar stack is **owner-derived** from USGS 3DEP 1 m DEM tiles, NOT
  organiser-supplied.  The primary lidar-peak instrument is therefore optimistic for
  the lidar-reading challengers (H65/H66/H68/H69); the preregistered gate carries an
  independent-instrument superiority condition on the SGMC off-catalogue population.
* H67 reads catalogue geometry only and is exempt from the circularity warning.
* The restored rasters are hash-pinned owner mirrors, not organiser-authenticated
  bytes, and the owner-reported public scores are not organiser receipts.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems47s3.geomorph import rank_scale

from . import h50, h60

#: H68 relaxed noise-mask radii (metres), frozen in the preregistration
H68_ROAD_M = 150.0
H68_CLAIM_M = 100.0
#: H69 strict noise-mask radii (metres), frozen in the preregistration
H69_ROAD_M = 400.0
H69_CLAIM_M = 250.0


# --------------------------------------------------------------------- masks
def noise_ok_rad(data_dir: Path, road_m: float, claim_m: float) -> np.ndarray:
    """True where the cell is >= road_m from a TIGER road and >= claim_m from a
    BLM closed mining claim (NaN distance = outside footprint -> False)."""
    with rasterio.open(Path(data_dir) / "external" / "audit_sources"
                       / "tiger_road_distance_m.tif") as src:
        road = src.read(1)
    with rasterio.open(Path(data_dir) / "external" / "audit_sources"
                       / "blm_closed_claim_distance_m.tif") as src:
        claim = src.read(1)
    ok = (np.nan_to_num(road, nan=-1.0) >= float(road_m)) & \
         (np.nan_to_num(claim, nan=-1.0) >= float(claim_m))
    return ok


def lidar_domain_rad(data_dir: Path, road_m: float, claim_m: float) -> np.ndarray:
    """Emission domain for a mask arm: evaluated & valid-lidar & noise-ok(radii)."""
    grids = h50.read_grid(data_dir)
    ch = h50.lidar_scarp_channels(data_dir)
    valid = ch["valid"] > 0
    del ch
    return grids["evaluated"] & valid & noise_ok_rad(data_dir, road_m, claim_m)


# -------------------------------------------------------------------- fields
def h65_field(data_dir: Path, mask: np.ndarray) -> np.ndarray:
    """H65: rank_scale of the step_max channel alone over the emission domain."""
    ch = h50.lidar_scarp_channels(data_dir)
    step = np.asarray(ch["step_max"], np.float32)
    del ch
    field = rank_scale(np.where(mask, step, np.nan))
    return np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)


def h66_field(data_dir: Path, mask: np.ndarray) -> np.ndarray:
    """H66: rank_scale of the per-cell mean of the six channel ranks."""
    ch = h50.lidar_scarp_channels(data_dir)
    acc = np.zeros(mask.shape, np.float64)
    for name in h60.H60_CHANNELS:
        acc += rank_scale(np.where(mask, ch[name], np.nan)).astype(np.float64)
    del ch
    acc /= float(len(h60.H60_CHANNELS))
    field = rank_scale(np.where(mask, acc, np.nan))
    return np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)


def h60_field_on(data_dir: Path, mask: np.ndarray) -> np.ndarray:
    """The H60 field definition recomputed over an arbitrary emission domain.

    Identical to ``h60.h60_field`` (channel-rank maximum, re-ranked); the mask
    argument is the arm's own domain.  Recomputation -- not reuse of H60's values --
    is required for H68 because the relaxed domain contains cells H60 never ranked.
    """
    return h60.h60_field(data_dir, mask)


def tip_pixels(catalogue: np.ndarray) -> np.ndarray:
    """Catalogue pixels with exactly one catalogue neighbour in 8-connectivity.

    Isolated single-pixel components have zero neighbours and are not tips, by the
    frozen definition.
    """
    cat = np.asarray(catalogue, bool)
    nbr = ndi.convolve(cat.astype(np.int8), np.ones((3, 3), np.int8),
                       mode="constant", cval=0) - cat.astype(np.int8)
    return cat & (nbr == 1)


def tip_distance(data_dir: Path) -> np.ndarray:
    """Euclidean distance (px) to the nearest catalogue-tip pixel."""
    with rasterio.open(Path(data_dir) / "labels.tif") as src:
        catalogue = src.read(1) == 1
    return ndi.distance_transform_edt(~tip_pixels(catalogue))


def h67_field(data_dir: Path, mask: np.ndarray) -> np.ndarray:
    """H67: rank_scale of 1/(1+d_tip) over the emission domain (tip proximity)."""
    d = tip_distance(data_dir).astype(np.float64)
    prox = 1.0 / (1.0 + d)
    field = rank_scale(np.where(mask, prox, np.nan))
    return np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)


# ------------------------------------------------------- H70 instrument pops
def instrument_sgmc_threshold(data_dir: Path, dist_px: float) -> np.ndarray:
    """SGMC fault pixels off the catalogue and farther than dist_px from it."""
    with rasterio.open(Path(data_dir) / "external"
                       / "derived_sgmc_faults_100m_u8.tif") as src:
        sgmc = src.read(1) > 0
    with rasterio.open(Path(data_dir) / "labels.tif") as src:
        catalogue = src.read(1) == 1
    with rasterio.open(Path(data_dir) / "sample_submission.tif") as src:
        footprint = np.isfinite(src.read(1))
    dc = ndi.distance_transform_edt(~catalogue)
    return sgmc & footprint & ~catalogue & (dc > float(dist_px))


def instrument_sgmc_near(data_dir: Path, near_px: float = 3.0) -> np.ndarray:
    """SGMC fault pixels off the catalogue but within near_px of it."""
    with rasterio.open(Path(data_dir) / "external"
                       / "derived_sgmc_faults_100m_u8.tif") as src:
        sgmc = src.read(1) > 0
    with rasterio.open(Path(data_dir) / "labels.tif") as src:
        catalogue = src.read(1) == 1
    with rasterio.open(Path(data_dir) / "sample_submission.tif") as src:
        footprint = np.isfinite(src.read(1))
    dc = ndi.distance_transform_edt(~catalogue)
    return sgmc & footprint & ~catalogue & (dc <= float(near_px))


def volcanic_vent_pixels(data_dir: Path, nrows: int, ncols: int) -> np.ndarray:
    """Boolean mask of the INGENIOUS volcanic-vent pixels (exploratory, n = 21).

    Rows/cols come from the pinned ``ext_gdr_volcanic_vents_in_footprint`` CSV;
    out-of-grid entries raise rather than silently dropping vents.
    """
    path = Path(data_dir) / "external" / "gdr_volcanic_vents_in_footprint.csv"
    mask = np.zeros((nrows, ncols), bool)
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            r, c = int(float(row["row"])), int(float(row["col"]))
            if not (0 <= r < nrows and 0 <= c < ncols):
                raise ValueError(f"vent pixel out of grid: row={r} col={c}")
            mask[r, c] = True
    return mask
