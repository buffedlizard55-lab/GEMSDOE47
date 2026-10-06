#!/usr/bin/env python3
"""Control experiment: is the winning transform just a proxy for ruggedness?

``scripts/transform_search.py`` selected ``lrm(det_elev_slope, r=9)`` with off-catalogue
precision 0.2603 against a random baseline of 0.0829.  A Local Relief Model is by
construction a ruggedness measure, and the off-catalogue target (USGS SGMC traces > 300 m
from the given catalogue) is itself concentrated in exposed, rugged terrain because that is
where geologists map contacts.  So the honest question is not "does LRM beat random" but

    does LRM beat the RUGGEDNESS IT CONTAINS?

Three controls are run, all against Instrument B (off-catalogue SGMC) and Instrument A
(the given catalogue):

  C1  stratified AUC -- compute the tie-aware AUC of LRM *within* deciles of the local mean
      slope and of the local mean elevation.  If LRM only encodes "this is a mountain", the
      within-stratum AUC collapses to 0.5.
  C2  partial precision -- regress out the ruggedness covariate by ranking within strata,
      then take the global top 40,000 of the within-stratum rank.  Precision of that set is
      the precision of LRM at matched ruggedness.
  C3  ruggedness-only baseline -- the local mean of det_elev_slope and the local mean of
      det_elev, scored the same way.  These are the pure "is it rugged / is it high" fields.

Run:  python3 scripts/control_lrm.py
Out:  evidence/control_lrm.json
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
from gems47s3 import geomorph as G
from gems47s3.spec import BAND_INDEX, FEATURE_INVALID_BELOW

DATA = ROOT / "data"
EV = ROOT / "evidence"


def midrank_auc(pos, neg):
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


def within_stratum_rank(a: np.ndarray, strata: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Rank ``a`` within each stratum to a uniform [0,1] marginal (strata-adjusted score)."""
    out = np.full(a.shape, np.nan, np.float32)
    for s in np.unique(strata[valid]):
        m = valid & (strata == s)
        if m.sum() < 500:
            continue
        v = a[m]
        srt = np.sort(v)
        out[m] = (np.searchsorted(srt, v, side="right") / float(srt.size)).astype(np.float32)
    return out


def precision_at(f: np.ndarray, valid: np.ndarray, target: np.ndarray, n: int = 40000) -> float:
    x = np.where(valid, np.nan_to_num(f, nan=-np.inf), -np.inf)
    idx = np.argpartition(x.ravel(), -n)[-n:]
    return float(target.ravel()[idx].mean())


def main() -> int:
    t0 = time.time()
    rng = np.random.default_rng(3)
    with rasterio.open(DATA / "training_features.tif") as ds:
        elev = ds.read(BAND_INDEX["det_elev"] + 1).astype(np.float64)
        slope = ds.read(BAND_INDEX["det_elev_slope"] + 1).astype(np.float64)
    with rasterio.open(DATA / "labels.tif") as ds:
        cat = ds.read(1) == 1
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        fp = np.isfinite(ds.read(1))
    for a in (elev, slope):
        a[~np.isfinite(a)] = np.nan
        a[a < FEATURE_INVALID_BELOW] = np.nan
    valid = fp & np.isfinite(elev) & np.isfinite(slope)
    elev = np.where(valid, elev, np.nanmedian(elev[valid])).astype(np.float32)
    slope = np.where(valid, slope, np.nanmedian(slope[valid])).astype(np.float32)

    dcat = ndi.distance_transform_edt(~cat).astype(np.float32)
    cat3 = fp & (dcat <= 3.0)
    with rasterio.open(DATA / "reference" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
    offcat = fp & sgmc & (dcat > 3.0)
    off3 = fp & (ndi.distance_transform_edt(~offcat) <= 3.0)
    bg = valid & ~cat3 & ~off3

    # ---------------- the selected transform and the ruggedness-only baselines
    lrm = G.rank_scale(np.where(valid, G.lrm(slope, 9.0), np.nan))
    lrm_e = G.rank_scale(np.where(valid, G.lrm(elev, 9.0), np.nan))
    scarp = G.rank_scale(np.where(valid, G.scarp_step(slope, 2), np.nan))
    rugged = G.rank_scale(ndi.uniform_filter(slope, 19, mode="nearest"))     # local mean slope
    height = G.rank_scale(ndi.uniform_filter(elev, 19, mode="nearest"))      # local mean elevation
    print(f"[setup] off3={int(off3.sum())} cat3={int(cat3.sum())} bg={int(bg.sum())} "
          f"({time.time()-t0:.0f}s)")

    fields = dict(lrm_slope_r9=lrm, lrm_elev_r9=lrm_e, scarp_slope_r2=scarp,
                  ruggedness_only=rugged, height_only=height,
                  lrm_x_rugged=lrm * rugged,
                  lrm_over_rugged=np.clip(lrm - 0.5 * rugged, 0, 1).astype(np.float32))

    # ---------------- C3: raw precision / AUC
    def smp(mask, n):
        idx = np.nonzero(mask.ravel())[0]
        return rng.choice(idx, size=min(n, idx.size), replace=False)
    P = dict(off=smp(off3, 60000), cat=smp(cat3, 60000))
    N = smp(bg, 250000)

    rows = []
    for name, f in fields.items():
        r = dict(field=name,
                 precision_top40k_offcat=round(precision_at(f, valid, off3), 5),
                 precision_top40k_catalogue=round(precision_at(f, valid, cat3), 5),
                 auc_off=round(midrank_auc(f.ravel()[P["off"]], f.ravel()[N]), 4),
                 auc_cat=round(midrank_auc(f.ravel()[P["cat"]], f.ravel()[N]), 4))
        rows.append(r)
        print(f"[C3] {name:18s} P@40k_off={r['precision_top40k_offcat']:.4f} "
              f"AUCoff={r['auc_off']:.4f} P@40k_cat={r['precision_top40k_catalogue']:.4f}")

    # ---------------- C1 + C2: stratify by ruggedness and by height
    strat_results = {}
    for sname, sfield in (("mean_slope_decile", rugged), ("mean_elevation_decile", height)):
        strata = np.zeros(valid.shape, np.int16)
        q = np.quantile(sfield[valid], np.linspace(0, 1, 11))
        strata[valid] = np.clip(np.searchsorted(q, sfield[valid], side="right") - 1, 0, 9)
        adj = within_stratum_rank(lrm, strata, valid)
        within = []
        for s in range(10):
            m = valid & (strata == s)
            p = off3 & m; n = bg & m
            if p.sum() < 200 or n.sum() < 2000:
                continue
            pi = smp(p, 20000); ni = smp(n, 60000)
            within.append(dict(stratum=int(s), n_off=int(p.sum()), n_bg=int(n.sum()),
                               auc_lrm_within=round(midrank_auc(lrm.ravel()[pi], lrm.ravel()[ni]), 4)))
        strat_results[sname] = dict(
            within_stratum_auc=within,
            mean_within_stratum_auc=round(float(np.mean([w["auc_lrm_within"] for w in within])), 4),
            strata_adjusted_precision_top40k_offcat=round(precision_at(adj, valid, off3), 5),
            strata_adjusted_precision_top40k_catalogue=round(precision_at(adj, valid, cat3), 5),
            strata_adjusted_auc_off=round(midrank_auc(adj.ravel()[P["off"]][np.isfinite(adj.ravel()[P["off"]])],
                                                      adj.ravel()[N][np.isfinite(adj.ravel()[N])]), 4),
        )
        sr = strat_results[sname]
        print(f"[C1] {sname:24s} mean within-stratum AUC(LRM) = {sr['mean_within_stratum_auc']:.4f}")
        for w in within:
            print(f"       stratum {w['stratum']}: n_off={w['n_off']:6d} AUC={w['auc_lrm_within']:.4f}")
        print(f"[C2] {sname:24s} strata-adjusted P@40k_off = "
              f"{sr['strata_adjusted_precision_top40k_offcat']:.4f} "
              f"(unadjusted {rows[0]['precision_top40k_offcat']:.4f})  ({time.time()-t0:.0f}s)")

    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        seconds=round(time.time() - t0, 1),
        random_baseline_P40k_offcat=round(float(off3.sum() / valid.sum()), 5),
        n_off3=int(off3.sum()), n_cat3=int(cat3.sum()), n_background=int(bg.sum()),
        controls=rows, stratified=strat_results,
        interpretation=(
            "If LRM were only a ruggedness proxy, mean_within_stratum_auc would be ~0.50 and the "
            "strata-adjusted precision would fall to the random baseline.  Read those two numbers "
            "against controls[ruggedness_only] and random_baseline_P40k_offcat."),
    )
    (EV / "control_lrm.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {EV/'control_lrm.json'}   ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
