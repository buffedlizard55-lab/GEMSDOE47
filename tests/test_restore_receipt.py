"""Restore must never certify missing/skipped bytes or accept directory escape."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("restore", ROOT / "scripts" / "restore_data.py")
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)


def entry(dest="core.tif", content=b"expected"):
    return {"id": "test", "dest": dest, "group": "core", "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(), "repo": "public/test", "ref": "pinned", "path": "core.tif"}


def test_skip_large_is_not_a_verification_receipt(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    e = entry(); e["bytes"] = 20_000_001
    manifest.write_text(json.dumps({"files": [e]}))
    monkeypatch.setattr(R, "MANIFEST", manifest); monkeypatch.setattr(R, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["restore", "--skip-large", "--target-dir", str(tmp_path / "inputs")])
    def forbidden(*args):
        pytest.fail("skip-large may not initiate a download")
    monkeypatch.setattr(R, "gh_raw", forbidden)
    assert R.main() == 0  # smoke-test success is not data verification
    receipt = json.loads((tmp_path / "data" / "restore_receipt.json").read_text())
    assert not receipt["all_verified"] and receipt["skipped_file_count"] == 1
    assert receipt["verified_file_count"] == 0


def test_download_hash_failure_preserves_existing_file(tmp_path, monkeypatch):
    path = tmp_path / "core.tif"; path.write_bytes(b"old")
    def fake(repo, ref, source, target):
        target.write_bytes(b"corrupt")
    monkeypatch.setattr(R, "gh_raw", fake)
    with pytest.raises(ValueError, match="MISMATCH"):
        R.restore_entry(entry(), tmp_path, False)
    assert path.read_bytes() == b"old"
    assert not path.with_suffix(".tif.assembling").exists()


@pytest.mark.parametrize("dest", ["../escape.tif", "."])
def test_manifest_cannot_escape_or_replace_the_data_directory(tmp_path, dest):
    with pytest.raises(ValueError, match="escapes"):
        R.restore_entry(entry(dest), tmp_path, False)


def test_unknown_ids_fail_instead_of_verifying_an_empty_request(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"; manifest.write_text(json.dumps({"files": [entry()]}))
    monkeypatch.setattr(R, "MANIFEST", manifest)
    monkeypatch.setattr(sys, "argv", ["restore", "--only", "does-not-exist", "--target-dir", str(tmp_path / "inputs")])
    with pytest.raises(SystemExit) as error:
        R.main()
    assert error.value.code == 2
