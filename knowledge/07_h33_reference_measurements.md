# Knowledge base 07 — the owner-reported d2.8 reference (h33-2-b2), measured

Measured 2026-10-08 by `scripts/analyze_h33_reference.py` →
`evidence/h33_reference_analysis.json`. Every number below is computed from the
hash-pinned mirror bytes, not from any webpage claim.

> **Attribution caveat (unchanged, from knowledge/05):** the public leaderboard is
> participant-level. No organiser receipt maps the 0.2778 row to this TIFF, and the
> owner page marks the raster unscored. 0.2778 is **owner-reported**. The measurements
> below describe the bytes, not an authenticated score.

## What the raster is

* `reference/h33-2-b2-zeros.tif` (SHA-256
  `c55bafc470054d8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, pinned in
  `registry/data_manifest.json` from `buffedlizard55-lab/GEMSDOE32`): **37,654 unit
  dots** (values exactly {0.0, 1.0}), all on the evaluated domain, **zero** on the
  catalogue, zero outside the footprint.
* Nearest-neighbour spacing: minimum 2.83 px, median 3.0 px, mean 3.74 px — the
  **d2.8 lineage** (280 m nominal spacing), matching its filename.
* Distance to catalogue (px): 2–3: 1,611 · 3–5: 3,237 · 5–10: 6,292 · 10–30: 12,981 ·
  30+: 13,533. Nothing within 2 px of the catalogue.
* **22,447 of 37,654 dots (59.6 %) fall inside the TIGER-road / BLM-closed-claim noise
  masks** that H60 excludes (≥250 m roads, ≥150 m claims).

## Lineage: it is a pruning of a scored sibling raster

Mask Jaccard against every prior raster reachable from this checkout (42 compared,
0 exact matches — the count grows as this repository publishes artifacts; the four
session-6 rasters are among them):

* `gems24-h25-1-dotted-h19-5-d2-8-...-nan.tif` (44,090 dots, owner-reported
  **0.2600**): Jaccard **0.854026**, and the reference is a **strict subset** of it
  (all 37,654 dots are among its 44,090).
* `gems19-h19-5-powerlaw-budget-multiline-corroborated-...-nan.tif` (121,131 dots,
  0.1922): the reference is also a strict subset of this one.

**h33-2-b2 is the d2.8 emission pruned from 44,090 to 37,654 dots.** The owner pages'
"mass/precision pruning of flank/rung predictions" description is confirmed
geometrically: same field, fewer dots.

## Whole-map proxy DTI (frozen instrument set, evaluated domain)

| instrument | DTI |
|---|---|
| lappos_t200_d3 | 0.055460 |
| lapneg_t200_d3 | 0.064712 |
| step_t150_d3 | 0.074499 |
| cross_t200_d3 | 0.014797 |
| upface_t200_d3 | 0.005571 |
| union_t200_d3 | 0.068763 |
| sgmc_offcat | 0.095386 |

(These are whole-map denominators; the screen's block-pooled numbers use per-block
denominators and are not numerically comparable one-to-one.)

## The pruning mechanism, verified algebraically on this raster

Keeping only the top-`f` dots by realised kernel weight against an instrument (the
best possible deletion order for DTI against that proxy):

* **lappos_t200_d3:** TP is unchanged at 1047.8 for every `f` from 1.0 down to 0.1
  (only 3,280 of the 37,654 dots carry any credit against this instrument); FP falls
  from 36,453 (f=1.0) to 2,564 (f=0.1); DTI rises **0.05546 → 0.08649**.
* **sgmc_offcat:** DTI rises 0.09539 → 0.10648 (f=0.2), then saturates.

So deleting the lowest-credit dots raises proxy DTI because the avoided
false-positive cost (α=0.2 per unit) exceeds the lost weighted truth credit
(exactly the credit-bar condition `w > α·DTI` in `knowledge/02`). The owner-reported
0.2600 → 0.2778 move on this lineage is **this mechanism**: mass discipline on an
existing field, not a new geological signal.

## Consequences carried into session 6 (H65–H68)

1. The 0.2778 route — prune an existing field harder — is closed to us as a
   *scientific* strategy, and our uniqueness gate (max mask Jaccard < 0.5 against
   every prior raster) would reject a re-pruning of the d2.8 emission: h33-2-b2
   itself sits at Jaccard 0.854 to a scored prior.
2. The open route is a **better field**. H60 already beats this reference on the
   frozen blocked holdout under identical block-pooled scoring (H60 0.287891 vs the
   d2.8 reference 0.049421 on the primary instrument, selection half).
3. Budget stays at the family-measured-best **37,654** unit dots — the same budget the
   pruned reference uses, so any gain must come from *where* the dots go, not how
   many.
