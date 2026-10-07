#!/usr/bin/env python3
"""The spacing / budget / flank-buffer sweep, scored on the Instrument-A holdout.

Instrument A holds out WHOLE 8-connected components of the given catalogue inside contiguous
spatial blocks, masks the rest of the catalogue exactly as the organiser does, and scores the
exact DTI on what is left.  It is run three ways:

    A1  held-out truth = ISOLATED components (alone in their 300 m dilation)
    A2  held-out truth = FLANKING components (sharing a 300 m dilation with another trace)
    AA  held-out truth = all components in the block

A1 and A2 are reported separately. The often-cited 0.2708 → 0.2778 values are participant/owner-reported
observations, not an authenticated nested score pair; their TIFF association is unverified. Any
flank-pruning sensitivity that uses them is a conditional scenario, not a causal estimate. The local
A1/A2 public-catalogue frames are descriptive proxy populations and do not establish private performance.

The unit of exchangeability for the conformal guarantee is the BLOCK.

Run:  python3 scripts/run_sweep_a.py [--quick]
Out:  evidence/sweep/sweep_a.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47s3 import emission as E
from gems47s3 import metric as M
from gems47s3.detector import Bands, Recipe, build_core, regional_gate, vacancy_gate
from gems47s3.grid import Grid

DATA = ROOT / "data"
SURF = DATA / "surfaces"
EV = ROOT / "evidence" / "sweep"
STRUCT8 = np.ones((3, 3), bool)

# --------------------------------------------------------------------------- recipes
# Every term is (band, transform, radius_px, weight).  All terms are rank-scaled to a uniform
# [0,1] marginal before the weighted geometric mean, so weights are relative log-contributions
# and no term can dominate by amplitude.
DEFAULT_RECIPES = [
    dict(name="R1_scarp9", terms=[["det_elev_slope", "scarp", 9, 1.0]],
         notes="the single winning transform of scripts/search_scarp_radius.py"),
    dict(name="R2_scarp9_topo",
         terms=[["det_elev_slope", "scarp", 9, 3.0], ["det_elev_slope", "curv", 2.5, 1.0],
                ["det_elev_slope", "detrend", 2.5, 1.0], ["det_elev_slope", "slope_var", 5, 1.0]],
         notes="scarp plus three corroborating fine-scale topographic terms"),
    dict(name="R3_scarp9_topo_reg",
         terms=[["det_elev_slope", "scarp", 9, 3.0], ["det_elev_slope", "curv", 2.5, 1.0],
                ["det_elev_slope", "detrend", 2.5, 1.0], ["det_elev_slope", "slope_var", 5, 1.0],
                ["geod_2ndinv", "regional", 25, 1.5], ["geod_shearrate", "regional", 25, 1.0]],
         notes="R2 plus the two strongest regional strain-rate priors (A2 population)"),
    dict(name="R4_scarp9_topo_reg_mag",
         terms=[["det_elev_slope", "scarp", 9, 3.0], ["det_elev_slope", "curv", 2.5, 1.0],
                ["det_elev_slope", "detrend", 2.5, 1.0], ["det_elev_slope", "slope_var", 5, 1.0],
                ["geod_2ndinv", "regional", 25, 1.5], ["geod_shearrate", "regional", 25, 1.0],
                ["mag_anom", "regional", 25, 1.0], ["tmi_hg", "line", 2.5, 1.0]],
         notes="R3 plus magnetic terms, which carry the A1 (isolated) population"),
    dict(name="R5_scarp9_vacancy",
         terms=[["det_elev_slope", "scarp", 9, 3.0], ["det_elev_slope", "curv", 2.5, 1.0],
                ["det_elev_slope", "detrend", 2.5, 1.0], ["det_elev_slope", "slope_var", 5, 1.0],
                ["geod_2ndinv", "regional", 25, 1.5], ["geod_shearrate", "regional", 25, 1.0],
                ["mag_anom", "regional", 25, 1.0], ["tmi_hg", "line", 2.5, 1.0]],
         use_vacancy=True, vacancy_scale_px=8.0, vacancy_power=0.5,
         notes="R4 times the H47-A catalogue-vacancy gate at half power"),
    dict(name="R6_scarp13_reg",
         terms=[["det_elev_slope", "scarp", 13, 3.0], ["det_elev_slope", "curv", 2.5, 1.0],
                ["geod_2ndinv", "regional", 25, 1.5], ["mag_anom", "regional", 25, 1.0]],
         notes="longer along-strike persistence (2.7 km), fewer corroborating terms"),
]


def recipes(quick: bool) -> list[Recipe]:
    src = DEFAULT_RECIPES[:3] if quick else DEFAULT_RECIPES[:5]
    return [Recipe(name=d["name"], terms=[(b, t, float(r), float(w)) for b, t, r, w in d["terms"]],
                   use_vacancy=d.get("use_vacancy", False),
                   vacancy_scale_px=d.get("vacancy_scale_px", 8.0),
                   vacancy_power=d.get("vacancy_power", 1.0),
                   notes=d.get("notes", "")) for d in src]


# Emission is parameterised by (min spacing, emitted DENSITY per 1000 scored pixels), not by
# a support quantile.  Density is the quantity the metric actually charges for, and it is
# directly comparable across folds of different size and across the reference artifacts: the
# Owner-reported H33-2-B2 raster has 37,654 positive pixels; 7.37/1000 is its descriptive
# density on the local scored grid. The participant DTI-to-raster mapping is unverified; this
# is a geometry-matched research reference, not an incumbent or score anchor.
OWNER_REFERENCE_DENSITY = 7.37


def operating_points(quick: bool) -> tuple[list[float], list[float], list[float]]:
    if quick:
        return [2.0, 2.8, 4.5], [2.0, 7.37, 20.0], [0.0, 2.0]
    return ([2.0, 2.8, 4.0],
            [2.0, 4.0, 7.37, 14.0, 24.0, 40.0],
            [0.0, 2.0])


# --------------------------------------------------------------------------- folds
# Prevalence-matched instruments. The 5,764..15,179 truth-size bracket in older evidence was
# inverted from owner-reported scores and unverified file mappings; it is an assumption-dependent
# scenario, not a measured or organizer-verified hidden-truth range. PM* folds test those scenario
# prevalences only. They do not identify private labels or justify an upload.
PM_PREVALENCES = {"PM0112": 0.00112, "PM0200": 0.00200, "PM0294": 0.00294}


def build_blocks(g: Grid, comp_lab: np.ndarray, n_comp: int, sizes: np.ndarray,
                 comp_kind: np.ndarray, n_rows: int, n_cols: int, seed: int = 0) -> list[dict]:
    """Whole-component, spatially-blocked, prevalence-matched folds for every instrument."""
    fid = g.spatial_folds(n_rows, n_cols)
    objs = ndi.find_objects(comp_lab)
    comp_block = np.full(n_comp + 1, -1, np.int32)
    for c in range(1, n_comp + 1):
        sl = objs[c - 1]
        sel = comp_lab[sl] == c
        vals, counts = np.unique(fid[sl][sel], return_counts=True)
        comp_block[c] = int(vals[np.argmax(counts)])
    rng = np.random.default_rng(seed)
    folds = []
    for k in range(n_rows * n_cols):
        region = (fid == k) & g.footprint
        if region.sum() < 5000:
            continue
        ys, xs = np.nonzero(region)
        crop = (int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1)
        in_block = np.nonzero((comp_block == k) & (np.arange(n_comp + 1) > 0))[0]
        truth = dict(
            A1=np.isin(comp_lab, in_block[comp_kind[in_block] == 1]) & region,
            A2=np.isin(comp_lab, in_block[comp_kind[in_block] == 2]) & region,
        )
        truth["AA"] = np.isin(comp_lab, in_block) & region
        sizes_in = sizes[in_block]
        for name, prev in PM_PREVALENCES.items():
            target = round(prev * float(region.sum()))
            order = rng.permutation(in_block.size)
            keep, acc, nkept = [], 0, 0
            for j in order:
                if acc >= target:
                    break
                keep.append(in_block[j]); acc += int(sizes_in[j]); nkept += 1
            truth[name] = np.isin(comp_lab, np.array(keep, dtype=comp_lab.dtype)) & region
            truth[name + "_ncomp"] = nkept
            truth[name + "_target_px"] = target
        folds.append(dict(k=k, crop=crop, region=region,
                          n_components=int(in_block.size), truth=truth))
    return folds


def score_binary(pred: np.ndarray, truth: np.ndarray, k_near: np.ndarray, n_truth: int) -> dict:
    """Exact binary DTI with the truth-side distance transform supplied (cached per fold)."""
    s = float(pred.sum())
    if n_truth == 0 or s == 0.0:
        return dict(tp=0.0, fp=s, fn=float(n_truth), n_truth=n_truth,
                    dti=0.0, coverage=0.0, S=s, M=0.0)
    tp = float(M.kernel(ndi.distance_transform_edt(~pred))[truth].sum())
    m = float(k_near[pred].sum())
    fp = s - m
    fn = float(n_truth) - tp
    denom = tp + M.ALPHA * fp + M.BETA * fn + M.EPS_METRIC
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n_truth, dti=float(tp / denom),
                coverage=float(tp / n_truth), S=s, M=m)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--blocks", type=int, default=5, help="blocks per side")
    ap.add_argument("--instruments", default="PM0200,PM0112,PM0294,A1,A2")
    ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--out", default=str(EV / "sweep_a.json"))
    args = ap.parse_args()
    t0 = time.time()
    EV.mkdir(parents=True, exist_ok=True)

    g = Grid()
    valid = np.load(SURF / "valid.npy")
    isolated = np.load(SURF / "A1_isolated.npy")
    flanking = np.load(SURF / "A2_flanking.npy")
    bands = Bands(DATA / "training_features.tif")

    comp_lab, n_comp = ndi.label(g.catalogue, structure=STRUCT8)
    sizes = np.bincount(comp_lab.ravel(), minlength=n_comp + 1)
    comp_kind = np.zeros(n_comp + 1, np.int8)
    iso_ids = np.unique(comp_lab[isolated]); iso_ids = iso_ids[iso_ids > 0]
    fla_ids = np.unique(comp_lab[flanking]); fla_ids = fla_ids[fla_ids > 0]
    comp_kind[iso_ids] = 1
    comp_kind[fla_ids] = 2
    assert int((comp_kind == 0).sum()) == 1, "every catalogue component must be A1 or A2"
    folds = build_blocks(g, comp_lab, n_comp, sizes, comp_kind, args.blocks, args.blocks,
                         seed=args.seed)
    print(f"[folds] {len(folds)} spatial blocks, {n_comp} components "
          f"(A1 isolated {int((comp_kind==1).sum()-1)}, A2 flanking {int((comp_kind==2).sum()-1)}) "
          f"({time.time()-t0:.0f}s)")
    for f in folds:
        print(f"   block {f['k']:2d} crop={f['crop']} comps={f['n_components']} "
              f"A1={int(f['truth']['A1'].sum())} A2={int(f['truth']['A2'].sum())} "
              f"PM0200={int(f['truth']['PM0200'].sum())} px")

    insts = args.instruments.split(",")
    n_blocks = len(folds)
    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(n_blocks)
    n_cal = n_blocks // 2
    calib = sorted(int(i) for i in perm[:n_cal])
    select = sorted(int(i) for i in perm[n_cal:])
    print(f"[split] calibration block indices {calib}")
    print(f"[split] selection   block indices {select}")

    recs = recipes(args.quick)
    spacings, qs, flanks = operating_points(args.quick)
    print(f"[sweep] {len(recs)} recipes x {len(spacings)} spacings x {len(qs)} densities "
          f"x {len(flanks)} flank buffers x {len(insts)} instruments x {n_blocks} blocks")

    # ---- global, label-free parts of each recipe (cached: scarp at r=9 costs ~25 s each)
    cores, regs = {}, {}
    for r in recs:
        cores[r.name] = build_core(r, bands, valid)["core"]
        rg = regional_gate(bands, valid, r.regional_bands, r.regional_sigma_px,
                           r.regional_power)
        if rg is not None:
            cores[r.name] = (cores[r.name] * rg).astype(np.float32)
        regs[r.name] = None
        print(f"[core] {r.name}: {len(r.terms)} terms  ({time.time()-t0:.0f}s)")

    # ---- conditional geometry reference: owner-reported H33-2-B2 raster; score association unverified
    owner_reference = None
    ip = DATA / "reference" / "scored_h33-2-b2_0.2778.tif"
    if ip.exists():
        with rasterio.open(ip) as ds:
            owner_reference = np.nan_to_num(ds.read(1).astype(np.float32)) > 0

    rows: list[dict] = []
    for bi, f in enumerate(folds):
        y0, y1, x0, x1 = f["crop"]
        for inst in insts:
            truth_full = f["truth"][inst]
            if truth_full.sum() < 30:
                continue
            visible = g.catalogue & ~truth_full
            d_vis = ndi.distance_transform_edt(~visible).astype(np.float32)
            # intersect with `valid`: 3,073 footprint pixels carry the float32 nodata sentinel
            # in at least one band (evidence/footprint_vs_feature_valid.json).  The field is 0
            # there, and leaving them in the scored domain both wastes budget and creates an
            # exact-tie plateau.  build_submission_s3.py uses the same domain, so the holdout and
            # the shipped raster are scored on identical rules.
            scored = f["region"] & ~visible & valid
            truth = truth_full[y0:y1, x0:x1]
            scored_c = scored[y0:y1, x0:x1]
            dvis_c = d_vis[y0:y1, x0:x1]
            n_truth = int(truth.sum())
            k_near = M.kernel(ndi.distance_transform_edt(~truth))

            # every loop variable this closure reads is bound as a default argument: B023 is
            # not a style complaint here, it is the difference between scoring fold k and
            # silently scoring whatever the loop variables hold when the closure is called.
            def record(name, op, mask, extra=None, _truth=truth, _k_near=k_near,
                       _n_truth=n_truth, _f=f, _inst=inst, _bi=bi, _scored_c=scored_c):
                r = score_binary(mask, _truth, _k_near, _n_truth)
                rows.append(dict(block=int(_f["k"]), instrument=_inst, recipe=name,
                                 half=("calibration" if _bi in calib else "selection"),
                                 block_index=_bi,
                                 op=op, dti=r["dti"], tp=r["tp"], fp=r["fp"], S=r["S"], M=r["M"],
                                 coverage=r["coverage"], n_truth=_n_truth,
                                 emitted=int(mask.sum()), n_scored=int(_scored_c.sum()),
                                 **(extra or {})))

            if owner_reference is not None:
                record("REF_owner_reported_H33_2_B2_unverified", "owner-supplied raster geometry",
                       owner_reference[y0:y1, x0:x1] & scored_c)

            for rec in recs:
                core = cores[rec.name]
                if rec.use_vacancy:
                    vg = vacancy_gate(bands, valid, visible, cores[rec.name],
                                      rec.vacancy_scale_px, rec.vacancy_power)
                    core = core * vg["gate"]
                fc = np.where(valid, np.clip(core, 0, 1), 0.0).astype(np.float32)[y0:y1, x0:x1]
                n_scored = int(scored_c.sum())
                # The flank buffer is applied to the SUPPORT, not after thinning: a candidate
                # within b of the visible catalogue is never emitted, and the budget is spent
                # on what remains.  Pruning after thinning instead would confound "the pruned
                # mass was worthless" with "pruning simply emitted less", and the whole point
                # of comparing b=0 with b>0 at MATCHED density is to separate those.
                flank_masks = {b: (scored_c if b <= 0 else (scored_c & (dvis_c > b)))
                               for b in flanks}
                for b in flanks:
                    emask = flank_masks[b]
                    for s in spacings:
                        for dens in qs:
                            budget = round(dens * n_scored / 1000.0)
                            em = E.emit(fc, emask, min_dist=s, support_q=1.0, blur="none",
                                        budget=budget)
                            record(rec.name, f"s{s:g}_d{dens:g}_b{b:g}", em["mask"],
                                   dict(min_dist=s, density_per_1000=dens, flank_b=b,
                                        budget=budget, n_thinned=em["n_thinned"],
                                        n_support=em["n_support"],
                                        emitted_before_flank=int(em["mask"].sum())))
        print(f"[sweep] block {f['k']} ({bi+1}/{len(folds)}) done, {len(rows)} rows  "
              f"({time.time()-t0:.0f}s)")

    out = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               seconds=round(time.time() - t0, 1), quick=args.quick,
               blocks_per_side=args.blocks, n_blocks=n_blocks,
               calibration_block_indices=calib, selection_block_indices=select,
               instruments=insts, recipes=[r.to_dict() for r in recs],
               spacings=spacings, densities_per_1000=qs, flank_buffers=flanks,
               owner_reference_density_per_1000=OWNER_REFERENCE_DENSITY,
               fold_report=[dict(k=f["k"], crop=list(f["crop"]), n_components=f["n_components"],
                                 **{n: int(f["truth"][n].sum()) for n in
                                    ("A1", "A2", "AA", "PM0112", "PM0200", "PM0294")},
                                 **{n + "_ncomp": f["truth"][n + "_ncomp"]
                                    for n in PM_PREVALENCES},
                                 realised_prevalence={n: round(
                                     f["truth"][n].sum() / max(int(f["region"].sum()), 1), 6)
                                     for n in PM_PREVALENCES}) for f in folds],
               n_rows=len(rows), rows=rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out))
    print(f"\nwrote {args.out}: {len(rows)} rows  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
