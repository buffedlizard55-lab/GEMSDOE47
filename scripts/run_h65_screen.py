#!/usr/bin/env python3
"""Run the preregistered H65 sub-2-pixel spacing extension.

Protocol: docs/research/h65-h68-hypotheses-preregistered.md at commit b73bb647.
This script does not upload anything or read private competition labels.
"""
from __future__ import annotations

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

from gems47 import grid as G
from gems47 import h50, h60
from gems47.conformal import simultaneous_lower_bounds
from gems47s3.metric import dti
from gemsdoe47.magnetic import ranked_pixels

EV = ROOT / "evidence" / "h65"
SPACINGS = (1.4, 1.6, 1.8, 2.0, 2.2, 2.4)
COVERAGE = 0.90
PRIMARY = "lappos_t200_d3"
INSTRUMENTS = {
    "lappos_t200_d3": ("lappos_max", 200, 3),
    "lapneg_t200_d3": ("lapneg_max", 200, 3),
    "step_t150_d3": ("step_max", 150, 3),
    "cross_t200_d3": ("cross_max", 200, 3),
    "upface_t200_d3": ("upface_max", 200, 3),
    "union_t200_d3": ("union", 200, 3),
}
H60_FROZEN = {
    "selection_mean": 0.2843788083499138,
    "pooled_primary_selection": 0.2878910923835811,
    "pooled_sgmc_selection": 0.19381303648178833,
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _emit_upto(field: np.ndarray, valid: np.ndarray, spacing: float, budget: int) -> np.ndarray:
    f = np.where(valid, np.nan_to_num(field, nan=0.0), 0.0).astype(np.float32)
    out = np.zeros(f.shape, np.float32)
    order = ranked_pixels(f, valid)
    if order.size:
        out.ravel()[h60._greedy_up_to(order, f.shape, spacing, budget)] = 1.0
    return out


def _score(pred: np.ndarray, truth: np.ndarray, valid: np.ndarray) -> dict:
    result = dti(pred, truth.astype(np.int8), valid=valid)
    return {"TP_w": result["tp"], "FP_w": result["fp"], "FN_w": result["fn"],
            "|G|": result["n_truth"], "S": result["S"], "Phi": result["M"],
            "DTI": result["dti"]}


def main() -> int:
    started = time.time()
    data = G.data_dir()
    grids = h60.read_grid(data)
    evaluated = grids["evaluated"]

    # Reuse code-reviewed block construction and assert every frozen attribute.
    from scripts.run_h60_screen import build_blocks
    blocks = build_blocks(evaluated)
    frozen = json.loads((ROOT / "evidence/h50/blocks.json").read_text())["blocks"]
    assert len(blocks) == len(frozen) == 41
    for got, expected in zip(blocks, frozen):
        for key in ("block_id", "bounds_rc", "budget", "role"):
            assert got[key] == expected[key], (key, got[key], expected[key])

    domain = h60.h60_emission_domain(data)
    field = h60.h60_field(data, domain)
    channels = h50.lidar_scarp_channels(data)
    lidar_valid = channels["valid"] > 0
    instruments = {}
    for name, (channel, threshold, min_distance) in INSTRUMENTS.items():
        if channel == "union":
            mask = np.zeros(evaluated.shape, bool)
            for channel_name in h50.LIDAR_SCARP_CHANNELS:
                mask |= h50.lidar_peaks(channels[channel_name], lidar_valid,
                                        threshold, min_distance)
        else:
            mask = h50.lidar_peaks(channels[channel], lidar_valid,
                                   threshold, min_distance)
        instruments[name] = mask & evaluated
    del channels, lidar_valid
    instruments["sgmc_offcat"] = h50.instrument_sgmc_offcatalogue(data) & evaluated

    rows = []
    for block in blocks:
        y0, y1, x0, x1 = block["bounds_rc"]
        sy, sx = slice(y0, y1), slice(x0, x1)
        valid = domain[sy, sx]
        local_field = field[sy, sx]
        for spacing in SPACINGS:
            pred = _emit_upto(local_field, valid, spacing, block["budget"])
            emitted = int(pred.sum())
            for instrument, truth in instruments.items():
                rows.append({"role": block["role"], "block_id": block["block_id"],
                             "model": "h65", "spacing_px": spacing,
                             "instrument": instrument, "emitted": emitted,
                             **_score(pred, truth[sy, sx], valid)})
        print(f"[h65 block {block['block_id']:2d}] {block['role']:11s} "
              f"budget={block['budget']:4d}", flush=True)

    EV.mkdir(parents=True, exist_ok=True)
    history = EV / "spacing-history.csv"
    with history.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    def matrix(instrument: str, role: str) -> np.ndarray:
        selected_blocks = [b for b in blocks if b["role"] == role]
        return np.array([[next(float(r["DTI"]) for r in rows
                               if r["block_id"] == b["block_id"]
                               and r["role"] == role
                               and r["instrument"] == instrument
                               and r["spacing_px"] == spacing)
                          for spacing in SPACINGS] for b in selected_blocks])

    def pooled(instrument: str, role: str, spacing: float) -> float:
        chosen = [r for r in rows if r["instrument"] == instrument
                  and r["role"] == role and r["spacing_px"] == spacing]
        tp = sum(float(r["TP_w"]) for r in chosen)
        fp = sum(float(r["FP_w"]) for r in chosen)
        truth = sum(float(r["|G|"]) for r in chosen)
        denominator = tp + 0.2 * fp + 0.8 * truth
        return tp / denominator if denominator else 0.0

    selection = matrix(PRIMARY, "selection")
    calibration = matrix(PRIMARY, "calibration")
    means = selection.mean(axis=0)
    chosen_index = max(range(len(SPACINGS)), key=lambda i: (float(means[i]), SPACINGS[i]))
    chosen = SPACINGS[chosen_index]
    band = simultaneous_lower_bounds(selection, calibration, coverage=COVERAGE)
    emitted = sum(int(r["emitted"]) for r in rows
                  if r["role"] == "selection" and r["spacing_px"] == chosen
                  and r["instrument"] == PRIMARY)
    measured = {
        "selected_spacing_px": chosen,
        "selection_mean": float(means[chosen_index]),
        "selection_means": [float(value) for value in means],
        "pooled_primary_selection": pooled(PRIMARY, "selection", chosen),
        "pooled_primary_calibration": pooled(PRIMARY, "calibration", chosen),
        "pooled_sgmc_selection": pooled("sgmc_offcat", "selection", chosen),
        "secondary_selection": {name: pooled(name, "selection", chosen)
                                for name in INSTRUMENTS},
        "emitted_mass_selection_half": emitted,
        "conformal": {
            "floor": float(band["lower_bounds"][chosen_index]),
            "rank_1_based": int(band["rank_1_based"]),
            "coverage_at_least": float(
                band["finite_sample_coverage_at_least_if_exchangeable"]),
            "band": band,
        },
    }
    conditions = {
        "selected_spacing_below_2px": chosen < 2.0,
        "pooled_primary_strictly_beats_h60": measured["pooled_primary_selection"]
                                               > H60_FROZEN["pooled_primary_selection"],
        "mean_primary_strictly_beats_h60": measured["selection_mean"]
                                             > H60_FROZEN["selection_mean"],
        "positive_conformal_floor": measured["conformal"]["floor"] > 0.0,
        "sgmc_noninferior_to_h60": measured["pooled_sgmc_selection"]
                                     >= H60_FROZEN["pooled_sgmc_selection"],
    }
    summary = {
        "schema_version": 1,
        "hypothesis_id": "H65",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "PASSED_PREBUILD_GATE" if all(conditions.values()) else "FAILED_GATE_NO_BUILD",
        "preregistration": "docs/research/h65-h68-hypotheses-preregistered.md",
        "preregistration_commit": "b73bb647916090a1493d6679ffb0cfe92b835d04",
        "design": {"blocks": 41, "selection_blocks": 20, "calibration_blocks": 21,
                   "guard_px": 3, "spacings_px": list(SPACINGS), "budget": 37654,
                   "coverage": COVERAGE, "primary_instrument": PRIMARY,
                   "independent_instrument": "sgmc_offcat",
                   "emission_domain_pixels": int(domain.sum())},
        "h60_frozen_comparator": H60_FROZEN,
        "measured": measured,
        "gate": {"conditions": conditions, "passed_prebuild": all(conditions.values()),
                 "format_and_uniqueness_pending": all(conditions.values())},
        "instrument_truth_pixels": {name: int(mask.sum())
                                    for name, mask in instruments.items()},
        "spacing_history_sha256": digest(history),
        "code_sha256": digest(Path(__file__)),
        "limitations": [
            "The primary instrument and prediction field share the owner-derived lidar stack, so the primary score is optimistic.",
            "The SGMC population is independent of the prediction field but is still a proxy, not private truth.",
            "The conformal statement assumes exchangeable block-score vectors; spatial blocking does not prove exchangeability.",
            "Coverage is marginal for one future proxy block, not a pooled map or leaderboard score.",
            "No competition slot was spent and no private label was read.",
        ],
        "elapsed_seconds": round(time.time() - started, 2),
    }
    (EV / "screen.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": summary["status"], "measured": measured,
                      "conditions": conditions}, indent=2)[:12000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
