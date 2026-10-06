"""The submission writer and the range-check diagnosis, on a synthetic grid.

These tests need no restored data, so they run in CI. The point of the range tests
is to reproduce the reported portal rejection and prove the fix: a NaN-intolerant
check of the form ``np.all((v>=0)&(v<=1))`` returns False for the ``-nan``
convention and True for the all-finite one, even though every real value in both is
exactly 0 or 1.
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


def _write(tmp_path, tmpl, dots, mode):
    p = tmp_path / f"s-{mode}.tif"
    S.write_submission(np.where(dots, 1.0, 0.0).astype(np.float32), p, mode=mode, template=tmpl)
    return p


def test_template_evaluated_excludes_catalogue_and_outside(tmpl):
    assert tmpl.evaluated.sum() == (tmpl.footprint & ~tmpl.catalogue).sum()
    assert not (tmpl.evaluated & tmpl.catalogue).any()
    assert not (tmpl.evaluated & ~tmpl.footprint).any()


def test_allfinite_variant_passes_every_range_reading(tmp_path, tmpl, dots):
    p = _write(tmp_path, tmpl, dots, "zeros")
    v = S.validate_submission(p, template=tmpl)
    assert v["all_checks_passed"] is True
    assert v["recommended_for_upload"] is True
    assert v["passes_nan_intolerant_range_check"] is True
    assert v["hard_failures"] == []
    assert v["stats"]["n_nan"] == 0
    assert v["stats"]["n_emitted"] == 400
    assert v["stats"]["v_min"] == 0.0 and v["stats"]["v_max"] == 1.0
    assert v["stats"]["n_emitted_on_catalogue"] == 0
    assert v["stats"]["n_emitted_outside_footprint"] == 0
    with rasterio.open(p) as s:
        assert s.count == 1 and s.dtypes[0] == "float32" and str(s.crs) == "EPSG:32611"
        assert s.nodata is None
        assert np.isfinite(s.read(1)).all()


def test_nan_variant_is_the_documented_failure_mode(tmp_path, tmpl, dots):
    p = _write(tmp_path, tmpl, dots, "nan")
    v = S.validate_submission(p, template=tmpl)
    with rasterio.open(p) as s:
        arr = s.read(1)
    # THE BUG: NaN fails both comparisons, so a NaN-intolerant check rejects a file
    # whose every real value is exactly 0 or 1.
    assert np.all((arr >= 0) & (arr <= 1)) is np.False_
    assert v["passes_nan_intolerant_range_check"] is False
    assert v["recommended_for_upload"] is False
    # ... while the NaN-tolerant reading passes, and no value is out of range.
    assert v["passes_nan_tolerant_range_check"] is True
    assert v["all_checks_passed"] is True          # NaN is legal, just riskier
    fin = np.isfinite(arr)
    assert set(np.unique(arr[fin]).tolist()) <= {0.0, 1.0}
    # NaN appears only outside the footprint
    assert ((~fin) & tmpl.footprint).sum() == 0
    assert np.array_equal(~fin, ~tmpl.footprint)


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
