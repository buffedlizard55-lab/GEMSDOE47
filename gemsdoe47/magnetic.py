"""Cross-scale magnetic-edge screening and guarded block evaluation.

The functions here operate on feature fields, not official fault probabilities.
They are deterministic so that a pinned input raster and parameter set reproduce
identical candidate masks and receipts.
"""
from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from scipy import ndimage

from src.gems47_metric import dti


def magnetic_edge_persistence(
    rank_field: Any,
    valid_mask: Any,
    *,
    scales_px: Sequence[float] = (2.0, 4.0, 8.0),
    support_threshold: float = 0.99,
    normalization_quantile: float = 0.99,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Return H47-B persistence, a single-scale baseline, and common support.

    ``rank_field`` is a finite float array (the caller converts uint8 ranks to
    [0, 1]); ``valid_mask`` identifies real measurements. Masked Gaussian
    smoothing avoids creating a false edge along nodata boundaries. At each
    scale, the gradient magnitude is normalized by a robust full-support
    quantile. The persistence score is the minimum normalized magnitude across
    scales multiplied by the minimum pairwise axial normal agreement.

    The output is an uncalibrated edge score in [0, 1], not a physical tilt,
    depth estimate, fault probability, or submission raster.
    """
    values = np.asarray(rank_field, dtype=np.float32)
    valid = np.asarray(valid_mask, dtype=bool)
    if values.ndim != 2 or valid.ndim != 2 or values.shape != valid.shape:
        raise ValueError("rank_field and valid_mask must be same-shape 2D arrays")
    if not np.isfinite(values[valid]).all():
        raise ValueError("valid rank_field cells must be finite")
    if np.any((values[valid] < 0.0) | (values[valid] > 1.0)):
        raise ValueError("rank_field values must be in [0, 1]")
    scales = tuple(float(s) for s in scales_px)
    if len(scales) < 2:
        raise ValueError("scales_px must contain at least two positive scales")
    if values.shape[0] < 2 or values.shape[1] < 2:
        raise ValueError("rank_field must be at least 2 by 2 for gradients")
    if any(not math.isfinite(s) or s <= 0 for s in scales):
        raise ValueError("all Gaussian scales must be positive finite pixel values")
    if tuple(sorted(scales)) != scales or len(set(scales)) != len(scales):
        raise ValueError("scales_px must be strictly increasing")
    if not 0.5 <= normalization_quantile < 1.0:
        raise ValueError("normalization_quantile must be in [0.5, 1)")
    if not 0.0 < support_threshold <= 1.0:
        raise ValueError("support_threshold must be in (0, 1]")

    weight = valid.astype(np.float32)
    safe_values = np.where(valid, values, 0.0).astype(np.float32, copy=False)
    supports: list[np.ndarray] = []
    magnitudes: list[np.ndarray] = []
    angles: list[np.ndarray] = []

    for sigma in scales:
        smooth_weight = ndimage.gaussian_filter(
            weight, sigma=sigma, mode="constant", cval=0.0, truncate=4.0
        )
        smooth_sum = ndimage.gaussian_filter(
            safe_values, sigma=sigma, mode="constant", cval=0.0, truncate=4.0
        )
        smoothed = np.zeros(values.shape, dtype=np.float32)
        np.divide(smooth_sum, smooth_weight, out=smoothed, where=smooth_weight > 0.0)
        supported = valid & (smooth_weight >= support_threshold)
        # Central differences must not touch an unsupported neighbor.
        stencil = ndimage.binary_erosion(
            supported, structure=np.ones((3, 3), dtype=bool), border_value=0
        )
        grad_y, grad_x = np.gradient(smoothed)
        magnitude = np.hypot(grad_x, grad_y).astype(np.float32)
        angle = np.arctan2(grad_y, grad_x).astype(np.float32)
        magnitude[~stencil] = 0.0
        supports.append(stencil)
        magnitudes.append(magnitude)
        angles.append(angle)

    common = np.logical_and.reduce(supports)
    if not common.any():
        empty = np.zeros(values.shape, dtype=np.float32)
        return empty, empty.copy(), common, {
            "valid_support_pixels": 0,
            "scales_px": list(scales),
            "normalization_quantile": float(normalization_quantile),
            "gradient_quantiles": [0.0 for _ in scales],
        }

    normalized: list[np.ndarray] = []
    gradient_quantiles: list[float] = []
    for magnitude in magnitudes:
        finite_mag = magnitude[common]
        scale_value = float(np.quantile(finite_mag, normalization_quantile))
        gradient_quantiles.append(scale_value)
        if not math.isfinite(scale_value) or scale_value <= np.finfo(np.float32).eps:
            norm = np.zeros(values.shape, dtype=np.float32)
        else:
            norm = np.clip(magnitude / scale_value, 0.0, 1.0).astype(np.float32)
        norm[~common] = 0.0
        normalized.append(norm)

    persistence = np.minimum(normalized[0], normalized[1])
    for norm in normalized[2:]:
        np.minimum(persistence, norm, out=persistence)

    agreement = np.ones(values.shape, dtype=np.float32)
    pair_count = 0
    for i in range(len(angles)):
        for j in range(i + 1, len(angles)):
            similarity = np.abs(np.cos(angles[i] - angles[j])).astype(np.float32)
            np.minimum(agreement, similarity, out=agreement)
            pair_count += 1
    persistence *= agreement
    persistence[~common] = 0.0
    np.clip(persistence, 0.0, 1.0, out=persistence)

    # The single-scale comparator uses the middle Gaussian scale and its own
    # robust normalization; it shares exactly the same common data support.
    middle = len(scales) // 2
    baseline = normalized[middle].copy()
    baseline[~common] = 0.0

    diagnostics = {
        "valid_support_pixels": int(common.sum()),
        "scales_px": list(scales),
        "support_threshold": float(support_threshold),
        "normalization_quantile": float(normalization_quantile),
        "gradient_quantiles": gradient_quantiles,
        "orientation_pair_count": pair_count,
        "score_type": "cross-scale normalized magnetic-edge persistence; uncalibrated",
    }
    return persistence, baseline, common, diagnostics


def ranked_pixels(score: Any, valid_mask: Any) -> np.ndarray:
    """Return valid flat indices sorted by descending score, then flat index.

    The secondary key makes tie handling explicit and reproducible.
    """
    values = np.asarray(score, dtype=np.float32)
    valid = np.asarray(valid_mask, dtype=bool)
    if values.ndim != 2 or valid.ndim != 2 or values.shape != valid.shape:
        raise ValueError("score and valid_mask must be same-shape 2D arrays")
    if not np.isfinite(values[valid]).all():
        raise ValueError("score must be finite at all valid cells")
    if np.any(values[valid] < 0):
        raise ValueError("score values must be non-negative")
    flat = np.flatnonzero(valid.ravel())
    if flat.size == 0:
        return flat
    flat_scores = values.ravel()[flat]
    order = np.lexsort((flat, -flat_scores))
    return flat[order]


def greedy_spaced_pixels(
    ranked_flat_indices: Any,
    shape: tuple[int, int],
    *,
    min_separation_px: float,
    budget: int,
) -> np.ndarray:
    """Greedily select top-ranked positions at a minimum Euclidean spacing.

    Points exactly ``min_separation_px`` apart are allowed. The function scans
    the supplied score ordering until it reaches ``budget`` or exhausts it.
    """
    ranked = np.asarray(ranked_flat_indices, dtype=np.int64)
    if ranked.ndim != 1:
        raise ValueError("ranked_flat_indices must be one-dimensional")
    height, width = shape
    if height <= 0 or width <= 0:
        raise ValueError("shape dimensions must be positive")
    total = height * width
    if np.any((ranked < 0) | (ranked >= total)):
        raise ValueError("ranked_flat_indices contains an out-of-grid index")
    if not math.isfinite(min_separation_px) or min_separation_px <= 0:
        raise ValueError("min_separation_px must be positive and finite")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
        raise ValueError("budget must be a positive integer")

    cell_size = float(min_separation_px)
    min_distance_sq = cell_size * cell_size
    buckets: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    selected: list[int] = []
    for flat_index in ranked:
        index = int(flat_index)
        row, col = divmod(index, width)
        cell_row = int(row // cell_size)
        cell_col = int(col // cell_size)
        blocked = False
        for nearby_row in range(cell_row - 1, cell_row + 2):
            if blocked:
                break
            for nearby_col in range(cell_col - 1, cell_col + 2):
                for selected_row, selected_col in buckets.get((nearby_row, nearby_col), ()):
                    dr = row - selected_row
                    dc = col - selected_col
                    if dr * dr + dc * dc < min_distance_sq - 1e-12:
                        blocked = True
                        break
                if blocked:
                    break
        if blocked:
            continue
        selected.append(index)
        buckets[(cell_row, cell_col)].append((row, col))
        if len(selected) == budget:
            return np.asarray(selected, dtype=np.int64)
    raise ValueError(
        f"spacing {min_separation_px:g}px produced only {len(selected)} of {budget} required points"
    )


def guarded_grid_block_scores(
    prediction: Any,
    truth: Any,
    *,
    nrows: int = 4,
    ncols: int = 4,
    guard_px: int = 3,
) -> list[dict[str, Any]]:
    """Score disjoint grid blocks after purging a guard from every block edge.

    Predictions and catalogue pixels in each guard inset are excluded from that
    block's DTI, so no prediction or truth pixel is counted in multiple blocks
    and kernel support cannot bridge directly into a neighbouring fold. Scores
    remain correlated across adjacent blocks; this function does not establish
    exchangeability or independence.
    """
    pred = np.asarray(prediction)
    target = np.asarray(truth)
    if pred.ndim != 2 or target.ndim != 2 or pred.shape != target.shape:
        raise ValueError("prediction and truth must be same-shape 2D arrays")
    if isinstance(nrows, bool) or not isinstance(nrows, int) or nrows < 1:
        raise ValueError("nrows must be a positive integer")
    if isinstance(ncols, bool) or not isinstance(ncols, int) or ncols < 1:
        raise ValueError("ncols must be a positive integer")
    if isinstance(guard_px, bool) or not isinstance(guard_px, int) or guard_px < 0:
        raise ValueError("guard_px must be a non-negative integer")

    row_edges = np.linspace(0, pred.shape[0], nrows + 1).astype(int)
    col_edges = np.linspace(0, pred.shape[1], ncols + 1).astype(int)
    result: list[dict[str, Any]] = []
    for block_row in range(nrows):
        for block_col in range(ncols):
            row0, row1 = int(row_edges[block_row]), int(row_edges[block_row + 1])
            col0, col1 = int(col_edges[block_col]), int(col_edges[block_col + 1])
            inner_row0, inner_row1 = row0 + guard_px, row1 - guard_px
            inner_col0, inner_col1 = col0 + guard_px, col1 - guard_px
            if inner_row1 <= inner_row0 or inner_col1 <= inner_col0:
                raise ValueError("guard_px leaves an empty block")
            pred_core = pred[inner_row0:inner_row1, inner_col0:inner_col1]
            truth_core = target[inner_row0:inner_row1, inner_col0:inner_col1]
            row_result = dti(pred_core, truth_core)
            row_result.update(
                block_id=block_row * ncols + block_col,
                block_row=block_row,
                block_col=block_col,
                guard_px=guard_px,
                valid_eval_pixels=int(pred_core.size),
            )
            result.append(row_result)
    return result


def pooled_block_dti(block_rows: Sequence[Mapping[str, Any]], block_ids: Sequence[int]) -> float:
    """Pool disjoint guarded block components using the organizer DTI identity."""
    ids = {int(block_id) for block_id in block_ids}
    rows = [row for row in block_rows if int(row["block_id"]) in ids]
    if not rows:
        raise ValueError("no block results selected for pooling")
    tp = float(sum(float(row["TPw"]) for row in rows))
    fp = float(sum(float(row["FPw"]) for row in rows))
    ng = float(sum(float(row["Ng"]) for row in rows))
    if ng <= 0:
        return 0.0
    return float(5.0 * tp / (tp + fp + 4.0 * ng))


def choose_spacing(
    results: Mapping[int, Sequence[Mapping[str, Any]]],
    block_ids: Sequence[int],
) -> tuple[int, float]:
    """Choose spacing by mean selection-block DTI; ties prefer larger spacing."""
    candidates: list[tuple[float, int]] = []
    wanted = {int(block_id) for block_id in block_ids}
    for spacing, rows in results.items():
        values = [float(row["dti"]) for row in rows if int(row["block_id"]) in wanted]
        if len(values) != len(wanted):
            raise ValueError(f"spacing {spacing}: missing one or more selection block scores")
        candidates.append((float(np.mean(values)), int(spacing)))
    if not candidates:
        raise ValueError("results contain no spacing configurations")
    mean, spacing = max(candidates, key=lambda item: (item[0], item[1]))
    return spacing, mean


def split_conformal_lower_bound(
    selection_scores: Sequence[float],
    calibration_scores: Sequence[float],
) -> dict[str, Any]:
    """One-sided split-conformal lower bound for a future block-level DTI.

    The finite-sample marginal coverage is conditional on exchangeability of
    the calibration and future block scores. It is not a guarantee under
    arbitrary spatial dependence or for a different private-label target.
    """
    selection = np.asarray(selection_scores, dtype=np.float64)
    calibration = np.asarray(calibration_scores, dtype=np.float64)
    if selection.ndim != 1 or calibration.ndim != 1:
        raise ValueError("selection_scores and calibration_scores must be one-dimensional")
    if selection.size == 0 or calibration.size == 0:
        raise ValueError("selection and calibration scores must both be non-empty")
    if not np.isfinite(selection).all() or not np.isfinite(calibration).all():
        raise ValueError("conformal scores must be finite")
    if np.any((selection < 0) | (selection > 1)) or np.any((calibration < 0) | (calibration > 1)):
        raise ValueError("DTI scores must be in [0, 1]")

    n = int(calibration.size)
    alpha = 1.0 / (n + 1.0)
    target_coverage = 1.0 - alpha
    rank = math.ceil((n + 1) * target_coverage)
    center = float(selection.mean())
    residuals = center - calibration
    order = np.sort(residuals)
    quantile = float(order[rank - 1])
    lower = float(np.clip(center - quantile, 0.0, 1.0))
    return {
        "n_calibration_blocks": n,
        "nominal_coverage": float(target_coverage),
        "alpha": float(alpha),
        "selection_mean": center,
        "calibration_scores": calibration.tolist(),
        "one_sided_residuals": residuals.tolist(),
        "sorted_residuals": order.tolist(),
        "rank_1_based": rank,
        "quantile": quantile,
        "lower_bound_clipped": lower,
        "assumption": "marginal block-score exchangeability; unverified under spatial dependence",
        "scope": "future comparable block-level score for the same calibration target; not a different private-label/leaderboard target",
    }
