#!/usr/bin/env python3
"""Exploratory permutation control for the LATI single-layer screen.

The screen ranked ``dcat_band_0_1.5`` (evaluated pixels within 1.5 px of the
given catalogue) first among geological layers. That layer is geometrically
thin, and a thin layer can produce a concentrated fitted q; the in-sample rank
may therefore reflect concentration as well as spatial alignment with the
owner-reported score/raster associations.

For each geological layer, generate ``--n-random`` spatially permuted copies.
A permutation preserves the exact multiset of rank values and tie structure
while disrupting spatial arrangement. Beating this finite permutation sample is
a diagnostic of association under this fit only. It does not authenticate the
score/file links, prove the LATI instrument or model valid, establish causality,
or validate private-target performance; ten draws are not a calibrated
significance test.

    python3 scripts/lati_controls.py [--n-random 12] [--top 20]
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

LEVELS = 256
K_LO, K_HI, BMAX = 2_000.0, 60_000.0, 12.0


L2 = 1e-5   # weak ridge; must be small because |beta| can legitimately reach ~12,
            # and the penalty enters the residual vector as sqrt(l2)*beta.


def fit_one(U, rows, obs):
    bm = lati.BinnedSoftmax(U, rows, obs, LEVELS if len(rows) == 1 else 32)
    f = bm.fit(l2=L2, bmax=BMAX, k_lo=K_LO, k_hi=K_HI)
    # report the UNPENALISED sum of squared DTI residuals (comparable across layers)
    pred = bm.predict(np.array(f["theta"]))
    f["ssr"] = float(np.sum((pred - bm.dti_obs) ** 2))
    f["ssr_penalised"] = float(np.sum(np.asarray(
        np.concatenate([pred - bm.dti_obs, np.sqrt(L2) * np.asarray(f["theta"][1:])])) ** 2))
    return f, bm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-random", type=int, default=12)
    ap.add_argument("--top", type=int, default=16, help="layers to test against the null")
    ap.add_argument("--frac", type=float, default=0.02,
                    help="reported only: top fraction of a layer that carries its mass")
    ap.add_argument("--out", default=str(ROOT / "evidence" / "lati_controls.json"))
    args = ap.parse_args()

    t0 = time.time()
    obs = lati.load_observations(verbose=False)
    st = FEAT.build_stack(verbose=False)
    U, names = st["U"], list(st["names"])
    n = U.shape[1]
    prev = json.loads((ROOT / "evidence" / "lati_fit.json").read_text())
    screen = [r for r in prev["single_layer_screen"] if not r["is_control"]]
    screen.sort(key=lambda r: r["ssr"])
    targets = screen[:args.top]
    print(f"[ctrl] testing {len(targets)} layers against matched-size random nulls "
          f"({args.n_random} draws each, top {args.frac:.0%} of each layer)")

    bm0 = lati.BinnedSoftmax(U, [], obs, 1)
    f0 = bm0.fit(l2=L2, bmax=BMAX, k_lo=K_LO, k_hi=K_HI)
    f0["ssr"] = float(np.sum((bm0.predict(np.array(f0["theta"])) - bm0.dti_obs) ** 2))
    print(f"[ctrl] uniform baseline SSR={f0['ssr']:.6f} K={f0['K']:,.0f}")

    rng = np.random.default_rng(4747)
    out = {"instrument": "LATI matched-size thinness control",
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "n_random_draws": args.n_random,
           "null_construction": "spatial permutation of the layer's own rank values "
                                "(preserves the marginal distribution and tie structure, "
                                "disrupts spatial arrangement)",
           "interpretation_scope": "Finite-permutation diagnostic for owner-reported score/raster fit only; does not authenticate pairings, prove the LATI instrument/model valid, establish causality, or validate private-target performance. Ten draws are not a calibrated significance test.",
           "uniform_baseline_ssr": f0["ssr"], "uniform_baseline_K": f0["K"],
           "n_evaluated_pixels": int(n), "layers": []}

    for rec in targets:
        j = rec["index"]
        layer = U[j]
        k_high = int((layer >= 255).sum())
        f, bm = fit_one(U, [j], obs)
        nulls = []
        for _ in range(args.n_random):
            r = layer[rng.permutation(n)]          # same multiset, no spatial signal
            Un = np.concatenate([U, r[None, :]])
            fn, _ = fit_one(Un, [len(names)], obs)
            nulls.append(dict(ssr=fn["ssr"], K=fn["K"], beta=fn["theta"][1]))
        ns = np.array([x["ssr"] for x in nulls])
        nk = np.array([x["K"] for x in nulls])
        z = float((ns.mean() - f["ssr"]) / ns.std()) if ns.std() > 0 else float("inf")
        beat = int((f["ssr"] < ns).sum())
        row = dict(layer=rec["layer"], ssr=f["ssr"], K=f["K"], beta=f["theta"][1],
                   n_pixels_at_top_rank=k_high,
                   null_ssr_mean=float(ns.mean()), null_ssr_sd=float(ns.std()),
                   null_ssr_min=float(ns.min()), null_ssr_max=float(ns.max()),
                   null_K_mean=float(nk.mean()),
                   z_vs_null=z, draws_beaten=f"{beat}/{args.n_random}",
                   verdict=("BEATS_ALL_TESTED_PERMUTATIONS" if beat == args.n_random else
                            ("PARTIAL_PERMUTATION_COMPARISON" if beat >= args.n_random * 0.75
                             else "NO_CLEAR_PERMUTATION_ADVANTAGE")))
        out["layers"].append(row)
        print(f"  {rec['layer']:<28} SSR={f['ssr']:.6f} K={f['K']:>8,.0f} | null "
              f"{ns.mean():.6f}+-{ns.std():.6f} (min {ns.min():.6f}) K_null={nk.mean():>8,.0f} "
              f"-> beat {beat}/{args.n_random}  z={z:+.2f}  {row['verdict']}", flush=True)

    out["seconds"] = round(time.time() - t0, 1)
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(f"\nwrote {args.out} ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
