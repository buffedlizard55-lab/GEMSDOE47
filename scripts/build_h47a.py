#!/usr/bin/env python3
"""Build a local H47-A screening surface from pre-aligned GeoTIFF bands.

This creates a research intermediate, not a competition submission. It does
not calibrate the score or validate performance. Inputs must be locally
available through an authorized source and will not be downloaded here.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gemsdoe47.candidate import compute_h47a_score
from gemsdoe47.validation import _same_grid, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mag-a", required=True, type=Path, help="GeoDAWN acquisition A magnetic grid")
    parser.add_argument("--mag-b", required=True, type=Path, help="overlapping acquisition B magnetic grid")
    parser.add_argument("--rad-a", type=Path, help="optional acquisition A radiometric grid")
    parser.add_argument("--rad-b", type=Path, help="optional acquisition B radiometric grid")
    parser.add_argument("--band-a", type=int, default=1, help="band index for magnetic A (default: 1)")
    parser.add_argument("--band-b", type=int, default=1, help="band index for magnetic B (default: 1)")
    parser.add_argument("--rad-band-a", type=int, default=1)
    parser.add_argument("--rad-band-b", type=int, default=1)
    parser.add_argument("--template", required=True, type=Path, help="official one-band sample/template grid")
    parser.add_argument("--out", required=True, type=Path, help="local research output, e.g. data/derived/h47a.tif")
    parser.add_argument("--quantile", type=float, default=0.995)
    parser.add_argument("--artifact-penalty", type=float, default=0.0, help="holdout-tunable; defaults to no suppression")
    parser.add_argument("--flight-bearing-a", type=float, help="compass azimuth clockwise from map north")
    parser.add_argument("--flight-bearing-b", type=float, help="compass azimuth clockwise from map north")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if (args.rad_a is None) != (args.rad_b is None):
        parser.error("--rad-a and --rad-b must be used together")
    if (args.flight_bearing_a is None) != (args.flight_bearing_b is None):
        parser.error("provide both flight bearings or neither")
    if args.artifact_penalty > 0 and args.flight_bearing_a is None:
        parser.error("a nonzero artifact penalty requires both flight bearings")
    if not args.template.is_file():
        parser.error(f"template not found: {args.template}")
    for label, path in (("mag-a", args.mag_a), ("mag-b", args.mag_b), ("rad-a", args.rad_a), ("rad-b", args.rad_b)):
        if path is not None and not path.is_file():
            parser.error(f"{label} input not found: {path}")

    args.out = args.out.resolve()
    if not args.out.is_relative_to((ROOT / "data").resolve()) and not args.out.is_relative_to((ROOT / "artifacts").resolve()):
        parser.error("research intermediates must be written under ignored data/ or artifacts/ folders")
    existing_sidecar = args.out.with_suffix(args.out.suffix + ".json")
    if (args.out.exists() or existing_sidecar.exists()) and not args.overwrite:
        parser.error(f"output or receipt already exists; choose a new path or pass --overwrite: {args.out}")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(args.template) as template:
        if template.count != 1:
            parser.error(f"template must have one band, found {template.count}")
        if template.crs is None or not template.crs.is_projected:
            parser.error("template CRS must be projected before computing map-space gradients")
        if abs(template.transform.b) > 1e-12 or abs(template.transform.d) > 1e-12:
            parser.error("rotated grids are unsupported; align inputs to a north-up grid first")
        dx = float(template.transform.a)
        dy = float(template.transform.e)
        if dx == 0 or dy == 0:
            parser.error("template has zero-sized pixels")
        template_profile = template.profile.copy()

    loaded: dict[str, np.ma.MaskedArray] = {}
    paths = {
        "magnetic_a": (args.mag_a, args.band_a),
        "magnetic_b": (args.mag_b, args.band_b),
    }
    if args.rad_a is not None:
        paths["radiometric_a"] = (args.rad_a, args.rad_band_a)
        paths["radiometric_b"] = (args.rad_b, args.rad_band_b)
    for name, (path, band) in paths.items():
        with rasterio.open(path) as dataset:
            if band < 1 or band > dataset.count:
                parser.error(f"{name} band {band} is outside the raster (has {dataset.count} bands)")
            with rasterio.open(args.template) as template:
                if not _same_grid(dataset, template):
                    parser.error(f"{name} grid does not match template; reproject/resample explicitly first")
            loaded[name] = dataset.read(band, masked=True)

    score, diagnostics = compute_h47a_score(
        loaded["magnetic_a"],
        loaded["magnetic_b"],
        radiometric_a=loaded.get("radiometric_a"),
        radiometric_b=loaded.get("radiometric_b"),
        dx=dx,
        dy=dy,
        quantile=args.quantile,
        artifact_penalty=args.artifact_penalty,
        flight_bearing_a=args.flight_bearing_a,
        flight_bearing_b=args.flight_bearing_b,
    )
    profile = template_profile.copy()
    for key in ("blockxsize", "blockysize", "interleave"):
        profile.pop(key, None)
    profile.update(
        driver="GTiff",
        count=1,
        dtype="float32",
        nodata=np.nan,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )

    with tempfile.NamedTemporaryFile(prefix=".h47a-", suffix=".tmp.tif", dir=args.out.parent, delete=False) as tmp:
        temporary_path = Path(tmp.name)
    sidecar = args.out.with_suffix(args.out.suffix + ".json")
    temporary_sidecar = sidecar.with_suffix(sidecar.suffix + ".tmp")
    try:
        with rasterio.open(temporary_path, "w", **profile) as destination:
            destination.write(score.astype(np.float32), 1)
            destination.update_tags(
                PROJECT="GEMSDOE47",
                HYPOTHESIS="H47-A",
                SURFACE_TYPE="uncalibrated screening score; not submission-ready",
                VALIDATION_STATUS="NOT_RUN",
                DESCRIPTION="Acquisition-invariant GeoDAWN edge support; see project documentation",
            )
        with rasterio.open(temporary_path) as check:
            written = check.read(1)
            if check.count != 1 or check.dtypes[0] != "float32":
                raise ValueError("screening output failed its single-band float32 write check")
            if check.width != template_profile["width"] or check.height != template_profile["height"]:
                raise ValueError("screening output dimensions changed during write")
            if not np.allclose(tuple(check.transform)[:6], tuple(template_profile["transform"])[:6], rtol=0, atol=1e-9):
                raise ValueError("screening output transform changed during write")
            if check.crs != template_profile["crs"]:
                raise ValueError("screening output CRS changed during write")
            valid_written = np.isfinite(written)
            if not valid_written.any():
                raise ValueError("screening surface has no finite pixels in the survey overlap")
            if np.any((written[valid_written] < 0.0) | (written[valid_written] > 1.0)):
                raise ValueError("screening surface contains a value outside [0, 1]")
            if check.nodata is None or not np.isnan(check.nodata):
                raise ValueError("screening output nodata tag is not NaN")

        input_hashes = {name: sha256_file(path) for name, (path, _) in paths.items()}
        diagnostics.update(
            {
                "status": "SCREENING_SURFACE_BUILT_VALIDATION_NOT_RUN",
                "template_sha256": sha256_file(args.template),
                "input_sha256": input_hashes,
                "output_path": str(args.out),
                "output_sha256": sha256_file(temporary_path),
                "grid": {
                    "width": int(template_profile["width"]),
                    "height": int(template_profile["height"]),
                    "crs": str(template_profile.get("crs")),
                    "transform": list(template_profile["transform"])[:6],
                },
            }
        )
        temporary_sidecar.write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary_path, args.out)
        os.replace(temporary_sidecar, sidecar)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        temporary_sidecar.unlink(missing_ok=True)
        raise

    print(json.dumps(diagnostics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
