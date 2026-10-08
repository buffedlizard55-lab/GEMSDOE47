---
title: Remaining work and limitations
layout: default
nav_order: 7
---

# Remaining work and limits — corrected 8 October 2026 (session 6, H65–H68)

> **H60 is the repository's recommendation: OK to download and submit.** H68 is a new unique
> validated candidate (a valid submission, not the recommendation). H65 is the round's best science
> and is published as a research artifact that is **NOT OK to submit while the frozen uniqueness
> bar stands**. No competition submission slot has been spent by this repository, and no organiser
> acceptance is claimed for any file. The older handoff that advised uploading without a passed
> gate, assumed a fixed weekly quota, treated H33's reported 0.2778 as an authenticated raster
> score, and described a causal gain from flank deletion is withdrawn; the 0.2778 attribution
> remains unverified (participant-level leaderboard, no organiser receipt).

## Immediate decision

**H60 remains the file to submit** (`docs/downloads/gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif`,
note `h60 lidar-scarp d2p0 conformal90`): it passed all six frozen conditions in its round
(primary 0.2879 vs the H50 anchor's 0.1659; independent SGMC 0.1938 vs random 0.0698; certified
split-conformal floor 0.0989 at ≥ 90.91 % coverage; uniqueness max Jaccard 0.0217; 17/17 format
checks). This round no arm displaced it under all six conditions:

* **H65 (scarp consensus) beat H60 on both holdout instruments** (0.2919 vs 0.2879 primary;
  0.1984 vs 0.1938 SGMC) — the strongest scientific result of the round — but its emission
  overlaps the H60 artifact at mask Jaccard **0.5119 ≥ 0.5**, failing frozen condition 6
  (bounded uniqueness). Published as a research artifact, NOT OK TO SUBMIT while the bar stands
  (IR-2026-10-08-E). It is unique against every scored prior submission (max 0.0067).
* **H68 (eight-channel lidar) is the new unique TIF** — the frozen winner by the SGMC tie-break,
  passing control conditions 1–4 and the uniqueness bar (max Jaccard 0.3066): a valid submission,
  but it does not beat H60 on the primary instrument (0.2783 vs 0.2879), so it is not the
  recommendation (IR-2026-10-08-B records the tie-break tension).

## Remaining work

1. **Owner decision on the slot.** Submit H60 (recommendation), or H68 (valid alternative), or
   record an explicit owner decision to submit H65 despite the self-imposed uniqueness bar. Any
   upload needs the eligibility/quota checks in the authenticated portal first, the receipt
   saved, and the exact bytes preserved if rejected.
2. **Uniqueness-bar-compliant H65 variant.** The 0.5119 overlap comes from emitting the same
   budget at the same spacing over the same domain with correlated fields. A preregistered
   variant (different budget, domain restriction, or hybrid tie-break) could clear the bar;
   preregister and re-screen before building anything.
3. **Independent-instrument program.** The primary instrument shares the lidar modality with
   every lidar-reading field. H67's Th/K component is independent of it. The GeoDAWN Th/K and
   U/K grids are already restored and hash-pinned (USGS GeoDAWN release, DOI
   10.5066/P93LGLVQ); USGS MRData ASTER alteration is named but not fetchable from this
   sandbox; QFaults/NBMG M167 are already inside the training labels (closed).
4. **Spacing below 2.0 px (preregister first).** H65's selection-half mean is still rising at
   the sweep edge; extend the sweep with the conformal guarantee simultaneous over the extended
   set; record under-emission at small spacings.
5. **Mask-radius ablation (preregister first).** The 250 m road / 150 m claim radii were frozen
   pre-score and never swept; a 3×3 radius grid is one screen.
6. **H67 λ sweep or Th/K ablation.** The alteration arm kept the round's best certified floor
   (0.1045) but diluted the primary instrument; isolate whether the radiometric component
   carries signal.

## Limitations that do not go away

* **Attribution.** The participant-level 0.2778 observation is not authenticated to H33-2-B2;
  the owner page marks that raster unscored. Measured this round
  (`evidence/h33_reference_analysis.json`): h33-2-b2 is the scored d2.8 emission pruned
  44,090 → 37,654 dots (strict mask subset, Jaccard 0.854), 59.6 % of its dots inside the
  road/claim noise masks, and the 0.2600 → 0.2778 move is the DTI pruning algebra — mass
  discipline on an existing field, not a new geological signal. The re-pruning route is closed
  by the uniqueness gate; the open route is a better field.
* **Circularity.** The primary instrument derives from the same owner-built lidar stack the
  lidar-reading fields (H60, H65, H66, H68) read; their primary-instrument numbers are optimistic
  by construction. The SGMC off-catalogue population is independent of the lidar fields but is
  biased toward mountain bedrock and its DTI is negatively rank-correlated (−0.421) with the 13
  owner-reported scores, while the primary instrument is positively correlated (+0.548).
* **Conformal semantics.** Every floor is a finite-sample, max-over-settings, one-sided split
  conformal bound (Lei et al. JASA 2018, Algorithm 2) at rank 20 of 22 — coverage at least
  90.91 % — conditional on block-level exchangeability, which spatial separation does not
  establish. It covers one future exchangeable block's proxy DTI, never the private leaderboard,
  and is never a distribution-free guarantee for private labels.
* **H65's margins are small** (+1.4 % primary, +2.4 % SGMC over H60) but consistent in direction
  on both instruments; they are selection-half measurements on a proxy, not a leaderboard
  prediction. H60 has not been scored by the organiser; no score exists for any file in this
  repository.
* **Provenance.** Competition arrays and comparison rasters are hash-pinned mirror/owner bytes,
  not authenticated organizer downloads. The lidar stack is owner-derived from USGS 3DEP 1 m DEM
  tiles (706/716; not organiser-supplied). The GeoDAWN grids are contractor u8-rank products of
  the USGS GeoDAWN release, not physical units. Restore pins prove mirror consistency, not
  organizer authentication.
* **Quota.** Public official pages do not establish the current per-user quota or slot
  accounting; no diagnostic cost is inferred or described as free.
* **Format distinction.** Official instructions say null or NaN outside the training bounds.
  H49's exact TIFF is all-finite with no NoData tag and fails that check; the H60/H65/H68
  artifacts are all-finite with zeros outside the footprint and no NoData tag (the portal
  previously rejected "Predicted values must be in range [0, 1]"; the all-finite {0,1} encoding
  answers it directly, and NaN-outside fallbacks are published alongside). Organizer acceptance
  of any encoding has not been tested.

## Actions explicitly not taken

This round did not upload or prepare a portal submission, use a competition slot, query
DrivenData (Terms), or read any private label. The screens and builds are local and
reproducible; the artifacts are published for the owner's judgement.

## References

- [Current README and standing user brief](../README.md)
- [Session-6 handoff](next-session.md)
- [H65–H68 evidence page](h65.html)
- [H60 evidence page](h60.html)
- [Corrected requirements audit](COMPLIANCE.md)
- [Submission readiness checklist](HOW_TO_SUBMIT.md)
- [Official GeoTIFF requirements](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official competition home and rules links](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Irregularities register](irregularities.md)
