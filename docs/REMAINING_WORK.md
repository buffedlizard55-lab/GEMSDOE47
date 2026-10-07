---
title: Remaining work and limitations
layout: default
nav_order: 7
---

# Remaining work and limits — corrected 7 October 2026

> **No current artifact is approved for upload.** This replaces an older handoff that incorrectly advised uploading a TIFF, assumed a fixed weekly quota, treated H33's reported 0.2778 as an authenticated raster score, and described a causal gain from flank deletion. Those instructions and conclusions are withdrawn.

## Immediate decision

Keep every submission gate closed. H47-C1 is the prominent current research artifact but failed its preregistered screen: pooled public-catalogue DTI 0.177872 versus the 0.180216 ordinary-terrain baseline; only 11/22 truth-bearing blocks improved (15 required); nominal 90% marginal proxy lower-bound estimate 0.0000 under unverified exchangeability. The H49 candidate inherited from main is preserved for audit but fails the published outside-null/NaN requirement: its exact TIFF is all-finite with no NoData tag. Its nominal 90% proxy lower-bound calculation assumes unverified exchangeability, the selection rule was amended post-hoc, and its 0.2778 comparator is an owner-reported d2.8 reference, not an authenticated leaderboard incumbent. H49 did not pass a common promotion comparison against the established spatially blocked holdout best. H47-B and H47-QC are negative research screens. H47-GSA/H47-MAXCOV and H48/session-3 artifacts are research-only or superseded. None has organizer acceptance or permission to use a slot.

## Remaining work

1. **Finish the review PR and verify repository checks.** The PR must be green and mergeable before it is merged; this is separate from competition eligibility.
2. **If a new candidate is proposed, preregister a fresh spatially blocked test** against a separately established holdout best, with equal-mass controls, adequate truth, and the specified confidence level. The current C1 test results cannot be reused as an untouched test for a tuned variant. A zero or unsupported assumption-conditional lower bound keeps the gate closed.
3. **Keep attribution conditional.** The participant-level 0.2778 observation is not authenticated to H33-2-B2. All H33-dependent fits and score inversions are hypothetical scenarios. The d2.8 TIFF is an **owner-reported d2.8 reference**, not a separately established spatially blocked holdout best. H47-SAF changes sign only between tested assumptions 0.2200 and 0.2400; there is no exact break-even.
4. **Keep the format distinction explicit.** Official instructions say null or NaN outside the training bounds. The exact H49 TIFF read-back has all 12,279,160 cells finite and no NoData tag; its original receipt records 5,167,373 mirrored footprint cells, so 7,111,787 outside cells are finite and it fails that check. Unmasked zero-outside all-finite H47-B single-scale, H47-GSA, H47-MAXCOV, H47-QC, H48-APEX/repack, and Session-3 variants also fail the local outside-nodata check. Its NaN-outside alternative follows an available owner-supplied mirror convention, not verified portal acceptance. H47-C1 instead has an internal validity mask; its local 15/15 checks are not an organizer test. The earlier rejected bytes are unavailable, so the cause remains unknown.
5. **Do not treat score observations as upload receipts.** Three historical λ-scaling score observations do not establish how many new files were uploaded or how many slots were used. Public official pages checked 2026-10-06 do not establish the current per-user quota or slot accounting. No diagnostic cost is inferred or described as free.
6. **Preserve provenance limits.** Competition arrays and comparison rasters in the local history are hash-pinned mirror/owner bytes, not authenticated organizer downloads. No hidden test labels, private score, or complete participant-to-TIFF mapping is available.

## Actions explicitly not taken

This review did not restore data, rerun H47-B, upload or prepare a portal submission, use a competition slot, or run a λ-probe. Data-dependent tests remain skipped because the cache is absent. Do not run gated pipelines or use a slot absent explicit authorization and a passed promotion gate.

## References

- [Current README and standing user brief](../README.md)
- [Corrected requirements audit](COMPLIANCE.md)
- [Submission readiness checklist](HOW_TO_SUBMIT.md)
- [Official GeoTIFF requirements](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official competition home and rules links](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Irregularities register](irregularities.md)
- [Next-session handoff](next-session.md)
