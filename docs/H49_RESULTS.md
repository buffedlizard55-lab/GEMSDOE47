# H49 round — exploratory public-proxy research (not a submission certificate)

> **RESEARCH ONLY · NOT SLOT-AUTHORIZED · DO NOT UPLOAD.** The exact TIFF is preserved for auditability, but its local read-back has 12,279,160/12,279,160 finite cells, no NaNs, no NoData tag, and a valid GDAL mask on every cell. The original build receipt records a 5,167,373-cell footprint, leaving 7,111,787 outside cells finite rather than null/NaN. It fails the published outside-null/NaN requirement. See the [deployed format-audit copy](data/h49-format-contract-audit.json) and the [canonical evidence copy](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/evidence/h49/format-contract-audit.json).

The prior optional portal-note draft is withdrawn. **Do not copy it into a portal.** No submission slot was authorized or used. This report preserves the research measurements but corrects the prior promotion, attribution, and format claims.

## Provenance and scope

The H49 inputs are hash-pinned **owner-supplied mirror** bytes, not organizer-authenticated inputs. Instrument A uses held-out components of the supplied public catalogue; Instrument B uses USGS SGMC traces more than 300 m from that catalogue. Both are public proxy instruments, not the competition's private truth or a verified sample of its scoring population. SGMC also includes pre-Quaternary and lithologic contacts, which can favor topographic detectors.

The 0.2778 comparator is an **owner-reported d2.8 reference raster**. The association between that raster and a participant-reported score is unverified; it is not an authenticated leaderboard incumbent. All H49 comparisons with it are local proxy measurements only.

## The two proxy instruments

- **Instrument A** (`evidence/sweep/sweep_h49.json`): 39 usable 8×8 spatial blocks, 15,555 scored rows, and five prevalence-matched instruments built from the supplied catalogue (PM0200, PM0112, PM0294, A1, A2). It measures ordering against mapped catalogue components and is optimistic for topographic fields.
- **Instrument B** (`evidence/sweep/sweep_h49b.json`): 39 usable 8×8 blocks, 4,719 scored rows; truth is whole USGS SGMC components more than 3 px (300 m) from the supplied catalogue, prevalence-matched to `p0200`. Masking the given catalogue reproduces a geometric mask used in the challenge; it does **not** make SGMC a proxy proven representative of hidden scoring labels.

The reported split allocated 20 blocks to selection and 19 to calibration. The split-conformal calculation below is **conditional on block-score exchangeability**, which is unverified geologically. It is a proxy estimate, not a guarantee for private labels, a full map, or a leaderboard score.

## Selected operating point and post-hoc amendment

`R7_scarp9_polarity` · `disk` · spacing **2.8 px (280 m)** · density **7.37 per 1,000 scored pixels** · catalogue-flank buffer **3 px (300 m)**.

The H49-B addendum preregistered maximizing a nominal 90% floor on the selection half. The later reported operating point instead maximizes the selection-half mean on Instrument B, after an audit of 400 repeated splits was examined. That is a **post-hoc rule amendment**. Reusing these same 39 blocks for the repeated-split analysis does not create an independent validation set; formal coverage for the post-hoc amended selection process is not established. The preregistered choice (`R2_scarp9_topo` / `oriented4` / `s3.6_d14_b2`) had a separate calculated Instrument-B lower-bound estimate of 0.05519, also conditional on the same assumptions.

## Nominal split-conformal calculation — assumption-conditional only

The reported calculation is **nominal 90%** (`α = 0.10`, `n = 19` calibration blocks, order statistic `k = 18`). Its Instrument-B lower-bound estimate is **0.03184**; Instrument A's corresponding estimate is 0.01828. These numbers describe the calculation on this public proxy split only. Because exchangeability is unverified and the operating rule was amended after inspecting repeated-split results, do **not** call either number a certified, guaranteed, private-target, or map-wide performance floor.

| Quantity | Instrument B (SGMC off-catalogue proxy) | Instrument A (PM0200 catalogue proxy) |
|---|---:|---:|
| Assumption-conditional lower-bound estimate, nominal 90% | **0.03184** | 0.01828 |
| Estimate at nominal 95% (`α = 0.05`) | 0.01793 | vacuous |
| Estimate at nominal 80% (`α = 0.20`) | 0.05783 | 0.03595 |
| Estimate at nominal 75% (`α = 0.25`) | 0.05824 | 0.03893 |
| Estimate at nominal 70% (`α = 0.30`) | 0.07383 | 0.04854 |
| Calibration-half mean (minimum) | 0.10090 (0.01793) | 0.08607 |
| Selection-half mean (minimum) | 0.10329 (0.00708) | 0.07553 |
| Leave-one-out worst estimate | 0.01793 | 0.01828 |
| DKW mean lower bound using fixed DTI support [0,1] | **0.00000** | **0.00000** |
| Calibration / selection blocks below the calculated estimate | 1 / 1 of 19 / 20 | 0 / 1 |
| Empirical violation rate, calibration / selection | 0.0526 / 0.0500 | 0.0000 / 0.0526 |

**DKW correction:** the mean-bound support is the metric's known `[0,1]` range. The former formula multiplied the DKW radius by the observed calibration min-to-max range, which is not a valid population-support bound. The previously reported 0.04098 (Instrument B) and 0.03801 (PM0200) values are retracted; using the full support and clipping at zero gives 0.00000 for both, establishing no positive mean lower bound. DKW also requires iid calibration draws, which is not verified for these heterogeneous spatial blocks; the post-results arm amendment independently prevents a full-procedure claim. This mean calculation is distinct from the one-block split-conformal order statistic above.

The reported repeated-split audit used 400 of 400 requested re-splits of the same blocks (selection included): lower-bound estimate p05 0.01793, median 0.03847, mean 0.04391; mean violation rate on the non-calibration half 0.0807 versus nominal `α = 0.10`, median 0.0526. **43.5%** of those re-splits had a violation rate above nominal alpha. These are descriptive stability diagnostics, not new independent samples or a validation of the amended rule.

## Local proxy comparisons — not promotion gates

The archived calculations show a selection-half mean of 0.10329 for the selected point versus 0.05750 for a fixed-seed random proxy control. Against the **owner-reported d2.8 reference raster**, the corresponding local proxy mean is 0.07108. Neither comparison is a leaderboard comparison, an authenticated-incumbent comparison, or evidence that H49 beats the established spatially blocked holdout best.

A paired blockwise calculation of H49-minus-reference DTI also fails to show a positive lower bound. The nominal 90% split-conformal lower prediction statistics for one future paired block are **−0.03342 on the 20-block selection half** and **−0.01050 on the 19-block calibration half**. The selection half was used to choose the H49 arm, so its value is descriptive; the calibration result is conditional on a fixed arm and exchangeable blocks, assumptions that do not repair the post-results amendment. The reference is labelled H33 in the local evidence, but its participant-score/file association remains unverified. These are not confidence bounds on a mean, leaderboard scores, or evidence of positive improvement.

| Historical calculation | Value | Correct interpretation |
|---|---:|---|
| Nominal 90% fixed-arm split-conformal lower statistic (H49 self-score) | 0.03184 | Proxy calculation; conditional on unverified exchangeability and subject to the post-hoc amendment; not an improvement bound versus the reference |
| Fixed-seed random proxy selection-half mean | 0.05750 | Local public-proxy control only |
| Owner-reported d2.8 reference proxy selection-half mean | 0.07108 | Comparator identity/score mapping unverified; not a leaderboard incumbent |
| Selected H49 proxy selection-half mean | 0.10329 | Public proxy result; not private/global performance |

## Preserved artifact and bounded novelty check

- File: [`gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif`](downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif), retained as research evidence only.
- SHA-256: `a5abe022b8352971dc2f27a2733f289607d4a9ac44b60335bde7c822826c2a1b`; 316,629 bytes.
- Local grid read-back: one float32 band, 3292 × 3730, EPSG:32611, 100 m; 37,612 positive unit dots. These properties do not cure the outside-null/NaN failure above.
- The earlier comparison covered 16 repository rasters: maximum Jaccard 0.292575 and maximum containment 0.452701. This is a **bounded local comparison**, not proof of global uniqueness or scientific novelty.
- The previous `all_checks_passed` builder receipt is retained as historical evidence. Its finiteness check did not establish that outside-footprint cells were null or NaN. The corrected read-back and scope are recorded in [`format-contract-audit.json`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/evidence/h49/format-contract-audit.json).

### Density sweep retained from the original report

These are reported block-sweep summaries, not performance forecasts. Instrument B remains a public SGMC proxy with the provenance and domain limitations described above.

**Instrument B** — `R7_scarp9_polarity`, `disk`, 2.8 px, 300 m flank:

| Density / 1,000 scored px | Mean block DTI | Pooled DTI | Truth recall | Emitted px per block (mean) |
|---:|---:|---:|---:|---:|
| 2 | 0.04705 | 0.04774 | 0.0464 | 261 |
| 4 | 0.07595 | 0.07898 | 0.0905 | 523 |
| 7.37 | 0.10213 | 0.10552 | 0.1515 | 963 |
| 14 | 0.09930 | 0.09757 | 0.1947 | 1828 |
| 25 | 0.08995 | 0.08814 | 0.1983 | 2225 |
| 40 | 0.08995 | 0.08814 | 0.1983 | 2225 |

**Instrument A** — `R7_scarp9_polarity`, `disk`, 2.8 px, 300 m flank:

| Density / 1,000 scored px | Mean block DTI | Pooled DTI | Truth recall | Emitted px per block (mean) |
|---:|---:|---:|---:|---:|
| 4 | 0.06990 | 0.06647 | 0.0777 | 549 |
| 7.37 | 0.08066 | 0.07598 | 0.1123 | 1012 |
| 14 | 0.07798 | 0.07499 | 0.1559 | 1921 |

## Paired block comparisons of H49-A and H49-B

| Comparison | Half | Blocks | Mean difference | A better | B better |
|---|---|---:|---:|---:|---:|
| oriented vs disk, Instrument B | selection | 20 | -0.01856 | 4 | 16 |
| oriented vs disk, Instrument B | calibration | 19 | -0.00761 | 8 | 11 |
| field swap, Instrument B | selection | 20 | -0.00642 | 8 | 11 |
| field swap, Instrument B | calibration | 19 | -0.00248 | 9 | 10 |
| lower vs selected density, Instrument B | selection | 20 | -0.02658 | 4 | 16 |
| lower vs selected density, Instrument B | calibration | 19 | -0.02576 | 4 | 15 |
| lower vs selected density, Instrument A | selection | 19 | -0.01562 | 6 | 13 |
| lower vs selected density, Instrument A | calibration | 18 | -0.00563 | 9 | 9 |
| higher vs selected density, Instrument B | selection | 20 | -0.00300 | 6 | 14 |
| higher vs selected density, Instrument B | calibration | 19 | -0.00265 | 8 | 11 |
| higher vs selected density, Instrument A | selection | 19 | +0.00196 | 12 | 7 |
| higher vs selected density, Instrument A | calibration | 18 | -0.00758 | 6 | 12 |

The reported paired differences do not establish H49-A (strike-aligned emitter) or H49-B (signed-polarity transform); effects vary across comparisons and halves. Their calculated results are retained, including negative results.

## What H49 does not establish

- No competition leaderboard score was measured, predicted, or implied.
- No evidence establishes that either public proxy follows the hidden-label sampling process, nor that spatial blocks are geologically exchangeable.
- No H49 result is comparable as a private score to the earlier H47-C1 holdout; the evaluation targets and instruments differ.
- The H49 artifact has **not** beaten the established spatially blocked holdout best under a common, preregistered promotion test.
- No H49 artifact is submission-eligible or slot-authorized. Do not upload or use a competition slot.

## Review links

- [Published organizer format instructions](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Owner-mirror and comparator provenance](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/data/reference/README.md)
- [Complete artifact register](all-downloads.html)
- [Current research-only landing page](index.html)
- [Archived original H49 report, before corrections](research/retired/H49_RESULTS-main-original-20261007.md)
