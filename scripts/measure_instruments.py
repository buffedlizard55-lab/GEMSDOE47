#!/usr/bin/env python3
"""Measure the target populations and build the A1/A2 held-out component split.

Reproduces every number in knowledge/02_the_two_instruments_measure_different_populations.md
and writes the pixel sets the sweep consumes:

  data/surfaces/A1_isolated.npy   held-out-eligible catalogue components that are ALONE in
                                  their 300 m dilation (flank prune cannot destroy them)
  data/surfaces/A2_flanking.npy   catalogue components that SHARE a 300 m dilation with
                                  another component (the "newly mapped geometry of an
                                  existing fault system" population, S13)
  data/surfaces/offcat_sgmc.npy   USGS SGMC traces > 300 m from the given catalogue
                                  (Instrument B, measured and REJECTED for selection)
  evidence/instrument_populations.json

Run:  python3 scripts/measure_instruments.py
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
from gems47s3.spec import FEATURE_BANDS, FEATURE_INVALID_BELOW

DATA = ROOT / "data"
SURF = DATA / "surfaces"
EV = ROOT / "evidence"
STRUCT8 = np.ones((3, 3), bool)


def main() -> int:
    t0 = time.time()
    SURF.mkdir(parents=True, exist_ok=True)
    EV.mkdir(parents=True, exist_ok=True)

    with rasterio.open(DATA / "labels.tif") as ds:
        cat = ds.read(1) == 1
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        fp = np.isfinite(ds.read(1))
    dcat = ndi.distance_transform_edt(~cat).astype(np.float32)
    cat3 = fp & (dcat <= 3.0)

    with rasterio.open(DATA / "reference" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
    offcat = fp & sgmc & (dcat > 3.0)
    off3 = fp & (ndi.distance_transform_edt(~offcat) <= 3.0)
    np.save(SURF / "offcat_sgmc.npy", offcat)

    # ---------------- A1 / A2: are catalogue components alone in their 300 m dilation?
    comp_lab, n_comp = ndi.label(cat, structure=STRUCT8)
    dilated = ndi.binary_dilation(cat, iterations=3, structure=STRUCT8)
    dil_lab, n_dil = ndi.label(dilated, structure=STRUCT8)
    # how many DISTINCT catalogue components touch each dilated blob
    ys, xs = np.nonzero(cat)
    dl = dil_lab[ys, xs]
    cl = comp_lab[ys, xs]
    order = np.argsort(dl, kind="stable")
    dl_s, cl_s = dl[order], cl[order]
    bounds = np.searchsorted(dl_s, np.arange(n_dil + 2))
    comp_is_flanking = np.zeros(n_comp + 1, bool)
    for b in range(1, n_dil + 1):
        seg = cl_s[bounds[b]:bounds[b + 1]]
        if seg.size == 0:
            continue
        u = np.unique(seg)
        if u.size > 1:
            comp_is_flanking[u] = True
    flanking = comp_is_flanking[comp_lab] & cat
    isolated = ~flanking & cat
    np.save(SURF / "A1_isolated.npy", isolated)
    np.save(SURF / "A2_flanking.npy", flanking)
    n_flank_comp = int(np.unique(comp_lab[flanking]).size) - 1
    n_iso_comp = int(np.unique(comp_lab[isolated]).size) - 1

    A1_3 = fp & (ndi.distance_transform_edt(~isolated) <= 3.0)
    A2_3 = fp & (ndi.distance_transform_edt(~flanking) <= 3.0)
    print(f"[A1/A2] components total {n_comp}: isolated {n_iso_comp} "
          f"({int(isolated.sum())} px), flanking {n_flank_comp} ({int(flanking.sum())} px)")
    print(f"[A1/A2] 300 m halos: A1_3={int(A1_3.sum())} px, A2_3={int(A2_3.sum())} px")

    # ---------------- the population table
    bg = fp & ~cat3
    table = []
    with rasterio.open(DATA / "training_features.tif") as ds:
        descs = list(ds.descriptions)
        for i, (name, _) in enumerate(FEATURE_BANDS, start=1):
            a = ds.read(i).astype(np.float64)
            a[~np.isfinite(a)] = np.nan
            a[a < FEATURE_INVALID_BELOW] = np.nan
            v = fp & np.isfinite(a)
            if v.sum() < 1000:
                continue
            srt = np.sort(a[v])

            def rk(mask, _a=a, _v=v, _srt=srt):
                x = _a[mask & _v]
                return float(np.searchsorted(_srt, x).mean() / _srt.size) if x.size else None
            table.append(dict(band=name, description=descs[i - 1],
                              background_p50=round(float(np.median(a[bg & v])), 4),
                              catalogue_p50=round(float(np.median(a[cat3 & v])), 4),
                              offcat_sgmc_p50=round(float(np.median(a[off3 & v])), 4),
                              rank_catalogue=round(rk(cat3), 4) if rk(cat3) else None,
                              rank_offcat_sgmc=round(rk(off3), 4) if rk(off3) else None,
                              rank_A1_isolated=round(rk(A1_3), 4) if rk(A1_3) else None,
                              rank_A2_flanking=round(rk(A2_3), 4) if rk(A2_3) else None))
            print(f"[table] {name:22s} cat={table[-1]['rank_catalogue']} "
                  f"off={table[-1]['rank_offcat_sgmc']} A1={table[-1]['rank_A1_isolated']} "
                  f"A2={table[-1]['rank_A2_flanking']}  ({time.time()-t0:.0f}s)")

    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        seconds=round(time.time() - t0, 1),
        populations=dict(
            footprint=int(fp.sum()), catalogue=int(cat.sum()),
            catalogue_within_300m=int(cat3.sum()),
            sgmc_offcatalogue=int(offcat.sum()), sgmc_offcatalogue_within_300m=int(off3.sum()),
            overlap_cat3_off3=int((cat3 & off3).sum()),
            components_total=int(n_comp),
            A1_isolated_components=int(n_iso_comp), A1_isolated_px=int(isolated.sum()),
            A2_flanking_components=int(n_flank_comp), A2_flanking_px=int(flanking.sum()),
            A1_300m_halo=int(A1_3.sum()), A2_300m_halo=int(A2_3.sum()),
            random_baseline_precision_at_40k=dict(
                catalogue=round(float(cat3.sum() / fp.sum()), 5),
                sgmc_offcatalogue=round(float(off3.sum() / fp.sum()), 5),
                A1=round(float(A1_3.sum() / fp.sum()), 5),
                A2=round(float(A2_3.sum() / fp.sum()), 5)),
        ),
        band_population_table=table,
        conclusion=("SGMC off-catalogue is high, steep, shallow-basement terrain (exposed "
                    "mountain bedrock); the given catalogue is close to background on elevation "
                    "and sediment thickness. The two populations are nearly disjoint in terrain "
                    "space, so Instrument B measures 'is this a mountain' and is rejected for "
                    "selection. See knowledge/02."),
    )
    (EV / "instrument_populations.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {EV/'instrument_populations.json'}   ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
