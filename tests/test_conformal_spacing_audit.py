import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe47.magnetic import split_conformal_lower_bound
from scripts.conformal_spacing_audit import (
    CALIBRATION_BLOCKS,
    LOCKED_TEST_BLOCKS,
    SELECTION_BLOCKS,
    _analyse_arm,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evidence" / "conformal_spacing_audit_20261006.json"
UNIQUENESS = ROOT / "evidence" / "conformal_candidate_uniqueness_20261006.json"


class ConformalSpacingAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.uniqueness = json.loads(UNIQUENESS.read_text(encoding="utf-8"))

    def test_frozen_selection_calibration_test_blocks_are_disjoint_and_complete(self):
        groups = [set(SELECTION_BLOCKS), set(CALIBRATION_BLOCKS), set(LOCKED_TEST_BLOCKS)]
        self.assertEqual(set.union(*groups), set(range(16)))
        self.assertEqual(sum(map(len, groups)), 16)
        self.assertTrue(all(groups[i].isdisjoint(groups[j]) for i in range(3) for j in range(i + 1, 3)))

    def test_spacing_is_selected_on_selection_scores_not_calibration_scores(self):
        sweep = {}
        for spacing in (2, 3, 4, 5, 6):
            rows = []
            for block_id in range(16):
                if block_id in SELECTION_BLOCKS:
                    value = 0.10 if spacing == 5 else 0.05
                elif block_id in CALIBRATION_BLOCKS:
                    # Deliberately make the calibration half favor another
                    # spacing; it must not change the selection decision.
                    value = 0.20 if spacing == 2 else 0.01
                else:
                    value = 0.02
                rows.append({
                    "block_id": block_id,
                    "dti": value,
                    "TPw": value,
                    "FPw": 0.0,
                    "Ng": 1,
                    "n_pred_pos": 1,
                })
            sweep[spacing] = rows
        result = _analyse_arm("synthetic", sweep)
        self.assertEqual(result["selected_spacing_px"], 5)
        self.assertEqual(result["selection_mean_block_dti"], 0.10)

    def test_split_conformal_floor_is_zero_and_level_is_checkable(self):
        conformal = split_conformal_lower_bound(
            [0.04, 0.05, 0.06, 0.07, 0.0],
            [0.04, 0.02, 0.03, 0.07, 0.0, 0.0],
        )
        self.assertEqual(conformal["n_calibration_blocks"], 6)
        self.assertAlmostEqual(conformal["nominal_coverage"], 6 / 7)
        self.assertEqual(conformal["rank_1_based"], 6)
        self.assertEqual(conformal["lower_bound_clipped"], 0.0)

    def test_metric_and_conformal_target_are_proxy_only(self):
        evaluation_target = self.report["protocol"]["evaluation_target"].lower()
        conformal_meaning = self.report["conformal_interpretation"]["meaning_if_exchangeability_held"].lower()
        self.assertIn("labels.tif == 1", evaluation_target)
        self.assertIn("known-fault catalogue mask", evaluation_target)
        self.assertIn("not the hidden new-fault target", evaluation_target)
        self.assertIn("diagnostic proxy only", conformal_meaning)
        self.assertIn("does not cover the missing-fault target", conformal_meaning)
        provenance = self.report["protocol_provenance"]
        self.assertEqual(
            provenance["original_frozen_document_sha256"],
            "4cb65d953e575d942f0b1db8d258a36fbc2c8caea32e3409da127d36eaa0c6c6",
        )
        current_hash = hashlib.sha256((ROOT / "docs" / "preregistered-h2.md").read_bytes()).hexdigest()
        self.assertEqual(provenance["current_clarified_document_sha256"], current_hash)
        self.assertIn("target interpretation only", provenance["post_score_clarification_scope"])

    def test_generated_download_is_format_valid_and_marked_research_only(self):
        artifact = self.report["artifact"]
        self.assertEqual(artifact["status"], "RESEARCH_ONLY_NOT_PROMOTED")
        self.assertFalse(self.report["promotion"]["slot_eligible"])
        path = ROOT / artifact["path"]
        self.assertTrue(path.is_file())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(digest, artifact["sha256"])
        self.assertIn("nanoutside.tif", artifact["path"])
        with rasterio.open(path) as dataset:
            self.assertEqual(dataset.count, 1)
            self.assertEqual(dataset.dtypes[0], "float32")
            self.assertEqual(dataset.crs.to_string(), "EPSG:32611")
            self.assertTrue(np.isnan(dataset.nodata))
            values = dataset.read(1)
        finite_values = values[np.isfinite(values)]
        self.assertTrue(finite_values.size > 0)
        self.assertEqual(int(np.isnan(values).sum()), 7_111_787)
        self.assertGreaterEqual(float(finite_values.min()), 0.0)
        self.assertLessEqual(float(finite_values.max()), 1.0)
        self.assertEqual(int((values > 0).sum()), 18_524)
        format_audit = artifact["format_audit"]
        strict = format_audit["strict_submission_validation"]
        self.assertEqual(strict["status"], "PASS")
        self.assertEqual(strict["submission"], artifact["path"])
        self.assertEqual(strict["nodata"], "NaN")
        self.assertEqual(strict["invalid_inside_pixels"], 0)
        self.assertEqual(strict["non_nan_outside_pixels"], 0)
        footprint = self.report["validation_footprint_audit"]
        self.assertEqual(footprint["template_footprint_pixels"], 5_167_373)
        self.assertEqual(footprint["features_derived_footprint_pixels"], 5_165_852)
        self.assertEqual(footprint["features_only_pixels_outside_template"], 1_540)
        self.assertEqual(footprint["template_pixels_invalid_in_features"], 3_061)
        self.assertEqual(len(footprint["template_footprint_mask_sha256"]), 64)
        feature_probe = format_audit["feature_derived_validation_probe"]
        self.assertEqual(feature_probe["status"], "FAIL")
        self.assertTrue(any("1540 in-footprint" in failure for failure in feature_probe["failures"]))
        self.assertTrue(any("3061 out-of-footprint" in failure for failure in feature_probe["failures"]))
        self.assertEqual(format_audit["range_error_probe"]["passes_nan_tolerant_range_check"], True)
        self.assertEqual(format_audit["range_error_probe"]["passes_nan_intolerant_range_check"], False)
        self.assertEqual(format_audit["allfinite_diagnostic_variant"]["sha256"],
                         "c640b71c7c57066dd77bbd42fcb6c436d0a8c201de6b0ec1d88ab25976089501")
        self.assertIn("nodata tag must be NaN", format_audit["allfinite_diagnostic_variant"]["strict_validator_failure"])
        self.assertFalse(format_audit["slot_eligible"])
        self.assertIn("catalogue-mask proxy", artifact["submission_note_for_a_research_trial_only"])
        self.assertFalse(self.report["conformal_interpretation"]["positive_guarantee"])
        self.assertEqual(self.report["conformal_interpretation"]["floor"], 0.0)

    def test_candidate_has_bounded_not_global_uniqueness_evidence(self):
        inventory = self.uniqueness["inventory"]
        comparison = self.uniqueness["comparison"]
        self.assertEqual(inventory["verified_exact_grid_comparisons"], 334)
        self.assertEqual(inventory["fetch_or_verification_failures"], 0)
        self.assertEqual(comparison["exact_positive_mask_matches"], 0)
        self.assertLess(comparison["maximum_equal_mass_jaccard"], 0.02)
        local = self.uniqueness["local_prior_artifact_comparison"]
        self.assertEqual(local["artifacts_attempted"], 19)
        self.assertEqual(local["exact_grid_comparisons"], 19)
        self.assertEqual(len(local["comparisons"]), 19)
        self.assertTrue(all(row["grid_comparable"] for row in local["comparisons"]))
        self.assertTrue(all(len(row["sha256"]) == 64 for row in local["comparisons"]))
        self.assertEqual(len(local["excluded_related_variants"]), 1)
        self.assertIn("allfinite.tif", local["excluded_related_variants"][0]["path"])
        self.assertEqual(local["excluded_related_variants"][0]["positive_mask_verified"], "true")
        self.assertEqual(local["exact_positive_mask_matches"], 0)
        self.assertLess(local["maximum_equal_mass_jaccard"], 0.03)
        self.assertIn("local prior", self.uniqueness["scope_caveat"].lower())
        self.assertIn("bounded", self.uniqueness["scope_caveat"].lower())


if __name__ == "__main__":
    unittest.main()
