#!/usr/bin/env python3
"""H49 sweep: does strike-aligned thinning (H49-A) or polarity coherence (H49-B) beat the control?

Design is frozen in ``docs/research/h49-hypotheses-preregistered.md``.  In one sentence:

  five prevalence-matched instruments (the same ones the round-2 sweep used) x a finer 8x8 spatial
  blocking x three recipes (frozen control R2_scarp9_topo, R2 + polarity, polarity only) x two
  emitters (the incumbent isotropic ``nms_disk`` and the new strike-aligned ``nms_oriented``) x a
  spacing/density grid, each scored with the exact DTI on the block's held-out truth, with a
  seeded half of the blocks reserved for CERTIFICATION and never used for a choice.

Everything that defines a row is label-free except the truth of the fold it is scored on; the
visible catalogue is exactly what the organiser leaves visible, and the fold's held-out truth is
removed from it before the emission domain is built.

Run:  python3 scripts/run_sweep_h49.py [--quick] [--blocks N] [--out PATH]
Out:  evidence/sweep/sweep_h49.json  (+ a console table)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47s3 import emission as E
from gems47s3 import metric as M
from gems47s3.detector import Bands, Recipe, build_core
from gems47s3.geomorph import orientation
from gems47s3.grid import Grid

STRUCT8 = np.ones((3, 3), bool)
EV = ROOT / "evidence" / "sweep"


def data_dir() -> Path:
    env = os.environ.get("GEMS_DATA_DIR", "").strip()
    if env:
        return Path(env)
    local = ROOT / "data"
    if (local / "training_features.tif").is_file():
        return local
    return ROOT / ".cache" / "gems_data"


def scratch_dir() -> Path:
    d = ROOT / ".cache" / "h49"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------- recipes
DEFAULT_RECIPES = [
    dict(name="R2_scarp9_topo",   # frozen control: the round-2 winner
         terms=[["det_elev_slope", "scarp", 9, 3.0], ["det_elev_slope", "curv", 2.5, 1.0],
                ["det_elev_slope", "detrend", 2.5, 1.0], ["det_elev_slope", "slope_var", 5, 1.0]],
         notes="unchanged from scripts/run_sweep_a.py; the control arm of this experiment"),
    dict(name="R7_scarp9_polarity",
         terms=[["det_elev_slope", "scarp", 9, 3.0], ["det_elev_slope", "polarity", 9, 2.0],
                ["det_elev_slope", "curv", 2.5, 1.0], ["det_elev_slope", "detrend", 2.5, 1.0],
                ["det_elev_slope", "slope_var", 5, 1.0]],
         notes="H49-B: control recipe plus signed two-scale polarity coherence at half the scarp weight"),
    dict(name="R8_polarity_only",
         terms=[["det_elev_slope", "polarity", 9, 1.0]],
         notes="H49-B ablation: the polarity transform alone, no unsigned scarp term"),
]

# The emitters under test.  "disk" is the incumbent isotropic rule; "oriented" is H49-A with the
# exclusion ellipse elongated ACROSS the strike, which is the only direction the metric does not pay
# for twice.
EMITTERS = {
    "disk": dict(kind="disk"),
    "oriented4": dict(kind="oriented", across=4.0),
}


def recipes(quick: bool) -> list[Recipe]:
    src = DEFAULT_RECIPES[:2] if quick else DEFAULT_RECIPES
    out = []
    for d in src:
        out.append(Recipe(name=d["name"],
                          terms=[(b, t, float(r), float(w)) for b, t, r, w in d["terms"]],
                          notes=d["notes"]))
    return out


def operating_points(quick: bool) -> tuple[list[float], list[float], list[float]]:
    if quick:
        return [2.8], [7.37], [2.0]
    # The catalogue-flank buffer is part of the operating point because the organiser's own nested
    # pair (h27-4 -> h33-2-b2, 0.2708 -> 0.2778) shows the family gained +0.0070 by deleting mass
    # within 200 m of the catalogue -- and staff state there is NO buffer around known faults, while
    # new-fault pixels MAY lie within 300 m of one.  2.0 px is the round-2 value (control); 3.0 px is
    # the metric's own kernel radius, the largest defensible exclusion.
    return [2.8, 3.6], [4.0, 7.37, 14.0], [2.0, 3.0]


# --------------------------------------------------------------------------- instruments
PM_PREVALENCES = {"PM0112": 0.00112, "PM0200": 0.00200, "PM0294": 0.00294}
INSTRUMENTS = ("PM0200", "PM0112", "PM0294", "A1", "A2")


def component_kinds(g: Grid) -> tuple[np.ndarray, np.ndarray, int, np.ndarray]:
    """8-connected catalogue components and the A1-isolated / A2-flanking split.

    Definition copied from ``scripts/measure_instruments.py`` so the two instruments mean the same
    thing here as in the round-2 sweep: a component is FLANKING if its 300 m dilation touches a
    different component, and ISOLATED otherwise.
    """
    cat = g.catalogue
    comp_lab, n_comp = ndi.label(cat, structure=STRUCT8)
    sizes = np.bincount(comp_lab.ravel(), minlength=n_comp + 1)
    dilated = ndi.binary_dilation(cat, iterations=3, structure=STRUCT8)
    dil_lab, n_dil = ndi.label(dilated, structure=STRUCT8)
    ys, xs = np.nonzero(cat)
    dl, cl = dil_lab[ys, xs], comp_lab[ys, xs]
    order = np.argsort(dl, kind="stable")
    dl_s, cl_s = dl[order], cl[order]
    bounds = np.searchsorted(dl_s, np.arange(n_dil + 2))
    comp_is_flanking = np.zeros(n_comp + 1, bool)
    for b in range(1, n_dil + 1):
        seg = cl_s[bounds[b]:bounds[b + 1]]
        if seg.size and np.unique(seg).size > 1:
            comp_is_flanking[np.unique(seg)] = True
    kind = np.zeros(n_comp + 1, np.int8)
    kind[comp_is_flanking] = 2
    kind[(np.arange(n_comp + 1) > 0) & ~comp_is_flanking] = 1
    return comp_lab, kind, n_comp, sizes


def build_blocks(g: Grid, comp_lab: np.ndarray, kind: np.ndarray, n_comp: int,
                 sizes: np.ndarray, blocks_per_side: int, seed: int,
                 min_region: int = 5_000, min_truth: int = 30, margin: int = 16) -> list[dict]:
    """Whole-component, spatially-blocked, prevalence-matched folds (instrument definitions kept
    identical to scripts/run_sweep_a.py; only the block count changes).

    Every array stored on a fold is CROPPED to the block (plus a ``margin`` pixel frame, which is
    wider than the 2 px flank buffer and the 3 px metric kernel).  Storing full-grid masks for 39
    folds x 6 instruments costs ~2.9 GB and OOM-killed the first run of this script on a 3.9 GB
    machine; the cropped form is ~45 MB in total and is exactly equivalent for every quantity the
    sweep measures, because nothing outside the block can affect a score inside it.
    """
    fid = g.spatial_folds(blocks_per_side, blocks_per_side)
    objs = ndi.find_objects(comp_lab)
    comp_block = np.full(n_comp + 1, -1, np.int32)
    for c in range(1, n_comp + 1):
        sl = objs[c - 1]
        sel = comp_lab[sl] == c
        vals, counts = np.unique(fid[sl][sel], return_counts=True)
        comp_block[c] = int(vals[np.argmax(counts)])
    rng = np.random.default_rng(seed)
    folds = []
    for k in range(blocks_per_side * blocks_per_side):
        region = (fid == k) & g.footprint
        if int(region.sum()) < min_region:
            continue
        in_block = np.nonzero((comp_block == k) & (np.arange(n_comp + 1) > 0))[0]
        if in_block.size == 0:
            continue
        ys, xs = np.nonzero(region)
        y0 = max(0, int(ys.min()) - margin); y1 = min(g.shape[0], int(ys.max()) + 1 + margin)
        x0 = max(0, int(xs.min()) - margin); x1 = min(g.shape[1], int(xs.max()) + 1 + margin)
        crop = (y0, y1, x0, x1)
        cs = (slice(y0, y1), slice(x0, x1))
        inner = (slice(int(ys.min()) - y0, int(ys.max()) + 1 - y0),
                 slice(int(xs.min()) - x0, int(xs.max()) + 1 - x0))
        truth = {
            "A1": (np.isin(comp_lab, in_block[kind[in_block] == 1]) & region)[cs].copy(),
            "A2": (np.isin(comp_lab, in_block[kind[in_block] == 2]) & region)[cs].copy(),
        }
        truth["AA"] = (np.isin(comp_lab, in_block) & region)[cs].copy()
        sizes_in = sizes[in_block]
        for name, prev in PM_PREVALENCES.items():
            target = round(prev * float(region.sum()))
            keep, acc, nkept = [], 0, 0
            for j in rng.permutation(in_block.size):
                if acc >= target:
                    break
                keep.append(in_block[j])
                acc += int(sizes_in[j])
                nkept += 1
            truth[name] = (np.isin(comp_lab, np.array(keep, dtype=comp_lab.dtype))
                           & region)[cs].copy()
            truth[name + "_ncomp"] = nkept
        # `.copy()` is load-bearing: a slice of a full-grid boolean array is a VIEW that keeps the
        # 12.3 M-pixel parent alive.  39 folds x 7 views retained 3.2 GB and OOM-killed this script.
        folds.append(dict(k=k, crop=crop, inner=inner, region=region[cs].copy(),
                          n_components=int(in_block.size), truth=truth,
                          n_region_px=int(region.sum())))
    usable = [f for f in folds if max(int(f["truth"][i].sum()) for i in INSTRUMENTS) >= min_truth]
    return usable


def score_binary(pred: np.ndarray, truth: np.ndarray, k_near: np.ndarray, n_truth: int) -> dict:
    s = float(pred.sum())
    if n_truth == 0 or s == 0.0:
        return dict(tp=0.0, fp=s, fn=float(n_truth), n_truth=n_truth, dti=0.0,
                    coverage=0.0, S=s, M=0.0)
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
    ap.add_argument("--blocks", type=int, default=8, help="blocks per side (8 -> 64 cells)")
    ap.add_argument("--seed", type=int, default=20261007)
    ap.add_argument("--out", default=str(EV / "sweep_h49.json"))
    args = ap.parse_args()
    t0 = time.time()
    EV.mkdir(parents=True, exist_ok=True)
    scratch = scratch_dir()

    dd = data_dir()
    print(f"[data] {dd}")
    g = Grid(dd)
    print(f"[grid] footprint {int(g.footprint.sum())}  catalogue {int(g.catalogue.sum())}")

    vpath = scratch / "valid.npy"
    if vpath.exists():
        valid = np.load(vpath)
        print(f"[grid] valid.npy cached: {int(valid.sum())} px")
    else:
        valid = g.all_bands_finite()
        np.save(vpath, valid)
        print(f"[grid] all-19-bands-finite {int(valid.sum())} px  ({time.time()-t0:.0f}s)")

    comp_lab, kind, n_comp, sizes = component_kinds(g)
    print(f"[A1/A2] components {n_comp}: isolated {int((kind == 1).sum())}, "
          f"flanking {int((kind == 2).sum())}")
    folds = build_blocks(g, comp_lab, kind, n_comp, sizes, args.blocks, args.seed)
    n_blocks = len(folds)
    perm = np.random.default_rng(args.seed).permutation(n_blocks)
    n_cal = n_blocks // 2
    calib = sorted(int(i) for i in perm[:n_cal])
    select = sorted(int(i) for i in perm[n_cal:])
    print(f"[blocks] {n_blocks} usable of {args.blocks ** 2} cells")
    print(f"[split] calibration {calib}")
    print(f"[split] selection   {select}")

    bands = Bands(dd / "training_features.tif")
    recs = recipes(args.quick)
    cores, thetas = {}, {}
    import resource as _res

    def _rss():
        return round(_res.getrusage(_res.RUSAGE_SELF).ru_maxrss / 1024.0, 1)

    for r in recs:
        print(f"[core] building {r.name} (rss {_rss()} MB)", flush=True)
        core = build_core(r, bands, valid)["core"]
        print(f"[core] built {r.name} (rss {_rss()} MB)", flush=True)
        cores[r.name] = core
        theta, coh = orientation(core, 2.0)
        thetas[r.name] = theta
        print(f"[core] {r.name}: {len(r.terms)} terms, median coherence "
              f"{float(np.median(coh[valid])):.3f}  ({time.time()-t0:.0f}s)")
    rnd_field = np.random.default_rng(args.seed + 1).random(core.shape).astype(np.float32)

    incumbent = None
    ip = dd / "reference" / "h33-2-b2-zeros.tif"
    if not ip.exists():
        ip = dd / "reference" / "scored_h33-2-b2_0.2778.tif"
    if ip.exists():
        import rasterio
        with rasterio.open(ip) as ds:
            incumbent = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
        print(f"[ref] incumbent {ip.name}: {int(incumbent.sum())} positive px")

    spacings, densities, flanks = operating_points(args.quick)
    cat_c = g.catalogue
    valid_c = valid
    rows: list[dict] = []
    for bi, f in enumerate(folds):
        y0, y1, x0, x1 = f["crop"]
        cat_crop = cat_c[y0:y1, x0:x1]
        valid_crop = valid_c[y0:y1, x0:x1]
        region_c = f["region"]
        for inst in INSTRUMENTS:
            truth = f["truth"][inst]
            if int(truth.sum()) < 30:
                continue
            # The visible catalogue is the full catalogue MINUS this fold's held-out truth; the
            # distance transform is evaluated on the crop frame, which is 16 px wider than the
            # block, so the 2 px flank buffer is exact for every pixel scored.
            visible_crop = cat_crop & ~truth
            d_vis_crop = ndi.distance_transform_edt(~visible_crop).astype(np.float32)
            scored_c = region_c & ~visible_crop & valid_crop
            n_scored = int(scored_c.sum())
            n_truth = int(truth.sum())
            k_near = M.kernel(ndi.distance_transform_edt(~truth))

            def record(recipe, emitter, op, mask, extra=None, _truth=truth, _k_near=k_near,
                       _n_truth=n_truth, _f=f, _inst=inst, _bi=bi, _n_scored=n_scored):
                r = score_binary(mask, _truth, _k_near, _n_truth)
                rows.append(dict(block=int(_f["k"]), instrument=_inst, recipe=recipe,
                                 emitter=emitter, op=op,
                                 half=("calibration" if _bi in calib else "selection"),
                                 block_index=_bi, dti=r["dti"], tp=r["tp"], fp=r["fp"],
                                 S=r["S"], M=r["M"], coverage=r["coverage"], n_truth=_n_truth,
                                 emitted=int(mask.sum()), n_scored=_n_scored, **(extra or {})))

            if incumbent is not None:
                record("REF_incumbent_0.2778", "as-shipped", "as-shipped",
                       incumbent[y0:y1, x0:x1] & scored_c, dict(budget=None))

            rf = rnd_field[y0:y1, x0:x1]
            for r in recs:
                core = cores[r.name][y0:y1, x0:x1]
                th = thetas[r.name][y0:y1, x0:x1]
                for s in spacings:
                    for dens in densities:
                        budget = round(dens * n_scored / 1000.0)
                        for fb in flanks:
                            emask = scored_c & (d_vis_crop > fb)
                            op = f"s{s:g}_d{dens:g}_b{fb:g}"
                            for ename, espec in EMITTERS.items():
                                if espec["kind"] == "disk":
                                    mask = E.nms_disk(core, emask, s)
                                else:
                                    mask = E.nms_oriented(core, emask, s,
                                                          float(espec["across"]), th)
                                n_thinned = int(mask.sum())
                                if n_thinned > budget:
                                    mask = E.topk_mask(np.where(mask, core, -np.inf), budget, mask)
                                record(r.name, ename, op, mask,
                                       dict(min_dist=s, density_per_1000=dens, flank_b=fb,
                                            across=espec.get("across"),
                                            budget=budget, n_thinned=n_thinned))
            # fixed-seed spaced random control, at the same budget and spacing, ONCE per fold
            for s in spacings:
                for dens in densities:
                    budget = round(dens * n_scored / 1000.0)
                    for fb in flanks:
                        emask = scored_c & (d_vis_crop > fb)
                        rmask = E.nms_disk(rf, emask, s)
                        if int(rmask.sum()) > budget:
                            rmask = E.topk_mask(np.where(rmask, rf, -np.inf), budget, rmask)
                        record("RANDOM_fixed_seed", "disk", f"s{s:g}_d{dens:g}_b{fb:g}", rmask,
                               dict(min_dist=s, density_per_1000=dens, flank_b=fb,
                                    budget=budget))
        print(f"[sweep] block {f['k']} ({bi + 1}/{n_blocks}) rows={len(rows)}  "
              f"({time.time()-t0:.0f}s)")

    out = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               seconds=round(time.time() - t0, 1), quick=args.quick,
               blocks_per_side=args.blocks, n_blocks=n_blocks,
               calibration_block_indices=calib, selection_block_indices=select,
               instruments=list(INSTRUMENTS),
               recipes=[r.to_dict() for r in recs],
               emitters={k: v for k, v in EMITTERS.items()},
               spacings=spacings, densities_per_1000=densities, flank_buffers_px=flanks,
               data_dir=str(dd),
               fold_report=[dict(k=f["k"], crop=list(f["crop"]), n_components=f["n_components"],
                                 **{n: int(f["truth"][n].sum()) for n in ("A1", "A2", "AA")},
                                 **{n: int(f["truth"][n].sum()) for n in PM_PREVALENCES},
                                 realised_prevalence={n: round(
                                     f["truth"][n].sum() / max(int(f["region"].sum()), 1), 6)
                                     for n in PM_PREVALENCES}) for f in folds],
               rows=rows)
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(f"\nwrote {args.out}  ({len(rows)} rows, {time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
