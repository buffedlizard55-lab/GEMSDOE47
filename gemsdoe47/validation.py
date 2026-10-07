"""Local byte-level checks for a strict NaN-outside GeoTIFF profile.

This checker intentionally requires a NaN nodata tag and raw NaN values outside
the supplied footprint. That is stricter than the published null-or-NaN wording
and does not establish portal acceptance; the supplied template/reference inputs
must be authenticated separately.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.windows import Window


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _same_grid(left: rasterio.io.DatasetReader, right: rasterio.io.DatasetReader) -> bool:
    transform_left = np.asarray(tuple(left.transform)[:6], dtype=np.float64)
    transform_right = np.asarray(tuple(right.transform)[:6], dtype=np.float64)
    return (
        left.width == right.width
        and left.height == right.height
        and left.crs == right.crs
        and bool(np.allclose(transform_left, transform_right, rtol=0.0, atol=1e-9))
    )


def _inside_from_features(features: rasterio.io.DatasetReader, window: Window) -> np.ndarray:
    """A pixel is in the footprint if any reference feature band is finite/valid."""
    bands = features.read(window=window, masked=True).astype(np.float64)
    values = np.asarray(bands.filled(np.nan), dtype=np.float64)
    valid = np.isfinite(values) & ~np.ma.getmaskarray(bands)
    return np.any(valid, axis=0)


def _inside_from_mask(mask_ds: rasterio.io.DatasetReader, window: Window) -> np.ndarray:
    """Return the explicit binary-mask footprint in a raster window."""
    values = mask_ds.read(1, window=window, masked=True)
    data = np.asarray(values.filled(0))
    valid = np.isfinite(data) & ~np.ma.getmaskarray(values)
    return valid & (data != 0)


def validate_submission(
    submission_path: str | Path,
    template_path: str | Path,
    *,
    features_path: str | Path | None = None,
    footprint_mask_path: str | Path | None = None,
    template_footprint: bool = False,
) -> dict[str, Any]:
    """Run a strict local NaN-outside profile; raise ``ValueError`` on failure.

    Supply exactly one footprint source:

    * ``features_path``: a cell is in-bounds when any unmasked feature is finite;
    * ``footprint_mask_path``: a nonzero, valid cell is in-bounds; or
    * ``template_footprint=True``: use the supplied sample template's own GDAL
      validity mask. This mode verifies an exact sample-template encoding and is
      the appropriate check when feature validity and sample footprint are known
      to differ.

    The final mode is not an assertion that the locally mirrored template is
    organizer-authenticated. Pixels outside the selected footprint must be raw
    NaN with a NaN nodata tag; numeric sentinels and finite outside values are
    rejected. Range checks are made on float32 values read back from disk.
    """
    source_count = int(features_path is not None) + int(footprint_mask_path is not None) + int(template_footprint)
    if source_count != 1:
        raise ValueError("provide exactly one of features_path, footprint_mask_path, or template_footprint")

    submission_path = Path(submission_path)
    template_path = Path(template_path)
    reference_path = Path(features_path or footprint_mask_path or template_path)
    for path in (submission_path, template_path, reference_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    counts = {
        "valid_pixels": 0,
        "outside_pixels": 0,
        "invalid_inside_pixels": 0,
        "non_nan_outside_pixels": 0,
        "below_zero_pixels": 0,
        "above_one_pixels": 0,
    }
    min_value = math.inf
    max_value = -math.inf
    with rasterio.open(template_path) as template, rasterio.open(submission_path) as result:
        if template.count != 1:
            raise ValueError(f"supplied template has {template.count} bands; expected 1")
        if result.count != 1:
            raise ValueError(f"submission has {result.count} bands; expected 1")
        if result.dtypes[0] != "float32":
            raise ValueError(f"submission dtype is {result.dtypes[0]}; expected float32")
        if not _same_grid(template, result):
            raise ValueError("submission grid does not exactly match template width/height/CRS/transform")
        if result.nodata is None or not math.isnan(float(result.nodata)):
            raise ValueError("submission nodata tag must be NaN to avoid numeric sentinel leakage")

        reference = None
        if not template_footprint:
            reference = rasterio.open(reference_path)
            if not _same_grid(template, reference):
                raise ValueError("footprint/features grid does not match the supplied template")
            if features_path is not None and reference.count < 1:
                raise ValueError("feature raster contains no bands")
            if footprint_mask_path is not None and reference.count != 1:
                raise ValueError("footprint mask must contain exactly one band")

        try:
            for _, window in result.block_windows(1):
                values = result.read(1, window=window)
                result_mask = result.read_masks(1, window=window) > 0
                if template_footprint:
                    inside = template.read_masks(1, window=window) > 0
                elif features_path is not None:
                    inside = _inside_from_features(reference, window)
                else:
                    inside = _inside_from_mask(reference, window)
                if inside.shape != values.shape:
                    raise ValueError("internal window mismatch while building footprint")

                finite = np.isfinite(values)
                invalid_inside = inside & (~finite | ~result_mask)
                counts["invalid_inside_pixels"] += int(invalid_inside.sum())
                inside_valid = inside & finite & result_mask
                if inside_valid.any():
                    in_values = values[inside_valid]
                    counts["valid_pixels"] += int(in_values.size)
                    min_value = min(min_value, float(np.min(in_values)))
                    max_value = max(max_value, float(np.max(in_values)))
                    counts["below_zero_pixels"] += int(np.count_nonzero(in_values < 0.0))
                    counts["above_one_pixels"] += int(np.count_nonzero(in_values > 1.0))

                outside = ~inside
                counts["outside_pixels"] += int(outside.sum())
                # NaN is the requested null value; infinities and numeric
                # sentinels outside the footprint are intentionally rejected.
                counts["non_nan_outside_pixels"] += int(np.count_nonzero(~np.isnan(values[outside])))
        finally:
            if reference is not None:
                reference.close()

        metadata = {
            "width": int(result.width),
            "height": int(result.height),
            "bands": int(result.count),
            "dtype": result.dtypes[0],
            "crs": result.crs.to_string() if result.crs else None,
            "transform": list(result.transform)[:6],
        }

    failures: list[str] = []
    if counts["valid_pixels"] == 0:
        failures.append("footprint contains no valid prediction pixels")
    if counts["invalid_inside_pixels"]:
        failures.append(f"{counts['invalid_inside_pixels']} in-footprint cells are non-finite or masked")
    if counts["non_nan_outside_pixels"]:
        failures.append(f"{counts['non_nan_outside_pixels']} out-of-footprint cells are not NaN")
    if counts["below_zero_pixels"]:
        failures.append(f"{counts['below_zero_pixels']} in-footprint values are below 0")
    if counts["above_one_pixels"]:
        failures.append(f"{counts['above_one_pixels']} in-footprint values are above 1")
    if failures:
        raise ValueError("\n".join(f"- {failure}" for failure in failures))

    if template_footprint:
        footprint_source = f"template_internal_mask:{template_path}"
    else:
        footprint_source = str(reference_path)
    return {
        "status": "LOCAL_PASS",
        "validation_scope": "strict local NaN-outside profile; not a portal oracle",
        "organizer_acceptance_established": False,
        "submission": str(submission_path),
        "sha256": sha256_file(submission_path),
        "template": str(template_path),
        "footprint_source": footprint_source,
        **metadata,
        "nodata": "NaN",
        **counts,
        "min_in_footprint": min_value,
        "max_in_footprint": max_value,
        "range": [0.0, 1.0],
    }


def write_json_report(report: dict[str, Any], destination: str | Path) -> None:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
