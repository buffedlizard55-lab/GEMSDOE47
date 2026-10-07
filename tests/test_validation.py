import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

from gemsdoe47.validation import validate_submission


class SubmissionValidationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.transform = Affine(100, 0, 1000, 0, -100, 2000)
        self.template = self.root / "template.tif"
        self.features = self.root / "features.tif"
        self.mask_path = self.root / "footprint_mask.tif"
        self.output = self.root / "prediction.tif"
        self.mask = np.ones((5, 6), dtype=np.uint8)
        self.mask[0, 0] = 0
        self.features_data = np.ones((5, 6), dtype=np.float32)
        self.features_data[0, 0] = np.nan
        template_data = np.zeros((5, 6), dtype=np.float32)
        template_data[0, 0] = np.nan
        self._write(self.template, template_data, nodata=np.nan)
        self._write(self.features, self.features_data, nodata=np.nan)
        self.mask_data = np.ones((5, 6), dtype=np.uint8)
        self.mask_data[0, 0] = 0
        self._write(self.mask_path, self.mask_data, nodata=0)
        self._write(self.output, self._valid_output(), nodata=np.nan)

    def tearDown(self):
        self.tempdir.cleanup()

    def _write(self, path, data, *, nodata):
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=data.shape[1],
            height=data.shape[0],
            count=1,
            dtype=data.dtype,
            crs="EPSG:32611",
            transform=self.transform,
            nodata=nodata,
        ) as dst:
            dst.write(data, 1)

    def _valid_output(self):
        result = np.full((5, 6), 0.5, dtype=np.float32)
        result[0, 0] = np.nan
        return result

    def test_accepts_compliant_written_float32(self):
        report = validate_submission(self.output, self.template, features_path=self.features)
        self.assertEqual(report["status"], "LOCAL_PASS")
        self.assertFalse(report["organizer_acceptance_established"])
        self.assertIn("not a portal oracle", report["validation_scope"])
        self.assertEqual(report["dtype"], "float32")
        self.assertEqual(report["valid_pixels"], 29)

    def test_accepts_explicit_binary_footprint_mask(self):
        report = validate_submission(self.output, self.template, footprint_mask_path=self.mask_path)
        self.assertEqual(report["status"], "LOCAL_PASS")
        self.assertFalse(report["organizer_acceptance_established"])
        self.assertEqual(report["outside_pixels"], 1)

    def test_accepts_the_template_internal_mask_as_the_footprint_source(self):
        report = validate_submission(self.output, self.template, template_footprint=True)
        self.assertEqual(report["status"], "LOCAL_PASS")
        self.assertIn("template_internal_mask:", report["footprint_source"])
        self.assertEqual(report["valid_pixels"], 29)
        self.assertEqual(report["outside_pixels"], 1)

    def test_requires_exactly_one_footprint_source(self):
        with self.assertRaisesRegex(ValueError, "provide exactly one"):
            validate_submission(self.output, self.template)
        with self.assertRaisesRegex(ValueError, "provide exactly one"):
            validate_submission(
                self.output,
                self.template,
                features_path=self.features,
                footprint_mask_path=self.mask_path,
            )

    def test_rejects_nan_inside_footprint(self):
        broken = self._valid_output()
        broken[2, 2] = np.nan
        self._write(self.output, broken, nodata=np.nan)
        with self.assertRaisesRegex(ValueError, "in-footprint cells are non-finite"):
            validate_submission(self.output, self.template, features_path=self.features)

    def test_rejects_out_of_range_after_write(self):
        broken = self._valid_output()
        broken[2, 2] = 1.01
        self._write(self.output, broken, nodata=np.nan)
        with self.assertRaisesRegex(ValueError, "above 1"):
            validate_submission(self.output, self.template, features_path=self.features)

    def test_rejects_numeric_outside_sentinel(self):
        broken = self._valid_output()
        broken[0, 0] = -9999.0
        self._write(self.output, broken, nodata=-9999.0)
        with self.assertRaisesRegex(ValueError, "nodata tag must be NaN"):
            validate_submission(self.output, self.template, features_path=self.features)

    def test_rejects_wrong_grid(self):
        with rasterio.open(
            self.output,
            "w",
            driver="GTiff",
            width=6,
            height=5,
            count=1,
            dtype="float32",
            crs="EPSG:32611",
            transform=Affine(100, 0, 900, 0, -100, 2000),
            nodata=np.nan,
        ) as dst:
            dst.write(self._valid_output(), 1)
        with self.assertRaisesRegex(ValueError, "grid does not exactly match"):
            validate_submission(self.output, self.template, features_path=self.features)


if __name__ == "__main__":
    unittest.main()
