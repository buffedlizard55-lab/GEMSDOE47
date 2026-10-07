"""Checks Markdown must not mutate the exact JSON used by the live feed."""
import base64
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publisher", ROOT / "scripts" / "publish_probe_check.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)


def test_unicode_and_backslashes_survive_api_markdown_transport(tmp_path, monkeypatch):
    body = {"page_title": "GEMS \\· GitHub — UTF-8", "floor": 0.0, "url": "https://example.org/data"}
    receipt = tmp_path / "receipt.json"; receipt.write_text(json.dumps(body))
    monkeypatch.chdir(tmp_path)
    for key, value in {"GITHUB_REPOSITORY": "owner/public", "GITHUB_SHA": "a"*40, "GITHUB_RUN_ID": "123"}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(sys, "argv", ["publisher", "--receipt", str(receipt), "--name", "Permitted public source feed"])
    monkeypatch.setattr(P.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout='{"conclusion":"neutral"}'))
    assert P.main() == 0
    payload = json.loads((tmp_path / ".cache" / "probe-check-payload.json").read_text())
    summary = payload["output"]["summary"]
    encoded = summary.split("```base64json\n", 1)[1].split("\n```", 1)[0]
    canonical = base64.b64decode(encoded, validate=True)
    assert json.loads(canonical) == body
    assert hashlib.sha256(canonical).hexdigest() in summary
    assert payload["name"] == "Permitted public source feed" and payload["conclusion"] == "neutral"
