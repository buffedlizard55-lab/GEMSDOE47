#!/usr/bin/env python3
"""RETIRED H47-C1 publisher; execution is disabled to protect reviewed artifacts.

This historical builder consumes ``scripts/run_conformal.py`` output, whose selected candidate
and reported floor reused calibration outcomes. Its old writer also predates the current strict
mask/footprint contract. It must not be used to create or overwrite a current download. The code
is retained below only as an educational record; H49 is an archived research artifact with a
closed slot gate, described in ``docs/H49_RESULTS.md``.

Running this entrypoint now exits before reading data, making directories, or writing files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47s3 import emission as E
from gems47s3.detector import Bands, Recipe, build_field
from gems47s3.grid import Grid
from gems47s3.raster import receipt_json, validate_submission, write_submission
from gems47s3.spec import FOOTPRINT_PIXELS, HEIGHT, WIDTH

DATA = ROOT / "data"
REF = DATA / "reference"
SUB = ROOT / "submission"
DL = ROOT / "docs" / "downloads"
EVS = ROOT / "evidence" / "submission"
DEFAULT_NAME = "gemsdoe47-scarp-persistence-v1"
DEFAULT_NOTE = ("Across-strike slope-step persisted 1.9 km along strike; binary dots at "
                "2 px spacing, 2 px off known-fault flanks; spacing chosen by split conformal.")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    inter = float((a & b).sum())
    union = float((a | b).sum())
    return inter / union if union else 1.0


def load_recipe_and_op(selection_path: Path) -> tuple[Recipe, dict]:
    sel = json.loads(Path(selection_path).read_text())
    chosen = sel["chosen"]
    rec = next(r for r in sel["recipes"] if r["name"] == chosen["recipe"]) \
        if "recipes" in sel else None
    if rec is None:
        sw = json.loads((ROOT / "evidence" / "sweep" / "sweep_a.json").read_text())
        rec = next(r for r in sw["recipes"] if r["name"] == chosen["recipe"])
    recipe = Recipe.from_dict(rec)
    # pass the whole selection through, plus the chosen block flattened, so every guarantee
    # statistic the selector computed (single split, repeated splits, mass ceiling, the
    # delivered-alpha audit) reaches the submission bundle unmodified
    out = dict(sel)
    out.update(op=chosen["op"], params=chosen["params"],
               worst_normalised_floor=chosen.get("worst_normalised_floor"),
               worst_normalised_mean=chosen.get("worst_normalised_mean"),
               mean_risk_objective=chosen.get("mean_risk"),
               worst_instrument=chosen.get("worst_instrument"),
               calibration_means=chosen.get("calibration_means", {}),
               floors_at_alpha=chosen.get("floors_at_alpha", {}),
               empirical_violation=chosen.get("empirical_violation_by_instrument", {}),
               normalised_means=chosen.get("normalised_means", {}))
    out["alpha"] = sel.get("alpha_used", sel.get("alpha"))
    return recipe, out


def main() -> int:
    print(
        "RETIRED: H47-C1 builder consumes a calibration-selected historical result and predates "
        "the strict current TIFF contract. No data were read and no files were written; H49 is an "
        "archived research artifact documented in docs/H49_RESULTS.md, not the current-artifact pointer.",
        file=sys.stderr,
    )
    return 2


def _legacy_main_not_for_execution() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selection", default=str(ROOT / "evidence" / "conformal" / "selection.json"))
    ap.add_argument("--name", default=DEFAULT_NAME)
    ap.add_argument("--note", default=DEFAULT_NOTE)
    ap.add_argument("--floor", default="repeated_split_p05",
                    choices=["repeated_split_p05", "single_split"],
                    help="which certified floor to quote next to the chosen spacing")
    ap.add_argument("--mode", default="zeros", choices=["zeros", "nan"])
    ap.add_argument("--dry-run", action="store_true", help="validate but do not write")
    args = ap.parse_args()
    t0 = time.time()
    SUB.mkdir(parents=True, exist_ok=True)
    DL.mkdir(parents=True, exist_ok=True)
    EVS.mkdir(parents=True, exist_ok=True)

    name = re.sub(r"[^A-Za-z0-9._-]", "-", args.name)
    recipe, choice = load_recipe_and_op(Path(args.selection))
    p = choice["params"]
    min_dist = float(p["min_dist"]); density = float(p["density_per_1000"]); flank_b = float(p["flank_b"])
    print(f"[frozen] recipe={recipe.name} spacing={min_dist} density={density}/1000 flank_b={flank_b}")
    rsr = choice.get("repeated_split_robustness") or {}
    a_key = f"alpha={choice['alpha']:.2f}"
    rep = (rsr.get("by_alpha", {}) or {}).get(a_key, {})
    floor_single = choice["guarantee"]["certified_floor"]
    floor_split_robust = rep.get("floor_p05")
    quoted = floor_split_robust if (args.floor == "repeated_split_p05" and floor_split_robust
                                    is not None) else floor_single
    print(f"[frozen] conformal guarantee: floor={quoted:.5f} at "
          f"{choice['guarantee']['certified_confidence_pct']}% confidence "
          f"(alpha={choice['alpha']}, n={choice['guarantee']['n_calibration_blocks']} blocks, "
          f"basis={args.floor})")
    print(f"[frozen]   single pre-registered split floor {floor_single:.5f}; "
          f"repeated-split ({rep.get('n_splits', 0)} splits) p05 {floor_split_robust}, "
          f"median {rep.get('floor_median')}, mean violation rate "
          f"{rep.get('mean_violation_rate')} vs nominal {choice['alpha']}")
    assert len(args.note) <= 200, f"Note must be <= 200 characters, got {len(args.note)}"

    g = Grid()
    valid = np.load(DATA / "surfaces" / "valid.npy")
    bands = Bands(DATA / "training_features.tif")
    built = build_field(recipe, bands, valid, g.catalogue)
    field = built["field"]
    print(f"[field] built on the full grid with the full catalogue visible  ({time.time()-t0:.0f}s)")

    # ---- emission domain: inside the footprint, finite in all bands, off the given catalogue
    scored = g.footprint & valid & ~g.catalogue
    n_scored = int(scored.sum())
    budget = round(density * n_scored / 1000.0)
    emask = scored if flank_b <= 0 else (scored & (g.d_catalogue > flank_b))
    em = E.emit(field, emask, min_dist=min_dist, support_q=1.0, blur="none", budget=budget)
    mask = em["mask"]
    n_emitted = int(mask.sum())
    print(f"[emit] scored domain {n_scored} px, budget {budget}, thinned {em['n_thinned']}, "
          f"emitted {n_emitted} px = {1000.0*n_emitted/n_scored:.2f} per 1000 "
          f"({100.0*n_emitted/FOOTPRINT_PIXELS:.4f}% of footprint)  ({time.time()-t0:.0f}s)")

    values = np.zeros((HEIGHT, WIDTH), np.float32)
    values[mask] = np.float32(1.0)

    # ---- uniqueness against every reference artifact
    uniq = []
    for rp in sorted(REF.glob("*.tif")):
        with rasterio.open(rp) as ds:
            other = ds.read(1)
        ob = np.nan_to_num(other.astype(np.float32)) > 0
        uniq.append(dict(file=rp.name, other_positive_px=int(ob.sum()),
                         intersection=int((mask & ob).sum()),
                         jaccard=round(jaccard(mask, ob), 6),
                         containment_of_other_in_ours=round(float((ob & mask).sum() / max(ob.sum(), 1)), 6),
                         sha256=sha256(rp)))
    max_j = max(u["jaccard"] for u in uniq)
    max_c = max(u["containment_of_other_in_ours"] for u in uniq)
    print(f"[unique] max Jaccard vs the {len(uniq)} reference artifacts = {max_j:.6f} "
          f"({max(uniq, key=lambda u: u['jaccard'])['file']}); max containment = {max_c:.4f}")

    out_paths = [SUB / f"{name}.tif", DL / f"{name}.tif"]
    receipts = []
    if not args.dry_run:
        for op in out_paths:
            w = write_submission(values, op, mode=args.mode, footprint=np.ones(values.shape, bool))
            rc = validate_submission(op, footprint=g.footprint, catalogue=g.catalogue)
            receipts.append(rc)
            receipt_json(rc, EVS / f"checks-{op.parent.name}-{name}.json")
            print(f"[write] {op}  {w['bytes']} bytes  sha256={w['sha256'][:16]}...  "
                  f"all_checks_passed={rc.ok}")
            assert rc.ok, json.dumps({k: v for k, v in rc.checks.items() if not v}, indent=2)
    else:
        print("[dry-run] not written")

    rc = receipts[0] if receipts else None
    bundle = dict(
        submission_name=name,
        note_optional=args.note,
        note_length=len(args.note),
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        seconds=round(time.time() - t0, 1),
        files=[str(p) for p in out_paths],
        sha256=[sha256(p) for p in out_paths] if not args.dry_run else [],
        recipe=recipe.to_dict(),
        operating_point=dict(min_spacing_px=min_dist, emitted_density_per_1000_scored=density,
                             catalogue_flank_buffer_px=flank_b,
                             catalogue_flank_buffer_m=flank_b * 100.0,
                             budget=budget, n_scored_domain=n_scored,
                             emitted_px=n_emitted,
                             emitted_pct_of_footprint=round(100.0 * n_emitted / FOOTPRINT_PIXELS, 5),
                             engine="nms_disk (field-ordered non-maximum suppression)"),
        conformal=dict(certified_floor_quoted=quoted, floor_basis=args.floor,
                       alpha=choice["alpha"],
                       primary_instrument=choice["primary_instrument"],
                       certified_floor=choice["guarantee"]["certified_floor"],
                       certified_confidence_pct=choice["guarantee"]["certified_confidence_pct"],
                       n_calibration_blocks=choice["guarantee"]["n_calibration_blocks"],
                       n_selection_blocks=choice["guarantee"]["n_selection_blocks"],
                       selection_half_mean_dti=choice["guarantee"]["selection_mean"],
                       cleared_floor=choice["guarantee"]["cleared_floor"],
                       leave_one_out_worst_floor=choice["guarantee"]["leave_one_out_worst_floor"],
                       dkw_mean_floor=choice["guarantee"]["mean_floor_dkw"],
                       vacuous=choice["guarantee"]["vacuous"],
                       alpha_sensitivity=choice["alpha_sensitivity"],
                       worst_normalised_floor_across_instruments=choice["worst_normalised_floor"],
                       worst_instrument=choice["worst_instrument"],
                       calibration_means_by_instrument=choice["calibration_means"],
                       exchangeability_caveat=choice["guarantee"]["exchangeability_note"]),
        format_receipt=rc.to_dict() if rc else None,
        uniqueness=dict(max_jaccard_vs_reference=max_j, max_containment_vs_reference=max_c,
                        is_unique=bool(max_j < 0.5 and max_c < 0.9),
                        threshold_jaccard=0.5, threshold_containment=0.9,
                        per_reference=uniq),
        values_are_binary=bool(np.array_equal(np.unique(values), np.array([0.0, 1.0], np.float32))),
        why_binary=("dDTI > 0 for a pixel of value v and best-cover weight w depends on w alone, "
                    "not on v; down-weighting a pixel that clears the bar only shrinks its gain. "
                    "Binary is the optimum of the soft family. See tests/test_metric_s3.py."),
    )
    (EVS / "bundle.json").write_text(json.dumps(bundle, indent=2))
    print(f"\nwrote {EVS/'bundle.json'}   ({time.time()-t0:.0f}s)")
    print(f"unique={bundle['uniqueness']['is_unique']}  format_ok={rc.ok if rc else None}  "
          f"binary={bundle['values_are_binary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
