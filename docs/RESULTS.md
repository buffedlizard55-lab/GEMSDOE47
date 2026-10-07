---
title: Results — corrected H33 and H49 evidence
layout: default
nav_order: 3
---

# Results — current evidence, score attribution and limitations

> **Correction notice (2026-10-06 local review):** an earlier results report treated the H33 0.2778 filename label as an authenticated organizer score and described the H27/H33 raster nesting as a scored natural experiment. That was not supported. The exact mask relationship is verified; the score-to-TIFF mapping is not. The old score-conditioned inversions remain in `evidence/inversion/live_anchor_inversion.json` as conditional owner-label arithmetic, not observed results.

## 1. H33/H27 byte-level relationship

The H33 `GEMSDOE32` zero-outside TIFF (SHA-256 `c55bafc470054e8271d1cb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`) has 37,654 positive pixels. It is a strict subset of the 40,199-positive H27 parent from `GEMSDOE28` (SHA-256 `2fc94a38d77f74d4f4ed1a97a83e7bb71a1ceea090515ec641e6681cc47c44c8`): 2,545 parent-only pixels, no H33-only pixels. The removed pixels are exactly those within Euclidean distance ≤2 px of the given-catalogue mask (1,201 at 1 px and 1,344 at 2 px). A separate 41,507-positive `GEMSDOE27` all-increments raster is not this parent.

These facts are reproduced in the [reusable knowledge record](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/05_why_02778_and_can_we_beat_it.md) and the pinned [mask audit](data/h47b-candidate-uniqueness-20261006.json). They establish a mask edit, not a score change.

## 2. Score receipt and causal interpretation

The public participant-board snapshot contains a 0.2778 observation at rank 13 under `extradr19`; no organizer receipt maps that entry to the H33 TIFF hash. The H33 owner README at commit `b983924b57781edd29b8e249c4923bf33d9902f6` explicitly calls the file **UNSCORED** and 0.2747 a projection. The older 0.2708 label also has no receipt mapping to the exact 40,199-positive parent. Owner narratives and filenames are secondary evidence, not organizer score receipts.

The published DTI algebra supports a marginal-credit rule: for a unit of added prediction mass that yields new kernel-weighted credit `w`, a local DTI increase requires `w > 0.2 × current DTI` (0.05556 at a hypothetical DTI of 0.2778). This does not identify the true hidden-label credit of the removed dots. Catalogue pixels are excluded exactly; there is no automatic 200 m neighborhood that becomes penalty-free. A nearby prediction still receives credit only if it covers hidden new-fault truth. See the [official metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) and [staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516).

**Conclusion:** we cannot honestly answer “why did this exact H33 TIFF score 0.2778?” because that score-to-file link is unauthenticated. Reduced off-target mass is a plausible mechanism, not an established causal explanation.

## 3. H49 public-proxy result and slot decision

H49 compares a signed-polarity scarp field with a public SGMC off-catalogue proxy. SGMC contains non-fault contacts; it is not the organizer’s hidden target. On this one sweep, the selected H49 arm has selection-half mean DTI 0.10329 versus 0.07108 for the H33 reference and 0.05750 for a mass-matched random mask. These are descriptive measurements from 20 selection blocks, not a leaderboard score or private-label forecast.

The nominal 90% fixed-arm split-conformal absolute DTI order statistic is 0.03184 (Instrument B; 19 calibration blocks; k=18), with 0.01828 on PM0200. Exchangeability of spatial blocks and a rule fixed independently of calibration outcomes are assumptions. The H49 mean-rule arm was selected after review of the results; its prospective status is not independently verifiable in Git history. Four hundred re-partitions reuse the same 39 blocks and are sensitivity diagnostics, not new independent samples.

Paired differences against the H33 reference have positive sample means and positive one-sided Student-t lower bounds, but the **90% split-conformal lower bound on fresh-block paired improvement is negative** for both candidate arms. The nominal absolute DTI floor is not a guarantee of improvement over the incumbent. The complete adaptive pipeline has no established conformal guarantee. **Do not spend a submission slot on H49.**

Full per-arm tables are in [H49 results](H49_RESULTS.html); the machine-readable certificate and paired metrics are in the [current artifact receipt](data/current-artifact.json) and the [repository evidence file](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/evidence/h49/conformal_certificate.json). Future candidates and their physical signatures, novelty, expected effect/cost and data-acquisition status are in [the ranked research queue](RESEARCH_HYPOTHESES.html).

## 4. Output validity is a separate gate

The first published H49 copy failed the strict internal-mask contract: masked reads did not treat outside-footprint cells as null. The candidate was rebuilt and the exact published bytes were read back. Current file: `gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif`, 409,124 bytes, SHA-256 `f2cec409ce3bec5a2805f1fab9a12ab7f72394f8be79cc365134ce43708c6060`. All 19 gating checks pass; the separate informational whole-grid range flag is also true (20 recorded checks total). The TIFF is one float32 band, 3292 × 3730, EPSG:32611, exact official transform, with an internal mask matching all 5,167,373 official-footprint cells; masked reads are null exactly outside. Raw samples across the entire grid are finite in [0,1], with no nodata tag or sidecar; 37,612 cells are positive. These facts establish format validity for these bytes, not scientific promotion or organizer acceptance.

A commit-pinned uniqueness audit covered 54 visible public repositories: 555 comparable inventory blobs plus 10 local-history rasters, zero exact mask/value matches, maximum Jaccard 0.292575 (against the prior GEMSDOE47 H49 raster). Three inventory entries were not directly comparable (two not single-band on the exact grid, one ZIP not containing a single TIFF); no repository inventory fetch failed. Global uniqueness is not proven, and inaccessible/unpublished files are outside scope. The full receipt is [`data/pinned-public-inventory-uniqueness.json`](data/pinned-public-inventory-uniqueness.json); the artifact pointer is [`data/current-artifact.json`](data/current-artifact.json). Scientific validation, bounded uniqueness and organizer acceptance remain separate; no score or acceptance is claimed.

## 5. Sources

- [Official competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Official metric and output format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData staff clarification on catalogue masking](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)
- [Pinned GEMSDOE32 owner README](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/b983924b57781edd29b8e249c4923bf33d9902f6/README.md) — secondary owner source; its H33 section says unscored/projection.
- [H33/H27 mask audit](data/h47b-candidate-uniqueness-20261006.json) — exact-grid mask comparison, not score authentication.
