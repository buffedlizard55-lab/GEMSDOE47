# Knowledge base 07 — the instrument ladder: which proxy populations reproduce the leaderboard ordering

Reusable across sessions. Every number below is read directly from a committed evidence
file in this repository (paths given); the 13 (raster, owner-reported score) pairs are the
same in all three studies and are **not** organiser receipts. With 13 pairs the standard
error of a Spearman rho is about 0.29 — treat small differences as noise and only the
large, repeated patterns as signal.

## 1. The three studies

| Study | Question | Evidence | Seed |
|---|---|---|---|
| H50 ranking | Which local proxy truth reproduces the leaderboard ordering? | `evidence/h50/instrument-ranking.json` | 20261007 |
| H64 (session 5) | Do catalogue-distance stratification or road/claim-mask filtering sharpen the lidar-peak instruments? | `evidence/h60/instrument-refinement.json` | 20261007 |
| H70 (session 6) | Do the remaining populations (downface, SGMC variants, vents) beat the H64 set? | `evidence/h65/instrument-refinement.json` | 20261008 |

Method (identical): whole-map DTI of each of the 13 restored scored rasters against the
population, Spearman/Kendall vs owner-reported scores, two-sided permutation p over 20,000
relabellings.

## 2. The ladder (Spearman vs owner-reported scores)

Lidar-peak populations, best first (H64 masked/stratified values where available):

| Population | Spearman | p | n_truth | Source |
|---|---|---|---|---|
| step t150 d3, road/claim-masked | +0.592 | 0.035 | 7,379 | H64 |
| lappos t200 d3, far (>3 px from catalogue) | +0.581 | 0.040 | 12,958 | H64 |
| lappos t200 d5 (unstratified) | +0.576 | — | 8,022 | H50 |
| lappos t200 d3, road/claim-masked | +0.576 | 0.044 | 5,864 | H64 |
| lapneg t200 d3, road/claim-masked | +0.576 | 0.043 | 6,967 | H64 |
| step t150 d3, far | +0.548 | 0.055 | 16,933 | H64 |
| lappos t200 d3 (unstratified) | +0.548 | — | 14,241 | H50 |
| cross t150 d3 (unstratified) | +0.532 | — | 20,489 | H50 |
| lapneg t150 d3 (unstratified) | +0.504 | — | 29,764 | H50 |
| lapneg t200 d3, far | +0.466 | 0.109 | 15,834 | H64 |
| step t150 d3 (unstratified) | +0.449 | — | 18,531 | H50 |
| cross t200 d3, road/claim-masked | +0.438 | 0.138 | 1,879 | H64 |
| lapneg t200 d3, near (≤3 px) | +0.432 | 0.136 | 1,413 | H64 |
| cross t200 d3, far | +0.410 | 0.168 | 4,191 | H64 |
| downface t200 d3, far | +0.350 | 0.236 | 1,850 | H70 |
| cross t200 d3 (unstratified) | +0.322 | — | 4,588 | H50 |
| upface t200 d3 (unstratified) | +0.322 | — | 1,608 | H50 |
| downface t200 d3, road/claim-masked | +0.306 | 0.306 | 811 | H70 |
| lappos t200 d3, near | +0.273 | 0.359 | 1,283 | H64 |
| union t200 d3, far | +0.333 | 0.264 | 32,334 | H64 |
| union t200 d3, near | +0.273 | 0.369 | 2,992 | H64 |
| union of six channels t200 d3 (unstratified) | −0.047 | — | 35,326 | H50 |
| ex_max t200 d3 | +0.488 | 0.092 | 12,202 | H64 |
| coh100 t200 d3 | −0.532 | 0.064 | 67,288 | H64 |

Catalogue-family populations:

| Population | Spearman | p | n_truth | Source |
|---|---|---|---|---|
| SGMC off-catalogue, near (≤3 px) | +0.278 | 0.357 | 17,493 | H70 |
| iso_catalogue (components ≤12 px) | +0.085 | — | 11,940 | H50 |
| SGMC off-catalogue, >500 m | −0.025 | 0.939 | 56,822 | H70 |
| SGMC off-catalogue, >300 m (frozen) | −0.025 | — | 62,122 | H50 |
| flank_catalogue (>12 px components) | −0.163 | — | 49,048 | H50 |
| SGMC off-catalogue, >200 m | −0.168 | 0.579 | 66,277 | H70 |
| SGMC off-catalogue, >100 m | −0.355 | 0.235 | 72,063 | H70 |
| catalogue (given, masked out of scoring) | −0.477 | — | 60,988 | H50 |
| catalogue ∪ SGMC off-catalogue | −0.554 | — | 123,110 | H50 |

Exploratory only: INGENIOUS volcanic vents, n = 21, Spearman +0.207, p = 0.52 — uninformative
by design (H70, preregistered as a diagnostic; no conclusion may rest on it).

## 3. The four robust patterns

1. **Sharp far-field steps predict the ordering; the catalogue anti-predicts it.** The top of
   the ladder is masked/far step and lappos peaks (+0.55…+0.59, p ≈ 0.04); the bottom is the
   given catalogue (−0.48) and its union with SGMC (−0.55). The hidden labels behave like a
   population that is *harder to hit than nothing but proportional in difficulty* to the lidar
   scarp population — for the seven real-detector family artifacts, leaderboard score ≈
   3.4–5.0 × lappos-DTI at a roughly constant ratio.
2. **Masks help; distance stratifies.** Road/claim-masking raises every tested channel's
   correlation (step +0.592 masked vs +0.449 unmasked); far-from-catalogue peaks beat near
   ones (lappos +0.581 far vs +0.273 near). Both facts motivated H60's design and explain
   H63's refutation (catalogue-hugging hurts).
3. **The union dilutes the strong channels.** Six-channel union −0.047; per-channel peaks up
   to +0.576. A max/mean over channels spends budget on cells the best channel rejects —
   the H65 (step-only) / H66 (consensus-mean) question.
4. **SGMC has a distance gradient with the opposite sign.** Near-catalogue SGMC faults are
   weakly positive (+0.278); far SGMC faults are at zero or negative (−0.025 at >500 m,
   −0.355 at >100 m). Leaderboard-ordered artifacts hit near-catalogue SGMC faults but
   far-field lidar scarps — consistent with hidden labels concentrated near known systems
   ("newly mapped geometry of existing fault systems") while far-field lidar skill still
   helps. The SGMC instrument is therefore an independent *real-fault* floor, not a
   leaderboard predictor, and gate conditions on it must be read that way.

## 4. What this does not establish

* None of the 13 scores is an organiser receipt; the h33-2-b2 → 0.2778 pairing is an
  assumption (IR-47-002). The ladder ranks *proxies*, not submissions.
* p ≈ 0.04 on one row of ~19 tested populations is suggestive, not corrected for multiple
  comparisons. The patterns above are trusted because they repeat across channels,
  thresholds and studies — not because of any single p-value.
* A positive instrument correlation does not certify that emitting on that population beats
  the leaderboard; the blocked-holdout screens (H50/H60/H65) test that separately, with the
  circularity warnings recorded in each screen receipt.
