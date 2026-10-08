"""H65: paired LiDAR scarp morphology consensus.

This is an exploratory transform over the owner's hash-pinned, 2 m-derived LiDAR
scarp descriptor raster. It uses the frozen H60 emission domain and three
orientation-insensitive channel ranks: localized slope step, crest convexity, and
base concavity. Unlike H60's maximum-over-channels rule, H65 requires evidence in
all three channels. It is a geological hypothesis, not a fault classifier or
organizer-authenticated input.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from gems47s3.geomorph import rank_scale

from . import h50

H65_CHANNELS = ("step_max", "lapneg_max", "lappos_max")


def paired_morphology_score(step: np.ndarray, lapneg: np.ndarray,
                            lappos: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Return an empirical-rank consensus field on ``valid``.

    Each input is ranked independently over the valid domain. The cube root of the
    product is the geometric mean, so a high value in only one channel cannot
    dominate the consensus. The final field is re-ranked on the same domain for a
    deterministic, tie-free ordering. Cells outside the mask are exactly zero.

    The input channel scales need only be ordinally meaningful; H65's pinned input
    channels are monotone uint8 quantisations of nonnegative descriptors.
    """
    arrays = tuple(np.asarray(a, dtype=np.float32) for a in (step, lapneg, lappos))
    mask = np.array(valid, dtype=bool, copy=True)
    if mask.ndim != 2 or any(a.ndim != 2 or a.shape != mask.shape for a in arrays):
        raise ValueError("H65 channels and validity mask must be same-shaped 2-D arrays")
    mask &= np.logical_and.reduce(tuple(np.isfinite(a) for a in arrays))
    if int(mask.sum()) < 100:
        raise ValueError("H65 requires at least 100 finite in-domain cells to rank")

    ranks = [rank_scale(np.where(mask, a, np.nan)) for a in arrays]
    product = (ranks[0].astype(np.float64)
               * ranks[1].astype(np.float64)
               * ranks[2].astype(np.float64))
    consensus = np.cbrt(product).astype(np.float32)
    field = rank_scale(np.where(mask, consensus, np.nan))
    return np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)


def paired_morphology_field(data_dir: Path, emission_domain: np.ndarray) -> np.ndarray:
    """Build the H65 field from the hash-pinned LiDAR descriptor stack.

    ``emission_domain`` is supplied by the caller (the fixed H60 domain in this
    round). The stack's ``valid`` channel is intersected again here so callers
    cannot accidentally rank invalid LiDAR cells.
    """
    channels = h50.lidar_scarp_channels(Path(data_dir))
    domain = np.array(emission_domain, dtype=bool, copy=True)
    if domain.shape != channels["valid"].shape:
        raise ValueError("H65 emission domain does not match LiDAR stack grid")
    domain &= channels["valid"] > 0
    return paired_morphology_score(
        channels["step_max"], channels["lapneg_max"], channels["lappos_max"], domain
    )
