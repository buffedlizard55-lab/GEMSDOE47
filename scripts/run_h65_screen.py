#!/usr/bin/env python3
"""H65-H68 spatially-blocked holdout screen with split-conformal operating-point selection.

Frozen design (docs/research/h65-hypotheses-preregistered.md, committed before any
score in this round was computed):

* **Blocks.**  The exact 41 blocks, guards, budgets and roles of the H50/H60 screens
  are re-derived with the same seed (500610) and asserted equal to
  ``evidence/h50/blocks.json`` before anything is scored.
* **Arms.**  ``h65`` (scarp-consensus field), ``h66`` (far-field lidar field),
  ``h67`` (alteration-corroborated lidar field), ``h68`` (extended-channel lidar
  field).  Anchors: ``h50`` and ``h60`` (frozen definitions, reproduced).  Controls:
  the mass-matched random control, the owner-reported d2.8 reference and H47-C1.
* **Instruments.**  Primary ``lappos_t200_d3`` (frozen); the frozen seven lidar-peak
  instruments plus the independent SGMC off-catalogue population.
* **Conformal operating-point rule (this round's methodological change).**  Per arm,
  max-over-settings one-sided split conformal at 0.90
  (``gems47.conformal.simultaneous_lower_bounds``, Lei et al. JASA 2018 Algorithm 2):
  the selection half centers the band, the disjoint calibration half certifies it, and
  the operating point is ``choose_operating_point`` -- the spacing with the greatest
  CERTIFIED LOWER BOUND (the guaranteed floor), not the greatest observed mean.  The
  reported confidence level is k/(n+1) = 20/22 >= 90.909 %.
* **Gate.**  The preregistered six-condition promotion gate, including
  ``beats_incumbent_h60`` (both pooled selection-half DTIs above H60's frozen
  0.287891 / 0.193813).  No gate here authorises an upload; it only decides whether an
  artefact is *built* for the owner's judgement.

This screen spends no competition submission slot and reads no private label.
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
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np
import rasterio

from gems47 import grid as G
from gems47 import h50, h60, h65
from gems47.conformal import choose_operating_point, simultaneous_lower_bounds

EV = ROOT / "evidence" / "h65"
SPACINGS = (2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.6)
BUDGET = 37_654
NROWS = NCOLS = 8
GUARD_PX = 3
SEED = 500610
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
ARMS = ("h65", "h66", "h67", "h68")
ANCHORS = ("h50", "h60")
CODE_PATHS = ("scripts/run_h65_screen.py", "src/gems47/h65.py", "src/gems47/h60.py",
              "src/gems47/h50.py", "src/gems47/conformal.py", "src/gems47s3/geomorph.py")

#: frozen incumbent values from the H60 screen (asserted against the receipt)
H60_FROZEN_PRIMARY = 0.287891
H60_FROZEN_SGMC = 0.193813
H50_FROZEN_PRIMARY = 0.165881


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(path: Path, values: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(values, indent=2, allow_nan=False) + "\n")


def build_blocks(mask: np.ndarray) -> list[dict]:
    """Identical construction to scripts/run_h60_screen.py::build_blocks."""
    yr = np.linspace(0, mask.shape[0], NROWS + 1).astype(int)
    xr = np.linspace(0, mask.shape[1], NCOLS + 1).astype(int)
    blocks = []
    for row in range(NROWS):
        for col in range(NCOLS):
            y0, y1 = int(yr[row]) + GUARD_PX, int(yr[row + 1]) - GUARD_PX
            x0, x1 = int(xr[col]) + GUARD_PX, int(xr[col + 1]) - GUARD_PX
            if y1 <= y0 or x1 <= x0:
                raise ValueError("guard leaves an empty block")
            core = mask[y0:y1, x0:x1]
            if not core.any():
                continue
            blocks.append(dict(block_id=row * NCOLS + col, row=row, col=col,
                               bounds_rc=[y0, y1, x0, x1], evaluated_pixels=int(core.sum())))
    total = sum(b["evaluated_pixels"] for b in blocks)
    if not blocks or total <= 0:
        raise ValueError("no evaluated pixels")
    for b in blocks:
        b["budget"] = max(1, round(BUDGET * b["evaluated_pixels"] / total))
    permutation = np.random.default_rng(SEED).permutation(len(blocks))
    half = len(blocks) // 2
    for i in permutation[:half]:
        blocks[int(i)]["role"] = "selection"
    for i in permutation[half:]:
        blocks[int(i)]["role"] = "calibration"
    return blocks


def _score(p: np.ndarray, truth: np.ndarray, valid: np.ndarray) -> dict:
    from gems47s3.metric import dti
    r = dti(p, truth.astype(np.int8), valid=valid)
    return {"TP_w": r["tp"], "FP_w": r["fp"], "FN_w": r["fn"], "|G|": r["n_truth"],
            "S": r["S"], "Phi": r["M"], "DTI": r["dti"]}


def _emit_upto(field: np.ndarray, valid: np.ndarray, spacing_px: float,
               budget: int) -> np.ndarray:
    """Greedy spaced emission capped at what the valid domain can hold.

    The noise-masked lidar domains are fragmented and cannot always hold the full
    block budget at small spacings; under-emission is the hypothesis's own bet and is
    reported, not hidden (session-5 deviation IR-2026-10-07-D): the ``emitted`` column
    of every row carries the actual mass.
    """
    from gemsdoe47.magnetic import ranked_pixels
    f = np.where(valid, np.nan_to_num(np.asarray(field, np.float32), nan=0.0), 0.0)
    p = np.zeros(f.shape, np.float32)
    order = ranked_pixels(f, valid)
    if order.size == 0:
        return p
    sel = h60._greedy_up_to(order, f.shape, spacing_px, budget)
    p.ravel()[sel] = 1.0
    return p


def main() -> int:
    started = time.time()
    data = G.data_dir()
    grids = h60.read_grid(data)
    mask = grids["evaluated"]

    # ---- frozen blocks: re-derive and assert equality with the H50 screen receipt
    blocks = build_blocks(mask)
    ref = json.loads((ROOT / "evidence" / "h50" / "blocks.json").read_text())
    assert len(blocks) == len(ref["blocks"]), "block count differs from frozen H50 blocks"
    for b, r in zip(blocks, ref["blocks"]):
        assert (b["block_id"] == r["block_id"] and b["bounds_rc"] == r["bounds_rc"]
                and b["budget"] == r["budget"] and b["role"] == r["role"]), \
            f"block mismatch vs frozen H50 blocks: {b} vs {r}"
    print(f"[blocks] {len(blocks)} blocks, roles/budgets byte-equal to the frozen H50 screen",
          flush=True)

    # ---- incumbent values: assert the frozen H60 receipt before using them in the gate
    h60_screen = json.loads((ROOT / "evidence" / "h60" / "screen.json").read_text())
    h60_arm = h60_screen["arms"]["h60"]
    h50_arm = h60_screen["arms"]["h50"]
    assert abs(h60_arm["pooled_primary_selection"] - H60_FROZEN_PRIMARY) < 1e-6, \
        "frozen H60 primary drifted"
    assert abs(h60_arm["pooled_sgmc_selection"] - H60_FROZEN_SGMC) < 1e-6, \
        "frozen H60 sgmc drifted"
    assert abs(h50_arm["pooled_primary_selection"] - H50_FROZEN_PRIMARY) < 1e-6, \
        "frozen H50 primary drifted"
    print("[incumbent] frozen H60 0.287891/0.193813 and H50 0.165881 asserted", flush=True)

    # ---- fields (all frozen definitions; see src/gems47/h65.py and h60.py)
    built = h65.build_all(data)
    fields: dict[str, np.ndarray] = {
        "h50": h60.h50_field(data, mask),
        "h60": h60.h60_field(data, h60.h60_emission_domain(data)),
        "h65": built["h65"]["field"],
        "h66": built["h66"]["field"],
        "h67": built["h67"]["field"],
        "h68": built["h68"]["field"],
    }
    arm_domain = {
        "h50": mask,
        "h60": h60.h60_emission_domain(data),
        "h65": built["h65"]["mask"],
        "h66": built["h66"]["mask"],
        "h67": built["h67"]["mask"],
        "h68": built["h68"]["mask"],
    }
    print(f"[fields] built ({time.time()-started:.0f}s); domains "
          + " ".join(f"{a}={int(d.sum())}" for a, d in arm_domain.items())
          + f"; consensus counts {built['h65']['counts']}", flush=True)

    # ---- instruments (frozen set of the H50/H60 screens)
    ch = h50.lidar_scarp_channels(data)
    valid_lidar = ch["valid"] > 0
    instruments = {}
    for iname, (chan, thr, md) in INSTRUMENTS.items():
        if chan == "union":
            m = np.zeros(mask.shape, bool)
            for nm in h50.LIDAR_SCARP_CHANNELS:
                m |= h50.lidar_peaks(ch[nm], valid_lidar, thr, md)
        else:
            m = h50.lidar_peaks(ch[chan], valid_lidar, thr, md)
        m &= grids["footprint"] & ~grids["catalogue"]
        instruments[iname] = m & mask
    del ch, valid_lidar
    sgmc = h50.instrument_sgmc_offcatalogue(data) & mask
    print("[instr] " + " ".join(f"{k}={int(v.sum())}" for k, v in instruments.items())
          + f" sgmc={int(sgmc.sum())}", flush=True)

    # ---- raster controls
    with rasterio.open(data / "reference" / "h33-2-b2-zeros.tif") as src:
        d28 = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0) > 0
    c1_path = ROOT / "docs" / "downloads" / \
        "gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif"
    with rasterio.open(c1_path) as src:
        c1 = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0) > 0

    rows: list[dict] = []
    t0 = time.time()
    for b in blocks:
        y0, y1, x0, x1 = b["bounds_rc"]
        sy, sx = slice(y0, y1), slice(x0, x1)
        rng = np.random.default_rng(SEED + b["block_id"])
        random_field = rng.random(mask[sy, sx].shape, dtype=np.float32)

        def record(model, spacing, p, valid_crop, _b=b, _sy=sy, _sx=sx):
            for iname, ifull in {**instruments, "sgmc_offcat": sgmc}.items():
                r = _score(p, ifull[_sy, _sx], valid_crop)
                rows.append(dict(role=_b["role"], block_id=_b["block_id"], model=model,
                                 spacing_px=spacing, instrument=iname,
                                 emitted=int(p.sum()), **r))

        for arm in ARMS + ANCHORS:
            valid_crop = arm_domain[arm][sy, sx]
            fld = fields[arm][sy, sx]
            budget = b["budget"]
            for spacing in SPACINGS:
                if arm == "h50":
                    p = h50.emit(fld, valid_crop, spacing, budget)
                else:
                    # the noise-masked lidar domains are fragmented and cannot always
                    # hold the full block budget at small spacings; emission is capped
                    # at the domain capacity and the actual mass is recorded
                    p = _emit_upto(fld, valid_crop, spacing, budget)
                record(arm, spacing, p, valid_crop)
        # mass-matched random control (same emitter/spacings/budget on the plain domain)
        for spacing in SPACINGS:
            p = h50.emit(random_field, mask[sy, sx], spacing, b["budget"])
            record("random", spacing, p, mask[sy, sx])
        # raster controls at their own emission
        for name, fld in (("h33_reference", d28), ("h47c1", c1)):
            p = fld[sy, sx].astype(np.float32)
            if float(p.sum()) <= 0:
                continue
            record(name, None, p, mask[sy, sx])
        print(f"[block {b['block_id']:2d}] {b['role']:11s} budget={b['budget']:5d} "
              f"rows={len(rows)} ({time.time()-t0:.0f}s)", flush=True)

    history = EV / "spacing-history.csv"
    EV.mkdir(parents=True, exist_ok=True)
    with history.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # ---- conformal operating-point selection per arm ---------------------------
    def matrix(model, instrument, role):
        return np.array([[ _row(rows, model, instrument, role, b["block_id"], s)
                           for s in SPACINGS]
                         for b in blocks if b["role"] == role], dtype=np.float64)

    def _row(rs, model, instrument, role, block_id, spacing):
        for r in rs:
            if (r["model"] == model and r["instrument"] == instrument
                    and r["role"] == role and r["block_id"] == block_id
                    and r["spacing_px"] == spacing):
                return float(r["DTI"])
        raise ValueError(f"missing row {model} {instrument} {role} {block_id} {spacing}")

    def pooled(model, instrument, role, spacing_value=None):
        rs = [r for r in rows if r["role"] == role and r["model"] == model
              and r["instrument"] == instrument
              and (spacing_value is None or r["spacing_px"] == spacing_value)]
        if not rs:
            return 0.0, 0
        T = sum(r["TP_w"] for r in rs)
        F = sum(r["FP_w"] for r in rs)
        K = sum(r["|G|"] for r in rs)
        den = T + 0.2 * F + 0.8 * K
        return (float(T / den) if den > 0 else 0.0), len(rs)

    arms_out = {}
    for arm in ARMS + ANCHORS:
        sel = matrix(arm, PRIMARY, "selection")
        cal = matrix(arm, PRIMARY, "calibration")
        band = simultaneous_lower_bounds(sel, cal, coverage=COVERAGE)
        # the operating point is the spacing with the greatest CERTIFIED floor
        chosen = choose_operating_point(band, SPACINGS)
        spacing_chosen = float(SPACINGS[chosen])
        sgmc_sel, _ = pooled(arm, "sgmc_offcat", "selection", spacing_chosen)
        emitted_sel = sum(int(r["emitted"]) for r in rows
                          if r["role"] == "selection" and r["model"] == arm
                          and r["spacing_px"] == spacing_chosen
                          and r["instrument"] == PRIMARY) // (len(instruments) + 1)
        arms_out[arm] = dict(
            selected_spacing_px=spacing_chosen,
            selection_rule="argmax certified conformal lower bound (guaranteed floor)",
            selection_mean=float(sel.mean(axis=0)[chosen]),
            selection_means=[float(v) for v in sel.mean(axis=0)],
            emitted_mass_selection_half=emitted_sel,
            pooled_primary_selection=pooled(arm, PRIMARY, "selection", spacing_chosen)[0],
            pooled_primary_calibration=pooled(arm, PRIMARY, "calibration",
                                              spacing_chosen)[0],
            pooled_sgmc_selection=sgmc_sel,
            secondary_selection={iname: pooled(arm, iname, "selection",
                                               spacing_chosen)[0] for iname in instruments},
            conformal=dict(floor=float(band["lower_bounds"][chosen]),
                           rank_1_based=int(band["rank_1_based"]),
                           coverage_at_least=float(
                               band["finite_sample_coverage_at_least_if_exchangeable"]),
                           n_selection=int(band["n_selection"]),
                           n_calibration=int(band["n_calibration"]),
                           lower_bounds=[float(v) for v in band["lower_bounds"]],
                           selection_centers=[float(v) for v in band["selection_centers"]],
                           band=band),
        )

    # controls at each arm's selected spacing (random is spacing-matched per arm)
    controls = {}
    for arm in ARMS + ANCHORS:
        sp = arms_out[arm]["selected_spacing_px"]
        controls[arm] = {
            "random": dict(primary=pooled("random", PRIMARY, "selection", sp)[0],
                           sgmc=pooled("random", "sgmc_offcat", "selection", sp)[0]),
            "h33_reference": dict(primary=pooled("h33_reference", PRIMARY, "selection")[0],
                                  sgmc=pooled("h33_reference", "sgmc_offcat", "selection")[0]),
            "h47c1": dict(primary=pooled("h47c1", PRIMARY, "selection")[0],
                          sgmc=pooled("h47c1", "sgmc_offcat", "selection")[0]),
        }

    # ---- the frozen six-condition promotion gate --------------------------------
    h50_anchor = arms_out["h50"]
    gate_rows = {}
    for arm in ARMS:
        a = arms_out[arm]
        c = controls[arm]
        cond = {
            "beats_h50_by_10pct": bool(a["pooled_primary_selection"]
                                       >= 1.10 * h50_anchor["pooled_primary_selection"]),
            "positive_conformal_floor": bool(a["conformal"]["floor"] > 0.0),
            "sgmc_beats_random": bool(a["pooled_sgmc_selection"] >= c["random"]["sgmc"]),
            "beats_random_3x_primary": bool(a["pooled_primary_selection"]
                                            >= 3.0 * c["random"]["primary"]),
            "beats_incumbent_h60": bool(
                a["pooled_primary_selection"] > H60_FROZEN_PRIMARY
                and a["pooled_sgmc_selection"] > H60_FROZEN_SGMC),
        }
        cond["passed_1_to_4"] = all(cond[k] for k in
                                    ("beats_h50_by_10pct", "positive_conformal_floor",
                                     "sgmc_beats_random", "beats_random_3x_primary"))
        gate_rows[arm] = dict(conditions=cond, passed=cond["passed_1_to_4"])
    passing = [a for a, g in gate_rows.items() if g["passed"]]
    promotable = [a for a in passing if gate_rows[a]["conditions"]["beats_incumbent_h60"]]
    winner = None
    if passing:
        winner = max(passing, key=lambda a: (arms_out[a]["pooled_sgmc_selection"],
                                             arms_out[a]["conformal"]["floor"]))

    summary = {
        "schema_version": 1,
        "hypothesis_ids": ["H65", "H66", "H67", "H68"],
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "RESEARCH_SCREEN_NOT_A_SUBMISSION",
        "preregistration": "docs/research/h65-hypotheses-preregistered.md",
        "design": {
            "blocks": f"{NROWS}x{NCOLS} contiguous, {GUARD_PX} px guard, roles assigned "
                      "before any score is computed; asserted byte-equal to the frozen "
                      "H50 screen blocks (seed 500610)",
            "budget": BUDGET,
            "spacings_px": list(SPACINGS),
            "primary_instrument": PRIMARY,
            "instruments": {k: list(v) for k, v in INSTRUMENTS.items()},
            "noise_masks": {"tiger_road_lt_m": h60.ROAD_MASK_M,
                            "blm_closed_claim_lt_m": h60.CLAIM_MASK_M},
            "h65_thresholds": {k: float(v) for k, v in h65.H65_THRESHOLDS.items()},
            "h66_far_radius_px": h65.H66_FAR_RADIUS_PX,
            "h67_lambda": h65.H67_LAMBDA,
            "h67_thk_band": h65.H67_THK_BAND,
            "h68_channels": list(h65.H68_CHANNELS),
            "emission_domains": {a: int(d.sum()) for a, d in arm_domain.items()},
            "conformal_rule": "operating point = argmax certified lower bound "
                              "(choose_operating_point); selection half centers, "
                              "calibration half certifies; coverage 0.90",
            "conformal_reference": "https://doi.org/10.1080/01621459.2017.1307116",
        },
        "h65_consensus_counts": built["h65"]["counts"],
        "arms": arms_out,
        "controls": controls,
        "gate": {"rule": "preregistered six-condition gate (see preregistration); "
                         "conditions 1-5 computed here, 6 (uniqueness + format) is "
                         "computed by the artefact builder if this gate passes",
                 "frozen_incumbent": {"h60_primary": H60_FROZEN_PRIMARY,
                                      "h60_sgmc": H60_FROZEN_SGMC,
                                      "h50_primary": H50_FROZEN_PRIMARY},
                 "per_arm": gate_rows, "passing_arms": passing,
                 "promotable_arms": promotable, "winner": winner,
                 "tiebreak": "highest pooled selection-half sgmc_offcat DTI, then "
                             "higher conformal floor",
                 "promotion_rule": "an arm replaces H60 as the primary (OK-to-submit) "
                                   "artifact only if it passes conditions 1-4 AND "
                                   "beats_incumbent_h60 (both pooled selection-half "
                                   "DTIs above H60's frozen values)"},
        "instrument_truth_pixels": {k: int(v.sum()) for k, v in instruments.items()},
        "instrument_sgmc_offcat_truth_pixels": int(sgmc.sum()),
        "code_digests": {p: digest(ROOT / p) for p in CODE_PATHS},
        "spacing_history_sha256": digest(history),
        "anchor_reproduction": {
            "expected_h50_pooled_primary_selection": H50_FROZEN_PRIMARY,
            "measured_h50": arms_out["h50"]["pooled_primary_selection"],
            "expected_h60_pooled_primary_selection": H60_FROZEN_PRIMARY,
            "measured_h60": arms_out["h60"]["pooled_primary_selection"],
            "matches": bool(
                abs(arms_out["h50"]["pooled_primary_selection"] - H50_FROZEN_PRIMARY) < 1e-6
                and abs(arms_out["h60"]["pooled_primary_selection"] - H60_FROZEN_PRIMARY) < 1e-6),
        },
        "limitations": [
            "The primary instrument is derived from the same owner-built lidar stack that "
            "the H60/H65/H66/H68 fields read; their primary-instrument numbers are "
            "optimistic by construction. H67's Th/K component is independent of it.",
            "Spatial separation does not establish geological exchangeability; every "
            "conformal floor is conditional on that assumption and covers one future "
            "block's proxy DTI, not the private leaderboard.",
            "The screen spends no competition submission slot and reads no private label.",
            "Owner-reported scores and the d2.8 reference raster are not organiser receipts.",
            "The GeoDAWN Th/K grid is a contractor u8-rank product, not physical units.",
        ],
        "elapsed_seconds": round(time.time() - started, 2),
    }
    save_json(EV / "screen.json", summary)
    print(json.dumps({"arms": {a: {k: arms_out[a][k] for k in
                                   ("selected_spacing_px", "selection_mean",
                                    "pooled_primary_selection", "pooled_sgmc_selection")}
                              for a in ARMS + ANCHORS},
                      "floors": {a: round(arms_out[a]["conformal"]["floor"], 6)
                                 for a in ARMS + ANCHORS},
                      "gate": {a: gate_rows[a]["conditions"] for a in ARMS},
                      "passing": passing, "promotable": promotable, "winner": winner,
                      "anchor_reproduction": summary["anchor_reproduction"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
