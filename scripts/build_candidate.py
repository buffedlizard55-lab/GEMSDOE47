#!/usr/bin/env python3
"""Build, validate and rank the GEMSDOE47 submission candidates.

Arms
  A  flank-augmented  q = LATI fit on {proximity-to-d2.8, catalogue halo 0-1.5 px}
                      the LOO-best model in evidence/flank_test.json
  B  pure-geological  q = LATI fit on {catalogue halo 0-1.5, halo 1.5-3, SGMC
                      off-catalogue proximity, RTP gradient, TMI gradient}
                      contains NO reference to any previous submission
  C  incumbent        the live-0.2600 d2.8 raster, reproduced from bytes (baseline)
  D  h33-2-b2         the reported-0.2778 raster, reproduced from bytes (baseline)

Emission: greedy on the exact marginal rule  dT*(1/DTI - alpha) > alpha*dF,
support-confined, with live coverage deduction (see src/gems47/emitter.py).

Frames used to rank (none of them is the organiser's hidden truth):
  1. LATI  - the fitted q itself; the only frame calibrated on real returns
  2. SGMC  - USGS SGMC faults >300 m off the given catalogue (official, independent)
  3. CATQ  - blocked catalogue holdout, scored WITHOUT the organiser's mask
             (contaminated; reported for continuity with the sibling repos)
  4. distinctness vs all 14 known prior rasters

    python3 scripts/build_candidate.py [--arms A,B] [--budget 150000]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47 import emitter as E
from gems47 import features as FEAT
from gems47 import grid as G
from gems47 import lati
from gems47 import metric as M
from gems47.scripts_common import rank_u8_inplace
from gems47.submission import validate_submission, write_submission

K_LO, K_HI, BMAX, L2 = 2_000.0, 120_000.0, 12.0, 1e-5

ARM_LAYERS = {
    "A": ["prox_d2.8", "dcat_band_0_1.5"],
    "B": ["dcat_band_0_1.5", "dcat_band_1.5_3", "sgmc_offcat_prox", "rtp_grad", "tmi_grad"],
}


def prox_layer(obs, oid, ev_idx, shape, cap=40.0):
    o = [x for x in obs if x.id == oid][0]
    H, W = shape
    m = np.zeros(H * W, bool)
    m[o.dot_flat] = True
    return rank_u8_inplace((-FEAT.dist_px(m.reshape(H, W), cap).ravel()[ev_idx]).astype(np.float32))


def fit_q(arm, obs, U, names, ev_idx, shape):
    keys = ARM_LAYERS[arm]
    rows = []
    for k in keys:
        rows.append(prox_layer(obs, "d2.8", ev_idx, shape) if k == "prox_d2.8"
                    else U[names.index(k)])
    Ux = np.stack(rows)
    L = {1: 256, 2: 64, 3: 32, 4: 20, 5: 14}[len(keys)]
    bm = lati.BinnedSoftmax(Ux, list(range(len(keys))), obs, L)
    f = bm.fit(l2=L2, bmax=BMAX, k_lo=K_LO, k_hi=K_HI)
    pred = bm.predict(np.array(f["theta"]))
    f["ssr"] = float(np.sum((pred - bm.dti_obs) ** 2))
    loo = 0.0
    for h in range(len(obs)):
        sub = [i for i in range(len(obs)) if i != h]
        g = bm.fit(l2=L2, subset=sub, theta0=np.array(f["theta"]), bmax=BMAX, k_lo=K_LO, k_hi=K_HI)
        loo += float(bm.predict(np.array(g["theta"]))[h] - bm.dti_obs[h]) ** 2
    # dense q on the evaluated pixel set
    eta = np.zeros(Ux.shape[1], np.float64)
    for jj in range(len(keys)):
        eta += f["theta"][1 + jj] * (Ux[jj].astype(np.float64) / 255.0 - 0.5)
    s = np.exp(eta - eta.max())
    q_ev = f["theta"][0] * s / s.sum()
    q = np.zeros(shape[0] * shape[1], np.float64)
    q[ev_idx] = q_ev
    f["loo_ssr"] = loo
    f["layers"] = keys
    return q.reshape(shape), f, bm


def catq_frames(t):
    H, W = t.shape
    folds = {"NW": (slice(0, H // 2), slice(0, W // 2)), "NE": (slice(0, H // 2), slice(W // 2, W)),
             "SW": (slice(H // 2, H), slice(0, W // 2)), "SE": (slice(H // 2, H), slice(W // 2, W))}
    out = {}
    for k, (sy, sx) in folds.items():
        tr = np.zeros((H, W), bool)
        tr[sy, sx] = t.catalogue[sy, sx]
        out[k] = tr
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="A,B")
    ap.add_argument("--budget", type=int, default=150_000)
    ap.add_argument("--matched", type=int, default=44_090)
    ap.add_argument("--outdir", default=str(ROOT / "docs" / "downloads"))
    ap.add_argument("--slug", default="gems47")
    args = ap.parse_args()
    t0 = time.time()

    t = G.load_template()
    ev = t.evaluated
    obs = lati.load_observations(verbose=False)
    st = FEAT.build_stack(verbose=False)
    U, names, ev_idx, shape = st["U"], list(st["names"]), st["ev_idx"], tuple(st["meta"]["shape"])

    with rasterio.open(G.data_dir() / "external" / "derived_sgmc_faults_100m_u8.tif") as s:
        sgmc = s.read(1) > 0
    dcat = FEAT.dist_px(t.catalogue, 80.0)
    truth_sgmc = sgmc & ev & (dcat > M.RANGE_PX)
    catq = catq_frames(t)
    print(f"[frames] SGMC off-catalogue truth = {int(truth_sgmc.sum()):,} px; "
          f"catalogue folds = {[int(v.sum()) for v in catq.values()]}")

    # baselines reproduced from bytes
    prior = {}
    for o in obs:
        m = np.zeros(shape[0] * shape[1], bool)
        m[o.dot_flat] = True
        prior[f"prior_{o.id}"] = (m.reshape(shape), o.dti)
    h33 = ROOT.parent / "refs" / "GEMSDOE32" / "docs" / "downloads" / \
        "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    if h33.exists():
        with rasterio.open(h33) as s:
            prior["prior_h33-2-b2"] = (np.nan_to_num(s.read(1)) > 0, 0.2778)
    print(f"[frames] {len(prior)} prior rasters available for distinctness")

    results = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "frames": {"sgmc_offcatalogue_K": int(truth_sgmc.sum()),
                          "catalogue_fold_K": {k: int(v.sum()) for k, v in catq.items()}},
               "arms": []}

    def evaluate(label, dots, extra=None):
        p = np.where(ev & dots, 1.0, 0.0)
        sg = M.score(p, truth_sgmc, ev).as_dict()
        cq = {k: round(M.score(p, tr, t.footprint).DTI, 6) for k, tr in catq.items()}
        # LATI-frame DTI is computed by the caller (needs q); here: distinctness
        dis = {}
        for nm, (pd, _) in prior.items():
            inter = int((pd & dots).sum())
            dis[nm] = dict(intersection=inter,
                           jaccard=round(inter / max(int((pd | dots).sum()), 1), 6),
                           frac_of_new=round(inter / max(int(dots.sum()), 1), 6))
        row = dict(arm=label, n_dots=int(dots.sum()),
                   on_catalogue=int((dots & t.catalogue).sum()),
                   outside_footprint=int((dots & ~t.footprint).sum()),
                   in_flank_0_3px=int((dots & ev & (dcat > 0) & (dcat <= 3.0)).sum()),
                   in_flank_0_1_5px=int((dots & ev & (dcat > 0) & (dcat <= 1.5)).sum()),
                   on_sgmc_offcat=int((dots & truth_sgmc).sum()),
                   sgmc_frame_dti=round(sg["DTI"], 6), sgmc_T=round(sg["TP_w"], 1),
                   sgmc_F=round(sg["FP_w"], 1), sgmc_recall=round(sg["weighted_recall"], 5),
                   sgmc_credit_per_dot=round(sg["credit_per_unit_mass"], 5),
                   catq_fold_dti=cq, catq_mean=round(float(np.mean(list(cq.values()))), 6),
                   distinctness=dis,
                   max_jaccard_vs_any_prior=round(max(v["jaccard"] for v in dis.values()), 6),
                   max_frac_overlap_vs_any_prior=round(max(v["frac_of_new"] for v in dis.values()), 6))
        if extra:
            row.update(extra)
        return row

    # ---- baselines ---------------------------------------------------------
    for nm in ("prior_d2.8", "prior_h33-2-b2"):
        if nm in prior:
            dots, dti = prior[nm]
            row = evaluate(nm + f" (reported {dti})", dots)
            row["reported_live_dti"] = dti
            results["arms"].append(row)
            print(f"[base] {nm:<18} dots={row['n_dots']:>7,} flank0-3px={row['in_flank_0_3px']:>6,} "
                  f"SGMC-DTI={row['sgmc_frame_dti']:.4f} CATQ={row['catq_mean']:.4f}")

    # ---- LATI arms ---------------------------------------------------------
    for arm in [a.strip() for a in args.arms.split(",") if a.strip()]:
        q, f, bm = fit_q(arm, obs, U, names, ev_idx, shape)
        print(f"\n[arm {arm}] layers={f['layers']} theta={[round(v,3) for v in f['theta']]} "
              f"K={f['K']:,.0f} SSR={f['ssr']:.6f} LOO={f['loo_ssr']:.6f}")
        allowed = ev & (q > 0)
        # greedy emission, budget set by the metric's own marginal rule
        res = E.emit_greedy(q, allowed, budget=args.budget, dti_start=0.26, verbose=True)
        dots = res.dots
        p = np.where(ev & dots, 1.0, 0.0)
        T = float((E.credit_field(dots.astype(np.float64)) * q).sum())
        a = np.zeros(shape)
        for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
            a += k * E._shift(dots.astype(np.float64), dy, dx)
        Phi = float((q * a).sum())
        F = float(dots.sum()) - Phi
        K = float(q.sum())
        lati_dti = M.dti_from_TFK(T, F, K)
        extra = dict(lati_K=K, lati_T=round(T, 1), lati_F=round(F, 1),
                     lati_predicted_dti=round(lati_dti, 6),
                     lati_weighted_recall=round(T / K, 5),
                     lati_credit_per_dot=round(T / max(float(dots.sum()), 1), 5),
                     emission_stopped_by=res.stopped_by, budget=args.budget)
        row = evaluate(f"ARM-{arm} greedy (LATI)", dots, extra)
        results["arms"].append(row)
        print(f"[arm {arm}] greedy: dots={row['n_dots']:,} flank0-3px={row['in_flank_0_3px']:,} "
              f"LATI-DTI={lati_dti:.4f} SGMC-DTI={row['sgmc_frame_dti']:.4f} "
              f"CATQ={row['catq_mean']:.4f} maxjac={row['max_jaccard_vs_any_prior']:.4f} "
              f"stopped={res.stopped_by}")

        # matched-budget variant for an apples-to-apples comparison
        mb = E.emit_topk(q, allowed, args.matched)
        T2 = float((E.credit_field(mb.astype(np.float64)) * q).sum())
        a2 = np.zeros(shape)
        for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
            a2 += k * E._shift(mb.astype(np.float64), dy, dx)
        F2 = float(mb.sum()) - float((q * a2).sum())
        row2 = evaluate(f"ARM-{arm} top{args.matched} (LATI)", mb, dict(
            lati_K=K, lati_T=round(T2, 1), lati_F=round(F2, 1),
            lati_predicted_dti=round(M.dti_from_TFK(T2, F2, K), 6),
            lati_weighted_recall=round(T2 / K, 5),
            lati_credit_per_dot=round(T2 / args.matched, 5)))
        results["arms"].append(row2)
        print(f"[arm {arm}] top{args.matched}: flank0-3px={row2['in_flank_0_3px']:,} "
              f"LATI-DTI={row2['lati_predicted_dti']:.4f} SGMC-DTI={row2['sgmc_frame_dti']:.4f} "
              f"CATQ={row2['catq_mean']:.4f} maxjac={row2['max_jaccard_vs_any_prior']:.4f}")

        # write the primary arm's GeoTIFF
        if arm == args.arms.split(",")[0].strip():
            stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            base = (f"{args.slug}-h47{arm}-flank-reoccupation-{stamp}")
            outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
            for mode in ("zeros", "nan"):
                fn = outdir / f"{base}-{mode}.tif"
                write_submission(p if mode == "zeros" else
                                 np.where(t.footprint, p, np.nan), fn, mode=mode)
                v = validate_submission(fn)
                h = hashlib.sha256(fn.read_bytes()).hexdigest()
                results.setdefault("shipped", []).append(dict(
                    mode=mode, filename=fn.name, sha256=h, bytes=fn.stat().st_size,
                    validation=v))
                print(f"[ship] {fn.name}  {fn.stat().st_size:,} B  sha256={h[:16]}...  "
                      f"all_checks_passed={v['all_checks_passed']}")
            results["shipped_note"] = (
                f"GEMSDOE47 H47-{arm} flank-reoccupation | LATI-inverted belief field "
                f"({', '.join(f['layers'])}), K={K:,.0f}, greedy marginal-rule emission, "
                f"{row['n_dots']} dots of which {row['in_flank_0_3px']} in the 0-300 m "
                f"catalogue halo; LATI-predicted DTI {lati_dti:.4f}; UNSCORED")

    results["seconds"] = round(time.time() - t0, 1)
    (ROOT / "evidence" / "candidates.json").write_text(json.dumps(results, indent=1, default=float))
    print(f"\nwrote evidence/candidates.json ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
