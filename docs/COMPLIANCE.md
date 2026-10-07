---
title: Corrected requirements audit
layout: default
nav_order: 8
---

# Corrected requirements and review status — 7 October 2026

> **No artifact is organizer-accepted or authorized for a competition slot.** H50 is the last locally promoted public-proxy candidate; H51 is newer but research-only without a fresh H51-specific holdout. Local promotion, a passing proxy gate, and a locally valid GeoTIFF are separate from organizer acceptance and portal eligibility. No upload or slot use is recorded.

This review also corrects older claims that treated an owner-reported score/file association as authenticated, claimed a causal gain from deleting masked pixels, described an H48 artifact as submission-ready, or stated an unverified per-week upload limit. Those claims and instructions are withdrawn.

## Current decision

H50's documented public-proxy gate passed at 2.8 px / 280 m. The max-residual one-sided split-conformal calculation uses 20 selection blocks and 21 disjoint calibration blocks, rank 20 of 22, nominal confidence 90%, and a **0.095701 DTI conditional lower floor**. Block-score exchangeability is unverified; no unconditional nonzero guarantee for the competition target is claimed. The blocked public-proxy pooled DTI is 0.1658806 for H50, 0.0494209 for the owner-reported d2.8 reference, 0.0482523 for H47-C1, and 0.0470493 for mass-matched random. The owner-mirrored lidar instrument shares slope information with H50's input. These are local proxy values, not private-label or leaderboard scores.

H50's primary NaN-outside TIFF passes local serialized read-back against the mirrored footprint (5,167,373 finite footprint cells; 7,111,787 NaNs outside). The local check does not establish organizer acceptance. The separate all-finite H50 variant writes zeros outside and does not literally satisfy published null/NaN-outside wording. H51's NaN-outside encoding also passes local read-back, but H51 has not been evaluated on a fresh frozen spatial holdout; the H50 conformal result does not transfer to H51.

H49 remains archived research-only. Its exact TIFF fails the outside-null/NaN requirement. Its former observed-range-scaled DKW mean floors (0.040976, Instrument B; 0.038014, PM0200) are retracted; corrected fixed-support `[0,1]` DKW arithmetic floors are zero, with iid sampling unverified. Its nominal 90% paired lower prediction statistics versus the H33-labelled reference are negative (−0.03342 selection; −0.01050 calibration), not mean confidence bounds or leaderboard results. The participant-score/file mapping is unverified and the selection rule was amended after results. See the [root README and standing brief](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md), [current H50 status receipt](data/current-artifact.json), [H50 evidence](h50.html), [H51 research page](h51.html), [corrected H49 report](H49_RESULTS.md), and [H49 format audit](data/h49-format-contract-audit.json).

## Requirement audit

| Requirement | Status | Evidence / boundary |
|---|---|---|
| Unique prediction, not a copied prior raster | **Bounded local audit only** | H50 has zero exact positive-mask matches among 31 compared local prior rasters; maximum mask Jaccard 0.045623. This is not global uniqueness or proof of geological novelty. H51's bounded comparison has maximum Jaccard 0.854329 and does not establish novelty or promotion. |
| Spatially blocked promotion before any slot | **H50 local gate passed; no slot authorized** | H50's documented public-proxy gate exceeds the listed controls and has a positive conditional calculation. The proxy is slope-correlated and block exchangeability is unverified; this is not a private-label or leaderboard result. H51 has no fresh H51-specific holdout. H47-C1, H47-QC and H49 remain research-only/failed or unpromoted. |
| Calibrated spacing and confidence level | **Reported with explicit assumptions** | H50 selects 2.8 px / 280 m on 20 blocks and calculates a 90% nominal, rank-20/22 lower floor of 0.095701 DTI on 21 disjoint calibration blocks, conditional on unverified block-score exchangeability. This does not imply nonzero private-target coverage. H51 has no applicable H51 certificate. |
| GeoTIFF format and prior range-error diagnosis | **Local checks only; organizer acceptance unknown** | Published instructions specify EPSG:32611, 100 m, matching bounds, one float32 layer, values in [0,1], and null/NaN outside. H50's NaN-outside variant locally reads back with the expected grid/footprint; its all-finite variant has zeros outside. H51's NaN-outside variant has local format evidence only. Historical rejected bytes and parser receipt remain unavailable, so the old range error's cause is unresolved. |
| H49 all-finite TIFF | **Fails outside-null/NaN check; research-only** | Exact TIFF read-back has 12,279,160 finite cells, no NaNs and no NoData tag; relative to its recorded 5,167,373-cell owner-mirror footprint, 7,111,787 outside cells remain finite. The original builder's finiteness check was insufficient. Corrected DKW and paired results are documented in H49 results and its archived receipt. |
| H33-2-B2 and reported DTI 0.2778 | **Attribution unverified** | No organizer receipt maps the 0.2778 row to a TIFF. The owner page marks that submission unscored. H33-dependent fits/comparisons are hypothetical or owner-reported context, not authenticated results. Call the d2.8 raster the **owner-reported d2.8 reference**, not an incumbent. |
| H47-SAF sensitivity | **Coarse bracket only** | The sign changes between tested assumed DTIs 0.2200 and 0.2400. No exact break-even or causal verdict is established. |
| Metric and masking claims | **Corrected** | `ρ=F/K` and `f=F/T` have different denominators. Deleting predictions exactly on masked pixels cannot by itself improve DTI; no causal gain from deleting masked pixels is inferred. |
| Submission quota / diagnostic cost | **Unknown from checked public official pages** | Pages checked 2026-10-06 do not establish current per-user quota or slot accounting. Three historical λ-scaling score observations do not establish a count of uploads or slots. No diagnostic cost is invented or called free. |
| User brief and three-pass review | **Preserved; checks in progress** | The full available user brief remains in [README §0](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md#0-read-this-first--the-standing-project-brief). Implementation, bug/assumption, and final-requirements review is recorded in the session handoff; this turn's tests and site checks must be reported from actual results. |

## Manual-review links

- [Official submission-format page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official competition home](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Sources and dated observations](sources.html)
- [Irregularities and evidence limits](irregularities.html)
- [Next-session handoff](next-session.md)

## Not done or authorized

This review has not used the competition portal, uploaded a file, or used a slot. Data-dependent tests and any checks run in this turn must be reported from their actual test results, not inferred from an older restore receipt. Local validation does not prove organizer acceptance or scientific performance. No credentials are requested or stored here.
