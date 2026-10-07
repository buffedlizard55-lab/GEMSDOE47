---
title: Remaining work and limitations
layout: default
nav_order: 7
---

# Remaining work and limits — corrected 7 October 2026

> **Current status: H50 is the last locally promoted candidate; no artifact is organizer-accepted or authorized for a competition slot.** H50 has a documented spatially blocked public-proxy result and a NaN-outside TIFF that passed local serialized read-back. These do not establish private-label or leaderboard performance, portal acceptance, eligibility, or slot authorization. No upload or slot use is recorded. H51 is a later multi-scale research variant without a fresh H51-specific frozen holdout; its historical conformal number is inherited from H50 and does not apply. H49 remains archived research-only. This corrects older upload-ready wording and reconciles the README with the machine-readable current-artifact pointer.

## Immediate decision

Keep the **competition-slot authorization** gate closed. H50's local public-proxy gate passed: at 2.8 px / 280 m the nominal 90% split-conformal calculation has rank 20/22 and a 0.095701 DTI lower floor conditional on block-score exchangeability; the assumption is unverified, so this is not an unconditional or private-label floor. Its blocked public-proxy pooled DTI was 0.1658806 versus 0.0494209 for an owner-reported d2.8 reference, 0.0482523 for H47-C1, and 0.0470493 for mass-matched random. The instrument shares slope information with H50's input and is based on owner-mirrored data; these are not leaderboard scores. H50's NaN-outside bytes locally match the mirrored footprint, but organizer acceptance is untested. The separate all-finite H50 file has zeros outside and does not literally meet published null/NaN-outside wording. H51 remains research-only until it passes its own fresh, preregistered blocked holdout; do not transfer H50's conformal statistic. H47-C1 failed its preregistered screen: pooled public-catalogue DTI 0.177872 versus the 0.180216 ordinary-terrain baseline; only 11/22 truth-bearing blocks improved (15 required); lower-bound estimate 0.0000 under unverified exchangeability. H49's exact TIFF is all-finite with no NoData tag and fails the published outside-null/NaN requirement. Its former observed-range-scaled DKW mean floors 0.040976 (Instrument B) and 0.038014 (PM0200) are retracted; corrected fixed-[0,1]-support arithmetic is 0.00000 for both, with DKW's iid assumption unverified. H49's nominal 90% paired lower prediction statistics for H49 minus the H33-labelled reference are negative on both reported halves (selection −0.03342; calibration −0.01050); participant-score mapping is unverified. No positive paired-improvement lower bound or H49 promotion is established. H47-B and H47-QC are negative research screens. H47-GSA/H47-MAXCOV and H48/session-3 artifacts are research-only or superseded. No organizer acceptance or competition-slot authorization is established for any file.

## Remaining work

1. **Finish the review PR and verify repository checks.** The PR must be green and mergeable before it is merged; this is separate from competition eligibility.
2. **If a new candidate is proposed, preregister a fresh spatially blocked test** against a separately established holdout best, with equal-mass controls, adequate truth, and the specified confidence level. The current C1 test results cannot be reused as an untouched test for a tuned variant. A zero or unsupported assumption-conditional lower bound keeps the gate closed.
3. **Keep attribution conditional.** The participant-level 0.2778 observation is not authenticated to H33-2-B2. All H33-dependent fits and score inversions are hypothetical scenarios. The d2.8 TIFF is an **owner-reported d2.8 reference**, not a separately established spatially blocked holdout best. H47-SAF changes sign only between tested assumptions 0.2200 and 0.2400; there is no exact break-even.
4. **Keep the format distinction explicit.** Published instructions say null or NaN outside the training bounds. H50's preferred NaN-outside TIFF passes local serialized read-back against the mirrored footprint (5,167,373 finite cells inside; 7,111,787 NaNs outside); that is not organizer acceptance. H50's separate all-finite variant writes zeros outside and does not literally satisfy the wording. H51 also has a locally read-back NaN-outside encoding, but that is format evidence only and does not promote H51. The exact H49 TIFF read-back has all 12,279,160 cells finite and no NoData tag; its original receipt records 5,167,373 mirrored footprint cells, so 7,111,787 outside cells are finite and it fails that check. Unmasked zero-outside all-finite H47-B single-scale, H47-GSA, H47-MAXCOV, H47-QC, H48-APEX/repack, and Session-3 variants also fail the local outside-nodata check. H48's NaN-outside alternative follows an available owner-supplied mirror convention, not verified portal acceptance. H47-C1 instead has an internal validity mask; its local 15/15 checks are not an organizer test. The earlier rejected bytes are unavailable, so the cause remains unknown.
5. **Do not treat score observations as upload receipts.** Three historical λ-scaling score observations do not establish how many new files were uploaded or how many slots were used. Public official pages checked 2026-10-06 do not establish the current per-user quota or slot accounting. No diagnostic cost is inferred or described as free.
6. **Preserve provenance limits.** Competition arrays and comparison rasters in the local history are hash-pinned mirror/owner bytes, not authenticated organizer downloads. No hidden test labels, private score, or complete participant-to-TIFF mapping is available.

## Actions explicitly not taken

This review did not restore data, rerun H47-B, upload or prepare a portal submission, use a competition slot, or run a λ-probe. Data-dependent tests remain skipped because the cache is absent. Do not run gated pipelines or use a slot absent explicit authorization and a passed promotion gate.

## References

- [Current README and standing user brief](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md)
- [Corrected requirements audit](COMPLIANCE.md)
- [Submission readiness checklist](HOW_TO_SUBMIT.md)
- [Official GeoTIFF requirements](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official competition home and rules links](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Irregularities register](irregularities.md)
- [Next-session handoff](next-session.md)
