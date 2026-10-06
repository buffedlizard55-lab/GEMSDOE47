"""Quality-screened GDR geothermometer consensus and structural-edge scoring.

The geochemical table is an owner-hosted mirror of the public INGENIOUS GDR
submission, not an organizer-authenticated source file. This module deliberately
reads only the location, measured outlet-temperature, and three geothermometer
columns; in particular it never reads the label-derived ``dist_known_fault_px``
column present in the CSV export.

All returned score fields are relative ranking surfaces, not calibrated fault
probabilities. Labels are intentionally absent from this module's API.
"""
from __future__ import annotations

import csv
import math
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage

THERMOMETER_FIELDS = (
    "geothermquartz_c",
    "geothermchalc_c",
    "geothermcat_c",
)
OUTLET_FIELD = "temp_c"
REQUIRED_FIELDS = ("name", "row", "col", OUTLET_FIELD, *THERMOMETER_FIELDS)

RESERVOIR_MIN_C = 80.0
RESERVOIR_MAX_C = 300.0
OUTLET_MIN_C = -5.0
OUTLET_MAX_C = 100.0
MAX_THERMOMETER_SPREAD_C = 30.0
GAUSSIAN_SIGMA_PX = 10.0
GAUSSIAN_TRUNCATE = 4.0
SOURCE_RADIUS_PX = 40.0
STRUCTURE_SIGMA_PX = 2.0
STRUCTURE_SUPPORT_THRESHOLD = 0.99
STRUCTURE_NORMALIZATION_QUANTILE = 0.99
NODATA_SENTINEL = -1e30


@dataclass(frozen=True)
class GeochemPoint:
    """One grouped, quality-screened source location."""

    name: str
    row: int
    col: int
    reservoir_temperature_c: float
    outlet_temperature_c: float
    thermometer_spread_c: float
    n_thermometers: int
    weight: float


@dataclass(frozen=True)
class GeochemAudit:
    """Source-only diagnostics; no catalogue labels or DTI values."""

    csv_rows: int
    grouped_locations: int
    groups_with_two_plausible_thermometers: int
    groups_with_plausible_outlet_temperature: int
    groups_passing_frozen_temperature_and_spread_screen: int
    positive_weight_locations: int
    unique_positive_source_cells: int
    ignored_label_derived_column: str
    fields_used: tuple[str, ...]


def _finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _normalized_name(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip().casefold()


def _median_in_range(values: list[float], low: float, high: float) -> float | None:
    kept = [v for v in values if low <= v <= high]
    if not kept:
        return None
    return float(np.median(np.asarray(kept, dtype=np.float64)))


def read_consensus_points(
    csv_path: Path | str,
    shape: tuple[int, int],
) -> tuple[list[GeochemPoint], GeochemAudit]:
    """Group repeated export rows and apply the locked geothermometer screen.

    Group identity is normalized station name plus integer 100 m row/column.
    Repeated rows within a group are summarized by the median for each method;
    this prevents repeated source-table rows from counting as extra locations.
    Empty names remain a shared empty-name key only at the same pixel.
    """
    csv_path = Path(csv_path)
    grouped: dict[tuple[str, int, int], dict[str, Any]] = {}
    rows_read = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = set(reader.fieldnames or ())
        missing = sorted(set(REQUIRED_FIELDS) - headers)
        if missing:
            raise ValueError(f"GDR mirror CSV is missing required fields: {missing}")
        for row in reader:
            rows_read += 1
            try:
                r = int(row["row"])
                c = int(row["col"])
            except (TypeError, ValueError):
                continue
            if not (0 <= r < shape[0] and 0 <= c < shape[1]):
                continue
            key = (_normalized_name(row.get("name")), r, c)
            if key not in grouped:
                grouped[key] = {field: [] for field in (*THERMOMETER_FIELDS, OUTLET_FIELD)}
            values = grouped[key]
            for field in (*THERMOMETER_FIELDS, OUTLET_FIELD):
                value = _finite_float(row.get(field))
                if value is not None:
                    values[field].append(value)

    points: list[GeochemPoint] = []
    with_two_methods = 0
    with_outlet = 0
    frozen_eligible = 0
    for (name, r, c), values in sorted(grouped.items()):
        method_temperatures = [
            temperature
            for field in THERMOMETER_FIELDS
            if (temperature := _median_in_range(
                values[field], 0.0, RESERVOIR_MAX_C
            )) is not None
        ]
        if len(method_temperatures) < 2:
            continue
        with_two_methods += 1

        outlet_temperature = _median_in_range(
            values[OUTLET_FIELD], OUTLET_MIN_C, OUTLET_MAX_C
        )
        if outlet_temperature is None:
            continue
        with_outlet += 1

        reservoir_temperature = float(np.median(method_temperatures))
        spread = float(max(method_temperatures) - min(method_temperatures))
        if (reservoir_temperature < RESERVOIR_MIN_C
                or spread > MAX_THERMOMETER_SPREAD_C):
            continue
        frozen_eligible += 1

        agreement = math.exp(-spread / MAX_THERMOMETER_SPREAD_C)
        reservoir = float(np.clip(
            (reservoir_temperature - RESERVOIR_MIN_C) / 120.0, 0.0, 1.0
        ))
        cooling = float(np.clip(
            (reservoir_temperature - outlet_temperature) / 120.0, 0.0, 1.0
        ))
        weight = agreement * reservoir * cooling
        if weight <= 0.0:
            continue
        points.append(GeochemPoint(
            name=name,
            row=r,
            col=c,
            reservoir_temperature_c=reservoir_temperature,
            outlet_temperature_c=outlet_temperature,
            thermometer_spread_c=spread,
            n_thermometers=len(method_temperatures),
            weight=float(weight),
        ))

    unique_cells = {(point.row, point.col) for point in points}
    audit = GeochemAudit(
        csv_rows=rows_read,
        grouped_locations=len(grouped),
        groups_with_two_plausible_thermometers=with_two_methods,
        groups_with_plausible_outlet_temperature=with_outlet,
        groups_passing_frozen_temperature_and_spread_screen=frozen_eligible,
        positive_weight_locations=len(points),
        unique_positive_source_cells=len(unique_cells),
        ignored_label_derived_column="dist_known_fault_px",
        fields_used=("name", "row", "col", OUTLET_FIELD, *THERMOMETER_FIELDS),
    )
    return points, audit


def geochemistry_influence(
    points: list[GeochemPoint],
    shape: tuple[int, int],
    footprint: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Rasterize points and make the fixed 1 km Gaussian influence field."""
    footprint = np.asarray(footprint, dtype=bool)
    if footprint.shape != shape:
        raise ValueError("footprint shape does not match requested surface shape")
    seed_weights = np.zeros(shape, dtype=np.float32)
    source_mask = np.zeros(shape, dtype=bool)
    for point in points:
        if not (0 <= point.row < shape[0] and 0 <= point.col < shape[1]):
            continue
        if not footprint[point.row, point.col]:
            continue
        seed_weights[point.row, point.col] = max(
            seed_weights[point.row, point.col], np.float32(point.weight)
        )
        source_mask[point.row, point.col] = True

    if not source_mask.any():
        raise ValueError("no positive-weight GDR points fall inside the template footprint")

    influence = ndimage.gaussian_filter(
        seed_weights,
        sigma=GAUSSIAN_SIGMA_PX,
        mode="constant",
        cval=0.0,
        truncate=GAUSSIAN_TRUNCATE,
    ).astype(np.float32)
    distance = ndimage.distance_transform_edt(~source_mask)
    support = (distance <= SOURCE_RADIUS_PX) & footprint
    influence[~support] = 0.0
    return influence, support, {
        "source_locations": len(points),
        "unique_source_cells": int(source_mask.sum()),
        "gaussian_sigma_px": GAUSSIAN_SIGMA_PX,
        "gaussian_truncate": GAUSSIAN_TRUNCATE,
        "maximum_influence_radius_px": SOURCE_RADIUS_PX,
        "support_pixels": int(support.sum()),
        "influence_max": float(influence.max()),
    }


def _masked_gaussian(
    values: np.ndarray,
    valid: np.ndarray,
    *,
    sigma: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    weight = valid.astype(np.float32)
    safe = np.where(valid, values, 0.0).astype(np.float32, copy=False)
    smooth_weight = ndimage.gaussian_filter(
        weight, sigma=sigma, mode="constant", cval=0.0, truncate=4.0
    )
    smooth_sum = ndimage.gaussian_filter(
        safe, sigma=sigma, mode="constant", cval=0.0, truncate=4.0
    )
    smooth = np.zeros(values.shape, dtype=np.float32)
    np.divide(smooth_sum, smooth_weight, out=smooth, where=smooth_weight > 0.0)
    supported = valid & (smooth_weight >= STRUCTURE_SUPPORT_THRESHOLD)
    return smooth, supported, smooth_weight


def structural_edge_agreement(
    rtp: np.ndarray,
    gravity: np.ndarray,
    footprint: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Compute aligned, normalized RTP/gravity gradient coincidence."""
    rtp = np.asarray(rtp, dtype=np.float32)
    gravity = np.asarray(gravity, dtype=np.float32)
    footprint = np.asarray(footprint, dtype=bool)
    if rtp.ndim != 2 or gravity.ndim != 2 or rtp.shape != gravity.shape:
        raise ValueError("rtp and gravity must be same-shape 2D arrays")
    if footprint.shape != rtp.shape:
        raise ValueError("footprint shape does not match potential-field arrays")

    rtp_valid = footprint & np.isfinite(rtp) & (rtp > NODATA_SENTINEL)
    gravity_valid = footprint & np.isfinite(gravity) & (gravity > NODATA_SENTINEL)
    rtp_smooth, rtp_support, _ = _masked_gaussian(
        rtp, rtp_valid, sigma=STRUCTURE_SIGMA_PX
    )
    gravity_smooth, gravity_support, _ = _masked_gaussian(
        gravity, gravity_valid, sigma=STRUCTURE_SIGMA_PX
    )
    common = rtp_support & gravity_support
    stencil = ndimage.binary_erosion(
        common, structure=np.ones((3, 3), dtype=bool), border_value=0
    )
    if not stencil.any():
        raise ValueError("no common supported RTP/gravity cells for edge calculation")

    rtp_gy, rtp_gx = np.gradient(rtp_smooth)
    gravity_gy, gravity_gx = np.gradient(gravity_smooth)
    rtp_magnitude = np.hypot(rtp_gx, rtp_gy).astype(np.float32)
    gravity_magnitude = np.hypot(gravity_gx, gravity_gy).astype(np.float32)

    rtp_scale = float(np.quantile(rtp_magnitude[stencil], STRUCTURE_NORMALIZATION_QUANTILE))
    gravity_scale = float(np.quantile(
        gravity_magnitude[stencil], STRUCTURE_NORMALIZATION_QUANTILE
    ))
    if (not math.isfinite(rtp_scale) or rtp_scale <= np.finfo(np.float32).eps
            or not math.isfinite(gravity_scale)
            or gravity_scale <= np.finfo(np.float32).eps):
        raise ValueError("RTP/gravity gradient normalization scale is invalid")

    rtp_norm = np.clip(rtp_magnitude / rtp_scale, 0.0, 1.0)
    gravity_norm = np.clip(gravity_magnitude / gravity_scale, 0.0, 1.0)
    denominator = rtp_magnitude * gravity_magnitude
    dot = np.abs(rtp_gx * gravity_gx + rtp_gy * gravity_gy)
    alignment = np.zeros(rtp.shape, dtype=np.float32)
    np.divide(dot, denominator, out=alignment, where=denominator > 1e-12)
    np.clip(alignment, 0.0, 1.0, out=alignment)

    edge = np.sqrt(rtp_norm * gravity_norm).astype(np.float32) * alignment
    edge[~stencil] = 0.0
    support = stencil & footprint
    edge[~support] = 0.0
    return edge, support, {
        "gaussian_sigma_px": STRUCTURE_SIGMA_PX,
        "support_threshold": STRUCTURE_SUPPORT_THRESHOLD,
        "normalization_quantile": STRUCTURE_NORMALIZATION_QUANTILE,
        "gradient_stencil_erosion_px": 1,
        "gradient_stencil": "common >=99% support eroded one pixel for centered finite differences",
        "rtp_gradient_normalizer": rtp_scale,
        "gravity_gradient_normalizer": gravity_scale,
        "common_support_pixels": int(support.sum()),
        "edge_max": float(edge.max()),
    }


def combine_geochemistry_and_structure(
    geochem_surface: np.ndarray,
    geochem_support: np.ndarray,
    structural_edge: np.ndarray,
    structural_support: np.ndarray,
    footprint: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Multiply the fixed evidence fields and return score and allowed support."""
    fields = [
        np.asarray(geochem_surface, dtype=np.float32),
        np.asarray(structural_edge, dtype=np.float32),
    ]
    supports = [
        np.asarray(geochem_support, dtype=bool),
        np.asarray(structural_support, dtype=bool),
        np.asarray(footprint, dtype=bool),
    ]
    shape = fields[0].shape
    if any(field.shape != shape for field in fields) or any(mask.shape != shape for mask in supports):
        raise ValueError("all surfaces and masks must share the same shape")
    valid = np.logical_and.reduce(supports) & np.isfinite(fields[0]) & np.isfinite(fields[1])
    score = np.zeros(shape, dtype=np.float32)
    score[valid] = fields[0][valid] * fields[1][valid]
    valid &= score > 0.0
    return score, valid


def audit_to_dict(audit: GeochemAudit) -> dict[str, Any]:
    """Convert dataclass diagnostics to JSON-safe primitives."""
    result = asdict(audit)
    result["fields_used"] = list(audit.fields_used)
    return result
