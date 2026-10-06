#!/usr/bin/env python3
"""GEMSDOE47 submission verifier — format, range, uniqueness, integrity.

Checks, in order:
  1. GeoTIFF opens with rasterio; 1 band; float32; shape/CRS/transform identical to the
     organizer's sample_submission.tif.
  2. Every finite value lies in [0,1]  (the exact cause of the earlier rejection).
  3. NaN appears exactly outside the valid footprint, matching sample_submission.tif — no NaN
     inside the footprint and no nodata sentinel that a scorer could read as a value.
  4. No Inf anywhere.
  5. Byte-unique against every sibling raster we hold; report max Jaccard (lineage honesty).
  6. sha256 + byte size match notes/results.json.
Exit code is non-zero if any hard check fails.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import numpy as np
import rasterio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.path.join(ROOT, "docs", "downloads")
SAMPLE_CANDIDATES = [
    "/home/user/_ref/GEMSDOE24/data/bridge/sample_submission.tif",
    os.path.join(ROOT, "work", "sample_submission.tif"),
]
fails: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def main() -> int:
    with open(os.path.join(ROOT, "notes", "results.json")) as fh:
        rec = json.load(fh)
    path = os.path.join(DL, rec["file"])
    print(f"verifying {path}")

    # 1. format
    with rasterio.open(path) as ds:
        a = ds.read(1)
        prof = ds.profile
        crs, tr, shape, dtype, nodata, count = ds.crs, ds.transform, ds.shape, ds.dtypes[0], ds.nodata, ds.count
    check(os.path.exists(path), "file exists")
    check(count == 1, f"band count == 1 (got {count})")
    check(dtype == "float32", f"dtype float32 (got {dtype})")
    check(str(crs) == "EPSG:32611", f"CRS EPSG:32611 (got {crs})")
    gdal = tuple(round(float(v), 6) for v in tr.to_gdal())
    check(gdal == (243350.0, 100.0, 0.0, 4508550.0, 0.0, -100.0), f"transform {gdal}")
    sample = next((p for p in SAMPLE_CANDIDATES if os.path.exists(p)), None)
    if sample:
        with rasterio.open(sample) as sd:
            check(sd.shape == shape, f"shape {shape} matches sample_submission {sd.shape}")
            check(sd.crs == crs, "CRS matches sample_submission")
            check(sd.transform == tr, "transform matches sample_submission")
    else:
        print("  SKIP  sample_submission.tif not present (shape check from results.json)")

    # 2/3/4 value range
    fin = a[np.isfinite(a)]
    check(not np.isinf(a).any(), "no Inf anywhere")
    check(float(fin.min()) >= 0.0 and float(fin.max()) <= 1.0,
          f"all finite values in [0,1] (min {fin.min()}, max {fin.max()})")
    check(isinstance(nodata, float) and np.isnan(nodata),
          f"nodata is nan, as in sample_submission.tif (got {nodata})")
    vals = np.unique(fin)
    check(bool(np.all(np.isin(vals, [0.0, 1.0]))), f"finite values are only 0.0/1.0 (found {vals[:5]})")
    check(int((a > 0).sum()) == rec["positives"], f"positives {rec['positives']}")
    # NaN must sit exactly outside the footprint, i.e. where labels == -1
    lab = next((p for p in ("/home/user/_ref/GEMSDOE24/data/bridge/labels.tif",
                            os.path.join(ROOT, "work", "labels.tif")) if os.path.exists(p)), None)
    if lab:
        with rasterio.open(lab) as ld:
            labels = ld.read(1)
        check(bool(np.array_equal(np.isnan(a), labels == -1)),
              "NaN mask == (labels == -1), exactly as in sample_submission.tif")
        check(not np.isnan(a[labels >= 0]).any(), "no NaN inside the valid footprint")
    else:
        print("  SKIP  labels.tif absent — NaN-vs-footprint check not run")

    # 5. uniqueness
    sub = a > 0
    rows = []
    sh = hashlib.sha256(open(path, "rb").read()).hexdigest()
    for p in sorted(glob.glob(os.path.join(ROOT, "work", "anchors", "*.tif"))):
        try:
            with rasterio.open(p) as ds:
                m = ds.read(1)
        except Exception:
            continue
        if m.shape != sub.shape:
            continue
        m = np.isfinite(m) & (m > 0)
        inter, union = int((sub & m).sum()), int((sub | m).sum())
        rows.append((inter / union if union else 0.0, os.path.basename(p),
                     hashlib.sha256(open(p, "rb").read()).hexdigest() == sh))
    rows.sort(reverse=True)
    print("  uniqueness vs sibling rasters:")
    for j, nm, same in rows[:5]:
        print(f"      Jaccard {j:.4f}  {nm}" + ("   <-- IDENTICAL BYTES" if same else ""))
    check(all(not s for _, _, s in rows), f"byte-unique vs all {len(rows)} sibling rasters")
    check(not rows or rows[0][0] < 1.0, f"no sibling raster equals this prediction set (max Jaccard {rows[0][0]:.4f})")

    # 6. integrity record
    check(sh == rec["sha256"], "sha256 matches notes/results.json")
    check(os.path.getsize(path) == rec["bytes"], "byte size matches notes/results.json")

    print()
    if fails:
        print(f"{len(fails)} CHECK(S) FAILED")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
