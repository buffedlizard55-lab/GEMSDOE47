"""Deterministic spatial block folds with conservative block-level guards.

This utility creates split indices only. It does not score a model and cannot
substitute for the official competition metric or an authenticated label set.
"""
from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SpatialFold:
    """Point-level train/test masks and the held-out grid block identifiers."""

    fold: int
    train_mask: np.ndarray
    test_mask: np.ndarray
    heldout_blocks: tuple[tuple[int, int], ...]
    purged_blocks: tuple[tuple[int, int], ...]


def spatial_block_folds(
    xy: Sequence[Sequence[float]] | np.ndarray,
    *,
    block_size_m: float,
    guard_m: float = 300.0,
    n_folds: int = 5,
    seed: int = 47,
    origin_xy: tuple[float, float] | None = None,
) -> list[SpatialFold]:
    """Split point locations into spatial blocks and purge guard-adjacent blocks.

    Coordinates must be in a projected CRS whose units are meters. All points
    in a square cell go to the same fold. Training points in any cell within
    ``guard_m`` of a held-out cell's *rectangle* are purged, which is
    conservative relative to a point-to-point buffer and prevents the scoring
    support from reaching across the fold boundary. Use the competition's
    actual grid coordinates and lock ``seed``/parameters before evaluating.
    """
    coordinates = np.asarray(xy, dtype=np.float64)
    if coordinates.ndim != 2 or coordinates.shape[1] != 2:
        raise ValueError("xy must have shape (n_points, 2)")
    if coordinates.shape[0] == 0:
        raise ValueError("xy must contain at least one point")
    if not np.isfinite(coordinates).all():
        raise ValueError("xy contains non-finite coordinates")
    if not math.isfinite(block_size_m) or block_size_m <= 0:
        raise ValueError("block_size_m must be a positive finite value")
    if not math.isfinite(guard_m) or guard_m < 0:
        raise ValueError("guard_m must be a non-negative finite value")
    if isinstance(n_folds, bool) or not isinstance(n_folds, int) or n_folds < 2:
        raise ValueError("n_folds must be an integer of at least 2")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")

    if origin_xy is None:
        origin = coordinates.min(axis=0)
    else:
        origin = np.asarray(origin_xy, dtype=np.float64)
        if origin.shape != (2,) or not np.isfinite(origin).all():
            raise ValueError("origin_xy must contain finite x/y coordinates")
    block_xy = np.floor((coordinates - origin) / block_size_m).astype(np.int64)
    keys_array = [tuple(map(int, row)) for row in block_xy]
    unique_blocks = sorted(set(keys_array))
    if len(unique_blocks) < n_folds:
        raise ValueError(
            f"need at least {n_folds} distinct spatial blocks; found {len(unique_blocks)}"
        )

    shuffled = unique_blocks.copy()
    random.Random(seed).shuffle(shuffled)
    block_fold: dict[tuple[int, int], int] = {
        block: index % n_folds for index, block in enumerate(shuffled)
    }
    point_fold = np.asarray([block_fold[key] for key in keys_array], dtype=np.int64)
    folds: list[SpatialFold] = []

    for fold_index in range(n_folds):
        heldout = tuple(sorted(block for block in unique_blocks if block_fold[block] == fold_index))
        test_mask = point_fold == fold_index
        purged: set[tuple[int, int]] = set()
        for candidate in unique_blocks:
            if candidate in heldout:
                continue
            for test_block in heldout:
                dx = max(abs(candidate[0] - test_block[0]) - 1, 0) * block_size_m
                dy = max(abs(candidate[1] - test_block[1]) - 1, 0) * block_size_m
                if math.hypot(dx, dy) <= guard_m:
                    purged.add(candidate)
                    break
        train_mask = np.asarray(
            [key not in purged and block_fold[key] != fold_index for key in keys_array],
            dtype=bool,
        )
        if not test_mask.any():
            raise RuntimeError(f"fold {fold_index} has no test points")
        if not train_mask.any():
            raise ValueError(
                f"fold {fold_index} has no training points after the {guard_m:g} m guard purge; "
                "increase block size or reduce fold count before preregistration"
            )
        if np.any(train_mask & test_mask):
            raise RuntimeError("internal split error: train and test masks overlap")
        folds.append(
            SpatialFold(
                fold=fold_index,
                train_mask=train_mask,
                test_mask=test_mask,
                heldout_blocks=heldout,
                purged_blocks=tuple(sorted(purged)),
            )
        )
    return folds
