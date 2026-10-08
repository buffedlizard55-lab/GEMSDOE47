---
title: Remaining work and limitations
layout: default
nav_order: 7
---

# Remaining work and limits — 7 October 2026

> **No competition upload or slot use is authorized or performed in this review.** H60 is the current locally promoted scientific candidate; organizer acceptance is untested. H47-C1 remains research-only, not promoted, and its gate remains closed. See [current status](current-status.html).

## Current evidence boundary

H60 passed its preregistered 41-block local gate at 2.0 px / 200 m. Pooled proxy DTI is 0.287891 on the primary off-catalogue lidar-peak instrument and 0.193813 on independent SGMC off-catalogue faults. The primary instrument is derived from the same owner-built lidar stack as the H60 field and is circular/optimistic; the results are not private-label or leaderboard scores. The 0.0989005 split-conformal floor at rank 20/22 (90.91% nominal marginal coverage) is conditional on unverified block-score exchangeability.

The all-finite H60 TIFF has finite zeros outside and does not literally satisfy the published null/NaN-outside instruction. The NaN-outside sibling matches that wording on local read-back, but portal acceptance remains untested. The historical rejected bytes and parser receipt are unavailable, so the old range-error cause remains unknown. The explicit C1 failure is unchanged: pooled proxy DTI 0.177872 vs. 0.180216 for baseline; 11/22 truth-bearing test blocks improved where 15 were required; assumption-conditional lower-bound estimate 0.0.

## Remaining work, only after a separate authorization

1. **Keep portal activity stopped for this review.** Do not upload, spend a feedback opportunity, or make a final selection. The [official DOE/NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) states up to three scoring/feedback submissions per week and one final selected file for the competition's rounds. This public cap does not disclose the entrant's eligibility, used/remaining weekly opportunities, or current final-selection state; those require the authenticated portal.
2. **De-circularize the strongest instrument before treating H60's primary score as transferable evidence.** The primary lidar-peak instrument uses the same owner-derived lidar stack the candidate reads. A new instrument should have zero shared code path with the field; a structurally independent regional or Quaternary-fault compilation is a research priority, subject to actual coverage verification.
3. **Preregister any extension before scoring.** The 2.0 px spacing is at the edge of the tested range, where the selection-half mean remained highest. Any extension below 2.0 px needs a frozen spacing set, capacity-aware emission accounting, and a conformal guarantee simultaneous over the expanded set; do not reuse the existing test as a fresh test for tuned settings.
4. **Measure the road/claim mask radii only under a preregistered ablation.** H64 supports using the masks but does not establish that 250 m / 150 m are optimal radii.
5. **Maintain the exact-byte distinction.** The local format audit is [`data/h60-encoding-audit.json`](data/h60-encoding-audit.json). The NaN-outside variant is an inspection candidate only; the all-finite zero-outside variant is a range-check diagnostic, not a locally format-conforming file under the published outside wording. A passing local check does not establish organizer acceptance.
6. **Keep attribution and provenance conditional.** Participant leaderboard rows do not identify TIFFs. The 0.2778 H33-2-B2 mapping remains owner-reported and unverified. The restored competition inputs are hash-pinned mirrors, not authenticated organizer downloads; no private labels or private score are available.
7. **Preserve the dated board snapshot.** The official public observation checked 7 October 2026 has rank 1 at 0.3774 and 0.3195 at rank 7. Do not call 0.3195 the current top; the board moves, and no score-to-file mapping is established.

## Actions not taken

This documentation review did not log in to the competition portal, restore competition data, run an H60 scoring pipeline, upload a file, request a score, use a weekly feedback opportunity, make the final selection, or spend a slot. Any data-dependent test result must be reported from the actual run, not inferred from a receipt or earlier handoff.

## References

- [Current status and exact-byte audit](current-status.html)
- [Current README and standing brief](README.md)
- [H60 scientific evidence](h60.html)
- [Corrected requirements audit](COMPLIANCE.md)
- [Submission status and safe checklist](HOW_TO_SUBMIT.md)
- [Official GeoTIFF requirements](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official competition rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Source register](sources.md)
