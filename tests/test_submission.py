"""The submission writer and local range-check behaviors, on a synthetic grid.

These tests need no restored data, so they run in CI. They show that a local
NaN-intolerant check of the form ``np.all((v>=0)&(v<=1))`` returns False for a
file containing NaNs and True for an all-finite file with the same finite values.
The earlier portal-rejected file's bytes are unavailable, so these tests do not
identify the cause of that rejection or establish organizer acceptance.
"""
from __future__ import annotations

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

from gems47 import grid as G
from gems47 import submission as S


@pytest.fixture(scope="module")
def tmpl():
    H, W = 60, 50
    footprint = np.zeros((H, W), bool)
    footprint[5:55, 5:45] = True
    catalogue = np.zeros((H, W), bool)
    catalogue[20:22, 10:30] = True
    return G.Template(shape=(H, W),
                      transform=Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
                      crs="EPSG:32611", footprint=footprint, catalogue=catalogue)


@pytest.fixture(scope="module")
def dots(tmpl):
    rng = np.random.default_rng(47)
    d = np.zeros(tmpl.shape, bool)
    idx = np.flatnonzero(tmpl.evaluated.ravel())
    d.ravel()[idx[rng.choice(idx.size, 400, replace=False)]] = True
    return d


def _write(tmp_path, tmpl, dots, mode, values=None):
    p = tmp_path / f"s-{mode}.tif"
    arr = np.where(dots, 1.0, 0.0).astype(np.float32) if values is None else values
    S.write_submission(arr, p, mode=mode, template=tmpl)
    return p


def test_template_evaluated_excludes_catalogue_and_outside(tmpl):
    assert tmpl.evaluated.sum() == (tmpl.footprint & ~tmpl.catalogue).sum()
    assert not (tmpl.evaluated & tmpl.catalogue).any()
    assert not (tmpl.evaluated & ~tmpl.footprint).any()


def test_allfinite_variant_passes_range_readings_but_fails_outside_nodata_check(tmp_path, tmpl, dots):
    p = _write(tmp_path, tmpl, dots, "zeros")
    v = S.validate_submission(p, template=tmpl)
    assert v["required_local_checks_passed"] is False
    assert v["all_checks_passed"] is False  # historical alias for required local checks
    assert v["recommended_for_upload"] is False
    assert v["passes_nan_intolerant_range_check"] is True
    assert v["checks"]["outside_template_footprint_is_nodata"] is False
    assert v["checks"]["masked_pixels_only_outside_footprint"] is True
    assert v["hard_failures"] == ["outside_template_footprint_is_nodata"]
    assert v["stats"]["n_nan"] == 0
    assert v["stats"]["n_emitted"] == 400
    assert v["stats"]["v_min"] == 0.0 and v["stats"]["v_max"] == 1.0
    assert v["stats"]["n_emitted_on_catalogue"] == 0
    assert v["stats"]["n_emitted_outside_footprint"] == 0
    with rasterio.open(p) as s:
        assert s.count == 1 and s.dtypes[0] == "float32" and str(s.crs) == "EPSG:32611"
        assert s.nodata is None
        assert np.isfinite(s.read(1)).all()


def test_nan_variant_fails_a_nan_intolerant_local_range_check(tmp_path, tmpl, dots):
    p = _write(tmp_path, tmpl, dots, "nan")
    v = S.validate_submission(p, template=tmpl)
    with rasterio.open(p) as s:
        arr = s.read(1)
    # NaN fails both comparisons, so this particular NaN-intolerant local check
    # rejects the synthetic file even though its finite values are exactly 0 or 1.
    # This demonstrates a possible failure mode, not the cause of the earlier portal rejection.
    assert np.all((arr >= 0) & (arr <= 1)) is np.False_
    assert v["passes_nan_intolerant_range_check"] is False
    assert v["recommended_for_upload"] is False
    # ... while the NaN-tolerant local reading passes, and no finite value is out of range.
    assert v["passes_nan_tolerant_range_check"] is True
    assert v["format"]["nodata"] == "NaN"       # JSON-safe representation of the TIFF metadata
    assert v["checks"]["outside_template_footprint_is_nodata"] is True
    assert v["checks"]["masked_pixels_only_outside_footprint"] is True
    assert v["required_local_checks_passed"] is True
    assert v["all_checks_passed"] is True          # historical alias; no portal claim
    assert any("RANGE_nan_intolerant" in key for key in v["diagnostic_failures"])
    fin = np.isfinite(arr)
    assert set(np.unique(arr[fin]).tolist()) <= {0.0, 1.0}
    # NaN appears only outside the footprint
    assert ((~fin) & tmpl.footprint).sum() == 0
    assert np.array_equal(~fin, ~tmpl.footprint)


def test_writer_defaults_to_nan_outside_footprint(tmp_path, tmpl, dots):
    p = tmp_path / "default-mode.tif"
    S.write_submission(np.where(dots, 1.0, 0.0).astype(np.float32), p, template=tmpl)
    with rasterio.open(p) as src:
        values = src.read(1)
        assert np.isnan(src.nodata)
    assert np.isnan(values[~tmpl.footprint]).all()
    result = S.validate_submission(p, template=tmpl)
    assert result["required_local_checks_passed"] is True
    assert result["checks"]["outside_template_footprint_is_nodata"] is True
    assert result["recommended_for_upload"] is False


def test_raw_nan_outside_without_nodata_tag_is_locally_supported(tmp_path, tmpl, dots):
    p = tmp_path / "raw-nan-no-tag.tif"
    values = np.where(tmpl.footprint, np.where(dots, 1.0, 0.0), np.nan).astype(np.float32)
    with rasterio.open(
        p, "w", driver="GTiff", height=tmpl.shape[0], width=tmpl.shape[1],
        count=1, dtype="float32", crs=tmpl.crs, transform=tmpl.transform,
    ) as dst:
        dst.write(values, 1)
    with rasterio.open(p) as src:
        assert src.nodata is None
    result = S.validate_submission(p, template=tmpl)
    assert result["checks"]["outside_template_footprint_is_nodata"] is True
    assert result["checks"]["masked_pixels_only_outside_footprint"] is True
    assert result["checks"]["RANGE_filled_then_checked"] is False
    assert result["required_local_checks_passed"] is True
    assert result["all_checks_passed"] is True
    assert "RANGE_filled_then_checked" in result["diagnostic_failures"]
    assert result["recommended_for_upload"] is False


def test_validator_does_not_treat_infinity_as_null_or_nan(tmp_path, tmpl, dots):
    p = _write(tmp_path, tmpl, dots, "nan")
    with rasterio.open(p, "r+") as dst:
        arr = dst.read(1)
        arr[0, 0] = np.inf  # outside the footprint, but not a null/NaN marker
        dst.write(arr, 1)
    result = S.validate_submission(p, template=tmpl)
    assert result["checks"]["no_infinite_values"] is False
    assert result["checks"]["outside_template_footprint_is_nodata"] is False
    assert result["stats"]["n_infinite"] == 1
    assert "no_infinite_values" in result["hard_failures"]
    assert "outside_template_footprint_is_nodata" in result["hard_failures"]
    assert result["required_local_checks_passed"] is False


def test_validator_rejects_nodata_mask_inside_footprint(tmp_path, tmpl, dots):
    p = tmp_path / "nodata-inside.tif"
    with rasterio.open(
        p, "w", driver="GTiff", height=tmpl.shape[0], width=tmpl.shape[1],
        count=1, dtype="float32", crs=tmpl.crs, transform=tmpl.transform,
        nodata=0.0,
    ) as dst:
        dst.write(np.where(dots, 1.0, 0.0).astype(np.float32), 1)
    result = S.validate_submission(p, template=tmpl)
    assert result["checks"]["outside_template_footprint_is_nodata"] is True
    assert result["checks"]["masked_pixels_only_outside_footprint"] is False
    assert "masked_pixels_only_outside_footprint" in result["hard_failures"]
    assert result["required_local_checks_passed"] is False


def test_writer_zeroes_outside_footprint_but_reports_masked_pixels(tmp_path, tmpl, dots):
    d = dots.copy()
    d[tmpl.catalogue] = True          # emit on masked catalogue pixels
    d[~tmpl.footprint] = True         # and outside the footprint
    p = _write(tmp_path, tmpl, d, "zeros")
    v = S.validate_submission(p, template=tmpl)
    # the writer forces zeros outside the footprint (that is what makes the file
    # all-finite), but it does NOT silently drop masked-pixel mass: emitting on a
    # catalogue pixel is legal and score-neutral (Hedge-v2 did exactly this), so it
    # is reported rather than removed.
    assert v["stats"]["n_emitted_outside_footprint"] == 0
    assert v["stats"]["n_emitted_on_catalogue"] == int(tmpl.catalogue.sum())
    assert v["checks"]["outside_template_footprint_is_nodata"] is False


def test_writer_rejects_out_of_range_input(tmp_path, tmpl, dots):
    p = tmp_path / "bad.tif"
    bad = np.where(dots, 1.7, -0.3).astype(np.float32)
    S.write_submission(bad, p, mode="zeros", template=tmpl)
    with rasterio.open(p) as s:
        arr = s.read(1)
    assert arr.max() <= 1.0 and arr.min() >= 0.0    # clipped by the writer


def test_writer_rejects_wrong_shape(tmpl):
    with pytest.raises(ValueError):
        S.write_submission(np.zeros((3, 3), np.float32), "/tmp/x.tif", template=tmpl)


def test_validator_rejects_non_100m_resolution(tmp_path, tmpl):
    p = tmp_path / "wrong-resolution.tif"
    with rasterio.open(
        p, "w", driver="GTiff", height=tmpl.shape[0], width=tmpl.shape[1],
        count=1, dtype="float32", crs=tmpl.crs,
        transform=Affine(50.0, 0.0, 243350.0, 0.0, -50.0, 4508550.0),
    ) as dst:
        dst.write(np.zeros(tmpl.shape, np.float32), 1)
    result = S.validate_submission(p, template=tmpl)
    assert result["checks"]["resolution_100m"] is False
    assert result["checks"]["transform_matches_template"] is False


def test_validator_reports_wrong_shape_without_crashing(tmp_path, tmpl):
    p = tmp_path / "wrong-shape.tif"
    with rasterio.open(
        p, "w", driver="GTiff", height=20, width=20, count=1, dtype="float32",
        crs=tmpl.crs, transform=tmpl.transform,
    ) as dst:
        dst.write(np.zeros((20, 20), np.float32), 1)
    result = S.validate_submission(p, template=tmpl)
    assert result["checks"]["shape_matches_template"] is False
    assert "outside_template_footprint_is_nodata" in result["hard_failures"]
    assert result["stats"]["n_emitted_on_catalogue"] is None


def test_writer_rejects_unknown_mode(tmpl, dots):
    with pytest.raises(ValueError):
        S.write_submission(np.zeros(tmpl.shape, np.float32), "/tmp/x.tif", mode="wat", template=tmpl)


def test_diff_report_detects_identical_and_different(tmp_path, tmpl, dots):
    a = _write(tmp_path, tmpl, dots, "zeros")
    b = _write(tmp_path, tmpl, dots, "nan")
    d = S.diff_report(a, b)
    assert d["identical"] is True and d["jaccard"] == 1.0 and d["a_only"] == 0
    other = dots.copy()
    dropped = np.flatnonzero(other.ravel())[:120]      # 120 pixels that ARE dots
    other.ravel()[dropped] = False
    c = tmp_path / "other.tif"
    S.write_submission(np.where(other, 1.0, 0.0).astype(np.float32), c, mode="zeros", template=tmpl)
    d2 = S.diff_report(a, c)
    assert d2["identical"] is False and 0.0 < d2["jaccard"] < 1.0
    assert d2["a_only"] == 120 and d2["b_only"] == 0 and d2["intersection"] == 280


def test_sentinel_values_would_be_flagged(tmp_path, tmpl, dots):
    p = tmp_path / "sentinel.tif"
    arr = np.where(dots, np.float32(1.0), np.float32(-3.4028234663852886e38))
    with rasterio.open(p, "w", driver="GTiff", height=tmpl.shape[0], width=tmpl.shape[1],
                       count=1, dtype="float32", crs=tmpl.crs, transform=tmpl.transform) as dst:
        dst.write(arr, 1)
    v = S.validate_submission(p, template=tmpl)
    assert v["checks"]["no_nodata_sentinel_values"] is False
    assert "no_nodata_sentinel_values" in v["hard_failures"]


def test_allfinite_mode_writes_byte_identical_zeros_mode(tmp_path, tmpl, dots):
    """``allfinite`` is the submission-named alias of the all-finite convention."""
    a = _write(tmp_path, tmpl, dots, "zeros")
    b = _write(tmp_path, tmpl, dots, "allfinite")
    assert a.read_bytes() == b.read_bytes()
    import numpy as np
    with rasterio.open(b) as src:
        v = src.read(1)
        assert src.nodata is None
        assert np.isfinite(v).all()
        # the exact range reading a NaN-intolerant portal check applies
        assert np.all((v >= 0) & (v <= 1))
        assert (v[~tmpl.footprint] == 0).all()
        assert float(v.max()) == 1.0 and float(v.min()) == 0.0


def test_allfinite_mode_clips_and_sanitises(tmp_path, tmpl, dots):
    bad = np.where(dots, np.float32(7.0), np.float32(np.nan)).astype(np.float32)
    p = _write(tmp_path, tmpl, dots, "allfinite", values=bad)
    with rasterio.open(p) as src:
        v = src.read(1)
    assert np.isfinite(v).all()
    assert float(v.max()) <= 1.0 and float(v.min()) >= 0.0
    assert (v[~tmpl.footprint] == 0).all()
