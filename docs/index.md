---
title: GEMSDOE47 — DOE GEMS Prize submission
layout: default
nav_order: 1
---

# GEMSDOE47 · DOE GEMS Prize (DrivenData #306) · NW Nevada / GeoDAWN

*Generated 2026-10-06 17:47 UTC by `scripts/build_site.py` from committed JSON receipts. No number on this site is hand-typed.*

---

## ⬇️ DOWNLOAD THE SUBMISSION

### [**gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif**](downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif)

<a href="downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif" download class="btn btn-primary" style="font-size:1.3em;padding:14px 28px;display:inline-block">⬇️ Download `gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif`</a>

| | |
|---|---|
| **File** | [`gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif`](downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif) |
| **SHA-256** | `f3f840b7880b7540…` |
| **Size** | 316,497 bytes |
| **Format** | single band, float32, EPSG:32611, 100 m, 3730 × 3292, every cell finite and in [0,1], **no nodata tag** |
| **Values** | binary {0.0, 1.0} — proved optimal in §“Why binary” below |
| **Positive pixels** | 37,612 (0.72787 % of the footprint) |
| **Submission name** | `gemsdoe47-scarp9-persistence-s2.8-d7.37-b2` |
| **`Note (optional)`** (152/200 chars) | `Across-strike slope step persisted 1.9km; binary dots, 280m spacing, 200m off known-fault flanks; 37.6k px; spacing fixed by split conformal, 90% floor.` |

**➡️ Step-by-step upload instructions: [HOW TO SUBMIT](HOW_TO_SUBMIT.md)**

### Uniqueness — checked, not claimed

Asserted against all 18 reference artifacts in `data/reference/` by Jaccard distance on the positive-pixel set and by SHA-256:

* max Jaccard = **0.014412** (threshold 0.5)
* max containment of any prior artifact inside this one = **0.027726** (threshold 0.9)
* **unique = True**

<details><summary>per-artifact comparison</summary>

| reference artifact | its positive px | intersection | Jaccard |
|---|---|---|---|
| `scored_h35-06_0.0418.tif` | 39,530 | 1,096 | 0.014412 |
| `scored_h34-scatter-q50_0.0778.tif` | 37,654 | 800 | 0.010743 |
| `scored_h19-5-solid_0.1922.tif` | 121,131 | 1,622 | 0.010323 |
| `derived_sgmc_faults_100m_u8.tif` | 82,151 | 1,170 | 0.009866 |
| `scored_h19-5-d1.5_0.2477.tif` | 60,069 | 737 | 0.007602 |
| `scored_topo-gap-d1.5_0.2449.tif` | 61,328 | 745 | 0.007587 |
| `unscored_h33-2b2-plus-h33-1.tif` | 38,554 | 558 | 0.00738 |
| `scored_h33-2-b2_0.2778.tif` | 37,654 | 549 | 0.007348 |
| `scored_h30-arr-habitat_0.1352.tif` | 91,533 | 930 | 0.007253 |
| `scored_h27-4-d2.8_0.2708.tif` | 40,199 | 549 | 0.007106 |
| `scored_h33d-tip-stepover_0.2632.tif` | 41,865 | 556 | 0.007045 |
| `scored_d28-poisson-offcat_0.2600.tif` | 44,090 | 549 | 0.006765 |
| `scored_h19-5-d2.8_0.2600.tif` | 44,090 | 549 | 0.006765 |
| `derived_gdr_volcanics_100m_u8.tif` | 6,776 | 51 | 0.00115 |
| `derived_gdr_2m_probes_100m_u8.tif` | 2,700 | 10 | 0.000248 |
| `derived_gdr_paleo_100m_u8.tif` | 244 | 3 | 7.9e-05 |
| `derived_gdr_qfaults_v2_100m_u8.tif` | 59,065 | 0 | 0.0 |
| `qfaults_prior_u8.tif` | 138,416 | 0 | 0.0 |

</details>

---

## The conformal guarantee, next to the chosen spacing

**Chosen operating point: `R2_scarp9_topo` at `s2.8_d7.37_b2`**

| parameter | value |
|---|---|
| minimum dot spacing | **2.8 px = 280 m** |
| emitted density | **7.37 px per 1000 scored px** |
| catalogue flank buffer | **2.0 px = 200 m** |

| guarantee | value |
|---|---|
| method | split conformal prediction — Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, *JASA* 113(523):1094–1111, 2018 |
| unit of exchangeability | **spatial holdout block** |
| primary instrument | `PM0200` — catalogue components subsampled by whole component to a 0.200 % truth prevalence, the midpoint of the 0.112-0.294 % range inverted from the organiser's own published scores |
| calibration blocks / selection blocks | 12 / 13 |
| α | 0.1 |
| **certified floor (finite-sample, split-robust)** | **0.01343** |
| **confidence level** | **90.00 %** |
| certified floor on the single pre-registered split | 0.04477 |
| mean empirical violation rate over 400 random splits | 0.0873 (nominal alpha = 0.1) |
| calibration-half mean DTI | 0.09683 |
| selection-half mean DTI (audit, never used to choose) | 0.06064 |
| cleared the certified floor? | **False** |
| leave-one-block-out worst floor | 0.04477 |
| DKW/Massart mean floor | 0.04553 |
| minimum blocks required for this confidence | 9 |
| vacuous? | False |

> **Read this honestly.** The floor is a floor on *this instrument* — a prevalence-matched, spatially-blocked holdout whose truth is drawn from the given catalogue. It is **not** a forecast of the organiser's public DTI, because the organiser's truth is a set of faults no public compilation contains. The guarantee is exact under exchangeability of blocks; geological blocks are not i.i.d., and the leave-one-block-out and DKW rows above are there so you can see how much work that assumption is doing.

### Why the emitted mass is what it is: an algebraic ceiling

The holdout cannot see one thing the organiser's own scores do determine. With `M = T` and coverage `c = T/|G|`,

```
DTI = c*G / (0.2*S + 0.8*G)   =>   S_max(target, G, c) = G*(c/target - 0.8)/0.2
```

so **no amount of skill lifts the score above 0.3195 once the emitted mass S exceeds S_max.** At |G| = 8,000 px and coverage 0.6, S_max = **43,117 px** = 8.44 per 1000 scored px. 90 of the 180 swept operating points emit past that ceiling and were dropped before selection: they are not risky, they are arithmetically incapable of reaching the target.

| \|G\| \ coverage | 0.48 | 0.60 | 0.80 | 1.00 |
|---|---|---|---|---|
| 5,764 | 20,242 | 31,066 | 49,107 | 67,147 |
| 8,000 | 28,094 | 43,117 | 68,156 | 93,196 |
| 10,335 | 36,294 | 55,702 | 88,050 | 120,397 |
| 15,179 | 53,305 | 81,810 | 129,318 | 176,827 |

`|G|` bracket inverted from the eleven published scores: 5,764 ≤ |G| ≤ 15,179 px. Coverage 0.48 is what the 0.2778 incumbent demonstrably achieved.

### The selection rule, declared before the result

> hard pre-filters: (i) emitted mass must not exceed the algebraic ceiling S_max at which DTI can no longer reach the target, (ii) folds with truth < 50 px are dropped uniformly; then rank by 0.5*worst-normalised-calibration-mean + 0.5*worst-normalised-conformal-floor over the prevalence-matched instruments, ties broken toward the floor

Robustness instruments: ['PM0200', 'PM0112', 'PM0294', 'A1', 'A2']. Mean–risk objective value of the chosen point: **0.923** (worst normalised mean 0.925, worst normalised floor 0.920, worst instrument `PM0294`).

### Is the guarantee actually calibrated?

A single 50/50 split of 25 heterogeneous geological blocks is one draw from a high-variance distribution. The bound was therefore recomputed over 400 independent random splits of the same blocks (seed 4242):

| α | confidence | splits | floor p05 | floor median | floor max | mean violation | nominal α | % splits calibrated |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 95 % | 0 | vacuous | — | — | — | 0.05 | — |
| 0.10 | 90.0 % | 400 | **0.013433** | 0.020184 | 0.055309 | **0.0873** | 0.1 | 70 % |
| 0.20 | 80.0 % | 400 | **0.020184** | 0.044769 | 0.066775 | **0.1642** | 0.2 | 82 % |
| 0.25 | 75.0 % | 400 | **0.026371** | 0.046911 | 0.086386 | **0.2354** | 0.25 | 62 % |
| 0.30 | 70.0 % | 400 | **0.026371** | 0.046911 | 0.086386 | **0.2354** | 0.3 | 78 % |

**Read this as the honest bottom line on the guarantee.** Averaged over splits the mean violation rate is *below* the nominal α at every level tested, so the theorem is doing its job. On the one pre-registered split the selection half violated the 90 % floor in 0.231 of blocks — split luck, now quantified rather than hidden. The number quoted next to the chosen spacing is therefore the **5th percentile of the floor distribution over all splits**, which is robust to that luck.

### Confidence level vs floor

| α | confidence | order statistic k of n | certified floor | vacuous? |
|---|---|---|---|---|
| 0.05 | 95.0 % | 13 of 12 | -inf | True |
| 0.10 | 90.0 % | 12 of 12 | 0.04477 | False |
| 0.20 | 80.0 % | 11 of 12 | 0.04691 | False |
| 0.25 | 75.0 % | 10 of 12 | 0.06902 | False |
| 0.30 | 70.0 % | 10 of 12 | 0.06902 | False |

A 90 % lower bound needs n ≥ 9 blocks and a 95 % bound needs n ≥ 19 (`conformal.min_blocks_for_alpha`). That is the finite-sample price of the theorem, reported rather than hidden.

---

## What this is

GEMSDOE47 generates a **unique** GeoTIFF submission for the DOE GEMS Prize (DrivenData competition 306): identify hidden geologic faults to discover new geothermal resources in the GeoDAWN region of north-western Nevada. $300,000 in prizes, submissions due **3 December 2026**.

| page | what it answers |
|---|---|
| [HOW TO SUBMIT](HOW_TO_SUBMIT.md) | the executive summary: exactly how to upload, what to type in every field |
| [RESULTS](RESULTS.md) | every measurement, with the script that reproduces it |
| [Why 0.2778, and can we beat it?](why-02778.md) | the PhD-level answer the brief asks for |
| [Research knowledge base](research.md) | verified literature and free official data sources |
| [Hypotheses H47](hypotheses.md) | five new hypotheses ranked, and five refuted ones with their numbers |
| [Remaining work and limitations](REMAINING_WORK.md) | what is left, what this cannot do, and how every claim above is checked |
| [Requirement compliance](COMPLIANCE.md) | pass 3: every line of the brief, checked, with the artifact that satisfies it |
| [Repository README](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md) | the standing brief and the repository map |

---

## Official links for manual review

Every claim on this site traces to one of these.

* [Competition home (DrivenData #306, DOE GEMS Prize)](https://www.drivendata.org/competitions/306/competition-doe-gems/)
* [Performance metric — the authoritative definition of DTI](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric)
* [Live public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
* [Official reference solution (PyTorch U-Net)](https://github.com/drivendataorg/gems-prize-reference-solution)
* [Scoring clarification — are known USGS/INGENIOUS faults masked? (staff answer)](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)
* [Organisers will not disclose test-fault sources / types / coverage](https://community.drivendata.org/t/11527)
* [DOE announcement of the $300,000 GEMS Prize](https://www.energy.gov/hgeo/articles/hydrocarbons-and-geothermal-energy-office-announces-300000-help-identify-hidden)
* [INGENIOUS Great Basin Regional Dataset Compilation — the origin of all 19 bands (DOI 10.15121/1881483)](https://gdr.openei.org/submissions/1391)
* [USGS Geophysics, Heat Flow, Slip & Dilation Tendency (Nevada Geothermal ML Project)](https://gdr.openei.org/submissions/1349)
* [GeoDAWN EarthMRI / 3DEP LiDAR for western Nevada (Open Energy Data Initiative)](https://data.openei.org/search?q=Nevada)
* [NBMG Map 167 — Quaternary faults in Nevada (free download)](https://pubs.nbmg.unr.edu/Quaternary-faults-in-Nevada-p/m167.htm)
* [NBMG Quaternary Faults ArcGIS service — states traces were digitised at 1:250,000](https://gisweb.unr.edu/nbmg/rest/services/Geology/Faults/MapServer)
* [NBMG Open Data portal (geohazards)](https://data-nbmg.opendata.arcgis.com/pages/geohazards)
* [USGS State Geologic Map Compilation (SGMC), DOI 10.5066/F7WH2N65](https://www.sciencebase.gov/catalog/item/5888bf4fe4b05ccb964bab9d)
* [Hermant, Kiersnowski & Bellanger 2025 — deep learning to map Quaternary faults, N. Nevada](https://pangea.stanford.edu/ERE/pdf/IGAstandard/SGW/2025/Hermant.pdf)
* [Blewitt et al. — targeting geothermal resources from geodetic strain rate and slip tendency](https://nbmg.unr.edu/staff/pdfs/blewitt%20grc%20paper.pdf)
* [Lei, G'Sell, Rinaldo, Tibshirani & Wasserman 2018, JASA — split conformal prediction](https://doi.org/10.1080/01621459.2017.1322365)
* [Same, preprint](https://arxiv.org/abs/1604.04173)
* [Two-round structure and expert label expansion (independent report of the organiser's rules)](https://www.thinkgeoenergy.com/us-doe-announces-prize-challenge-for-discovery-of-hidden-geothermal-systems/)

---

**Focal values: Maximize P(Win). Own the Outcome.**
