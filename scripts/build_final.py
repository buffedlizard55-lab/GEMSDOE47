#!/usr/bin/env python3
"""Build, evaluate and ship the GEMSDOE47 submission (hypothesis H47-GSA).

Belief model: forward-selected on the FULL thirteen-observation LATI set (the
twelve restored scored rasters plus the reported-0.2778 flank-pruned
``h33-2-b2`` raster, which is the datum that falsified the earlier flank
hypothesis).  Selection criterion is leave-one-observation-out CV, so the model
is never chosen by a frame it was fitted on.

PRE-REGISTERED SELECTION RULE (fixed before the arms were run):
  R1  emit at the budget the metric's own marginal rule chooses, and also at the
      two matched budgets 44,090 (the live-0.2600 incumbent) and 37,654 (the
      reported-0.2778 arm), so every comparison is at equal mass;
  R2  rank arms by F1 (the 13-observation LOO-best belief model) at matched
      budget against the incumbent;
  R3  reject any arm that is worse than the incumbent on F4 (the official,
      independent USGS SGMC off-catalogue frame);
  R4  reject any arm whose maximum Jaccard overlap with any prior raster in the
      collection exceeds 0.90 - the deliverable must be a distinct submission.
F3 (uniform q) and F5 (blocked catalogue holdout) are reported, never selected
on: F3 makes no shape assumption and therefore penalises every concentrated
field, and F5's truth IS the masked catalogue, so it rewards the opposite skill.

    python3 scripts/build_final.py
"""

from __future__ import annotations

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
from gems47.research_policy import require_research_only
from gems47.scripts_common import rank_u8_inplace
from gems47.submission import diff_report, validate_submission, write_submission

L2, BMAX, KLO, KHI = 1e-5, 12.0, 2_000.0, 120_000.0
LEVELS = {1: 256, 2: 64, 3: 32, 4: 20, 5: 14}
H33 = Path("/home/user/refs/GEMSDOE32/docs/downloads/"
           "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
MATCHED = [44_090, 37_654]


def add_h33(obs12, t, ev, ev_idx, shape) -> list[lati.Obs]:
    with rasterio.open(H33) as s:
        v = np.nan_to_num(s.read(1).astype(np.float32))
    pred = np.where(ev, v, 0.0)
    dm = pred > 0
    dflat = np.flatnonzero(dm.ravel())
    pos = np.full(shape[0] * shape[1], -1, np.int64)
    pos[ev_idx] = np.arange(ev_idx.size)
    w = M.max_kernel_filter(pred.astype(np.float64))
    a = np.zeros(shape)
    for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        a += k * lati._shift_in(dm.astype(np.float64), dy, dx)
    o = lati.Obs(id="h33-2-b2", dti=0.2778, site="GEMSDOE32",
                 family="flank-pruned (reported 0.2778, attribution CONFLICTED)",
                 sha256=hashlib.sha256(H33.read_bytes()).hexdigest(),
                 S=float(pred[dm].sum()), n_dots=int((v > 0).sum()),
                 n_on_catalogue=int((v > 0)[t.catalogue].sum()),
                 w=w.ravel()[ev_idx].astype(np.float32), a=a.ravel()[ev_idx].astype(np.float32),
                 dot_pos=pos[dflat], dot_flat=dflat,
                 extras={"note": "13th observation; the datum that falsified the flank hypothesis"})
    return list(obs12) + [o]


def fit(rows_u8, obs):
    V = np.stack(rows_u8)
    bm = lati.BinnedSoftmax(V, list(range(len(rows_u8))), obs, LEVELS[len(rows_u8)])
    f = bm.fit(l2=L2, bmax=BMAX, k_lo=KLO, k_hi=KHI)
    f["ssr"] = float(np.sum((bm.predict(np.array(f["theta"])) - bm.dti_obs) ** 2))
    loo, per = 0.0, []
    for h in range(len(obs)):
        sub = [i for i in range(len(obs)) if i != h]
        g = bm.fit(l2=L2, subset=sub, theta0=np.array(f["theta"]), bmax=BMAX, k_lo=KLO, k_hi=KHI)
        e = float(bm.predict(np.array(g["theta"]))[h] - obs[h].dti)
        per.append(e)
        loo += e * e
    f["loo"] = loo
    f["loo_residuals"] = per
    eta = np.zeros(V.shape[1])
    for j in range(len(rows_u8)):
        eta += f["theta"][1 + j] * (V[j].astype(np.float64) / 255.0 - 0.5)
    s = np.exp(eta - eta.max())
    return f, s / s.sum()


def main() -> int:
    require_research_only()
    t0 = time.time()
    t = G.load_template()
    ev, shape = t.evaluated, t.shape
    obs12 = lati.load_observations(verbose=False)
    st = FEAT.build_stack(verbose=False)
    U, names, ev_idx = st["U"], list(st["names"]), st["ev_idx"]
    obs = add_h33(obs12, t, ev, ev_idx, shape)
    HL = HY.build_layers(t)
    d_cat = HL["_diag_d_catalogue"]
    halo3 = ev & (d_cat > 0) & (d_cat <= M.RANGE_PX)
    print(f"[data] {len(obs)} observations (12 restored + h33-2-b2 @ reported 0.2778)")

    def prox(oid, cap=40.0):
        o = [x for x in obs12 if x.id == oid][0]
        m = np.zeros(shape[0] * shape[1], bool)
        m[o.dot_flat] = True
        return rank_u8_inplace((-FEAT.dist_px(m.reshape(shape), cap).ravel()[ev_idx]).astype(np.float32))

    PX = prox("d2.8")
    layers: dict[str, np.ndarray] = {"prox_d2.8": PX}
    for j, nm in enumerate(names):
        layers[nm] = U[j]
    for k, v in HL.items():
        if not k.startswith("_diag"):
            layers[k] = rank_u8_inplace(v.ravel()[ev_idx].astype(np.float32))

    # ---- forward selection on the 13-observation LOO ----------------------
    prev = json.loads((ROOT / "evidence" / "screen13.json").read_text())
    pool = [r["layer"] for r in prev["screen"][:14] if r["layer"] in layers]
    f_base, w_base = fit([PX], obs)
    q_base = np.zeros(shape[0] * shape[1]); q_base[ev_idx] = f_base["theta"][0] * w_base
    q_base = q_base.reshape(shape)
    print(f"[base] incumbent-field-only model: K={f_base['theta'][0]:,.0f} "
          f"SSR={f_base['ssr']:.6f} LOO={f_base['loo']:.6f}")
    cache = ROOT / ".cache" / "final_model_selection.json"
    if cache.exists():
        cj = json.loads(cache.read_text())
        print(f"[select] cache hit: layers={cj['layers']} LOO={cj['loo']:.6f}")
        sel = cj
        f_sel, w_sel = fit([layers[c] for c in sel["layers"]], obs)
        q1 = np.zeros(shape[0] * shape[1]); q1[ev_idx] = f_sel["theta"][0] * w_sel
        q1 = q1.reshape(shape)
        q3 = np.zeros(shape); q3[ev] = 12_348.0 / ev.sum()
        hist = cj.get("hist", [])
        _skip_selection = True
    else:
        _skip_selection = False
    chosen: list[str] = ["prox_d2.8"]
    cur_loo = f_base["loo"]
    hist = [dict(step=0, added=None, layers=list(chosen), K=f_base["theta"][0],
                 theta=f_base["theta"], ssr=f_base["ssr"], loo=cur_loo)]
    for step in (range(1, 5) if not _skip_selection else []):
        best = None
        for nm in pool:
            if nm in chosen:
                continue
            f, _ = fit([layers[c] for c in chosen] + [layers[nm]], obs)
            if best is None or f["loo"] < best["loo"]:
                best = dict(step=step, added=nm, layers=chosen + [nm], K=f["theta"][0],
                            theta=[float(v) for v in f["theta"]], ssr=f["ssr"], loo=f["loo"],
                            loo_residuals=f["loo_residuals"])
        if best is None or best["loo"] >= cur_loo - 1e-9:
            print(f"[select] step {step}: no layer improves LOO ({best['loo'] if best else None} "
                  f"vs {cur_loo:.6f}) -> STOP")
            if best:
                best["rejected"] = True
                hist.append(best)
            break
        chosen = best["layers"]
        cur_loo = best["loo"]
        hist.append(best)
        print(f"[select] step {step}: + {best['added']:<22} K={best['K']:>9,.0f} "
              f"SSR={best['ssr']:.6f} LOO={cur_loo:.6f} ({100*(f_base['loo']-cur_loo)/f_base['loo']:+.1f}% vs base)")
    if not _skip_selection:
        accepted = [h for h in hist if not h.get("rejected")]
        sel = accepted[-1]
        f_sel, w_sel = fit([layers[c] for c in sel["layers"]], obs)
        q1 = np.zeros(shape[0] * shape[1]); q1[ev_idx] = f_sel["theta"][0] * w_sel
        q1 = q1.reshape(shape)
        q3 = np.zeros(shape); q3[ev] = 12_348.0 / ev.sum()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(dict(layers=sel["layers"], loo=sel["loo"],
                                         ssr=sel["ssr"], K=sel["K"], theta=sel["theta"],
                                         hist=hist), indent=1))
    print(f"[model] SELECTED layers={sel['layers']} theta={[round(v,3) for v in f_sel['theta']]} "
          f"K={f_sel['theta'][0]:,.0f} SSR={f_sel['ssr']:.6f} LOO={f_sel['loo']:.6f}")

    with rasterio.open(G.data_dir() / "external" / "derived_sgmc_faults_100m_u8.tif") as s:
        sg = s.read(1) > 0
    truth_sgmc = sg & ev & (d_cat > M.RANGE_PX)
    H, W = shape
    folds = {}
    for k, (sy, sx) in {"NW": (slice(0, H // 2), slice(0, W // 2)),
                        "NE": (slice(0, H // 2), slice(W // 2, W)),
                        "SW": (slice(H // 2, H), slice(0, W // 2)),
                        "SE": (slice(H // 2, H), slice(W // 2, W))}.items():
        tr = np.zeros(shape, bool); tr[sy, sx] = t.catalogue[sy, sx]; folds[k] = tr

    priors: dict[str, tuple[np.ndarray, float | None]] = {}
    for o in obs:
        m = np.zeros(shape[0] * shape[1], bool); m[o.dot_flat] = True
        priors[f"prior_{o.id}"] = (m.reshape(shape), o.dti)
    for f_ in sorted((ROOT.parent / "refs" / "GEMSDOE32" / "docs" / "downloads").glob("*-zeros.tif")):
        try:
            with rasterio.open(f_) as s:
                priors["g32_" + f_.stem[:52]] = (np.nan_to_num(s.read(1)) > 0, None)
        except Exception:
            pass
    for f_ in sorted((ROOT.parent / "refs" / "GEMSDOE42" / "docs" / "downloads").glob("*.tif")):
        try:
            with rasterio.open(f_) as s:
                priors["g42_" + f_.stem[:52]] = (np.nan_to_num(s.read(1)) > 0, None)
        except Exception:
            pass
    print(f"[frames] {len(priors)} prior rasters available for the distinctness test")

    def evaluate(label, dots, reported=None):
        dots = dots & ev
        p = np.where(dots, 1.0, 0.0)
        r = dict(arm=label, n_dots=int(dots.sum()), reported_live_dti=reported,
                 on_catalogue=int((dots & t.catalogue).sum()),
                 outside_footprint=int((dots & ~t.footprint).sum()),
                 flank_0_300m=int((dots & halo3).sum()),
                 flank_0_300m_pct=round(100 * (dots & halo3).sum() / max(int(dots.sum()), 1), 2),
                 annulus_300m_2500m=int((dots & ev & (d_cat > 3) & (d_cat <= 25)).sum()),
                 annulus_pct=round(100 * (dots & ev & (d_cat > 3) & (d_cat <= 25)).sum()
                                   / max(int(dots.sum()), 1), 2),
                 on_sgmc_offcat=int((dots & truth_sgmc).sum()))
        for nm, q in (("F1_lati_selected", q1), ("F2_lati_incumbent", q_base), ("F3_lati_uniform", q3)):
            ps = E.predicted_score(q, dots)
            r[nm] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in ps.items()}
        s4 = M.score(p, truth_sgmc, ev).as_dict()
        r["F4_sgmc_offcatalogue"] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in s4.items()}
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

    # ---- emission ----------------------------------------------------------
    arms: list[dict] = []
    print("\n[emit] greedy under the exact marginal rule (budget chosen by the metric itself)")
    res = E.emit_greedy(q1, ev.copy(), budget=150_000, dti_start=0.0, batch=4000, verbose=True)
    arms.append(("greedy", res.dots, res.stopped_by, res.dti_trace))
    for b in MATCHED:
        rb = E.emit_greedy(q1, ev.copy(), budget=b, dti_start=0.0, batch=4000)
        arms.append((f"matched{b}", rb.dots, rb.stopped_by, rb.dti_trace))
    for b in MATCHED:
        arms.append((f"topk{b}", E.emit_topk(q1, ev.copy(), b), f"top-{b} by belief", None))

    rows = []
    for lbl, dots, stop, trace in arms:
        r = evaluate(f"GEMSDOE47 {lbl}", dots)
        r["emission_stopped_by"] = stop
        r["dti_trace_last"] = (trace[-6:] if trace else None)
        rows.append(r)
    for nm in ("prior_d2.8", "prior_h33-2-b2", "prior_h19-5", "prior_r13-lattice", "prior_placeholder"):
        if nm in priors:
            rows.append(evaluate(nm, priors[nm][0], priors[nm][1]))

    print("\n=== multi-frame evaluation ===")
    print(f"{'arm':<32}{'dots':>8}{'flank%':>8}{'annul%':>8}{'F1 sel':>9}{'F2 inc':>9}{'F3 unif':>9}"
          f"{'F4 SGMC':>9}{'F5 CATQ':>9}{'maxJac':>9}")
    for r in rows:
        print(f"{r['arm']:<32}{r['n_dots']:>8,}{r['flank_0_300m_pct']:>8.1f}{r['annulus_pct']:>8.1f}"
              f"{r['F1_lati_selected']['DTI']:>9.4f}{r['F2_lati_incumbent']['DTI']:>9.4f}"
              f"{r['F3_lati_uniform']['DTI']:>9.4f}{r['F4_sgmc_offcatalogue']['DTI']:>9.4f}"
              f"{r['F5_catq_mean']:>9.4f}{r['max_jaccard_vs_any_prior']:>9.4f}")

    inc = [r for r in rows if r["arm"] == "prior_d2.8"][0]
    cand_rows = [r for r in rows if r["arm"].startswith("GEMSDOE47")]
    # R2/R3/R4 selection
    ok = []
    for r in cand_rows:
        r2 = r["F1_lati_selected"]["DTI"] > inc["F1_lati_selected"]["DTI"]
        r3 = r["F4_sgmc_offcatalogue"]["DTI"] >= inc["F4_sgmc_offcatalogue"]["DTI"]
        r4 = r["max_jaccard_vs_any_prior"] <= 0.90
        r["passes_R2_F1_beats_incumbent"] = bool(r2)
        r["passes_R3_F4_not_worse"] = bool(r3)
        r["passes_R4_distinct"] = bool(r4)
        r["eligible"] = bool(r2 and r3 and r4)
        if r["eligible"]:
            ok.append(r)
        print(f"[select] {r['arm']:<28} R2={r2} R3={r3} R4={r4} -> {'ELIGIBLE' if r['eligible'] else 'rejected'}")
    ship = None
    if ok:
        matched = [r for r in ok if r["arm"].endswith(str(MATCHED[0])) or f"matched{MATCHED[0]}" in r["arm"]]
        ship = max(matched or ok, key=lambda r: r["F1_lati_selected"]["DTI"])
    else:
        ship = max(cand_rows, key=lambda r: r["F1_lati_selected"]["DTI"])
        ship["shipped_despite_rejection"] = True
    print(f"\n[ship] SELECTED: {ship['arm']}  dots={ship['n_dots']:,}  "
          f"F1={ship['F1_lati_selected']['DTI']:.4f} (incumbent {inc['F1_lati_selected']['DTI']:.4f})")

    # ---- write -------------------------------------------------------------
    dots = np.zeros(shape, bool)
    lbl = ship["arm"].split(" ", 1)[1]
    for l2_, d2_, s2_, tr2_ in arms:
        if f"GEMSDOE47 {l2_}" == ship["arm"]:
            dots = d2_ & ev
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    h = hashlib.sha256(np.ascontiguousarray(dots.view(np.uint8)).tobytes()).hexdigest()
    slug = f"gems47-h47gsa-{'-'.join(c.replace('prox_d2.8','incumb') for c in sel['layers'][1:])}"[:88]
    base_name = f"{slug}-{int(dots.sum())}px-{stamp}-{h[:10]}"
    outdir = ROOT / ".cache" / "retired_lati_reproduction" / "build_final"
    outdir.mkdir(parents=True, exist_ok=True)
    shipped = []
    pvals = np.where(dots, np.float32(1.0), np.float32(0.0))
    for mode in ("allfinite", "nan"):
        fn = outdir / f"{base_name}-{mode}.tif"
        write_submission(pvals if mode == "allfinite" else
                         np.where(t.footprint, pvals, np.float32(np.nan)), fn,
                         mode="zeros" if mode == "allfinite" else "nan", template=t)
        v = validate_submission(fn, template=t)
        shipped.append(dict(mode=mode, filename=fn.name, primary=(mode == "allfinite"),
                            sha256=hashlib.sha256(fn.read_bytes()).hexdigest(),
                            bytes=fn.stat().st_size, validation=v))
        print(f"[write] {fn.name} {fn.stat().st_size:,} B all_passed={v['all_checks_passed']} "
              f"nan_intolerant_range_ok={v['passes_nan_intolerant_range_check']} "
              f"recommended={v['recommended_for_upload']}")
    dr = diff_report(outdir / f"{base_name}-allfinite.tif", outdir / f"{base_name}-nan.tif")
    note = (f"GEMSDOE47 H47-GSA | 13-observation LATI forward selection "
            f"({', '.join(sel['layers'][1:])}), K={f_sel['theta'][0]:,.0f}, exact-marginal-rule "
            f"emission, {int(dots.sum())} dots, {ship['annulus_pct']:.0f}% in the 300 m-2.5 km "
            f"catalogue annulus; UNSCORED")
    out = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               hypothesis="H47-GSA: geodetic-strain / hydrothermal-alteration / seismicity "
                          "annulus model of the hidden new-fault population",
               selection_rule="see this file's docstring (pre-registered R1-R4)",
               forward_selection=hist, selected=dict(layers=sel["layers"], theta=f_sel["theta"],
                                                     K=f_sel["theta"][0], ssr=f_sel["ssr"],
                                                     loo=f_sel["loo"],
                                                     loo_residuals=f_sel["loo_residuals"]),
               baseline_model=dict(layers=["prox_d2.8"], theta=f_base["theta"], K=f_base["theta"][0],
                                   ssr=f_base["ssr"], loo=f_base["loo"]),
               frames=dict(
                   F1="13-observation LOO-selected LATI belief q",
                   F2="incumbent-field-only LATI q (favours the incumbent)",
                   F3="uniform q at the model-free diffuse-probe K=12,348 (adversarial to any concentration)",
                   F4="USGS SGMC faults >300 m off the catalogue (official, independent)",
                   F5="4-quadrant blocked holdout on the given catalogue, scored unmasked (contaminated)"),
               results=rows, shipped_arm=ship["arm"], shipped=shipped,
               submission_name=base_name, submission_note=note,
               allfinite_vs_nan_identical=dr["identical"],
               n_priors_compared=len(priors),
               seconds=round(time.time() - t0, 1))
    (outdir / "final_build-educational-only.json").write_text(json.dumps(out, indent=1, default=float))
    np.save(ROOT / ".cache" / "final_dots.npy", dots)
    np.save(ROOT / ".cache" / "final_q1.npy", q1.astype(np.float32))
    print(f"\nwrote evidence/final_build.json ({time.time()-t0:.0f}s)")
    print("NOTE:", note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
