#!/usr/bin/env python3
"""Tie-aware skill audit of every derived surface, cached artifact and field variant.

A surface can look excellent under a naive rank statistic and be worthless: if it is a
plateau over 99 % of the grid, a searchsorted-'left' rank reports ~1.0 for ANY subset.  This
script therefore reports, for every surface:

  * plateau_fraction -- share of valid pixels sitting at the single most common value
  * distinct_values
  * auc -- tie-aware Mann-Whitney AUC against the catalogue dilated by 1 px (Instrument A
    skill: does it find MAPPED faults?)
  * auc_offcat -- the same against USGS SGMC faults that lie > 300 m from the given catalogue
    (Instrument B skill: does it find REAL faults the catalogue lacks?  This is the
    population the organiser actually scores.)
  * precision_at_40k -- the fraction of the top 40,000 pixels that are within 3 px of an
    off-catalogue real fault, i.e. the quantity the metric actually pays for.

Run:  python3 scripts/diagnose_surfaces.py
Out:  evidence/surface_skill.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DATA = ROOT / "data"
SURF = DATA / "surfaces"
REF = DATA / "reference"
EV = ROOT / "evidence"


def midrank_auc(pos: np.ndarray, neg: np.ndarray) -> float:
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    allv = np.concatenate([pos, neg])
    order = np.argsort(allv, kind="mergesort")
    srt = allv[order]
    ranks = np.empty(allv.size, np.float64)
    i = 0
    while i < srt.size:
        j = i
        while j + 1 < srt.size and srt[j + 1] == srt[i]:
            j += 1
        ranks[i:j + 1] = 0.5 * (i + j) + 1.0
        i = j + 1
    r = np.empty(allv.size, np.float64)
    r[order] = ranks
    n1, n2 = pos.size, neg.size
    return float((r[:n1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n2))


def audit(name: str, a: np.ndarray, ctx: dict) -> dict:
    a = np.asarray(a, np.float64)
    valid = ctx["valid"] & np.isfinite(a)
    if valid.sum() < 1000:
        return dict(surface=name, skipped="too few valid pixels")
    vals = a[valid]
    uv, uc = np.unique(vals, return_counts=True)
    plateau = float(uc.max() / uc.size)
    d = dict(surface=name, valid_px=int(valid.sum()), distinct_values=int(uv.size),
             plateau_fraction=round(plateau, 5),
             plateau_value=float(uv[np.argmax(uc)]),
             min=float(vals.min()), p50=float(np.median(vals)), p99=float(np.quantile(vals, .99)),
             max=float(vals.max()))
    for key, mask in (("catalogue_1px", ctx["pos_cat"]), ("offcatalogue_sgmc", ctx["pos_off"]),
                      ("volcanics_offcat", ctx["pos_vol"])):
        p = a.ravel()[mask["pos"]]; n = a.ravel()[mask["neg"]]
        p = p[np.isfinite(p)]; n = n[np.isfinite(n)]
        d[f"auc_{key}"] = round(midrank_auc(p, n), 4)
    # precision of the top-40k at the metric's own 300 m support
    for key, target in (("top40k_offcat", ctx["off3"]), ("top40k_catalogue", ctx["cat3"])):
        f = np.where(valid, a, -np.inf)
        n = 40000
        idx = np.argpartition(f.ravel(), -n)[-n:]
        d[f"precision_{key}"] = round(float(target.ravel()[idx].mean()), 5)
        d[f"recall_{key}"] = round(float(target.ravel()[idx].sum() / max(target.sum(), 1)), 5)
    return d


def main() -> int:
    t0 = time.time()
    rng = np.random.default_rng(11)
    valid = np.load(SURF / "valid.npy")
    cat = np.load(SURF / "catalogue.npy")
    fp = np.load(SURF / "footprint.npy")
    dcat = ndi.distance_transform_edt(~cat).astype(np.float32)
    cat3 = fp & (dcat <= 3.0)
    off3 = None
    with rasterio.open(REF / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
    offcat = fp & sgmc & (dcat > 3.0)
    off3 = fp & (ndi.distance_transform_edt(~offcat) <= 3.0)
    with rasterio.open(REF / "derived_gdr_volcanics_100m_u8.tif") as ds:
        vol = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
    voloff = fp & vol & (dcat > 3.0)

    def sample(mask, n):
        idx = np.nonzero(mask.ravel())[0]
        return rng.choice(idx, size=min(n, idx.size), replace=False)

    bg = fp & ~cat3 & ~off3
    ctx = dict(
        valid=valid,
        pos_cat=dict(pos=sample(cat3, 60000), neg=sample(bg, 300000)),
        pos_off=dict(pos=sample(off3, 60000), neg=sample(bg, 300000)),
        pos_vol=dict(pos=sample(voloff, 20000), neg=sample(bg, 300000)),
        cat3=cat3, off3=off3,
    )
    print(f"[setup] cat3={int(cat3.sum())} offcat_sgmc={int(offcat.sum())} "
          f"off3={int(off3.sum())} volcanics_offcat={int(voloff.sum())} bg={int(bg.sum())}")

    rows = []
    targets = sorted(SURF.glob("*.npy"))
    targets += sorted(REF.glob("scored_*.tif")) + sorted(REF.glob("unscored_*.tif"))
    for p in targets:
        if p.suffix == ".npy":
            if p.name in ("catalogue.npy", "footprint.npy", "scored.npy", "valid.npy",
                          "d_catalogue.npy", "theta.npy"):
                continue
            a = np.load(p).astype(np.float32)
        else:
            with rasterio.open(p) as ds:
                a = np.nan_to_num(ds.read(1).astype(np.float32))
        rows.append(audit(p.name, a, ctx))
        r = rows[-1]
        print(f"[audit] {p.name:56s} plateau={r['plateau_fraction']:.3f} "
              f"AUCcat={r['auc_catalogue_1px']:.4f} AUCoff={r['auc_offcatalogue_sgmc']:.4f} "
              f"P@40k_off={r['precision_top40k_offcat']:.4f}  ({time.time()-t0:.0f}s)")

    rows.sort(key=lambda r: -(r.get("precision_top40k_offcat") or 0))
    out = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               seconds=round(time.time() - t0, 1),
               note=("auc_* are tie-aware Mann-Whitney AUCs; precision_top40k_* is the fraction "
                     "of the 40,000 highest-scoring footprint pixels lying within 3 px (300 m, "
                     "the metric's kernel support) of the named target population."),
               surfaces=rows)
    EV.mkdir(parents=True, exist_ok=True)
    (EV / "surface_skill.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {EV/'surface_skill.json'}   ({time.time()-t0:.0f}s)")
    print(f"\n{'surface':56s} {'AUCcat':>7s} {'AUCoff':>7s} {'P@40k_off':>10s} {'P@40k_cat':>10s}")
    for r in rows[:22]:
        print(f"{r['surface'][:56]:56s} {r['auc_catalogue_1px']:7.4f} "
              f"{r['auc_offcatalogue_sgmc']:7.4f} {r['precision_top40k_offcat']:10.4f} "
              f"{r['precision_top40k_catalogue']:10.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
