#!/usr/bin/env python3
"""Unit tests for legacy emission helpers and the research-artifact format only.

These tests do not establish geological performance or submission eligibility.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.gems47_emit import (
    flank_prune,
    greedy_min_separation,
    octile_dot_spacing,
    order_chain,
    redot,
    to_raster,
    trace_chains,
)
from src.gems47_metric import dti

RESEARCH_ARTIFACT = ROOT / "docs" / "downloads" / "superseded" / (
    "gems47-h47b-tmiup150-xscale-persist-n18524-"
    "research-not-submittable-20261006.tif"
)
DATA_DIR = Path(os.environ.get("GEMS_DATA_DIR", ROOT / ".cache" / "gems_data"))
LABELS = DATA_DIR / "labels.tif"
TEMPLATE = DATA_DIR / "sample_submission.tif"
RESULTS = ROOT / "notes" / "results.json"
H47B_REPORT = ROOT / "docs" / "h47b-screen-report-20261006.json"
UNIQUENESS_AUDIT = ROOT / "docs" / "h47b-uniqueness-audit-20261006.json"
EXPECTED_SHA256 = "7e5df9d01689e438e8379ebd4763ed803de02e94826f43da37c33c16380d669b"


def _mask(coords, shape=(40, 40)):
    mask = np.zeros(shape, bool)
    for row, col in coords:
        mask[row, col] = True
    return mask


class TestDTIMetric(unittest.TestCase):
    def setUp(self):
        self.truth = np.zeros((30, 30), np.uint8)
        self.truth[10, 5:25] = 1

    def test_perfect_mask_scores_one(self):
        prediction = self.truth.astype(np.float32)
        self.assertAlmostEqual(dti(prediction, self.truth)["dti"], 1.0, places=9)

    def test_two_pixel_offset_scores_one_third(self):
        prediction = np.zeros((30, 30), np.float32)
        prediction[12, 5:25] = 1.0
        self.assertAlmostEqual(dti(prediction, self.truth)["dti"], 1.0 / 3.0, places=6)

    def test_far_row_scores_below_perfect(self):
        prediction = np.zeros((30, 30), np.float32)
        prediction[20, 5:25] = 1.0
        self.assertLess(dti(prediction, self.truth)["dti"], 1.0)

    def test_empty_prediction_scores_zero(self):
        prediction = np.zeros((30, 30), np.float32)
        self.assertEqual(dti(prediction, self.truth)["dti"], 0.0)

    def test_masked_truth_and_prediction_score_zero(self):
        prediction = self.truth.astype(np.float32)
        self.assertEqual(dti(prediction, self.truth, mask=self.truth)["dti"], 0.0)

    def test_formula_identity_holds_on_synthetic_random_fields(self):
        """Check the local implementation's algebraic reduction on synthetic arrays."""
        rng = np.random.default_rng(0)
        for _ in range(5):
            prediction = (rng.random((40, 40)) < 0.05).astype(np.float32)
            truth = (rng.random((40, 40)) < 0.04).astype(np.uint8)
            result = dti(prediction, truth)
            self.assertAlmostEqual(result["dti"], result["dti_identity"], places=6)


class TestOperators(unittest.TestCase):
    def test_flank_prune_removes_only_within_threshold(self):
        dots = _mask([(5, 5), (5, 6), (20, 20)])
        distance = np.full((40, 40), 100.0)
        distance[5, 5], distance[5, 6] = 0.0, 1.0
        out = flank_prune(dots, distance, 2)
        self.assertEqual(int(out.sum()), 1)
        self.assertTrue(out[20, 20])
        self.assertFalse((out & ~dots).any(), "flank_prune must be delete-only")
        np.testing.assert_array_equal(np.nonzero(out), np.array([[20], [20]]))

    def test_min_separation_respects_spacing_and_is_delete_only(self):
        line = _mask([(10, col) for col in range(20)])
        kept = greedy_min_separation(line, 4.0)
        gaps = np.diff(np.sort(np.nonzero(kept)[1]))
        self.assertGreaterEqual(gaps.min(), 4.0)
        self.assertFalse((kept & ~line).any())
        self.assertGreaterEqual(int(kept.sum()), 3)
        self.assertLessEqual(int(kept.sum()), 6)

    def test_spacing_statistic_is_positive(self):
        self.assertGreater(octile_dot_spacing(_mask([(1, 1), (1, 2), (1, 10)])), 0)

    def test_two_dot_pair_forms_one_chain(self):
        components, (ys, xs) = trace_chains(_mask([(2, 2), (2, 4)]), 4.5)
        self.assertEqual(len(components), 1)
        self.assertEqual(len(components[0]), 2)
        self.assertEqual(len(order_chain(components[0], ys, xs)), 2)

    def test_redot_spaces_a_straight_trace(self):
        trace = _mask([(5, col) for col in range(30)])
        result = redot(trace, 5.0)
        xs = np.unique(np.nonzero(result)[1])
        gaps = np.diff(xs)
        self.assertLessEqual(gaps.max(), 5)
        self.assertGreaterEqual(gaps.min(), 4)
        self.assertLessEqual(gaps.std(), 1.0)

    def test_redot_reemits_a_sparse_subset_of_a_dense_trace(self):
        trace = _mask([(5, col) for col in range(30)])
        result = redot(trace, 3.0)
        self.assertLess(int(result.sum()), int(trace.sum()))
        self.assertFalse((result & ~trace).any())

    def test_to_raster_writes_nan_outside_the_footprint(self):
        pair = _mask([(2, 2), (2, 4)])
        self.assertTrue(set(np.unique(to_raster(pair, np.ones((40, 40), bool)))) <= {0.0, 1.0})
        self.assertTrue(np.isnan(to_raster(pair, np.zeros((40, 40), bool))).any())


class TestResearchArtifactContract(unittest.TestCase):
    """Mechanical checks on a research file; they do not authorize submission."""

    @classmethod
    def setUpClass(cls):
        if not RESEARCH_ARTIFACT.is_file():
            raise unittest.SkipTest("tracked H47-B research artifact not present")
        import rasterio
        cls.rasterio = rasterio
        with rasterio.open(RESEARCH_ARTIFACT) as dataset:
            cls.data = dataset.read(1)
            cls.shape = dataset.shape
            cls.crs = dataset.crs
            cls.dtypes = dataset.dtypes
            cls.count = dataset.count
            cls.nodata = dataset.nodata
            cls.transform = dataset.transform
        cls.sha256 = hashlib.sha256(RESEARCH_ARTIFACT.read_bytes()).hexdigest()
        cls.results = json.loads(RESULTS.read_text(encoding="utf-8"))

    def test_screen_report_never_marks_h47b_slot_eligible(self):
        report = json.loads(H47B_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["promotion"]["status"], "NOT_PROMOTED")
        self.assertFalse(report["promotion"]["slot_eligible"])
        self.assertFalse(report["promotion"]["metric_screen_passed"])
        self.assertTrue(
            any("public-mirror" in reason for reason in report["promotion"]["reasons_not_promoted"])
        )

    def test_screen_report_preserves_the_frozen_protocol_and_proxy_semantics(self):
        report = json.loads(H47B_REPORT.read_text(encoding="utf-8"))
        target = report["block_protocol"]["evaluation_target"].lower()
        clarification = report["protocol_post_score_clarification"]
        self.assertIn("labels.tif == 1", target)
        self.assertIn("known usgs/ingenious", target)
        self.assertIn("not the hidden missing-fault target", target)
        self.assertEqual(
            report["protocol_sha256"],
            "4cb65d953e575d942f0b1db8d258a36fbc2c8caea32e3409da127d36eaa0c6c6",
        )
        self.assertTrue(clarification["original_frozen_protocol_sha256_preserved"])
        self.assertEqual(
            clarification["current_document_sha256"],
            hashlib.sha256((ROOT / "docs" / "preregistered-h2.md").read_bytes()).hexdigest(),
        )

    def test_bounded_uniqueness_audit_matches_the_artifact_and_scope(self):
        audit = json.loads(UNIQUENESS_AUDIT.read_text(encoding="utf-8"))
        comparison = audit["comparison"]
        rows = audit["all_comparisons_sorted_by_equal_mass_jaccard_descending"]
        self.assertEqual(audit["candidate"]["path"], RESEARCH_ARTIFACT.relative_to(ROOT).as_posix())
        self.assertEqual(audit["candidate"]["sha256"], EXPECTED_SHA256)
        self.assertEqual(len(rows), 334)
        self.assertEqual(comparison["exact_positive_mask_matches"], 0)
        self.assertEqual(len(comparison["non_comparable_artifacts"]), 2)
        self.assertEqual(audit["inventory"]["repositories"], 55)
        self.assertEqual(audit["inventory"]["paths"], 425)
        self.assertTrue(any("not a global search" in item for item in audit["limitations"]))

    def test_filename_and_ledger_mark_it_research_only(self):
        self.assertIn("research-not-submittable", RESEARCH_ARTIFACT.name)
        self.assertEqual(self.results["record_status"], "NO_ELIGIBLE_SUBMISSION")
        record = self.results["research_artifacts"][0]
        self.assertEqual(record["status"], "RESEARCH_ONLY_NOT_FOR_PORTAL")
        self.assertEqual(record["file"], RESEARCH_ARTIFACT.relative_to(ROOT).as_posix())

    def test_band_count_dtype_and_grid(self):
        self.assertEqual(self.count, 1)
        self.assertEqual(self.dtypes[0], "float32")
        self.assertEqual(str(self.crs), "EPSG:32611")
        self.assertEqual(self.shape, (3730, 3292))

    def test_geotransform_matches_recorded_grid(self):
        self.assertEqual(
            tuple(round(float(value), 6) for value in self.transform.to_gdal()),
            (243350.0, 100.0, 0.0, 4508550.0, 0.0, -100.0),
        )

    def test_matches_sample_geometry_when_local_template_is_available(self):
        if not TEMPLATE.is_file():
            self.skipTest("mirrored sample_submission.tif not present")
        with self.rasterio.open(TEMPLATE) as sample:
            self.assertEqual(sample.shape, self.shape)
            self.assertEqual(sample.crs, self.crs)
            self.assertEqual(sample.transform, self.transform)

    def test_values_are_in_range_and_binary(self):
        finite = self.data[np.isfinite(self.data)]
        self.assertGreaterEqual(float(finite.min()), 0.0)
        self.assertLessEqual(float(finite.max()), 1.0)
        self.assertFalse(np.isinf(self.data).any())
        self.assertTrue(set(np.unique(finite)) <= {0.0, 1.0})

    def test_positive_count_and_nodata(self):
        self.assertEqual(int((self.data > 0).sum()), 18524)
        self.assertTrue(isinstance(self.nodata, float) and np.isnan(self.nodata))

    def test_sha256_matches_current_research_ledger(self):
        self.assertEqual(self.sha256, EXPECTED_SHA256)
        self.assertEqual(self.sha256, self.results["research_artifacts"][0]["sha256"])

    def test_nan_matches_mirrored_footprint_when_labels_are_available(self):
        if not LABELS.is_file():
            self.skipTest("mirrored labels.tif not present")
        with self.rasterio.open(LABELS) as labels_dataset:
            labels = labels_dataset.read(1)
        np.testing.assert_array_equal(np.isnan(self.data), labels == -1)
        self.assertFalse(np.isnan(self.data[labels >= 0]).any())


if __name__ == "__main__":
    unittest.main(verbosity=2)
