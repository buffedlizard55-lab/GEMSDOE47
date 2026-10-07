# H47-B public-catalogue screen — 2026-10-06

> **Decision: NOT PROMOTED. No submission slot is recommended.** This document describes the earlier H47-B cross-scale experiment, not the later single-scale control. The cross-scale TIFF is retained under `docs/downloads/superseded/`; the single-scale artifact, its footprint-mask discrepancy and exact format audit are documented separately in the [H47-B mask audit](h47b-mask-audit-20261006.html). A valid GeoTIFF profile does not rescue the failed holdout/control gate.

## Executive result

H47-B ranked a rank-encoded `TMI_up150` magnetic edge-persistence field at 2, 4, and 8 pixels on the 100 m grid. Spacing was selected on five preregistered blocks, evaluated on six calibration blocks, then assessed on five locked blocks. The candidate beat a tuned single-scale edge baseline by a small margin on the pooled locked-test DTI, but **lost to a fixed-seed random control**. Its mechanically computed, assumption-conditional conformal lower-bound estimate was **zero**. Five of the 16 blocks contained no known-catalogue mask pixels, including two locked-test and two calibration blocks.

| Locked-test measure | H47-B | Single-scale baseline | Fixed-seed random |
|---|---:|---:|---:|
| Pooled DTI (the preregistered promotion comparison) | 0.02755344 | 0.02563947 | **0.03715911** |
| Unweighted mean of five block DTIs | 0.01197844 | 0.01099731 | **0.02181179** |
| Promotion condition | beat baseline | — | **H47-B lost** |

These values are **public-catalogue screening results**, not a DrivenData private score and not a score attributed to any historical TIFF. Crucially, `labels.tif == 1` marks known USGS/INGENIOUS fault pixels, which the organizer says are masked from the actual off-catalogue target ([staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)). This experiment scored against those known-fault pixels as a diagnostic resemblance proxy; it is **not a spatial holdout of missing-fault labels** and cannot validate private-fault discovery. The input catalogue and template came from a public group-hosted GitHub mirror, not a direct authenticated organizer download. See [the frozen protocol](preregistered-h2.md), the [machine-readable screen report](h47b-screen-report-20261006.json), and the [full artifact comparison record](h47b-uniqueness-audit-20261006.json).

## Protocol and inputs

- The input hashes and original protocol were frozen before H47-B scoring. The protocol document now includes a post-score target-semantics clarification only; the original frozen SHA-256 and current clarification-document SHA-256 are both recorded in the machine-readable report. The source-code implementation is `gemsdoe47/magnetic.py` and `scripts/run_h2_experiment.py`.
- The feature is `TMI_up150` from a `uint8` rank-encoded GeoDAWN mirror. It is **not physical magnetic units**, raw total magnetic intensity, a tilt-angle solution, or a physical source-depth estimate.
- The known-fault catalogue mask (`labels.tif == 1`) was used as a diagnostic evaluation proxy; it is not the hidden off-catalogue target. The acquisition-block raster was used only for descriptive subgroup checks.
- DTI was computed with this repository's implementation, [`src/gems47_metric.py`](../src/gems47_metric.py), transcribed from the official [DrivenData metric description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). This is a local formula implementation, not an organizer-run scorer or an official private-score receipt.
- The 4 × 4 grid used disjoint block cores with a 3-pixel/300 m edge guard. The selection, calibration, and locked-test assignment was fixed before scoring. The guard prevents direct kernel overlap across block edges; it **does not establish statistical independence**.

## Spacing sweep

For each candidate, exactly 18,524 binary predictions were emitted at each tested spacing. Selection used the unweighted mean DTI over the five selection blocks; pooled test DTI pools metric components over disjoint test cores.

| Minimum spacing | H47-B selection mean | H47-B pooled locked test | Baseline selection mean | Baseline pooled locked test |
|---:|---:|---:|---:|---:|
| 2 px / 200 m | 0.02712319 | 0.01438034 | 0.02649283 | 0.01246441 |
| 3 px / 300 m | 0.03956202 | 0.02119639 | 0.04190327 | 0.02070047 |
| 4 px / 400 m | 0.04757245 | 0.02498688 | 0.04901068 | 0.02393470 |
| **5 px / 500 m** | **0.04860422** | **0.02755344** | **0.05203546** | **0.02563947** |
| 6 px / 600 m | 0.04619826 | 0.02883342 | 0.04871409 | 0.02714003 |

The preregistered selection rule selects 5 px for H47-B and 5 px for the baseline. H47-B's test mean-block value is not the promotion statistic; it is included to show the block-level average. The full per-block and full sweep records are in the JSON report.

### Locked blocks and label coverage

The locked blocks were IDs 2, 5, 8, 11, and 14. Only IDs 2, 5, and 14 contained known-catalogue mask pixels: 6,091; 10,600; and 5,342 respectively. IDs 8 and 11 had zero mask pixels and scored zero for all methods. The candidate beat the single-scale baseline in each of the three nonempty proxy blocks, but the random control scored higher than H47-B in each. This is a negative resemblance-proxy screen, not evidence about missing-fault labels.

Across all 16 blocks, five were empty of known-catalogue mask pixels: selection block 7; locked-test blocks 8 and 11; calibration blocks 12 and 15. An empty proxy block's score of zero says nothing about whether a missing fault is present there.

## Conformal calculation — not a positive lower-bound estimate

At selected spacing 5 px, selection mean DTI was `μ = 0.04860422299678556`. The six calibration DTI values were approximately `[0.04322934, 0.02420100, 0.03694814, 0.07157694, 0, 0]`. The one-sided residuals were `μ − DTIᵢ`; the preregistered order statistic was rank 6 of 6 at nominal `6/7 ≈ 85.7%` coverage **conditional on marginal block-score exchangeability**.

The resulting quantile is `0.04860422299678556` and the clipped lower bound is **0.0**. Spatial dependence makes exchangeability unverified, and two calibration blocks have no known-catalogue mask pixels. The nominal number is an assumption-conditional calculation for the catalogue-mask proxy only; it is **not** a missing-fault performance floor or a guarantee about private labels or leaderboard score. The older claimed `0.34837` floor is separately retired (see [analysis](analysis.md)).

## File audit and accessible-artifact comparison

The research TIFF is [`downloads/superseded/gems47-h47b-tmiup150-xscale-persist-n18524-research-not-submittable-20261006.tif`](downloads/superseded/gems47-h47b-tmiup150-xscale-persist-n18524-research-not-submittable-20261006.tif), SHA-256 `7e5df9d01689e438e8379ebd4763ed803de02e94826f43da37c33c16380d669b`.

- One-band float32; 3292 × 3730; EPSG:32611; 100 m pixels.
- GDAL-order transform `(243350, 100, 0, 4508550, 0, -100)`.
- 5,167,373 in-footprint pixels; values in `[0, 1]`; 18,524 pixels equal 1; remaining in-footprint pixels equal 0; 7,111,787 outside-footprint pixels are NaN.
- The persisted file passed the local byte-level format/range audit. That is **format validity only**, not organizer acceptance or scientific promotion.

For a bounded uniqueness check, a one-time inventory of 55 visible `buffedlizard55-lab` GEMSDOE repositories found 425 tracked TIFF paths and 336 distinct Git blobs. Of those, 334 one-band rasters matched the candidate grid exactly; two blobs were read but excluded for different geotransforms (one same-sized 100 m grid with a shifted origin; one 32 × 48 format-test grid). The [full audit record](h47b-uniqueness-audit-20261006.json) lists paths, blob hashes, all 334 comparisons, and the two exclusions. All fetched blobs were Git-SHA verified; there were no fetch/read failures. There were zero exact positive-mask matches. Maximum equal-mass Jaccard similarity was **0.01119057**; maximum positive-support Jaccard was **0.01685795**.

This supports uniqueness **only against the accessible repository artifacts in that one-time inventory**. It cannot establish global uniqueness, search private/deleted/unindexed files, authenticate any old score mapping, or turn a failed candidate into a submission. The old GEMSDOE47 d-cat/annulus TIFF is itself a delete-only subset of a published mask and is not a valid uniqueness precedent.

## Final gate and next action

H47-B failed the preregistered gate because it lost to the random control and its assumption-conditional lower bound was zero. **Do not upload it or spend a slot.** Keep the file only as a clearly labeled research artifact. The runner now permanently records `slot_eligible: false` for H47-B and has no non-research publication path: the public-mirror screen cannot confer submission eligibility even if a later reproduction were to clear its metric screen. Before testing another candidate: obtain authorized official competition inputs where available; establish a reproducible current spatial-holdout best; preregister a new, distinct detector and controls; and require a test gain over that best and the controls with adequate label coverage. A participant leaderboard score cannot substitute for any of those checks.
