"""Verification of the ACTUAL shipped GeoTIFFs against the real competition grid.

Marked ``needs_data``: requires the restored bytes (``scripts/restore_data.py
--group all``) so that CI can run the data-free suite without 1.2 GB.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems47 import grid as G
from gems47 import submission as S

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.needs_data


@pytest.fixture(scope="module")
def shipped():
    p = ROOT / "evidence" / "shipped.json"
    if not p.exists():
        pytest.skip("evidence/shipped.json not built; run scripts/ship.py")
    return json.loads(p.read_text())


@pytest.fixture(scope="module")
def tmpl():
    if not (G.data_dir() / "labels.tif").exists():
        pytest.skip("restored competition bytes not present")
    return G.load_template()


def test_grid_constants_match_the_bytes(tmpl):
    rec = G.receipt()
    assert rec["declared_constants_match_bytes"] is True
    assert rec["shape"] == [3730, 3292]
    assert rec["crs"] == "EPSG:32611"
    assert rec["footprint_pixels"] == 5_167_373
    assert rec["catalogue_pixels"] == 60_988
    assert rec["evaluated_pixels"] == 5_106_385


def test_sample_submission_footprint_and_ones(tmpl):
    with rasterio.open(G.data_dir() / "sample_submission.tif") as s:
        ss = s.read(1)
    assert np.array_equal(np.isfinite(ss), tmpl.footprint)
    ones = ss > 0
    assert int(ones.sum()) == 60_988
    assert not (ones & ~tmpl.catalogue).any()      # IR-47-003: the "sample" is not all-zero


def test_training_nodata_is_float32_min_not_nan():
    with rasterio.open(G.data_dir() / "training_features.tif") as s:
        assert s.count == 19
        b = s.read(1)
    assert (b <= -1e30).any()                       # IR-47-001
    assert np.isfinite(b[b <= -1e30]).all()         # ... and np.isfinite does NOT catch it


def test_every_shipped_file_exists_and_matches_its_recorded_hash(shipped):
    for rec in shipped["shipped"]:
        p = ROOT / "docs" / "downloads" / rec["filename"]
        assert p.exists(), f"{rec['filename']} is referenced by the site but missing"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == rec["sha256"], f"{rec['filename']}: hash drift"
        assert p.stat().st_size == rec["bytes"]


def test_primary_download_passes_every_check_including_the_nan_intolerant_one(shipped, tmpl):
    prim = [r for r in shipped["shipped"] if r["primary_download"]]
    assert len(prim) == 1, "exactly one file may be the primary download"
    rec = prim[0]
    p = ROOT / "docs" / "downloads" / rec["filename"]
    v = S.validate_submission(p, template=tmpl)
    assert v["all_checks_passed"] is True
    assert v["recommended_for_upload"] is True
    assert v["passes_nan_intolerant_range_check"] is True   # the reported rejection
    assert v["hard_failures"] == []
    assert v["stats"]["n_nan"] == 0
    assert v["stats"]["n_emitted"] == rec["n_dots"] == 37_654
    assert v["stats"]["n_emitted_on_catalogue"] == 0
    assert v["stats"]["n_emitted_outside_footprint"] == 0
    assert v["stats"]["v_min"] == 0.0 and v["stats"]["v_max"] == 1.0
    assert v["format"]["count"] == 1
    assert v["format"]["dtype"] == "float32"
    assert v["format"]["crs"] == "EPSG:32611"


def test_nan_variants_fail_only_the_nan_intolerant_check(shipped, tmpl):
    nans = [r for r in shipped["shipped"] if r["mode"] == "nan"]
    assert nans
    for rec in nans:
        v = S.validate_submission(ROOT / "docs" / "downloads" / rec["filename"], template=tmpl)
        assert v["passes_nan_intolerant_range_check"] is False
        assert v["passes_nan_tolerant_range_check"] is True
        assert v["recommended_for_upload"] is False
        assert v["stats"]["n_nan"] == 7_111_787
        assert v["hard_failures"] == []


def test_allfinite_and_nan_variants_of_an_arm_are_the_same_raster(shipped):
    by_arm = {}
    for r in shipped["shipped"]:
        by_arm.setdefault(r["arm"], {})[r["mode"]] = ROOT / "docs" / "downloads" / r["filename"]
    for arm, pair in by_arm.items():
        d = S.diff_report(pair["allfinite"], pair["nan"])
        assert d["identical"] is True, arm
        assert d["jaccard"] == 1.0


def test_the_primary_submission_is_distinct_from_every_prior_raster(shipped):
    prim = [r for r in shipped["shipped"] if r["primary_download"]][0]
    rows = [r for r in shipped["results"] if r["arm"].startswith("GEMSDOE47")
            and str(prim["n_dots"]) and r["n_dots"] == prim["n_dots"]]
    assert rows
    best = min(r["max_jaccard_vs_any_prior"] for r in rows)
    assert best < 0.90, f"primary arm is too close to a prior submission (Jaccard {best})"


def test_no_shipped_file_carries_values_outside_the_unit_interval(shipped):
    for rec in shipped["shipped"]:
        with rasterio.open(ROOT / "docs" / "downloads" / rec["filename"]) as s:
            v = s.read(1)
        fin = np.isfinite(v)
        assert float(v[fin].min()) >= 0.0 and float(v[fin].max()) <= 1.0
        assert not (v[fin] <= -1e30).any()
