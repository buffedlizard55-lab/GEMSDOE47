#!/usr/bin/env python3
"""Exploratory LATI v2 fit to twelve owner-reported score/raster pairs.

The raster hashes are pinned, but the score-to-file associations have no organizer
receipts. Public leaderboard rows are participant-level and are not mapped to these
TIFFs; results are not authenticated private-target performance.

Model (see src/gems47/lati.py::BinnedSoftmax):

    q(x) = K * exp(sum_m beta_m u_m(x)) / sum_x exp(sum_m beta_m u_m(x))

    DTI_i = T_i / (alpha*(T_i + S_i - Phi_i) + beta_w*K),
    T_i   = <q, w_i>   (exact),      Phi_i = <q, a_i>   (first order in q)

Stages
  0  uniform-q baseline; and the exploratory K estimates from two owner-reported *diffuse*
     probes (r13-lattice, placeholder) whose halos average over the footprint
  1  single-layer screen over 59 geological layers + 15 controls
  2  forward selection on leave-one-observation-out CV (geological layers only)
  3  bootstrap over observations -> interval on K and on every beta
  4  dense (unbinned) re-verification of the chosen model
  5  writes the fitted q to .cache/lati_q.npy and evidence/lati_fit.json

    python3 scripts/lati_fit.py [--max-feat 4] [--pool 18] [--boot 300]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47 import features as FEAT
from gems47 import lati
from gems47 import metric as M

LEVELS_BY_R = {0: 1, 1: 256, 2: 64, 3: 32, 4: 20, 5: 14, 6: 12}
K_LO, K_HI = 2_000.0, 60_000.0
BMAX = 12.0


def rank_u8_inplace(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, np.float64)
    order = np.argsort(x, kind="stable")
    r = np.empty(x.size)
    r[order] = np.arange(x.size, dtype=np.float64)
    return np.clip(np.rint(r / max(x.size - 1, 1) * 255.0), 0, 255).astype(np.uint8)


def build_controls(obs, ev_idx, shape, U, names, seed=0):
    """Positive controls: proximity to each previously submitted raster.
    Negative control: a spatially permuted copy of a real layer."""
    H, W = shape
    rows = []
    labels = []
    for o in obs:
        m = np.zeros(H * W, bool)
        m[o.dot_flat] = True
        d = FEAT.dist_px(m.reshape(H, W), 40.0)
        rows.append(rank_u8_inplace(-d.ravel()[ev_idx]))
        labels.append(f"control_prox_{o.id}")
        del m, d
    rng = np.random.default_rng(seed)
    j = names.index("lidar_scarp_composite")
    rows.append(U[j][rng.permutation(U.shape[1])])
    labels.append("control_shuffled_lidar_composite")
    return np.stack(rows), labels


def fit(bm, l2=0.0, subset=None, theta0=None):
    return bm.fit(l2=l2, subset=subset, theta0=theta0, bmax=BMAX, k_lo=K_LO, k_hi=K_HI)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-feat", type=int, default=4)
    ap.add_argument("--pool", type=int, default=18)
    ap.add_argument("--l2", type=float, default=0.01)
    ap.add_argument("--boot", type=int, default=300)
    ap.add_argument("--no-controls", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "evidence" / "lati_fit.json"))
    args = ap.parse_args()

    t0 = time.time()
    obs = lati.load_observations(verbose=True)
    st = FEAT.build_stack(verbose=False)
    U, names = st["U"], list(st["names"])
    ev_idx, shape = st["ev_idx"], tuple(st["meta"]["shape"])

    ctrl_labels: list[str] = []
    if not args.no_controls:
        Uc, ctrl_labels = build_controls(obs, ev_idx, shape, U, names)
        U = np.concatenate([U, Uc])
        names = names + ctrl_labels
    n_geo = len(names) - len(ctrl_labels)
    print(f"[lati] {len(names)} layers = {n_geo} geological + {len(ctrl_labels)} controls; "
          f"n_eval={U.shape[1]:,} ({time.time()-t0:.0f}s)", flush=True)

    out = {
        "instrument": "LATI v2 - exploratory owner-reported score/raster fit (softmax intensity)",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "observation_scope": {
            "owner_reported_score_raster_pairs": len(obs),
            "organizer_receipts_available": False,
            "leaderboard_participant_rows_mapped_to_tiffs": False,
            "h33_included_as_score_observation": False,
            "interpretation": "exploratory fit only; score/file associations are owner-reported and unauthenticated",
        },
        "model": {"form": "q(x) = K*exp(sum beta_m u_m(x)) / Z, u = rank percentile in [-0.5,0.5]",
                  "alpha": M.ALPHA, "beta_weight": M.BETA, "range_m": M.RANGE_M,
                  "T_exact": "T_i = <q, w_i>, w_i = max-filter of the submitted dot set",
                  "Phi_first_order": "Phi_i = <q, a_i>, a_i = kernel-sum filter of the dot set",
                  "mask_mode": "zero: catalogue pixels removed before BOTH sums",
                  "K_bounds": [K_LO, K_HI], "beta_bound": BMAX},
        "n_evaluated_pixels": int(U.shape[1]),
        "layer_names": names, "n_geological_layers": n_geo,
        "observations": [dict(id=o.id, site=o.site, family=o.family, dti=o.dti, S=o.S,
                              n_dots=o.n_dots, n_on_catalogue=o.n_on_catalogue,
                              sha256=o.sha256, **o.extras) for o in obs],
    }

    # ---------------- stage 0 ----------------------------------------------
    bm0 = lati.BinnedSoftmax(U, [], obs, 1)
    f0 = fit(bm0)
    f0["components"] = bm0.components(np.array(f0["theta"]))
    out["baseline_uniform"] = f0
    print(f"\n[stage0] uniform q (all 12): K={f0['K']:,.0f} SSR={f0['ssr']:.6f} "
          f"max|resid|={f0['max_abs_resid']:.4f}")
    diffuse = {}
    for oid in ("r13-lattice", "placeholder", "h25-ctx"):
        i = [o.id for o in obs].index(oid)
        g = fit(bm0, subset=[i])
        diffuse[oid] = dict(K=g["K"], dti_obs=obs[i].dti, dti_model=g["pred"][i],
                            note="exploratory inverse under an owner-reported score/raster association; its diffuse 300 m halo reduces spatial-shape sensitivity, but the score link is unauthenticated")
        print(f"   exploratory K from {oid:<12} = {g['K']:>9,.0f}  "
              f"(model DTI {g['pred'][i]:.4f} vs owner-reported {obs[i].dti:.4f})")
    out["K_from_diffuse_probes"] = diffuse

    # ---------------- stage 1 ----------------------------------------------
    t1 = time.time()
    screen = []
    for j, nm in enumerate(names):
        bm = lati.BinnedSoftmax(U, [j], obs, LEVELS_BY_R[1])
        f = fit(bm)
        screen.append(dict(layer=nm, index=int(j), is_control=nm.startswith("control_"),
                           K=f["K"], beta=f["theta"][1], ssr=f["ssr"],
                           dssr_vs_uniform=f0["ssr"] - f["ssr"],
                           max_abs_resid=f["max_abs_resid"], at_bound=f["at_bound"]))
        if (j + 1) % 15 == 0:
            print(f"[stage1] {j+1}/{len(names)} ({time.time()-t1:.0f}s)", flush=True)
    screen.sort(key=lambda r: r["ssr"])
    for r, rank in zip(screen, range(1, len(screen) + 1)):
        r["rank"] = rank
    out["single_layer_screen"] = screen
    geo = [r for r in screen if not r["is_control"]]
    ctl = [r for r in screen if r["is_control"]]
    print(f"\n[stage1] uniform baseline SSR = {f0['ssr']:.6f}")
    print("  top 18 GEOLOGICAL layers (controls excluded from the shipped model):")
    for r in geo[:18]:
        print(f"   #{r['rank']:<3} {r['layer']:<28} SSR={r['ssr']:.6f} dSSR={r['dssr_vs_uniform']:+.6f} "
              f"K={r['K']:>9,.0f} beta={r['beta']:+.3f} maxres={r['max_abs_resid']:.4f}")
    print("  CONTROLS (descriptive fit diagnostics; not model-validity tests):")
    for r in ctl:
        print(f"   #{r['rank']:<3} {r['layer']:<38} SSR={r['ssr']:.6f} K={r['K']:>9,.0f} beta={r['beta']:+.3f}")

    # ---------------- stage 2 ----------------------------------------------
    pool = [r["index"] for r in geo[:args.pool]]
    chosen: list[int] = []
    hist = []
    cur_loo = f0["ssr"] * len(obs) / len(obs)  # compare against uniform in-sample SSR
    base_loo = 0.0
    for hold in range(len(obs)):
        sub = [i for i in range(len(obs)) if i != hold]
        g = fit(bm0, subset=sub)
        base_loo += (bm0.predict(np.array(g["theta"]))[hold] - obs[hold].dti) ** 2
    cur_loo = base_loo
    print(f"\n[stage2] uniform-baseline LOO SSR = {base_loo:.6f}")
    for step in range(args.max_feat):
        L = LEVELS_BY_R[len(chosen) + 1]
        best = None
        for j in pool:
            if j in chosen:
                continue
            rows = chosen + [j]
            bm = lati.BinnedSoftmax(U, rows, obs, L)
            f = fit(bm, l2=args.l2)
            cv = 0.0
            for hold in range(len(obs)):
                sub = [i for i in range(len(obs)) if i != hold]
                g = fit(bm, l2=args.l2, subset=sub, theta0=np.array(f["theta"]))
                cv += (bm.predict(np.array(g["theta"]))[hold] - obs[hold].dti) ** 2
            f["loo_cv_ssr"] = float(cv)
            if best is None or cv < best["loo_cv_ssr"]:
                best = dict(f, index=int(j), layer=names[j], rows=list(rows), L=L)
        if best is None:
            break
        best.pop("pred", None)
        improved = best["loo_cv_ssr"] < cur_loo - 1e-9
        hist.append(best)
        print(f"[stage2] step {step+1}: + {best['layer']:<28} SSR={best['ssr']:.6f} "
              f"LOO={best['loo_cv_ssr']:.6f} (prev {cur_loo:.6f}) K={best['K']:,.0f} "
              f"-> {'ACCEPT' if improved else 'REJECT (no LOO gain)'}", flush=True)
        if not improved:
            hist[-1]["rejected"] = True
            break
        chosen.append(best["index"])
        cur_loo = best["loo_cv_ssr"]
    out["forward_selection"] = hist
    out["chosen_layers"] = [names[j] for j in chosen]
    out["baseline_loo_ssr"] = base_loo

    # ---------------- stage 3 ----------------------------------------------
    L = LEVELS_BY_R[len(chosen)] if chosen else 1
    bm = lati.BinnedSoftmax(U, chosen, obs, L)
    final = fit(bm, l2=args.l2)
    rng = np.random.default_rng(20261006)
    boots = []
    for _ in range(args.boot):
        sub = rng.integers(0, len(obs), len(obs)).tolist()
        if len(set(sub)) < 5:
            continue
        try:
            g = fit(bm, l2=args.l2, subset=sub, theta0=np.array(final["theta"]))
            boots.append(g["theta"])
        except Exception:
            continue
    B = np.array(boots)
    out["bootstrap"] = {
        "n": len(B),
        "K": {"mean": float(B[:, 0].mean()), "sd": float(B[:, 0].std()),
              "p2.5": float(np.percentile(B[:, 0], 2.5)),
              "p50": float(np.percentile(B[:, 0], 50)),
              "p97.5": float(np.percentile(B[:, 0], 97.5))},
        "beta": [{"layer": ("K (modeled total truth mass; not measured)" if i == 0 else names[chosen[i - 1]]),
                  "mean": float(B[:, i].mean()), "sd": float(B[:, i].std()),
                  "p2.5": float(np.percentile(B[:, i], 2.5)),
                  "p97.5": float(np.percentile(B[:, i], 97.5)),
                  "frac_positive": float((B[:, i] > 0).mean())} for i in range(B.shape[1])],
    }

    # ---------------- stage 4: dense verification ---------------------------
    # dense q on the evaluated pixel set
    eta = np.zeros(U.shape[1], np.float64)
    for jj, j in enumerate(chosen):
        eta += final["theta"][1 + jj] * (U[j].astype(np.float64) / 255.0 - 0.5)
    s = np.exp(eta - eta.max())
    q = final["theta"][0] * s / s.sum()
    dense = lati.components(obs, q)
    binned = bm.components(np.array(final["theta"]))
    err = float(max(abs(b["dti_model"] - d["dti_model"]) for b, d in zip(binned, dense)))
    out["final_model"] = dict(
        layers=out["chosen_layers"], theta=final["theta"], l2=args.l2, L=L,
        ssr=final["ssr"], loo_cv_ssr=cur_loo, K=final["K"],
        max_abs_resid=final["max_abs_resid"], binning_max_abs_dti_error=err,
        dense_components=dense, binned_components=binned,
        q_summary=dict(mean=float(q.mean()), max=float(q.max()),
                       p50=float(np.median(q)), p99=float(np.percentile(q, 99)),
                       p999=float(np.percentile(q, 99.9)),
                       top44090_mass=float(np.sort(q)[-44_090:].sum()),
                       top100000_mass=float(np.sort(q)[-100_000:].sum()),
                       mass_above_0p2=float(q[q > 0.002].sum()),
                       n_above_0p2=int((q > 0.002).sum())))
    print(f"\n[final] layers={out['chosen_layers']}")
    print(f"        theta={[round(v,4) for v in final['theta']]}  K={final['K']:,.0f}  "
          f"SSR={final['ssr']:.6f}  LOO={cur_loo:.6f}  binning err={err:.2e}")
    for d in dense:
        print(f"   {d['id']:<12} obs={d['dti_obs']:.4f} model={d['dti_model']:.4f} "
              f"resid={d['dti_model']-d['dti_obs']:+.4f} T={d['T']:>8.1f} F={d['F']:>9.1f} "
              f"recall={d['weighted_recall']:.3f} credit/dot={d['credit_per_dot']:.4f}")
    bk = out["bootstrap"]["K"]
    print(f"[boot] K 95% CI = {bk['p2.5']:,.0f} .. {bk['p97.5']:,.0f}  (median {bk['p50']:,.0f})")

    out["seconds"] = round(time.time() - t0, 1)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1, default=float))
    (ROOT / ".cache").mkdir(exist_ok=True)
    np.save(ROOT / ".cache" / "lati_q.npy", q.astype(np.float32))
    np.save(ROOT / ".cache" / "lati_theta.npy", np.array(final["theta"]))
    (ROOT / ".cache" / "lati_chosen.json").write_text(json.dumps(
        {"layers": out["chosen_layers"], "indices": chosen, "theta": final["theta"],
         "K": final["K"], "ssr": final["ssr"], "loo": cur_loo}, indent=1))
    print(f"wrote {args.out} and .cache/lati_q.npy  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
