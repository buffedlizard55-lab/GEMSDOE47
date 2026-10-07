---
title: How to submit
layout: default
nav_order: 2
---

# HOW TO SUBMIT — executive summary

*Generated 2026-10-07 03:26 UTC by `scripts/update_site_h49.py` from
`evidence/submission/bundle_h49.json` and `evidence/h49/conformal_certificate.json`.*

## 1. Download the file

**[`docs/downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif`](downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif)** — one click:

<a href="downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif" download class="btn btn-primary" style="font-size:1.3em;padding:14px 28px;display:inline-block">⬇️ Download `gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif`</a>

| | |
|---|---|
| SHA-256 | `a5abe022b8352971dc2f27a2733f289607d4a9ac44b60335bde7c822826c2a1b` |
| Size | 316,629 bytes |
| Bands / dtype | 1 × float32 |
| CRS | EPSG:32611 (UTM zone 11N) |
| Dimensions | 3730 rows × 3292 cols |
| Transform | `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)` — 100 m pixels |
| nodata tag | **absent** |
| Cell values | every one of the 12,279,160 cells is finite and in [0,1]; values are exactly {0, 1} |
| Positive pixels | 37,612 |

### Verify it yourself before uploading

```bash
python3 -m pip install rasterio numpy
python3 - <<'PY'
import rasterio, numpy as np
with rasterio.open('downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif') as ds:
    a = ds.read(1)
    print(ds.crs, ds.width, ds.height, ds.nodata, tuple(ds.transform)[:6])
    print(a.dtype, np.isfinite(a).all(), a.min(), a.max(), (a > 0).sum())
PY
```

Expected: `EPSG:32611 3292 3730 None (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)` then
`float32 True 0.0 1.0 37612`.

The same 15 checks, run fail-closed against the written bytes, are in
`evidence/submission/checks-h49-gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.json`.

## 2. Upload it

1. Sign in at <https://www.drivendata.org/> and open
   [competition 306 — The Geologic Enhanced Mapping System (GEMS) Prize Challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/).
2. Click **Submissions** in the competition navigation.
3. Choose the file you just downloaded.
4. In **Submission name**, paste:

   ```
   gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3
   ```

5. In **Note (optional)** (146/200 characters), paste:

   ```
   Signed-polarity scarp field; 37,612 dots, 2.8px/280m spacing, 300m off known-fault flanks; spacing certified by split conformal, 90% floor 0.0318.
   ```

## 3. What the number in that note means — and what it does not

The note reports the **split-conformal guarantee of the operating point**, which is the number a
Phase 2 reviewer can check against the evidence in this repository:

| Quantity | Value | Where it comes from |
|---|---|---|
| Spacing / operating point | 2.8 px (280 m), 7.37 per 1,000 scored px, 300 m catalogue-flank buffer | `evidence/h49/conformal_certificate.json` |
| Confidence level | 90 % (α = 0.1) | one-sided split conformal, Lei et al. JASA 2018 |
| **Guaranteed minimum holdout DTI** | **0.03184** per 8×8 spatial block | Instrument B (SGMC faults > 300 m from the given catalogue), 19 calibration blocks, order statistic k = 18 |
| Same quantity, corroborating instrument | 0.01828 | Instrument A (PM0200, catalogue-derived) |
| Leave-one-out worst floor | 0.01793 | recomputed with each calibration block removed |
| Floors at other levels | 0.05 → 0.01793, 0.10 → 0.03184, 0.20 → 0.05783, 0.25 → 0.05824, 0.30 → 0.07383 | α grid |
| Procedure audit | 400 independent re-splits; floor p05 0.01793; mean violation rate 0.081 vs nominal α = 0.1 | whole select-then-certify procedure re-run |

**Not claimed:** no leaderboard score, no private-label guarantee, no claim that the certificate's
exchangeability unit (a spatial block) is geologically exchangeable in fact. The metric the
organiser scores is not this instrument.
