"""CI reopens the current H65 research-only TIFF and checks its evidence boundary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems47 import grid as G

ROOT = Path(__file__).resolve().parents[1]
H65_TIFF = "gemsdoe47-h65-paired-scarp-consensus-s2p8-20261008-research-only-nanoutside.tif"
H65_SHA256 = "10834af251114a4aa0bf6138eea497db4299ab968873a0cfaab1836062dc2992"


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_current_artifact_receipts_are_explicitly_research_only_and_no_slot():
    status = _json("docs/data/current-artifact.json")
    receipt = _json("docs/data/h65-research-tiff.json")
    screen = _json("evidence/h65/screen.json")
    comparison = _json("evidence/h65/corrected-h50-comparison.json")

    assert status["status"] == "H65_RESEARCH_ONLY_NOT_PROMOTED_DO_NOT_SUBMIT"
    assert status["artifact"] == H65_TIFF
    assert status["scientific_promotion_gate_passed"] is False
    assert status["submission_candidate"] is False
    assert status["upload_authorized_in_this_review"] is False
    assert status["slot_authorized_in_this_review"] is False
    assert status["upload_performed_in_this_review"] is False
    assert status["score_requested_in_this_review"] is False
    assert status["portal_account_or_remaining_slots_checked"] is False
    assert receipt["status"] == status["status"]
    assert receipt["promotion_gate_passed"] is False
    assert receipt["organizer_acceptance_established"] is False
    assert receipt["slot_authorized"] is False and receipt["slot_used"] is False
    assert receipt["unique_portal_name_if_future_authorized"] == \
        "GEMSDOE47-H65-paired-scarp-s2p8-20261008"
    assert receipt["proposed_short_portal_note_if_future_authorized"] == \
        "H65 paired scarp consensus d2p8"
    assert screen["promotion_gate"]["all_passed"] is False
    assert screen["promotion_gate"]["submission_authorized"] is False
    assert comparison["slot_used"] is False
    assert comparison["selection_pooled_sgmc_dti"]["h65"] == pytest.approx(0.083472, abs=1e-6)
    assert comparison["selection_pooled_sgmc_dti"]["h50"] == pytest.approx(0.135296, abs=1e-6)
    assert comparison["paired_simultaneous_lower_prediction_bound"] == pytest.approx(-0.131296, abs=1e-6)


def test_actual_h65_tiff_matches_hash_template_grid_nodata_and_unit_range():
    receipt = _json("docs/data/h65-research-tiff.json")
    path = ROOT / "docs" / "downloads" / H65_TIFF
    assert path.is_file()
    assert path.stat().st_size == 360_524
    assert hashlib.sha256(path.read_bytes()).hexdigest() == H65_SHA256
    assert receipt["sha256"] == H65_SHA256
    assert receipt["bytes"] == path.stat().st_size
    builder = ROOT / "scripts" / "build_h65_research_tiff.py"
    assert hashlib.sha256(builder.read_bytes()).hexdigest() == receipt["builder_source_sha256"]
    assert "recorded during receipt reconciliation" in receipt["builder_source_hash_scope"]

    with rasterio.open(path) as source:
        assert source.driver == "GTiff"
        assert source.count == 1 and source.dtypes == ("float32",)
        assert source.shape == G.SHAPE
        assert source.transform == G.TRANSFORM
        assert source.crs.to_string() == G.CRS
        assert tuple(source.bounds) == G.BOUNDS
        assert source.nodata is not None and np.isnan(source.nodata)
        pixels = source.read(1)
        valid = source.read_masks(1) > 0

    assert int(valid.sum()) == G.FOOTPRINT_PIXELS
    assert np.isnan(pixels[~valid]).all()
    finite = pixels[valid]
    assert np.isfinite(finite).all()
    assert np.all((finite >= 0.0) & (finite <= 1.0))
    assert set(np.unique(finite).tolist()) == {0.0, 1.0}
    assert int((finite > 0).sum()) == 37_654
    assert hashlib.sha256(np.packbits(pixels.ravel() > 0).tobytes()).hexdigest() == \
        receipt["prediction_mask_sha256"]
    assert receipt["format_validation"]["required_local_checks_passed"] is True
    assert receipt["format_validation"]["recommended_for_upload"] is False
    assert receipt["organizer_acceptance_established"] is False
    assert "unknown" in receipt["range_error_note"].lower()


def test_h65_conformal_metadata_reports_rank_target_and_unverified_exchangeability():
    current = _json("docs/data/current-artifact.json")
    result = current["scientific_result"]
    assert result["spacing_px"] == 2.8 and result["spacing_m"] == 280.0
    assert result["selection_blocks"] == 20 and result["calibration_blocks"] == 21
    assert result["conformal_nominal_coverage"] == 0.90
    assert result["conformal_rank_1_based"] == 20
    assert result["conditional_marginal_coverage_at_least_if_exchangeable"] == \
        pytest.approx(20 / 22)
    assert result["block_exchangeability_verified"] is False
    assert result["validation_blocks_previously_examined"] is True
    assert result["status"] == "exploratory_proxy_validation_not_leaderboard_score"
    assert result["sgmc_proxy_conformal_floor"] == pytest.approx(0.007885310023730621)
    assert result["h65_minus_h60_paired_simultaneous_lower_prediction_bound"] == \
        pytest.approx(-0.06212659724213554)


def test_bounded_uniqueness_audit_reports_its_failure_and_limits_without_global_claim():
    audit = _json("evidence/h65/uniqueness-audit.json")
    current = _json("docs/data/current-artifact.json")
    inventory = audit["inventory"]
    assert inventory["visible_repositories"] == 55
    assert inventory["exact_grid_blobs_attempted"] == 334
    assert inventory["verified_exact_grid_comparisons"] == 333
    assert inventory["fetch_or_verification_failures"] == 1
    assert len(audit["failures"]) == 1
    assert "404" in audit["failures"][0]["error"]
    assert audit["comparison"]["exact_positive_mask_matches"] == 0
    assert audit["local_prior_artifact_comparison"]["closest_positive_support"][
        "positive_support_jaccard"] == pytest.approx(0.18120931691632028)
    assert current["artifact_integrity"]["global_uniqueness_established"] is False
    assert current["artifact_integrity"]["broader_inventory_audit"]["bounded_only"] is True


def test_deployed_machine_readable_evidence_matches_root_evidence():
    pairs = {
        "docs/data/h65-screen.json": "evidence/h65/screen.json",
        "docs/data/h65-spacing-history.csv": "evidence/h65/spacing-history.csv",
        "docs/data/h65-corrected-h50-comparison.json": "evidence/h65/corrected-h50-comparison.json",
        "docs/data/h65-uniqueness-audit.json": "evidence/h65/uniqueness-audit.json",
        "docs/data/h60-corrected-domain-screen.json": "evidence/h60/corrected-domain/screen.json",
        "docs/data/h60-corrected-domain-spacing-history.csv": "evidence/h60/corrected-domain/spacing-history.csv",
        "docs/data/h50-frozen-blocks.json": "evidence/h50/blocks.json",
    }
    for deployed, canonical in pairs.items():
        assert (ROOT / deployed).read_bytes() == (ROOT / canonical).read_bytes(), deployed
