import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

from scripts.build_footprint_mask import build_footprint_mask


class FootprintMaskTests(unittest.TestCase):
    def test_builds_binary_mask_from_finite_unmasked_template_cells(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            template = root / "sample.tif"
            output = root / "footprint.tif"
            values = np.array(
                [[0.0, 1.0, np.nan], [-9999.0, 0.5, 0.0]],
                dtype=np.float32,
            )
            with rasterio.open(
                template,
                "w",
                driver="GTiff",
                width=3,
                height=2,
                count=1,
                dtype="float32",
                crs="EPSG:32611",
                transform=Affine(100, 0, 1000, 0, -100, 2000),
                nodata=-9999.0,
            ) as dataset:
                dataset.write(values, 1)

            report = build_footprint_mask(template, output)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["valid_pixels"], 4)
            self.assertEqual(report["outside_pixels"], 2)
            with rasterio.open(output) as dataset:
                np.testing.assert_array_equal(
                    dataset.read(1),
                    np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8),
                )
                self.assertEqual(dataset.nodata, 0)
                self.assertEqual(dataset.crs.to_string(), "EPSG:32611")

    def test_never_overwrites_the_template(self):
        with tempfile.TemporaryDirectory() as temporary:
            template = Path(temporary) / "sample.tif"
            with rasterio.open(
                template,
                "w",
                driver="GTiff",
                width=1,
                height=1,
                count=1,
                dtype="float32",
                crs="EPSG:32611",
                transform=Affine(100, 0, 1000, 0, -100, 2000),
                nodata=np.nan,
            ) as dataset:
                dataset.write(np.array([[0]], dtype=np.float32), 1)
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                build_footprint_mask(template, template)


if __name__ == "__main__":
    unittest.main()
