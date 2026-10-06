import unittest

import numpy as np

from gemsdoe47.spatial import spatial_block_folds


class SpatialFoldTests(unittest.TestCase):
    def setUp(self):
        # One point at the center of each cell in a 5 x 5 projected-metre grid.
        self.xy = np.asarray(
            [[500.0 + 1000.0 * x, 500.0 + 1000.0 * y] for y in range(5) for x in range(5)]
        )

    def test_folds_are_deterministic_disjoint_and_buffered(self):
        folds_a = spatial_block_folds(self.xy, block_size_m=1000.0, guard_m=300.0, n_folds=5, seed=9)
        folds_b = spatial_block_folds(self.xy, block_size_m=1000.0, guard_m=300.0, n_folds=5, seed=9)
        self.assertEqual([f.heldout_blocks for f in folds_a], [f.heldout_blocks for f in folds_b])
        for fold in folds_a:
            self.assertTrue(fold.test_mask.any())
            self.assertFalse(np.any(fold.train_mask & fold.test_mask))
            self.assertEqual(fold.train_mask.shape, (len(self.xy),))
            heldout = set(fold.heldout_blocks)
            purged = set(fold.purged_blocks)
            self.assertTrue(heldout.isdisjoint(purged))
            # For this one-point-per-cell layout, every neighboring 1000 m
            # cell is within a 300 m guard of at least one held-out cell.
            self.assertTrue(purged)
            train_points = self.xy[fold.train_mask]
            test_points = self.xy[fold.test_mask]
            train_blocks = {tuple(map(int, np.floor(point / 1000.0))) for point in train_points}
            test_blocks = {tuple(map(int, np.floor(point / 1000.0))) for point in test_points}
            for train_block in train_blocks:
                for test_block in test_blocks:
                    dx = max(abs(train_block[0] - test_block[0]) - 1, 0) * 1000.0
                    dy = max(abs(train_block[1] - test_block[1]) - 1, 0) * 1000.0
                    self.assertGreater(np.hypot(dx, dy), 300.0)

    def test_every_point_is_tested_once(self):
        folds = spatial_block_folds(self.xy, block_size_m=1000.0, n_folds=5, seed=9)
        count = np.sum([f.test_mask.astype(np.int8) for f in folds], axis=0)
        np.testing.assert_array_equal(count, np.ones(len(self.xy), dtype=np.int64))

    def test_rejects_guard_that_removes_all_training_blocks(self):
        with self.assertRaisesRegex(ValueError, "no training points"):
            spatial_block_folds(self.xy, block_size_m=1000.0, guard_m=100000.0, n_folds=5)

    def test_rejects_too_few_blocks_and_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            spatial_block_folds([[0.0, 0.0]], block_size_m=1000.0, n_folds=2)
        with self.assertRaises(ValueError):
            spatial_block_folds([[0.0, float("nan")], [2.0, 1.0]], block_size_m=1000.0)


if __name__ == "__main__":
    unittest.main()
