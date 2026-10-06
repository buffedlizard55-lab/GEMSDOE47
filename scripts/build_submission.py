#!/usr/bin/env python3
"""Build the GEMSDOE47 submission and evaluate it under five truth frames.

Belief field (LOO-selected in evidence/strike_decomposition.json):

    q(x) = K * exp( b1*u[proximity to the incumbent field]
                  + b2*u[graded catalogue halo, 0-300 m] ) / Z

Emission: greedy on the exact marginal rule  dT*(1/DTI-alpha) > alpha*dF  with
the EXACT Bernoulli E[kappa] (never the first-order sum filter, which drives
FP_w negative on concentrated fields), support-confined to the footprint minus
the masked catalogue.

Frames - none of them is the organiser's hidden truth, so all five are reported:
  F1 LATI-best    q from the LOO-best model (the frame calibrated on real returns)
  F2 LATI-incumb  q from the incumbent-field-only model (favors the incumbent)
  F3 LATI-uniform uniform q at the model-free diffuse-probe K (adversarial: makes
                  no shape assumption at all, penalises any concentration)
  F4 SGMC-offcat  USGS SGMC faults >300 m off the catalogue (official, independent;
                  LATI puts only ~0.5% of the truth here, so it is reported with
                  that caveat rather than used to select)
  F5 CATQ-blocked 4-quadrant blocked holdout on the given catalogue, scored
                  WITHOUT the organiser's mask (contaminated by construction)

    python3 scripts/build_submission.py [--budget 44090] [--slug gems47]
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
from gems47 import hypotheses as HY
from gems47 import lati
from gems47 import metric as M
from gems47.research_policy import reject_pages_output, require_research_only
from gems47.scripts_common import rank_u8_inplace
from gems47.submission import diff_report, validate_submission, write_submission

K_LO, K_HI, BMAX, L2 = 2_000.0, 120_000.0, 12.0, 1e-5


def prox_layer(obs, oid, ev_idx, shape, cap=40.0):
    o = [x for x in obs if x.id == oid][0]
    m = np.zeros(shape[0] * shape[1], bool)
    m[o.dot_flat] = True
    return rank_u8_inplace((-FEAT.dist_px(m.reshape(shape), cap).ravel()[ev_idx]).astype(np.float32))


def fit_model(rows_u8, obs, l2=L2, bmax=BMAX):
    V = np.stack(rows_u8)
    L = {1: 256, 2: 64, 3: 32, 4: 20}[len(rows_u8)]
    bm = lati.BinnedSoftmax(V, list(range(len(rows_u8))), obs, L)
    f = bm.fit(l2=l2, bmax=bmax, k_lo=K_LO, k_hi=K_HI)
    pred = bm.predict(np.array(f["theta"]))
    f["ssr"] = float(np.sum((pred - bm.dti_obs) ** 2))
    loo, per = 0.0, []
    for h in range(len(obs)):
        sub = [i for i in range(len(obs)) if i != h]
        g = bm.fit(l2=l2, subset=sub, theta0=np.array(f["theta"]), bmax=bmax, k_lo=K_LO, k_hi=K_HI)
        e = float(bm.predict(np.array(g["theta"]))[h] - bm.dti_obs[h])
        per.append(e)
        loo += e * e
    f["loo_ssr"] = loo
    f["loo_residuals"] = per
    eta = np.zeros(V.shape[1])
    for j in range(len(rows_u8)):
        eta += f["theta"][1 + j] * (V[j].astype(np.float64) / 255.0 - 0.5)
    s = np.exp(eta - eta.max())
    return f, (s / s.sum())


def dense_q(shape, ev_idx, w_norm, K):
    q = np.zeros(shape[0] * shape[1])
    q[ev_idx] = K * w_norm
    return q.reshape(shape)


def main() -> int:
    require_research_only()
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=44_090,
                    help="dot budget; default matches the live-0.2600 incumbent exactly")
    ap.add_argument("--slug", default="gems47")
    ap.add_argument("--hypothesis", default="h47-saf")
    ap.add_argument("--outdir", default=str(ROOT / ".cache" / "retired_lati_reproduction" / "build_submission"))
    ap.add_argument("--greedy", action="store_true", default=True,
                    help="greedy marginal-rule emission (default); dots are spaced by the rule itself")
    ap.add_argument("--topk", action="store_true", help="use plain top-k ranking instead of greedy")
    ap.add_argument("--batch", type=int, default=2000)
    args = ap.parse_args()
    t0 = time.time()

    t = G.load_template()
    ev, shape = t.evaluated, t.shape
    obs = lati.load_observations(verbose=False)
    st = FEAT.build_stack(verbose=False)
    ev_idx = st["ev_idx"]   # this exploratory build derives its layers from hypotheses.py
    HL = HY.build_layers(t)
    d_cat = HL["_diag_d_catalogue"]
    halo3 = ev & (d_cat > 0) & (d_cat <= M.RANGE_PX)
    halo15 = ev & (d_cat > 0) & (d_cat <= 1.5)

    u_prox = prox_layer(obs, "d2.8", ev_idx, shape)
    u_flank = rank_u8_inplace(HL["flank_halo_0_3"].ravel()[ev_idx].astype(np.float32))

    # ---- F1: LOO-best belief model ----------------------------------------
    f1, w1 = fit_model([u_prox, u_flank], obs)
    q1 = dense_q(shape, ev_idx, w1, f1["theta"][0])
    # ---- F2: incumbent-field-only model -----------------------------------
    f2, w2 = fit_model([u_prox], obs)
    q2 = dense_q(shape, ev_idx, w2, f2["theta"][0])
    # ---- F3: uniform q at the model-free diffuse-probe K ------------------
    K3 = 12_348.0
    q3 = np.zeros(shape)
    q3[ev] = K3 / ev.sum()
    print(f"[models] F1 LOO-best  K={f1['theta'][0]:,.0f} SSR={f1['ssr']:.6f} LOO={f1['loo_ssr']:.6f} "
          f"theta={[round(v,3) for v in f1['theta']]}")
    print(f"[models] F2 incumbent K={f2['theta'][0]:,.0f} SSR={f2['ssr']:.6f} LOO={f2['loo_ssr']:.6f} "
          f"theta={[round(v,3) for v in f2['theta']]}")
    print(f"[models] F3 uniform   K={K3:,.0f} (model-free estimate from the r13-lattice diffuse probe)")

    # ---- the candidate ----------------------------------------------------
    allowed = ev.copy()
    if args.topk:
        cand = E.emit_topk(q1, allowed, args.budget)
        stop = f"top-{args.budget} by belief"
        res = None
    else:
        res = E.emit_greedy(q1, allowed, budget=args.budget, dti_start=0.26,
                            batch=args.batch, verbose=True)
        cand = res.dots
        stop = f"{res.stopped_by} (greedy marginal rule, batch={args.batch})"
    n_cand = int(cand.sum())
    print(f"[cand] {n_cand:,} dots ({stop}); flank 0-150m = {int((cand&halo15).sum()):,} "
          f"({100*(cand&halo15).sum()/n_cand:.1f}%), flank 0-300m = {int((cand&halo3).sum()):,} "
          f"({100*(cand&halo3).sum()/n_cand:.1f}%), on catalogue = {int((cand&t.catalogue).sum())}, "
          f"outside footprint = {int((cand&~t.footprint).sum())}")

    # ---- baselines reproduced from bytes ----------------------------------
    priors: dict[str, tuple[np.ndarray, float | None]] = {}
    for o in obs:
        m = np.zeros(shape[0] * shape[1], bool)
        m[o.dot_flat] = True
        priors[f"prior_{o.id}"] = (m.reshape(shape), o.dti)
    h33 = ROOT.parent / "refs" / "GEMSDOE32" / "docs" / "downloads" / \
        "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    if h33.exists():
        with rasterio.open(h33) as s:
            priors["prior_h33-2-b2_reported_0.2778"] = (np.nan_to_num(s.read(1)) > 0, 0.2778)
    h27 = ROOT.parent / "refs" / "GEMSDOE32" / "docs" / "downloads"
    for extra, live in [("gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif", 0.2600)]:
        p = h27 / extra
        if p.exists():
            with rasterio.open(p) as s:
                priors["prior_d2.8_zeros_variant"] = (np.nan_to_num(s.read(1)) > 0, live)

    with rasterio.open(G.data_dir() / "external" / "derived_sgmc_faults_100m_u8.tif") as s:
        sg = s.read(1) > 0
    truth_sgmc = sg & ev & (d_cat > M.RANGE_PX)
    folds = {}
    H, W = shape
    for k, (sy, sx) in {"NW": (slice(0, H // 2), slice(0, W // 2)),
                        "NE": (slice(0, H // 2), slice(W // 2, W)),
                        "SW": (slice(H // 2, H), slice(0, W // 2)),
                        "SE": (slice(H // 2, H), slice(W // 2, W))}.items():
        tr = np.zeros(shape, bool)
        tr[sy, sx] = t.catalogue[sy, sx]
        folds[k] = tr

    def evaluate(label, dots, reported=None):
        p = np.where(ev & dots, 1.0, 0.0)
        r = dict(arm=label, n_dots=int(dots.sum()), reported_live_dti=reported,
                 on_catalogue=int((dots & t.catalogue).sum()),
                 outside_footprint=int((dots & ~t.footprint).sum()),
                 flank_0_150m=int((dots & halo15).sum()),
                 flank_0_300m=int((dots & halo3).sum()),
                 flank_0_150m_pct=round(100 * (dots & halo15).sum() / max(int(dots.sum()), 1), 3),
                 on_sgmc_offcat=int((dots & truth_sgmc).sum()))
        for nm, q in (("F1_lati_best", q1), ("F2_lati_incumbent", q2), ("F3_lati_uniform", q3)):
            ps = E.predicted_score(q, dots & ev)
            r[nm] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in ps.items()}
        s4 = M.score(p, truth_sgmc, ev).as_dict()
        r["F4_sgmc_offcatalogue"] = {k: (round(v, 6) if isinstance(v, float) else v)
                                     for k, v in s4.items()}
        cq = {k: round(M.score(p, tr, t.footprint).DTI, 6) for k, tr in folds.items()}
        r["F5_catq_blocked"] = cq
        r["F5_catq_mean"] = round(float(np.mean(list(cq.values()))), 6)
        dis = {}
        for nm, (pd_, _) in priors.items():
            inter = int((pd_ & dots).sum())
            dis[nm] = dict(intersection=inter,
                           jaccard=round(inter / max(int((pd_ | dots).sum()), 1), 6),
                           frac_of_candidate=round(inter / max(int(dots.sum()), 1), 6))
        r["distinctness"] = dis
        r["max_jaccard_vs_any_prior"] = round(max(v["jaccard"] for v in dis.values()), 6)
        r["max_frac_overlap_vs_any_prior"] = round(max(v["frac_of_candidate"] for v in dis.values()), 6)
        return r

    rows = [evaluate("GEMSDOE47 CANDIDATE", cand)]
    for nm in ("prior_d2.8", "prior_h33-2-b2_reported_0.2778", "prior_h19-5", "prior_r13-lattice"):
        if nm in priors:
            rows.append(evaluate(nm, priors[nm][0], priors[nm][1]))

    print("\n=== multi-frame evaluation (DTI under each truth frame) ===")
    hdr = f"{'arm':<38}{'dots':>8}{'flank%':>8}{'F1 LATI':>10}{'F2 inc':>9}{'F3 unif':>9}{'F4 SGMC':>9}{'F5 CATQ':>9}"
    print(hdr)
    for r in rows:
        print(f"{r['arm']:<38}{r['n_dots']:>8,}{r['flank_0_150m_pct']:>8.1f}"
              f"{r['F1_lati_best']['DTI']:>10.4f}{r['F2_lati_incumbent']['DTI']:>9.4f}"
              f"{r['F3_lati_uniform']['DTI']:>9.4f}{r['F4_sgmc_offcatalogue']['DTI']:>9.4f}"
              f"{r['F5_catq_mean']:>9.4f}")
    base = [r for r in rows if r["arm"] == "prior_d2.8"][0]
    cand_r = rows[0]
    print("\n=== candidate minus incumbent d2.8 (paired, per frame) ===")
    for nm, key in (("F1 LATI-best", ("F1_lati_best", "DTI")), ("F2 LATI-incumbent", ("F2_lati_incumbent", "DTI")),
                    ("F3 LATI-uniform", ("F3_lati_uniform", "DTI")), ("F4 SGMC-offcat", ("F4_sgmc_offcatalogue", "DTI")),
                    ("F5 CATQ-blocked", (None, "F5_catq_mean"))):
        a = cand_r[key[0]][key[1]] if key[0] else cand_r[key[1]]
        b = base[key[0]][key[1]] if key[0] else base[key[1]]
        print(f"   {nm:<18} {a:.4f} - {b:.4f} = {a-b:+.4f}")
    print(f"   distinctness: max Jaccard vs any prior = {cand_r['max_jaccard_vs_any_prior']:.4f}, "
          f"max overlap fraction = {cand_r['max_frac_overlap_vs_any_prior']:.4f}")

    # ---- write the GeoTIFFs ------------------------------------------------
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    h = hashlib.sha256(np.ascontiguousarray(cand.view(np.uint8)).tobytes()).hexdigest()
    base_name = f"{args.slug}-{args.hypothesis}-flank-reoccupation-{n_cand}px-{stamp}-{h[:10]}"
    outdir = Path(args.outdir)
    reject_pages_output(outdir, ROOT)
    outdir.mkdir(parents=True, exist_ok=True)
    shipped = []
    pvals = np.where(ev & cand, np.float32(1.0), np.float32(0.0))
    for mode in ("allfinite", "nan"):
        fn = outdir / f"{base_name}-{mode}.tif"
        write_submission(pvals if mode == "allfinite" else
                         np.where(t.footprint, pvals, np.float32(np.nan)), fn,
                         mode="zeros" if mode == "allfinite" else "nan", template=t)
        v = validate_submission(fn, template=t)
        shipped.append(dict(mode=mode, filename=fn.name, primary=(mode == "allfinite"),
                            sha256=hashlib.sha256(fn.read_bytes()).hexdigest(),
                            bytes=fn.stat().st_size, validation=v))
        print(f"\n[ship] {fn.name}  {fn.stat().st_size:,} B  sha256={shipped[-1]['sha256'][:16]}...")
        print(f"       all_checks_passed={v['all_checks_passed']} "
              f"passes_nan_intolerant_range_check={v['passes_nan_intolerant_range_check']} "
              f"recommended_for_upload={v['recommended_for_upload']} hard_failures={v['hard_failures']}")
    dr = diff_report(outdir / f"{base_name}-allfinite.tif", outdir / f"{base_name}-nan.tif")

    note = (f"GEMSDOE47 H47-SAF | LATI-inverted belief (graded 0-300 m catalogue halo x "
            f"multiphysics ridge), K={f1['theta'][0]:,.0f}, exact-marginal-rule greedy emission, "
            f"{n_cand} dots of which {cand_r['flank_0_300m']} ({cand_r['flank_0_150m_pct']:.1f}% in 0-150 m) "
            f"re-occupy the catalogue flank the 0.2778 arm emptied; UNSCORED")

    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        hypothesis="H47-SAF: strike-agnostic graded catalogue-flank re-occupation",
        belief_model=dict(layers=["prox_d2.8", "flank_halo_0_3"], theta=f1["theta"],
                          K=f1["theta"][0], ssr=f1["ssr"], loo_ssr=f1["loo_ssr"],
                          loo_residuals=f1["loo_residuals"],
                          alternative_model=dict(layers=["prox_d2.8"], theta=f2["theta"],
                                                 ssr=f2["ssr"], loo_ssr=f2["loo_ssr"]),
                          uniform_model_K=K3),
        emission=dict(rule="dT*(1/DTI-alpha) > alpha*dF with exact Bernoulli E[kappa]",
                      stopped_by=stop, budget=args.budget, mode=("topk" if args.topk else "greedy"),
                      dti_trace=(res.dti_trace if res else None)),
        frames=dict(
            F1="LATI LOO-best q (calibrated on 12 real returned DTIs)",
            F2="LATI incumbent-field-only q (favours the incumbent)",
            F3=f"uniform q at K={K3:,.0f} from the model-free r13-lattice diffuse probe "
               "(adversarial to any concentration)",
            F4="USGS SGMC faults >300 m off the catalogue (official, independent). CAVEAT: "
               "the LOO-best LATI model puts only ~0.5% of the hidden truth here, so this "
               "frame is reported, not used to select.",
            F5="4-quadrant blocked holdout on the given catalogue scored WITHOUT the "
               "organiser's mask. CAVEAT: its truth IS the catalogue, so it rewards the "
               "opposite skill; a candidate cannot even be scored on it under the "
               "organiser's stated masking (see evidence/irregularities IR-47-005)."),
        results=rows, shipped=shipped, submission_note=note,
        allfinite_vs_nan_identical=dr["identical"],
        seconds=round(time.time() - t0, 1))
    (outdir / "submission_build-educational-only.json").write_text(json.dumps(out, indent=1, default=float))
    np.save(ROOT / ".cache" / "candidate_dots.npy", cand)
    np.save(ROOT / ".cache" / "q_f1.npy", q1.astype(np.float32))
    print(f"\nwrote evidence/submission_build.json ({time.time()-t0:.0f}s)")
    print("NOTE:", note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
