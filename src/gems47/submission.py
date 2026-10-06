"""Submission writer + local GeoTIFF-format and range validator (not a portal oracle).

Why this module exists
----------------------
The reported portal rejection was::

    "Predicted values must be in range [0, 1]"

A scan of 29 accessible sibling GeoTIFFs recorded two out-of-footprint
conventions: ``-nan`` files have 7,111,787 NaN pixels and fail a NaN-intolerant
``np.all((v >= 0) & (v <= 1))`` check; all-finite ``-zeros`` variants pass that
check. The rejected file from the earlier portal report is unavailable, so this
is a demonstrated failure mode in the scanned files, not a root-cause diagnosis
of the earlier rejection.

``validate_submission`` runs NaN-intolerant and NaN-tolerant range readings plus
local metadata, grid, footprint, and nodata checks. The all-finite (zeros)
variant is useful for diagnosing NaN-intolerant range logic, but zeros outside
the supplied footprint do not satisfy the official page's null/NaN-outside
wording. The NaN variant matches the available mirrored sample's nodata
convention, but that mirror is not organizer-authenticated and the prior
rejection's cause is unknown. Neither mode is recommended for upload without
checking the exact authorized inputs and current portal behavior.

The official submission-format specification (checked 2026-10-06) is at:
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format
It requires matching the training-data CRS, 100 m resolution and bounds, null or
NaN outside the bounds, one float32 layer, and predictions in [0, 1]. The local
template in this checkout comes from a group-hosted mirror and is not organizer
authentication; verify the authorized training data and template before upload.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

from . import grid as G


def write_submission(values: np.ndarray, path: Path | str, mode: str = "nan",
                     template: G.Template | None = None) -> Path:
    """Write a single-band float32 GeoTIFF on the supplied template grid.

    The default ``mode="nan"`` writes NaN outside the supplied footprint.
    The template must be verified against authorized training data before any
    upload. ``mode="zeros"`` is an explicit diagnostic that writes 0.0 outside
    the footprint and leaves
    nodata unset; this tests an all-finite variant but does not meet the
    official null/NaN-outside wording for the supplied footprint. It passes a
    NaN-intolerant range check.
    ``mode="nan"``    NaN outside the footprint, nodata = nan. This matches the
                      available mirrored ``sample_submission.tif`` convention,
                      but the mirror is not organizer authentication. A raw
                      NaN-intolerant ``np.all((v>=0)&(v<=1))`` check fails; no
                      portal-acceptance claim is made for either mode.
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
    """Run local format/range checks, not a portal oracle.

    ``required_local_checks_passed`` covers required local grid/footprint/value
    checks. NaN-sensitive whole-array readings are diagnostics and are reported
    separately; neither result establishes organizer acceptance.
    """
    path = Path(path)
    t = template or G.load_template()
    checks: dict[str, bool] = {}
    with rasterio.open(path) as src:
        v = src.read(1)
        nodata_value = src.nodata
        nodata = ("NaN" if nodata_value is not None and np.isnan(nodata_value)
                  else nodata_value)
        info = dict(driver=src.driver, count=src.count, dtype=str(src.dtypes[0]),
                    crs=str(src.crs), width=src.width, height=src.height,
                    nodata=nodata, shape=list(src.shape),
                    transform=list(src.transform)[:6],
                    bounds=[src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top])
        desc = src.descriptions

    nan_values = np.isnan(v)
    infinite_values = np.isinf(v)
    fin = np.isfinite(v)
    n_nan = int(nan_values.sum())
    n_infinite = int(infinite_values.sum())

    checks["single_band"] = info["count"] == 1
    checks["dtype_float32"] = info["dtype"] == "float32"
    checks["crs_epsg32611"] = info["crs"] in ("EPSG:32611", "epsg:32611")
    shape_matches = tuple(info["shape"]) == tuple(t.shape)
    checks["shape_matches_template"] = shape_matches
    checks["transform_matches_template"] = (
        Affine(*info["transform"]) == t.transform)
    # Bounds and resolution are derived from the TEMPLATE, not from module-level
    # constants, so the validator also works on a synthetic grid in the tests and
    # cannot silently pass a file that merely matches hard-coded numbers.
    tb = rasterio.transform.array_bounds(t.shape[0], t.shape[1], t.transform)
    checks["resolution_100m"] = (
        abs(abs(info["transform"][0]) - 100.0) < 1e-9
        and abs(abs(info["transform"][4]) - 100.0) < 1e-9)
    checks["bounds_match_template"] = all(abs(a - b) < 1e-6 for a, b in zip(info["bounds"], tb))
    # "data outside the bounds is null or nan" -> NaN may only appear outside
    # the footprint; NaN inside it would silently delete a prediction. Infinity
    # is not a null/NaN marker and is rejected separately below.
    checks["nan_only_outside_footprint"] = bool(
        shape_matches and not (nan_values & t.footprint).any())
    checks["no_infinite_values"] = bool(not infinite_values.any())
    # A finite value outside the supplied template footprint is not the null/NaN
    # representation requested by the published submission-format page.
    checks["outside_template_footprint_is_nodata"] = False  # set from masked read below
    checks["masked_pixels_only_outside_footprint"] = False  # set from masked read below
    # A no-NaN variant is useful for diagnostics, but not a portal-safety finding.
    checks["all_pixels_finite"] = bool(fin.all())
    checks["finite_where_footprint"] = bool(shape_matches and fin[t.footprint].all())
    checks["no_nodata_sentinel_values"] = bool(not (v[fin] <= -1e30).any())

    # ---- the range checks, in every reading we could construct --------------
    fv = v[fin]
    emitted = fin & (v > 0)
    checks["RANGE_nan_intolerant: np.all((v>=0)&(v<=1))"] = bool(np.all((v >= 0) & (v <= 1)))
    checks["RANGE_nan_tolerant: finite values within [0,1]"] = bool(
        np.all((fv >= 0) & (fv <= 1)))
    emitted_values = v[emitted]
    checks["RANGE_emitted_values_within_[0,1]"] = bool(
        np.all((emitted_values >= 0) & (emitted_values <= 1)))
    checks["RANGE_min_max_reported"] = True
    with rasterio.open(path) as src:
        mv = src.read(1, masked=True)
    nodata_mask = np.ma.getmaskarray(mv)
    if shape_matches:
        outside_nodata = (nan_values | nodata_mask)[~t.footprint]
        checks["outside_template_footprint_is_nodata"] = bool(outside_nodata.all())
        checks["masked_pixels_only_outside_footprint"] = bool(
            not (nodata_mask & t.footprint).any())
    masked_values = np.ma.getdata(mv)
    masked_finite = masked_values[~nodata_mask & np.isfinite(masked_values)]
    checks["RANGE_masked_read: finite unmasked values within [0,1]"] = bool(
        np.all((masked_finite >= 0) & (masked_finite <= 1)))
    ma = np.ma.getdata(np.ma.filled(mv, 0.0)) if hasattr(mv, "mask") else mv
    checks["RANGE_filled_then_checked"] = bool(np.all((ma >= 0) & (ma <= 1)))
    stats = dict(
        n_pixels=int(v.size), n_finite=int(fin.sum()), n_nan=n_nan,
        n_infinite=n_infinite,
        n_footprint=int(t.footprint.sum()), n_emitted=int(emitted.sum()),
        n_emitted_on_catalogue=(int((emitted & t.catalogue).sum()) if shape_matches else None),
        n_emitted_outside_footprint=(int((emitted & ~t.footprint).sum()) if shape_matches else None),
        v_min=float(fv.min()) if fv.size else None,
        v_max=float(fv.max()) if fv.size else None,
        v_unique_count=int(np.unique(fv).size),
        v_unique_values=[float(x) for x in np.unique(fv)[:8]],
        emitted_mass=float(v[emitted].sum()),
        band_descriptions=list(desc),
    )
    # Keep raw/full-array NaN-sensitive range readings separate from required
    # local format checks: the published instructions permit null/NaN outside
    # bounds, but a portal may implement its own range validation. Neither these
    # readings nor the remaining local checks establish organizer acceptance.
    SOFT = ("RANGE_nan_intolerant", "RANGE_filled_then_checked",
            "all_pixels_finite", "RANGE_min_max_reported")
    hard_fail = [k for k, ok in checks.items()
                 if not ok and not any(k.startswith(s2) for s2 in SOFT)]
    nan_intolerant_ok = checks["RANGE_nan_intolerant: np.all((v>=0)&(v<=1))"]
    nan_tolerant_ok = checks["RANGE_nan_tolerant: finite values within [0,1]"]
    required_local_ok = bool(not hard_fail and nan_tolerant_ok)
    diagnostic_failures = [
        key for key, ok in checks.items()
        if not ok and any(key.startswith(prefix) for prefix in SOFT)
    ]
    return dict(path=str(path), format=info, stats=stats, checks=checks,
                hard_failures=hard_fail,
                diagnostic_failures=diagnostic_failures,
                passes_nan_intolerant_range_check=nan_intolerant_ok,
                passes_nan_tolerant_range_check=nan_tolerant_ok,
                required_local_checks_passed=required_local_ok,
                all_checks_passed=required_local_ok,  # historical alias; ignores soft diagnostics
                recommended_for_upload=False,
                upload_recommendation_scope=(
                    "not established by a local validator; check the current official requirements and portal behavior"
                ))


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
