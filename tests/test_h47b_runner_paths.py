"""The H47-B runner and restore utility must resolve the same pinned mirror layout.

These tests inspect only path/configuration metadata; they do not restore data or run H47-B.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "h47b_runner_paths_under_test", ROOT / "scripts" / "run_h2_experiment.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_paths_match_restore_manifest_without_loading_data(monkeypatch):
    monkeypatch.delenv("GEMS_DATA_DIR", raising=False)
    runner = _load_runner()
    expected_root = ROOT / ".cache" / "gems_data"

    assert runner.DATA_DIR == expected_root
    assert runner.LABELS_PATH == expected_root / "labels.tif"
    assert runner.TEMPLATE_PATH == expected_root / "sample_submission.tif"
    assert runner.EXT_PATH == expected_root / "external" / "geodawn_extensions_u8.tif"
    assert runner.EXT_MANIFEST == expected_root / "external" / "geodawn_extensions.json"
    assert runner.ACQ_PATH == (
        expected_root / "external" / "audit_sources" / "acquisition_block_id_100m.tif"
    )
    assert runner.ACQ_RECEIPT == (
        expected_root / "external" / "audit_sources" / "acquisition_blocks_receipt.json"
    )

    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in manifest["files"]}
    expected = {
        "labels": ("labels.tif", runner.PINNED_HASHES["labels"]),
        "sample_submission": ("sample_submission.tif", runner.PINNED_HASHES["template"]),
        "ext_geodawn_extensions_u8": (
            "external/geodawn_extensions_u8.tif",
            runner.PINNED_HASHES["features"],
        ),
        "ext_geodawn_extensions_manifest": (
            "external/geodawn_extensions.json",
            runner.EXT_MANIFEST_SHA256,
        ),
        "ext_acquisition_blocks_figure_derived": (
            "external/audit_sources/acquisition_block_id_100m.tif",
            runner.PINNED_HASHES["acquisition_blocks"],
        ),
        "ext_acquisition_blocks_receipt": (
            "external/audit_sources/acquisition_blocks_receipt.json",
            runner.ACQ_RECEIPT_SHA256,
        ),
    }
    for entry_id, (dest, digest) in expected.items():
        entry = by_id[entry_id]
        assert entry["repo"] == "buffedlizard55-lab/GEMSDOE24"
        assert entry["ref"] == runner.PINNED_SOURCE_REF
        assert entry["dest"] == dest
        assert entry["sha256"] == digest
