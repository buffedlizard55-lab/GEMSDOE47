#!/usr/bin/env python3
"""Package a new H47-A prediction only after a machine-checked promotion gate.

This script is intentionally fail-closed. It is not a holdout scorer and does
not certify the truthfulness of the human-reviewed promotion report. It checks
the report fields, exact input hashes, the per-fold evidence, and the written
GeoTIFF contract before creating an ignored local artifact and receipt.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gemsdoe47.validation import sha256_file, validate_submission


def _promotion_gate(report: dict, prediction: Path, template: Path, features: Path) -> dict:
    required_true = (
        "official_inputs_authorized",
        "preregistered_before_scoring",
        "spatially_blocked",
        "matched_mass",
        "controls_reported",
    )
    if type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        raise ValueError("promotion report schema_version must be integer 1")
    if report.get("hypothesis_id") != "H47-A":
        raise ValueError("only a reviewed H47-A promotion report is accepted by this packager")
    if report.get("status") != "promoted":
        raise ValueError("promotion report status must be 'promoted'")
    if report.get("score_metric") != "official_dw_tversky":
        raise ValueError("promotion report must identify the official_dw_tversky metric")
    if not isinstance(report.get("report_id"), str) or not report["report_id"].strip():
        raise ValueError("promotion report needs a non-empty string report_id")
    for key in required_true:
        if report.get(key) is not True:
            raise ValueError(f"promotion gate is not satisfied: {key} must be true")
    evidence = report.get("evidence")
    if not isinstance(evidence, dict):
        raise TypeError("promotion report must include a structured evidence object")
    for key in ("domain_matched_random_control_reported", "ablations_reported"):
        if evidence.get(key) is not True:
            raise ValueError(f"promotion evidence is incomplete: {key} must be true")
    scorer_version = evidence.get("official_scorer_version")
    if not isinstance(scorer_version, str) or not scorer_version.strip():
        raise ValueError("promotion evidence must pin the official scorer version")
    for key in ("preregistration_sha256", "fold_assignment_sha256"):
        value = evidence.get(key)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise ValueError(f"promotion evidence {key} must be a SHA-256 digest")
    source_hashes = evidence.get("source_data_sha256")
    if not isinstance(source_hashes, dict) or not source_hashes:
        raise ValueError("promotion evidence must list source-data SHA-256 hashes")
    if not all(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
        for value in source_hashes.values()
    ):
        raise ValueError("every source-data hash must be a lowercase SHA-256 digest")
    code_revision = evidence.get("model_code_revision")
    if not isinstance(code_revision, str) or not re.fullmatch(r"[0-9a-f]{40}", code_revision):
        raise ValueError("promotion evidence model_code_revision must be a full git commit SHA")
    guard = report.get("guard_m")
    if not isinstance(guard, (int, float)) or not math.isfinite(guard) or guard < 300.0:
        raise ValueError("promotion report needs a spatial guard of at least 300 m")

    hashes = {
        "prediction_sha256": prediction,
        "template_sha256": template,
        "features_sha256": features,
    }
    for field, path in hashes.items():
        if report.get(field) != sha256_file(path):
            raise ValueError(f"promotion report {field} does not match current file bytes")

    try:
        raw_pooled = (report["pooled_incumbent_dti"], report["pooled_candidate_dti"])
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in raw_pooled):
            raise TypeError("pooled DTI values must be numeric, not booleans/strings")
        pooled_incumbent, pooled_candidate = map(float, raw_pooled)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("promotion report must include pooled incumbent/candidate DTI") from error
    if not all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in (pooled_incumbent, pooled_candidate)):
        raise ValueError("pooled DTI values must be finite and in [0, 1]")
    if pooled_candidate <= pooled_incumbent:
        raise ValueError("candidate pooled holdout score does not beat the incumbent")

    folds = report.get("folds")
    if not isinstance(folds, list) or len(folds) < 3:
        raise ValueError("at least three spatial holdout folds are required")
    block_ids: set[str] = set()
    candidate_wins = 0
    incumbent_scores: list[float] = []
    candidate_scores: list[float] = []
    for index, fold in enumerate(folds):
        if not isinstance(fold, dict):
            raise TypeError(f"fold {index} must be an object")
        block_id = fold.get("block_id")
        if not isinstance(block_id, str) or not block_id.strip() or block_id in block_ids:
            raise ValueError("fold block_id values must be non-empty and unique")
        block_ids.add(block_id)
        try:
            raw_values = (
                fold["incumbent_dti"],
                fold["candidate_dti"],
                fold["incumbent_mass"],
                fold["candidate_mass"],
            )
            if any(
                isinstance(value, bool) or not isinstance(value, (int, float))
                for value in raw_values
            ):
                raise TypeError("fold scores/masses must be numeric, not booleans/strings")
            incumbent, candidate, incumbent_mass, candidate_mass = map(float, raw_values)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"fold {index} has missing or invalid score/mass fields") from error
        if not all(math.isfinite(value) for value in (incumbent, candidate, incumbent_mass, candidate_mass)):
            raise ValueError(f"fold {index} contains non-finite values")
        if not (0.0 <= incumbent <= 1.0 and 0.0 <= candidate <= 1.0):
            raise ValueError(f"fold {index} score is outside [0, 1]")
        if not (0.0 <= incumbent_mass <= 1.0 and 0.0 <= candidate_mass <= 1.0):
            raise ValueError(f"fold {index} emission mass is outside [0, 1]")
        if abs(incumbent_mass - candidate_mass) > 1e-8:
            raise ValueError(f"fold {index} does not match emitted prediction mass")
        incumbent_scores.append(incumbent)
        candidate_scores.append(candidate)
        candidate_wins += candidate > incumbent

    incumbent_mean = sum(incumbent_scores) / len(incumbent_scores)
    candidate_mean = sum(candidate_scores) / len(candidate_scores)
    required_wins = math.ceil(2.0 * len(folds) / 3.0)
    if candidate_mean <= incumbent_mean:
        raise ValueError("candidate mean holdout score does not beat the incumbent")
    if candidate_wins < required_wins:
        raise ValueError(
            f"candidate wins {candidate_wins}/{len(folds)} folds; at least {required_wins} are required"
        )
    return {
        "report_id": report["report_id"],
        "model_code_revision": code_revision,
        "official_scorer_version": evidence["official_scorer_version"],
        "preregistration_sha256": evidence["preregistration_sha256"],
        "fold_assignment_sha256": evidence["fold_assignment_sha256"],
        "folds": len(folds),
        "guard_m": float(guard),
        "incumbent_mean_dti": incumbent_mean,
        "candidate_mean_dti": candidate_mean,
        "pooled_incumbent_dti": pooled_incumbent,
        "pooled_candidate_dti": pooled_candidate,
        "candidate_fold_wins": candidate_wins,
        "minimum_fold_wins": required_wins,
        "matched_mass": True,
    }


def _verify_clean_code_revision(expected_revision: str) -> None:
    """Require the promoted code commit to be the current clean project tree."""
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if revision != expected_revision:
        raise ValueError(
            f"current code revision {revision} differs from promoted revision {expected_revision}"
        )
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=ROOT,
        text=True,
    )
    if status.strip():
        raise ValueError("working tree is not clean; commit/review changes before packaging")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction", required=True, type=Path, help="new single-band prediction; not a prior submission")
    parser.add_argument("--promotion-report", required=True, type=Path, help="human-reviewed report following docs/promotion-report.schema.json")
    parser.add_argument("--template", required=True, type=Path, help="official sample-submission GeoTIFF (use its actual authorized-download path)")
    parser.add_argument("--features", required=True, type=Path, help="official training_features.tif for the footprint mask")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "artifacts" / "approved", help="ignored local output folder")
    parser.add_argument("--portal-note", help="optional short accurate portal note; defaults to a provenance-only description")
    args = parser.parse_args()
    for label, path in (("prediction", args.prediction), ("promotion report", args.promotion_report), ("template", args.template), ("features", args.features)):
        if not path.is_file():
            parser.error(f"{label} not found: {path}")
    args.out_dir = args.out_dir.resolve()
    if not args.out_dir.is_relative_to((ROOT / "artifacts").resolve()):
        parser.error("packaged files must be written under the ignored artifacts/ folder")

    try:
        report = json.loads(args.promotion_report.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise TypeError("promotion report must be a JSON object")
        gate_summary = _promotion_gate(report, args.prediction, args.template, args.features)
        _verify_clean_code_revision(gate_summary["model_code_revision"])
        input_audit = validate_submission(args.prediction, args.template, features_path=args.features)
    except (OSError, TypeError, json.JSONDecodeError, ValueError, RuntimeError) as error:
        print(f"PACKAGING BLOCKED\n{error}", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(args.template) as template:
        profile = template.profile.copy()
        width, height = template.width, template.height
        transform, crs = template.transform, template.crs
    with rasterio.open(args.prediction) as source:
        prediction_values = source.read(1)
    if prediction_values.shape != (height, width):
        print("PACKAGING BLOCKED\nprediction shape changed after validation", file=sys.stderr)
        return 2

    profile.update(
        driver="GTiff",
        width=width,
        height=height,
        count=1,
        dtype="float32",
        transform=transform,
        crs=crs,
        nodata=np.nan,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )
    with tempfile.NamedTemporaryFile(prefix=".gemsdoe47-build-", suffix=".tif", dir=args.out_dir, delete=False) as tmp:
        temporary_path = Path(tmp.name)
    try:
        with rasterio.open(temporary_path, "w", **profile) as destination:
            destination.write(prediction_values.astype(np.float32, copy=False), 1)
            destination.update_tags(
                PROJECT="GEMSDOE47",
                HYPOTHESIS="H47-A",
                VALIDATION_STATUS="SPATIAL_HOLDOUT_PROMOTED; see JSON receipt",
                PROMOTION_REPORT_ID=str(gate_summary["report_id"]),
            )
        output_hash = sha256_file(temporary_path)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"GEMSDOE47_H47A_GeoDAWNInvariant_v1_{timestamp}_{output_hash[:12]}.tif"
        final_path = args.out_dir / filename
        if final_path.exists():
            raise FileExistsError(f"refusing to overwrite existing artifact: {final_path}")
        os.replace(temporary_path, final_path)
        # Reopen the exact final path after the atomic rename. The receipt must
        # point to the deliverable that remains on disk, not a vanished temp.
        packaged_audit = validate_submission(
            final_path,
            args.template,
            features_path=args.features,
        )
        with rasterio.open(final_path) as packaged:
            packaged_values = packaged.read(1)
        if not np.array_equal(prediction_values, packaged_values, equal_nan=True):
            raise RuntimeError("packaged pixel values differ from promoted prediction bytes")
        if sha256_file(final_path) != output_hash:
            raise RuntimeError("artifact SHA-256 changed after packaging")
    except Exception:
        temporary_path.unlink(missing_ok=True)
        if "final_path" in locals() and final_path.exists():
            final_path.unlink()
        raise

    note = args.portal_note or (
        "H47-A: GeoDAWN acquisition-invariant magnetic/radiometric lineament candidate; "
        "external data: USGS GeoDAWN, DOI 10.5066/P93LGLVQ. See project validation receipt "
        f"{gate_summary['report_id']} for spatial holdout provenance."
    )
    receipt = {
        "status": "PACKAGED_NOT_SUBMITTED",
        "filename": filename,
        "sha256": output_hash,
        "created_utc": timestamp,
        "hypothesis_id": "H47-A",
        "promotion_report_sha256": sha256_file(args.promotion_report),
        "prediction_sha256": sha256_file(args.prediction),
        "template_sha256": sha256_file(args.template),
        "features_sha256": sha256_file(args.features),
        "holdout_gate": gate_summary,
        "input_validation": input_audit,
        "packaged_validation": packaged_audit,
        "portal_note": note,
        "submission_action": "manual entrant action required; no slot spent by this script",
    }
    receipt_path = final_path.with_suffix(".json")
    note_path = final_path.with_suffix(".txt")
    if receipt_path.exists() or note_path.exists():
        final_path.unlink(missing_ok=True)
        raise FileExistsError("refusing to overwrite an existing artifact receipt or portal note")
    temporary_receipt = None
    temporary_note = None
    receipt_created = False
    note_created = False
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=".gemsdoe47-receipt-", suffix=".tmp", dir=args.out_dir, delete=False
        ) as stream:
            temporary_receipt = Path(stream.name)
            stream.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=".gemsdoe47-note-", suffix=".tmp", dir=args.out_dir, delete=False
        ) as stream:
            temporary_note = Path(stream.name)
            stream.write(note + "\n")
        os.replace(temporary_receipt, receipt_path)
        receipt_created = True
        os.replace(temporary_note, note_path)
        note_created = True
    except Exception:
        if temporary_receipt is not None:
            temporary_receipt.unlink(missing_ok=True)
        if temporary_note is not None:
            temporary_note.unlink(missing_ok=True)
        if receipt_created:
            receipt_path.unlink(missing_ok=True)
        if note_created:
            note_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
