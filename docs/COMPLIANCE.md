---
title: Corrected requirements audit
layout: default
nav_order: 8
---

# Corrected requirements and review status — 7 October 2026

> **This replaces the prior “Requirement compliance” report.** That report incorrectly treated an owner-reported score/file association as authenticated, claimed a causal score gain from deleting masked pixels, described an H48 artifact as submission-ready, and stated an unverified per-week upload limit. Those conclusions and instructions are withdrawn.

## Current decision

**No TIFF in this repository is approved for competition submission. No slot is authorized.** The primary H47-C1 candidate is explicitly research-only and failed its predeclared promotion gate: pooled public-catalogue DTI 0.177872 versus the 0.180216 ordinary-terrain baseline; 11/22 truth-bearing blocks improve, below the required 15; the nominal 90% marginal proxy lower-bound estimate is 0.0000 under unverified exchangeability. The H49 candidate inherited from main is preserved as a separate research artifact; it fails the published null-or-NaN-outside check, uses a public SGMC proxy under unverified exchangeability, and applies a post-hoc amended operating rule. Its 0.2778 comparator is only an owner-reported d2.8 reference. Neither run passed a common promotion test against the established spatially blocked holdout best. These are local proxy results, not private-score estimates. See the [README](../README.md), [current evidence page](evidence.html), [H49 correction](H49_RESULTS.md), and [H49 format audit](data/h49-format-contract-audit.json).

## Requirement audit

| Requirement | Status | Evidence / boundary |
|---|---|---|
| Unique prediction, not a copied prior raster | **Bounded research audit only** | H47-C1 has no exact mask or in-footprint-value match in 561 comparisons across 54 visible, commit-pinned owner inventories plus local history. Maximum Jaccard is 0.040617. This is not global uniqueness or proof of geological novelty; it does not authorize upload. |
| Spatially blocked promotion before any slot | **Not met; gate closed** | H47-C1 loses the pooled control and wins only 11/22 truth-bearing blocks (15 required). H47-B and H47-QC also remain negative research screens. H47-GSA is not a separately validated holdout winner. |
| Calibrated spacing and confidence level | **Reported with assumptions; no positive floor** | H47-C1 selected 2.8 px / 280 m with nominal 90% simultaneous marginal block calibration; exchangeability is unverified and the clipped assumption-conditional lower-bound estimate is zero. No private/global guarantee follows. |
| GeoTIFF format and prior range-error diagnosis | **Local checks only; organizer acceptance unknown** | The official problem page specifies EPSG:32611, 100 m, matching bounds, one float32 layer, values in [0,1], and null/NaN outside. The H47-C1 TIFF stores finite raw values and uses an internal validity mask to mark outside pixels null; 15/15 local read-back checks pass. The portal has not tested it. The historical rejected bytes and parser receipt are unavailable, so the old error's cause is unresolved. |
| All-finite research encodings, including H49 | **Fail the explicit outside-nodata check / not promoted** | The exact H49 TIFF read-back has 12,279,160 finite cells, no NaNs and no NoData tag; relative to its recorded 5,167,373-cell owner-mirror footprint, 7,111,787 outside cells remain finite. The original builder's finiteness check was insufficient. H47-B single-scale, H47-GSA, H47-MAXCOV, H47-QC, H48-APEX/repack, and older Session-3 all-finite variants likewise fail the local outside-null/NaN requirement. Separate NaN-outside variants follow available owner-supplied mirror conventions only; verified portal acceptance is not established. No research variant is recommended for upload. See [`H49_RESULTS.md`](H49_RESULTS.md) and [`h49-format-contract-audit.json`](data/h49-format-contract-audit.json). |
| H33-2-B2 and reported DTI 0.2778 | **Attribution unverified** | The public leaderboard is participant-level and no organizer receipt maps the 0.2778 row to the H33-2-B2 TIFF. H33-dependent fits and comparisons are hypothetical/conditional scenarios, not authenticated results. Call the d2.8 raster the **owner-reported d2.8 reference**; do not call it an incumbent. |
| H47-SAF sensitivity | **Coarse bracket only** | The sign changes between tested assumed DTIs 0.2200 and 0.2400. No exact break-even or causal verdict is established. |
| Metric and masking claims | **Corrected** | `ρ=F/K` and `f=F/T` have different denominators. Deleting predictions exactly on masked pixels cannot by itself improve DTI; no causal gain from deleting masked pixels is inferred. |
| Submission quota / diagnostic cost | **Unknown from checked public official pages** | Pages checked 2026-10-06 do not establish current per-user quota or slot accounting. Three historical λ-scaling score observations do not establish a count of uploads or slots. No diagnostic cost is invented or called free. |
| User brief and three-pass review | **Preserved and reviewed** | The full available user brief remains in [README §0](../README.md#0-read-this-first--the-standing-project-brief). The implementation, bug/assumption, and final-requirements passes are recorded in [review-log.md](review-log.md). |

## Manual-review links

- [Official submission-format page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official competition home](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Sources and dated observations](sources.html)
- [Irregularities and evidence limits](irregularities.html)
- [Next-session handoff](next-session.md)

## Not done or authorized

This review did not restore data, rerun H47-B or H49, upload a file, use a competition slot, or run a λ-probe. Main's committed restore receipt is preserved as pre-existing provenance; it is not evidence of a restore initiated during this review. Any data-dependent tests that skip or run must be reported from the actual test result, not inferred from that receipt. Local validation does not prove organizer acceptance or scientific performance.
