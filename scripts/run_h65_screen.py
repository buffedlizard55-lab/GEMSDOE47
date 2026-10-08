#!/usr/bin/env python3
"""Correct-domain rerun of H60 and preregistered H65.

Prediction eligibility and metric validity are deliberately separate: H60/H65 may
emit only inside their restricted LiDAR domain, but DTI is evaluated over every
known-fault-excluded footprint pixel in each frozen guarded block. The old H60
receipt/history are retained as historical artifacts and explicitly superseded.
No competition slot is used. Inputs are pinned owner mirrors, not organizer-authenticated.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
import numpy as np
import rasterio

from gems47 import grid as G
from gems47 import h50, h60, h65
from gems47.conformal import simultaneous_lower_bounds
from gems47s3.metric import dti, dti_binary
from gemsdoe47.magnetic import ranked_pixels

EV = ROOT / "evidence" / "h65"
SPACINGS = (2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.6)
BUDGET, NROWS, NCOLS, GUARD, SEED = 37_654, 8, 8, 3, 500610
COVERAGE = 0.90
PRIMARY, INDEPENDENT = "lappos_t200_d3", "sgmc_offcat"
MANIFEST_IDS = ("labels", "sample_submission", "ext_lidar_scarp_features_u8",
                "ext_derived_sgmc_faults_100m_u8", "ext_tiger_road_distance_m",
                "ext_blm_closed_claim_distance_m")
CODE_PATHS = ("scripts/run_h65_screen.py", "scripts/run_h60_screen.py",
              "src/gems47/h65.py", "src/gems47/h60.py", "src/gems47/h50.py",
              "src/gems47/conformal.py", "src/gems47s3/metric.py")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def verify_inputs(data: Path) -> dict:
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text())
    entries = {x["id"]: x for x in manifest["files"]}
    pins = {}
    for key in MANIFEST_IDS:
        item = entries[key]
        path = data / item["dest"]
        sha, nbytes = digest(path), path.stat().st_size
        if sha != item["sha256"] or nbytes != item["bytes"]:
            raise ValueError(f"manifest mismatch: {key} {sha} ({nbytes} bytes)")
        pins[key] = {"path": item["dest"], "sha256": sha, "bytes": nbytes,
                     "provenance": item.get("provenance", "")}
    return pins


def build_blocks(mask: np.ndarray) -> list[dict]:
    yr = np.linspace(0, mask.shape[0], NROWS + 1).astype(int)
    xr = np.linspace(0, mask.shape[1], NCOLS + 1).astype(int)
    blocks = []
    for row in range(NROWS):
        for col in range(NCOLS):
            y0, y1 = int(yr[row]) + GUARD, int(yr[row + 1]) - GUARD
            x0, x1 = int(xr[col]) + GUARD, int(xr[col + 1]) - GUARD
            if y1 <= y0 or x1 <= x0:
                raise ValueError("guard leaves an empty block")
            n = int(mask[y0:y1, x0:x1].sum())
            if n:
                blocks.append({"block_id": row * NCOLS + col, "row": row, "col": col,
                               "bounds_rc": [y0, y1, x0, x1], "evaluated_pixels": n})
    total = sum(b["evaluated_pixels"] for b in blocks)
    for b in blocks:
        b["budget"] = max(1, round(BUDGET * b["evaluated_pixels"] / total))
    order = np.random.default_rng(SEED).permutation(len(blocks))
    half = len(blocks) // 2
    for i in order[:half]:
        blocks[int(i)]["role"] = "selection"
    for i in order[half:]:
        blocks[int(i)]["role"] = "calibration"
    return blocks


def assert_frozen_blocks(blocks: list[dict]) -> None:
    # evidence/h60/blocks.json named in the preregistration is absent from this checkout.
    # H60's runner itself asserts against this H50 receipt, which is the frozen 41-block design.
    ref = json.loads((ROOT / "evidence/h50/blocks.json").read_text())["blocks"]
    if len(blocks) != len(ref):
        raise AssertionError(f"block count differs: {len(blocks)} vs frozen {len(ref)}")
    for actual, frozen in zip(blocks, ref):
        for key in ("block_id", "bounds_rc", "budget", "role"):
            if actual[key] != frozen[key]:
                raise AssertionError(f"frozen block mismatch ({key}): {actual} != {frozen}")


def emit_upto(field: np.ndarray, domain: np.ndarray, spacing: float, budget: int) -> np.ndarray:
    f = np.where(domain, np.nan_to_num(np.asarray(field, np.float32), nan=0.0), 0.0)
    order = ranked_pixels(f, domain)
    sel = h60._greedy_up_to(order, f.shape, spacing, int(budget))
    p = np.zeros(f.shape, np.float32)
    p.ravel()[sel] = 1.0
    return p


def metric(pred: np.ndarray, truth: np.ndarray, scoring_domain: np.ndarray,
           *, crosscheck: bool = False) -> dict:
    # All screen predictions are binary, so EDT evaluation is exact and much faster.
    r = dti_binary(pred, truth, valid=scoring_domain)
    if crosscheck:
        slow = dti(pred, truth, valid=scoring_domain)
        for k in ("tp", "fp", "fn", "dti"):
            if not np.isclose(r[k], slow[k], rtol=1e-11, atol=1e-11):
                raise AssertionError(f"binary DTI cross-check failed for {k}: {r[k]} != {slow[k]}")
    return {"TP_w": float(r["tp"]), "FP_w": float(r["fp"]),
            "FN_w": float(r["fn"]), "n_truth": int(r["n_truth"]),
            "DTI": float(r["dti"])}


def _matrix(rows, blocks, model, instrument, role):
    lookup = {(r["model"], r["instrument"], r["role"], r["block_id"], r["spacing_px"]): r
              for r in rows}
    return np.asarray([[float(lookup[(model, instrument, role, b["block_id"], s)]["DTI"])
                        for s in SPACINGS] for b in blocks if b["role"] == role], float)


def _pooled(rows, model, instrument, role, spacing):
    rs = [r for r in rows if r["model"] == model and r["instrument"] == instrument
          and r["role"] == role and r["spacing_px"] == spacing]
    tp, fp, fn = (sum(float(r[k]) for r in rs) for k in ("TP_w", "FP_w", "FN_w"))
    return {"pooled_dti": float(tp / (tp + .2 * fp + .8 * fn + 1e-12)),
            "mean_block_dti": float(np.mean([r["DTI"] for r in rs])),
            "blocks": len(rs), "TP_w": tp, "FP_w": fp, "FN_w": fn,
            "n_truth": sum(int(r["n_truth"]) for r in rs),
            "emitted": sum(int(r["emitted"]) for r in rs)}


def _summarize(rows, blocks, model, instrument):
    selection = _matrix(rows, blocks, model, instrument, "selection")
    calibration = _matrix(rows, blocks, model, instrument, "calibration")
    means = selection.mean(axis=0)
    index = max(range(len(SPACINGS)), key=lambda i: (float(means[i]), SPACINGS[i]))
    band = simultaneous_lower_bounds(selection, calibration, coverage=COVERAGE)
    spacing = SPACINGS[index]
    return {"selected_spacing_px": spacing,
            "selected_spacing_m": spacing * 100,
            "selection_mean_block_dti": float(means[index]),
            "selection_means_by_spacing": means.tolist(),
            "selected_lower_prediction_bound": float(band["lower_bounds"][index]),
            "nominal_coverage": float(band["nominal_coverage"]),
            "finite_sample_coverage_at_least_if_exchangeable": float(
                band["finite_sample_coverage_at_least_if_exchangeable"]),
            "calibration_n": int(band["n_calibration"]),
            "order_statistic_rank_1_based": int(band["rank_1_based"]),
            "selection_summary": _pooled(rows, model, instrument, "selection", spacing),
            "calibration_summary": _pooled(rows, model, instrument, "calibration", spacing),
            "conformal_band": band}


def _paired_difference(rows, blocks, h65_index, h60_index):
    lookup = {(r["model"], r["instrument"], r["role"], r["block_id"], r["spacing_px"]): float(r["DTI"])
              for r in rows}
    # Make all 7x7 H65-minus-H60 contrasts simultaneous, so the selection-half
    # choice of two spacings is covered by the joint band. Affine-map [-1,1] to
    # [0,1] because the shared conformal implementation validates DTI-like scores.
    matrices = {}
    pairs = [(a, b) for a in SPACINGS for b in SPACINGS]
    for role in ("selection", "calibration"):
        vals = []
        for block in blocks:
            if block["role"] != role:
                continue
            row = []
            for a, b in pairs:
                diff = (lookup[("h65", INDEPENDENT, role, block["block_id"], a)]
                        - lookup[("h60", INDEPENDENT, role, block["block_id"], b)])
                if not -1.000000001 <= diff <= 1.000000001:
                    raise ValueError("paired DTI difference outside [-1,1]")
                row.append((diff + 1.0) * 0.5)
            vals.append(row)
        matrices[role] = np.asarray(vals, dtype=float)
    band = simultaneous_lower_bounds(matrices["selection"], matrices["calibration"],
                                     coverage=COVERAGE)
    chosen = SPACINGS.index(SPACINGS[h65_index]) * len(SPACINGS) + SPACINGS.index(SPACINGS[h60_index])
    # Returned lower bands are clipped to [0,1]; mapping back remains conservative.
    lower = 2.0 * float(band["lower_bounds"][chosen]) - 1.0
    return {"target": "one future block's paired H65-minus-H60 SGMC-proxy DTI",
            "h65_spacing_px": SPACINGS[h65_index], "h60_spacing_px": SPACINGS[h60_index],
            "selection_mean_difference": float(2 * matrices["selection"][:, chosen].mean() - 1),
            "calibration_mean_difference": float(2 * matrices["calibration"][:, chosen].mean() - 1),
            "lower_prediction_bound": lower,
            "nominal_coverage": float(band["nominal_coverage"]),
            "finite_sample_coverage_at_least_if_exchangeable": float(
                band["finite_sample_coverage_at_least_if_exchangeable"]),
            "calibration_n": int(band["n_calibration"]),
            "order_statistic_rank_1_based": int(band["rank_1_based"]),
            "all_spacing_pairs_simultaneous": True,
            "exchangeability_verified": False,
            "band_on_affine_transformed_difference": band}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    for name in ("screen.json", "spacing-history.csv", "blocks.json"):
        if (EV / name).exists() and not args.overwrite:
            raise SystemExit(f"{EV / name} exists; pass --overwrite to replace")
    started = time.time()
    data = G.data_dir()
    pins = verify_inputs(data)
    grids = h60.read_grid(data)
    evaluated = grids["evaluated"]
    blocks = build_blocks(evaluated)
    assert_frozen_blocks(blocks)
    print(f"[blocks] exact H50/H60 frozen roles: {len(blocks)} blocks; "
          f"{sum(b['role']=='selection' for b in blocks)} selection / "
          f"{sum(b['role']=='calibration' for b in blocks)} calibration", flush=True)

    emission = h60.h60_emission_domain(data)
    field60 = h60.h60_field(data, emission)
    field65 = h65.paired_morphology_field(data, emission)
    with rasterio.open(data / "external/lidar_scarp_features_u8.tif") as src:
        names = list(src.descriptions)
        lappos = src.read(names.index("lappos_max") + 1).astype(np.float32)
        lidar_valid = src.read(names.index("valid") + 1) > 0
    lappos_truth = h50.lidar_peaks(lappos, lidar_valid, threshold=200, min_distance=3)
    lappos_truth &= evaluated
    del lappos, lidar_valid
    sgmc_truth = h50.instrument_sgmc_offcatalogue(data) & evaluated
    instruments = {PRIMARY: lappos_truth, INDEPENDENT: sgmc_truth}
    print(f"[masks] scoring={int(evaluated.sum()):,}; emission={int(emission.sum()):,}; "
          f"primary_proxy={int(lappos_truth.sum()):,}; sgmc_proxy={int(sgmc_truth.sum()):,}",
          flush=True)

    rows, checked = [], set()
    t0 = time.time()
    for block in blocks:
        y0, y1, x0, x1 = block["bounds_rc"]
        sy, sx = slice(y0, y1), slice(x0, x1)
        score_domain = evaluated[sy, sx]
        h60_domain = emission[sy, sx]
        rng = np.random.default_rng(SEED + block["block_id"])
        random_field = rng.random(score_domain.shape, dtype=np.float32)
        fields = {"h60": field60[sy, sx], "h65": field65[sy, sx], "random": random_field}
        for model, field in fields.items():
            emit_domain = score_domain if model == "random" else h60_domain
            for spacing in SPACINGS:
                pred = emit_upto(field, emit_domain, spacing, block["budget"])
                for instrument, truth_full in instruments.items():
                    check = (model, instrument) not in checked
                    scores = metric(pred, truth_full[sy, sx], score_domain, crosscheck=check)
                    checked.add((model, instrument))
                    rows.append({"role": block["role"], "block_id": block["block_id"],
                                 "model": model, "spacing_px": float(spacing),
                                 "instrument": instrument, "emitted": int(pred.sum()),
                                 "emission_domain_pixels": int(emit_domain.sum()),
                                 "scoring_domain_pixels": int(score_domain.sum()), **scores})
        print(f"[block {block['block_id']:2d}] {block['role']:11s} "
              f"budget={block['budget']:5d}; rows={len(rows):4d}; "
              f"{time.time()-t0:.0f}s", flush=True)

    EV.mkdir(parents=True, exist_ok=True)
    history = EV / "spacing-history.csv"
    with history.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    save_json(EV / "blocks.json", {"source": "evidence/h50/blocks.json (H60 runner's asserted frozen reference)",
                                   "guard_px": GUARD, "blocks": blocks})

    summaries = {model: {instrument: _summarize(rows, blocks, model, instrument)
                         for instrument in (PRIMARY, INDEPENDENT)}
                 for model in ("h60", "h65")}
    h60_idx = SPACINGS.index(summaries["h60"][INDEPENDENT]["selected_spacing_px"])
    h65_idx = SPACINGS.index(summaries["h65"][INDEPENDENT]["selected_spacing_px"])
    paired = _paired_difference(rows, blocks, h65_idx, h60_idx)
    h60_pooled = summaries["h60"][INDEPENDENT]["selection_summary"]["pooled_dti"]
    h65_pooled = summaries["h65"][INDEPENDENT]["selection_summary"]["pooled_dti"]
    random_control = _pooled(rows, "random", INDEPENDENT, "selection", SPACINGS[h65_idx])
    gates = {
        "h65_selected_spacing_beats_h60_on_pooled_selection_sgmc": h65_pooled > h60_pooled,
        "all_spacing_pairs_paired_sgmc_lower_bound_positive": paired["lower_prediction_bound"] > 0,
    }
    promoted = all(gates.values())
    summary = {
        "schema_version": 1,
        "status": "EXPLORATORY_SCREEN_NO_SUBMISSION_SLOT_USED",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "preregistration": "docs/research/h65-hypotheses-preregistered-20261008.md",
        "benchmark": "H60 recomputed with correct full evaluation-domain DTI mask; old H60 artifacts remain historical",
        "design": {
            "blocks": "41 contiguous spatial blocks from frozen 8x8 design, 3 px guards",
            "selection_blocks": sum(b["role"] == "selection" for b in blocks),
            "calibration_blocks": sum(b["role"] == "calibration" for b in blocks),
            "roles_and_budgets_asserted_against": "evidence/h50/blocks.json",
            "spacing_px": list(SPACINGS), "nominal_coverage": COVERAGE,
            "finite_sample_rank": "ceil((n_cal+1)*0.90)=20 of 21 calibration residuals",
            "selection_rule": "highest selection-half mean block DTI; tie -> larger spacing",
            "budget_whole_map": BUDGET,
            "emission": "greedy ranked pixels, Euclidean minimum spacing, capped if a restricted domain cannot fit budget",
            "scoring": "DTI over every evaluated pixel in each guarded block; never masked by method-specific emission domain",
        },
        "domain_counts": {"evaluated_pixels": int(evaluated.sum()),
                           "h60_h65_emission_pixels": int(emission.sum()),
                           "primary_proxy_pixels": int(lappos_truth.sum()),
                           "sgmc_proxy_pixels": int(sgmc_truth.sum())},
        "models": summaries,
        "paired_h65_minus_h60_sgmc": paired,
        "mass_matched_random_control_at_h65_selected_spacing": random_control,
        "promotion_gate": {"criteria": gates, "all_passed": promoted,
                           "decision": "LOCAL_PROXY_ONLY_REQUIRES_FRESH_CONFIRMATION" if promoted
                                       else "NOT_PROMOTED; retain corrected H60 as local proxy anchor",
                           "submission_authorized": False, "slot_used": False},
        "scoring_domain_correction": {
            "issue": "The old scripts/run_h60_screen.py passed each arm's restricted emission mask as the DTI valid mask. That removed proxy-truth cells outside the emission domain and failed to count those false negatives.",
            "impact": "Historical evidence/h60/screen.json, spacing-history.csv, selected-spacing floors, and H60-family rankings are emission-scoped and must not be described as full evaluated-map or official-metric assurance.",
            "preservation": "Historical files are unchanged; this screen is a new corrected-domain H60/H65 comparison.",
            "correction": "The runner now passes the full evaluated mask independently of the emitter mask and records both domain sizes.",
        },
        "conformal_scope": {
            "rank": "k=ceil((21+1)*0.90)=20; finite-sample marginal level is at least 20/22 = 90.91% if block score vectors and one future block are exchangeable.",
            "target": "one future guarded block's public-proxy DTI (or paired SGMC difference), not a mean, whole-map DTI, leaderboard score, private labels, or Phase 2 outcome",
            "assumptions": "spatial blocking does not prove geological block exchangeability; H65 reuses blocks already examined in prior repository work, so H65 is exploratory and not a fresh confirmatory guarantee",
            "floor_location": "models.{h60,h65}.{sgmc_offcat,lappos_t200_d3}.selected_lower_prediction_bound; paired_h65_minus_h60_sgmc.lower_prediction_bound",
        },
        "block_reference_irregularity": "The H65 preregistration cites evidence/h60/blocks.json, but that file is absent in this checkout. H60's own runner re-derives and asserts its frozen blocks against evidence/h50/blocks.json; this rerun uses that same H50 receipt and verifies all roles/budgets before scoring.",
        "input_pins": pins,
        "code_sha256": {p: digest(ROOT / p) for p in CODE_PATHS},
        "spacing_history_sha256": digest(history),
        "metric_source": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric",
        "limitations": [
            "Inputs are owner-mirrored and hash-pinned; not organizer-authenticated bytes.",
            "The primary lappos peak proxy shares the owner-derived LiDAR modality with both fields and is circular/optimistic.",
            "SGMC off-catalogue is a public geological-map proxy, not hidden competition truth; geological contact bias remains.",
            "The corrected H60/H65 block comparisons are not scores on the competition leaderboard and do not validate the user-reported 0.3774 target.",
            "No TIFF, portal upload, private-label query, weekly slot use, or final selection occurred.",
        ],
        "elapsed_seconds": round(time.time() - started, 2),
    }
    save_json(EV / "screen.json", summary)
    print(json.dumps({"selected": {m: {"sgmc_spacing_px": summaries[m][INDEPENDENT]["selected_spacing_px"],
                                          "sgmc_pooled_selection_dti": summaries[m][INDEPENDENT]["selection_summary"]["pooled_dti"],
                                          "sgmc_floor": summaries[m][INDEPENDENT]["selected_lower_prediction_bound"],
                                          "lappos_spacing_px": summaries[m][PRIMARY]["selected_spacing_px"],
                                          "lappos_floor": summaries[m][PRIMARY]["selected_lower_prediction_bound"]}
                                  for m in ("h60", "h65")},
                      "paired_sgmc_lower_bound": paired["lower_prediction_bound"],
                      "gate": gates, "h65_promotion": summary["promotion_gate"]["decision"],
                      "elapsed_seconds": summary["elapsed_seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
