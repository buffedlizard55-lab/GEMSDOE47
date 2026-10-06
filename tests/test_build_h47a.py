import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parents[1]


class BuildH47ATests(unittest.TestCase):
    def setUp(self):
        self.data_root = ROOT / "data"
        self.created_data_root = not self.data_root.exists()
        self.data_root.mkdir(exist_ok=True)
        self.tempdir = tempfile.TemporaryDirectory(dir=self.data_root)
        self.work = Path(self.tempdir.name)
        self.transform = Affine(100, 0, 500000, 0, -100, 4500000)
        self.profile = {
            "driver": "GTiff",
            "width": 64,
            "height": 64,
            "count": 1,
            "dtype": "float32",
            "crs": "EPSG:32611",
            "transform": self.transform,
            "nodata": np.nan,
        }
        self.a = self.work / "mag_a.tif"
        self.b = self.work / "mag_b.tif"
        self.template = self.work / "template.tif"
        self.output = self.work / "h47a.tif"
        edge = np.zeros((64, 64), dtype=np.float32)
        edge[:, 32:] = 5.0
        self._write(self.a, edge)
        self._write(self.b, edge)
        self._write(self.template, np.zeros((64, 64), dtype=np.float32))

    def tearDown(self):
        self.tempdir.cleanup()
        if self.created_data_root:
            self.data_root.rmdir()

    def _write(self, path, values, transform=None):
        profile = dict(self.profile)
        if transform is not None:
            profile["transform"] = transform
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(values, 1)

    def _run(self):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "build_h47a.py"),
                "--mag-a",
                str(self.a),
                "--mag-b",
                str(self.b),
                "--template",
                str(self.template),
                "--out",
                str(self.output),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_builds_a_tagged_non_submission_screening_surface(self):
        completed = self._run()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(self.output.is_file())
        self.assertTrue(self.output.with_suffix(".tif.json").is_file())
        with rasterio.open(self.output) as result:
            self.assertEqual(result.count, 1)
            self.assertEqual(result.dtypes[0], "float32")
            self.assertTrue(np.isnan(result.nodata))
            self.assertEqual(result.tags()["VALIDATION_STATUS"], "NOT_RUN")
            values = result.read(1)
            finite = values[np.isfinite(values)]
            self.assertGreater(finite.size, 0)
            self.assertGreater(float(finite.max()), 0.0)
            self.assertGreaterEqual(float(finite.min()), 0.0)
            self.assertLessEqual(float(finite.max()), 1.0)
        receipt = json.loads(self.output.with_suffix(".tif.json").read_text())
        self.assertEqual(receipt["status"], "SCREENING_SURFACE_BUILT_VALIDATION_NOT_RUN")
        self.assertEqual(receipt["validation_status"], "NOT_RUN")

    def test_refuses_silent_grid_resampling(self):
        self._write(self.b, np.zeros((64, 64), dtype=np.float32), Affine(100, 0, 500100, 0, -100, 4500000))
        completed = self._run()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("reproject/resample explicitly first", completed.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
