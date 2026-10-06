#!/usr/bin/env python3
"""Which of the 19 official bands actually carries information at the 300 m scale?

The metric resolves 300 m (3 px).  A band whose structure is smooth on, say, 100 km scales
cannot place a fault to within 300 m no matter how it is filtered -- it can only be used as
a slow regional prior.  This measures, per band and without any modelling:

  * the fraction of the band's variance that survives removal of a sigma=3 px (300 m)
    smooth  ->  ``hf_frac``: the part of the signal that lives AT the metric's scale;
  * the lag-1/2/3 px normalised autocorrelation  ->  how fast the band decorrelates;
  * the tie-aware AUC (Mann-Whitney with 0.5 credit for ties) of the band, and of its
    300 m-scale residual, against the catalogue dilated by 1 px  ->  does it detect mapped
    faults at all?

Tie-aware AUC is used deliberately: several derived surfaces here are dominated by plateaus,
and a searchsorted 'left' rank silently reports AUC ~1.0 for a constant surface.  That
artefact was found and fixed in this repository; the corrected statistic is
``auc = (mean rank with ties averaged - correction)`` computed by scipy-free midranking.

Run:  python3 scripts/diagnose_bands.py
Out:  evidence/band_scale_diagnostics.json
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


def midrank_auc(pos: np.ndarray, neg: np.ndarray) -> float:
    """Mann-Whitney AUC with exact tie handling (ties score 0.5)."""
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
        ranks[i:j + 1] = 0.5 * (i + j) + 1.0          # average rank, 1-based
        i = j + 1
    r = np.empty(allv.size, np.float64)
    r[order] = ranks
    rp = r[:pos.size].sum()
    n1, n2 = pos.size, neg.size
    return float((rp - n1 * (n1 + 1) / 2.0) / (n1 * n2))


def main() -> int:
    t0 = time.time()
    EV.mkdir(parents=True, exist_ok=True)
    with rasterio.open(DATA / "labels.tif") as ds:
        cat = ds.read(1) == 1
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        fp = np.isfinite(ds.read(1))
    catd = ndi.binary_dilation(cat, np.ones((3, 3), bool))
    # a subsample keeps the AUC computation tractable and its standard error tiny
    rng = np.random.default_rng(7)
    pos_all = np.nonzero(catd.ravel())[0]
    neg_all = np.nonzero((fp & ~ndi.binary_dilation(catd, np.ones((5, 5), bool))).ravel())[0]
    pos_sel = rng.choice(pos_all, size=min(60_000, pos_all.size), replace=False)
    neg_sel = rng.choice(neg_all, size=min(300_000, neg_all.size), replace=False)
    print(f"[setup] catalogue-dilated positives {pos_all.size} (sampled {pos_sel.size}), "
          f"background negatives {neg_all.size} (sampled {neg_sel.size})")

    rows = []
    with rasterio.open(DATA / "training_features.tif") as ds:
        for i, (name, desc) in enumerate(FEATURE_BANDS, start=1):
            a = ds.read(i).astype(np.float64)
            a[~np.isfinite(a)] = np.nan
            a[a < FEATURE_INVALID_BELOW] = np.nan
            v = fp & np.isfinite(a)
            vals = a[v]
            med = float(np.median(vals))
            filled = np.where(v, a, med)
            sm = ndi.gaussian_filter(filled, 3.0, mode="nearest")
            resid = (filled - sm)[v]
            var_tot = float(np.var(vals - vals.mean()))
            var_hf = float(np.var(resid))
            hf = var_hf / var_tot if var_tot > 0 else 0.0
            # lag autocorrelations on the valid domain
            ac = {}
            for lag in (1, 2, 3, 5, 10, 30):
                sh = ndi.shift(filled, (0, lag), mode="nearest")
                both = v & np.isfinite(sh)
                x = filled[both]; y = sh[both]
                ac[f"lag{lag}px"] = round(float(np.corrcoef(x, y)[0, 1]), 5)
            # AUC of the raw band and of its 300 m-scale residual, vs the mapped catalogue
            raw_pos = a.ravel()[pos_sel]; raw_neg = a.ravel()[neg_sel]
            okp = np.isfinite(raw_pos); okn = np.isfinite(raw_neg)
            auc_raw = midrank_auc(raw_pos[okp], raw_neg[okn])
            rr = (filled - sm)
            auc_hf = midrank_auc(rr.ravel()[pos_sel], rr.ravel()[neg_sel])
            aa = np.abs(rr)
            auc_abs_hf = midrank_auc(aa.ravel()[pos_sel], aa.ravel()[neg_sel])
            rows.append(dict(band=name, description=desc, valid_px=int(v.sum()),
                             median=med, var_total=var_tot, hf_variance_fraction=round(hf, 6),
                             autocorr=ac, auc_raw=round(auc_raw, 4),
                             auc_300m_residual_signed=round(auc_hf, 4),
                             auc_300m_residual_abs=round(auc_abs_hf, 4)))
            print(f"[{i:2d}/{len(FEATURE_BANDS)}] {name:22s} hf={hf:7.4f} "
                  f"lag1={ac['lag1px']:.4f} lag3={ac['lag3px']:.4f} lag30={ac['lag30px']:.4f} "
                  f"AUCraw={auc_raw:.4f} AUC|hf|={auc_abs_hf:.4f}  ({time.time()-t0:.0f}s)")

    rows.sort(key=lambda r: -r["auc_300m_residual_abs"])
    out = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               purpose=("measure which official bands carry structure at the metric's own "
                        "300 m scale and whether they detect mapped faults"),
               n_positive_sample=int(pos_sel.size), n_negative_sample=int(neg_sel.size),
               bands=rows,
               reading=("hf_variance_fraction is the share of a band's variance that survives "
                        "removal of a 300 m smooth.  A band with hf ~ 0 cannot localise a fault "
                        "to within the kernel support and can only act as a regional prior. "
                        "auc_300m_residual_abs is the tie-aware AUC of |band - smooth(band)| "
                        "against the catalogue dilated by 1 px; 0.5 means no skill."),
               )
    (EV / "band_scale_diagnostics.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {EV/'band_scale_diagnostics.json'}   ({time.time()-t0:.0f}s)")
    print("\n--- ranked by AUC of the 300 m-scale residual ---")
    print(f"{'band':22s} {'hf_frac':>8s} {'lag3px':>8s} {'AUCraw':>8s} {'AUC|hf|':>8s}")
    for r in rows:
        print(f"{r['band']:22s} {r['hf_variance_fraction']:8.4f} {r['autocorr']['lag3px']:8.4f} "
              f"{r['auc_raw']:8.4f} {r['auc_300m_residual_abs']:8.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
