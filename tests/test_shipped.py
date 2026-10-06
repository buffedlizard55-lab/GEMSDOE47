"""Re-check retained research GeoTIFFs and their closed submission gate.

Marked ``needs_data``: uses the restored competition template/labels and the
research TIFFs retained on the project site. The historical artifact records are
not current submission authorization.
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
        pytest.skip("evidence/shipped.json not built; run the research builder")
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
    assert not (ones & ~tmpl.catalogue).any()  # The sample contains known faults, not an all-zero raster.


def test_training_nodata_is_float32_min_not_nan():
    path = G.data_dir() / "training_features.tif"
    if not path.exists():
        pytest.skip("training feature raster not restored")
    with rasterio.open(path) as s:
        assert s.count == 19
        band = s.read(1)
    assert (band <= -1e30).any()
    assert np.isfinite(band[band <= -1e30]).all()


def test_every_retained_research_file_matches_its_recorded_hash(shipped):
    for rec in shipped["shipped"]:
        path = ROOT / "docs" / "downloads" / rec["filename"]
        assert path.exists(), f"{rec['filename']} is referenced by the research record but missing"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == rec["sha256"]
        assert path.stat().st_size == rec["bytes"]
        assert rec["submission_authorized"] is False
        assert rec["slot_eligible"] is False
        assert rec["primary_download"] is False


def test_status_overlay_keeps_gate_closed_and_observation_scope_qualified(shipped):
    status = shipped["status_audit_2026_10_06"]
    assert status["current_decision"] == "RESEARCH_ONLY_NOT_FOR_PORTAL"
    assert status["submission_slot_authorized"] is False
    assert status["h33_score_file_mapping_verified"] is False
    assert status["owner_reported_score_raster_pairs"] == 12
    assert shipped["observation_scope"]["model_rows"] == 13
    assert shipped["observation_scope"]["owner_reported_pairs"] == 12
    assert all("RESEARCH ONLY" in role for role in shipped["arm_roles"].values())
    assert shipped["historical_fields_audit_2026_10_06"]["status"] == "SUPERSEDED_NOT_CURRENT"
    cost_audit = shipped["submission_cost_audit"]
    assert cost_audit["lambda_probe_design_score_observations"] == 3
    assert cost_audit["lambda_1_anchor_score_file_mapping_verified"] is False
    assert cost_audit["probe_authorized"] is False
    assert "unverified" in cost_audit["current_per_user_quota_or_slot_accounting"].lower()


def test_saved_validations_are_reconciled_with_outside_nodata_requirement(shipped):
    review = shipped["format_review_2026_10_06"]
    assert review["published_outside_bounds_requirement"] == "null or NaN"
    assert review["organizer_acceptance_established"] is False
    assert review["upload_recommendation"] == "none"
    for record in shipped["shipped"]:
        validation = record["validation"]
        is_nan = record["mode"] == "nan"
        assert validation["checks"]["outside_template_footprint_is_nodata"] is is_nan
        assert validation["checks"]["no_infinite_values"] is True
        assert validation["checks"]["masked_pixels_only_outside_footprint"] is True
        assert validation["stats"]["n_infinite"] == 0
        assert validation["required_local_checks_passed"] is is_nan
        assert validation["all_checks_passed"] is is_nan
        expected_diagnostics = (
            {
                "RANGE_nan_intolerant: np.all((v>=0)&(v<=1))",
                "all_pixels_finite",
            }
            if is_nan else set()
        )
        assert set(validation["diagnostic_failures"]) == expected_diagnostics
        assert validation["recommended_for_upload"] is False
        assert record["validation_at_generation_legacy"]["recommended_for_upload_now"] is False


def test_allfinite_variant_passes_raw_range_but_fails_outside_nodata_requirement(shipped, tmpl):
    variants = [r for r in shipped["shipped"] if r["mode"] == "allfinite"]
    assert variants
    for rec in variants:
        validation = S.validate_submission(ROOT / "docs" / "downloads" / rec["filename"], template=tmpl)
        assert validation["all_checks_passed"] is False
        assert validation["passes_nan_intolerant_range_check"] is True
        assert validation["checks"]["outside_template_footprint_is_nodata"] is False
        assert validation["hard_failures"] == ["outside_template_footprint_is_nodata"]
        assert validation["stats"]["n_nan"] == 0
        assert validation["stats"]["n_emitted"] == rec["n_dots"] == 37_654
        assert validation["stats"]["n_emitted_on_catalogue"] == 0
        assert validation["stats"]["n_emitted_outside_footprint"] == 0
        assert validation["stats"]["v_min"] == 0.0 and validation["stats"]["v_max"] == 1.0
        assert validation["format"]["count"] == 1
        assert validation["format"]["dtype"] == "float32"
        assert validation["format"]["crs"] == "EPSG:32611"
        # The validator only reports format suitability; the project's separate gate stays closed.
        assert rec["submission_authorized"] is False
        assert rec["slot_eligible"] is False


def test_nan_variants_fail_only_the_nan_intolerant_check(shipped, tmpl):
    nans = [r for r in shipped["shipped"] if r["mode"] == "nan"]
    assert nans
    for rec in nans:
        validation = S.validate_submission(
            ROOT / "docs" / "downloads" / rec["filename"], template=tmpl
        )
        assert validation["passes_nan_intolerant_range_check"] is False
        assert validation["passes_nan_tolerant_range_check"] is True
        assert validation["recommended_for_upload"] is False
        assert validation["checks"]["outside_template_footprint_is_nodata"] is True
        assert validation["all_checks_passed"] is True
        assert validation["stats"]["n_nan"] == 7_111_787
        assert validation["hard_failures"] == []


def test_allfinite_and_nan_variants_of_an_arm_are_the_same_raster(shipped):
    by_arm = {}
    for record in shipped["shipped"]:
        by_arm.setdefault(record["arm"], {})[record["mode"]] = (
            ROOT / "docs" / "downloads" / record["filename"]
        )
    for arm, pair in by_arm.items():
        assert set(pair) == {"allfinite", "nan"}
        diff = S.diff_report(pair["allfinite"], pair["nan"])
        assert diff["identical"] is True, arm
        assert diff["jaccard"] == 1.0
        with rasterio.open(pair["allfinite"]) as s0, rasterio.open(pair["nan"]) as s1:
            zeros_outside = s0.read(1)
            nodata_variant = s1.read(1)
        outside = ~np.isfinite(nodata_variant)
        assert outside.any()
        assert np.isfinite(zeros_outside).all()
        assert np.all(zeros_outside[outside] == 0.0)
        assert np.array_equal(zeros_outside[~outside], nodata_variant[~outside])


def test_no_retained_research_file_carries_values_outside_the_unit_interval(shipped):
    for record in shipped["shipped"]:
        with rasterio.open(ROOT / "docs" / "downloads" / record["filename"]) as dataset:
            values = dataset.read(1)
        finite = np.isfinite(values)
        assert float(values[finite].min()) >= 0.0
        assert float(values[finite].max()) <= 1.0
        assert not (values[finite] <= -1e30).any()
