#!/usr/bin/env python3
"""SUPERSEDED by scripts/run_sweep_a.py -- kept because it produced the measurement that
superseded it.

This script scores the sweep against INSTRUMENT B: whole components of USGS SGMC traces lying
> 300 m from the given catalogue.  knowledge/02_the_two_instruments_measure_different_populations.md
records why that instrument was rejected -- those traces are exposed mountain bedrock (median
detrended elevation +115 m, median det_elev_slope 13.0, median depth-to-basement 105 m) while the
given expert-mapped Quaternary catalogue is near background on all three (-69 m, 5.1, 321 m).  The
populations are nearly disjoint in terrain space, so selecting against Instrument B builds a
bedrock-contact detector -- the documented false-positive mode of fault-mapping models in this
province (Hermant et al. 2025).  `height_only` reaches precision-at-40k 0.3325 on Instrument B,
better than any fault-specific transform tried, which is decisive.

Everything below this header is the original Instrument-B sweep.  Run scripts/run_sweep_a.py for
the selection instrument actually used.

--- original docstring ---
The spacing/buffer/blur sweep scored on the spatially-blocked, density-matched holdout.

This produces the calibration data the split-conformal selector consumes: a sequence of
operating points, each scored against holdout DTI on B spatial blocks, with the blocks
divided into a calibration half (used to choose) and a selection half (used only to audit).

Run:  python3 scripts/run_sweep.py [--quick] [--blocks 4] [--prevalences p0112,p0200,p0294]
Out:  evidence/sweep/sweep_results.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47s3 import emission as E
from gems47s3 import metric as M
from gems47s3.holdout import PREVALENCE_TARGETS, build_folds, offcatalogue_enrichment

SURF = ROOT / "data" / "surfaces"
REF = ROOT / "data" / "reference"
EV = ROOT / "evidence" / "sweep"


def load(name: str) -> np.ndarray:
    return np.load(SURF / name)


# --------------------------------------------------------------------------- field variants
def ecdf(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Rank-normalise ``a`` over ``valid`` to a uniform [0,1] marginal.

    Rank space, not clipped-z space: the two H47-A densities have very different shapes
    (physics lineament density is smooth and unimodal, catalogue trace density is spiky and
    zero over most of the grid), so a difference of robust z-scores is dominated by that
    shape mismatch.  Mapping both to a common uniform marginal makes the residual a
    statement about relative rank, which is what the hypothesis actually claims.
    """
    v = valid & np.isfinite(a)
    out = np.zeros(a.shape, np.float32)
    if v.sum() < 100:
        return out
    vals = a[v]
    srt = np.sort(vals)
    out[v] = (np.searchsorted(srt, a[v], side="left") / float(srt.size)).astype(np.float32)
    return out


def field_variants(g, valid, block_catalogue_visible, per_block_cache) -> dict:
    """Combine the cached H47 surfaces into the field variants under test.

    ``block_catalogue_visible`` is the catalogue the detector is allowed to see on this
    block (the held-out components are removed), so H47-A cannot leak the fold truth.
    """
    corr_mean = load("corr_mean.npy")
    corr_max = load("corr_max.npy")
    corr_count = load("corr_count.npy")
    B_braid = load("B_braid.npy")
    C_asym = load("C_drain_asym.npy")
    C_mag = load("C_drain_mag.npy")
    D_strain = load("D_strain.npy")
    E_base = load("E_basement.npy")
    E_pers = load("E_persistence.npy")
    E_flip = load("E_signflip.npy")

    if "A" not in per_block_cache:
        # physics lineament density and catalogue trace density at a MATCHED 8-px (800 m) scale
        d_fp = ndi.gaussian_filter(g.footprint.astype(np.float32), 8.0, mode="nearest")
        d_fp = np.maximum(d_fp, 1e-6)
        phys = ndi.gaussian_filter(np.where(valid, corr_mean, 0.0).astype(np.float32),
                                   8.0, mode="nearest") / d_fp
        cat = ndi.gaussian_filter(block_catalogue_visible.astype(np.float32),
                                  8.0, mode="nearest") / d_fp
        Rp = ecdf(phys, valid)                    # physics rank   in [0,1]
        Rc = ecdf(cat, valid)                     # catalogue rank in [0,1]
        # H47-A in two forms: a signed rank residual and the product ("physics high AND
        # catalogue absent"), which is the form the hypothesis actually states.
        per_block_cache["A_resid"] = np.clip(Rp - Rc, 0.0, 1.0).astype(np.float32)
        per_block_cache["A_prod"] = (Rp * (1.0 - Rc)).astype(np.float32)
        per_block_cache["Rp"] = Rp
        per_block_cache["Rc"] = Rc
    A_resid = per_block_cache["A_resid"]
    A_prod = per_block_cache["A_prod"]
    corr_gate = np.clip(corr_count / 5.0, 0.0, 1.0).astype(np.float32)

    gm = lambda *xs: np.exp(np.mean([np.log(np.clip(x, 1e-4, None)) for x in xs],
                                    axis=0)).astype(np.float32)
    out = {}
    # V1 baseline: multi-physics corroboration only (the family's consensus idea, re-derived)
    out["V1_corr"] = (0.5 * corr_mean + 0.5 * corr_max).astype(np.float32)
    # V2: H47-A(product) x H47-B braid -- mapping gap gated by damage-zone multimodality
    out["V2_Aprod_B"] = gm(A_prod + 0.05, np.clip(B_braid, 0, 1) + 0.15)
    # V3 PRIMARY: H47-A(product) x corroboration max x along-strike persistence
    out["V3_Aprod_corr_pers"] = gm(A_prod + 0.05, corr_max + 0.10, np.clip(E_pers, 0, 1) + 0.25)
    # V4: all five hypotheses, product form
    out["V4_all5"] = gm(A_prod + 0.05, np.clip(B_braid, 0, 1) + 0.15,
                        np.maximum(C_asym, C_mag) + 0.15, D_strain + 0.10, E_base + 0.10)
    # V5: physics only, NO catalogue geometry (isolates H47-A's contribution)
    out["V5_noA"] = gm(np.clip(B_braid, 0, 1) + 0.15, corr_max + 0.10,
                       np.maximum(C_asym, C_mag) + 0.15, D_strain + 0.10, E_base + 0.10)
    # V6: accommodation-zone locator (H47-E sign flip) gated by corroboration
    out["V6_signflip"] = gm(E_flip + 0.10, corr_max + 0.10, np.clip(B_braid, 0, 1) + 0.20)
    # V7: H47-A signed rank residual variant (tests product vs residual form)
    out["V7_Aresid_corr"] = gm(A_resid + 0.05, corr_max + 0.10, np.clip(E_pers, 0, 1) + 0.25)
    # V8: corroboration-count hard gate (>= 3 of 5 families) x H47-A product
    out["V8_gate3_Aprod"] = np.where(corr_gate >= 0.6, A_prod, 0.02 * A_prod).astype(np.float32)
    return out


def operating_points(quick: bool) -> list[dict]:
    if quick:
        grid = dict(spacings=[2.0, 2.8, 4.5], qs=[0.01, 0.03], flanks=[0.0, 2.0],
                    blurs=[("oriented", 2.0, 0.5)])
    else:
        grid = dict(spacings=[1.5, 2.0, 2.8, 3.5, 4.5, 6.0], qs=[0.008, 0.02, 0.05],
                    flanks=[0.0, 1.0, 2.0, 3.0],
                    blurs=[("none", 0.0, 0.0), ("oriented", 2.0, 0.5), ("oriented", 4.0, 0.0),
                           ("isotropic", 1.85, 1.85)])
    ops = []
    for s in grid["spacings"]:
        for q in grid["qs"]:
            for b in grid["flanks"]:
                for blur, sa, sc in grid["blurs"]:
                    ops.append(dict(name=f"s{s:g}_q{q:g}_b{b:g}_{blur}{sa:g}x{sc:g}",
                                    min_dist=s, support_q=q, flank_b=b, blur=blur,
                                    sigma_along=sa, sigma_across=sc))
    return ops


def score_on_fold(pred_full: np.ndarray, fold, ) -> dict:
    """Exact DTI of a full-grid prediction restricted to one block's scored domain."""
    y0, y1, x0, x1 = fold._crop
    p = pred_full[y0:y1, x0:x1]
    truth = fold.truth[y0:y1, x0:x1]
    scored = fold.scored[y0:y1, x0:x1]
    r = M.dti(np.where(scored, p, 0.0).astype(np.float32), truth, valid=scored)
    r.update(fold=fold.k, prevalence=fold.prevalence, n_truth=fold.n_truth)
    return r


def add_crop(folds):
    """Attach a tight crop box to each fold so scoring never touches the whole grid."""
    for f in folds:
        ys, xs = np.nonzero(f.region)
        f._crop = (int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1)
    return folds


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--blocks", type=int, default=4, help="blocks per side (blocks = n^2)")
    ap.add_argument("--prevalences", default="p0112,p0200,p0294")
    ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--out", default=str(EV / "sweep_results.json"))
    args = ap.parse_args()

    t0 = time.time()
    EV.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "src"))
    from gems47s3.grid import Grid
    g = Grid()
    valid = load("valid.npy")
    d_cat_full = load("d_catalogue.npy")
    theta = load("theta.npy")
    coherence = load("coherence.npy")

    prevs = args.prevalences.split(",")
    for p in prevs:
        assert p in PREVALENCE_TARGETS, p

    # ------------------------------------------------------------- holdout blocks
    folds_by_prev = {p: add_crop(build_folds(g, args.blocks, args.blocks, p, args.seed))
                     for p in prevs}
    block_report = {}
    for p, folds in folds_by_prev.items():
        block_report[p] = [dict(block=f.k, region_px=int(f.region.sum()),
                                n_truth=f.n_truth, n_known=int(f.known.sum()),
                                components_truth=f.n_components_truth,
                                components_available=f.n_components_total,
                                realised_prevalence=round(f.n_truth / max(int(f.region.sum()), 1), 6))
                           for f in folds]
        print(f"[folds:{p}] {len(folds)} blocks, truth px "
              f"{[f.n_truth for f in folds]}  ({time.time()-t0:.0f}s)")

    # calibration / selection split of the BLOCKS (this is the unit of exchangeability)
    n_blocks = len(folds_by_prev[prevs[0]])
    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(n_blocks)
    n_cal = n_blocks // 2
    calib_idx = sorted(int(i) for i in perm[:n_cal])
    select_idx = sorted(int(i) for i in perm[n_cal:])
    print(f"[split] calibration blocks {calib_idx}   selection blocks {select_idx}")

    ops = operating_points(args.quick)
    print(f"[sweep] {len(ops)} operating points")

    # ------------------------------------------------------------- reference: incumbent artifact
    incumbent = None
    inc_path = REF / "scored_h33-2-b2_0.2778.tif"
    if inc_path.exists():
        import rasterio
        with rasterio.open(inc_path) as ds:
            a = ds.read(1)
        incumbent = (np.nan_to_num(a.astype(np.float32)) > 0)
        print(f"[reference] incumbent 0.2778 artifact loaded: {int(incumbent.sum())} px")

    results = []
    variant_names = None
    for p in prevs:
        folds = folds_by_prev[p]
        for fi, fold in enumerate(folds):
            y0, y1, x0, x1 = fold._crop
            # the detector sees only the catalogue that is NOT held out on this block
            visible_cat = g.catalogue & ~fold.truth
            cache = {}
            fields = field_variants(g, valid, visible_cat, cache)
            if variant_names is None:
                variant_names = list(fields)
            scored_sub = fold.scored[y0:y1, x0:x1]
            dcat_sub = d_cat_full[y0:y1, x0:x1]
            theta_sub = theta[y0:y1, x0:x1]
            coh_sub = coherence[y0:y1, x0:x1]
            truth_sub = fold.truth[y0:y1, x0:x1]

            # off-catalogue enrichment gate (second, independent instrument)
            prior_path = REF / "derived_sgmc_faults_100m_u8.tif"
            enrich = {}
            if prior_path.exists() and fi == 0:
                import rasterio
                with rasterio.open(prior_path) as ds:
                    prior = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
                class _G:  # minimal duck-typed grid for the enrichment helper
                    footprint = g.footprint[y0:y1, x0:x1]
                    d_catalogue = d_cat_full[y0:y1, x0:x1]
                for vn, fv in fields.items():
                    enrich[vn] = offcatalogue_enrichment(fv[y0:y1, x0:x1], _G(), prior[y0:y1, x0:x1])

            for vn, fv in fields.items():
                fsub = fv[y0:y1, x0:x1]
                for op in ops:
                    em = E.emit(fsub, scored_sub, min_dist=op["min_dist"],
                                support_q=op["support_q"], d_catalogue=dcat_sub,
                                flank_b=op["flank_b"], blur=op["blur"],
                                sigma_along=op["sigma_along"], sigma_across=op["sigma_across"],
                                theta=theta_sub, coherence=coh_sub, engine="nms")
                    pred = em["mask"].astype(np.float32)
                    r = M.dti(pred, truth_sub, valid=scored_sub)
                    results.append(dict(
                        prevalence=p, block=int(fold.k), block_index=fi,
                        half=("calibration" if fi in calib_idx else "selection"),
                        variant=vn, op=op["name"], **{k: op[k] for k in
                                                      ("min_dist", "support_q", "flank_b",
                                                       "blur", "sigma_along", "sigma_across")},
                        dti=float(r["dti"]), tp=float(r["tp"]), fp=float(r["fp"]),
                        n_truth=int(r["n_truth"]), emitted=int(em["n_after_flank"]),
                        emitted_before_flank=int(em["n_before_flank"]),
                        coverage=float(r["coverage"]),
                        offcat_enrichment=(enrich.get(vn, {}).get("enrichment_vs_uniform")
                                           if p == prevs[0] and fi == 0 else None),
                    ))
            if incumbent is not None:
                inc_sub = incumbent[y0:y1, x0:x1] & scored_sub
                r = M.dti(inc_sub.astype(np.float32), truth_sub, valid=scored_sub)
                results.append(dict(prevalence=p, block=int(fold.k), block_index=fi,
                                    half=("calibration" if fi in calib_idx else "selection"),
                                    variant="REF_incumbent_0.2778", op="as-shipped",
                                    min_dist=None, support_q=None, flank_b=None, blur=None,
                                    sigma_along=None, sigma_across=None,
                                    dti=float(r["dti"]), tp=float(r["tp"]), fp=float(r["fp"]),
                                    n_truth=int(r["n_truth"]), emitted=int(inc_sub.sum()),
                                    emitted_before_flank=int(inc_sub.sum()),
                                    coverage=float(r["coverage"]), offcat_enrichment=None))
            print(f"[sweep:{p}] block {fold.k} ({fi+1}/{len(folds)}) done  "
                  f"{len(results)} rows  ({time.time()-t0:.0f}s)")

    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        seconds=round(time.time() - t0, 1),
        blocks_per_side=args.blocks, n_blocks=n_blocks,
        calibration_blocks=calib_idx, selection_blocks=select_idx,
        prevalences=prevs, prevalence_targets=PREVALENCE_TARGETS,
        variants=variant_names, operating_points=[o["name"] for o in ops],
        block_report=block_report, rows=results,
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out))
    print(f"\nwrote {args.out}: {len(results)} rows, {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
