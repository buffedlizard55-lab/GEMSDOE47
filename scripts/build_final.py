#!/usr/bin/env python3
"""Legacy exploratory builder for the H47-GSA research artifact; never submit its output.

The historical LATI fit contains twelve owner-reported score/raster pairs plus
H33-2-B2 as a *conditional scenario* at assumed DTI 0.2778. The public
participant-level row is not authenticated to that TIFF. Consequently, every
13-row selection, fitted coefficient, cross-fit, and generated artifact that uses
this row is conditional and must not be presented as a verified score/validation
result. The H47-GSA cross-fit is negative and H33-dependent; H47-GSA is not
promoted.

The local R1-R4 filters recorded below are historical diagnostics only. They do
not establish a gain over the current spatially blocked holdout best, and passing
them cannot authorize a submission. This script now labels any generated TIFF as
research-only and closes the project submission gate. Existing downloads are
preserved.

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
from gems47.scripts_common import rank_u8_inplace
from gems47.submission import diff_report, validate_submission, write_submission

L2, BMAX, KLO, KHI = 1e-5, 12.0, 2_000.0, 120_000.0
LEVELS = {1: 256, 2: 64, 3: 32, 4: 20, 5: 14}
H33 = ROOT / ".cache" / "gems_data" / "reference" / "h33-2-b2-zeros.tif"
H33_SHA256 = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
H33_ASSUMED_DTI = 0.2778
MATCHED = [44_090, 37_654]


def add_h33(obs12, t, ev, ev_idx, shape) -> list[lati.Obs]:
    if not H33.is_file():
        raise SystemExit(f"missing {H33}; restore registry entry ref_h33_2_b2 before running")
    digest = hashlib.sha256(H33.read_bytes()).hexdigest()
    if digest != H33_SHA256:
        raise SystemExit(f"H33 SHA-256 mismatch: {digest} != {H33_SHA256}")
    with rasterio.open(H33) as s:
        if s.count != 1 or not G.dataset_matches_template_grid(s, t):
            raise SystemExit("H33 reference raster grid does not match the competition template")
        v = np.nan_to_num(s.read(1).astype(np.float32), nan=0.0)
    pred = np.where(ev, v, 0.0)
    dm = pred > 0
    dflat = np.flatnonzero(dm.ravel())
    pos = np.full(shape[0] * shape[1], -1, np.int64)
    pos[ev_idx] = np.arange(ev_idx.size)
    w = M.max_kernel_filter(pred.astype(np.float64))
    a = np.zeros(shape)
    for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        a += k * lati._shift_in(dm.astype(np.float64), dy, dx)
    o = lati.Obs(
        id="h33-2-b2",
        dti=H33_ASSUMED_DTI,
        site="GEMSDOE32",
        family="flank-pruned reference raster; score/file mapping unverified",
        sha256=digest,
        S=float(pred[dm].sum()),
        n_dots=int((v > 0).sum()),
        n_on_catalogue=int((v > 0)[t.catalogue].sum()),
        w=w.ravel()[ev_idx].astype(np.float32),
        a=a.ravel()[ev_idx].astype(np.float32),
        dot_pos=pos[dflat],
        dot_flat=dflat,
        extras={"assumed_dti_scenario": H33_ASSUMED_DTI,
                "score_file_mapping_verified": False},
    )
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
    print("RETIRED: legacy LATI builder disabled; see README.md and docs/COMPLIANCE.md", file=sys.stderr)
    return 2
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
    print(f"[data] {len(obs12)} owner-reported pairs + 1 conditional H33 scenario "
          f"(assumed DTI {H33_ASSUMED_DTI:.4f}; score/file mapping unverified)")

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

    # ---- conditional 13-row forward-selection scenario -------------------
    prev = json.loads((ROOT / "evidence" / "screen13.json").read_text())
    pool = [r["layer"] for r in prev["screen"][:14] if r["layer"] in layers]
    f_base, w_base = fit([PX], obs)
    q_base = np.zeros(shape[0] * shape[1]); q_base[ev_idx] = f_base["theta"][0] * w_base
    q_base = q_base.reshape(shape)
    print(f"[base] owner-reported d2.8-reference-field-only model: K={f_base['theta'][0]:,.0f} "
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

    def evaluate(
        label,
        dots,
        *,
        owner_reported_dti=None,
        assumed_dti_scenario=None,
        score_file_mapping_verified=None,
    ):
        dots = dots & ev
        p = np.where(dots, 1.0, 0.0)
        r = dict(
            arm=label,
            n_dots=int(dots.sum()),
            owner_reported_dti=owner_reported_dti,
            assumed_dti_scenario=assumed_dti_scenario,
            score_file_mapping_verified=score_file_mapping_verified,
            score_attribution_status=(
                "owner-reported; no organizer receipt" if owner_reported_dti is not None else None
            ),
            on_catalogue=int((dots & t.catalogue).sum()),
            outside_footprint=int((dots & ~t.footprint).sum()),
            flank_0_300m=int((dots & halo3).sum()),
            flank_0_300m_pct=round(100 * (dots & halo3).sum() / max(int(dots.sum()), 1), 2),
            annulus_300m_2500m=int((dots & ev & (d_cat > 3) & (d_cat <= 25)).sum()),
            annulus_pct=round(
                100 * (dots & ev & (d_cat > 3) & (d_cat <= 25)).sum()
                / max(int(dots.sum()), 1),
                2,
            ),
            on_sgmc_offcat=int((dots & truth_sgmc).sum()),
        )
        for nm, q in (("F1_lati_selected", q1), ("F2_lati_d2_8_reference", q_base), ("F3_lati_uniform", q3)):
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
        if nm not in priors:
            continue
        if nm == "prior_h33-2-b2":
            rows.append(
                evaluate(
                    "H33-2-B2 reference raster (conditional assumed-DTI scenario; score/file mapping unverified)",
                    priors[nm][0],
                    assumed_dti_scenario=H33_ASSUMED_DTI,
                    score_file_mapping_verified=False,
                )
            )
        else:
            rows.append(
                evaluate(
                    f"owner-reported reference {nm.removeprefix('prior_')}",
                    priors[nm][0],
                    owner_reported_dti=priors[nm][1],
                    score_file_mapping_verified=False,
                )
            )

    print("\n=== multi-frame evaluation ===")
    print(f"{'arm':<32}{'dots':>8}{'flank%':>8}{'annul%':>8}{'F1 sel':>9}{'F2 d2.8ref':>10}{'F3 unif':>9}"
          f"{'F4 SGMC':>9}{'F5 CATQ':>9}{'maxJac':>9}")
    for r in rows:
        print(f"{r['arm']:<32}{r['n_dots']:>8,}{r['flank_0_300m_pct']:>8.1f}{r['annulus_pct']:>8.1f}"
              f"{r['F1_lati_selected']['DTI']:>9.4f}{r['F2_lati_d2_8_reference']['DTI']:>9.4f}"
              f"{r['F3_lati_uniform']['DTI']:>9.4f}{r['F4_sgmc_offcatalogue']['DTI']:>9.4f}"
              f"{r['F5_catq_mean']:>9.4f}{r['max_jaccard_vs_any_prior']:>9.4f}")

    d28_reference_row = [r for r in rows if r["arm"] == "prior_d2.8"][0]
    cand_rows = [r for r in rows if r["arm"].startswith("GEMSDOE47")]
    # Historical local diagnostics only; they do not constitute the project gate.
    local_passed = []
    for r in cand_rows:
        r2 = r["F1_lati_selected"]["DTI"] > d28_reference_row["F1_lati_selected"]["DTI"]
        r3 = (r["F4_sgmc_offcatalogue"]["DTI"]
              >= d28_reference_row["F4_sgmc_offcatalogue"]["DTI"])
        r4 = r["max_jaccard_vs_any_prior"] <= 0.90
        r["passes_historical_R2_F1_beats_d2_8_reference"] = bool(r2)
        r["passes_historical_R3_F4_not_worse"] = bool(r3)
        r["passes_historical_R4_distinctness_threshold"] = bool(r4)
        r["passes_historical_local_filters"] = bool(r2 and r3 and r4)
        r["project_slot_eligible"] = False
        if r["passes_historical_local_filters"]:
            local_passed.append(r)
        print(
            f"[diagnostic] {r['arm']:<28} local R2={r2} R3={r3} R4={r4}; "
            "project slot eligibility=False"
        )
    if local_passed:
        matched = [r for r in local_passed if r["arm"].endswith(str(MATCHED[0]))
                   or f"matched{MATCHED[0]}" in r["arm"]]
        research_selected = max(
            matched or local_passed,
            key=lambda r: r["F1_lati_selected"]["DTI"],
        )
    else:
        research_selected = max(cand_rows, key=lambda r: r["F1_lati_selected"]["DTI"])
        research_selected["passes_historical_local_filters"] = False
    research_selected["project_slot_eligible"] = False
    print(
        f"\n[research-only] Selected for artifact audit: {research_selected['arm']} "
        f"dots={research_selected['n_dots']:,}; slot eligibility=False; "
        f"conditional F1={research_selected['F1_lati_selected']['DTI']:.4f} "
        f"(owner-reported d2.8 reference {d28_reference_row['F1_lati_selected']['DTI']:.4f})"
    )

    # ---- write -------------------------------------------------------------
    dots = np.zeros(shape, bool)
    for l2_, d2_, _score_, _truth_ in arms:
        if f"GEMSDOE47 {l2_}" == research_selected["arm"]:
            dots = d2_ & ev
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    h = hashlib.sha256(np.ascontiguousarray(dots.view(np.uint8)).tobytes()).hexdigest()
    slug = f"gems47-h47gsa-research-only-{'-'.join(c.replace('prox_d2.8','d28ref') for c in sel['layers'][1:])}"[:100]
    base_name = f"{slug}-{int(dots.sum())}px-{stamp}-{h[:10]}"
    outdir = ROOT / "docs" / "downloads"
    outdir.mkdir(parents=True, exist_ok=True)
    research_artifacts = []
    pvals = np.where(dots, np.float32(1.0), np.float32(0.0))
    for mode in ("allfinite", "nan"):
        fn = outdir / f"{base_name}-{mode}.tif"
        write_submission(pvals if mode == "allfinite" else
                         np.where(t.footprint, pvals, np.float32(np.nan)), fn,
                         mode="zeros" if mode == "allfinite" else "nan", template=t)
        v = validate_submission(fn, template=t)
        v["project_submission_authorized"] = False
        v["project_gate_status"] = "CLOSED_RESEARCH_ONLY"
        research_artifacts.append(dict(
            mode=mode,
            filename=fn.name,
            passes_nan_intolerant_range_check=bool(v["passes_nan_intolerant_range_check"]),
            sha256=hashlib.sha256(fn.read_bytes()).hexdigest(),
            bytes=fn.stat().st_size,
            research_only=True,
            submission_authorized=False,
            slot_eligible=False,
            validation=v,
        ))
        print(f"[write] {fn.name} {fn.stat().st_size:,} B required_local_checks_passed={v['required_local_checks_passed']} "
              f"nan_intolerant_range_ok={v['passes_nan_intolerant_range_check']} "
              "upload_recommendation=none "
              "project_submission_authorized=False")
    dr = diff_report(outdir / f"{base_name}-allfinite.tif", outdir / f"{base_name}-nan.tif")
    research_note = (
        f"RESEARCH ONLY — NOT FOR PORTAL. H47-GSA conditional 13-row LATI fit "
        f"(12 owner-reported pairs + H33 assumed DTI {H33_ASSUMED_DTI:.4f}; "
        "score/file mapping unverified); "
        f"selected layers {', '.join(sel['layers'][1:])}, K={f_sel['theta'][0]:,.0f}; "
        f"{int(dots.sum())} dots, {research_selected['annulus_pct']:.0f}% in the "
        "300 m–2.5 km catalogue annulus. No submission authorized."
    )
    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        hypothesis="H47-GSA exploratory geodetic-strain / hydrothermal-alteration / seismicity model",
        selection_rule="historical local R1-R4 diagnostics only; see docstring; passing them does not authorize a submission",
        observation_scope=dict(
            owner_reported_pairs=len(obs12),
            conditional_h33_scenario_count=1,
            h33_assumed_dti=H33_ASSUMED_DTI,
            h33_score_file_mapping_verified=False,
        ),
        forward_selection=hist,
        selected=dict(
            layers=sel["layers"],
            theta=f_sel["theta"],
            K=f_sel["theta"][0],
            ssr=f_sel["ssr"],
            loo=f_sel["loo"],
            loo_residuals=f_sel["loo_residuals"],
            conditional_on_h33_assumption=True,
        ),
        baseline_model=dict(
            layers=["prox_d2.8"],
            theta=f_base["theta"],
            K=f_base["theta"][0],
            ssr=f_base["ssr"],
            loo=f_base["loo"],
            conditional_on_h33_assumption=True,
        ),
        frames=dict(
            F1="conditional 13-row LOO-selected LATI belief q (H33 mapping unverified)",
            F2="conditional owner-reported d2.8-reference-field-only LATI q",
            F3="uniform diagnostic q at K=12,348 from an owner-reported diffuse-pair inverse; not verified hidden-label mass",
            F4="USGS SGMC faults >300 m off the catalogue (local diagnostic)",
            F5="4-quadrant blocked holdout on the given catalogue, scored unmasked (contaminated)"),
        results=rows,
        selected_research_arm=research_selected["arm"],
        research_artifacts=research_artifacts,
        research_artifact_name=base_name,
        research_note=research_note,
        submission_gate=dict(
            status="CLOSED",
            authorized=False,
            slot_eligible=False,
            reasons=[
                "no candidate has demonstrated a gain over an established spatially blocked holdout best",
                "H47-GSA cross-fit is negative and conditional on the unverified H33 mapping",
                "local format validation and Jaccard distinctness do not establish predictive value",
            ],
        ),
        allfinite_vs_nan_identical=dr["identical"],
        n_priors_compared=len(priors),
        seconds=round(time.time() - t0, 1),
    )
    (ROOT / "evidence" / "final_build.json").write_text(json.dumps(out, indent=1, default=float, allow_nan=False))
    np.save(ROOT / ".cache" / "final_dots.npy", dots)
    np.save(ROOT / ".cache" / "final_q1.npy", q1.astype(np.float32))
    print(f"\nwrote evidence/final_build.json ({time.time()-t0:.0f}s)")
    print("NOTE:", research_note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
