# Results and leaderboard attribution — corrected 2026-10-06

> **No score from this project is a DrivenData leaderboard score. H47-QC and H47-B are not promoted and are not eligible for a submission slot.** This page supersedes previous score-ladder and “conformal floor” interpretations; public board rows do not authenticate a TIFF/score pair.

## Decision in brief

H47-B is a new magnetic-edge persistence screen and its mask has low similarity to the accessible sibling-repository TIFFs checked in that audit. Its local output-format audit passed. It nevertheless failed its preregistered scientific gate: the locked-test candidate lost to the fixed-seed random control and its assumption-conditional conformal lower floor was zero. H47-QC is the latest screen and also failed; see its result below. Do not upload either.

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

## H47-QC geothermometer-consensus screen — negative result

H47-QC was frozen before scoring in [`preregistered-h47qc-20261006.md`](preregistered-h47qc-20261006.md). Its label-blind builder uses repeated-row medians for three mirror-exported GDR geothermometers, a measured outlet-temperature proxy, a fixed agreement/temperature/cooling weight, a 1 km Gaussian field, and aligned gradients in named RTP and isostatic-gravity bands. The `dist_known_fault_px` CSV field is never read. The build counted 90 positive-weight source groups at 89 unique cells; after structural-validity intersection, 252,618 cells remained for the combined ranking.

| Selected 5,000-point operating point | Spacing | Locked-test pooled DTI |
|---|---:|---:|
| **H47-QC** | **6 px / 600 m** | **0.01316894** |
| Geochemistry-only ablation | 6 px / 600 m | **0.01419481** |
| Structural-edge-only ablation | 6 px / 600 m | 0.01255839 |
| H47-B equal-mass persistence | 5 px / 500 m | 0.00782453 |
| Single-scale magnetic baseline | 5 px / 500 m | 0.00812956 |
| Fixed-seed random within H47-QC support | 5 px / 500 m | 0.01285767 |
| Fixed-seed random over full footprint | 6 px / 600 m | 0.01232633 |

Spacing for each method was selected on the five frozen selection blocks, with the five locked blocks reserved for final reporting. H47-QC beat four of six comparators but **lost to the geochemistry-only ablation**. That is not evidence that the structural interaction improves the thermal-source ranking. The selected-mask mean block DTI was 0.006385 on selection blocks, 0.012113 on calibration blocks, and 0.006791 on locked-test blocks; the difference across small block sets shows substantial geographic heterogeneity.

With six calibration blocks the largest preregistered nominal one-sided split-conformal level is **6/7 = 85.7%**. The clipped lower future-comparable-block DTI floor was **0.0**, so the bound is vacuous. Exchangeability is unverified under spatial dependence, and neither this level nor its floor transfers to private labels or the leaderboard.

The 5,000-point artifact has a valid all-finite `[0,1]` GeoTIFF format, but **54 selected cells coincide with known public-catalogue labels**. The public proxy DTI counts those as known-label hits; it does not establish withheld-fault discovery. The artifact is [available for download with a short note](downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.md), explicitly **research only / do not submit**. Full metrics and hashes: [`h47qc-screen-20261006.json`](h47qc-screen-20261006.json). A separate bounded audit compared it to 334 exact-grid rasters from 55 public sibling repositories: zero exact masks, maximum equal-mass Jaccard 0.002104; see [`h47qc-uniqueness-audit-20261006.json`](h47qc-uniqueness-audit-20261006.json). This does not change the failed gate.

## Scientific assessment of the reported 0.2778 value

The most defensible mechanism is **precision gained by pruning low-marginal-credit evaluated prediction mass**, not proof of a new geological discovery. From the documented metric, for binary/weighted predictions `DTI = 5T / (T + F + 4K)`, where `T` is distance-weighted credit, `F` is false-positive mass, and `K` is the scored truth count. A point helps only when its marginal kernel credit is sufficient relative to the existing score; cutting low-credit predictions can improve the ratio even when total coverage falls.

The owner-reported family trajectory from 0.1922 to 0.2778 is consistent with this: emitted mass reportedly falls 69% (121,131 to 37,654 pixels), while covered 300 m kernel credit falls about 33% (449,693 to 302,510). Those are useful mechanism clues, **not verified explanation of the 0.2778 leaderboard row**. The official public board is participant-level (`extradr19` was observed at 0.2778/#13 on 2026-10-06); it does not identify a TIFF. The GEMSDOE32 H33-2-B2 page marks that raster **UNSCORED**, and no organizer receipt links its hash to the participant row. Therefore do not state that H33-2-B2 earned 0.2778 or that a particular deletion caused it.

In particular, the claim that removing dots on masked catalogue pixels yielded “free precision” conflicts with the repository's working mask interpretation: DrivenData staff said those pixels are excluded from evaluation, and a mirror-byte comparison (two owner-reported 0.1563 entries differing on catalogue-only mass) is consistent with masking before both DTI sums. Under that semantics, deleting only masked pixels should not change the score at all. The public rows and owner mirrors are not receipt-authenticated, so even this empirical cross-check is corroborative rather than a formal test of the private scorer. **Bottom line:** sparse pruning can explain why a family of reported DTI values rose; the file-level cause of the public 0.2778 remains unresolved.


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
