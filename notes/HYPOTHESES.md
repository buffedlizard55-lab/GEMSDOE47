# Hypothesis status — current through 2026-10-07

> **Current candidate: H60, locally promoted by the preregistered H60–H64 holdout gate.** Its primary lidar-peak instrument is circular/optimistic because it is derived from the same owner-built lidar stack H60 reads; the independent SGMC proxy is corroboration, not a hidden-label result. Organizer acceptance is untested. No portal upload or competition slot use is authorized or performed in this review. H47-C1 remains research-only/not promoted; its gate remains closed. See [`docs/current-status.html`](../docs/current-status.html) and [`docs/h60.html`](../docs/h60.html).

## Current decision

- **H60 lidar scarp-crest field:** selected at 2.0 px / 200 m; passed the local preregistered gate. Pooled proxy DTI is 0.287891 on the primary owner-derived lidar-peak instrument and 0.193813 on independent off-catalogue SGMC. The one-sided conformal floor is 0.0989005 at rank 20/22, conditional on unverified block-score exchangeability. None is a private-label or leaderboard score.
- **H60 file encodings:** the NaN-outside TIFF matches the published outside-null/NaN wording on local read-back; organizer acceptance is untested. The all-finite TIFF passes a raw [0,1] range check but writes zeros outside, so it is a diagnostic rather than the format-convention candidate. The current ZIP contains the all-finite diagnostic and is not an upload bundle. Exact hashes and counts are in [`docs/data/h60-encoding-audit.json`](../docs/data/h60-encoding-audit.json).
- **H47-C1:** not promoted. Its frozen screen pooled DTI 0.177872 versus the 0.180216 ordinary-terrain baseline; it won only 11/22 truth-bearing test blocks versus the required 15; its assumption-conditional lower-bound estimate is zero. This gate remains closed and is not reopened by H60.
- **H50:** earlier locally promoted scientific fallback, superseded by H60; its published all-finite zero-outside encoding does not literally meet the official outside-null/NaN rule. It is not portal-accepted.
- **H47-B cross-scale magnetic-edge persistence:** historical frozen public-mirror screen, **NOT PROMOTED**. Locked-test pooled DTI was 0.027553 vs 0.025639 for the tuned single-scale baseline and 0.037159 for the fixed-seed random control. Its assumption-conditional conformal lower floor clipped to 0.0.
- **H51 multi-scale slope anomaly:** near-duplicate of H50 (maximum mask Jaccard 0.8543); not an independent candidate.

## Rules, attribution, and access limits

- The [DOE/NLR official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) states up to three scoring/feedback submissions per week and one final selected file for the competition's rounds. The rules do not expose the entrant's eligibility, previous submissions, remaining weekly opportunities, or current final-selection state; those require the authenticated portal.
- The saved official public leaderboard observation checked 7 October 2026 has rank 1 at 0.3774 and 0.3195 at rank 7. The board is participant-level and dated, not a file/hash receipt. The H33-2-B2 / 0.2778 mapping remains owner-reported and unverified.
- Competition data remained login-gated in the unauthenticated review. Restored arrays are hash-pinned mirrors, not authenticated organizer downloads. No private labels or private score are claimed.

## Standing scientific gate

Any future candidate must be preregistered before scoring and must beat the established spatially blocked holdout best plus relevant random/domain controls with adequate label coverage. A positive conformal floor is usable only if the exchangeability unit and assumptions are defensible; a nominal level alone is not a private/global guarantee. The exact serialized TIFF must match the published grid/range/null requirements, be bounded-unique against the accessible inventory, and pass a local byte audit. Local checks do not establish organizer acceptance. A portal upload requires separate user authorization and authenticated account/rules checks.

## Retired historic recommendation

The old `gems47-dcat20-annulus-flankprune` artifact is a delete-only subset of a published network; it is not an independent detector. Its modeled 0.34912 score and claimed 0.34837 floor are withdrawn because the score-to-file mappings were unauthenticated, the selected rungs were not valid exchangeable calibration data, and the target was a long extrapolation. The old analysis is preserved only in [`notes/results-retired-unverified-20261006.json`](results-retired-unverified-20261006.json) and is not evidence for a submission.
