---
title: How to submit
layout: default
nav_order: 2
---

# HOW TO SUBMIT — executive summary

*Generated 2026-10-07 06:20 UTC by `scripts/update_site_h49.py` from
`evidence/submission/bundle_h49.json` and `evidence/h49/conformal_certificate.json`.*

> **Promotion gate closed. The file is downloadable for research review, but do not submit it or spend a competition slot.** Format validation, scientific validation, uniqueness scope and organizer acceptance are separate.

## 1. Download the file

**[`docs/downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif`](downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif)** — one click:

<a href="downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif" download class="btn btn-primary" style="font-size:1.3em;padding:14px 28px;display:inline-block">⬇️ Download `gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif`</a>

| | |
|---|---|
| SHA-256 | `f2cec409ce3bec5a2805f1fab9a12ab7f72394f8be79cc365134ce43708c6060` |
| Size | 409,124 bytes |
| Bands / dtype | 1 × float32 |
| CRS | EPSG:32611 (UTM zone 11N) |
| Dimensions | 3730 rows × 3292 cols |
| Transform | `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)` — 100 m pixels |
| nodata tag | **absent** |
| Cell values | every one of the 12,279,160 cells is finite and in [0,1]; values are exactly {0, 1} |
| Positive pixels | 37,612 |

### Verify format independently (this does not authorize submission)

```bash
python3 -m pip install rasterio numpy
python3 - <<'PY'
import rasterio, numpy as np
with rasterio.open('downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif') as ds:
    a = ds.read(1)
    valid = ds.read_masks(1) > 0
    masked = ds.read(1, masked=True)
    print(ds.crs, ds.width, ds.height, ds.nodata, tuple(ds.transform)[:6])
    print(a.dtype, np.isfinite(a).all(), a.min(), a.max(), (a > 0).sum())
    print(valid.sum(), np.ma.getmaskarray(masked).sum())
PY
```

Expected: EPSG:32611, 3292 × 3730, no nodata tag, exact 100 m affine, raw finite values in
[0,1], 37612 positives, a self-contained mask over exactly
5,167,373 official-footprint cells, and masked reads null exactly outside.
This checks format, not science, uniqueness beyond the recorded bounded audit, portal acceptance or slot authorization.

The same 19/19 gating checks pass when run fail-closed against the written bytes; the separate informational whole-grid range flag is True. The receipt is in
`evidence/submission/checks-h49-gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.json`.

## 2. Exact submission sequence — only after a future candidate clears every gate

The current H49 candidate is **not authorized to upload**. Preserve a slot until a future candidate has passed the preregistered spatial-holdout, format and bounded-uniqueness checks.

1. Sign in at <https://www.drivendata.org/> and open
   [competition 306 — The Geologic Enhanced Mapping System (GEMS) Prize Challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/).
2. Click **Submissions** in the competition navigation.
3. Choose only the exact TIFF for a candidate whose scientific, format and bounded-uniqueness gates passed. The present H49 TIFF is research-only; do not select it for submission.
4. For an authorized future candidate, paste its exact registered **Submission name**:

   ```
   gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3
   ```

5. The present H49 note below is shown for audit, not submission. Do not paste it or the current name unless a future re-evaluation opens the gate. For an authorized future candidate, use its reviewed note (168/200 characters):

   ```
   H49 polarity-scarp field; 37,612 dots, 2.8px spacing. Nominal 90% Instrument-B split-conformal floor 0.0318; post-hoc rule provenance and exchangeability caveats apply.
   ```

## 3. What the number in the research note means — and what it does not

The note reports a **nominal fixed-arm split-conformal order statistic**, not a claim that the
complete adaptive selection procedure has a valid guarantee. It is a public-proxy diagnostic:

| Quantity | Value | Where it comes from |
|---|---|---|
| Spacing / operating point | 2.8 px (280 m), 7.37 per 1,000 scored px, 300 m catalogue-flank buffer | `evidence/h49/conformal_certificate.json` |
| Confidence label | nominal 90 % (α = 0.1) | split conformal, Lei et al. JASA 2018; requires exchangeable spatial blocks |
| **Nominal fixed-arm lower statistic** | **0.03184** per 8×8 Instrument-B block | 19 calibration blocks, order statistic k = 18; valid only if arm/rule is fixed independently of calibration outcomes |
| Corroborating Instrument-A statistic | 0.01828 | PM0200 catalogue-derived proxy; not private labels |
| Leave-one-out sensitivity | 0.01793 | recomputed with each calibration block removed |
| Floors at other nominal levels | 0.05 → 0.01793, 0.10 → 0.03184, 0.20 → 0.05783, 0.25 → 0.05824, 0.30 → 0.07383 | α grid |
| Repartition diagnostic | 400 re-partitions reuse the same 39 blocks; floor p05 0.01793; mean violation rate 0.081 vs nominal α = 0.1 | stability/sensitivity only; not new samples |

**Not claimed:** no leaderboard score, no private-label guarantee, and no proof that a spatial
block is exchangeable. The mean rule was adopted after the sweep; the 400 re-partitions reuse the
same 39 blocks. The 90% paired-difference conformal lower bound versus the incumbent is negative
for both arms. The complete promotion gate is closed: do not spend a slot on this candidate.
