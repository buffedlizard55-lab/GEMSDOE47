import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

from gemsdoe47.magnetic import (
    choose_spacing,
    greedy_spaced_pixels,
    guarded_grid_block_scores,
    magnetic_edge_persistence,
    pooled_block_dti,
    ranked_pixels,
    split_conformal_lower_bound,
)
from src.gems47_metric import dti

ROOT = Path(__file__).resolve().parents[1]


class MagneticScreenTests(unittest.TestCase):
    def test_h47b_runner_exposes_only_research_publication(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_h2_experiment.py"), "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("--publish-research-only", result.stdout)
        self.assertNotIn("--publish-if-passes", result.stdout)
        self.assertNotIn("PROMOTED_ARTIFACT_NAME", result.stdout)

    def test_persistent_step_edge_is_bounded_and_scale_supported(self):
        field = np.zeros((129, 129), dtype=np.float32)
        field[:, 64:] = 1.0
        valid = np.ones(field.shape, dtype=bool)
        score, baseline, support, diagnostics = magnetic_edge_persistence(
            field,
            valid,
            scales_px=(2.0, 4.0, 8.0),
            support_threshold=0.99,
        )
        self.assertEqual(score.shape, field.shape)
        self.assertGreater(float(score[64, 64]), 0.0)
        self.assertGreaterEqual(float(score.min()), 0.0)
        self.assertLessEqual(float(score.max()), 1.0)
        self.assertGreaterEqual(float(baseline.max()), float(score.max()))
        self.assertEqual(int(support.sum()), diagnostics["valid_support_pixels"])
        self.assertFalse(support[0, 0])

    def test_nodata_neighborhood_is_removed_from_common_support(self):
        field = np.zeros((129, 129), dtype=np.float32)
        field[:, 64:] = 1.0
        valid = np.ones(field.shape, dtype=bool)
        valid[30:40, 30:40] = False
        score, baseline, support, _ = magnetic_edge_persistence(field, valid)
        self.assertFalse(support[35, 35])
        self.assertFalse(support[35, 31])
        self.assertTrue(support[70, 70])
        self.assertEqual(float(score[35, 35]), 0.0)
        self.assertEqual(float(baseline[35, 35]), 0.0)

    def test_invalid_values_and_scale_order_fail_closed(self):
        field = np.zeros((16, 16), dtype=np.float32)
        with self.assertRaisesRegex(ValueError, r"in \[0, 1\]"):
            magnetic_edge_persistence(field + 2.0, np.ones_like(field, dtype=bool))
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            magnetic_edge_persistence(field, np.ones_like(field, dtype=bool), scales_px=(4, 2))

    def test_ranked_pixels_uses_flat_index_for_ties(self):
        score = np.asarray([[0.5, 0.8], [0.8, 0.1]], dtype=np.float32)
        valid = np.ones(score.shape, dtype=bool)
        ranked = ranked_pixels(score, valid)
        np.testing.assert_array_equal(ranked[:3], np.asarray([1, 2, 0]))

    def test_greedy_spacing_selects_exact_mass_and_respects_distance(self):
        score = np.arange(100, dtype=np.float32).reshape(10, 10)
        ranked = ranked_pixels(score, np.ones(score.shape, dtype=bool))
        selected = greedy_spaced_pixels(
            ranked, score.shape, min_separation_px=2.0, budget=8
        )
        self.assertEqual(len(selected), 8)
        points = np.asarray([divmod(int(index), score.shape[1]) for index in selected])
        for i, point in enumerate(points):
            distances = np.sqrt(np.sum((points[i + 1 :] - point) ** 2, axis=1))
            self.assertTrue(np.all(distances >= 2.0))

    def test_greedy_spacing_raises_if_budget_cannot_be_reached(self):
        with self.assertRaisesRegex(ValueError, "produced only"):
            greedy_spaced_pixels(
                np.asarray([0]), (1, 1), min_separation_px=1.0, budget=2
            )

    def test_guarded_block_scores_are_disjoint_and_pool_to_one_dti(self):
        pred = np.zeros((40, 40), dtype=np.float32)
        truth = np.zeros((40, 40), dtype=bool)
        truth[8:12, 8:12] = True
        pred[8:12, 8:12] = 1.0
        truth[28:32, 28:32] = True
        pred[28:32, 28:32] = 1.0
        rows = guarded_grid_block_scores(pred, truth, nrows=2, ncols=2, guard_px=3)
        self.assertEqual(len(rows), 4)
        pooled = pooled_block_dti(rows, (0, 1, 2, 3))
        self.assertAlmostEqual(pooled, dti(pred, truth)["dti"], places=6)
        self.assertEqual(rows[0]["Ng"], 16.0)
        self.assertEqual(rows[3]["Ng"], 16.0)

    def test_spacing_selection_and_one_sided_conformal_quantile(self):
        rows = {
            2: [
                {"block_id": 1, "dti": 0.1},
                {"block_id": 4, "dti": 0.3},
            ],
            3: [
                {"block_id": 1, "dti": 0.2},
                {"block_id": 4, "dti": 0.2},
            ],
            5: [
                {"block_id": 1, "dti": 0.2},
                {"block_id": 4, "dti": 0.2},
            ],
        }
        spacing, mean = choose_spacing(rows, (1, 4))
        self.assertEqual(spacing, 5)
        self.assertAlmostEqual(mean, 0.2)
        conformal = split_conformal_lower_bound(
            selection_scores=[0.2, 0.4],
            calibration_scores=[0.1, 0.2, 0.3],
        )
        self.assertEqual(conformal["rank_1_based"], 3)
        self.assertAlmostEqual(conformal["nominal_coverage"], 0.75)
        self.assertAlmostEqual(conformal["quantile"], 0.2)
        self.assertAlmostEqual(conformal["lower_bound_clipped"], 0.1)

    def test_conformal_rejects_empty_or_out_of_range_scores(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            split_conformal_lower_bound([], [0.1])
        with self.assertRaisesRegex(ValueError, r"in \[0, 1\]"):
            split_conformal_lower_bound([0.1], [1.1])


if __name__ == "__main__":
    unittest.main()
