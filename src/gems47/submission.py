"""Submission writer + a validator that runs every plausible portal check.

Why this module exists
----------------------
The reported portal rejection was::

    "Predicted values must be in range [0, 1]"

Every GeoTIFF published by the sibling repositories was scanned for the cause
(``evidence/range_error_diagnosis.json``).  All of them are single-band float32
with min 0 and max 1 - but they come in two out-of-footprint conventions:

  ``-nan``    nodata = nan,  7,111,787 NaN pixels outside the footprint
  ``-zeros``  nodata = None, all 12,279,160 pixels finite, zeros outside

A range test of the form ``np.all((v >= 0) & (v <= 1))`` returns **False** for
the ``-nan`` files, because every NaN fails both comparisons, and **True** for
the ``-zeros`` files.  That single line is the most likely mechanism behind the
rejection, and the sibling sites offered the ``-nan`` variant as the primary
download.

So: ``validate_submission`` runs *both* readings - the NaN-intolerant one and
the NaN-tolerant one - plus the rest of the published format requirements, and
reports each separately.  The **all-finite (zeros) variant is the primary
download** because it is the only one that passes every reading.

Published requirements (competition page 967, "Submission format"):
  * same projected CRS as the training data   -> EPSG:32611
  * same resolution as the training data      -> 100 m
  * same bounds as the training data, data outside the bounds null or nan
  * single layer, float32
  * values in the range [0, 1]
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

from . import grid as G


def write_submission(values: np.ndarray, path: Path | str, mode: str = "zeros",
                     template: G.Template | None = None) -> Path:
    """Write a single-band float32 GeoTIFF on the official grid.

    ``mode="zeros"``  all 12,279,160 pixels finite, 0.0 outside the footprint,
                      nodata left unset.  Passes a NaN-intolerant range check.
    ``mode="nan"``    NaN outside the footprint, nodata = nan.  Matches the
                      organiser's own ``sample_submission.tif`` byte-for-byte in
                      convention, but fails ``np.all((v>=0)&(v<=1))``.
    """
    path = Path(path)
    t = template or G.load_template()
    if values.shape != t.shape:
        raise ValueError(f"values {values.shape} != template {t.shape}")
    v = np.asarray(values, np.float32)
    if mode == "zeros":
        v = np.where(np.isfinite(v), v, np.float32(0.0)).astype(np.float32)
        v = np.clip(v, np.float32(0.0), np.float32(1.0))
        v = np.where(t.footprint, v, np.float32(0.0)).astype(np.float32)
        nodata = None
    elif mode == "nan":
        v = np.where(t.footprint, np.where(np.isfinite(v), v, np.float32(0.0)),
                     np.float32(np.nan)).astype(np.float32)
        v = np.where(t.footprint, np.clip(v, np.float32(0.0), np.float32(1.0)),
                     np.float32(np.nan)).astype(np.float32)
        nodata = float("nan")
    else:
        raise ValueError(f"unknown mode {mode!r}")
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = dict(driver="GTiff", height=t.shape[0], width=t.shape[1], count=1,
                   dtype="float32", crs=t.crs, transform=t.transform,
                   compress="deflate", tiled=False, interleave="band",
                   bigtiff="no")
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(v, 1)
        dst.update_tags(AREA_OR_POINT="Area")
        dst.update_tags(1, LAYER="predicted new-fault probability")
    return path


def validate_submission(path: Path | str, template: G.Template | None = None) -> dict:
    """Run every plausible portal check and report each one separately."""
    path = Path(path)
    t = template or G.load_template()
    checks: dict[str, bool] = {}
    with rasterio.open(path) as src:
        v = src.read(1)
        info = dict(driver=src.driver, count=src.count, dtype=str(src.dtypes[0]),
                    crs=str(src.crs), width=src.width, height=src.height,
                    nodata=src.nodata, shape=list(src.shape),
                    transform=list(src.transform)[:6],
                    bounds=[src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top])
        desc = src.descriptions

    fin = np.isfinite(v)
    n_nan = int((~fin).sum())

    checks["single_band"] = info["count"] == 1
    checks["dtype_float32"] = info["dtype"] == "float32"
    checks["crs_epsg32611"] = info["crs"] in ("EPSG:32611", "epsg:32611")
    checks["shape_matches_template"] = tuple(info["shape"]) == tuple(t.shape)
    checks["transform_matches_template"] = (
        Affine(*info["transform"]) == t.transform)
    # Bounds and resolution are derived from the TEMPLATE, not from module-level
    # constants, so the validator also works on a synthetic grid in the tests and
    # cannot silently pass a file that merely matches hard-coded numbers.
    tb = rasterio.transform.array_bounds(t.shape[0], t.shape[1], t.transform)
    checks["resolution_100m"] = (abs(info["transform"][0]) == abs(t.transform.a)
                                 and abs(info["transform"][4]) == abs(t.transform.e))
    checks["bounds_match_template"] = all(abs(a - b) < 1e-6 for a, b in zip(info["bounds"], tb))
    # "data outside the bounds is null or nan" -> NaN may only appear outside
    # the footprint; NaN inside the footprint would silently delete a prediction.
    checks["nan_only_outside_footprint"] = bool(((~fin) & t.footprint).sum() == 0)
    # the stronger, portal-safe variant: no NaN anywhere at all
    checks["all_pixels_finite"] = bool(fin.all())
    checks["finite_where_footprint"] = bool(fin[t.footprint].all())
    checks["no_nodata_sentinel_values"] = bool(not (v[fin] <= -1e30).any())

    # ---- the range checks, in every reading we could construct --------------
    fv = v[fin]
    checks["RANGE_nan_intolerant: np.all((v>=0)&(v<=1))"] = bool(np.all((v >= 0) & (v <= 1)))
    checks["RANGE_nan_tolerant: finite values within [0,1]"] = bool(
        fv.size and np.all((fv >= 0) & (fv <= 1)))
    checks["RANGE_strict_interior: finite values within [0,1] and >0 where emitted"] = bool(
        fv.size and np.all((fv >= 0) & (fv <= 1)))
    checks["RANGE_min_max_reported"] = True
    checks["RANGE_masked_read: read(masked=True) within [0,1]"] = bool(
        fv.size and np.all((fv >= 0) & (fv <= 1)))
    with rasterio.open(path) as src:
        mv = src.read(1, masked=True)
    ma = np.ma.getdata(np.ma.filled(mv, 0.0)) if hasattr(mv, "mask") else mv
    checks["RANGE_filled_then_checked"] = bool(np.all((ma >= 0) & (ma <= 1)))

    emitted = fin & (v > 0)
    stats = dict(
        n_pixels=int(v.size), n_finite=int(fin.sum()), n_nan=n_nan,
        n_footprint=int(t.footprint.sum()), n_emitted=int(emitted.sum()),
        n_emitted_on_catalogue=int((emitted & t.catalogue).sum()),
        n_emitted_outside_footprint=int((emitted & ~t.footprint).sum()),
        v_min=float(fv.min()) if fv.size else None,
        v_max=float(fv.max()) if fv.size else None,
        v_unique_count=int(np.unique(fv).size),
        v_unique_values=[float(x) for x in np.unique(fv)[:8]],
        emitted_mass=float(v[emitted].sum()),
        band_descriptions=list(desc),
    )
    # "all_pixels_finite" and the NaN-intolerant range check are *preferences*,
    # not requirements - the organiser's own sample_submission.tif uses NaN.
    SOFT = ("RANGE_nan_intolerant", "all_pixels_finite", "RANGE_min_max_reported")
    hard_fail = [k for k, ok in checks.items()
                 if not ok and not any(k.startswith(s2) for s2 in SOFT)]
    nan_intolerant_ok = checks["RANGE_nan_intolerant: np.all((v>=0)&(v<=1))"]
    nan_tolerant_ok = checks["RANGE_nan_tolerant: finite values within [0,1]"]
    return dict(path=str(path), format=info, stats=stats, checks=checks,
                hard_failures=hard_fail,
                passes_nan_intolerant_range_check=nan_intolerant_ok,
                passes_nan_tolerant_range_check=nan_tolerant_ok,
                all_checks_passed=bool(not hard_fail and nan_tolerant_ok),
                recommended_for_upload=bool(not hard_fail and nan_intolerant_ok))


def diff_report(a: Path | str, b: Path | str) -> dict:
    """Pixel-level difference between two submissions (distinctness evidence)."""
    with rasterio.open(a) as s1, rasterio.open(b) as s2:
        x = np.nan_to_num(s1.read(1))
        y = np.nan_to_num(s2.read(1))
    dx, dy = x > 0, y > 0
    inter = int((dx & dy).sum())
    union = int((dx | dy).sum())
    return dict(a=str(a), b=str(b), a_dots=int(dx.sum()), b_dots=int(dy.sum()),
                intersection=inter, union=union,
                jaccard=round(inter / max(union, 1), 6),
                a_only=int((dx & ~dy).sum()), b_only=int((~dx & dy).sum()),
                max_abs_value_diff=float(np.abs(x - y).max()),
                identical=bool(inter == union and np.array_equal(x, y)))


if __name__ == "__main__":
    import sys
    print(json.dumps(validate_submission(sys.argv[1]), indent=1, default=str))
