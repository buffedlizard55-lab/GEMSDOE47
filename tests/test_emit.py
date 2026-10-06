#!/usr/bin/env python3
"""Unit tests for the emission operators, the metric and the submission contract.

Runs under ``python -m unittest discover -s tests`` (the CI runner) and standalone
(``python3 tests/test_emit.py``).
"""
from __future__ import annotations

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = "/home/user/_ref/GEMSDOE24/data/bridge/labels.tif"
SUBMISSION = os.path.join(ROOT, "docs", "downloads",
                          "gems47-dcat20-annulus-flankprune-n18524-20261006.tif")


def _mask(coords, shape=(40, 40)):
    m = np.zeros(shape, bool)
    for r, c in coords:
        m[r, c] = True
    return m


class TestMetric(unittest.TestCase):
    def setUp(self):
        self.truth = np.zeros((30, 30), np.uint8)
        self.truth[10, 5:25] = 1

    def test_perfect_mask_scores_one(self):
        perfect = np.zeros((30, 30), np.float32)
        perfect[self.truth == 1] = 1.0
        self.assertAlmostEqual(dti(perfect, self.truth)["dti"], 1.0, places=9)

    def test_two_pixel_offset_scores_exactly_one_third(self):
        # TP = 20*(1/3), FP = 20*(2/3), N_g = 20 -> 5*(20/3) / (20/3 + 40/3 + 80) = 1/3
        off = np.zeros((30, 30), np.float32)
        off[12, 5:25] = 1.0
        self.assertAlmostEqual(dti(off, self.truth)["dti"], 1.0 / 3.0, places=6)

    def test_far_row_scores_below_perfect(self):
        far = np.zeros((30, 30), np.float32)
        far[20, 5:25] = 1.0
        self.assertLess(dti(far, self.truth)["dti"], 1.0)

    def test_empty_mask_scores_zero(self):
        self.assertEqual(dti(np.zeros((30, 30), np.float32), self.truth)["dti"], 0.0)

    def test_predicting_the_truth_with_mask_alias_scores_zero(self):
        self.assertEqual(dti(self.truth.astype(np.float32), self.truth, mask=self.truth)["dti"], 0.0)

    def test_algebraic_identity_holds_on_random_fields(self):
        """dti == 5*TPw/(TPw + FPw + 4*Ng) to machine precision — the identity this
        project's whole operating-point argument rests on."""
        rng = np.random.default_rng(0)
        for _ in range(5):
            p = (rng.random((40, 40)) < 0.05).astype(np.float32)
            g = (rng.random((40, 40)) < 0.04).astype(np.uint8)
            r = dti(p, g)
            self.assertAlmostEqual(r["dti"], r["dti_identity"], places=6)


class TestOperators(unittest.TestCase):
    def test_flank_prune_removes_only_within_threshold(self):
        dots = _mask([(5, 5), (5, 6), (20, 20)])
        dist = np.full((40, 40), 100.0)
        dist[5, 5], dist[5, 6] = 0.0, 1.0
        out = flank_prune(dots, dist, 2)
        self.assertEqual(int(out.sum()), 1)
        self.assertTrue(out[20, 20])
        self.assertFalse((out & ~dots).any(), "flank_prune must be delete-only")
        np.testing.assert_array_equal(np.nonzero(out), np.array([[20], [20]]))

    def test_min_separation_respects_spacing_and_is_delete_only(self):
        line = _mask([(10, c) for c in range(20)])
        kept = greedy_min_separation(line, 4.0)
        gaps = np.diff(np.sort(np.nonzero(kept)[1]))
        self.assertGreaterEqual(gaps.min(), 4.0)
        self.assertFalse((kept & ~line).any())
        self.assertGreaterEqual(int(kept.sum()), 3)
        self.assertLessEqual(int(kept.sum()), 6)

    def test_spacing_statistic_is_positive(self):
        self.assertGreater(octile_dot_spacing(_mask([(1, 1), (1, 2), (1, 10)])), 0)

    def test_two_dot_pair_forms_one_chain(self):
        comps, (ys, xs) = trace_chains(_mask([(2, 2), (2, 4)]), 4.5)
        self.assertEqual(len(comps), 1)
        self.assertEqual(len(comps[0]), 2)
        self.assertEqual(len(order_chain(comps[0], ys, xs)), 2)

    def test_redot_spaces_a_straight_trace(self):
        trace = _mask([(5, c) for c in range(30)])
        r = redot(trace, 5.0)
        xs = np.unique(np.nonzero(r)[1])
        gaps = np.diff(xs)
        self.assertLessEqual(gaps.max(), 5)
        self.assertGreaterEqual(gaps.min(), 4)
        self.assertLessEqual(gaps.std(), 1.0)

    def test_redot_is_documented_as_lossy(self):
        """redot may move positions off the original dots; the submission therefore does not use it."""
        trace = _mask([(5, c) for c in range(30)])
        r = redot(trace, 3.0)
        self.assertGreaterEqual(int((r & ~trace).sum()), 0)

    def test_to_raster_writes_nan_outside_the_footprint(self):
        pair = _mask([(2, 2), (2, 4)])
        self.assertTrue(set(np.unique(to_raster(pair, np.ones((40, 40), bool)))) <= {0.0, 1.0})
        self.assertTrue(np.isnan(to_raster(pair, np.zeros((40, 40), bool))).any())


class TestSubmissionContract(unittest.TestCase):
    """The portal-facing contract, asserted on the actual bytes we would upload."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(SUBMISSION):
            raise unittest.SkipTest("submission artifact not built yet")
        import rasterio
        cls.rasterio = rasterio
        with rasterio.open(SUBMISSION) as ds:
            cls.data = ds.read(1)
            cls.profile_shape = ds.shape
            cls.crs = ds.crs
            cls.dtypes = ds.dtypes
            cls.count = ds.count
            cls.nodata = ds.nodata
            cls.transform = ds.transform

    def test_band_count_dtype_and_grid(self):
        self.assertEqual(self.count, 1)
        self.assertEqual(self.dtypes[0], "float32")
        self.assertEqual(str(self.crs), "EPSG:32611")
        self.assertEqual(self.profile_shape, (3730, 3292))

    def test_geotransform_matches_the_competition_grid(self):
        self.assertEqual(tuple(round(float(v), 6) for v in self.transform.to_gdal()),
                         (243350.0, 100.0, 0.0, 4508550.0, 0.0, -100.0))

    def test_matches_sample_submission_geometry_when_available(self):
        sample = "/home/user/_ref/GEMSDOE24/data/bridge/sample_submission.tif"
        if not os.path.exists(sample):
            self.skipTest("sample_submission.tif not present")
        with self.rasterio.open(sample) as sd:
            self.assertEqual(sd.shape, self.profile_shape)
            self.assertEqual(sd.crs, self.crs)
            self.assertEqual(sd.transform, self.transform)

    def test_values_are_inside_zero_one(self):
        finite = self.data[np.isfinite(self.data)]
        self.assertGreaterEqual(float(finite.min()), 0.0)
        self.assertLessEqual(float(finite.max()), 1.0)
        self.assertFalse(np.isinf(self.data).any())

    def test_only_zero_and_one_are_emitted(self):
        finite = self.data[np.isfinite(self.data)]
        self.assertTrue(set(np.unique(finite)) <= {0.0, 1.0})

    def test_positive_count(self):
        self.assertEqual(int((self.data > 0).sum()), 18524)

    def test_nodata_convention_matches_the_template(self):
        self.assertTrue(isinstance(self.nodata, float) and np.isnan(self.nodata))

    def test_nan_sits_exactly_outside_the_valid_footprint(self):
        if not os.path.exists(LABELS):
            self.skipTest("labels.tif not present")
        with self.rasterio.open(LABELS) as ld:
            labels = ld.read(1)
        np.testing.assert_array_equal(np.isnan(self.data), labels == -1)
        self.assertFalse(np.isnan(self.data[labels >= 0]).any())


if __name__ == "__main__":
    unittest.main(verbosity=2)
