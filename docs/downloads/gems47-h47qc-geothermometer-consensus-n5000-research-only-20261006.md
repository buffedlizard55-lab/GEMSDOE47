# H47-QC research artifact — **do not submit**

**Status: NOT PROMOTED.** The preregistered public-catalogue screen failed the promotion gate. This file is provided for transparent review and download only; do not spend a competition slot or upload it.

## One-click file

[Download `gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.tif`](gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.tif)

- SHA-256: `3866b60cf91b4f6bff2ef694153550aa97a744a3091a57ef9f83da41e16b91b2`
- 1-band `float32`, EPSG:32611, 100 m, 3292 × 3730; all 12,279,160 cells are finite and in `[0,1]`.
- Exactly 5,000 binary points (`1.0`); remaining cells are `0.0`, including outside the sample-template footprint. This is an **uncalibrated research mask**, not a probability surface.
- The repository's read-back validator passed all format/range checks. This does not imply that DrivenData accepts the file or that it is scientifically valid.

## Short distinguishing note

Suggested optional-note text, **for identification only—not permission to submit**:

> H47-QC geothermometer consensus × aligned RTP–gravity edge; 5,000 binary pixels; RESEARCH ONLY

## Preregistered result

H47-QC combined quality-screened INGENIOUS geothermometer consensus with aligned RTP/isostatic-gravity gradient strength. It selected 6 px / 600 m minimum spacing on five selection blocks. On the five locked public-catalogue test blocks, pooled DTI was **0.013169**. At the same 5,000-point budget, the geochemistry-only ablation scored **0.014195**; the random-within-candidate-support control scored **0.012858**; the matched H47-B persistence and single-scale magnetic baselines scored **0.007825** and **0.008130**. The candidate therefore did not beat every comparator.

The six calibration blocks yield the largest preregistered nominal split-conformal level, **6/7 = 85.7%**, but the assumption-conditional lower-bound estimate is **0.0**. It is vacuous; spatial block exchangeability is unverified. **The score is not a guaranteed performance level for the private target or leaderboard.**

Of the 5,000 selected cells, 54 coincide with known public-catalogue labels. The local proxy DTI counts those known-fault pixels as positive; it does not establish discovery of withheld new faults. See the full [machine-readable experiment report](../h47qc-screen-20261006.json), the frozen [preregistration](../preregistered-h47qc-20261006.md), and the [hypothesis shortlist](../hypotheses-round2-20261006.md).

## Bounded uniqueness check

The exact positive mask has no match among 334 one-band rasters on the identical grid from 55 visible `buffedlizard55-lab` GEMSDOE repositories. Maximum top-5,000 equal-mass Jaccard was **0.002104**; maximum positive-support Jaccard was **0.002443**. All 336 inventoried TIFF blobs were fetched and checked against their recorded Git blob SHA-1; two were excluded for grid mismatch. This is a bounded public-inventory comparison, not proof of global uniqueness, provenance, score attribution, or model performance. A separate post-merge check against the other 12 same-grid TIFFs published in this repository found no exact positive-mask match; the maximum positive-support Jaccard was **0.003175** (H47-GSA). The pairwise H47-QC/H47-C1 Jaccard was **0.000915**. This local check supplements, but does not broaden, the public-inventory audit. Full comparisons and paths are in the [uniqueness audit](../h47qc-uniqueness-audit-20261006.json).

## Sources and limitations

The local CSV is an owner-hosted mirror attributed to DOE INGENIOUS [GDR submission 1391](https://gdr.openei.org/submissions/1391) (DOI [10.15121/1881483](https://doi.org/10.15121/1881483)), not an authenticated organizer download. The exact canonical definitions of its three exported geothermometer columns were not verified. Geothermometer consensus is not independent evidence: water type, disequilibrium, mixing/dilution, and data-entry/provenance errors can bias the estimates. Gravity and magnetic edges can mark contacts, intrusions, and processing artefacts as well as faults. The local labels are a known-fault public-catalogue proxy, not the private newly mapped target. See the [source register](../sources.md) and [full H47-QC report](../h47qc-screen-20261006.json).
