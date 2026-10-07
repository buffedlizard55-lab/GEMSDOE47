#!/usr/bin/env python3
"""H49 Instrument-B sweep: the emission density/spacing response against INDEPENDENT faults.

Design is frozen in ``docs/research/h49b-instrument-b-preregistration.md`` before this file ran:

  * truth = USGS SGMC traces more than 300 m from the given catalogue, whole components only,
    prevalence-matched to p0200 inside each 8x8 block -- real faults the given catalogue does NOT
    contain, which is the population the organiser actually scores;
  * the given catalogue is masked in full inside every block, exactly as the organiser masks it, so
    the emission domain here IS the competition domain;
  * two frozen fields (R2_scarp9_topo control, R7_scarp9_polarity = H49-B), two emitters (isotropic
    ``nms_disk`` control and strike-aligned ``nms_oriented`` = H49-A) at identical emitted mass, a
    spacing x density x flank grid whose density range is deliberately extended upward because the
    first run's optimum sat on its upper boundary, and a fixed-seed spaced random control;
  * one seeded 50/50 split of the usable blocks into SELECTION and CALIBRATION halves, so the arm can
    be chosen on one half and certified on the other.

Run:  python3 scripts/run_sweep_h49b.py [--blocks-limit N] [--out PATH]
Out:  evidence/sweep/sweep_h49b.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import resource
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
from gems47s3.detector import Bands, build_core
from gems47s3.geomorph import orientation
from gems47s3.grid import Grid
from gems47s3.holdout import build_offcatalogue_folds

EV = ROOT / "evidence" / "sweep"
MARGIN = 16


def _load_sweep_module():
    spec = importlib.util.spec_from_file_location("sweep_h49", ROOT / "scripts" / "run_sweep_h49.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spacings", default="2.8")
    ap.add_argument("--densities", default="2,4,7.37,14,25,40")
    ap.add_argument("--flanks", default="2,3")
    ap.add_argument("--emitters", default="disk,oriented4")
    ap.add_argument("--recipes", default="R2_scarp9_topo,R7_scarp9_polarity")
    ap.add_argument("--prevalence", default="p0200")
    ap.add_argument("--seed", type=int, default=20261007)
    ap.add_argument("--blocks-limit", type=int, default=0)
    ap.add_argument("--out", default=str(EV / "sweep_h49b.json"))
    args = ap.parse_args()
    t0 = time.time()

    sw = _load_sweep_module()
    spacings = [float(x) for x in args.spacings.split(",")]
    densities = [float(x) for x in args.densities.split(",")]
    flanks = [float(x) for x in args.flanks.split(",")]
    emitters = {k: sw.EMITTERS[k] for k in args.emitters.split(",")}
    rec_names = [x for x in args.recipes.split(",") if x]
    recs = [r for r in sw.recipes(quick=False) if r.name in rec_names]

    dd = sw.data_dir()
    g = Grid(dd)
    valid = np.load(sw.scratch_dir() / "valid.npy")
    print(f"[data] {dd}  footprint {int(g.footprint.sum())}  catalogue {int(g.catalogue.sum())}  "
          f"valid {int(valid.sum())}  (rss {rss_mb()} MB)")

    with rasterio.open(dd / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
    prior = g.footprint & sgmc
    print(f"[B] SGMC in footprint {int(prior.sum())} px; "
          f"> 3 px from the catalogue {int((prior & (g.d_catalogue > 3.0)).sum())} px")

    folds = build_offcatalogue_folds(g, prior, n_rows=8, n_cols=8, prevalence=args.prevalence,
                                     seed=args.seed, min_cat_dist=3.0)
    folds = [f for f in folds if int(f.truth.sum()) >= 30]
    if args.blocks_limit:
        folds = folds[:args.blocks_limit]
    n_blocks = len(folds)
    truth_px = [int(f.truth.sum()) for f in folds]
    print(f"[B] folds: {n_blocks}; truth px min/median/max "
          f"{min(truth_px)}/{int(np.median(truth_px))}/{max(truth_px)}; "
          f"total truth {sum(truth_px)} px")
    perm = np.random.default_rng(args.seed).permutation(n_blocks)
    n_cal = n_blocks // 2
    calib = sorted(int(i) for i in perm[:n_cal])
    select = sorted(int(i) for i in perm[n_cal:])
    print(f"[split] calibration {calib}")
    print(f"[split] selection   {select}")

    bands = Bands(dd / "training_features.tif")
    cores, thetas = {}, {}
    for r in recs:
        print(f"[core] building {r.name} (rss {rss_mb()} MB)", flush=True)
        core = build_core(r, bands, valid)["core"]
        cores[r.name] = core
        theta, coh = orientation(core, 2.0)
        thetas[r.name] = theta
        print(f"[core] {r.name}: {len(r.terms)} terms, median coherence "
              f"{float(np.median(coh[valid])):.3f}  ({time.time() - t0:.0f}s, rss {rss_mb()} MB)")
    rnd_field = np.random.default_rng(args.seed + 1).random(core.shape).astype(np.float32)

    incumbent = None
    ip = dd / "reference" / "h33-2-b2-zeros.tif"
    if ip.exists():
        with rasterio.open(ip) as ds:
            incumbent = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
        print(f"[ref] incumbent {ip.name}: {int(incumbent.sum())} positive px")

    fid = g.spatial_folds(8, 8)
    rows: list[dict] = []
    for bi, f in enumerate(folds):
        k = int(f.k)
        y0, y1, x0, x1 = f._crop
        y0, y1 = max(0, y0 - MARGIN), min(g.catalogue.shape[0], y1 + MARGIN)
        x0, x1 = max(0, x0 - MARGIN), min(g.catalogue.shape[1], x1 + MARGIN)
        cat_crop = g.catalogue[y0:y1, x0:x1]
        valid_crop = valid[y0:y1, x0:x1]
        sl = (slice(y0, y1), slice(x0, x1))
        region_c = (fid == k)[sl]
        # the organiser masks the catalogue in full; here nothing is held back, because the truth
        # is a different compilation entirely
        d_cat_crop = ndi.distance_transform_edt(~cat_crop).astype(np.float32)
        scored_c = region_c & ~cat_crop & valid_crop
        n_scored = int(scored_c.sum())
        truth = f.truth[sl]
        n_truth = int(truth.sum())
        if n_scored < 1000 or n_truth < 20:
            continue
        k_near = M.kernel(ndi.distance_transform_edt(~truth))

        def record(recipe, emitter, op, mask, extra=None, _truth=truth, _k_near=k_near,
                   _n_truth=n_truth, _f=f, _bi=bi, _n_scored=n_scored):
            # score_binary is the sweep's single scoring path: TP_w = sum over truth of the exact
            # kernel weight of the nearest predicted pixel.  (metric.dti_binary takes ``valid`` /
            # ``known`` as its 3rd/4th arguments -- passing k_near and n_truth there silently
            # zeroed every row of the first B run.  Do not "simplify" this call.)
            r = sw.score_binary(mask, _truth, _k_near, _n_truth)
            rows.append(dict(block=int(_f.k), instrument="B_sgmc_offcat", recipe=recipe,
                             emitter=emitter, op=op,
                             half=("calibration" if _bi in calib else "selection"),
                             block_index=_bi, dti=r["dti"], tp=r["tp"], fp=r["fp"], S=r["S"],
                             M=r["M"], coverage=r["coverage"], n_truth=_n_truth,
                             emitted=int(mask.sum()), n_scored=_n_scored, **(extra or {})))

        if incumbent is not None:
            record("REF_incumbent_0.2778", "as-shipped", "as-shipped", incumbent[sl] & scored_c,
                   dict(budget=None))

        rf = rnd_field[sl]
        for r in recs:
            core = cores[r.name][sl]
            th = thetas[r.name][sl]
            for s in spacings:
                for dens in densities:
                    budget = round(dens * n_scored / 1000.0)
                    for fb in flanks:
                        emask = scored_c if fb <= 0 else (scored_c & (d_cat_crop > fb))
                        op = f"s{s:g}_d{dens:g}_b{fb:g}"
                        for ename, espec in emitters.items():
                            if espec["kind"] == "disk":
                                mask = E.nms_disk(core, emask, s)
                            else:
                                mask = E.nms_oriented(core, emask, s, float(espec["across"]), th)
                            n_thinned = int(mask.sum())
                            if n_thinned > budget:
                                mask = E.topk_mask(np.where(mask, core, -np.inf), budget, mask)
                            record(r.name, ename, op, mask,
                                   dict(min_dist=s, density_per_1000=dens, flank_b=fb,
                                        across=espec.get("across"), budget=budget,
                                        n_thinned=n_thinned))
        for s in spacings:
            for dens in densities:
                budget = round(dens * n_scored / 1000.0)
                for fb in flanks:
                    emask = scored_c if fb <= 0 else (scored_c & (d_cat_crop > fb))
                    rmask = E.nms_disk(rf, emask, s)
                    if int(rmask.sum()) > budget:
                        rmask = E.topk_mask(np.where(rmask, rf, -np.inf), budget, rmask)
                    record("RANDOM_fixed_seed", "disk", f"s{s:g}_d{dens:g}_b{fb:g}", rmask,
                           dict(min_dist=s, density_per_1000=dens, flank_b=fb, budget=budget))
        if not any(r["S"] for r in rows[-60:]):
            raise RuntimeError(f"every row of block {k} has zero emitted mass in the scored "
                               "domain -- scoring path is broken, refusing to write a bad sweep")
        print(f"[sweep] block {k} ({bi + 1}/{n_blocks}) truth={n_truth} scored={n_scored} "
              f"rows={len(rows)}  ({time.time() - t0:.0f}s, rss {rss_mb()} MB)", flush=True)

    out = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               seconds=round(time.time() - t0, 1), instrument="B_sgmc_offcat",
               prevalence=args.prevalence, min_cat_dist_px=3.0, seed=args.seed,
               blocks_per_side=8, n_blocks=n_blocks,
               calibration_block_indices=calib, selection_block_indices=select,
               recipes=[r.to_dict() for r in recs],
               emitters={k: v for k, v in emitters.items()},
               spacings=spacings, densities_per_1000=densities, flank_buffers_px=flanks,
               data_dir=str(dd), rows=rows)
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out))
    print(f"\nwrote {p}  ({len(rows)} rows, {time.time() - t0:.0f}s)  rss peak {rss_mb()} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
