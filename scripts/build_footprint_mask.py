#!/usr/bin/env python3
"""Build a one-band binary footprint from finite, unmasked sample-template cells.

This helper does not authenticate a sample file or determine the organizer's
intended evaluation footprint. Use only an authorized sample-submission file;
compare its grid and footprint to the current official instructions before
validating a prospective submission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_footprint_mask(template_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    """Write and verify a uint8 mask where finite, unmasked template cells are 1."""
    template_path = Path(template_path)
    output_path = Path(output_path)
    if not template_path.is_file():
        raise FileNotFoundError(template_path)
    if template_path.resolve() == output_path.resolve():
        raise ValueError("output mask must not overwrite the sample template")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid_pixels = 0
    with rasterio.open(template_path) as src:
        if src.count != 1:
            raise ValueError(f"sample template has {src.count} bands; expected 1")
        profile = src.profile.copy()
        profile.update(count=1, dtype="uint8", nodata=0, compress="deflate")
        with rasterio.open(output_path, "w", **profile) as dst:
            for _, window in src.block_windows(1):
                sample = src.read(1, window=window, masked=True)
                values = np.asarray(np.ma.getdata(sample))
                inside = np.isfinite(values) & ~np.ma.getmaskarray(sample)
                valid_pixels += int(inside.sum())
                dst.write(inside.astype(np.uint8), 1, window=window)
        source_grid = (src.width, src.height, src.crs, src.transform)

    if valid_pixels == 0:
        output_path.unlink(missing_ok=True)
        raise ValueError("sample template contains no finite, unmasked pixels")

    with rasterio.open(output_path) as check:
        if check.count != 1 or check.dtypes[0] != "uint8" or check.nodata != 0:
            raise ValueError("written footprint mask has an unexpected band/type/nodata profile")
        if (check.width, check.height, check.crs, check.transform) != source_grid:
            raise ValueError("written footprint mask grid differs from the sample template")
        observed_valid = 0
        for _, window in check.block_windows(1):
            values = check.read(1, window=window)
            if not np.isin(values, (0, 1)).all():
                raise ValueError("written footprint mask contains values other than 0 and 1")
            observed_valid += int(np.count_nonzero(values))
        if observed_valid != valid_pixels:
            raise ValueError("written footprint mask count differs from source finite cells")

    return {
        "status": "PASS",
        "template": str(template_path),
        "template_sha256": _sha256(template_path),
        "footprint_mask": str(output_path),
        "footprint_mask_sha256": _sha256(output_path),
        "width": source_grid[0],
        "height": source_grid[1],
        "valid_pixels": valid_pixels,
        "outside_pixels": source_grid[0] * source_grid[1] - valid_pixels,
        "nodata": 0,
        "note": (
            "Mask is derived only from finite, unmasked cells in the given sample template; "
            "it does not verify official provenance or organizer evaluation-footprint semantics."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path, help="authorized sample-submission GeoTIFF")
    parser.add_argument("--output", required=True, type=Path, help="destination one-band uint8 mask GeoTIFF")
    args = parser.parse_args()
    try:
        report = build_footprint_mask(args.template, args.output)
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
