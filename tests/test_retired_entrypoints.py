import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RETIRED_SCRIPTS = (
    ROOT / "src" / "make_submission.py",
    ROOT / "src" / "gems47_verify_submission.py",
    ROOT / "scripts" / "run_conformal.py",
    ROOT / "scripts" / "build_submission_s3.py",
    ROOT / "scripts" / "build_site.py",
)
PROTECTED_FILES = (
    ROOT / "notes" / "results.json",
    ROOT / "docs" / "downloads" / "gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif",
    ROOT / "docs" / "downloads" / "gems47-h51-multiscale-s2p8-20261007-allfinite.tif",
    ROOT / "docs" / "downloads" / "gems47-h51-multiscale-s2p8-20261007-nanoutside.tif",
    ROOT / "docs" / "index.html",
    ROOT / "docs" / "H49_RESULTS.md",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RetiredEntrypointTests(unittest.TestCase):
    def test_historical_entrypoints_fail_closed_without_mutation(self):
        before = {path: sha256(path) for path in PROTECTED_FILES}
        with tempfile.TemporaryDirectory() as temp_dir:
            for script in RETIRED_SCRIPTS:
                custom_output = Path(temp_dir) / f"{script.stem}-output.json"
                args = []
                if script.name == "run_conformal.py":
                    args = ["--out", str(custom_output)]
                elif script.name == "build_submission_s3.py":
                    args = ["--name", "retired-review-probe"]
                with self.subTest(script=script.name):
                    result = subprocess.run(
                        [sys.executable, str(script), *args],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("RETIRED", result.stderr)
                    self.assertFalse(custom_output.exists())
                    for path, digest in before.items():
                        self.assertEqual(sha256(path), digest, f"retired script mutated {path}")
        self.assertFalse((ROOT / "submission" / "retired-review-probe.tif").exists())
        self.assertFalse((ROOT / "docs" / "downloads" / "retired-review-probe.tif").exists())


if __name__ == "__main__":
    unittest.main()
