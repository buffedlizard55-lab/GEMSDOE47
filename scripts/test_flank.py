#!/usr/bin/env python3
"""Historical H47 flank diagnostics on catalogue and public SGMC proxies.

This legacy script is not an independent evaluation of private labels. SGMC is a
public geologic-map compilation that includes non-fault contacts and may omit
faults; its off-catalogue traces are a proxy population only. It does not establish
what the organizer scores. The reported H33 0.2778 value is a filename/board
association without an organizer receipt mapping that value to exact TIFF bytes.

Q1 fits catalogue-flank layers with and without the earlier field using the
historical leave-one-observation-out setup. This is an exploratory diagnostic,
not a prospective promotion test.

Q2 compares historical masks against the SGMC off-catalogue proxy using the
published metric. It is not “real truth” for the private target.

Q3 reports four spatial quadrants of the given-catalogue mask. This rewards
catalogue similarity and cannot validate discovery of uncatalogued faults.

    python3 scripts/test_flank.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47 import features as FEAT
from gems47 import grid as G
from gems47 import lati
from gems47 import metric as M
from gems47.scripts_common import rank_u8_inplace

K_LO, K_HI, BMAX, L2 = 2_000.0, 120_000.0, 12.0, 1e-5


def prox_layer(obs, oid, ev_idx, shape, cap=40.0):
    o = [x for x in obs if x.id == oid][0]
    H, W = shape
    m = np.zeros(H * W, bool)
    m[o.dot_flat] = True
    d = FEAT.dist_px(m.reshape(H, W), cap)
    return rank_u8_inplace((-d.ravel()[ev_idx]).astype(np.float32))


def fit(bm, subset=None, theta0=None):
    f = bm.fit(l2=L2, subset=subset, theta0=theta0, bmax=BMAX, k_lo=K_LO, k_hi=K_HI)
    pred = bm.predict(np.array(f["theta"]))
    f["ssr"] = float(np.sum((pred - bm.dti_obs) ** 2))
    return f


def loo(bm):
    tot = 0.0
    per = []
    for h in range(len(bm.ids)):
        sub = [i for i in range(len(bm.ids)) if i != h]
        g = fit(bm, subset=sub)
        e = float(bm.predict(np.array(g["theta"]))[h] - bm.dti_obs[h])
        per.append(e)
        tot += e * e
    return tot, per


def main() -> int:
    t0 = time.time()
    obs = lati.load_observations(verbose=False)
    st = FEAT.build_stack(verbose=False)
    U, names = st["U"], list(st["names"])
    ev_idx, shape = st["ev_idx"], tuple(st["meta"]["shape"])
    t = G.load_template()
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    # ---------------- Q1 ----------------------------------------------------
    extra = {
        "prox_d2.8": prox_layer(obs, "d2.8", ev_idx, shape),
        "dcat_band_0_1.5": U[names.index("dcat_band_0_1.5")],
        "dcat_band_1.5_3": U[names.index("dcat_band_1.5_3")],
        "sgmc_offcat_prox": U[names.index("sgmc_offcat_prox")],
        "sgmc_offcat": U[names.index("sgmc_offcat")],
    }
    combos = [
        ("incumbent-field-only", ["prox_d2.8"]),
        ("incumbent+flank0_1.5", ["prox_d2.8", "dcat_band_0_1.5"]),
        ("incumbent+flank0_3", ["prox_d2.8", "dcat_band_0_1.5", "dcat_band_1.5_3"]),
        ("incumbent+flank+sgmc", ["prox_d2.8", "dcat_band_0_1.5", "dcat_band_1.5_3",
                                  "sgmc_offcat_prox"]),
        ("flank+sgmc (no incumbent)", ["dcat_band_0_1.5", "dcat_band_1.5_3", "sgmc_offcat_prox"]),
    ]
    q1 = []
    print("[Q1] does the catalogue flank add signal beyond the incumbent's own field?")
    for label, keys in combos:
        Ux = np.stack([extra[k] for k in keys])
        bm = lati.BinnedSoftmax(Ux, list(range(len(keys))), obs,
                                {1: 256, 2: 64, 3: 32, 4: 20}[len(keys)])
        f = fit(bm)
        l, per = loo(bm)
        q1.append(dict(model=label, layers=keys, theta=f["theta"], K=f["K"],
                       ssr=f["ssr"], loo_ssr=l, loo_residuals=per,
                       max_abs_resid=f["max_abs_resid"]))
        print(f"   {label:<30} K={f['K']:>9,.0f} SSR={f['ssr']:.6f} LOO={l:.6f} "
              f"maxres={f['max_abs_resid']:.4f} theta={[round(v,3) for v in f['theta']]}")
    out["Q1_flank_incremental"] = q1
    base = q1[0]
    best = min(q1, key=lambda r: r["loo_ssr"])
    out["Q1_verdict"] = dict(
        baseline_model=base["model"], baseline_loo=base["loo_ssr"],
        best_model=best["model"], best_loo=best["loo_ssr"],
        flank_adds_signal=bool(best["loo_ssr"] < base["loo_ssr"] - 1e-9),
        improvement=base["loo_ssr"] - best["loo_ssr"])
    print(f"   -> best by LOO: {best['model']} ({best['loo_ssr']:.6f} vs baseline "
          f"{base['loo_ssr']:.6f}); flank adds signal = "
          f"{out['Q1_verdict']['flank_adds_signal']}")

    # ---------------- Q2: SGMC off-catalogue frame --------------------------
    with rasterio.open(G.data_dir() / "external" / "derived_sgmc_faults_100m_u8.tif") as s:
        sgmc = s.read(1) > 0
    dcat = FEAT.dist_px(t.catalogue, 80.0)
    truth_s = (sgmc & t.evaluated & (dcat > M.RANGE_PX))
    K_S = int(truth_s.sum())
    print(f"\n[Q2] SGMC off-catalogue proxy: {K_S:,} trace pixels "
          f"(SGMC traces >300 m from the given catalogue, inside the footprint; contacts may occur)")
    ev = t.evaluated

    def score_dots(dots, truth):
        p = np.where(ev & dots, 1.0, 0.0)
        return M.score(p, truth, ev).as_dict()

    arms = {}
    d28 = np.zeros(shape, bool); d28.ravel()[[o.dot_flat for o in obs if o.id == "d2.8"][0]] = True
    arms["historical d2.8 field (score mapping unverified)"] = d28
    h33 = ROOT.parent / "refs" / "GEMSDOE32" / "docs" / "downloads" / \
        "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    if h33.exists():
        with rasterio.open(h33) as s:
            v = s.read(1)
        arms["H33-labelled reference (score mapping unverified)"] = np.nan_to_num(v) > 0
    # flank arm: dots inside the 1-3 px catalogue halo, ranked by an SGMC/ridge composite
    halo = (dcat > 0) & (dcat <= M.RANGE_PX) & ev
    arms["flank_halo_only (all %d px)" % int(halo.sum())] = halo
    sgmc_only = sgmc & ev & (dcat > M.RANGE_PX)
    arms["sgmc_offcat_only (%d px)" % int(sgmc_only.sum())] = sgmc_only

    q2 = []
    for label, dots in arms.items():
        r = score_dots(dots, truth_s)
        r["arm"] = label
        r["n_dots"] = int(dots.sum())
        q2.append(r)
        print(f"   {label:<38} dots={r['n_dots']:>7,} T={r['TP_w']:>9.1f} F={r['FP_w']:>10.1f} "
              f"recall={r['weighted_recall']:.4f} credit/dot={r['credit_per_unit_mass']:.4f} "
              f"DTI={r['DTI']:.4f}")
    out["Q2_sgmc_offcatalogue_frame"] = dict(K=K_S, definition="USGS SGMC trace pixels "
        ">300 m from the given catalogue and inside the supplied footprint. SGMC includes "
        "non-fault contacts and is only a public proxy; this is not the hidden competition target.",
        arms=q2)

    # ---------------- Q3: blocked catalogue holdout -------------------------
    H, W = shape
    q3 = []
    folds = {"NW": (slice(0, H // 2), slice(0, W // 2)), "NE": (slice(0, H // 2), slice(W // 2, W)),
             "SW": (slice(H // 2, H), slice(0, W // 2)), "SE": (slice(H // 2, H), slice(W // 2, W))}
    print("\n[Q3] spatially blocked holdout on the given catalogue (contaminated frame)")
    for fk, (sy, sx) in folds.items():
        tr = np.zeros(shape, bool); tr[sy, sx] = t.catalogue[sy, sx]
        if tr.sum() == 0:
            continue
        row = {"fold": fk, "K": int(tr.sum())}
        for label, dots in arms.items():
            row[label] = round(M.score(np.where(ev & dots, 1.0, 0.0), tr, ev).DTI, 6)
        q3.append(row)
        print("   fold", fk, {k: v for k, v in row.items() if k not in ("fold", "K")})
    out["Q3_blocked_catalogue_holdout"] = q3
    out["caveat_Q3"] = ("truth IS the given catalogue, so this frame rewards catalogue "
                        "skill and structurally cannot reward a genuinely new fault "
                        "(the same defect GEMSDOE42 logged in registry/irregularities.json)")

    out["seconds"] = round(time.time() - t0, 1)
    (ROOT / "evidence" / "flank_test.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"\nwrote evidence/flank_test.json ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
