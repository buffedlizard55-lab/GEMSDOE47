---
title: How to submit
layout: default
nav_order: 2
---

# HOW TO SUBMIT — executive summary

*Generated 2026-10-06 19:58 UTC by `scripts/build_site.py`.*

## 1. Download the file

**[`docs/downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif`](downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif)** — one click:

<a href="downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif" download class="btn btn-primary" style="font-size:1.3em;padding:14px 28px;display:inline-block">⬇️ Download `gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif`</a>

| | |
|---|---|
| SHA-256 | `f3f840b7880b7540ac6260b6b791ea55b2a875646c28401b01960096dc2da291` |
| Size | 316,497 bytes |
| Bands / dtype | 1 × float32 |
| CRS | EPSG:32611 (UTM zone 11N) |
| Dimensions | 3730 rows × 3292 cols |
| Transform | `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)` — 100 m pixels |
| nodata tag | **absent** |
| Cell values | every one of the 12,279,160 cells is finite and in [0,1]; min exactly 0.0, max exactly 1.0 |
| Positive pixels | 37,612 |

### Verify it yourself before uploading

```bash
pip install --break-system-packages rasterio numpy
python3 - <<'PY'
import rasterio, numpy as np
with rasterio.open('downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif') as ds:
    a = ds.read(1)
    print(ds.crs, ds.width, ds.height, ds.nodata, tuple(ds.transform)[:6])
    print(a.dtype, np.isfinite(a).all(), a.min(), a.max(), (a > 0).sum())
PY
```

Expected: `EPSG:32611 3292 3730 None (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)` then `float32 True 0.0 1.0 37612`.

The same fifteen checks, run fail-closed against the written bytes, are in `evidence/submission/checks-*-gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.json`.

## 2. Upload it

1. Sign in at <https://www.drivendata.org/> and open [competition 306 — The Geologic Enhanced Mapping System (GEMS) Prize Challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/).
2. Click **Submissions** in the competition navigation.
3. Choose the file you just downloaded.
4. In **Submission name**, paste:

   ```
   gemsdoe47-scarp9-persistence-s2.8-d7.37-b2
   ```

5. In **Note (optional)** (152/200 characters), paste:

   ```
   Across-strike slope step persisted 1.9km; binary dots, 280m spacing, 200m off known-fault flanks; 37.6k px; spacing fixed by split conformal, 90% floor.
   ```

6. Submit. The portal validates the raster server-side before scoring.

### Rules that affect how you spend the slot

* **Three submissions per rolling 7-day window**; **one final selection per entity** is scored at the close of the Initial Prize Round. Verify on the competition's Rules page before submitting — this is the family's recorded reading, not a quotation.
* The **same submission** is scored twice: against a private expert-labelled test set (Initial Round, $50 k + top 5 × $10 k) and again against an expanded label set built from expert review of **all** submissions (Final Round, $100/70/40/25/15 k). Only the top five advance. ([independent report](https://www.thinkgeoenergy.com/us-doe-announces-prize-challenge-for-discovery-of-hidden-geothermal-systems/))
* Submissions close **3 December 2026**.
* Generative-AI use is allowed but **must be disclosed**. This repository discloses it: the code, the analysis and these documents were produced with an AI coding agent; every number is reproducible by a committed script from the official rasters.

## 3. What was chosen, and with what guarantee

**Operating point `R2_scarp9_topo` / `s2.8_d7.37_b2`**

* minimum dot spacing **2.8 px (280 m)**
* emitted density **7.37 px per 1000 scored px**
* catalogue flank buffer **2.0 px (200 m)**

**Split conformal guarantee (Lei et al., *JASA* 2018, [DOI](https://doi.org/10.1080/01621459.2017.1322365)):** with 12 calibration blocks, a fresh spatial block's DTI is at least **0.04477** with probability ≥ **90.00 %**.

Quoted floor basis: **repeated_split_p05**. On the single pre-registered split the floor is 0.04477; over 400 independent random splits of the same blocks the 5th percentile is 0.01343, and that is the number quoted, because one split of 25 heterogeneous geological blocks is one draw from a high-variance distribution. The mean violation rate over those splits is 0.0873 against a nominal alpha of 0.1, so the theorem is empirically calibrated.

The selection half (13 blocks, never used to choose) realised a mean DTI of **0.06064**.

The operating point was chosen by maximising the **conformal floor**, not the calibration mean, and then by a max-min robustness criterion across five holdout instruments — because ranking by the mean selects the noisiest high mean, which is the failure mode the brief names.

**This floor is a floor on the holdout instrument, not a forecast of the public leaderboard score.** See [RESULTS](RESULTS.html#what-the-holdout-can-and-cannot-say).

## 4. Why the format is what it is

The portal rejection `"Predicted values must be in range [0, 1]"` has two distinct mechanisms, and both are closed:

1. **a value outside [0,1].** The official `training_features.tif` stores its 7,113,320 out-of-footprint cells as the float32 sentinel `-3.4028234663852886e38`. Any pipeline that carries a band value through unmasked, or normalises by a minimum that is the sentinel, writes that value out.
2. **a `nodata` tag whose value is outside [0,1]** — `nan`, or the sentinel. A validator can read the tag itself as a predicted value.

The shipped raster therefore writes **every one of the 12,279,160 cells as a finite float32 in [0,1] with no nodata tag at all**. Outside the footprint the confidence is `0.0`, which is a legal value in [0,1] and cannot trip a range check. This is the configuration shared by all six reference artifacts that never drew a format complaint (three further artifacts do carry `nodata=nan` and 7,111,787 NaN cells and were still scored, so NaN is *accepted* — it is simply one validator change away from mechanism 2, and there is nothing to gain from the risk).

`src/gems47s3/raster.py::validate_submission` re-opens the written bytes — it never trusts the in-memory array that was written — and gates fifteen checks fail-closed.

### Why the values are binary and not a probability map

For a pixel of value `v` whose best-cover kernel weight is `w`, adding it changes `TP_w` by `v·w` and the denominator by `α·v = 0.2·v`. **`v` cancels out of the sign**, so `dDTI > 0 ⟺ w > 0.2·DTI` regardless of `v`. Down-weighting a pixel that clears the bar only shrinks its gain; up-weighting one that misses only enlarges the penalty. A `{0,1}` mask is the optimum of the entire soft family. Tested in `tests/test_metric_s3.py::test_binary_is_optimal_over_soft_scaling`, and consistent with practice: **all eleven scored reference artifacts are exactly `{0.0, 1.0}`.**
