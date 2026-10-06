#!/usr/bin/env python3
"""RETIRED LATI builders: educational reproduction only, never a slot candidate.

Both arms depend on adaptive, unauthenticated leaderboard observations and fitted
truth models. Their scores are proxy beliefs, not organizer receipts. H47-GSA
failed cross-fitting. H47-MAXCOV changes an emission rule, not the geology; its
covered-kernel integral is not DTI without truth. Neither is approved.

The official competition has up to three scoring submissions per week and ONE
selected file for both prize rounds, not unlimited final-round submissions.

Opt-in: python scripts/ship.py --research-only
Outputs go to ignored cache, never delete or replace the current research TIFF.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47 import emitter as E
from gems47 import grid as G
from gems47 import lati
from gems47 import metric as M
from gems47.research_policy import require_research_only
from gems47.scripts_common import rank_u8_inplace
from gems47.submission import diff_report, validate_submission, write_submission

L2, BMAX, KLO, KHI = 1e-5, 12.0, 2_000.0, 120_000.0
LEVELS = {1: 256, 2: 64, 3: 32, 4: 20, 5: 14}
H33_REL = "reference/h33-2-b2-zeros.tif"
# recorded by evidence/flank_sensitivity.json from the sibling clone, so the
# restore is verifiable rather than trusted
H33_SHA256 = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
H33_DTI = 0.2778
K_UNIFORM = 12_348.0   # model-dependent approximation from an unauthenticated diffuse-probe score
ARM2_LAYERS = ["prox_d2.8", "geod_shearrate", "rad_ThK", "thermal_warm_prox", "geod_dilaterate"]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def dist_px(mask: np.ndarray, cap: float) -> np.ndarray:
    if not mask.any():
        return np.full(mask.shape, cap, np.float32)
    return np.clip(ndimage.distance_transform_edt(~mask), 0, cap).astype(np.float32)


def obs_from_dots(dots: np.ndarray, dti: float, oid: str, site: str, family: str,
                  sha: str, t: G.Template, ev_idx: np.ndarray, pos: np.ndarray,
                  raw_pos: np.ndarray | None = None) -> lati.Obs:
    """Build a lati.Obs from a boolean dot mask, applying mask_mode='zero'."""
    ev = t.evaluated
    pred = np.where(ev & dots, 1.0, 0.0)
    dm = pred > 0
    dflat = np.flatnonzero(dm.ravel())
    w = M.max_kernel_filter(pred.astype(np.float64))
    a = np.zeros(t.shape)
    for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        a += k * lati._shift_in(dm.astype(np.float64), dy, dx)
    allp = dots if raw_pos is None else raw_pos
    return lati.Obs(id=oid, dti=dti, site=site, family=family, sha256=sha,
                    S=float(pred[dm].sum()), n_dots=int(allp.sum()),
                    n_on_catalogue=int((allp & t.catalogue).sum()),
                    w=w.ravel()[ev_idx].astype(np.float32),
                    a=a.ravel()[ev_idx].astype(np.float32),
                    dot_pos=pos[dflat], dot_flat=dflat, extras={})


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=37_654,
                    help="matched to the reported-0.2778 arm: equal-mass comparison")
    ap.add_argument("--budget2", type=int, default=44_090,
                    help="matched to the live-0.2600 incumbent")
    args = ap.parse_args()
    t0 = time.time()
    data = G.data_dir()
    t = G.load_template(data)
    ev, shape = t.evaluated, t.shape
    H, W = shape
    ev_idx = np.flatnonzero(ev.ravel())
    pos = np.full(H * W, -1, np.int64)
    pos[ev_idx] = np.arange(ev_idx.size)
    print(f"[grid] {shape} evaluated={int(ev.sum()):,} catalogue={int(t.catalogue.sum()):,}")

    # ---- the 13 observations ------------------------------------------------
    obs: list[lati.Obs] = []
    for rec in lati.OBSERVATIONS:
        p = data / "scored" / rec["file"]
        if not p.exists():
            raise SystemExit(f"missing {p}; run scripts/restore_data.py --group all")
        with rasterio.open(p) as s:
            v = np.nan_to_num(s.read(1).astype(np.float32))
        obs.append(obs_from_dots(v > 0, rec["dti"], rec["id"], rec["site"], rec["family"],
                                 sha256_file(p), t, ev_idx, pos, raw_pos=v > 0))
    h33p = data / H33_REL
    if not h33p.exists():
        raise SystemExit(f"missing {h33p}; see registry/data_manifest.json entry 'ref_h33_2_b2'")
    got = sha256_file(h33p)
    if got != H33_SHA256:
        raise SystemExit(f"h33-2-b2 hash mismatch: {got} != {H33_SHA256}")
    with rasterio.open(h33p) as s:
        v33 = np.nan_to_num(s.read(1).astype(np.float32))
    obs.append(obs_from_dots(v33 > 0, H33_DTI, "h33-2-b2", "GEMSDOE32",
                             "flank-pruned (reported 0.2778, attribution CONFLICTED)",
                             got, t, ev_idx, pos, raw_pos=v33 > 0))
    print(f"[obs] {len(obs)} observations; h33-2-b2 sha256 verified {got[:16]}...")

    # ---- belief layers (computed directly, no 59-layer stack needed) --------
    d28 = np.zeros(H * W, bool)
    d28[[o.dot_flat for o in obs if o.id == "d2.8"][0]] = True
    d28 = d28.reshape(shape)
    layers = {"prox_d2.8": rank_u8_inplace((-dist_px(d28, 40.0).ravel()[ev_idx]).astype(np.float32))}

    with rasterio.open(data / "training_features.tif") as s:
        for band, nm in ((7, "geod_shearrate"), (8, "geod_dilaterate")):
            v = s.read(band).astype(np.float32)
            v[~(ev & (v > -1e30))] = 0.0
            layers[nm] = rank_u8_inplace(v.ravel()[ev_idx])
    with rasterio.open(data / "external" / "geodawn_extensions_u8.tif") as s:
        ext = s.read().astype(np.float32)          # ThK, UK, UTh, TMI_up150
    layers["rad_ThK"] = rank_u8_inplace(ext[0].ravel()[ev_idx])
    del ext

    warm = np.zeros(shape, bool)
    with open(data / "external" / "gdr_wellspring_in_footprint.csv") as fh:
        for row in csv.DictReader(fh):
            try:
                r, c = int(row["row"]), int(row["col"])
            except (ValueError, KeyError, TypeError):
                continue
            if 0 <= r < H and 0 <= c < W:
                warm[r, c] = True
    layers["thermal_warm_prox"] = rank_u8_inplace((-dist_px(warm & ev, 60.0).ravel()[ev_idx]).astype(np.float32))
    print(f"[layers] built {len(layers)} belief layers ({time.time()-t0:.0f}s)")

    # ---- fit both arms ------------------------------------------------------
    f1, w1 = fit([layers["prox_d2.8"]], obs)
    qA = np.zeros(H * W); qA[ev_idx] = f1["theta"][0] * w1
    qA = qA.reshape(shape)
    f2, w2 = fit([layers[c] for c in ARM2_LAYERS], obs)
    qB = np.zeros(H * W); qB[ev_idx] = f2["theta"][0] * w2
    qB = qB.reshape(shape)
    qU = np.zeros(shape); qU[ev] = K_UNIFORM / ev.sum()
    print(f"[arm1] H47-MAXCOV  layers=['prox_d2.8'] K={f1['theta'][0]:,.0f} "
          f"SSR={f1['ssr']:.6f} LOO={f1['loo']:.6f}")
    print(f"[arm2] H47-GSA     layers={ARM2_LAYERS[1:]} K={f2['theta'][0]:,.0f} "
          f"SSR={f2['ssr']:.6f} LOO={f2['loo']:.6f}")

    # ---- frames -------------------------------------------------------------
    with rasterio.open(data / "external" / "derived_sgmc_faults_100m_u8.tif") as s:
        sg = s.read(1) > 0
    d_cat = dist_px(t.catalogue, 80.0)
    truth_sgmc = sg & ev & (d_cat > M.RANGE_PX)
    halo3 = ev & (d_cat > 0) & (d_cat <= M.RANGE_PX)
    annulus = ev & (d_cat > 3) & (d_cat <= 25)
    folds = {}
    for k, (sy, sx) in {"NW": (slice(0, H // 2), slice(0, W // 2)),
                        "NE": (slice(0, H // 2), slice(W // 2, W)),
                        "SW": (slice(H // 2, H), slice(0, W // 2)),
                        "SE": (slice(H // 2, H), slice(W // 2, W))}.items():
        tr = np.zeros(shape, bool); tr[sy, sx] = t.catalogue[sy, sx]; folds[k] = tr
    priors = {}
    for o in obs:
        m = np.zeros(H * W, bool); m[o.dot_flat] = True
        priors[f"scored_{o.id}"] = m.reshape(shape)
    print(f"[frames] SGMC off-catalogue truth={int(truth_sgmc.sum()):,} px; "
          f"{len(priors)} prior rasters for distinctness")

    def evaluate(label, dots, reported=None):
        dots = dots & ev
        n = int(dots.sum())
        p = np.where(dots, 1.0, 0.0)
        cov = E.credit_field(dots.astype(np.float64))
        r = dict(arm=label, n_dots=n, reported_live_dti=reported,
                 on_catalogue=int((dots & t.catalogue).sum()),
                 outside_footprint=int((dots & ~t.footprint).sum()),
                 flank_0_300m=int((dots & halo3).sum()),
                 flank_0_300m_pct=round(100 * (dots & halo3).sum() / max(n, 1), 2),
                 annulus_300m_2500m=int((dots & annulus).sum()),
                 annulus_pct=round(100 * (dots & annulus).sum() / max(n, 1), 2),
                 on_sgmc_offcat=int((dots & truth_sgmc).sum()),
                 covered_kernel_integral=round(float(cov[ev].sum()), 1),
                 covered_evaluated_px=int((cov > 0)[ev].sum()))
        for nm, q in (("F1_arm1_belief", qA), ("F2_arm2_belief", qB), ("F3_uniform", qU)):
            ps = E.predicted_score(q, dots)
            r[nm] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in ps.items()}
        s4 = M.score(p, truth_sgmc, ev).as_dict()
        r["F4_sgmc_offcatalogue"] = {k: (round(v, 6) if isinstance(v, float) else v)
                                     for k, v in s4.items()}
        cq = {k: round(M.score(p, tr, t.footprint).DTI, 6) for k, tr in folds.items()}
        r["F5_catq_blocked"] = cq
        r["F5_catq_mean"] = round(float(np.mean(list(cq.values()))), 6)
        dis = {}
        for nm, pd_ in priors.items():
            inter = int((pd_ & dots).sum())
            dis[nm] = dict(intersection=inter,
                           jaccard=round(inter / max(int((pd_ | dots).sum()), 1), 6),
                           frac_of_candidate=round(inter / max(n, 1), 6))
        r["distinctness"] = dis
        r["max_jaccard_vs_any_prior"] = round(max(v["jaccard"] for v in dis.values()), 6)
        r["max_frac_overlap_vs_any_prior"] = round(max(v["frac_of_candidate"] for v in dis.values()), 6)
        r["distinct_from_every_prior"] = bool(r["max_jaccard_vs_any_prior"] < 0.90)
        return r

    # ---- emit ---------------------------------------------------------------
    arms: dict[str, np.ndarray] = {}
    stops: dict[str, str] = {}
    for b in (args.budget, args.budget2):
        for tag, q in (("arm1_maxcov", qA), ("arm2_h47gsa", qB)):
            print(f"\n[emit] {tag} budget={b:,}")
            r = E.emit_greedy(q, ev.copy(), budget=b, dti_start=0.0, batch=4000, verbose=True)
            arms[f"{tag}_{b}"] = r.dots
            stops[f"{tag}_{b}"] = r.stopped_by

    rows_out = []
    for lbl, d in arms.items():
        rr = evaluate(f"GEMSDOE47 {lbl}", d)
        rr["emission_stopped_by"] = stops[lbl]
        rows_out.append(rr)
    for o in obs:
        m = np.zeros(H * W, bool); m[o.dot_flat] = True
        rows_out.append(evaluate(f"REFERENCE {o.id}", m.reshape(shape), o.dti))

    print("\n=== multi-frame evaluation ===")
    print(f"{'arm':<30}{'dots':>8}{'coverage':>11}{'F1 arm1':>9}{'F2 arm2':>9}{'F3 unif':>9}"
          f"{'F4 SGMC':>9}{'F5 CATQ':>9}{'annul%':>8}{'maxJac':>8}")
    for r in rows_out:
        print(f"{r['arm']:<30}{r['n_dots']:>8,}{r['covered_kernel_integral']:>11,.0f}"
              f"{r['F1_arm1_belief']['DTI']:>9.4f}{r['F2_arm2_belief']['DTI']:>9.4f}"
              f"{r['F3_uniform']['DTI']:>9.4f}{r['F4_sgmc_offcatalogue']['DTI']:>9.4f}"
              f"{r['F5_catq_mean']:>9.4f}{r['annulus_pct']:>8.1f}{r['max_jaccard_vs_any_prior']:>8.4f}")
    ref = {r["arm"]: r for r in rows_out}
    i1, i2 = ref["REFERENCE d2.8"], ref["REFERENCE h33-2-b2"]
    print("\n=== paired comparison at matched budget ===")
    for lbl in (f"GEMSDOE47 arm1_maxcov_{args.budget}", f"GEMSDOE47 arm2_h47gsa_{args.budget}"):
        r = ref[lbl]
        print(f"  {lbl}")
        for frame, key in (("covered kernel integral", (None, "covered_kernel_integral")),
                           ("F1 arm1 belief", ("F1_arm1_belief", "DTI")),
                           ("F3 uniform", ("F3_uniform", "DTI")),
                           ("F4 SGMC-offcat", ("F4_sgmc_offcatalogue", "DTI")),
                           ("F5 CATQ-blocked", (None, "F5_catq_mean"))):
            a = r[key[0]][key[1]] if key[0] else r[key[1]]
            b1 = i1[key[0]][key[1]] if key[0] else i1[key[1]]
            b2 = i2[key[0]][key[1]] if key[0] else i2[key[1]]
            print(f"     {frame:<26}{a:>13,.4f}  vs d2.8 {b1:>11,.4f} ({a-b1:+,.4f})  "
                  f"vs h33 {b2:>11,.4f} ({a-b2:+,.4f})")

    # ---- write --------------------------------------------------------------
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    outdir = ROOT / ".cache" / "retired_lati_reproduction" / "ship"
    outdir.mkdir(parents=True, exist_ok=True)
    removed = []  # historical reproduction must never delete published TIFFs
    shipped = []
    specs = [
        ("arm1_maxcov", "h47maxcov", "RETIRED EDUCATIONAL REPRODUCTION - NOT PROMOTED, NO SLOT",
         f"GEMSDOE47 H47-MAXCOV-{args.budget} | 13-observation LATI belief (incumbent-field "
         f"proximity, K={f1['theta'][0]:,.0f}); exact-marginal-rule max-coverage emission at "
         f"matched budget; changes the EMISSION RULE, not the geology; UNSCORED"),
        ("arm2_h47gsa", "h47gsa", "RETIRED FAILED RESEARCH ARM - NOT PROMOTED, NO SLOT",
         f"GEMSDOE47 H47-GSA-{args.budget} | LATI forward selection over an a-priori geothermal "
         f"pool ({', '.join(ARM2_LAYERS[1:])}), K={f2['theta'][0]:,.0f}; FAILED cross-fitted "
         f"validation (-0.061 / -0.045 out of fold); do NOT spend a weekly slot; UNSCORED"),
    ]
    for key, slug, role, note in specs:
        dots = arms[f"{key}_{args.budget}"] & ev
        h = hashlib.sha256(np.ascontiguousarray(dots.view(np.uint8)).tobytes()).hexdigest()
        base_name = f"gems47-{slug}-{args.budget}px-{stamp}-{h[:10]}"
        pvals = np.where(dots, np.float32(1.0), np.float32(0.0))
        for mode in ("allfinite", "nan"):
            fn = outdir / f"{base_name}-{mode}.tif"
            write_submission(pvals if mode == "allfinite" else
                             np.where(t.footprint, pvals, np.float32(np.nan)), fn,
                             mode="zeros" if mode == "allfinite" else "nan", template=t)
            v = validate_submission(fn, template=t)
            shipped.append(dict(arm=key, slug=slug, role=role, budget=args.budget, mode=mode,
                                primary_download=False, slot_authorized=False,
                                filename=fn.name, name=base_name,
                                sha256=sha256_file(fn), bytes=fn.stat().st_size,
                                n_dots=int(dots.sum()), submission_note=note, validation=v))
            print(f"\n[write] {fn.name}\n        {fn.stat().st_size:,} B  {role}")
            print(f"        all_checks_passed={v['all_checks_passed']} "
                  f"nan_intolerant_range_ok={v['passes_nan_intolerant_range_check']} "
                  f"recommended_for_upload={v['recommended_for_upload']} "
                  f"hard_failures={v['hard_failures']}")
        dr = diff_report(outdir / f"{base_name}-allfinite.tif", outdir / f"{base_name}-nan.tif")
        shipped[-1]["allfinite_vs_nan_identical"] = dr["identical"]
        shipped[-2]["allfinite_vs_nan_identical"] = dr["identical"]

    cf = ROOT / "evidence" / "crossfit_validation.json"
    crossfit = json.loads(cf.read_text())["verdict"] if cf.exists() else None
    out = dict(generated_utc=stamp, budget=args.budget, budget2=args.budget2,
               n_observations=len(obs),
               belief_models=dict(
                   arm1=dict(name="H47-MAXCOV", layers=["prox_d2.8"], theta=f1["theta"],
                             K=f1["theta"][0], ssr=f1["ssr"], loo=f1["loo"],
                             loo_residuals=f1["loo_residuals"]),
                   arm2=dict(name="H47-GSA", layers=ARM2_LAYERS, theta=f2["theta"],
                             K=f2["theta"][0], ssr=f2["ssr"], loo=f2["loo"],
                             loo_residuals=f2["loo_residuals"]),
                   uniform_K=K_UNIFORM,
                   uniform_K_provenance="assumption-dependent estimate from an unauthenticated r13-lattice probe "
                                        "(its 300 m halo averages the whole footprint)"),
               frames=dict(
                   F1="13-observation LATI q, ARM 1 belief (incumbent-field proximity only)",
                   F2="13-observation LATI q, ARM 2 belief (H47-GSA forward selection)",
                   F3=f"uniform q at the assumed K={K_UNIFORM:,.0f} (adversarial to any concentration)",
                   F4="USGS SGMC faults >300 m off the given catalogue (official, independent)",
                   F5="4-quadrant blocked holdout on the given catalogue, scored unmasked (contaminated)",
                   coverage="covered 300 m kernel integral over the evaluated footprint - exact, "
                            "needs no truth model at all"),
               results=rows_out, shipped=shipped, superseded_outputs_removed=removed,
               crossfit_validation=crossfit, n_priors_compared=len(priors),
               seconds=round(time.time() - t0, 1))
    (outdir / "retired-lati-report.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"\nwrote ignored-cache retired-lati-report.json ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
