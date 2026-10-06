# Spatial holdout and promotion protocol

**Locked:** 2026-10-06 UTC, before any candidate scoring. **No holdout was run.** This is an auditable gate and helper implementation, not validation evidence.

## Before a fold is evaluated

- Acquire the authorized competition inputs from the official [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), preserve SHA-256 hashes and grid metadata, and record label semantics.
- Identify the incumbent using its exact code/input hashes and verified local out-of-fold report. No incumbent score exists in this checkout; do not infer one from the user's prior public scores.
- Fix the spatial block size, coordinate origin, seed, H47-A quantile, flight-line penalty variants, prediction mass, and all controls in a dated preregistration receipt **before computing held-out metrics**.
- Reserve at least three geographically distinct folds. The `spatial_block_folds` helper assigns complete square cells to folds and purges from training any cells whose rectangle is within the configured guard of a held-out block. Use projected coordinates in metres and guard at least **300 m**, matching the official distance kernel's support. A proposed seed/block configuration that leaves no training points after purging must fail before scoring; adjust block size or fold count during preregistration, not after inspecting candidate scores.
- Use the official reference solution for the competition score; do not substitute an unverified clone of the scorer. Evaluate whole out-of-fold maps with the same metric version and locked valid-footprint mask.

## Locked promotion rule for the package utility

`scripts/package_submission.py` refuses to package unless the reviewed JSON report records all of these:

1. authorized official inputs, preregistration before scoring, spatially blocked splits, explicit controls, and `official_dw_tversky` scoring;
2. guard ≥300 m, at least three unique folds, and equal emitted mass for candidate/incumbent in every fold;
3. pooled holdout score and unweighted mean fold score both strictly above the incumbent, **and** the candidate better than incumbent in at least two-thirds of folds (ceiling for fractional fold counts);
4. SHA-256 of prediction, official template, feature raster, source-data files, preregistration and fold assignment recorded; model code revision and official scorer version pinned; and
5. a successful byte-level audit of both the source prediction and newly packaged GeoTIFF. Packaging also requires that the current Git revision match the promoted code commit and the tracked working tree be clean.

The package script checks these claims mechanically but **does not authenticate the scientific honesty of the report**. A reviewer must inspect fold definitions, code, controls, official scorer version and receipts. The packager only creates a local artifact under ignored `artifacts/`; it does not submit a portal entry or publish a website download.

## Honest interpretation

A gain on spatially held-out public catalogue traces is evidence against some forms of spatial overfit, not proof that the surface discovers faults absent from that catalogue. Report fold-level scores and uncertainty, null/random controls, ablations, label coverage and failure regions. A tie, unstable fold pattern, failed control or missing authorized file keeps the slot gate closed.
