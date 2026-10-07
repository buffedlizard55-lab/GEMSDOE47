---
title: Corrected research results
layout: default
nav_order: 3
---

# Results — scoped to the evidence

**No result in this file is a private leaderboard score or a submission authorization.** Earlier long-form output that treated owner-reported score/file pairs as authenticated has been preserved, prominently withdrawn, in [`docs/research/retired/`](research/retired/). The current concise record below supersedes it.

## H47-C1 — current primary research screen

- Pooled public-catalogue proxy DTI: **0.177872**; selection-only ordinary-terrain/raw-band baseline: **0.180216**; fixed-seed spaced random: **0.070924**.
- Mean block proxy DTI: 0.177038 for H47-C1 and 0.176051 for the baseline. C1 wins **11/22** truth-bearing test blocks; **15** are required by the preregistered gate.
- Selected spacing: **2.8 px / 280 m**. Nominal **90% simultaneous marginal block** calibration assumes exchangeability, which is unverified; the clipped assumption-conditional lower-bound estimate is **0.0000**. No private/global guarantee follows.
- The secondary SGMC-distance diagnostic loses to random: 0.073537 vs 0.083174. No leaderboard score is attributed to the TIFF.
- Decision: **research-only, not promoted, do not upload**. See [`docs/data/current-submission.json`](data/current-submission.json), [screen page](index.html), and [README](../README.md).

## H49 — retained mainline study, format-failing and not promoted

H49's nominal 90% split-conformal calculation is a **0.03184 assumption-conditional lower-bound estimate** on public SGMC proxy blocks (`n=19`, `k=18`), not an unconditional/private/global floor. Block-score exchangeability is unverified, and the operating-point rule was amended after inspecting repeated-split results. The 0.2778 comparator is only an **owner-reported d2.8 reference**; score/file attribution is unverified, and it is not an authenticated leaderboard incumbent.

The exact artifact read-back has 12,279,160 finite cells, no NaNs, no NoData tag, and a valid mask on every cell. Against the original 5,167,373-cell owner-mirror footprint receipt, 7,111,787 outside cells are finite, so the TIFF **fails** the published null-or-NaN-outside requirement. The artifact and historical receipts are retained for audit, but H49 did not pass a common promotion test against the established spatially blocked holdout best. **Not slot-authorized; do not upload.** See [corrected H49 report](H49_RESULTS.md), [format audit](data/h49-format-contract-audit.json), and [artifact register](all-downloads.html).

## H47-QC and H47-B — separate negative screens

- H47-QC pooled public-catalogue proxy DTI: **0.0131689425**, below the geochemistry-only ablation at **0.0141948068**. Its nominal split-conformal level is 6/7 (85.7%) only under unverified block-score exchangeability; clipped assumption-conditional lower-bound estimate **0.0**. Research-only.
- H47-B cross-scale screen: pooled proxy DTI **0.02755344**, below fixed-seed random **0.03715911**. The later single-scale H47-B screen scores **0.02563947**, below both cross-scale and random. Its clipped assumption-conditional conformal lower-bound estimate is zero. The H47-B mask comparison uses a public owner-supplied mirror; the sample-template and feature-derived masks disagree. No local result establishes organizer acceptance.
- No H47-B rerun was performed for this review.

## Legacy H47-GSA / H47-MAXCOV and H47-SAF

All H47-GSA and H47-MAXCOV rasters remain **research-only and unpromoted**. H47-GSA observation-level cross-fit deltas **−0.0611** and **−0.0450** versus the **owner-reported d2.8 reference** are conditional on the disputed H33-2-B2/0.2778 association; they are not an authenticated leaderboard comparison or a spatial holdout. The participant leaderboard is not mapped to TIFF hashes by organizer receipts.

H47-SAF sensitivity changes sign only **between tested assumed DTIs 0.2200 and 0.2400**. This is a coarse-grid bracket, not an exact break-even and not a causal result. The H33 association is unverified, so any dependent fit is a hypothetical scenario.

## Metric and attribution limits

The DTI algebra distinguishes `ρ=F/K` from `f=F/T`; the denominators differ. For `x=T/K`, `ρ=F/K`, `α=0.2`, and `β=0.8`,

```text
x = (αρ + β) / (1/DTI − α)
```

For `f=F/T`, use instead

```text
x = β / (1/DTI − α(1 + f))
```

An illustrative ratio is not a verified participant measurement; this algebra does not establish that DTI 0.3195 is unreachable. Deleting predictions exactly on masked pixels cannot by itself improve DTI. No causal gain from deleting masked pixels is inferred; nearby evaluated-pixel pruning would require paired evaluation.

A dated public leaderboard observation is participant-level. It does not authenticate a TIFF association. Three historical λ-scaling score observations are not a verified count of uploads or slots. Public official pages checked 2026-10-06 do not establish current per-user quota or slot accounting; no diagnostic cost is inferred or called free.

## Format status

The published format page requires null or NaN outside the training-data bounds. H47-C1 has finite raw samples in [0,1] plus an internal validity mask that marks outside pixels null; its 15/15 local checks are not portal acceptance. Unmasked all-finite H47-B single-scale, H47-GSA, H47-MAXCOV, H47-QC, H48-APEX/repack, and older Session-3 variants write zeros outside and fail the explicit outside-nodata check. Separate NaN-outside variants follow available owner-supplied mirror conventions only; portal acceptance remains unverified. The previous rejected bytes and parser receipt are unavailable, so the historical range-error cause is unknown.

[Official format requirements](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [Irregularities](irregularities.md) · [Three-pass review log](review-log.md)
