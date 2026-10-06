# Results, conformal audit, and leaderboard attribution — 2026-10-06

> **Decision: no artifact from this project is submission-eligible, and no competition slot is recommended.** The new downloadable TIFF is research-only. It loses to both H47-B and a fixed-seed random control on the locked spatial *known-catalogue-mask proxy*; its clipped conformal lower bound is zero. This proxy is not the competition's missing-fault target.

## Decision in brief

| Selected method (d=5 px / 500 m) | Locked-test pooled DTI against known-fault catalogue mask (proxy only) | Result |
|---|---:|---|
| H47-B cross-scale `TMI_up150` magnetic-edge persistence | 0.02755344 | Not promoted |
| Single-scale `TMI_up150` edge control (the new research-only TIFF) | 0.02563947 | Not promoted |
| Fixed-seed random control | **0.03715911** | Exceeds both methods |

The new GeoTIFF is a genuinely generated mask rather than a copied submission. It has 18,524 binary predictions, passes the strict local byte-level validator against an explicit binary mask derived from finite cells in the mirrored sample template, and has zero exact positive-mask matches among 334 checked historical exact-grid TIFFs. The feature-derived footprint does not match the mirrored sample/label footprint, so this format pass does not resolve the official authorized evaluation footprint. These facts establish neither a useful geological signal nor eligibility for upload. See the [download and summary](executive-summary.html), [H47-B validation report](validation-h47b-20261006.md), [spacing/conformal JSON](../evidence/conformal_spacing_audit_20261006.json), and [candidate uniqueness JSON](../evidence/conformal_candidate_uniqueness_20261006.json).

## Split-conformal spacing audit

The frozen audit selected spacing on five blocks, calibrated on six disjoint blocks, and reserved five blocks as locked test. The sweep covered 2–6 px. Selection used only selection blocks; both arms selected 5 px / 500 m.

The reference labels are **known USGS/INGENIOUS catalogue-mask pixels** (`labels.tif == 1`), which the organizer says are masked from the actual off-catalogue evaluation ([staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)). The local metric was run against that mask unmasked to create a diagnostic resemblance proxy; it is not a holdout of the hidden new-fault target. The conformal target is only a future comparable block score against this same proxy.

With six calibration proxy scores, the chosen one-sided order statistic is rank 6 of 6 and the nominal split-conformal marginal level is 6/7 = **85.7%**, conditional on exchangeability. The clipped lower prediction bound is **0.000** for both arms. Two calibration blocks have no catalogue-mask pixels; one selection and two locked-test blocks are also empty. An empty mask core is not proof of no geological fault.

Spatial block exchangeability is not verified. The nominal level is not private-label coverage, missing-fault DTI, cellwise/conditional coverage, leaderboard DTI, rank, or a universal performance guarantee. The standard split-conformal argument applies only if calibration and future proxy block scores are exchangeable; see [Lei et al. (2018)](https://arxiv.org/abs/1604.04173) and the [publisher DOI](https://doi.org/10.1080/01621459.2017.1307116). The zero floor and proxy target provide no positive basis to spend a slot.

The descriptive full-domain DTI values (H47-B 0.04642384; single-scale 0.04727772; random 0.03601067) use the entire available public catalogue and are not holdout or hidden-target estimates. Do not present them as predictive performance.

## The new TIFF and format audit

Path: [`docs/downloads/gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-nanoutside.tif`](downloads/gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-nanoutside.tif)

- SHA-256: `dc71c807fbca2cd398f394bcd91b10ecec6b46fe89c2d61f5b1c058fef672811`; 309,530 bytes.
- One-band float32; EPSG:32611; 3292 columns × 3730 rows; 100 m; exact sample-template transform; NaN nodata tag and NaNs outside the explicit footprint; 18,524 binary positive predictions; in-footprint range [0,1].
- The strict local validator **passes when the footprint is supplied as an explicit binary mask derived from finite cells in the mirrored `sample_submission.tif`**. The sample and labels each have 5,167,373 footprint pixels. The `training_features.tif`-derived footprint has 5,165,852: 1,540 feature-valid pixels fall outside the sample mask, while 3,061 sample-footprint cells are invalid/masked in features. Using the feature-derived mask therefore fails validation in both directions. The authorized official footprint is unresolved; the explicit sample mask only makes the local check internally consistent with the mirror's sample/label footprint.
- The paired all-finite diagnostic encoding, [`gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-allfinite.tif`](downloads/gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-allfinite.tif), has the same positive mask but zeros outside and no NaN nodata tag. It fails the strict validator and is retained only to test a possible NaN-intolerant range-check hazard. The portal's historical error cause is unknown; neither variant is recommended for upload.
- Local format validity is not scientific validation or organizer acceptance. The candidate failed the known-catalogue-mask proxy screen. The rejected historical TIFF and organizer-side diagnostic are unavailable, so the range-error root cause remains unknown.
- Research-trial note (reference only, not for upload): `single-scale edge; d=5 px/500 m; catalogue-mask proxy conformal 6/7=85.7% nominal, lower floor 0.000 (exchangeability unverified); RESEARCH ONLY`.

## Bounded uniqueness comparison

The historical inventory contains 55 visible sibling repositories and 336 unique Git blobs. The saved remote audit fetched the 334 exact-grid comparable rasters one at a time, verified each against its recorded Git blob SHA-1 and byte count, and had zero fetch/verification failures. This full remote fetch was not repeated for the NaN-outside encoding: its positive mask was verified identical to the paired all-finite diagnostic, so the prior mask-based remote comparison applies. The candidate has zero exact positive-mask matches. Its maximum positive-support Jaccard was **0.02010094**; maximum top-equal-mass Jaccard at 18,524 pixels was **0.01290464** (closest artifact: `GEMSDOE35/docs/downloads/gemsdoe35-h35-01-e58e5dbee6-20261004T164802Z-candidate.tif`). Separately, the NaN-outside candidate was compared against **19/19** independent prior exact-grid TIFFs present in this repository's downloads and restored data cache: zero exact matches, with maximum support and equal-mass Jaccard **0.02054983** against the earlier H47-B cross-scale TIFF. The paired all-finite encoding is excluded from local priors as a same-run diagnostic, not an independent prior model.

These are bounded statements about the dated visible-repository inventory and local files available at audit time, not global uniqueness. It excludes private, deleted, unindexed, or later artifacts and does not prove geological novelty, score attribution, or predictive performance. The separate historical H47-B uniqueness results are in [`h47b-uniqueness-audit-20261006.json`](h47b-uniqueness-audit-20261006.json); do not conflate its Jaccard values with the new TIFF's.

## Latest saved public leaderboard evidence and the 0.2778 question

A one-time read of the official [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) on 2026-10-06 was recorded as follows:

| Saved public row | Score | Attribution boundary |
|---|---:|---|
| Rank 1 | **0.3774** | Participant name not preserved |
| DARD, rank 7 | **0.3195** | Participant-level row only |
| `extradr19`, rank 13 | **0.2778** | Participant-level row only |

The board is a changing public page, not an artifact receipt. It contains no TIFF hashes or upload IDs. The GEMSDOE32 owner page marks H33-2-B2 as **UNSCORED**; therefore its alleged mapping to the `extradr19` 0.2778 row is contested. The project cannot truthfully state why that TIFF scored 0.2778—or even that it did.

If the disputed mapping were correct, the metric equation

```text
DTI = T / (T + 0.2 F + 0.8 (K − T)) = T / (0.2 (T + F) + 0.8 K)
```

shows why removing emissions with low expected credit can improve precision. But the H33-specific causal story is not established: it depends on the contested file/score pairing and on mask semantics. Local evidence supports zeroing known-catalogue pixels before both sums; deleting only pixels that are fully excluded cannot itself change DTI. More analysis of off-catalogue halo pixels is required before attributing any score change to the flank-pruning operation. The full conditional arithmetic and its limitations are described in [`knowledge/02_the_metric_algebra.md`](../knowledge/02_the_metric_algebra.md) and [`docs/evidence.html`](evidence.html).

The previous in-repository leaderboard snapshot put 0.3345 at rank 1 and was superseded by the later saved read. Neither 0.3195 nor 0.2778 is the latest saved rank-1 score. The project does not automate leaderboard access. DrivenData's [Terms of Use](https://www.drivendata.org/termsofuse/) restrict automated monitoring and require prior written consent for manual monitoring/copying; the site links to the official board instead of implementing a live feed.

## Retired historical claims

The modeled `0.34912` score and purported `0.34837` split-conformal floor at 75% are retired and must not be reused. They relied on selected rungs from one monotone deletion family, did not establish exchangeable calibration examples, used the unverified 0.2778 file/score mapping, and extrapolated the chosen operating point. The old claims are preserved only in [`notes/results-retired-unverified-20261006.json`](../notes/results-retired-unverified-20261006.json).

The older `gems47-dcat20-annulus-flankprune-n18524-20261006.tif` is a pruned subset of a sibling mask, not a new detector and not an acceptable deliverable under the no-copy requirement. Byte uniqueness does not imply scientific uniqueness.

## Official metric and interpretation limits

The official [competition description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) defines the weighted DTI. With `FN_w = K − T`, this repository's algebraic form is `DTI = T / (0.2(T + F) + 0.8K)`. The local implementation is tested against a literal implementation and the official worked example, but it is not an organizer-run scorer. No model-based calculation from the public mirror identifies hidden labels or private leaderboard performance.

## What would change the decision

A future prediction must be genuinely new, and beat the current spatially blocked holdout best and nontrivial controls under a preregistered rule; have adequate label coverage; show a positive lower bound only if its assumptions are defensible; pass exact-byte format and bounded-uniqueness audits; and have a clear path to authorized validation. Keep the slot unused until these gates pass. The official competition description says one submission is selected for scoring across the initial and final prize rounds; it does not justify assuming unlimited uploads. Check the current participant portal for upload allowance and deadline.
