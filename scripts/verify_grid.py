#!/usr/bin/env python3
"""Re-derive every constant in src/gems47/grid.py from the restored bytes.

Exits non-zero if any declared constant disagrees with the rasters, so it can be
used as a pre-flight check before building a submission.

    python3 scripts/verify_grid.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47 import grid as G  # noqa: E402


def main() -> int:
    data = G.data_dir()
    if not (data / "labels.tif").exists():
        print(f"no restored bytes at {data}; run scripts/restore_data.py --group all")
        return 2
    rec = G.receipt(data)
    print(json.dumps(rec, indent=1))
    checks = {
        "shape_matches_declaration": rec["shape"] == list(G.SHAPE),
        "crs_matches_declaration": rec["crs"] == G.CRS,
        "transform_matches_declaration": rec["transform"] == list(G.TRANSFORM)[:6],
        "footprint_matches_declaration": rec["footprint_pixels"] == G.FOOTPRINT_PIXELS,
        "catalogue_matches_declaration": rec["catalogue_pixels"] == G.CATALOGUE_PIXELS,
        "n_pixels_matches_declaration": rec["n_pixels"] == G.N_PIXELS,
        "resolution_is_100m": rec["resolution_m"] == G.RESOLUTION_M,
        "self_consistency_flag": rec["declared_constants_match_bytes"],
    }
    t = G.load_template(data)
    with rasterio.open(data / "sample_submission.tif") as src:
        ss = src.read(1)
        ss_nodata = src.nodata
    checks["sample_footprint_equals_labels_footprint"] = bool(
        np.array_equal(np.isfinite(ss), t.footprint))
    checks["sample_ones_all_on_catalogue"] = bool(((ss > 0) & ~t.catalogue).sum() == 0)
    checks["sample_nodata_is_nan"] = bool(
        ss.dtype == np.float32 and ss_nodata is not None and np.isnan(float(ss_nodata)))
    with rasterio.open(data / "labels.tif") as src:
        checks["labels_nodata_is_minus_one"] = src.nodata == -1
        checks["labels_dtype_int8"] = str(src.dtypes[0]) == "int8"
    with rasterio.open(data / "training_features.tif") as src:
        checks["training_has_19_bands"] = src.count == 19
        checks["training_descriptions_present"] = all(src.descriptions)
        b1 = src.read(1)
        checks["training_sentinel_is_float32_min_not_nan"] = bool(
            (b1 <= -1e30).any() and np.isfinite(b1[b1 <= -1e30]).all())

    print("\nchecks:")
    bad = 0
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
        bad += 0 if v else 1
    print(f"\n{len(checks)-bad}/{len(checks)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
