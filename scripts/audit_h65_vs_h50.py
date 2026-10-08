#!/usr/bin/env python3
"""Matched corrected-domain H65 vs frozen H50 proxy reference (no tuning or slot use)."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src")]
import numpy as np

from gems47.conformal import simultaneous_lower_bounds

SPACINGS = (2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.6)
COVERAGE = 0.90


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        out = list(csv.DictReader(f))
    for row in out:
        row["block_id"] = int(row["block_id"])
        row["spacing_px"] = float(row["spacing_px"]) if row["spacing_px"] else None
        for k in ("TP_w", "FP_w", "FN_w", "DTI"):
            row[k] = float(row[k])
    return out


def blocks(rows: list[dict]) -> dict[int, str]:
    found = {}
    for r in rows:
        if r["instrument"] == "sgmc_offcat" and r["model"] in ("h50", "h65"):
            found[r["block_id"]] = r["role"]
    return found


def matrix(rows, model, role):
    index = {(r["model"], r["instrument"], r["role"], r["block_id"], r["spacing_px"]): r
             for r in rows}
    ids = sorted(i for i, role0 in blocks(rows).items() if role0 == role)
    return ids, np.asarray([[index[(model, "sgmc_offcat", role, i, s)]["DTI"]
                             for s in SPACINGS] for i in ids], float)


def pooled(rows, model, role, spacing):
    chosen = [r for r in rows if r["model"] == model and r["instrument"] == "sgmc_offcat"
              and r["role"] == role and r["spacing_px"] == spacing]
    tp, fp, fn = (sum(r[k] for r in chosen) for k in ("TP_w", "FP_w", "FN_w"))
    return float(tp / (tp + .2 * fp + .8 * fn + 1e-12))


def main() -> int:
    a_path = ROOT / "evidence/h65/spacing-history.csv"
    b_path = ROOT / "evidence/h60/corrected-domain/spacing-history.csv"
    a, b = read_rows(a_path), read_rows(b_path)
    if blocks(a) != blocks(b) or len(blocks(a)) != 41:
        raise AssertionError("H65/H50 roles or 41-block population differ")
    h65_screen = json.loads((ROOT / "evidence/h65/screen.json").read_text())
    h60_screen = json.loads((ROOT / "evidence/h60/corrected-domain/screen.json").read_text())
    d65 = float(h65_screen["models"]["h65"]["sgmc_offcat"]["selected_spacing_px"])
    d50 = float(h60_screen["arms"]["h50"]["selected_spacing_px"])
    selected_pair_index = SPACINGS.index(d65) * len(SPACINGS) + SPACINGS.index(d50)
    matrices = {}
    pairs = [(x, y) for x in SPACINGS for y in SPACINGS]
    for role in ("selection", "calibration"):
        ids_a, ma = matrix(a, "h65", role)
        ids_b, mb = matrix(b, "h50", role)
        if ids_a != ids_b:
            raise AssertionError(f"role block order differs for {role}")
        rows_a = {(r["model"], r["instrument"], r["role"], r["block_id"], r["spacing_px"]): r
                  for r in a}
        rows_b = {(r["model"], r["instrument"], r["role"], r["block_id"], r["spacing_px"]): r
                  for r in b}
        diffs = []
        for block_id in ids_a:
            row = []
            for x, y in pairs:
                diff = (rows_a[("h65", "sgmc_offcat", role, block_id, x)]["DTI"]
                        - rows_b[("h50", "sgmc_offcat", role, block_id, y)]["DTI"])
                if not -1.000000001 <= diff <= 1.000000001:
                    raise ValueError("DTI difference outside [-1,1]")
                row.append((diff + 1) / 2)
            diffs.append(row)
        matrices[role] = np.asarray(diffs, float)
    band = simultaneous_lower_bounds(matrices["selection"], matrices["calibration"],
                                     coverage=COVERAGE)
    lower = 2 * float(band["lower_bounds"][selected_pair_index]) - 1
    selected_diff = {
        role: float(2 * matrices[role][:, selected_pair_index].mean() - 1)
        for role in ("selection", "calibration")
    }
    h65_pooled = pooled(a, "h65", "selection", d65)
    h50_pooled = pooled(b, "h50", "selection", d50)
    out = {
        "status": "EXPLORATORY_CROSS_SCREEN_COMPARISON_NO_SLOT",
        "comparison": "H65 selected on SGMC selection means vs H50 selected on primary lappos means; both scored over full evaluated block domains",
        "h65_selected_spacing_px": d65, "h50_selected_spacing_px": d50,
        "selection_pooled_sgmc_dti": {"h65": h65_pooled, "h50": h50_pooled,
                                       "h65_minus_h50": h65_pooled - h50_pooled},
        "paired_selected_spacing_difference": selected_diff,
        "paired_simultaneous_lower_prediction_bound": lower,
        "nominal_coverage": COVERAGE,
        "rank_1_based": int(band["rank_1_based"]),
        "finite_sample_coverage_at_least_if_exchangeable": float(
            band["finite_sample_coverage_at_least_if_exchangeable"]),
        "all_49_spacing_pairs_jointly_bounded": True,
        "exchangeability_verified": False,
        "h65_reuses_previously_examined_blocks": True,
        "selection_blocks": int(band["n_selection"]),
        "calibration_blocks": int(band["n_calibration"]),
        "block_roles_match": True,
        "conformal_band": band,
        "source_sha256": {"h65_history": hashlib.sha256(a_path.read_bytes()).hexdigest(),
                           "corrected_h60_family_history": hashlib.sha256(b_path.read_bytes()).hexdigest()},
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope_limit": "public SGMC proxy only; no private leaderboard or full-map assurance; exploratory because H65 design followed earlier analyses on these blocks",
        "slot_used": False,
    }
    path = ROOT / "evidence/h65/corrected-h50-comparison.json"
    path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
