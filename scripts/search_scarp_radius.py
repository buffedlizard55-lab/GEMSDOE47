#!/usr/bin/env python3
"""Extend the winning transform (across-strike step, persisted along strike) to long radii.

scripts/search_field.py found that precision-at-40k against Instrument A rises monotonically
with the along-strike persistence half-width r for scarp(det_elev_slope, r):
r=1.5 -> 0.2467, r=2.5 -> 0.3385, r=5 -> 0.4611, r=9 -> 0.5049 (random baseline 0.0861).
A longer run-length is a stricter test of "this is a laterally persistent linear step, not a
stream bank or a fan edge", so the trend is physically expected.  This script finds where it
turns over, on det_elev_slope, det_elev and tmi_hg, and reports the whole precision-at-N curve
because the emission decision is marginal, not a single-N one.

Run:  python3 scripts/search_scarp_radius.py
Out:  evidence/scarp_radius_search.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from gems47s3 import geomorph as G
from gems47s3.detector import Bands

DATA = ROOT / "data"; SURF = DATA / "surfaces"; EV = ROOT / "evidence"
NS = (2_000, 5_000, 10_000, 20_000, 40_000, 80_000, 160_000)

def auc(pos, neg):
    allv = np.concatenate([pos, neg]); o = np.argsort(allv, kind="mergesort"); s = allv[o]
    r = np.empty(allv.size); i = 0
    while i < s.size:
        j = i
        while j + 1 < s.size and s[j+1] == s[i]: j += 1
        r[i:j+1] = 0.5*(i+j)+1.0; i = j+1
    rr = np.empty(allv.size); rr[o] = r
    n1, n2 = pos.size, neg.size
    return float((rr[:n1].sum() - n1*(n1+1)/2)/(n1*n2))

def main():
    t0 = time.time(); rng = np.random.default_rng(99)
    bands = Bands(DATA / "training_features.tif")
    with rasterio.open(DATA/"sample_submission.tif") as ds: fp = np.isfinite(ds.read(1))
    with rasterio.open(DATA/"labels.tif") as ds: cat = ds.read(1) == 1
    iso = np.load(SURF/"A1_isolated.npy"); fla = np.load(SURF/"A2_flanking.npy")
    dcat = ndi.distance_transform_edt(~cat).astype(np.float32)
    T = dict(cat=fp & (dcat <= 3.0),
             A1=fp & (ndi.distance_transform_edt(~iso) <= 3.0),
             A2=fp & (ndi.distance_transform_edt(~fla) <= 3.0))
    valid = fp & np.isfinite(bands("det_elev_slope")) & np.isfinite(bands("det_elev"))
    bg = valid & ~T["cat"]
    smp = lambda m, n: rng.choice(np.nonzero(m.ravel())[0], size=min(n, int(m.sum())), replace=False)
    S = {k: dict(pos=smp(v, 40000), neg=smp(bg, 120000)) for k, v in T.items()}
    print("[setup] " + " ".join(f"{k}={int(v.sum())}" for k, v in T.items()) +
          " random P@40k: " + " ".join(f"{k}={v.sum()/valid.sum():.4f}" for k, v in T.items()))
    rows = []
    for b in ("det_elev_slope", "det_elev", "tmi_hg"):
        z = bands.filled(b, valid)
        for r in (5, 9, 13, 17, 21, 25, 31):
            t = G.rank_scale(np.where(valid, G.scarp_step(z, r), np.nan))
            x = np.where(valid, t, -np.inf).ravel()
            idx = np.argpartition(x, -NS[-1])[-NS[-1]:]
            idx = idx[np.argsort(-x[idx], kind="stable")]
            d = dict(band=b, transform="scarp", radius=r)
            for k, m in T.items():
                fl = m.ravel()
                for n in NS: d[f"P@{n//1000}k_{k}"] = round(float(fl[idx[:n]].mean()), 5)
                d[f"lift@40k_{k}"] = round(d[f"P@40k_{k}"]/(fl[valid.ravel()].sum()/valid.sum()), 3)
                p = t.ravel()[S[k]["pos"]]; q = t.ravel()[S[k]["neg"]]
                d[f"auc_{k}"] = round(auc(p[np.isfinite(p)], q[np.isfinite(q)]), 4)
            rows.append(d)
            print(f"[scarp] {b:16s} r={r:3d} P@40k cat={d['P@40k_cat']:.4f} "
                  f"A1={d['P@40k_A1']:.4f} A2={d['P@40k_A2']:.4f} | P@10k cat={d['P@10k_cat']:.4f} "
                  f"P@160k cat={d['P@160k_cat']:.4f} | AUCcat={d['auc_cat']}  ({time.time()-t0:.0f}s)")
        # signed variant (H47-E) at the best radius
        for r in (9, 17):
            t = G.rank_scale(np.where(valid, np.abs(G.signed_scarp_step(z, r)), np.nan))
            x = np.where(valid, t, -np.inf).ravel()
            idx = np.argpartition(x, -NS[-1])[-NS[-1]:]; idx = idx[np.argsort(-x[idx], kind="stable")]
            d = dict(band=b, transform="signed_scarp_abs", radius=r)
            for k, m in T.items():
                fl = m.ravel()
                for n in NS: d[f"P@{n//1000}k_{k}"] = round(float(fl[idx[:n]].mean()), 5)
                d[f"lift@40k_{k}"] = round(d[f"P@40k_{k}"]/(fl[valid.ravel()].sum()/valid.sum()), 3)
            rows.append(d)
            print(f"[signed] {b:16s} r={r:3d} P@40k cat={d['P@40k_cat']:.4f} A2={d['P@40k_A2']:.4f}")
    out = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               seconds=round(time.time()-t0,1), target_sizes={k:int(v.sum()) for k,v in T.items()},
               random_P40k={k: round(float(v.sum()/valid.sum()),5) for k,v in T.items()},
               candidates=sorted(rows, key=lambda r: -r.get("P@40k_cat", 0)))
    (EV/"scarp_radius_search.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {EV/'scarp_radius_search.json'}  ({time.time()-t0:.0f}s)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
