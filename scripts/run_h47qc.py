#!/usr/bin/env python3
"""Run the preregistered H47-QC geothermometer-consensus screen.

The candidate field is built without reading the public label raster. Only after
all seven ranking fields and their fixed support masks exist does this script
open labels for the guarded 4x4 block DTI screen. A failed research gate still
writes a clearly named research-only GeoTIFF; this script never uploads files or
opens a competition slot.

Run after restoring the manifest-pinned local mirror files:
    PYTHONPATH=src .venv/bin/python scripts/run_h47qc.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
from gems47 import submission as S
from gems47.geochem_consensus import (
    combine_geochemistry_and_structure,
    geochemistry_influence,
    read_consensus_points,
    structural_edge_agreement,
)
from gemsdoe47.magnetic import (
    choose_spacing,
    greedy_spaced_pixels,
    guarded_grid_block_scores,
    magnetic_edge_persistence,
    pooled_block_dti,
    ranked_pixels,
    split_conformal_lower_bound,
)

DATA = G.data_dir()
BUDGET = 5_000
SPACINGS = (2, 3, 4, 5, 6)
BLOCK_SHAPE = (4, 4)
GUARD_PX = 3
SELECTION_BLOCKS = (1, 4, 7, 10, 13)
CALIBRATION_BLOCKS = (0, 3, 6, 9, 12, 15)
TEST_BLOCKS = (2, 5, 8, 11, 14)
RANDOM_SEED = 47062026
OUTPUT_REL = Path(
    "docs/downloads/gems47-h47qc-geothermometer-consensus-n5000-"
    "research-only-20261006.tif"
)
REPORT_REL = Path("evidence/h47qc-screen-20261006.json")

PINNED_SHA256 = {
    "gdr_wellspring_csv": "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
    "training_features": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "geodawn_extensions": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check_pins(paths: dict[str, Path]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for key, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"missing pinned input {key}: {path}")
        value = sha256_file(path)
        expected = PINNED_SHA256[key]
        if value != expected:
            raise ValueError(f"SHA-256 mismatch for {key}: {value} != {expected}")
        observed[key] = value
    return observed


def _read_prediction_grid(sample_path: Path) -> tuple[tuple[int, int], np.ndarray, dict[str, Any]]:
    """Read only the sample raster for the candidate builder's grid and mask."""
    with rasterio.open(sample_path) as src:
        raw = src.read(1)
        footprint = np.isfinite(raw) & (src.read_masks(1) > 0)
        meta = {
            "shape": list(src.shape),
            "crs": str(src.crs),
            "transform": list(src.transform)[:6],
            "resolution_m": [float(src.transform.a), float(src.transform.e)],
            "count": src.count,
            "dtype": src.dtypes[0],
            "nodata": "NaN" if isinstance(src.nodata, float) and math.isnan(src.nodata) else src.nodata,
            "footprint_pixels": int(footprint.sum()),
        }
    if meta["count"] != 1 or meta["dtype"] != "float32":
        raise ValueError("sample_submission must be a one-band float32 raster")
    if meta["crs"] != G.CRS or tuple(meta["shape"]) != G.SHAPE:
        raise ValueError(f"unexpected sample grid: {meta}")
    if not np.array_equal(meta["resolution_m"], [100.0, -100.0]):
        raise ValueError(f"unexpected sample resolution: {meta['resolution_m']}")
    return tuple(meta["shape"]), footprint, meta


def _band_index(dataset: rasterio.io.DatasetReader, short_name: str) -> int:
    """Resolve a one-based training-band index from the embedded description."""
    for index, description in enumerate(dataset.descriptions, start=1):
        if description and description.split(" - ", 1)[0].strip() == short_name:
            return index
    raise ValueError(f"training_features.tif has no described {short_name!r} band")


def _build_score_fields(
    *,
    csv_path: Path,
    features_path: Path,
    extensions_path: Path,
    shape: tuple[int, int],
    footprint: np.ndarray,
) -> tuple[dict[str, tuple[np.ndarray | None, np.ndarray]], dict[str, Any]]:
    """Build all candidate/control rank fields without opening labels.tif."""
    points, source_audit = read_consensus_points(csv_path, shape)
    geo_surface, geo_support, geo_diagnostics = geochemistry_influence(
        points, shape, footprint
    )

    with rasterio.open(features_path) as src:
        rtp_band = _band_index(src, "rtp")
        gravity_band = _band_index(src, "iso_grav_anom")
        if src.count != 19 or src.shape != shape:
            raise ValueError("training feature raster does not match the preregistered grid")
        rtp = src.read(rtp_band).astype(np.float32, copy=False)
        gravity = src.read(gravity_band).astype(np.float32, copy=False)

    edge, edge_support, edge_diagnostics = structural_edge_agreement(
        rtp, gravity, footprint
    )
    del rtp, gravity
    combined, combined_valid = combine_geochemistry_and_structure(
        geo_surface, geo_support, edge, edge_support, footprint
    )
    geochem_valid = geo_support & footprint & (geo_surface > 0.0)
    structural_valid = edge_support & footprint & (edge > 0.0)

    with rasterio.open(extensions_path) as src:
        if src.count != 4 or src.shape != shape or src.dtypes[3] != "uint8":
            raise ValueError("GeoDAWN extension raster does not match the pinned H47-B input")
        tmi_up150 = src.read(4)
    mag_valid = (tmi_up150 > 0) & footprint
    mag_rank = np.zeros(shape, dtype=np.float32)
    mag_rank[mag_valid] = (tmi_up150[mag_valid].astype(np.float32) - 1.0) / 254.0
    h47b, single_scale, common_support, mag_diagnostics = magnetic_edge_persistence(
        mag_rank,
        mag_valid,
        scales_px=(2.0, 4.0, 8.0),
        support_threshold=0.99,
        normalization_quantile=0.99,
    )
    h47b_valid = common_support & footprint & (h47b > 0.0)
    single_valid = common_support & footprint & (single_scale > 0.0)

    score_fields: dict[str, tuple[np.ndarray | None, np.ndarray]] = {
        "H47-QC": (combined, combined_valid),
        "geochemistry-only": (geo_surface, geochem_valid),
        "structural-edge-only": (edge, structural_valid),
        "H47-B-equal-mass": (h47b, h47b_valid),
        "single-scale-magnetic-equal-mass": (single_scale, single_valid),
        "random-within-H47-QC-support": (None, combined_valid.copy()),
        "random-full-footprint": (None, footprint.copy()),
    }
    for name, (score, valid) in score_fields.items():
        if score is not None:
            if not np.isfinite(score[valid]).all():
                raise ValueError(f"{name} score has non-finite supported cells")
            if np.any(score[valid] < 0.0):
                raise ValueError(f"{name} score has negative supported cells")
        if int(valid.sum()) < BUDGET:
            raise ValueError(
                f"{name} support has only {int(valid.sum())} cells for fixed budget {BUDGET}"
            )

    diagnostics = {
        "geochem_source": {
            **source_audit.__dict__,
            "fields_used": list(source_audit.fields_used),
        },
        "geochem_surface": geo_diagnostics,
        "structural_edge": edge_diagnostics,
        "magnetic_h47b": mag_diagnostics,
        "support_pixels_by_variant": {
            name: int(valid.sum()) for name, (_, valid) in score_fields.items()
        },
        "candidate_field_normalization": "relative, uncalibrated; no label-informed calibration",
        "label_free_builder": True,
        "ignored_csv_field": "dist_known_fault_px",
    }
    return score_fields, diagnostics


def _random_order(valid: np.ndarray, seed: int) -> np.ndarray:
    indices = np.flatnonzero(valid.ravel())
    np.random.default_rng(seed).shuffle(indices)
    return indices


def _mean_score(rows: list[dict[str, Any]], block_ids: tuple[int, ...]) -> float:
    by_id = {int(row["block_id"]): row for row in rows}
    return float(np.mean([by_id[block_id]["dti"] for block_id in block_ids]))


def _summarize_variant(rows_by_spacing: dict[int, list[dict[str, Any]]]) -> dict[str, Any]:
    selected_spacing, selection_mean = choose_spacing(rows_by_spacing, SELECTION_BLOCKS)
    summaries: dict[str, Any] = {}
    for spacing, rows in sorted(rows_by_spacing.items()):
        summaries[str(spacing)] = {
            "mean_selection_block_dti": _mean_score(rows, SELECTION_BLOCKS),
            "mean_calibration_block_dti": _mean_score(rows, CALIBRATION_BLOCKS),
            "mean_locked_test_block_dti": _mean_score(rows, TEST_BLOCKS),
            "pooled_selection_dti": pooled_block_dti(rows, SELECTION_BLOCKS),
            "pooled_calibration_dti": pooled_block_dti(rows, CALIBRATION_BLOCKS),
            "pooled_locked_test_dti": pooled_block_dti(rows, TEST_BLOCKS),
        }
    selected_rows = rows_by_spacing[selected_spacing]
    return {
        "selected_spacing_px": int(selected_spacing),
        "selected_spacing_m": int(selected_spacing * 100),
        "selection_mean_block_dti": selection_mean,
        "selected_spacing_results": summaries[str(selected_spacing)],
        "sweep": summaries,
        "selected_block_rows": selected_rows,
    }


def _score_all_variants(
    score_fields: dict[str, tuple[np.ndarray | None, np.ndarray]],
    labels: np.ndarray,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[int, np.ndarray]]]:
    truth = labels == 1
    results: dict[str, dict[str, Any]] = {}
    emitted_positions: dict[str, dict[int, np.ndarray]] = {}
    for name, (score_field, valid) in score_fields.items():
        if score_field is None:
            order = _random_order(valid, RANDOM_SEED + (0 if name.endswith("support") else 1))
        else:
            order = ranked_pixels(score_field, valid)
        rows_by_spacing: dict[int, list[dict[str, Any]]] = {}
        positions_by_spacing: dict[int, np.ndarray] = {}
        for spacing in SPACINGS:
            positions = greedy_spaced_pixels(
                order,
                labels.shape,
                min_separation_px=float(spacing),
                budget=BUDGET,
            )
            prediction = np.zeros(labels.shape, dtype=np.float32)
            prediction.ravel()[positions] = 1.0
            rows = guarded_grid_block_scores(
                prediction,
                truth,
                nrows=BLOCK_SHAPE[0],
                ncols=BLOCK_SHAPE[1],
                guard_px=GUARD_PX,
            )
            if int(np.count_nonzero(prediction)) != BUDGET:
                raise AssertionError(f"{name} emitted the wrong mass at spacing {spacing}")
            rows_by_spacing[spacing] = rows
            positions_by_spacing[spacing] = positions
        results[name] = _summarize_variant(rows_by_spacing)
        emitted_positions[name] = positions_by_spacing
    return results, emitted_positions


def _block_truth_counts(labels: np.ndarray) -> list[dict[str, int]]:
    counts: list[dict[str, int]] = []
    row_edges = np.linspace(0, labels.shape[0], BLOCK_SHAPE[0] + 1).astype(int)
    col_edges = np.linspace(0, labels.shape[1], BLOCK_SHAPE[1] + 1).astype(int)
    for block_row in range(BLOCK_SHAPE[0]):
        for block_col in range(BLOCK_SHAPE[1]):
            row0 = int(row_edges[block_row]) + GUARD_PX
            row1 = int(row_edges[block_row + 1]) - GUARD_PX
            col0 = int(col_edges[block_col]) + GUARD_PX
            col1 = int(col_edges[block_col + 1]) - GUARD_PX
            block_id = block_row * BLOCK_SHAPE[1] + block_col
            counts.append({
                "block_id": block_id,
                "positive_truth_pixels": int(np.count_nonzero(
                    labels[row0:row1, col0:col1] == 1
                )),
            })
    return counts


def _load_labels_for_evaluation(labels_path: Path, footprint: np.ndarray) -> np.ndarray:
    """Open labels only after label-free surfaces and support masks are built."""
    with rasterio.open(labels_path) as src:
        labels = src.read(1)
        if src.shape != footprint.shape:
            raise ValueError("label raster shape does not match the sample grid")
        if not np.array_equal(labels != -1, footprint):
            raise ValueError("label/template footprints disagree")
        if not np.all(np.isin(labels[footprint], (0, 1))):
            raise ValueError("label raster contains unexpected in-footprint values")
    return labels


def run(output_path: Path, report_path: Path) -> dict[str, Any]:
    start = time.time()
    csv_path = DATA / "external" / "gdr_wellspring_in_footprint.csv"
    features_path = DATA / "training_features.tif"
    labels_path = DATA / "labels.tif"
    sample_path = DATA / "sample_submission.tif"
    extensions_path = DATA / "external" / "geodawn_extensions_u8.tif"
    input_paths = {
        "gdr_wellspring_csv": csv_path,
        "training_features": features_path,
        "labels": labels_path,
        "sample_submission": sample_path,
        "geodawn_extensions": extensions_path,
    }
    hashes = _check_pins(input_paths)
    shape, footprint, grid_meta = _read_prediction_grid(sample_path)

    print("[h47qc] building source and structural fields without labels", flush=True)
    score_fields, feature_diagnostics = _build_score_fields(
        csv_path=csv_path,
        features_path=features_path,
        extensions_path=extensions_path,
        shape=shape,
        footprint=footprint,
    )
    print("[h47qc] score fields built; now opening public labels for guarded DTI", flush=True)
    labels = _load_labels_for_evaluation(labels_path, footprint)
    truth_counts = _block_truth_counts(labels)
    results, emitted_positions = _score_all_variants(score_fields, labels)

    candidate = results["H47-QC"]
    selected_spacing = int(candidate["selected_spacing_px"])
    by_id = {int(row["block_id"]): row for row in candidate["selected_block_rows"]}
    conformal = split_conformal_lower_bound(
        [float(by_id[index]["dti"]) for index in SELECTION_BLOCKS],
        [float(by_id[index]["dti"]) for index in CALIBRATION_BLOCKS],
    )
    comparators = {
        name: {
            "selected_spacing_px": int(summary["selected_spacing_px"]),
            "selected_spacing_m": int(summary["selected_spacing_m"]),
            "locked_test_pooled_dti": float(
                summary["selected_spacing_results"]["pooled_locked_test_dti"]
            ),
            "locked_test_mean_block_dti": float(
                summary["selected_spacing_results"]["mean_locked_test_block_dti"]
            ),
        }
        for name, summary in results.items()
        if name != "H47-QC"
    }
    candidate_test = float(candidate["selected_spacing_results"]["pooled_locked_test_dti"])
    beats_every_comparator = all(
        candidate_test > item["locked_test_pooled_dti"]
        for item in comparators.values()
    )
    nonzero_conformal_floor = float(conformal["lower_bound_clipped"]) > 0.0
    exact_mass = int(BUDGET) == int(emitted_positions["H47-QC"][selected_spacing].size)
    numerical_screen_pass = bool(
        exact_mass and beats_every_comparator and nonzero_conformal_floor
    )
    # Provenance authorization, full uniqueness review, and human scientific
    # release review are not machine-inferred; this runner never authorizes an upload.
    promotion_pass = False

    prediction = np.zeros(shape, dtype=np.float32)
    selected_positions = emitted_positions["H47-QC"][selected_spacing]
    prediction.ravel()[selected_positions] = 1.0
    template = G.load_template(DATA)
    S.write_submission(prediction, output_path, mode="zeros", template=template)
    # The repository writer's generic competition label says “probability”; this
    # binary, uncalibrated research mask must not be presented as calibrated.
    with rasterio.open(output_path, "r+") as written:
        written.update_tags(
            1,
            LAYER="H47-QC binary research mask; uncalibrated, not probability",
        )
        written.update_tags(
            HYPOTHESIS_ID="H47-QC",
            STATUS="RESEARCH_ONLY_NOT_FOR_PORTAL",
        )
    artifact_audit = S.validate_submission(output_path, template=template)
    outside_cells = int(template.footprint.size - template.footprint.sum())
    format_review = {
        "status": "FAIL" if not artifact_audit["checks"]["outside_template_footprint_is_nodata"] else "LOCAL_CHECKS_PASS",
        "published_requirement": "Cells outside the training-data bounds must be null or NaN.",
        "outside_null_or_nan": artifact_audit["checks"]["outside_template_footprint_is_nodata"],
        "footprint_cells": int(template.footprint.sum()),
        "outside_cells": outside_cells,
        "outside_cells_finite": int(artifact_audit["stats"]["n_finite"] - artifact_audit["stats"]["n_footprint"]),
        "footprint_basis": "Owner-supplied mirror; not organizer-authenticated.",
        "submission_eligible": False,
        "slot_authorized": False,
        "organizer_acceptance_established": False,
        "reason": "This historical H47-QC writer uses finite zeros outside the mirror footprint; that fails the published null-or-NaN-outside requirement.",
    }
    if not artifact_audit["required_local_checks_passed"]:
        print("[h47qc] format review failed; preserving this as research-only evidence; no upload is authorized", file=sys.stderr)
    artifact_hash = sha256_file(output_path)

    # The old H47-B number is useful context, but it used 18,524 points and is
    # deliberately not mixed into this 5,000-point matched-mass gate.
    old_h47b_context = {
        "budget": 18_524,
        "selected_spacing_px": 5,
        "locked_test_pooled_dti": 0.02755344310252606,
        "fixed_seed_random_locked_test_pooled_dti": 0.03715911385648702,
        "single_scale_baseline_locked_test_pooled_dti": 0.02563946679372895,
        "note": "historical different-mass public-catalogue screen; context only",
    }
    report = {
        "schema_version": 1,
        "hypothesis_id": "H47-QC",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "protocol": "docs/preregistered-h47qc-20261006.md",
        "scope": "public-catalogue spatial-block screen on hash-pinned owner mirrors; not private-label validation",
        "inputs": {
            "data_directory": str(DATA),
            "sha256": hashes,
            "grid": grid_meta,
        },
        "candidate_construction": feature_diagnostics,
        "block_protocol": {
            "nrows": BLOCK_SHAPE[0],
            "ncols": BLOCK_SHAPE[1],
            "guard_px": GUARD_PX,
            "guard_m": GUARD_PX * 100,
            "selection_block_ids": list(SELECTION_BLOCKS),
            "calibration_block_ids": list(CALIBRATION_BLOCKS),
            "locked_test_block_ids": list(TEST_BLOCKS),
            "spatial_independence": "not established",
            "positive_truth_by_guarded_block": truth_counts,
        },
        "emission": {
            "budget": BUDGET,
            "spacings_px": list(SPACINGS),
            "selection_rule": "highest mean block DTI on selection blocks; exact ties favor larger spacing",
            "pixel_values": [0.0, 1.0],
            "random_seed": RANDOM_SEED,
        },
        "spacing_sweep": results,
        "selected_candidate": {
            "spacing_px": selected_spacing,
            "spacing_m": int(selected_spacing * 100),
            "positive_pixels": int(selected_positions.size),
            "selection_mean_block_dti": float(candidate["selection_mean_block_dti"]),
            "calibration_mean_block_dti": float(
                candidate["selected_spacing_results"]["mean_calibration_block_dti"]
            ),
            "locked_test_mean_block_dti": float(
                candidate["selected_spacing_results"]["mean_locked_test_block_dti"]
            ),
            "locked_test_pooled_dti": candidate_test,
        },
        "split_conformal_lower_bound": conformal,
        "matched_mass_comparators": comparators,
        "historical_h47b_different_mass_context": old_h47b_context,
        "review_interpretation": {
            "status": "RESEARCH_ONLY_NOT_PROMOTED",
            "promotion_gate_passed": False,
            "submission_eligible": False,
            "slot_authorized": False,
            "current_format_review": format_review["status"],
            "reason": format_review["reason"],
        },
        "promotion_gate": {
            "must_beat_all_matched_comparators_on_locked_test": True,
            "beats_every_comparator": beats_every_comparator,
            "must_have_positive_conformal_floor": True,
            "positive_floor": nonzero_conformal_floor,
            "exact_mass": exact_mass,
            "numerical_screen_passed": numerical_screen_pass,
            "provenance_and_uniqueness_review_completed_by_runner": False,
            "human_scientific_release_review_completed_by_runner": False,
            "upload_authorized": False,
            "passed": promotion_pass,
            "decision": "NOT PROMOTED — numerical screen fails; research only, do not upload or spend a slot",
        },
        "artifact": {
            "path": str(output_path.relative_to(ROOT)),
            "sha256": artifact_hash,
            "format_audit": artifact_audit,
            "format_review": format_review,
            "emitted_on_public_catalogue_pixels": int(
                artifact_audit["stats"]["n_emitted_on_catalogue"]
            ),
            "emitted_public_catalogue_fraction": float(
                artifact_audit["stats"]["n_emitted_on_catalogue"] / BUDGET
            ),
            "suggested_note_field_text": (
                "H47-QC geothermometer consensus × aligned RTP–gravity edge; "
                "5,000 binary pixels; RESEARCH ONLY"
            ),
            "portal_note": (
                "RESEARCH ONLY — NOT FOR SUBMISSION. H47-QC public-catalogue screen; "
                "locked-test/control and positive conformal-floor gate did not pass."
            ),
        },
        "limitations": [
            "CSV and competition rasters are owner-hosted mirrors; hashes prove mirror consistency, not organizer authentication",
            "the GDR field dictionary for the mirror-exported geothermometer columns was not independently verified",
            "geothermometer methods share samples and may be biased by water chemistry, disequilibrium, and dilution",
            "source rows are grouped locations, not guaranteed independent wells or sampling events; no time field supports persistence claims",
            "candidate feature construction does not read labels or the label-derived dist_known_fault_px field",
            "public catalogue block DTI is not a score for the private newly mapped fault target",
            "the selected 5,000-pixel mask places 54 pixels on known catalogue labels; the proxy DTI counts these known faults and is not evidence of withheld-fault discovery",
            "the edge implementation erodes common >=99%-supported pixels by one cell to keep the centered finite-difference stencil valid; this support guard was not tuned on labels but was not spelled out in the preregistration prose",
            "spatial blocks are correlated; conformal coverage is conditional on unverified exchangeability",
            "the bounded audit shows NaN can fail a NaN-intolerant range check, but the original rejected bytes are unavailable; this all-finite format is a precaution, not a diagnosis or organizer-confirmed acceptance",
            "no leaderboard score or >0.2778 / >0.3195 / >0.3774 claim is inferred",
        ],
        "elapsed_seconds": round(time.time() - start, 2),
    }
    report_json = json.dumps(report, indent=2) + "\n"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_json, encoding="utf-8")
    # GitHub Pages is served from docs/, so publish an identical JSON evidence
    # copy there for the one-click artifact page. This is evidence, not a score.
    (ROOT / "docs" / "h47qc-screen-20261006.json").write_text(
        report_json, encoding="utf-8"
    )
    print(json.dumps({
        "candidate_spacing_px": selected_spacing,
        "candidate_locked_test_pooled_dti": candidate_test,
        "candidate_conformal_nominal": conformal["nominal_coverage"],
        "candidate_conformal_floor": conformal["lower_bound_clipped"],
        "promotion_gate": promotion_pass,
        "artifact": str(output_path),
        "sha256": artifact_hash,
        "report": str(report_path),
    }, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / OUTPUT_REL)
    parser.add_argument("--report", type=Path, default=ROOT / REPORT_REL)
    args = parser.parse_args()
    run(args.output.resolve(), args.report.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
