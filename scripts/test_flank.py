#!/usr/bin/env python3
"""Exploratory H47 flank-model comparison and public-frame diagnostics.

Q1  Compare the 12-row owner-reported LATI LOO fit with and without catalogue
    flank layers. This is a model-specific association screen, not a causal
    ablation or private-target validation. H33-2-B2 is not included as an
    authenticated score pair.

Q2  Compare rasters on a public USGS SGMC off-catalogue frame. These are public
    mapped faults, not organizer-authenticated hidden labels; the comparison is
    descriptive and cannot alone promote or falsify a candidate.

Q3  Report a four-quadrant holdout on the given catalogue only as a contaminated
    diagnostic: because its truth is the catalogue, it rewards the opposite
    skill and is never used as the project promotion gate.

    python3 scripts/test_flank.py
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
    out = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "observation_scope": {
            "owner_reported_pairs_in_q1": len(obs),
            "h33_score_file_mapping_verified": False,
            "interpretation": "Q1 is an exploratory 12-row LOO comparison; local SGMC/catalogue frames are screening proxies, not organizer-authenticated private truth",
        },
    }

    # ---------------- Q1 ----------------------------------------------------
    extra = {
        "prox_d2.8": prox_layer(obs, "d2.8", ev_idx, shape),
        "dcat_band_0_1.5": U[names.index("dcat_band_0_1.5")],
        "dcat_band_1.5_3": U[names.index("dcat_band_1.5_3")],
        "sgmc_offcat_prox": U[names.index("sgmc_offcat_prox")],
        "sgmc_offcat": U[names.index("sgmc_offcat")],
    }
    combos = [
        ("owner-reported d2.8 reference-field-only", ["prox_d2.8"]),
        ("d2.8 reference + flank 0-1.5px", ["prox_d2.8", "dcat_band_0_1.5"]),
        ("d2.8 reference + flank 0-3px", ["prox_d2.8", "dcat_band_0_1.5", "dcat_band_1.5_3"]),
        ("d2.8 reference + flank + SGMC", ["prox_d2.8", "dcat_band_0_1.5", "dcat_band_1.5_3",
                                             "sgmc_offcat_prox"]),
        ("flank + SGMC (no d2.8 reference field)", ["dcat_band_0_1.5", "dcat_band_1.5_3", "sgmc_offcat_prox"]),
    ]
    q1 = []
    print("[Q1] does adding catalogue-flank features reduce LOO error in this exploratory fit to owner-reported rows?")
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
        flank_reduces_loo_error_in_exploratory_fit=bool(best["loo_ssr"] < base["loo_ssr"] - 1e-9),
        loo_ssr_reduction=base["loo_ssr"] - best["loo_ssr"])
    print(f"   -> lowest LOO error: {best['model']} ({best['loo_ssr']:.6f} vs baseline "
          f"{base['loo_ssr']:.6f}); exploratory-fit reduction = "
          f"{out['Q1_verdict']['flank_reduces_loo_error_in_exploratory_fit']}")

    # ---------------- Q2: SGMC off-catalogue frame --------------------------
    with rasterio.open(G.data_dir() / "external" / "derived_sgmc_faults_100m_u8.tif") as s:
        sgmc = s.read(1) > 0
    dcat = FEAT.dist_px(t.catalogue, 80.0)
    truth_s = (sgmc & t.evaluated & (dcat > M.RANGE_PX))
    K_S = int(truth_s.sum())
    print(f"\n[Q2] SGMC off-catalogue frame: {K_S:,} truth pixels "
          f"(USGS SGMC faults >300 m from the given catalogue, inside the footprint)")
    ev = t.evaluated

    def score_dots(dots, truth):
        p = np.where(ev & dots, 1.0, 0.0)
        return M.score(p, truth, ev).as_dict()

    arms = {}
    d28 = np.zeros(shape, bool); d28.ravel()[[o.dot_flat for o in obs if o.id == "d2.8"][0]] = True
    arms["owner-reported d2.8 reference (DTI 0.2600; no organizer receipt)"] = d28
    h33 = ROOT / ".cache" / "gems_data" / "reference" / "h33-2-b2-zeros.tif"
    if h33.exists():
        digest = hashlib.sha256(h33.read_bytes()).hexdigest()
        if digest != "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9":
            raise SystemExit("H33 reference raster SHA-256 mismatch")
        with rasterio.open(h33) as s:
            if s.count != 1 or not G.dataset_matches_template_grid(s, t):
                raise SystemExit("H33 reference raster grid does not match the competition template")
            v = s.read(1)
        arms["H33-2-B2 reference raster (score/file mapping unverified)"] = np.nan_to_num(v) > 0
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
    out["Q2_sgmc_offcatalogue_frame"] = dict(K=K_S, definition="USGS SGMC fault pixels "
        ">300 m from the competition catalogue, inside the sample_submission footprint, "
        "excluding masked catalogue pixels", arms=q2)

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
    (ROOT / "evidence" / "flank_test.json").write_text(json.dumps(out, indent=1, default=float, allow_nan=False))
    print(f"\nwrote evidence/flank_test.json ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
