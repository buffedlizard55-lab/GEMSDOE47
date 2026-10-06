"""Strict one-file GeoTIFF contract: finite raw values AND a null footprint mask.

An internal TIFF validity mask stores outside-footprint pixels as invalid/null
while their underlying samples are zero. This avoids NaN-intolerant raw range
checks without marking valid zero predictions as nodata. No sidecar .msk file.

This is a GDAL/rasterio format check, NOT proof of organizer acceptance, data
provenance, geological discovery, or permission to use a submission slot.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import rasterio

from .grid import Template


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(path: str | Path, template: Template) -> dict:
    """Reopen the actual bytes, including mask semantics and sidecar dependence."""
    path = Path(path)
    with rasterio.open(path) as source:
        v = source.read(1)
        mask = source.read_masks(1) > 0
        geometry_ok = source.shape == template.shape
        expected_bounds = rasterio.transform.array_bounds(*template.shape, template.transform)
        checks = {
            "driver_gtiff": source.driver == "GTiff",
            "single_band": source.count == 1,
            "dtype_float32": source.dtypes == ("float32",),
            "crs_matches_template": source.crs == rasterio.crs.CRS.from_string(template.crs),
            "shape_matches_template": geometry_ok,
            "transform_matches_template": bool(np.allclose(tuple(source.transform), tuple(template.transform), atol=1e-9, rtol=0)),
            "bounds_match_template": bool(np.allclose(tuple(source.bounds), expected_bounds, atol=1e-6, rtol=0)),
            "raw_all_finite": bool(np.isfinite(v).all()),
            "raw_range_0_1": bool(((v >= 0) & (v <= 1)).all()),
            "nodata_tag_unset": source.nodata is None,
            "mask_matches_official_template_footprint": geometry_ok and bool(np.array_equal(mask, template.footprint)),
            "outside_raw_zero": geometry_ok and bool((v[~template.footprint] == 0).all()),
            "one_self_contained_file": len(source.files) == 1 and Path(source.files[0]).resolve() == path.resolve(),
        }
        # Check a masked read independently of read_masks, not just finite pixels.
        masked = source.read(1, masked=True)
        checks["masked_read_null_exactly_outside"] = geometry_ok and bool(
            np.array_equal(np.ma.getmaskarray(masked), ~template.footprint))
        checked_values = masked.compressed()
        checks["masked_read_range_0_1"] = bool(checked_values.size and np.isfinite(checked_values).all()
                                               and ((checked_values >= 0) & (checked_values <= 1)).all())
        stats = {"pixels": int(v.size), "positive_pixels": int((v > 0).sum()),
                 "raw_nonfinite_pixels": int((~np.isfinite(v)).sum()),
                 "raw_out_of_range_pixels": int(((v < 0) | (v > 1)).sum()),
                 "invalid_mask_pixels": int((~mask).sum()),
                 "min": float(v.min()) if np.isfinite(v).all() else None,
                 "max": float(v.max()) if np.isfinite(v).all() else None}
        if geometry_ok:
            stats["positive_on_catalogue"] = int(((v > 0) & template.catalogue).sum())
            stats["positive_outside_footprint"] = int(((v > 0) & ~template.footprint).sum())
        profile = {"shape": list(source.shape), "count": source.count, "dtype": list(source.dtypes),
                   "crs": str(source.crs), "transform": list(source.transform)[:6],
                   "bounds": list(source.bounds), "internal_mask": len(source.files) == 1}
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size,
            "format_valid": all(checks.values()), "checks": checks,
            "failed_checks": [name for name, ok in checks.items() if not ok],
            "stats": stats, "profile": profile, "organizer_acceptance_verified": False,
            "scientific_eligibility_not_decided_by_this_validator": True}


def write(values: np.ndarray, path: str | Path, template: Template, *, tags: dict | None = None) -> dict:
    """Strict export: reject bad interior input rather than silently clip/repair."""
    path = Path(path)
    a = np.asarray(values)
    if a.shape != template.shape or a.ndim != 2:
        raise ValueError("prediction shape differs from template")
    if not np.issubdtype(a.dtype, np.number) or np.issubdtype(a.dtype, np.complexfloating):
        raise ValueError("prediction must be real numeric")
    inside = a[template.footprint]
    if not np.isfinite(inside).all() or ((inside < 0) | (inside > 1)).any():
        raise ValueError("in-footprint predictions must be finite and in [0,1] before float32 conversion")
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    v = np.where(template.footprint, a, 0).astype(np.float32)
    profile = {"driver": "GTiff", "height": template.shape[0], "width": template.shape[1],
               "count": 1, "dtype": "float32", "crs": template.crs, "transform": template.transform,
               "compress": "deflate", "tiled": True, "blockxsize": 256, "blockysize": 256,
               "nodata": None, "BIGTIFF": "IF_SAFER"}
    with tempfile.NamedTemporaryFile(suffix=".tif", prefix=".gems47-export-", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True), rasterio.open(temporary, "w", **profile) as destination:
            destination.write(v, 1)
            destination.write_mask(template.footprint.astype(np.uint8) * 255)
            destination.set_band_description(1, "fault confidence; unit-dot research prediction")
            destination.update_tags(AREA_OR_POINT="Area", **(tags or {}))
        audit = validate(temporary, template)
        if not audit["format_valid"]:
            raise ValueError(f"serialized contract failed: {audit['failed_checks']}")
        # Hard-link publishes atomically without ever overwriting a racing file.
        os.link(temporary, path)
        temporary.unlink()
        final = validate(path, template)
        if final["sha256"] != audit["sha256"] or not final["format_valid"]:
            path.unlink(missing_ok=True)
            raise ValueError("final artifact changed or failed its independent read-back")
        return final
    finally:
        temporary.unlink(missing_ok=True)
        temporary.with_suffix(temporary.suffix + ".msk").unlink(missing_ok=True)


def single_tiff_zip(tiff: str | Path, path: str | Path) -> dict:
    """Deterministic zip containing exactly the TIFF, never a report/sidecar."""
    tiff, path = Path(tiff), Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    info = zipfile.ZipInfo(tiff.name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    with zipfile.ZipFile(path, "x") as archive:
        archive.writestr(info, tiff.read_bytes())
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        if members != [tiff.name] or hashlib.sha256(archive.read(tiff.name)).hexdigest() != sha256(tiff):
            path.unlink(missing_ok=True)
            raise ValueError("zip contents differ from the verified single TIFF")
    return {"filename": path.name, "sha256": sha256(path), "bytes": path.stat().st_size,
            "members": members, "single_geotiff_verified": True}


def save_receipt(path: Path, receipt: dict) -> None:
    path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
