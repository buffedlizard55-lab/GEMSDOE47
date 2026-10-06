"""Screening surface for H47-A, not a calibrated probability model.

H47-A tests whether edges in independent overlapping GeoDAWN survey products
persist at the same locations and with the same axial orientation. The output
is a normalized screening score in [0, 1]. It must not be submitted without
separate calibration and a spatially blocked holdout against an incumbent.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np


def _as_2d_float(values: Any, name: str) -> tuple[np.ndarray, np.ndarray]:
    """Return float64 data and a mask that respects masked arrays and NaNs."""
    masked = np.ma.asarray(values, dtype=np.float64)
    data = np.asarray(masked.filled(np.nan), dtype=np.float64)
    if data.ndim != 2:
        raise ValueError(f"{name} must be a two-dimensional single-band array")
    valid = np.isfinite(data) & ~np.ma.getmaskarray(masked)
    return data, valid


def _interior_stencil(mask: np.ndarray) -> np.ndarray:
    """Pixels with a valid center and N/S/E/W neighbors for centered gradients."""
    result = mask.copy()
    height, width = mask.shape
    result[0, :] = False
    result[-1, :] = False
    result[:, 0] = False
    result[:, -1] = False
    result[1:-1, 1:-1] &= (
        mask[:-2, 1:-1]
        & mask[2:, 1:-1]
        & mask[1:-1, :-2]
        & mask[1:-1, 2:]
    )
    # Explicitly handle arrays too small for a centered 3x3 neighborhood.
    if height < 3 or width < 3:
        result[:] = False
    return result


def _edge_field(
    values: Any,
    name: str,
    *,
    dx: float,
    dy: float,
    quantile: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Calculate robustly normalized gradient magnitude and map-space angle."""
    data, finite = _as_2d_float(values, name)
    if not np.isfinite(dx) or not np.isfinite(dy) or dx == 0 or dy == 0:
        raise ValueError("dx and dy must be finite, non-zero map-coordinate pixel steps")

    grad_valid = _interior_stencil(finite)
    if data.shape[0] < 2 or data.shape[1] < 2:
        empty = np.zeros(data.shape, dtype=np.float64)
        return empty, empty.copy(), grad_valid, 0.0
    # Missing values are replaced only to make np.gradient safe; cells near any
    # missing neighbor are excluded by grad_valid and cannot create nodata edges.
    safe = np.where(finite, data, 0.0)
    grad_y, grad_x = np.gradient(safe, dy, dx)
    magnitude = np.hypot(grad_x, grad_y)
    angle = np.arctan2(grad_y, grad_x)
    selected = magnitude[grad_valid]
    selected = selected[np.isfinite(selected) & (selected > np.finfo(np.float64).eps)]
    # Excluding exact zero gradients avoids a zero quantile when lineaments are
    # sparse relative to the full image. Cross-survey agreement still filters
    # isolated one-off noise; spatial validation must determine usefulness.
    scale = float(np.quantile(selected, quantile)) if selected.size else 0.0
    if not np.isfinite(scale) or scale <= np.finfo(np.float64).eps:
        normalized = np.zeros_like(magnitude, dtype=np.float64)
    else:
        normalized = np.clip(magnitude / scale, 0.0, 1.0)
    normalized[~grad_valid] = 0.0
    return normalized, angle, grad_valid, scale


def _axial_similarity(angle_a: np.ndarray, angle_b: np.ndarray) -> np.ndarray:
    """Orientation agreement for unoriented lineaments (theta and theta+pi)."""
    return np.abs(np.cos(angle_a - angle_b))


def _line_parallelism(edge_normal: np.ndarray, bearing_degrees: float) -> np.ndarray:
    """Score whether an edge's tangent is parallel to a flight-line bearing.

    ``bearing_degrees`` is compass azimuth clockwise from map north (0 = north,
    90 = east). The edge normal is perpendicular to its lineament tangent, so
    a high score indicates the lineament itself follows the flight direction.
    """
    if not np.isfinite(bearing_degrees):
        raise ValueError("flight bearings must be finite compass azimuths")
    flight_angle = np.deg2rad(90.0 - bearing_degrees)
    return np.abs(np.sin(edge_normal - flight_angle))


def compute_h47a_score(
    magnetic_a: Any,
    magnetic_b: Any,
    *,
    radiometric_a: Any | None = None,
    radiometric_b: Any | None = None,
    dx: float = 1.0,
    dy: float = -1.0,
    quantile: float = 0.995,
    artifact_penalty: float = 0.0,
    flight_bearing_a: float | None = None,
    flight_bearing_b: float | None = None,
) -> tuple[np.ndarray, Mapping[str, Any]]:
    """Return H47-A's uncalibrated cross-survey lineament screening surface.

    Required magnetic inputs and the optional radiometric pair must be aligned
    arrays on the same grid. Values may be NumPy masked arrays; masked and
    non-finite input cells are excluded, along with one-pixel neighborhoods
    needed by the gradient stencil. No reprojection or resampling is performed.

    Each modality contributes the weaker normalized edge amplitude from the
    two acquisitions, multiplied by axial orientation agreement. If both
    modalities are present their support is averaged where both are valid.
    ``artifact_penalty`` is deliberately zero by default: penalty strength is
    a holdout hyperparameter, not something to tune against a public leaderboard.
    """
    if not 0.5 <= quantile < 1.0:
        raise ValueError("quantile must be in [0.5, 1.0)")
    if not 0.0 <= artifact_penalty <= 1.0:
        raise ValueError("artifact_penalty must be in [0, 1]")
    if (flight_bearing_a is None) != (flight_bearing_b is None):
        raise ValueError("provide both flight bearings or neither")
    if artifact_penalty > 0 and flight_bearing_a is None:
        raise ValueError("nonzero artifact_penalty requires both flight bearings")
    if flight_bearing_a is not None and (
        not np.isfinite(flight_bearing_a) or not np.isfinite(flight_bearing_b)
    ):
        raise ValueError("flight bearings must be finite compass azimuths")

    mag_a, mag_a_angle, mag_a_valid, mag_a_scale = _edge_field(
        magnetic_a, "magnetic_a", dx=dx, dy=dy, quantile=quantile
    )
    mag_b, mag_b_angle, mag_b_valid, mag_b_scale = _edge_field(
        magnetic_b, "magnetic_b", dx=dx, dy=dy, quantile=quantile
    )
    if mag_a.shape != mag_b.shape:
        raise ValueError("magnetic_a and magnetic_b must have identical shapes")

    pairs: list[tuple[str, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float]] = [
        (
            "magnetic",
            mag_a,
            mag_a_angle,
            mag_a_valid,
            mag_b,
            mag_b_angle,
            mag_b_valid,
            mag_a_scale,
            mag_b_scale,
        )
    ]
    if (radiometric_a is None) != (radiometric_b is None):
        raise ValueError("radiometric_a and radiometric_b must be supplied together")
    if radiometric_a is not None and radiometric_b is not None:
        rad_a, rad_a_angle, rad_a_valid, rad_a_scale = _edge_field(
            radiometric_a, "radiometric_a", dx=dx, dy=dy, quantile=quantile
        )
        rad_b, rad_b_angle, rad_b_valid, rad_b_scale = _edge_field(
            radiometric_b, "radiometric_b", dx=dx, dy=dy, quantile=quantile
        )
        if rad_a.shape != mag_a.shape or rad_b.shape != mag_a.shape:
            raise ValueError("all modality arrays must have identical shapes")
        pairs.append(
            (
                "radiometric",
                rad_a,
                rad_a_angle,
                rad_a_valid,
                rad_b,
                rad_b_angle,
                rad_b_valid,
                rad_a_scale,
                rad_b_scale,
            )
        )

    height, width = mag_a.shape
    sum_score = np.zeros((height, width), dtype=np.float64)
    pair_count = np.zeros((height, width), dtype=np.uint8)
    pair_valid_count = 0
    pair_diagnostics: dict[str, dict[str, float | int]] = {}
    artifact_a = None if flight_bearing_a is None else float(flight_bearing_a)
    artifact_b = None if flight_bearing_b is None else float(flight_bearing_b)

    for (
        label,
        strength_a,
        angle_a,
        valid_a,
        strength_b,
        angle_b,
        valid_b,
        scale_a,
        scale_b,
    ) in pairs:
        valid_pair = valid_a & valid_b
        support = np.minimum(strength_a, strength_b) * _axial_similarity(angle_a, angle_b)
        if artifact_penalty > 0:
            assert artifact_a is not None and artifact_b is not None
            align_a = _line_parallelism(angle_a, artifact_a) * strength_a
            align_b = _line_parallelism(angle_b, artifact_b) * strength_b
            artifact_support = np.maximum(align_a, align_b)
            support *= 1.0 - artifact_penalty * artifact_support
        support[~valid_pair] = 0.0
        sum_score += support
        pair_count += valid_pair.astype(np.uint8)
        pair_valid_count += int(valid_pair.sum())
        pair_diagnostics[label] = {
            "valid_pixels": int(valid_pair.sum()),
            "edge_scale_a": scale_a,
            "edge_scale_b": scale_b,
        }

    output = np.full((height, width), np.nan, dtype=np.float32)
    supported = pair_count > 0
    output[supported] = (sum_score[supported] / pair_count[supported]).astype(np.float32)
    # Guard the serialized dtype too; the output is a score, not a probability.
    finite_output = np.isfinite(output)
    output[finite_output] = np.clip(output[finite_output], 0.0, 1.0)
    diagnostics: dict[str, Any] = {
        "hypothesis_id": "H47-A",
        "surface_type": "uncalibrated acquisition-invariant screening score, not a probability",
        "quantile": float(quantile),
        "artifact_penalty": float(artifact_penalty),
        "flight_bearing_a_deg_clockwise_from_north": artifact_a,
        "flight_bearing_b_deg_clockwise_from_north": artifact_b,
        "valid_pixels": int(supported.sum()),
        "pair_valid_pixels_total": pair_valid_count,
        "modalities": pair_diagnostics,
        "nodata": "NaN outside the joint data/gradient support",
        "validation_status": "NOT_RUN",
    }
    return output, diagnostics
