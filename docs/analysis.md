# Results and leaderboard attribution — corrected 2026-10-06

> **No score from this project is a DrivenData leaderboard score. H47-B is not promoted and is not eligible for a submission slot.** This page supersedes the previous score-ladder and “conformal floor” interpretation.

## Decision in brief

H47-B is a new magnetic-edge persistence screen and its mask has low similarity to the accessible sibling-repository TIFFs checked in this audit. Its local output-format audit passed. It nevertheless failed the preregistered scientific promotion gate: the locked-test candidate lost to the fixed-seed random control and the assumption-conditional conformal lower floor was zero. Do not upload it.

The detailed measurements, per-block results, input provenance, output audit, and scope of the uniqueness check are in the [H47-B validation report](validation-h47b-20261006.md). The complete sanitized experiment record is [`h47b-screen-report-20261006.json`](h47b-screen-report-20261006.json).

## Latest saved public leaderboard evidence

A one-time read of the official [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) on 2026-10-06 was recorded as follows:

| Public row | Score | What is retained |
|---|---:|---|
| Rank 1 | **0.3774** | Participant name was not preserved in the session record. |
| DARD, rank 7 | **0.3195** | Participant-level public score. |
| `extradr19`, rank 13 | **0.2778** | Participant-level public score. |

The earlier checked-in snapshot and web pages listed **0.3345 as rank 1** and DARD at rank 5. That is stale relative to the later captured read and has been superseded; the older participant name and intermediate rows are not carried forward because they cannot be verified from the saved record. The leaderboard is a moving public display, not a feed. This project does not automate access or monitoring.

**Crucial attribution boundary:** the public board reports participant rows, not TIFF filenames, exact file hashes, or organizer receipt IDs. None of the rows above identifies a particular TIFF. `0.3195` is not the latest captured rank-1 score. `0.2778` is not verified as the score of the GEMSDOE32 H33-2-B2 TIFF: the owner page marks that candidate **UNSCORED**, and the participant-level board cannot repair the missing mapping. The user-provided result list remains a user report; see [prior results](prior-results.md).

## Retraction: old score model and alleged conformal floor

The previous pages reported a modeled `0.34912` score and a purported split-conformal lower floor of `0.34837` at 75%. **That claim is retired and must not be reused.** The inputs were selected rungs from a single monotone deletion family, not demonstrated exchangeable calibration examples; the 0.2778 score-to-file link was not organizer-authenticated; and the selected operating point was a long extrapolation. These conditions do not support the represented distribution-free guarantee or a claim of private/leaderboard performance. The values are preserved only as an explicitly retired historical record in [`notes/results-retired-unverified-20261006.json`](../notes/results-retired-unverified-20261006.json) and in the prior-result notes.

The older `docs/downloads/gems47-dcat20-annulus-flankprune-n18524-20261006.tif` is derived by pruning a published sibling mask. It is not a new detector, does not meet the user's no-copy submission requirement, and is retained only for historical audit. Its byte uniqueness does not make its prediction scientifically unique.

## H47-B public-catalogue screen

The experiment used the rank-encoded `TMI_up150` channel from a public group-hosted GeoDAWN mirror; the labels and sample template were also mirrored, not acquired through an authenticated organizer download. The preregistered 4 × 4 spatial screen used disjoint 300 m-guarded block cores and matched emission mass. DTI was computed by this repository's implementation of the formula in the official [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/); it was not an organizer-run scorer.

| Locked-test result | DTI |
|---|---:|
| H47-B, selected spacing 5 px / 500 m | 0.02755344 |
| Tuned single-scale edge baseline, 5 px / 500 m | 0.02563947 |
| Fixed-seed random control, matched mass and spacing | **0.03715911** |

The candidate beat the baseline but lost to random. The unweighted mean block DTIs were 0.01197844, 0.01099731, and 0.02181179 respectively. Two of the five locked blocks had no catalogue truth; three had truth, and random exceeded H47-B in all three. Five of the 16 total blocks were empty, including two calibration blocks. The nominal 6/7 conformal calculation produced a clipped lower floor of **0.0**, with exchangeability unverified. These are useful negative screening results, not evidence that magnetic data cannot help.

The descriptive full-domain DTI values (H47-B 0.04642384; baseline 0.04727772; random 0.03601067) use all available public catalogue labels and are **not** holdout or hidden-target estimates. Do not present them as predictive performance.

## Uniqueness: bounded finding, not a promotion argument

The one-time GitHub inventory covered 55 visible `buffedlizard55-lab` GEMSDOE repositories. It found 425 tracked TIFF paths representing 336 unique Git blobs; 334 one-band rasters matched the candidate's full grid, and two blobs were read but excluded for different geotransforms. Fetched bytes were verified against Git blob IDs. There were no fetch/read failures and no exact positive-mask matches. The maximum equal-mass Jaccard similarity was 0.011190567; the maximum positive-support Jaccard was 0.016857947.

That supports a narrow statement: **the H47-B mask was not an exact match to any of those 334 accessible, comparable rasters in the inventory.** It does not prove global uniqueness, cover private/deleted/unindexed prior files, establish a score attribution, or override H47-B's failed holdout gate. The tracked [full uniqueness-audit JSON](h47b-uniqueness-audit-20261006.json) includes the inventory identities, all comparisons, and the two exclusions; additional raw downloads and the original run environment remain under ignored `work/audit/`.

## Metric and interpretation limits

The official problem description defines weighted `TPw`, `FPw`, and `FNw`; using `FNw = Ng − TPw` gives

```text
DTI = 5 × TPw / (TPw + FPw + 4 × Ng)
```

`src/gems47_metric.py` implements that formula and includes regression checks, including the official worked-example components. This repository implementation has not been run by the organizer. Reducing the formula further to a function of a presumed dot count requires extra assumptions about prediction values and distance-weighted false positives; those assumptions do not authenticate old scores or identify a TIFF.

## What would change the decision

A future candidate needs a preregistered, reproducible gain over the **current spatially blocked holdout best**, plus meaningful null/random and domain controls; sufficient label coverage; a conformal floor only if its assumptions are defensible; a fresh byte-level output audit; and a uniqueness check with explicit coverage limits. It must be a new prediction, not a pruned prior map. Until all gates pass, retain the slot. See the [validation protocol](validation-protocol.md), [submission guide](submit.html), and [irregularity register](irregularities.md).
