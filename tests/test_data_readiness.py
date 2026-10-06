import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DataReadinessTests(unittest.TestCase):
    def test_missing_authorized_data_fails_closed_without_download_attempt(self):
        with tempfile.TemporaryDirectory() as empty_data:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "check_competition_data.py"),
                    "--data-dir",
                    empty_data,
                    "--labels",
                    "labels.tif",
                    "--template",
                    "template.tif",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("BLOCKED", completed.stdout)
        self.assertIn("https://www.drivendata.org/competitions/306/competition-doe-gems/data/", completed.stdout)
        self.assertIn("does not log in, download files, or bypass access controls", completed.stdout)


if __name__ == "__main__":
    unittest.main()
