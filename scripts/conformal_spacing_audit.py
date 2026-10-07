#!/usr/bin/env python3
"""Recompute the H47-B spacing sweep and a split-conformal audit from pinned mirrors.

This script uses only files restored by ``scripts/restore_data.py``. It never
contacts DrivenData, submits anything, or authorizes a competition slot. The
scored label is the known-fault catalogue mask in the public mirror, used as a
diagnostic resemblance proxy. Conformalization targets future comparable
block-level proxy scores only—not the missing-fault target or leaderboard score.

The split is the frozen H47-B assignment: five selection blocks, six calibration
blocks, and five locked test blocks. Selection is performed only on the selection
blocks; calibration is applied once to the selected operating point. Spatial
exchangeability is not established, so the stated conformal coverage is
assumption-conditional. The generated raster is research-only irrespective of
its format audit.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gems47 import grid as G
from gems47.submission import validate_submission as validate_range_hypotheses
from gems47.submission import write_submission
from gemsdoe47.magnetic import (
    choose_spacing,
    greedy_spaced_pixels,
    guarded_grid_block_scores,
    magnetic_edge_persistence,
    pooled_block_dti,
    ranked_pixels,
    split_conformal_lower_bound,
)
from gemsdoe47.validation import validate_submission as validate_strict_submission
from scripts.build_footprint_mask import build_footprint_mask

DATA = G.data_dir()
FEATURES = DATA / "external" / "geodawn_extensions_u8.tif"
LABELS = DATA / "labels.tif"
TEMPLATE = DATA / "sample_submission.tif"
TRAINING_FEATURES = DATA / "training_features.tif"
VALIDATION_FOOTPRINT_MASK = DATA / "template_footprint_mask_u8.tif"
OUTPUT = ROOT / "docs" / "downloads" / (
    "gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-"
    "research-only-not-for-submission-20261006-nanoutside.tif"
)
ALLFINITE_DIAGNOSTIC = ROOT / "docs" / "downloads" / (
    "gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-"
    "research-only-not-for-submission-20261006-allfinite.tif"
)
REPORT = ROOT / "evidence" / "conformal_spacing_audit_20261006.json"

PINNED_SHA256 = {
    "features": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
    "labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "template": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}
TRAINING_FEATURES_SHA256 = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
SPACINGS_PX = (2, 3, 4, 5, 6)
BUDGET = 18_524
BLOCK_ROWS = 4
BLOCK_COLS = 4
GUARD_PX = 3
SELECTION_BLOCKS = (1, 4, 7, 10, 13)
CALIBRATION_BLOCKS = (0, 3, 6, 9, 12, 15)
LOCKED_TEST_BLOCKS = (2, 5, 8, 11, 14)
RANDOM_SEED = 47_062_026


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _verify_inputs() -> tuple[G.Template, np.ndarray, np.ndarray, dict[str, str]]:
    paths = {"features": FEATURES, "labels": LABELS, "template": TEMPLATE}
    hashes: dict[str, str] = {}
    for label, path in paths.items():
        _require(path.is_file(), f"missing {label}: {path}; run scripts/restore_data.py --group all")
        hashes[label] = sha256_file(path)
        _require(hashes[label] == PINNED_SHA256[label],
                 f"{label} SHA-256 mismatch: {hashes[label]} != {PINNED_SHA256[label]}")

    template = G.load_template(DATA)
    with rasterio.open(FEATURES) as feature_ds, rasterio.open(LABELS) as labels_ds:
        for name, ds in (("features", feature_ds), ("labels", labels_ds)):
            _require(ds.shape == template.shape, f"{name} shape differs from sample template")
            _require(ds.crs is not None and ds.crs.to_string() == template.crs,
                     f"{name} CRS differs from sample template")
            _require(tuple(ds.transform)[:6] == tuple(template.transform)[:6],
                     f"{name} geotransform differs from sample template")
        _require(feature_ds.count == 4 and feature_ds.dtypes[3] == "uint8",
                 "unexpected GeoDAWN extension raster band count/type")
        _require(labels_ds.count == 1 and labels_ds.dtypes[0] == "int8" and labels_ds.nodata == -1,
                 "unexpected label mirror profile")
        channel = feature_ds.read(4)
        labels = labels_ds.read(1)

    _require(np.array_equal(labels != -1, template.footprint),
             "label and sample-template footprints differ")
    _require(np.all(np.isin(labels[template.footprint], (0, 1))),
             "label values inside the footprint are not binary")
    _require(np.all((channel == 0) | template.footprint),
             "GeoDAWN channel has nonzero values outside the sample footprint")
    catalogue_mask = labels == 1
    return template, channel, catalogue_mask, hashes


def _write_template_footprint_mask_and_audit(template: G.Template) -> dict[str, Any]:
    _require(TRAINING_FEATURES.is_file(), f"missing training features: {TRAINING_FEATURES}")
    training_hash = sha256_file(TRAINING_FEATURES)
    _require(training_hash == TRAINING_FEATURES_SHA256,
             f"training feature SHA-256 mismatch: {training_hash}")
    mask_build = build_footprint_mask(TEMPLATE, VALIDATION_FOOTPRINT_MASK)
    _require(mask_build["status"] == "PASS", "sample-template footprint-mask builder failed")
    _require(mask_build["valid_pixels"] == int(template.footprint.sum()),
             "sample-template finite mask differs from the pinned label footprint")

    feature_only = template_only = template_pixels = feature_pixels = 0
    with (rasterio.open(TEMPLATE) as template_ds,
          rasterio.open(TRAINING_FEATURES) as feature_ds,
          rasterio.open(VALIDATION_FOOTPRINT_MASK) as mask_ds):
        _require(feature_ds.shape == template_ds.shape, "training feature shape differs from template")
        _require(feature_ds.crs == template_ds.crs, "training feature CRS differs from template")
        _require(feature_ds.transform == template_ds.transform,
                 "training feature transform differs from template")
        for _, window in template_ds.block_windows(1):
            sample = template_ds.read(1, window=window, masked=True)
            sample_values = np.asarray(np.ma.getdata(sample))
            sample_inside = np.isfinite(sample_values) & ~np.ma.getmaskarray(sample)
            mask_inside = mask_ds.read(1, window=window) != 0
            _require(np.array_equal(sample_inside, mask_inside),
                     "written binary mask differs from sample-template finite cells")
            row_start = int(window.row_off)
            col_start = int(window.col_off)
            expected = template.footprint[
                row_start:row_start + int(window.height),
                col_start:col_start + int(window.width),
            ]
            _require(np.array_equal(sample_inside, expected),
                     "sample-submission finite mask differs from the pinned label footprint")

            bands = feature_ds.read(window=window, masked=True)
            feature_data = np.asarray(np.ma.getdata(bands))
            feature_valid = np.isfinite(feature_data) & ~np.ma.getmaskarray(bands)
            feature_inside = np.any(feature_valid, axis=0)
            template_pixels += int(sample_inside.sum())
            feature_pixels += int(feature_inside.sum())
            feature_only += int((feature_inside & ~sample_inside).sum())
            template_only += int((sample_inside & ~feature_inside).sum())

    _require(template_pixels == mask_build["valid_pixels"],
             "windowed sample-footprint count differs from the mask-builder count")
    return {
        "training_features_sha256": training_hash,
        "template_footprint_source": "finite, unmasked cells in sample_submission.tif",
        "template_footprint_mask": str(VALIDATION_FOOTPRINT_MASK.relative_to(ROOT)),
        "template_footprint_mask_sha256": mask_build["footprint_mask_sha256"],
        "template_footprint_pixels": template_pixels,
        "features_derived_footprint_pixels": feature_pixels,
        "features_only_pixels_outside_template": feature_only,
        "template_pixels_invalid_in_features": template_only,
        "validator_note": (
            "The feature-derived footprint differs from the sample/label footprint in this mirror. "
            "Strict TIFF validation therefore used an explicit binary mask derived from finite, "
            "unmasked sample-template cells, not the training_features-derived mask; verify the "
            "authorized official mask for any future candidate."
        ),
    }


def _make_prediction(order: np.ndarray, shape: tuple[int, int], footprint: np.ndarray,
                     spacing: int) -> np.ndarray:
    selected = greedy_spaced_pixels(
        order,
        shape,
        min_separation_px=float(spacing),
        budget=BUDGET,
    )
    prediction = np.zeros(shape, dtype=np.float32)
    prediction.ravel()[selected] = 1.0
    prediction[~footprint] = np.nan
    _require(int(np.count_nonzero(prediction == 1.0)) == BUDGET,
             f"spacing {spacing}px failed to emit exactly {BUDGET} points")
    return prediction


def _score_sweep(order: np.ndarray, catalogue_mask: np.ndarray, footprint: np.ndarray) -> dict[int, list[dict[str, Any]]]:

    results: dict[int, list[dict[str, Any]]] = {}
    for spacing in SPACINGS_PX:
        prediction = _make_prediction(order, catalogue_mask.shape, footprint, spacing)
        rows = guarded_grid_block_scores(
            prediction,
            catalogue_mask,
            nrows=BLOCK_ROWS,
            ncols=BLOCK_COLS,
            guard_px=GUARD_PX,
        )
        for row in rows:
            row["role"] = (
                "selection" if row["block_id"] in SELECTION_BLOCKS else
                "calibration" if row["block_id"] in CALIBRATION_BLOCKS else "locked_test"
            )
        results[spacing] = rows
    return results


def _by_block(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(row["block_id"]): row for row in rows}


def _analyse_arm(
    name: str,
    sweep: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    selected_spacing, selection_mean = choose_spacing(sweep, SELECTION_BLOCKS)
    selected_rows = sweep[selected_spacing]
    by_id = _by_block(selected_rows)
    selection_scores = [float(by_id[i]["dti"]) for i in SELECTION_BLOCKS]
    calibration_scores = [float(by_id[i]["dti"]) for i in CALIBRATION_BLOCKS]
    conformal = split_conformal_lower_bound(selection_scores, calibration_scores)
    return {
        "arm": name,
        "selected_spacing_px": int(selected_spacing),
        "selected_spacing_m": int(selected_spacing * 100),
        "selection_mean_block_dti": float(selection_mean),
        "selection_block_scores": [
            {"block_id": i, "dti": float(by_id[i]["dti"])} for i in SELECTION_BLOCKS
        ],
        "calibration_block_scores": [
            {"block_id": i, "dti": float(by_id[i]["dti"])} for i in CALIBRATION_BLOCKS
        ],
        "locked_test_block_scores": [
            {"block_id": i, "dti": float(by_id[i]["dti"]),
             "catalogue_mask_pixels": int(by_id[i]["Ng"]),
             "predicted_pixels_in_core": int(by_id[i]["n_pred_pos"])}
            for i in LOCKED_TEST_BLOCKS
        ],
        "pooled_selection_dti": pooled_block_dti(selected_rows, SELECTION_BLOCKS),
        "pooled_calibration_dti": pooled_block_dti(selected_rows, CALIBRATION_BLOCKS),
        "pooled_locked_test_dti": pooled_block_dti(selected_rows, LOCKED_TEST_BLOCKS),
        "conformal_lower_prediction_bound": conformal,
        "spacing_sweep_by_px": {
            str(spacing): {
                "mean_selection_dti": float(np.mean([
                    _by_block(rows)[i]["dti"] for i in SELECTION_BLOCKS
                ])),
                "mean_calibration_dti": float(np.mean([
                    _by_block(rows)[i]["dti"] for i in CALIBRATION_BLOCKS
                ])),
                "mean_locked_test_dti": float(np.mean([
                    _by_block(rows)[i]["dti"] for i in LOCKED_TEST_BLOCKS
                ])),
                "pooled_selection_dti": pooled_block_dti(rows, SELECTION_BLOCKS),
                "pooled_calibration_dti": pooled_block_dti(rows, CALIBRATION_BLOCKS),
                "pooled_locked_test_dti": pooled_block_dti(rows, LOCKED_TEST_BLOCKS),
            }
            for spacing, rows in sorted(sweep.items())
        },
        "block_scores_at_every_spacing": {
            str(spacing): [
                {key: (int(value) if key in {"block_id", "Ng", "n_pred_pos"} else
                       float(value) if isinstance(value, (int, float, np.number)) else value)
                 for key, value in row.items()}
                for row in rows
            ]
            for spacing, rows in sorted(sweep.items())
        },
    }


def _random_control(
    template: G.Template,
    catalogue_mask: np.ndarray,
    common_support: np.ndarray,
    spacing: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(RANDOM_SEED)
    random_values = rng.random(template.shape, dtype=np.float32)
    valid = common_support & template.footprint
    order = ranked_pixels(random_values, valid)
    prediction = _make_prediction(order, template.shape, template.footprint, spacing)
    rows = guarded_grid_block_scores(
        prediction, catalogue_mask, nrows=BLOCK_ROWS, ncols=BLOCK_COLS, guard_px=GUARD_PX
    )
    for row in rows:
        row["role"] = (
            "selection" if row["block_id"] in SELECTION_BLOCKS else
            "calibration" if row["block_id"] in CALIBRATION_BLOCKS else "locked_test"
        )
    return {
        "seed": RANDOM_SEED,
        "spacing_px": spacing,
        "budget": BUDGET,
        "pooled_locked_test_dti": pooled_block_dti(rows, LOCKED_TEST_BLOCKS),
        "locked_test_block_scores": [
            {"block_id": i, "dti": float(_by_block(rows)[i]["dti"]),
             "catalogue_mask_pixels": int(_by_block(rows)[i]["Ng"])}
            for i in LOCKED_TEST_BLOCKS
        ],
    }


def run() -> dict[str, Any]:
    template, channel, catalogue_mask, hashes = _verify_inputs()
    footprint_audit = _write_template_footprint_mask_and_audit(template)
    valid = (channel > 0) & template.footprint
    rank_field = np.zeros(template.shape, dtype=np.float32)
    rank_field[valid] = (channel[valid].astype(np.float32) - 1.0) / 254.0

    print("Computing cross-scale H47-B and single-scale comparator fields...")
    h47b_score, single_scale_score, common_support, diagnostics = magnetic_edge_persistence(
        rank_field,
        valid,
        scales_px=(2.0, 4.0, 8.0),
        support_threshold=0.99,
        normalization_quantile=0.99,
    )
    h47b_valid = common_support & template.footprint & (h47b_score > 0.0)
    single_valid = common_support & template.footprint & (single_scale_score > 0.0)
    _require(int(h47b_valid.sum()) >= BUDGET, "H47-B support cannot meet the fixed emission budget")
    _require(int(single_valid.sum()) >= BUDGET, "single-scale support cannot meet the fixed emission budget")

    h47b_order = ranked_pixels(h47b_score, h47b_valid)
    single_order = ranked_pixels(single_scale_score, single_valid)
    print("Scoring five operating points in 16 guarded spatial blocks...")
    h47b_sweep = _score_sweep(h47b_order, catalogue_mask, template.footprint)
    single_sweep = _score_sweep(single_order, catalogue_mask, template.footprint)
    h47b = _analyse_arm("H47-B cross-scale persistence", h47b_sweep)
    single = _analyse_arm("single-scale 400m edge comparator", single_sweep)

    _require(h47b["selected_spacing_px"] == 5,
             "recomputed H47-B selection differs from the frozen screen (expected 5px)")
    _require(single["selected_spacing_px"] == 5,
             "recomputed single-scale selection differs from the frozen screen (expected 5px)")

    # The spacing decision and conformal calibration are now fixed. The random
    # control and locked test are reported separately and cannot change selection.
    random = _random_control(template, catalogue_mask, common_support, h47b["selected_spacing_px"])
    h47b_test = h47b["pooled_locked_test_dti"]
    single_test = single["pooled_locked_test_dti"]
    random_test = random["pooled_locked_test_dti"]
    single_floor = single["conformal_lower_prediction_bound"]["lower_bound_clipped"]

    # The primary research file is a newly generated single-scale d=5 mask,
    # distinct from the older H47-B cross-scale raster. It follows the template's
    # NaN-outside-footprint convention and remains research-only because its
    # diagnostic proxy/control screen failed.
    selected_prediction = _make_prediction(
        single_order, template.shape, template.footprint, single["selected_spacing_px"]
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    write_submission(selected_prediction, OUTPUT, mode="nan", template=template)

    strict_audit = validate_strict_submission(
        OUTPUT, TEMPLATE, footprint_mask_path=VALIDATION_FOOTPRINT_MASK
    )
    _require(strict_audit["status"] == "PASS", "strict local submission validator did not pass")
    _require(strict_audit["invalid_inside_pixels"] == 0, "strict validator found invalid in-footprint pixels")
    _require(strict_audit["non_nan_outside_pixels"] == 0, "strict validator found numeric values outside footprint")
    _require(strict_audit["below_zero_pixels"] == 0 and strict_audit["above_one_pixels"] == 0,
             "strict validator found in-footprint values outside [0,1]")
    for path_key in ("submission", "template", "footprint_source"):
        strict_audit[path_key] = str(Path(strict_audit[path_key]).relative_to(ROOT))

    try:
        validate_strict_submission(OUTPUT, TEMPLATE, features_path=TRAINING_FEATURES)
    except ValueError as exc:
        feature_derived_validation = {
            "status": "FAIL",
            "failures": str(exc).splitlines(),
            "interpretation": (
                "The same TIFF passes against the explicit sample-template mask but fails when "
                "training_features-derived validity is treated as the footprint; this is the recorded "
                "mirror mask discrepancy, not evidence that either mask is the authorized official footprint."
            ),
        }
    else:
        raise ValueError("feature-derived validation unexpectedly passed despite the pinned footprint mismatch")

    range_probe = validate_range_hypotheses(OUTPUT, template=template)
    _require(range_probe["passes_nan_tolerant_range_check"],
             "NaN-tolerant local range check failed on the primary research TIFF")
    diagnostic_variant = {
        "path": str(ALLFINITE_DIAGNOSTIC.relative_to(ROOT)),
        "exists": ALLFINITE_DIAGNOSTIC.is_file(),
        "sha256": sha256_file(ALLFINITE_DIAGNOSTIC) if ALLFINITE_DIAGNOSTIC.is_file() else None,
        "interpretation": (
            "same single-scale positive mask with zeros outside the footprint; useful only to test "
            "a NaN-intolerant range expression, and not compliant with the strict NaN-outside validator"
        ),
    }
    if ALLFINITE_DIAGNOSTIC.is_file():
        try:
            validate_strict_submission(
                ALLFINITE_DIAGNOSTIC, TEMPLATE, footprint_mask_path=VALIDATION_FOOTPRINT_MASK
            )
        except ValueError as exc:
            diagnostic_variant["strict_validator_failure"] = str(exc)
        else:
            diagnostic_variant["strict_validator_failure"] = None

    format_audit = {
        "strict_submission_validation": strict_audit,
        "feature_derived_validation_probe": feature_derived_validation,
        "range_error_probe": {
            "passes_nan_intolerant_range_check": range_probe["passes_nan_intolerant_range_check"],
            "passes_nan_tolerant_range_check": range_probe["passes_nan_tolerant_range_check"],
            "legacy_recommended_for_upload": range_probe["recommended_for_upload"],
            "interpretation": (
                "the primary TIFF satisfies the strict NaN-outside format contract and the "
                "NaN-tolerant [0,1] check, but a naive all-pixel comparison rejects its allowed NaNs; "
                "this demonstrates a plausible parser hazard, not the unknown historical portal cause"
            ),
        },
        "allfinite_diagnostic_variant": diagnostic_variant,
        "slot_eligible": False,
        "submission_recommendation": (
            "NOT FOR SUBMISSION: strict format validity is not scientific validation or organizer acceptance"
        ),
    }

    promotion_reasons = []
    if single_test <= h47b_test:
        promotion_reasons.append("single-scale locked-test pooled DTI did not beat selected H47-B")
    if single_test <= random_test:
        promotion_reasons.append("single-scale locked-test pooled DTI did not beat the fixed-seed random control")
    if single_floor <= 0.0:
        promotion_reasons.append("split-conformal lower bound is zero, so there is no positive floor")
    promotion_reasons.append("all inputs are owner-hosted mirrors, not authenticated organizer downloads")
    promotion_reasons.append("spatial block exchangeability is unverified")
    promotion_reasons.append(
        "this run is a known-fault catalogue-mask resemblance proxy, not a missing-fault target evaluation"
    )

    empty_blocks = []
    selected_by_id = _by_block(single_sweep[single["selected_spacing_px"]])
    for block_id, row in sorted(selected_by_id.items()):
        if int(row["Ng"]) == 0:
            empty_blocks.append({
                "block_id": int(block_id),
                "role": row["role"],
                "reason": "no known-catalogue-mask pixels in guarded block core",
            })

    report = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_id": "H47-B-single-scale-control",
        "source_data_provenance": (
            "owner-hosted, hash-pinned GEMSDOE24 GitHub mirror; hashes establish byte consistency, "
            "not authenticated organizer provenance"
        ),
        "source_links": {
            "competition_problem": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
            "known_catalogue_mask_clarification": "https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516",
            "official_geodawn_release": "https://doi.org/10.5066/P93LGLVQ",
            "mirror_repository": "https://github.com/buffedlizard55-lab/GEMSDOE24",
            "conformal_paper": "https://doi.org/10.1080/01621459.2017.1307116",
        },
        "input_sha256": hashes,
        "grid": {
            "shape": list(template.shape),
            "crs": template.crs,
            "transform_gdal": list(template.transform.to_gdal()),
            "resolution_m": 100,
            "footprint_pixels": int(template.footprint.sum()),
            "known_catalogue_mask_pixels": int(template.catalogue.sum()),
        },
        "validation_footprint_audit": footprint_audit,
        "feature": {
            "channel": "TMI_up150, uint8 rank-encoded mirror channel",
            "transform": "masked Gaussian edge magnitude; sigma 4 px, common H47-B support",
            "score_diagnostics": diagnostics,
            "interpretation_boundary": (
                "not raw magnetic units, a physical tilt-depth solution, or a calibrated fault probability"
            ),
        },
        "protocol": {
            "spacings_px": list(SPACINGS_PX),
            "spacings_m": [100 * x for x in SPACINGS_PX],
            "fixed_budget_per_raster": BUDGET,
            "guarded_grid": [BLOCK_ROWS, BLOCK_COLS],
            "guard_px": GUARD_PX,
            "guard_m": GUARD_PX * 100,
            "selection_blocks": list(SELECTION_BLOCKS),
            "calibration_blocks": list(CALIBRATION_BLOCKS),
            "locked_test_blocks": list(LOCKED_TEST_BLOCKS),
            "evaluation_target": (
                "labels.tif == 1, a known-fault catalogue mask; diagnostic resemblance proxy only, "
                "not the hidden new-fault target used to reward off-catalogue predictions"
            ),
            "selection_rule": "mean DTI over selection blocks; exact ties prefer larger spacing",
            "conformal_rule": (
                "one-sided split conformal on the selected spacing's catalogue-mask proxy DTI only; "
                "residual = selection mean - calibration proxy DTI; rank ceil((n+1)*(1-alpha)), alpha=1/(n+1)"
            ),
            "locked_test_used_for_selection": False,
        },
        "protocol_provenance": {
            "original_frozen_document_sha256": (
                "4cb65d953e575d942f0b1db8d258a36fbc2c8caea32e3409da127d36eaa0c6c6"
            ),
            "current_clarified_document_sha256": sha256_file(ROOT / "docs" / "preregistered-h2.md"),
            "post_score_clarification_scope": (
                "target interpretation only: labels.tif == 1 is the known-fault catalogue-mask proxy; "
                "no inputs, labels, splits, formulas, or scores changed"
            ),
        },
        "empty_guarded_blocks": empty_blocks,
        "arms": {
            "H47-B": h47b,
            "single_scale_baseline": single,
        },
        "random_control": random,
        "comparisons": {
            "H47B_pooled_locked_test_dti": h47b_test,
            "single_scale_pooled_locked_test_dti": single_test,
            "random_pooled_locked_test_dti": random_test,
            "single_scale_beats_H47B": bool(single_test > h47b_test),
            "single_scale_beats_random": bool(single_test > random_test),
        },
        "artifact": {
            "path": str(OUTPUT.relative_to(ROOT)),
            "sha256": sha256_file(OUTPUT),
            "bytes": OUTPUT.stat().st_size,
            "status": "RESEARCH_ONLY_NOT_PROMOTED",
            "format_audit": format_audit,
            "selected_spacing_px": single["selected_spacing_px"],
            "selected_spacing_m": single["selected_spacing_m"],
            "conformal_nominal_coverage": single["conformal_lower_prediction_bound"]["nominal_coverage"],
            "conformal_lower_floor": single_floor,
            "submission_note_for_a_research_trial_only": (
                "single-scale edge; d=5 px/500 m; catalogue-mask proxy conformal 6/7=85.7% nominal, "
                "assumption-conditional lower-bound estimate 0.000 (exchangeability unverified); RESEARCH ONLY"
            ),
            "not_for_submission_because": promotion_reasons,
        },
        "promotion": {
            "slot_eligible": False,
            "status": "NOT_PROMOTED",
            "reasons": promotion_reasons,
        },
        "conformal_interpretation": {
            "nominal_confidence_level": single["conformal_lower_prediction_bound"]["nominal_coverage"],
            "floor": single_floor,
            "meaning_if_exchangeability_held": (
                "marginal 85.7% split-conformal coverage for a lower prediction bound on a future comparable "
                "block-level DTI against the known-fault catalogue mask (diagnostic proxy only); this does "
                "not cover the missing-fault target and is not a worst-case, cellwise, or leaderboard guarantee"
            ),
            "assumption_status": "unverified; spatial dependence and empty catalogue-mask blocks occur",
            "positive_guarantee": False,
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"H47-B: selected d={h47b['selected_spacing_px']} px, "
          f"locked DTI={h47b_test:.8f}, conformal floor="
          f"{h47b['conformal_lower_prediction_bound']['lower_bound_clipped']:.8f}")
    print(f"Single-scale: selected d={single['selected_spacing_px']} px, "
          f"locked DTI={single_test:.8f}, random={random_test:.8f}, "
          f"conformal floor={single_floor:.8f}")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes), SHA256 {sha256_file(OUTPUT)}")
    print(f"Report: {REPORT}")
    print("DECISION: NOT PROMOTED; no competition slot is authorized.")
    return report


def main() -> int:
    try:
        run()
    except (FileNotFoundError, ValueError, AssertionError, rasterio.errors.RasterioError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
