"""Retired builders cannot delete the new artifact or implicitly approve a slot."""
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from gems47.research_policy import reject_pages_output

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ["ship.py", "build_final.py", "build_submission.py"]


@pytest.mark.parametrize("script", SCRIPTS)
def test_retired_builder_requires_explicit_educational_opt_in_without_mutation(script):
    files = sorted((ROOT / "docs" / "downloads").glob("*.tif"))
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT,
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 2 and "RETIRED" in completed.stderr
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files} == before


def test_educational_output_must_not_overwrite_the_pages_release():
    with pytest.raises(ValueError, match="cannot overwrite"):
        reject_pages_output(ROOT / "docs" / "downloads", ROOT)
    reject_pages_output(ROOT / ".cache" / "educational", ROOT)
