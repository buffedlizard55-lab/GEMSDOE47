"""H65 preregistration, negative gate and publication contracts."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _screen() -> dict:
    return json.loads((ROOT / "evidence/h65/screen.json").read_text())


def test_h65_was_preregistered_before_the_screen_code_commit() -> None:
    text = (ROOT / "docs/research/h65-h68-hypotheses-preregistered.md").read_text()
    for token in ("H65", "H66", "H67", "H68", "[1.4, 1.6, 1.8, 2.0, 2.2, 2.4]",
                  "strictly below 2.0 px", "90.91%", "sgmc_offcat"):
        assert token in text
    screen = _screen()
    assert screen["preregistration_commit"] == "b73bb647916090a1493d6679ffb0cfe92b835d04"


def test_h65_failed_closed_and_no_artifact_was_built() -> None:
    screen = _screen()
    assert screen["status"] == "FAILED_GATE_NO_BUILD"
    assert screen["gate"]["passed_prebuild"] is False
    conditions = screen["gate"]["conditions"]
    assert conditions["selected_spacing_below_2px"] is False
    assert sum(not value for value in conditions.values()) == 1
    assert screen["measured"]["selected_spacing_px"] == 2.2
    assert not list((ROOT / "docs/downloads").glob("*h65*.tif"))


def test_h65_improvements_are_reported_without_overriding_the_gate() -> None:
    screen = _screen()
    result = screen["measured"]
    h60 = screen["h60_frozen_comparator"]
    assert result["pooled_primary_selection"] > h60["pooled_primary_selection"]
    assert result["selection_mean"] > h60["selection_mean"]
    assert result["pooled_sgmc_selection"] > h60["pooled_sgmc_selection"]
    assert result["conformal"]["floor"] > 0
    assert result["conformal"]["rank_1_based"] == 20
    assert result["conformal"]["coverage_at_least"] == 20 / 22


def test_h65_history_and_deployed_receipts_are_byte_identical() -> None:
    history = ROOT / "evidence/h65/spacing-history.csv"
    deployed_history = ROOT / "docs/data/h65-spacing-history.csv"
    receipt = ROOT / "evidence/h65/screen.json"
    deployed_receipt = ROOT / "docs/data/h65-screen.json"
    assert history.read_bytes() == deployed_history.read_bytes()
    assert receipt.read_bytes() == deployed_receipt.read_bytes()
    rows = list(csv.DictReader(history.open()))
    assert len(rows) == 41 * 6 * 7  # blocks * spacings * instruments
    assert {float(row["spacing_px"]) for row in rows} == {1.4, 1.6, 1.8, 2.0, 2.2, 2.4}
    assert {row["role"] for row in rows} == {"selection", "calibration"}
    assert hashlib.sha256(history.read_bytes()).hexdigest() == _screen()["spacing_history_sha256"]


def test_h65_site_says_no_tiff_and_keeps_h60_primary() -> None:
    page = (ROOT / "docs/h65.html").read_text()
    assert "NO TIFF BUILT" in page
    assert "DO NOT SUBMIT" in page
    assert "H60 remains the approved primary" in page
    assert "90.91%" in page
