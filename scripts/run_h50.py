#!/usr/bin/env python3
"""Exploratory H50 sweep on previously inspected H49 public-proxy blocks.

This does NOT establish fresh holdout superiority or authorize a submission.
The corrected protocol audit is docs/research/h50-hypotheses-preregistered.md.
Quotas are upper bounds, not exact matched masses. SGMC targets are not private
competition truth. A fixed selection-only choice precedes calibration arithmetic.
"""
from __future__ import annotations

import argparse
import csv
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
from gems47s3 import geomorph as G
from gems47s3 import metric as M
from gems47s3.detector import Bands, Recipe, build_core
from gems47s3.grid import Grid
from gems47s3.holdout import build_offcatalogue_folds

EV = ROOT / "evidence" / "h50"
SEED = 20261007
ALPHA = 0.10
SPACINGS = [1.5, 2.8, 3.6, 4.6, 5.8]
DENSITY = 7.37
FLANKS = [2.0, 3.0]
SIGMA_SCATTER = 1.85  # px, GEMSDOE28 H28 owner-report-derived MODEL parameter (not a measurement)


def rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)


def data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / ".cache" / "gems_data"


# --------------------------------------------------------------------------- H50 inputs
def reservoir_corridor_prior(dd: Path, valid: np.ndarray) -> dict:
    """H50-1: continuous reservoir-temperature corridor prior from GDR well/spring rows.

    Weight per station cell = clip((T_used - 30) / 170, 0, 1) with T_used the median of the
    available geothermometer estimates (quartz/chalcedony/cation) when >=1 exists, else temp_c.
    The label-derived column dist_known_fault_px is NEVER read. Rows outside the grid are skipped.
    """
    h, w = valid.shape
    acc = np.zeros((h, w), np.float64)
    n_used = 0
    n_skipped = 0
    with open(dd / "external" / "gdr_wellspring_in_footprint.csv") as fh:
        for row in csv.DictReader(fh):
            try:
                r = int(row["row"]); c = int(row["col"])
            except (KeyError, ValueError):
                n_skipped += 1
                continue
            if not (0 <= r < h and 0 <= c < w):
                n_skipped += 1
                continue
            ests = []
            for key in ("geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
                v = row.get(key, "")
                if v not in ("", "nan", "NULL", "None"):
                    try:
                        fv = float(v)
                    except ValueError:
                        continue
                    if 0.0 <= fv <= 300.0:
                        ests.append(fv)
            t_used = float(np.median(ests)) if ests else None
            if t_used is None:
                v = row.get("temp_c", "")
                if v in ("", "nan", "NULL", "None"):
                    n_skipped += 1
                    continue
                try:
                    t_used = float(v)
                except ValueError:
                    n_skipped += 1
                    continue
            if not np.isfinite(t_used):
                n_skipped += 1
                continue
            acc[r, c] = max(acc[r, c], float(np.clip((t_used - 30.0) / 170.0, 0.0, 1.0)))
            n_used += 1
    blurred = ndi.gaussian_filter(acc.astype(np.float32), 40.0, mode="nearest")
    prior = G.rank_scale(np.where(valid, blurred, np.nan)).astype(np.float32)
    return dict(prior=prior, n_rows_used=n_used, n_rows_skipped=n_skipped,
                n_cells_nonzero=int((acc > 0).sum()),
                raw_sum=float(acc.sum()), blurred_max=float(blurred.max()))


def kth_ridge_term(dd: Path, valid: np.ndarray) -> tuple[np.ndarray, dict]:
    """H50-2: K/Th alteration-ratio across-strike step ridge (GeoDAWN radiometrics, u8 mirror)."""
    with rasterio.open(dd / "external" / "geodawn_rad_u8.tif") as ds:
        k = ds.read(1).astype(np.float32)
        th = ds.read(2).astype(np.float32)
    z = np.log1p(k) - np.log1p(th)
    z = ndi.gaussian_filter(z, 2.0, mode="nearest")
    step = np.asarray(G.scarp_step(z, 5), np.float32)
    term = G.rank_scale(np.where(valid & np.isfinite(step), step, np.nan)).astype(np.float32)
    return term, dict(source="external/geodawn_rad_u8.tif bands K,Th (u8 quantised mirror)",
                      transform="scarp_step(log(K+1)-log(Th+1), 5) after sigma=2 smoothing")


def combine_terms(terms_weights: list[tuple[np.ndarray, float]], valid: np.ndarray) -> np.ndarray:
    logacc = np.zeros(valid.shape, np.float64)
    wsum = 0.0
    for t, w in terms_weights:
        logacc += float(w) * np.log(np.clip(t, 1e-6, None))
        wsum += float(w)
    core = np.exp(logacc / max(wsum, 1e-9)).astype(np.float32)
    return np.where(valid, G.rank_scale(np.where(valid, core, np.nan)), 0.0).astype(np.float32)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks-limit", type=int, default=0)
    ap.add_argument("--out", default=str(EV / "h50_validation.json"))
    args = ap.parse_args()
    t0 = time.time()
    EV.mkdir(parents=True, exist_ok=True)
    dd = data_dir()

    g = Grid(dd)
    valid = g.all_bands_finite()
    print(f"[data] footprint {int(g.footprint.sum())}  catalogue {int(g.catalogue.sum())}  "
          f"valid {int(valid.sum())}  (rss {rss_mb()} MB)", flush=True)

    with rasterio.open(dd / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
    prior_truth = g.footprint & sgmc
    folds = build_offcatalogue_folds(g, prior_truth, n_rows=8, n_cols=8, prevalence="p0200",
                                     seed=SEED, min_cat_dist=3.0)
    folds = [f for f in folds if int(f.truth.sum()) >= 30]
    if args.blocks_limit:
        folds = folds[: args.blocks_limit]
    n_blocks = len(folds)
    truth_px = [int(f.truth.sum()) for f in folds]
    print(f"[B] folds {n_blocks}; truth px min/med/max {min(truth_px)}/{int(np.median(truth_px))}/"
          f"{max(truth_px)}; total {sum(truth_px)}", flush=True)

    perm = np.random.default_rng(SEED).permutation(n_blocks)
    n_cal = n_blocks // 2
    calib_idx = sorted(int(i) for i in perm[:n_cal])
    select_idx = sorted(int(i) for i in perm[n_cal:])
    print(f"[split] selection {select_idx}", flush=True)
    print(f"[split] calibration {calib_idx}", flush=True)

    # ------------------------------------------------------------------ fields
    r7_recipe = Recipe(name="R7_scarp9_polarity",
                       terms=[("det_elev_slope", "scarp", 9.0, 3.0),
                              ("det_elev_slope", "polarity", 9.0, 2.0),
                              ("det_elev_slope", "curv", 2.5, 1.0),
                              ("det_elev_slope", "detrend", 2.5, 1.0),
                              ("det_elev_slope", "slope_var", 5.0, 1.0)])
    r2_recipe = Recipe(name="R2_scarp9_topo",
                       terms=[("det_elev_slope", "scarp", 9.0, 3.0),
                              ("det_elev_slope", "curv", 2.5, 1.0),
                              ("det_elev_slope", "detrend", 2.5, 1.0),
                              ("det_elev_slope", "slope_var", 5.0, 1.0)])
    bands = Bands(dd / "training_features.tif")
    print("[field] building R7 terms", flush=True)
    r7_built = build_core(r7_recipe, bands, valid, want_terms=True)
    r7_core = r7_built["core"]
    r2_core = build_core(r2_recipe, bands, valid)["core"]
    print(f"[field] R2/R7 done ({time.time()-t0:.0f}s, rss {rss_mb()} MB)", flush=True)

    corr_meta = reservoir_corridor_prior(dd, valid)
    corr_prior = corr_meta["prior"]
    print(f"[field] H50-1 corridor prior: "
          f"{ {k: v for k, v in corr_meta.items() if k != 'prior'} }", flush=True)
    kth_term, kth_meta = kth_ridge_term(dd, valid)
    print(f"[field] H50-2 K/Th ridge term: {kth_meta}", flush=True)

    t = r7_built["terms"]
    s = t["det_elev_slope:scarp:9"]
    p = t["det_elev_slope:polarity:9"]
    c = t["det_elev_slope:curv:2.5"]
    dtr = t["det_elev_slope:detrend:2.5"]
    sv = t["det_elev_slope:slope_var:5"]
    h50b_core = combine_terms([(s, 3.0), (p, 2.0), (c, 1.0), (dtr, 1.0), (sv, 1.0), (kth_term, 1.5)],
                              valid)
    floor = 0.35
    h50a_core = combine_terms([(r7_core, 1.0)], valid) * (floor + (1.0 - floor) * corr_prior)
    h50a_core = np.where(valid, G.rank_scale(np.where(valid, h50a_core, np.nan)), 0.0).astype(np.float32)
    h50c_core = h50b_core * (floor + (1.0 - floor) * corr_prior)
    h50c_core = np.where(valid, G.rank_scale(np.where(valid, h50c_core, np.nan)), 0.0).astype(np.float32)

    fields = {"R2_scarp9_topo": r2_core, "R7_scarp9_polarity": r7_core,
              "H50a_corridor": h50a_core, "H50b_kth_ridge": h50b_core, "H50c_both": h50c_core}
    blurred = {}
    for name, f in fields.items():
        blurred[name] = ndi.gaussian_filter(f, SIGMA_SCATTER, mode="nearest").astype(np.float32)
    print(f"[field] all arms built ({time.time()-t0:.0f}s, rss {rss_mb()} MB)", flush=True)

    rnd_field = np.random.default_rng(SEED + 1).random(r7_core.shape).astype(np.float32)

    # ------------------------------------------------------------------ sweep
    rows: list[dict] = []
    for bi, f in enumerate(folds):
        y0, y1, x0, x1 = f._crop
        truth = f.truth[y0:y1, x0:x1]
        scored_c = f.scored[y0:y1, x0:x1] & valid[y0:y1, x0:x1]
        n_scored = int(scored_c.sum())
        n_truth = int(truth.sum())
        d_vis_crop = g.d_catalogue[y0:y1, x0:x1]
        half = "calibration" if bi in calib_idx else "selection"

        def record(arm, emitter, spacing, fb, mask, extra=None, *,
                   truth=truth, scored_c=scored_c, f=f, bi=bi, half=half,
                   n_truth=n_truth, n_scored=n_scored):
            r = M.dti_binary(mask, truth, valid=scored_c)
            rows.append(dict(block=int(f.k), block_index=bi, half=half, arm=arm,
                             emitter=emitter, spacing_px=spacing, flank_b=fb,
                             dti=float(r["dti"]), tp=float(r["tp"]), fp=float(r["fp"]),
                             S=float(r["S"]), M=float(r["M"]), coverage=float(r["coverage"]),
                             n_truth=n_truth, emitted=int(mask.sum()), n_scored=n_scored,
                             **(extra or {})))

        budget = round(DENSITY * n_scored / 1000.0)
        for arm, field in fields.items():
            for s_px in SPACINGS:
                for fb in FLANKS:
                    emask = scored_c & (d_vis_crop > fb)
                    mask = E.nms_disk(field[y0:y1, x0:x1], emask, s_px)
                    if int(mask.sum()) > budget:
                        mask = E.topk_mask(np.where(mask, field[y0:y1, x0:x1], -np.inf), budget, mask)
                    record(arm, "disk", s_px, fb, mask, dict(budget=budget))
                    mask_b = E.nms_disk(blurred[arm][y0:y1, x0:x1], emask, s_px)
                    if int(mask_b.sum()) > budget:
                        mask_b = E.topk_mask(np.where(mask_b, blurred[arm][y0:y1, x0:x1], -np.inf),
                                             budget, mask_b)
                    record(arm, "blur185", s_px, fb, mask_b, dict(budget=budget))
        rf = rnd_field[y0:y1, x0:x1]
        for s_px in SPACINGS:
            for fb in FLANKS:
                emask = scored_c & (d_vis_crop > fb)
                rm = E.nms_disk(rf, emask, s_px)
                if int(rm.sum()) > budget:
                    rm = E.topk_mask(np.where(rm, rf, -np.inf), budget, rm)
                record("RANDOM_fixed_seed", "disk", s_px, fb, rm, dict(budget=budget))
        print(f"[sweep] block {f.k} ({bi+1}/{n_blocks}) rows={len(rows)} ({time.time()-t0:.0f}s)",
              flush=True)

    # write the flat spacing history CSV (the "score history" the conformal step consumes)
    csv_path = EV / "spacing_sweep_h50.csv"
    with csv_path.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    # ------------------------------------------------------------------ selection + conformal
    def mean_dti(arm, emitter, spacing, fb, half_name):
        vals = [r["dti"] for r in rows
                if r["arm"] == arm and r["emitter"] == emitter and r["spacing_px"] == spacing
                and r["flank_b"] == fb and r["half"] == half_name]
        return (float(np.mean(vals)), len(vals)) if vals else (float("nan"), 0)

    cands = []
    for arm in fields:
        for emitter in ("disk", "blur185"):
            for s_px in SPACINGS:
                for fb in FLANKS:
                    m_sel, n_sel = mean_dti(arm, emitter, s_px, fb, "selection")
                    m_cal, n_cal = mean_dti(arm, emitter, s_px, fb, "calibration")
                    cands.append(dict(arm=arm, emitter=emitter, spacing_px=s_px, flank_b=fb,
                                      selection_mean=m_sel, calibration_mean=m_cal,
                                      n_selection=n_sel, n_calibration=n_cal))
    cands.sort(key=lambda d: (-d["selection_mean"], d["spacing_px"], d["arm"]))
    chosen = cands[0]

    # current holdout best reference (H49 report) and local control reproduction
    ref_h49 = 0.10329
    r7_rep = [c for c in cands if c["arm"] == "R7_scarp9_polarity" and c["emitter"] == "disk"
              and c["spacing_px"] == 2.8 and c["flank_b"] == 3.0][0]
    rnd_rows = [r["dti"] for r in rows if r["arm"] == "RANDOM_fixed_seed"
                and r["spacing_px"] == chosen["spacing_px"] and r["flank_b"] == chosen["flank_b"]
                and r["half"] == "selection"]
    rnd_mean = float(np.mean(rnd_rows)) if rnd_rows else float("nan")

    cal_vals = sorted(r["dti"] for r in rows
                      if r["arm"] == chosen["arm"] and r["emitter"] == chosen["emitter"]
                      and r["spacing_px"] == chosen["spacing_px"] and r["flank_b"] == chosen["flank_b"]
                      and r["half"] == "calibration")
    n = len(cal_vals)
    k = int(np.floor(ALPHA * (n + 1)))
    floor_dti = cal_vals[k - 1] if k >= 1 else 0.0
    coverage = (n + 1 - k) / (n + 1)
    sel_vals = sorted(r["dti"] for r in rows
                      if r["arm"] == chosen["arm"] and r["emitter"] == chosen["emitter"]
                      and r["spacing_px"] == chosen["spacing_px"] and r["flank_b"] == chosen["flank_b"]
                      and r["half"] == "selection")

    gate_beats_holdout_best = bool(chosen["selection_mean"] > max(ref_h49, r7_rep["selection_mean"]))
    gate_positive_floor = bool(floor_dti > 0.0)
    gate_beats_random = bool(chosen["selection_mean"] > 3.0 * rnd_mean)
    gate_pass = False  # reused validation and unsupported exchangeability cannot authorize a slot

    cert = dict(
        formal_coverage_established=False,
        caveat="Previously inspected H49 blocks reused; not a fresh holdout. Export is not this pipeline.",
        method="split conformal one-sided lower prediction bound (Lei et al., JASA 2018)",
        nominal_level=1 - ALPHA, alpha=ALPHA,
        exchangeability_unit="8x8 spatial block (Instrument B)",
        n_calibration_blocks=n, order_statistic_k=k,
        rank_coverage=(n + 1 - k) / (n + 1),
        lower_bound_estimate=float(floor_dti),
        calibration_dti_sorted=cal_vals,
        selection_dti_sorted=sel_vals,
        scope=("assumption-conditional on unverified block-score exchangeability of the public "
               "SGMC-off-catalogue proxy; NOT a guarantee for private labels, map-wide DTI or "
               "any leaderboard score"),
    )

    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        seconds=round(time.time() - t0, 1),
        protocol="docs/research/h50-hypotheses-preregistered.md",
        seed=SEED, spacings_px=SPACINGS, density_per_1000=DENSITY, flank_buffers_px=FLANKS,
        sigma_scatter_px=SIGMA_SCATTER,
        instrument=("B: USGS SGMC > 300 m from given catalogue, whole components, p0200, "
                    "8x8 folds, catalogue masked"),
        n_blocks=n_blocks,
        selection_block_indices=select_idx, calibration_block_indices=calib_idx,
        h50_inputs=dict(corridor_prior={k: v for k, v in corr_meta.items() if k != "prior"},
                        kth_ridge=kth_meta),
        field_weights=dict(R7=dict(scarp=3, polarity=2, curv=1, detrend=1, slope_var=1),
                           H50b_extra=dict(kth_ridge=1.5, total=9.5),
                           corridor_prior=dict(floor=0.35, weight=0.65, sigma_px=40.0)),
        candidates=cands[:20],
        chosen=chosen,
        r7_operating_point_reproduction=r7_rep,
        h49_reported_holdout_best_selection_mean=ref_h49,
        random_selection_mean=rnd_mean,
        conformal=cert,
        gate=dict(beats_holdout_best=gate_beats_holdout_best,
                  positive_conformal_floor=gate_positive_floor,
                  beats_random_by_3x=gate_beats_random, passed=gate_pass),
        rows_file=str(csv_path),
        n_rows=len(rows),
        scope_notice=("public proxy measurements only; no leaderboard score, projection or slot "
                      "authorization"),
    )
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(f"\nchosen: {chosen}", flush=True)
    print(f"conformal floor {floor_dti:.5f} at rank {coverage:.3f} (k={k}, n={n})", flush=True)
    print(f"gate: {out['gate']}", flush=True)
    print(f"wrote {args.out} + {csv_path} ({len(rows)} rows, {time.time()-t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
