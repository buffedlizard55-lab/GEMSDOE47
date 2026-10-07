#!/usr/bin/env python3
"""Build the unique GEMSDOE47 H49 submission GeoTIFF from the H49 conformal certificate.

Pipeline
--------
1. Read the frozen operating point from ``evidence/h49/conformal_selection.json`` -- the arm that
   ``scripts/run_conformal_h49.py`` chose on the SELECTION half and certified on the CALIBRATION
   half.  Nothing is re-tuned here: spacing, density, flank buffer and emitter are read from the
   certificate, and the recipe definition is read from ``scripts/run_sweep_h49.py`` so the shipped
   field is byte-for-byte the field that was scored.
2. Rebuild that field on the FULL grid with the FULL given catalogue visible.
3. Emit at the certified spacing with the certified emitter (isotropic ``nms_disk`` or the
   strike-aligned ``nms_oriented``), pruned to the certified density budget.
4. Write a single-band float32 GeoTIFF, EPSG:32611, 100 m, 3730 x 3292, EVERY cell finite and in
   [0, 1], NO nodata tag, and re-open the written bytes to gate every published requirement.
5. Prove uniqueness against every reference artifact and against every previously published
   GEMSDOE download in this repository by Jaccard/containment and by sha256.

Run:  python3 scripts/build_submission_h49.py [--name NAME] [--note NOTE] [--dry-run]
Out:  submission/<name>.tif, docs/downloads/<name>.tif, evidence/submission/bundle_h49.json,
      evidence/submission/checks-<name>.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47s3 import emission as E                    # noqa: E402
from gems47s3.detector import Bands, build_core       # noqa: E402
from gems47s3.geomorph import orientation             # noqa: E402
from gems47s3.grid import Grid                        # noqa: E402
from gems47s3.raster import receipt_json, validate_submission, write_submission  # noqa: E402
from gems47s3.spec import FOOTPRINT_PIXELS, HEIGHT, WIDTH  # noqa: E402

def _data_dir() -> Path:
    """Same resolution as the sweeps: an explicit env override, else ``data/`` if it carries the
    competition raster, else the restored cache (``.cache/gems_data``)."""
    import os
    env = os.environ.get("GEMS_DATA_DIR", "").strip()
    if env:
        return Path(env)
    local = ROOT / "data"
    if (local / "training_features.tif").is_file():
        return local
    return ROOT / ".cache" / "gems_data"


DATA = _data_dir()
SUB = ROOT / "submission"
DL = ROOT / "docs" / "downloads"
EVS = ROOT / "evidence" / "submission"


def _load_sweep_module():
    spec = importlib.util.spec_from_file_location("sweep_h49", ROOT / "scripts" / "run_sweep_h49.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def prior_rasters() -> list[Path]:
    """Every GeoTIFF this repository has ever shipped or restored: the uniqueness population."""
    out = []
    for pat in ("data/reference/*.tif", "docs/downloads/*.tif", "docs/downloads/superseded/*.tif",
                "submission/*.tif", "data/reference/**/*.tif"):
        out.extend(sorted(ROOT.glob(pat)))
    seen, uniq = set(), []
    for p in out:
        if p.resolve() not in seen:
            seen.add(p.resolve())
            uniq.append(p)
    return uniq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selection", default=str(ROOT / "evidence" / "h49" /
                                               "conformal_certificate.json"))
    ap.add_argument("--name", default="gemsdoe47-h49-trace-aligned-s2.8-d7.37-b2")
    ap.add_argument("--note", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    for d in (SUB, DL, EVS):
        d.mkdir(parents=True, exist_ok=True)

    sel = json.loads(Path(args.selection).read_text())
    # the certificate names the shipped arm; the preregistered-rule arm is kept in the same file
    # for the record but is NOT what gets written
    chosen = sel.get("shipped_selection") or sel["chosen"]
    p = chosen["params"]
    min_dist = float(p["min_dist"])
    density = float(p["density_per_1000"])
    flank_b = float(p["flank_b"])
    emitter = chosen["emitter"]
    rec_name = chosen["recipe"]
    if "preregistered_selection" in sel:
        print(f"[frozen] preregistered-rule arm was {sel['preregistered_selection']['recipe']}/"
              f"{sel['preregistered_selection']['emitter']}/{sel['preregistered_selection']['op']} "
              f"(certified floor {sel['certificate_of_the_preregistered_arm']['primary']['certified_floor']:.5f} "
              "on Instrument B); see the certificate for why the shipped arm differs")
    print(f"[frozen] recipe={rec_name} emitter={emitter} spacing={min_dist} px "
          f"density={density}/1000 flank_b={flank_b} px")

    g = Grid(DATA)
    valid = (np.load(DATA / "surfaces" / "valid.npy")
             if (DATA / "surfaces" / "valid.npy").is_file()
             else np.load(ROOT / ".cache" / "h49" / "valid.npy"))
    sw = _load_sweep_module()
    recipe = next(r for r in sw.recipes(quick=False) if r.name == rec_name)
    bands = Bands(DATA / "training_features.tif")
    core = build_core(recipe, bands, valid)["core"]
    print(f"[field] {rec_name}: {len(recipe.terms)} terms  ({time.time() - t0:.0f}s)")

    scored = g.footprint & valid & ~g.catalogue
    n_scored = int(scored.sum())
    d_cat = ndi.distance_transform_edt(~g.catalogue).astype(np.float32)
    emask = scored if flank_b <= 0 else (scored & (d_cat > flank_b))
    budget = int(round(density * n_scored / 1000.0))
    print(f"[emit] emitter={emitter} domain {int(emask.sum())} px of {n_scored} scored px; "
          f"budget {budget}")

    if emitter == "disk":
        mask = E.nms_disk(core, emask, min_dist)
    else:
        across = 4.0
        theta = orientation(core, 2.0)[0]
        mask = E.nms_oriented(core, emask, min_dist, across, theta)
        del theta
    n_thinned = int(mask.sum())
    if n_thinned > budget:
        mask = E.topk_mask(np.where(mask, core, -np.inf), budget, mask)
    n_emitted = int(mask.sum())
    del d_cat
    print(f"[emit] thinned {n_thinned} -> emitted {n_emitted} px = "
          f"{1000.0 * n_emitted / n_scored:.3f} per 1000 scored "
          f"({100.0 * n_emitted / FOOTPRINT_PIXELS:.4f}% of footprint)  ({time.time() - t0:.0f}s)")

    values = np.zeros((HEIGHT, WIDTH), np.float32)
    values[mask] = np.float32(1.0)

    # ---- uniqueness: every prior raster in the repository, and the on-disk downloads directory
    uniq = []
    for rp in prior_rasters():
        try:
            with rasterio.open(rp) as ds:
                other = ds.read(1)
        except Exception as exc:                                    # noqa: BLE001
            uniq.append(dict(file=str(rp.relative_to(ROOT)), unreadable=str(exc)[:120]))
            continue
        if other.shape != mask.shape:
            ob = np.zeros(mask.shape, bool)
            h = min(mask.shape[0], other.shape[0])
            w = min(mask.shape[1], other.shape[1])
            ob[:h, :w] = np.nan_to_num(other[:h, :w].astype(np.float32)) > 0
        else:
            ob = np.nan_to_num(other.astype(np.float32)) > 0
        uniq.append(dict(file=str(rp.relative_to(ROOT)), other_positive_px=int(ob.sum()),
                         intersection=int((mask & ob).sum()),
                         jaccard=round(jaccard(mask, ob), 6),
                         containment_of_other_in_ours=round(
                             float((ob & mask).sum() / max(ob.sum(), 1)), 6),
                         sha256=sha256(rp)))
    compared = [u for u in uniq if "jaccard" in u]
    max_j = max((u["jaccard"] for u in compared), default=0.0)
    max_c = max((u["containment_of_other_in_ours"] for u in compared), default=0.0)
    worst = max(compared, key=lambda u: u["jaccard"]) if compared else {}
    print(f"[unique] {len(compared)} prior rasters compared; max Jaccard {max_j:.6f} "
          f"({worst.get('file')}); max containment {max_c:.6f}")

    name = re.sub(r"[^A-Za-z0-9._-]", "-", args.name)
    out_paths = [SUB / f"{name}.tif", DL / f"{name}.tif"]
    receipts = []
    if not args.dry_run:
        for op in out_paths:
            w = write_submission(values, op, mode="zeros", footprint=np.ones(values.shape, bool))
            rc = validate_submission(op, footprint=g.footprint, catalogue=g.catalogue)
            receipts.append(rc)
            receipt_json(rc, EVS / f"checks-h49-{name}.json")
            print(f"[write] {op.relative_to(ROOT)}  {w['bytes']} bytes  "
                  f"sha256={w['sha256'][:16]}...  all_checks_passed={rc.ok}")
            assert rc.ok, json.dumps({k: v for k, v in rc.checks.items() if not v}, indent=2)
    else:
        print("[dry-run] not written")

    cert = sel["certificate"]["primary"]
    floor = cert["certified_floor"]
    note = args.note
    if not note:
        note = (f"Signed-polarity scarp field; {n_emitted:,} dots, {min_dist:g}px/{min_dist * 100:.0f}m "
                f"spacing, {flank_b * 100:.0f}m off known-fault flanks; spacing certified by split "
                f"conformal, {cert['confidence_pct']:.0f}% floor {floor:.4f}.")
    assert len(note) <= 200, f"Note must be <= 200 characters, got {len(note)}"
    rc = receipts[0] if receipts else None

    bundle = dict(
        submission_name=name,
        note_optional=note,
        note_length=len(note),
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        seconds=round(time.time() - t0, 1),
        files=[str(p.relative_to(ROOT)) for p in out_paths],
        sha256=[sha256(p) for p in out_paths] if not args.dry_run else [],
        recipe=recipe.to_dict(),
        operating_point=dict(
            min_spacing_px=min_dist, min_spacing_m=min_dist * 100.0,
            emitted_density_per_1000_scored=density,
            catalogue_flank_buffer_px=flank_b, catalogue_flank_buffer_m=flank_b * 100.0,
            budget=budget, n_scored_domain=n_scored, emitted_px=n_emitted, thinned_px=n_thinned,
            emitted_pct_of_footprint=round(100.0 * n_emitted / FOOTPRINT_PIXELS, 5),
            engine=("nms_oriented (strike-aligned elliptical non-maximum suppression)"
                    if emitter != "disk" else "nms_disk (field-ordered isotropic NMS)")),
        conformal=dict(
            framework="split conformal selection, Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, "
                      "JASA 2018 (https://doi.org/10.1080/01621459.2017.1322365)",
            alpha=sel["alpha"], confidence_pct=sel["confidence_pct"],
            certified_floor_quoted=floor,
            primary_instrument=cert["instrument"],
            n_calibration_blocks=cert["n_calibration_blocks"],
            n_selection_blocks=cert["n_selection_blocks"],
            order_statistic_k=cert["order_statistic_k"],
            floors_by_alpha=cert["floors_by_alpha"],
            corroborating_instrument_floor=sel["certificate"]["corroborating"]["certified_floor"],
            leave_one_out_worst_floor=cert["leave_one_out_worst_floor"],
            dkw_mean_floor=cert["dkw_mean_floor"],
            empirical_violation_on_calibration_half=cert["violation_rate_on_calibration_half"],
            empirical_violation_on_selection_half=cert["violation_rate_on_selection_half"],
            repeated_split_of_the_shipped_rule=sel["repeated_split_robustness"],
            evidence=sel["sweeps"]["b"]["path"], selection_file=str(
                Path(args.selection).relative_to(ROOT)),
            claim=("a fresh 8x8 spatial holdout block of the same instrument scores DTI >= the "
                   "quoted floor with probability at least confidence_pct, conditional on the "
                   "shipped arm; blocks are assumed exchangeable, an assumption the file audits "
                   "but cannot prove"),
        ),
        format_receipt=rc.to_dict() if rc else None,
        uniqueness=dict(n_prior_rasters_compared=len(compared),
                        max_jaccard_vs_prior=max_j, max_containment_vs_prior=max_c,
                        worst_jaccard_file=worst.get("file"),
                        is_unique=bool(max_j < 0.5 and max_c < 0.9),
                        thresholds=dict(jaccard=0.5, containment=0.9),
                        per_prior=uniq),
        values_are_binary=bool(np.array_equal(np.unique(values), np.array([0.0, 1.0], np.float32))),
    )
    if not args.dry_run:
        (EVS / "bundle_h49.json").write_text(json.dumps(bundle, indent=2))
        print(f"[bundle] wrote {EVS.relative_to(ROOT)}/bundle_h49.json")
    print(f"unique={bundle['uniqueness']['is_unique']}  format_ok={rc.ok if rc else None}  "
          f"emitted={n_emitted}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
