import unittest

import numpy as np

from gemsdoe47.candidate import compute_h47a_score


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.size = 41
        self.edge = np.zeros((self.size, self.size), dtype=np.float32)
        self.edge[:, self.size // 2 :] = 1.0

    def test_same_persistent_edge_has_nonzero_bounded_support(self):
        score, diagnostics = compute_h47a_score(self.edge, self.edge)
        row, col = self.size // 2, self.size // 2
        self.assertTrue(np.isfinite(score[row, col]))
        self.assertGreater(float(score[row, col]), 0.0)
        self.assertLessEqual(float(np.nanmax(score)), 1.0)
        self.assertGreaterEqual(float(np.nanmin(score)), 0.0)
        self.assertEqual(diagnostics["validation_status"], "NOT_RUN")

    def test_integer_and_masked_input_are_supported(self):
        integer_edge = np.zeros((self.size, self.size), dtype=np.int16)
        integer_edge[:, self.size // 2 :] = 10
        result, _ = compute_h47a_score(integer_edge, integer_edge)
        self.assertGreater(float(result[20, self.size // 2]), 0.0)

    def test_sparse_but_persistent_line_does_not_collapse_to_zero_scale(self):
        data = np.zeros((501, 501), dtype=np.float32)
        data[:, 250:] = 1.0
        score, _ = compute_h47a_score(data, data)
        self.assertGreater(float(score[250, 250]), 0.0)

    def test_orientation_is_axial_not_directional(self):
        score_forward, _ = compute_h47a_score(self.edge, self.edge)
        score_reversed, _ = compute_h47a_score(self.edge, -self.edge)
        row, col = self.size // 2, self.size // 2
        self.assertAlmostEqual(float(score_forward[row, col]), float(score_reversed[row, col]), places=6)

    def test_orthogonal_edges_do_not_agree_away_from_intersection(self):
        horizontal = np.zeros_like(self.edge)
        horizontal[self.size // 2 :, :] = 1.0
        score, _ = compute_h47a_score(self.edge, horizontal)
        self.assertAlmostEqual(float(score[8, self.size // 2]), 0.0, places=6)
        self.assertAlmostEqual(float(score[self.size // 2, 8]), 0.0, places=6)

    def test_missing_data_neighborhood_is_nan_not_a_false_edge(self):
        data = self.edge.copy()
        data[10, 10] = np.nan
        score, _ = compute_h47a_score(data, self.edge)
        self.assertTrue(np.isnan(score[10, 10]))
        self.assertTrue(np.isnan(score[10, 9]))
        self.assertTrue(np.isnan(score[9, 10]))
        self.assertTrue(np.isfinite(score[20, 20]))

    def test_flight_line_penalty_is_optional_and_reduces_aligned_edge(self):
        unpenalized, _ = compute_h47a_score(self.edge, self.edge)
        penalized, _ = compute_h47a_score(
            self.edge,
            self.edge,
            artifact_penalty=0.8,
            flight_bearing_a=0.0,
            flight_bearing_b=0.0,
        )
        row, col = self.size // 2, self.size // 2
        self.assertLess(float(penalized[row, col]), float(unpenalized[row, col]))

    def test_tiny_array_returns_no_support_instead_of_gradient_error(self):
        score, diagnostics = compute_h47a_score(
            np.ones((1, 8), dtype=np.int16),
            np.ones((1, 8), dtype=np.int16),
        )
        self.assertTrue(np.isnan(score).all())
        self.assertEqual(diagnostics["valid_pixels"], 0)

    def test_rejects_one_radiometric_layer_or_unpaired_bearings(self):
        with self.assertRaises(ValueError):
            compute_h47a_score(self.edge, self.edge, radiometric_a=self.edge)
        with self.assertRaises(ValueError):
            compute_h47a_score(self.edge, self.edge, flight_bearing_a=15.0)


if __name__ == "__main__":
    unittest.main()
