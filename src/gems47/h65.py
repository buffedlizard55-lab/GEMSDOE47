"""H65-H68 -- session-6 hypothesis slate: scarp consensus, far-field, alteration
corroboration, and the extended-channel lidar field.

Preregistration
---------------
``docs/research/h65-hypotheses-preregistered.md`` (committed before any score in this
round was computed) freezes the fields, the blocked-holdout design, the instruments,
the controls, the conformal operating-point rule and the promotion gate.  This module
implements the frozen definitions and nothing else; every deviation is recorded in the
screen receipt.

The slate (ranked by expected DTI improvement x implementation cost in the
preregistration)
------------------------------------------------------------------------------------------
* **H65 scarp-consensus field.**  Per cell, the count of the six H60 lidar channels
  whose amplitude exceeds its frozen instrument threshold, ranked lexicographically
  (count descending, then the H60 channel-rank-max descending as the amplitude
  tie-break).  H60's per-cell MAX lets one noisy operator spend the budget; consensus
  requires independent operators to agree at the same cell.
* **H66 far-field lidar field.**  The H60 field restricted to cells more than 3 px
  (one metric-kernel radius) from every catalogue pixel -- the unmapped-system pole
  that H63's refuted near-gate was the opposite of, and that H64 measured correlating
  better with the 13 owner-reported scores (lappos +0.581 far vs +0.273 near).
* **H67 alteration-corroborated lidar field.**  Additive 50/50 rank mixture (the H62
  mechanism, lambda frozen at 0.5) of the H60 lidar field and the rank of the USGS
  GeoDAWN contractor Th/K ratio grid.  Hydrothermal alteration leaches (argillic) or
  adds (potassic) potassium, so Th/K is the standard airborne-radiometric alteration
  index; a scarp coincident with an alteration high is a sealed fluid conduit -- the
  hidden geothermal vent the competition rewards.  GeoDAWN was flown by USGS/DOE for
  undiscovered geothermal resources over this footprint.
* **H68 extended-channel lidar field.**  The H60 rank-max mechanism over eight
  amplitude channels: H60's six plus ``ex_max`` (max 2 m slope in excess of the 30 m
  regional slope) and ``relief`` (local relief).  ``coh100`` is excluded (H64 measured
  it anti-correlating, -0.532); ``strike``/``ex_mean`` are not max-amplitudes.

Provenance limits (do not drop)
-------------------------------
* The lidar stack is **owner-derived** from USGS 3DEP 1 m DEM tiles (706/716; work
  resolution 2 m; per-channel meanings pinned in GEMSDOE24
  ``data/external/lidar_scarp_features.json``), NOT organiser-supplied.  USGS 3DEP
  products carry no use restrictions.
* The GeoDAWN Th/K grid is a contractor product of the USGS GeoDAWN release
  (DOI 10.5066/P93LGLVQ); bytes are u8 ranks over the 1st-99th percentiles, not
  physical units; 0 = nodata.  USGS data release; retain attribution.
* The restored rasters are hash-pinned owner mirrors, not organiser-authenticated
  bytes, and the owner-reported public scores are not organiser receipts.
* The primary lidar-peak instrument shares its terrain modality with every
  lidar-reading field (H60, H65, H66, H68); their primary-instrument numbers are
  optimistic by construction.  H67's Th/K component and the SGMC off-catalogue
  population are independent of it.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems47s3.geomorph import rank_scale

from . import h50, h60

#: the eight amplitude channels of H68 (H60's frozen six + ex_max + relief)
H68_CHANNELS = h60.H60_CHANNELS + ("ex_max", "relief")

#: per-channel consensus thresholds (frozen): the instrument thresholds of the H50/H60
#: screens -- t200 for the band-passed channels, t150 for step_max
H65_THRESHOLDS = {"step_max": 150.0, "lappos_max": 200.0, "lapneg_max": 200.0,
                  "upface_max": 200.0, "downface_max": 200.0, "cross_max": 200.0}

#: H66 far-field radius: cells farther than this (px) from every catalogue pixel.
#: 3 px = 300 m = the metric's own kernel support (RADIUS_PX); the same near/far split
#: the H64 instrument refinement used.
H66_FAR_RADIUS_PX = 3.0

#: H67 mixture weight (additive; frozen at 1/2, the H62 mechanism)
H67_LAMBDA = 0.5

#: band name of the Th/K ratio grid inside external/geodawn_extensions_u8.tif
H67_THK_BAND = "ThK"


# --------------------------------------------------------------------- io
def read_grid(data_dir: Path) -> dict:
    """Footprint / catalogue / evaluated masks (same contract as ``h50.read_grid``)."""
    return h50.read_grid(data_dir)


def thk_ratio(data_dir: Path) -> np.ndarray:
    """The USGS GeoDAWN contractor Th/K ratio grid as float32 (0 = nodata).

    Band order and quantisation are pinned by ``external/geodawn_extensions.json``
    (u8 ranks over each source channel's finite in-footprint 1st..99th percentiles;
    bytes are ranks, not physical units).  The rank transform used downstream is
    monotone in the u8 code, so ranking the code is ranking the ratio.
    """
    path = Path(data_dir) / "external" / "geodawn_extensions_u8.tif"
    with rasterio.open(path) as src:
        names = list(src.descriptions)
        if H67_THK_BAND not in names:
            raise ValueError(f"geodawn extensions stack lacks band {H67_THK_BAND!r}")
        return src.read(names.index(H67_THK_BAND) + 1).astype(np.float32)


# ------------------------------------------------------------------ domains
def h60_domain(data_dir: Path) -> np.ndarray:
    """The H60 emission domain (evaluated & valid-lidar & road/claim noise-ok)."""
    return h60.h60_emission_domain(data_dir)


def h66_domain(data_dir: Path, base: np.ndarray | None = None) -> np.ndarray:
    """H66 emission domain: the H60 domain AND farther than 3 px from the catalogue."""
    grids = read_grid(data_dir)
    dcat = ndi.distance_transform_edt(~grids["catalogue"])
    base = h60_domain(data_dir) if base is None else base
    return base & (dcat > H66_FAR_RADIUS_PX)


def h67_domain(data_dir: Path, base: np.ndarray | None = None) -> np.ndarray:
    """H67 emission domain: the H60 domain AND valid (non-nodata) Th/K."""
    base = h60_domain(data_dir) if base is None else base
    return base & (thk_ratio(data_dir) > 0)


# ------------------------------------------------------------------ fields
def _lexicographic_rank(keys_desc: tuple[np.ndarray, ...], mask: np.ndarray) -> np.ndarray:
    """Tie-free rank in (0,1] over ``mask``; ``keys_desc`` are descending-sort keys,
    the FIRST key primary.  Returns 0 outside ``mask``."""
    out = np.zeros(mask.shape, np.float32)
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return out
    # np.lexsort uses the LAST key as primary, so reverse the key order
    order = np.lexsort(tuple(-k[ys, xs] for k in reversed(keys_desc)))
    r = (np.arange(1, ys.size + 1, dtype=np.float64) / float(ys.size)).astype(np.float32)
    out[ys[order], xs[order]] = r
    return out


def h65_consensus(data_dir: Path, mask: np.ndarray | None = None) -> dict:
    """H65: amplitude-tie-broken consensus count of the six scarp channels.

    ``consensus[y, x] = number of channels c with channel_c[y, x] > threshold_c``;
    the field is the lexicographic rank of (consensus desc, H60 channel-rank-max
    desc) over the emission domain.  No label, catalogue geometry, prior prediction
    or score enters this function.
    """
    data_dir = Path(data_dir)
    ch = h50.lidar_scarp_channels(data_dir)
    valid = ch["valid"] > 0
    if mask is None:
        mask = h60_domain(data_dir)
    mask = mask & valid
    consensus = np.zeros(mask.shape, np.int32)
    for name, thr in H65_THRESHOLDS.items():
        if name not in ch:
            raise ValueError(f"lidar scarp stack lacks channel {name!r}")
        consensus += (ch[name] > float(thr)).astype(np.int32)
    amp = h60.channel_rank_max(data_dir, mask)
    field = _lexicographic_rank((consensus.astype(np.float64), amp.astype(np.float64)), mask)
    if not np.isfinite(field[mask]).all() or (field[mask] <= 0).any() or (field[mask] > 1).any():
        raise ValueError("H65 field is not finite and inside (0,1] on the emission domain")
    return dict(field=field, mask=mask,
                counts={int(k): int(v) for k, v in zip(*np.unique(consensus[mask],
                                                                   return_counts=True))},
                n_channels=len(H65_THRESHOLDS))


def h66_field(data_dir: Path, mask: np.ndarray | None = None) -> dict:
    """H66: the H60 field restricted to the far-from-catalogue domain.

    Same field values as H60; only the emission domain differs (cells farther than
    ``H66_FAR_RADIUS_PX`` from every catalogue pixel).  The catalogue is a *given*
    training input (``existing_faults.tif``); the scoring domain masks it out of
    evaluation, and nothing here reads any hidden label.
    """
    data_dir = Path(data_dir)
    if mask is None:
        mask = h66_domain(data_dir)
    base = h60.h60_field(data_dir, h60_domain(data_dir))
    field = np.where(mask, base, 0.0).astype(np.float32)
    if not np.isfinite(field[mask]).all() or (field[mask] <= 0).any() or (field[mask] > 1).any():
        raise ValueError("H66 field is not finite and inside (0,1] on the emission domain")
    return dict(field=field, mask=mask)


def h67_field(data_dir: Path, mask: np.ndarray | None = None) -> dict:
    """H67: additive 50/50 rank mixture of the H60 lidar field and the Th/K rank.

    Structure (lidar scarp amplitude) + fossil heat (radiometric alteration).  The
    mixture weight is frozen at 0.5 (the H62 mechanism).  No label, catalogue
    geometry, prior prediction or score enters this function.
    """
    data_dir = Path(data_dir)
    if mask is None:
        mask = h67_domain(data_dir)
    h60f = h60.h60_field(data_dir, h60_domain(data_dir))
    thk = thk_ratio(data_dir)
    mix = (H67_LAMBDA * h60f
           + (1.0 - H67_LAMBDA) * rank_scale(np.where(mask, thk, np.nan)).astype(np.float32))
    field = rank_scale(np.where(mask, mix, np.nan))
    field = np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)
    if not np.isfinite(field[mask]).all() or (field[mask] <= 0).any() or (field[mask] > 1).any():
        raise ValueError("H67 field is not finite and inside (0,1] on the emission domain")
    return dict(field=field, mask=mask, lambda_=H67_LAMBDA, thk_band=H67_THK_BAND)


def h68_field(data_dir: Path, mask: np.ndarray | None = None) -> dict:
    """H68: rank-max over the eight amplitude channels (H60's six + ex_max + relief)."""
    data_dir = Path(data_dir)
    ch = h50.lidar_scarp_channels(data_dir)
    valid = ch["valid"] > 0
    if mask is None:
        mask = h60_domain(data_dir)
    mask = mask & valid
    acc = np.zeros(mask.shape, np.float32)
    for name in H68_CHANNELS:
        if name not in ch:
            raise ValueError(f"lidar scarp stack lacks channel {name!r}")
        r = rank_scale(np.where(mask, ch[name], np.nan)).astype(np.float32)
        np.maximum(acc, r, out=acc)
    field = rank_scale(np.where(mask, acc, np.nan))
    field = np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)
    if not np.isfinite(field[mask]).all() or (field[mask] <= 0).any() or (field[mask] > 1).any():
        raise ValueError("H68 field is not finite and inside (0,1] on the emission domain")
    return dict(field=field, mask=mask, channels=list(H68_CHANNELS))


def build_all(data_dir: Path) -> dict:
    """Build every arm's field + domain once (the screen crops per block)."""
    data_dir = Path(data_dir)
    base = h60_domain(data_dir)
    dom66 = h66_domain(data_dir, base)
    dom67 = h67_domain(data_dir, base)
    return {
        "h65": h65_consensus(data_dir, base),
        "h66": h66_field(data_dir, dom66),
        "h67": h67_field(data_dir, dom67),
        "h68": h68_field(data_dir, base),
        "domains": {"h60": int(base.sum()), "h66": int(dom66.sum()),
                    "h67": int(dom67.sum())},
    }
