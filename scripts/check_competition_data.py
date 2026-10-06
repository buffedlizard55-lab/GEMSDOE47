#!/usr/bin/env python3
"""Check authorized local competition files. This script never downloads data."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OFFICIAL_DATA_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/data/"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_input(path: Path | None, data_dir: Path) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else data_dir / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data", help="local folder; ignored by git")
    parser.add_argument("--labels", type=Path, help="path to official raster labels; confirm its exact name after login")
    parser.add_argument("--template", type=Path, help="path to official sample-submission GeoTIFF; confirm its exact name after login")
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()
    features_path = data_dir / "training_features.tif"
    dem_links_path = data_dir / "1m_DEM_links.csv"
    labels_path = resolve_input(args.labels, data_dir)
    template_path = resolve_input(args.template, data_dir)
    required = {
        "training_features.tif (named on official problem page)": features_path,
        "official raster labels (local filename not verified without login)": labels_path,
        "official sample-submission GeoTIFF (local filename not verified without login)": template_path,
        "1m_DEM_links.csv (named on official problem page)": dem_links_path,
    }
    missing = [(label, path) for label, path in required.items() if path is None or not path.is_file()]
    if missing:
        print("BLOCKED: official competition inputs are incomplete.")
        for label, path in missing:
            print(f"  missing: {label}: {path or 'supply --labels / --template'}")
        print(f"\nObtain and identify the official files through your authorized entrant account at:\n  {OFFICIAL_DATA_URL}")
        print("The unauthenticated public page confirms the feature and DEM-link names, but this script does not guess hidden download names.")
        print("This script does not log in, download files, or bypass access controls.")
        return 2

    raster_paths = [features_path, labels_path, template_path]
    try:
        import rasterio
    except ImportError:
        print("Rasterio is not installed; install requirements.txt to inspect TIFF metadata.", file=sys.stderr)
        return 2

    records = []
    reference_grid = None
    grid_mismatches = []
    for path in raster_paths:
        assert path is not None
        with rasterio.open(path) as dataset:
            grid = {
                "width": dataset.width,
                "height": dataset.height,
                "crs": dataset.crs.to_string() if dataset.crs else None,
                "transform": list(dataset.transform)[:6],
            }
            if path == features_path:
                reference_grid = grid
            elif reference_grid is not None and (
                grid["width"] != reference_grid["width"]
                or grid["height"] != reference_grid["height"]
                or grid["crs"] != reference_grid["crs"]
                or not np.allclose(
                    grid["transform"], reference_grid["transform"], rtol=0.0, atol=1e-9
                )
            ):
                grid_mismatches.append(str(path))
            records.append(
                {
                    "path": str(path),
                    "sha256": sha256(path),
                    **grid,
                    "bands": dataset.count,
                    "dtype": list(dataset.dtypes),
                    "nodata": "NaN" if dataset.nodata is not None and str(dataset.nodata) == "nan" else dataset.nodata,
                }
            )

    records.append(
        {
            "path": str(dem_links_path),
            "sha256": sha256(dem_links_path),
            "bytes": dem_links_path.stat().st_size,
        }
    )
    status = "FILES_PRESENT_METADATA_RECORDED"
    if grid_mismatches:
        status = "BLOCKED_GRID_MISMATCH"
    print(json.dumps({"status": status, "grid_mismatches": grid_mismatches, "files": records}, indent=2))
    print("\nNext: inspect label encoding/semantics, CRS, nodata, and exact grid alignment before any experiment.")
    return 2 if grid_mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
