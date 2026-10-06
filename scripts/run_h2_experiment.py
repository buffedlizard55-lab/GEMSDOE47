#!/usr/bin/env python3
"""Run the preregistered H47-B magnetic-edge persistence screen.

This script evaluates only against public mirrored catalogue labels. It writes
its candidate under ignored ``work/candidates/`` by default. The H47-B screen
uses a public mirror and is never slot-eligible; this script can only copy its
output to ``docs/downloads/`` with the explicitly research-only filename and
status enabled by ``--publish-research-only``.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
DATA_MANIFEST_PATH = ROOT / "registry" / "data_manifest.json"
sys.path.insert(0, str(ROOT))

from gemsdoe47.magnetic import (
    choose_spacing,
    greedy_spaced_pixels,
    guarded_grid_block_scores,
    magnetic_edge_persistence,
    pooled_block_dti,
    ranked_pixels,
    split_conformal_lower_bound,
)
from gemsdoe47.validation import sha256_file, validate_submission
from src.gems47_metric import dti

WORK = ROOT / "work"
DATA_DIR = ROOT / ".cache" / "gems_data"
PINNED_SOURCE_REF = "07345ea0604953d7efb858d9cfbc21e20c7aca0b"
EXT_PATH = DATA_DIR / "external" / "geodawn_extensions_u8.tif"
EXT_MANIFEST = DATA_DIR / "external" / "geodawn_extensions.json"
ACQ_PATH = DATA_DIR / "external" / "audit_sources" / "acquisition_block_id_100m.tif"
ACQ_RECEIPT = DATA_DIR / "external" / "audit_sources" / "acquisition_blocks_receipt.json"
LABELS_PATH = DATA_DIR / "labels.tif"
TEMPLATE_PATH = DATA_DIR / "sample_submission.tif"
OUT_DIR = WORK / "candidates"

PINNED_HASHES = {
    "features": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
    "labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "template": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "acquisition_blocks": "2c0785c4b3ec46c734d1be7a7aedbb3e816201100ab358033a3af074418c894a",
}
EXT_MANIFEST_SHA256 = "56556f24c051043fd7a85587786118f8064624f2ad0604aaa3e6614f1a9f6d2f"
ACQ_RECEIPT_SHA256 = "577076187434560514baa62995f6bb61b4d43f015b1abaf9a358936b94b5fb75"
EXPECTED_GRID = {
    "shape": (3730, 3292),
    "crs": "EPSG:32611",
    "transform": (243350.0, 100.0, 0.0, 4508550.0, 0.0, -100.0),
}
SPACINGS = (2, 3, 4, 5, 6)
BUDGET = 18524
GUARD_PX = 3
BLOCK_SHAPE = (4, 4)
SELECTION_BLOCKS = (1, 4, 7, 10, 13)
CALIBRATION_BLOCKS = (0, 3, 6, 9, 12, 15)
TEST_BLOCKS = (2, 5, 8, 11, 14)
ARTIFACT_NAME = "gems47-h47b-tmiup150-xscale-persist-n18524-research-not-submittable-20261006.tif"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _same_grid(left: rasterio.io.DatasetReader, right: rasterio.io.DatasetReader) -> bool:
    return (
        left.width == right.width
        and left.height == right.height
        and left.crs == right.crs
        and np.allclose(
            np.asarray(tuple(left.transform)[:6], dtype=np.float64),
            np.asarray(tuple(right.transform)[:6], dtype=np.float64),
            rtol=0.0,
            atol=1e-9,
        )
    )


def _load_inputs() -> dict[str, Any]:
    paths = {
        "features": EXT_PATH,
        "labels": LABELS_PATH,
        "template": TEMPLATE_PATH,
        "acquisition_blocks": ACQ_PATH,
    }
    actual_hashes: dict[str, str] = {}
    for key, path in paths.items():
        _require(path.is_file(), f"missing {key} input: {path}")
        actual_hashes[key] = sha256_file(path)
        _require(
            actual_hashes[key] == PINNED_HASHES[key],
            f"{key} SHA-256 mismatch: {actual_hashes[key]} != {PINNED_HASHES[key]}",
        )

    _require(DATA_MANIFEST_PATH.is_file(), f"missing registry data manifest: {DATA_MANIFEST_PATH}")
    registry = json.loads(DATA_MANIFEST_PATH.read_text(encoding="utf-8"))
    registry_by_id = {entry["id"]: entry for entry in registry["files"]}
    expected_registry_entries = {
        "labels": ("data/bridge/labels.tif", "labels.tif", PINNED_HASHES["labels"]),
        "sample_submission": (
            "data/bridge/sample_submission.tif", "sample_submission.tif", PINNED_HASHES["template"]
        ),
        "ext_geodawn_extensions_u8": (
            "data/external/geodawn_extensions_u8.tif",
            "external/geodawn_extensions_u8.tif",
            PINNED_HASHES["features"],
        ),
        "ext_geodawn_extensions_manifest": (
            "data/external/geodawn_extensions.json",
            "external/geodawn_extensions.json",
            EXT_MANIFEST_SHA256,
        ),
        "ext_acquisition_blocks_figure_derived": (
            "data/external/audit_sources/acquisition_block_id_100m.tif",
            "external/audit_sources/acquisition_block_id_100m.tif",
            PINNED_HASHES["acquisition_blocks"],
        ),
        "ext_acquisition_blocks_receipt": (
            "data/external/audit_sources/acquisition_blocks_receipt.json",
            "external/audit_sources/acquisition_blocks_receipt.json",
            ACQ_RECEIPT_SHA256,
        ),
    }
    for entry_id, (source_path, dest, digest) in expected_registry_entries.items():
        entry = registry_by_id.get(entry_id)
        _require(entry is not None, f"registry/data_manifest.json lacks {entry_id}")
        _require(
            entry.get("repo") == "buffedlizard55-lab/GEMSDOE24"
            and entry.get("ref") == PINNED_SOURCE_REF
            and entry.get("path") == source_path
            and entry.get("dest") == dest
            and entry.get("sha256") == digest,
            f"registry source/provenance mismatch for {entry_id}",
        )

    _require(EXT_MANIFEST.is_file(), f"missing feature manifest: {EXT_MANIFEST}")
    manifest_hash = sha256_file(EXT_MANIFEST)
    _require(manifest_hash == EXT_MANIFEST_SHA256,
             f"feature manifest SHA-256 mismatch: {manifest_hash} != {EXT_MANIFEST_SHA256}")
    manifest = json.loads(EXT_MANIFEST.read_text(encoding="utf-8"))
    _require(manifest.get("product_sha256") == PINNED_HASHES["features"],
             "feature manifest product hash does not match the pinned raster")
    _require(manifest.get("channels") == ["ThK", "UK", "UTh", "TMI_up150"],
             "unexpected GeoDAWN extensions channel order")
    _require(
        "uint8" in str(manifest.get("quantisation", "")).lower()
        and "rank" in str(manifest.get("quantisation", "")).lower(),
        "manifest does not document rank-encoded uint8 values",
    )

    _require(ACQ_RECEIPT.is_file(), f"missing acquisition-block receipt: {ACQ_RECEIPT}")
    receipt_hash = sha256_file(ACQ_RECEIPT)
    _require(receipt_hash == ACQ_RECEIPT_SHA256,
             f"acquisition-block receipt SHA-256 mismatch: {receipt_hash} != {ACQ_RECEIPT_SHA256}")
    acq_receipt = json.loads(ACQ_RECEIPT.read_text(encoding="utf-8"))
    _require(acq_receipt.get("status") == "derived_audited" and acq_receipt.get("label_free") is True,
             "acquisition-block receipt does not match the pinned label-free derivation")
    _require(acq_receipt.get("official_coordinates") is False,
             "acquisition-block boundaries are not official coordinates")
    _require(acq_receipt.get("raster", {}).get("sha256") == PINNED_HASHES["acquisition_blocks"],
             "acquisition-block receipt does not pin the expected raster")
    _require(acq_receipt.get("primary_audit_variant") == "a1_plus_a2_outside_area1",
             "unexpected acquisition-block primary audit variant")
    _require(acq_receipt.get("line_km_audit", {}).get(
        "a1_plus_a2_outside_area1", {}).get("audit", {}).get("passed") is True,
        "acquisition-block primary descriptive audit did not pass")
    actual_hashes["feature_manifest"] = manifest_hash
    actual_hashes["acquisition_blocks_receipt"] = receipt_hash

    with (
        rasterio.open(EXT_PATH) as feature_ds,
        rasterio.open(LABELS_PATH) as labels_ds,
        rasterio.open(TEMPLATE_PATH) as template_ds,
        rasterio.open(ACQ_PATH) as acquisition_ds,
    ):
        for name, dataset in (
            ("features", feature_ds),
            ("labels", labels_ds),
            ("template", template_ds),
            ("acquisition blocks", acquisition_ds),
        ):
            _require(dataset.shape == EXPECTED_GRID["shape"], f"{name}: wrong shape {dataset.shape}")
            _require(dataset.crs is not None and dataset.crs.to_string() == EXPECTED_GRID["crs"],
                     f"{name}: wrong CRS {dataset.crs}")
            _require(
                np.allclose(dataset.transform.to_gdal(), EXPECTED_GRID["transform"],
                            rtol=0.0, atol=1e-9),
                f"{name}: wrong geotransform {dataset.transform}",
            )
        _require(feature_ds.count == 4 and feature_ds.dtypes[3] == "uint8",
                 "unexpected GeoDAWN extensions profile")
        _require(labels_ds.count == 1 and labels_ds.dtypes[0] == "int8"
                 and labels_ds.nodata == -1, "unexpected mirrored label profile")
        _require(template_ds.count == 1 and template_ds.dtypes[0] == "float32"
                 and math.isnan(float(template_ds.nodata)), "unexpected sample template profile")
        _require(acquisition_ds.count == 1 and acquisition_ds.dtypes[0] == "uint8",
                 "unexpected acquisition-block profile")

        features = feature_ds.read(4)
        labels = labels_ds.read(1)
        template_raw = template_ds.read(1)
        template_mask = template_ds.read_masks(1) > 0
        acquisition_blocks = acquisition_ds.read(1)
        template_footprint = template_mask & np.isfinite(template_raw)
        label_footprint = labels != -1
        _require(np.array_equal(template_footprint, label_footprint),
                 "label and template footprints differ; refusing to infer missing cells")
        _require(np.all(np.isin(labels[label_footprint], (0, 1))),
                 "labels contain values other than -1, 0, and 1")
        _require(np.all(np.isfinite(template_raw[template_footprint])),
                 "template has non-finite values inside its data footprint")
        _require(np.all((features == 0) | template_footprint),
                 "GeoDAWN magnetic channel has data outside the template footprint")
        _require(np.all(np.isin(acquisition_blocks[template_footprint], (1, 2, 3, 4))),
                 "acquisition block raster has unexpected in-footprint IDs")

        profile = template_ds.profile.copy()
        labels_copy = labels.copy()
        footprint_copy = template_footprint.copy()
        feature_valid = (features > 0) & template_footprint
        acquisition_copy = acquisition_blocks.copy()

    return {
        "features": features,
        "feature_valid": feature_valid,
        "labels": labels_copy,
        "footprint": footprint_copy,
        "acquisition_blocks": acquisition_copy,
        "profile": profile,
        "hashes": actual_hashes,
        "manifest": manifest,
    }


def _make_map(
    ordered: np.ndarray,
    shape: tuple[int, int],
    *,
    spacing: int,
    budget: int,
    footprint: np.ndarray,
) -> np.ndarray:
    selected = greedy_spaced_pixels(
        ordered, shape, min_separation_px=float(spacing), budget=budget
    )
    prediction = np.zeros(shape, dtype=np.float32)
    prediction.ravel()[selected] = 1.0
    prediction[~footprint] = np.nan
    return prediction


def _block_map(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(row["block_id"]): row for row in rows}


def _mean_block_score(rows: list[dict[str, Any]], block_ids: tuple[int, ...]) -> float:
    by_id = _block_map(rows)
    values = [float(by_id[index]["dti"]) for index in block_ids]
    return float(np.mean(values))


def _mask_acquisition_core(
    prediction: np.ndarray,
    truth: np.ndarray,
    acquisition_ids: np.ndarray,
    block_id: int,
    guard_px: int,
) -> dict[str, Any]:
    region = acquisition_ids == block_id
    interior = ndimage.distance_transform_edt(region) > float(guard_px)
    core = region & interior
    if not core.any():
        return {"block_id": int(block_id), "dti": 0.0, "valid_pixels": 0,
                "positive_truth": 0, "note": "no area remained after guard"}
    p = np.where(core, np.nan_to_num(prediction, nan=0.0), 0.0).astype(np.float32)
    g = (truth == 1) & core
    result = dti(p, g)
    return {
        "block_id": int(block_id),
        "dti": float(result["dti"]),
        "valid_pixels": int(core.sum()),
        "positive_truth": int(result["Ng"]),
        "positive_prediction": int(result["n_pred_pos"]),
        "guard_px": int(guard_px),
    }


def _block_report_rows(
    rows_by_spacing: dict[int, list[dict[str, Any]]],
) -> dict[str, dict[str, float]]:
    summaries: dict[str, dict[str, float]] = {}
    for spacing, rows in sorted(rows_by_spacing.items()):
        summaries[str(spacing)] = {
            "mean_selection_dti": _mean_block_score(rows, SELECTION_BLOCKS),
            "mean_calibration_dti": _mean_block_score(rows, CALIBRATION_BLOCKS),
            "mean_test_dti": _mean_block_score(rows, TEST_BLOCKS),
            "pooled_selection_dti": pooled_block_dti(rows, SELECTION_BLOCKS),
            "pooled_calibration_dti": pooled_block_dti(rows, CALIBRATION_BLOCKS),
            "pooled_test_dti": pooled_block_dti(rows, TEST_BLOCKS),
        }
    return summaries


def _write_candidate(
    path: Path,
    prediction: np.ndarray,
    profile: dict[str, Any],
    template_path: Path,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    output_profile = profile.copy()
    output_profile.update(dtype="float32", count=1, nodata=float("nan"))
    with rasterio.open(path, "w", **output_profile) as dataset:
        dataset.write(prediction.astype(np.float32, copy=False), 1)
    # The mirrored labels raster uses -1 as its only nodata value, so its valid
    # mask is the same data footprint as the sample template; its 0/1 class values
    # are ignored by the validator's feature-footprint path.
    audit = validate_submission(
        path,
        template_path,
        features_path=LABELS_PATH,
    )
    return audit


def run(*, publish_research_only: bool = False) -> dict[str, Any]:
    inputs = _load_inputs()
    feature_rank = np.zeros(inputs["features"].shape, dtype=np.float32)
    feature_rank[inputs["feature_valid"]] = (
        inputs["features"][inputs["feature_valid"]].astype(np.float32) - 1.0
    ) / 254.0
    h2_score, single_scale_score, common_support, feature_diagnostics = (
        magnetic_edge_persistence(
            feature_rank,
            inputs["feature_valid"],
            scales_px=(2.0, 4.0, 8.0),
            support_threshold=0.99,
            normalization_quantile=0.99,
        )
    )
    candidate_valid = common_support & inputs["footprint"] & (h2_score > 0.0)
    baseline_valid = common_support & inputs["footprint"] & (single_scale_score > 0.0)
    _require(int(candidate_valid.sum()) >= BUDGET,
             f"H47-B has only {int(candidate_valid.sum())} valid edge cells for budget {BUDGET}")
    _require(int(baseline_valid.sum()) >= BUDGET,
             f"baseline has only {int(baseline_valid.sum())} valid edge cells for budget {BUDGET}")

    print("Ranking H47-B candidate field...")
    h2_order = ranked_pixels(h2_score, candidate_valid)
    print("Ranking single-scale comparator...")
    baseline_order = ranked_pixels(single_scale_score, baseline_valid)
    truth = inputs["labels"] == 1

    h2_rows: dict[int, list[dict[str, Any]]] = {}
    baseline_rows: dict[int, list[dict[str, Any]]] = {}
    for spacing in SPACINGS:
        print(f"Scoring spacing={spacing}px (H47-B + single-scale), guarded 4x4 blocks...")
        h2_prediction = _make_map(
            h2_order, h2_score.shape, spacing=spacing, budget=BUDGET,
            footprint=inputs["footprint"],
        )
        baseline_prediction = _make_map(
            baseline_order, single_scale_score.shape, spacing=spacing, budget=BUDGET,
            footprint=inputs["footprint"],
        )
        h2_rows[spacing] = guarded_grid_block_scores(
            h2_prediction, truth, nrows=BLOCK_SHAPE[0], ncols=BLOCK_SHAPE[1],
            guard_px=GUARD_PX,
        )
        baseline_rows[spacing] = guarded_grid_block_scores(
            baseline_prediction, truth, nrows=BLOCK_SHAPE[0], ncols=BLOCK_SHAPE[1],
            guard_px=GUARD_PX,
        )
        h2_mass = int(np.count_nonzero(h2_prediction == 1.0))
        baseline_mass = int(np.count_nonzero(baseline_prediction == 1.0))
        _require(h2_mass == BUDGET and baseline_mass == BUDGET,
                 f"mass mismatch at spacing {spacing}: H47-B={h2_mass}, baseline={baseline_mass}")

    selected_spacing, selection_mean = choose_spacing(h2_rows, SELECTION_BLOCKS)
    baseline_spacing, baseline_selection_mean = choose_spacing(baseline_rows, SELECTION_BLOCKS)
    h2_selected_rows = h2_rows[selected_spacing]
    baseline_selected_rows = baseline_rows[baseline_spacing]
    selected_by_id = _block_map(h2_selected_rows)
    calibration_scores = [selected_by_id[index]["dti"] for index in CALIBRATION_BLOCKS]
    conformal = split_conformal_lower_bound(
        [selected_by_id[index]["dti"] for index in SELECTION_BLOCKS],
        calibration_scores,
    )

    selected_prediction = _make_map(
        h2_order, h2_score.shape, spacing=selected_spacing, budget=BUDGET,
        footprint=inputs["footprint"],
    )
    baseline_prediction = _make_map(
        baseline_order, single_scale_score.shape, spacing=baseline_spacing, budget=BUDGET,
        footprint=inputs["footprint"],
    )
    random_rng = np.random.default_rng(47062026)
    random_score = random_rng.random(selected_prediction.shape, dtype=np.float32)
    random_valid = common_support & inputs["footprint"]
    random_order = ranked_pixels(random_score, random_valid)
    random_prediction = _make_map(
        random_order, random_score.shape, spacing=selected_spacing, budget=BUDGET,
        footprint=inputs["footprint"],
    )
    random_rows = guarded_grid_block_scores(
        random_prediction, truth, nrows=BLOCK_SHAPE[0], ncols=BLOCK_SHAPE[1],
        guard_px=GUARD_PX,
    )

    h2_test_pooled = pooled_block_dti(h2_selected_rows, TEST_BLOCKS)
    baseline_test_pooled = pooled_block_dti(baseline_selected_rows, TEST_BLOCKS)
    random_test_pooled = pooled_block_dti(random_rows, TEST_BLOCKS)
    floor = float(conformal["lower_bound_clipped"])
    metric_screen_passed = bool(
        h2_test_pooled > baseline_test_pooled
        and h2_test_pooled > random_test_pooled
        and floor > 0.0
    )
    metric_reasons = []
    if h2_test_pooled <= baseline_test_pooled:
        metric_reasons.append("locked-test pooled DTI did not beat the selection-picked single-scale baseline")
    if h2_test_pooled <= random_test_pooled:
        metric_reasons.append("locked-test pooled DTI did not beat the fixed-seed random control")
    if floor <= 0.0:
        metric_reasons.append("assumption-conditional conformal lower bound is not positive")
    research_only_reason = (
        "public-mirror H47-B screen is research-only and cannot confer submission-slot eligibility"
    )
    reasons = [*metric_reasons, research_only_reason]
    status = "NOT_PROMOTED"
    research_note = (
        f"H47-B selected spacing={selected_spacing}px / {selected_spacing * 100}m; "
        f"split-conformal nominal marginal coverage={conformal['nominal_coverage']:.1%} "
        f"(n={conformal['n_calibration_blocks']}, rank={conformal['rank_1_based']}, "
        "conditional on block-score exchangeability; unverified); "
        f"clipped lower bound={floor:.3f}; public-mirror research screen only."
    )
    portal_note = (
        "RESEARCH ONLY — NOT FOR SUBMISSION. Do not paste this note into the portal. "
        + research_note
    )
    if metric_reasons:
        portal_note += " Metric-screen failures: " + "; ".join(metric_reasons) + "."

    summaries = {
        "H47-B": _block_report_rows(h2_rows),
        "single_scale_baseline": _block_report_rows(baseline_rows),
    }
    selected_by_id = _block_map(h2_selected_rows)
    baseline_by_id = _block_map(baseline_selected_rows)
    random_by_id = _block_map(random_rows)
    detailed_blocks = []
    for block_id in range(BLOCK_SHAPE[0] * BLOCK_SHAPE[1]):
        detailed_blocks.append({
            "block_id": block_id,
            "row": block_id // BLOCK_SHAPE[1],
            "column": block_id % BLOCK_SHAPE[1],
            "role": (
                "selection" if block_id in SELECTION_BLOCKS else
                "calibration" if block_id in CALIBRATION_BLOCKS else "locked_test"
            ),
            "positive_truth_pixels": int(selected_by_id[block_id]["Ng"]),
            "H47B_dti": float(selected_by_id[block_id]["dti"]),
            "H47B_positive_predictions": int(selected_by_id[block_id]["n_pred_pos"]),
            "baseline_dti": float(baseline_by_id[block_id]["dti"]),
            "baseline_positive_predictions": int(baseline_by_id[block_id]["n_pred_pos"]),
            "random_dti": float(random_by_id[block_id]["dti"]),
            "random_positive_predictions": int(random_by_id[block_id]["n_pred_pos"]),
        })

    acquisition_summary = [
        _mask_acquisition_core(
            selected_prediction, inputs["labels"], inputs["acquisition_blocks"],
            acquisition_id, GUARD_PX,
        )
        for acquisition_id in (1, 2, 3, 4)
    ]
    all_domain = {
        "H47B_dti_against_mirrored_catalogue": float(dti(selected_prediction, truth)["dti"]),
        "baseline_dti_against_mirrored_catalogue": float(dti(baseline_prediction, truth)["dti"]),
        "random_dti_against_mirrored_catalogue": float(dti(random_prediction, truth)["dti"]),
        "interpretation": "descriptive full-label alignment only; not a spatial holdout or hidden-target score",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidate_path = OUT_DIR / ARTIFACT_NAME
    audit = _write_candidate(candidate_path, selected_prediction, inputs["profile"], TEMPLATE_PATH)
    candidate_sha = audit["sha256"]
    _require(int(audit["valid_pixels"]) == int(inputs["footprint"].sum()),
             "persisted output valid pixel count differs from template footprint")
    _require(int(audit["below_zero_pixels"]) == 0 and int(audit["above_one_pixels"]) == 0,
             "output range audit failed")

    report: dict[str, Any] = {
        "report_version": 1,
        "hypothesis_id": "H47-B",
        "protocol": "docs/preregistered-h2.md",
        "protocol_sha256": sha256_file(ROOT / "docs" / "preregistered-h2.md"),
        "source_data_provenance": "public group-hosted GitHub mirror; not direct organizer download",
        "pinned_source_ref": PINNED_SOURCE_REF,
        "input_sha256": inputs["hashes"],
        "feature_manifest_sha256": inputs["hashes"]["feature_manifest"],
        "acquisition_block_audit_provenance": {
            "receipt_sha256": inputs["hashes"]["acquisition_blocks_receipt"],
            "receipt_path": str(ACQ_RECEIPT.relative_to(ROOT)),
            "official_coordinates": False,
            "label_free": True,
            "use": "descriptive subgroup audit only; not used for feature construction, spacing selection, or promotion",
        },
        "grid": {
            "height": EXPECTED_GRID["shape"][0],
            "width": EXPECTED_GRID["shape"][1],
            "crs": EXPECTED_GRID["crs"],
            "transform": list(EXPECTED_GRID["transform"]),
            "resolution_m": 100,
        },
        "feature_channel": "TMI_up150; uint8 rank encoding, not physical units",
        "feature_diagnostics": feature_diagnostics,
        "block_protocol": {
            "nrows": BLOCK_SHAPE[0],
            "ncols": BLOCK_SHAPE[1],
            "guard_px": GUARD_PX,
            "guard_m": GUARD_PX * 100,
            "selection_block_ids": list(SELECTION_BLOCKS),
            "calibration_block_ids": list(CALIBRATION_BLOCKS),
            "locked_test_block_ids": list(TEST_BLOCKS),
            "split_rule": "block id (row + column) mod 3; fixed before scoring",
            "spatial_independence": "not assumed or established",
        },
        "emission": {
            "budget_per_candidate": BUDGET,
            "spacings_px": list(SPACINGS),
            "spacings_m": [int(value * 100) for value in SPACINGS],
            "candidate_rule": "descending score; ties by row-major flat index; greedy Euclidean min separation",
            "selection_rule": "highest mean DTI on five selection blocks; tie favors larger spacing",
        },
        "spacing_sweep": summaries,
        "selected_spacing_px": selected_spacing,
        "selected_spacing_m": selected_spacing * 100,
        "selection_mean_dti": selection_mean,
        "baseline_selected_spacing_px": baseline_spacing,
        "baseline_selected_spacing_m": baseline_spacing * 100,
        "baseline_selection_mean_dti": baseline_selection_mean,
        "conformal_lower_bound": conformal,
        "locked_test": {
            "H47B_pooled_dti": h2_test_pooled,
            "single_scale_baseline_pooled_dti": baseline_test_pooled,
            "random_control_pooled_dti": random_test_pooled,
            "H47B_mean_block_dti": _mean_block_score(h2_selected_rows, TEST_BLOCKS),
            "baseline_mean_block_dti": _mean_block_score(baseline_selected_rows, TEST_BLOCKS),
            "random_mean_block_dti": _mean_block_score(random_rows, TEST_BLOCKS),
            "candidate_beats_baseline": h2_test_pooled > baseline_test_pooled,
            "candidate_beats_random": h2_test_pooled > random_test_pooled,
            "block_details": detailed_blocks,
        },
        "acquisition_block_subgroup_audit": acquisition_summary,
        "full_domain_alignment": all_domain,
        "promotion": {
            "status": status,
            "slot_eligible": False,
            "metric_screen_passed": metric_screen_passed,
            "reasons_not_promoted": reasons,
            "rule": "This public-mirror research screen can never confer slot eligibility; its separate metric screen requires beating the tuned single-scale baseline and random control with a positive assumption-conditional floor.",
        },
        "artifact": {
            "path": str(candidate_path.relative_to(ROOT)),
            "sha256": candidate_sha,
            "format_audit": audit,
            "positive_pixels": int(np.count_nonzero(selected_prediction == 1.0)),
            "unique_name": ARTIFACT_NAME,
            "research_note": research_note,
            "portal_note": portal_note,
            "future_candidate_boundary": "Any future authorized-input detector must be a separately preregistered candidate with a new hypothesis ID, evidence record, and filename; this H47-B file remains research-only.",
        },
        "limitations": [
            "the mirrored catalogue labels and sample template were not independently authenticated against organizer downloads",
            "TMI_up150 is one quantized upward-continuation channel, not raw magnetic data or a physical tilt-depth solution",
            "block scores are spatially dependent; conformal level is conditional on an unverified exchangeability assumption",
            "the public label catalogue is not the private target of newly mapped faults",
            "no official leaderboard score or 0.2778 TIFF mapping is inferred from this experiment",
            "this script always marks H47-B as not slot-eligible and never publishes a non-research filename",
        ],
    }
    report_path = OUT_DIR / "gems47-h47b-screen-report-20261006.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if publish_research_only:
        published_path = ROOT / "docs" / "downloads" / ARTIFACT_NAME
        if published_path.exists():
            _require(
                sha256_file(published_path) == candidate_sha,
                "refusing to overwrite the tracked research TIFF with different bytes",
            )
        else:
            shutil.copyfile(candidate_path, published_path)
        published_audit = validate_submission(
            published_path, TEMPLATE_PATH, features_path=LABELS_PATH
        )
        _require(published_audit["sha256"] == candidate_sha,
                 "published TIFF hash differs from research candidate")
        report["research_only_publication"] = {
            "path": str(published_path.relative_to(ROOT)),
            "sha256": candidate_sha,
            "format_audit": published_audit,
            "status": "RESEARCH_ONLY_NOT_FOR_PORTAL",
            "reason": "; ".join(reasons),
        }
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"RESEARCH ONLY — NOT FOR SUBMISSION: {published_path.relative_to(ROOT)}")

    print(f"status: {status}")
    print(f"selected spacing: {selected_spacing}px ({selected_spacing * 100}m)")
    print(f"selection mean DTI: {selection_mean:.6f}")
    print(f"calibrated lower floor: {floor:.6f} at nominal {conformal['nominal_coverage']:.1%} coverage (exchangeability conditional)")
    print(f"locked-test pooled DTI H47-B / baseline / random: {h2_test_pooled:.6f} / {baseline_test_pooled:.6f} / {random_test_pooled:.6f}")
    print(f"candidate SHA-256: {candidate_sha}")
    print(f"report: {report_path.relative_to(ROOT)}")
    if reasons:
        print("not-promoted reasons:")
        for reason in reasons:
            print(f"  - {reason}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--publish-research-only",
        action="store_true",
        help="copy the candidate to docs/downloads/ only with an unmistakable research-only filename and report label",
    )
    args = parser.parse_args()
    try:
        run(publish_research_only=args.publish_research_only)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"H47-B SCREEN FAILED CLOSED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
