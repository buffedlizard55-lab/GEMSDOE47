#!/usr/bin/env python3
"""H50 spatially-blocked holdout screen with split-conformal operating-point selection.

Design (frozen before any test score is produced)
-------------------------------------------------
* **Blocks.**  8x8 contiguous rectangular blocks of the competition grid with a 3 px guard,
  so no pixel and no 300 m kernel support is shared between two blocks.  Roles are assigned
  to every block that has evaluated pixels, *before* any score is computed; blocks with few
  or no truth pixels are never dropped after the fact.
* **Split.**  One seeded 50/50 split of the blocks into a **selection half** and a
  **calibration half**.  The spacing is chosen on the selection half only; the calibration
  half, which the choice never saw, then certifies it.  This is the split-conformal
  structure of Lei, G'Sell, Rinaldo, Tibshirani and Wasserman (JASA 2018, Algorithm 2 /
  Theorem 2.2, https://doi.org/10.1080/01621459.2017.1307116), implemented by
  ``gems47.conformal.simultaneous_lower_bounds``.
* **Unit.**  One block's DTI against Instrument L (the off-catalogue 1 m lidar scarp-peak
  population).  The maximum residual is taken over the whole spacing sweep inside a block,
  so the band is simultaneous over the sweep.
* **Controls**, all at the chosen spacing and the same per-block budget: a fixed-seed spaced
  random field, the owner-reported d2.8 reference raster, and the repository's previous
  holdout best (H47-C1).  A candidate that does not beat every control on the selection half
  does not pass the gate.
* **Outputs.**  ``evidence/h50/screen.json`` plus ``evidence/h50/spacing-history.csv``.

This screen does not spend a competition submission slot and does not read any private label.
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
from scipy import ndimage as ndi

from gems47 import grid as G
from gems47 import h50
from gems47.conformal import simultaneous_lower_bounds
from gems47s3.geomorph import rank_scale

SPACINGS = (2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.6)
BUDGET = 37_654
NROWS = NCOLS = 8
GUARD_PX = 3
SEED = 500610
COVERAGE = 0.90
REFERENCE_COVERAGES = (0.90, 0.80, 0.75)
REGIONAL_SIGMA_PX = 25.0
PRIMARY_INSTRUMENT = "lappos_t200_d3"
INSTRUMENTS = {
    "lappos_t200_d3": ("lappos_max", 200, 3),
    "lapneg_t200_d3": ("lapneg_max", 200, 3),
    "step_t150_d3": ("step_max", 150, 3),
    "cross_t200_d3": ("cross_max", 200, 3),
    "upface_t200_d3": ("upface_max", 200, 3),
    "union_t200_d3": ("union", 200, 3),
}
CODE_PATHS = ("scripts/run_h50_screen.py", "src/gems47/h50.py", "src/gems47/conformal.py",
              "src/gems47/metric.py", "src/gems47s3/metric.py", "gemsdoe47/magnetic.py")


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
                # A geometric cell with no evaluated pixel cannot be a conformal unit.
                # It is dropped here, before roles are assigned, so the decision is made
                # without looking at any score.
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


def main() -> int:
    started = time.time()
    data = G.data_dir()
    grids = h50.read_grid(data)
    mask = grids["evaluated"]
    blocks = build_blocks(mask)
    roles = {r: sum(b["role"] == r for b in blocks) for r in ("selection", "calibration")}

    # ---- the H50 field: rank of the detrended-elevation slope above its regional level
    with rasterio.open(data / "training_features.tif") as src:
        slope = src.read(h50.SLOPE_BAND).astype(np.float32)
    slope[~np.isfinite(slope)] = 0.0
    slope[slope < -1e30] = 0.0
    regional = ndi.gaussian_filter(slope, REGIONAL_SIGMA_PX, mode="nearest")
    field = rank_scale(np.where(mask, slope - regional, np.nan))
    field = np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)

    # ---- instruments
    ch = h50.lidar_scarp_channels(data)
    valid = ch["valid"] > 0
    instruments = {}
    for iname, (chan, thr, md) in INSTRUMENTS.items():
        if chan == "union":
            m = np.zeros(mask.shape, bool)
            for nm in h50.LIDAR_SCARP_CHANNELS:
                m |= h50.lidar_peaks(ch[nm], valid, thr, md)
        else:
            m = h50.lidar_peaks(ch[chan], valid, thr, md)
        m &= grids["footprint"] & ~grids["catalogue"]
        instruments[iname] = m & mask
    sgmc = h50.instrument_sgmc_offcatalogue(data) & mask

    # ---- controls
    with rasterio.open(data / "reference" / "h33-2-b2-zeros.tif") as src:
        h33 = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0) > 0
    c1_path = ROOT / "docs" / "downloads" / \
        "gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif"
    with rasterio.open(c1_path) as src:
        c1 = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0) > 0

    rows = []
    control_rows = []
    t0 = time.time()
    for b in blocks:
        y0, y1, x0, x1 = b["bounds_rc"]
        sy, sx = slice(y0, y1), slice(x0, x1)
        valid = mask[sy, sx]
        truth_primary = instruments[PRIMARY_INSTRUMENT][sy, sx]
        b["truth_pixels_primary"] = int(truth_primary.sum())
        rng = np.random.default_rng(SEED + b["block_id"])
        random_field = rng.random(valid.shape, dtype=np.float32)
        # the random control is emitted with the SAME greedy spaced selection, spacing and
        # budget as the candidate, so the comparison is mass-matched
        for name, fld in (("h50", field[sy, sx]), ("random", random_field),
                          ("h33_reference", h33[sy, sx].astype(np.float32)),
                          ("h47c1", c1[sy, sx].astype(np.float32))):
            if name == "h50":
                for spacing in SPACINGS:
                    p = h50.emit(fld, valid, spacing, b["budget"])
                    for iname, itruth in instruments.items():
                        r = _score(p, itruth[sy, sx], valid)
                        rows.append(dict(role=b["role"], block_id=b["block_id"], model=name,
                                         spacing_px=spacing, instrument=iname, **r))
            elif name == "random":
                for spacing in SPACINGS:
                    p = h50.emit(random_field, valid, spacing, b["budget"])
                    for iname, itruth in instruments.items():
                        r = _score(p, itruth[sy, sx], valid)
                        control_rows.append(dict(role=b["role"], block_id=b["block_id"],
                                                 model=name, spacing_px=spacing,
                                                 instrument=iname, **r))
            else:
                p = fld
                if float(p.sum()) <= 0:
                    continue
                for iname, itruth in instruments.items():
                    r = _score(p, itruth[sy, sx], valid)
                    control_rows.append(dict(role=b["role"], block_id=b["block_id"], model=name,
                                             spacing_px=None, instrument=iname, **r))
        print(f"[block {b['block_id']:2d}] {b['role']:11s} truth={b['truth_pixels_primary']:5d} "
              f"budget={b['budget']:5d} ({time.time()-t0:.0f}s)", flush=True)

    # ---- selection on the SELECTION half only -------------------------------
    def matrix(model, instrument, role):
        return np.array([[_row(rows, model, instrument, role, b["block_id"], s) for s in SPACINGS]
                         for b in blocks if b["role"] == role])

    sel = matrix("h50", PRIMARY_INSTRUMENT, "selection")
    cal = matrix("h50", PRIMARY_INSTRUMENT, "calibration")
    means = sel.mean(axis=0)
    chosen = int(max(range(len(SPACINGS)), key=lambda i: (float(means[i]), float(SPACINGS[i]))))
    spacing = float(SPACINGS[chosen])

    bands = {}
    for cov in REFERENCE_COVERAGES:
        bands[f"{cov:.2f}"] = simultaneous_lower_bounds(sel, cal, coverage=cov)
    band = bands[f"{COVERAGE:.2f}"]

    def pooled(model, instrument, role, spacing_value=None):
        sel_rows = [r for r in rows + control_rows
                    if r["role"] == role and r["model"] == model and r["instrument"] == instrument
                    and (spacing_value is None or r["spacing_px"] == spacing_value)]
        if not sel_rows:
            return 0.0
        T = sum(r["TP_w"] for r in sel_rows)
        F = sum(r["FP_w"] for r in sel_rows)
        K = sum(r["|G|"] for r in sel_rows)
        den = T + 0.2 * F + 0.8 * K
        return float(T / den) if den > 0 else 0.0

    # the random control is matched on spacing and mass; the two raster controls are used at
    # their own emission, so they carry no spacing key
    control_spacing = {"random": spacing, "h33_reference": None, "h47c1": None}
    controls = {}
    for name in ("random", "h33_reference", "h47c1"):
        sp = control_spacing[name]
        controls[name] = dict(
            selection_mean=pooled(name, PRIMARY_INSTRUMENT, "selection", sp),
            selection_block_mean=_block_mean(rows + control_rows, name, PRIMARY_INSTRUMENT,
                                             "selection", sp),
            calibration_mean=pooled(name, PRIMARY_INSTRUMENT, "calibration", sp),
        )
    candidate = dict(selection_mean=pooled("h50", PRIMARY_INSTRUMENT, "selection", spacing),
                     selection_block_mean=float(means[chosen]),
                     calibration_mean=pooled("h50", PRIMARY_INSTRUMENT, "calibration", spacing),
                     conformal_floor=float(band["lower_bounds"][chosen]),
                     conformal_rank=int(band["rank_1_based"]),
                     conformal_coverage=float(band["finite_sample_coverage_at_least_if_exchangeable"]))
    beats_random = candidate["selection_mean"] > controls["random"]["selection_mean"]
    beats_h33 = candidate["selection_mean"] > controls["h33_reference"]["selection_mean"]
    beats_c1 = candidate["selection_mean"] > controls["h47c1"]["selection_mean"]
    gate = dict(beats_random_control=bool(beats_random),
                beats_owner_reported_d28_reference=bool(beats_h33),
                beats_h47c1_previous_holdout_best=bool(beats_c1),
                positive_conformal_floor=bool(candidate["conformal_floor"] > 0.0),
                passed=bool(beats_random and beats_h33 and beats_c1
                            and candidate["conformal_floor"] > 0.0))

    history = ROOT / "evidence" / "h50" / "spacing-history.csv"
    with history.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "schema_version": 1,
        "hypothesis_id": "H50",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "RESEARCH_SCREEN_NOT_A_SUBMISSION",
        "design": {
            "blocks": f"{NROWS}x{NCOLS} contiguous, {GUARD_PX} px guard, roles assigned "
                      "before any score is computed",
            "split": "one seeded 50/50 split into a selection half and a calibration half; "
                     "the spacing is chosen on the selection half and certified on the "
                     "calibration half",
            "conformal_method": "max-over-settings one-sided split conformal "
                                "(Lei et al. JASA 2018 Algorithm 2 / Theorem 2.2)",
            "conformal_reference": "https://doi.org/10.1080/01621459.2017.1307116",
            "unit": "one spatial block's DTI against the off-catalogue lidar scarp-peak "
                    "instrument",
            "primary_instrument": PRIMARY_INSTRUMENT,
        "controls": "the random control uses the same greedy spaced selection, spacing and "
                    "per-block budget as the candidate (mass-matched); the h33 reference and "
                    "H47-C1 controls are used at their own emission, restricted to the block",
            "budget": BUDGET,
            "spacings_px": list(SPACINGS),
            "regional_sigma_px": REGIONAL_SIGMA_PX,
            "seed": SEED,
        },
        "block_counts": roles,
        "block_truth_counts": {r: sum(b["role"] == r and b["truth_pixels_primary"] > 0
                                      for b in blocks) for r in roles},
        "selected_spacing_px": spacing,
        "selected_spacing_index": chosen,
        "selection_means": [float(v) for v in means],
        "conformal": band,
        "conformal_at_other_levels": {k: {"lower_bounds": v["lower_bounds"],
                                          "rank_1_based": v["rank_1_based"],
                                          "coverage_at_least_if_exchangeable":
                                              v["finite_sample_coverage_at_least_if_exchangeable"]}
                                      for k, v in bands.items()},
        "candidate": candidate,
        "controls": controls,
        "gate": gate,
        "instrument_truth_pixels": {k: int(v.sum()) for k, v in instruments.items()},
        "instrument_sgmc_offcat_truth_pixels": int(sgmc.sum()),
        "secondary_instrument_selection_mean": {
            iname: pooled("h50", iname, "selection", spacing) for iname in instruments},
        "control_rows": control_rows,
        "spacing_history_sha256": digest(history),
        "limitations": [
            "Instrument L is derived from a lidar product that shares a physical quantity "
            "(slope) with the field's input band; it is an optimistic instrument for this field.",
            "Spatial separation does not establish geological exchangeability; the conformal "
            "floor is conditional on that assumption and is not a private-label guarantee.",
            "The screen does not spend a competition submission slot and reads no private label.",
            "Owner-reported scores and the d2.8 reference raster are not organiser receipts.",
        ],
        "elapsed_seconds": round(time.time() - started, 2),
    }
    save_json(ROOT / "evidence" / "h50" / "screen.json", summary)
    save_json(ROOT / "evidence" / "h50" / "blocks.json", {"blocks": blocks, "seed": SEED,
                                                          "guard_px": GUARD_PX})
    print(json.dumps({"selected_spacing_px": spacing, "candidate": candidate,
                      "controls": controls, "gate": gate,
                      "conformal_floor": band["lower_bounds"][chosen],
                      "conformal_coverage": band["finite_sample_coverage_at_least_if_exchangeable"]},
                     indent=2))
    return 0


def _score(p: np.ndarray, truth: np.ndarray, valid: np.ndarray) -> dict:
    from gems47s3.metric import dti
    r = dti(p, truth.astype(np.int8), valid=valid)
    return {"TP_w": r["tp"], "FP_w": r["fp"], "FN_w": r["fn"], "|G|": r["n_truth"],
            "S": r["S"], "Phi": r["M"], "DTI": r["dti"]}


def _row(rows, model, instrument, role, block_id, spacing):
    for r in rows:
        if (r["model"] == model and r["instrument"] == instrument and r["role"] == role
                and r["block_id"] == block_id and r["spacing_px"] == spacing):
            return float(r["DTI"])
    raise ValueError(f"missing row {model} {instrument} {role} {block_id} {spacing}")


def _block_mean(rows, model, instrument, role, spacing_value=None):
    vals = [float(r["DTI"]) for r in rows if r["model"] == model and r["instrument"] == instrument
            and r["role"] == role
            and (spacing_value is None or r["spacing_px"] == spacing_value)]
    return float(np.mean(vals)) if vals else 0.0


if __name__ == "__main__":
    raise SystemExit(main())
