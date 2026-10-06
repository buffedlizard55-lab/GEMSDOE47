import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RETIRED_SCRIPTS = (
    ROOT / "src" / "make_submission.py",
    ROOT / "src" / "gems47_verify_submission.py",
)
RESULTS = ROOT / "notes" / "results.json"


class RetiredEntrypointTests(unittest.TestCase):
    def test_historical_builder_and_verifier_fail_closed_without_mutation(self):
        before = hashlib.sha256(RESULTS.read_bytes()).hexdigest()
        for script in RETIRED_SCRIPTS:
            with self.subTest(script=script.name):
                result = subprocess.run(
                    [sys.executable, str(script)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("RETIRED", result.stderr)
                self.assertEqual(hashlib.sha256(RESULTS.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
