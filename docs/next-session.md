# Next-session plan — continue from the verified state

> **Current state (2026-10-06 UTC): no eligible submission and no slot recommendation.** The latest H47-QC screen selected 6 px / 600 m at 5,000 points, scored 0.013169 on locked public-catalogue blocks, lost to the geochemistry-only ablation (0.014195), and had an 85.7% nominal split-conformal level with a 0.0 lower floor. H47-B also lost to random; H47-GSA failed cross-fit. All are research only. The legacy d-cat/annulus TIFF is a delete-only subset of a published mask. Old 0.34912/0.34837 claims, the erroneous 102.7% recall statement, and the earlier 0.3345 rank-1 board snapshot are superseded. Do not repeat those claims.

## Ordered actions

1. **Keep every slot closed.** Do not upload any TIFF in `docs/downloads/`, including H47-QC. H47-QC's valid format and low similarity to accessible artifacts do not outweigh its failed matched-mass and conformal gates.
2. **Establish authorized data provenance.** The official DrivenData data page is login-gated. If this work continues under an authorized entrant account, preserve the exact official feature, catalogue-label and sample-template bytes/hashes and compare them with the group-hosted `GEMSDOE24` mirror. Do not bypass login. The current H47-B report is explicitly based on mirror files.
3. **Build a comparable incumbent.** No artifact-authenticated, comparable spatially blocked “current best” has been established. Build and save a reproducible baseline plus fold report with the official task formula, adequate truth counts and disjoint guarded spatial cores. Do not treat leaderboard scores or the historical TIFF as an incumbent.
4. **Resolve next-candidate feasibility before coding.** First inspect official USGS QFFD geometry/metadata for H47-C and count its footprint coverage; the available local summary CSV is not trace geometry. If coverage is insufficient, assess official ASTER alteration polygons (H47-D) or INGENIOUS temporal well/spring records (H47-F), counting and mapping coverage before proposing implementation. Record licenses and source URLs.
5. **Rank and preregister a genuinely new detector.** State the physical signature, missing-catalogue rationale, known confounders, controls, exact inputs/hashes, split assignment, mass, metric and promotion gate. Do not tune on a locked block. H47-B's existing held-out data must not be recycled as an independent test for a re-tuned version.
6. **Run the full evaluation.** Compare against the current spatial holdout best and same-mass random/domain controls, report pooled and per-block DTI, label coverage, calibration assumptions and failure regions. No slot unless the predeclared rule passes.
7. **Audit the candidate file.** Build a new TIFF only from a promoted output; validate exact bytes/grid/range/nodata, assign a unique filename and note, and compare against accessible historical artifacts. Repeat the uniqueness check if new repositories or artifacts become visible; never claim global uniqueness from the current inventory.
8. **Update the site and release only after evidence.** Keep research downloads conspicuously labeled. A distinct, newly promoted candidate may be linked at the top only after full review; H47-B itself must remain research-only and must never be renamed or relabeled as a submission. Submit manually through an authorized portal account and retain the organizer receipt.
9. **Delivery gate.** Complete the three review passes, full test suite, Ruff, local HTML-link checks, and GitHub CI. Open/merge a PR only when all evidence and wording are consistent. This repository never submits automatically and does not monitor the leaderboard.

## Current source boundaries

- **Official pages reviewed:** DrivenData problem/data/rules/leaderboard pages; USGS GeoDAWN, QFFD, 3DEP, ASTER; DOE INGENIOUS; NASA/USGS sources listed in [`sources.md`](sources.md).
- **Not directly acquired here:** official raw GeoDAWN archives and authenticated competition inputs. H47-B used a public owner-hosted mirror.
- **No authenticated file-to-score receipt:** public participant rows, including 0.2778, do not identify a TIFF.
- **Latest saved public-board observation:** rank 1 = 0.3774 (name not retained); DARD = 0.3195/#7; `extradr19` = 0.2778/#13. The old 0.3345/#1 snapshot is stale. No automated monitoring.
- **Current bounded uniqueness finding:** H47-QC has zero exact positive-mask matches among 334 exact-grid rasters from 55 visible sibling repositories; maximum top-5,000 equal-mass Jaccard 0.002104 and positive-support Jaccard 0.002443. The full comparison is in [`h47qc-uniqueness-audit-20261006.json`](h47qc-uniqueness-audit-20261006.json). This is not a global uniqueness claim or submission authorization.

## Continue from these files

- [`preregistered-h47qc-20261006.md`](preregistered-h47qc-20261006.md), [`h47qc-screen-20261006.json`](h47qc-screen-20261006.json), and [`h47qc-uniqueness-audit-20261006.json`](h47qc-uniqueness-audit-20261006.json) — current candidate, result and bounded uniqueness audit
- [`downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.tif`](downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.tif) — format-valid research artifact; do not submit
- [`validation-h47b-20261006.md`](validation-h47b-20261006.md), [`h47b-screen-report-20261006.json`](h47b-screen-report-20261006.json), and [`h47b-uniqueness-audit-20261006.json`](h47b-uniqueness-audit-20261006.json) — prior negative screen
- [`preregistered-h2.md`](preregistered-h2.md) — frozen H47-B protocol
- [`hypotheses-round2-20261006.md`](hypotheses-round2-20261006.md) — four fresh hypotheses ranked before H47-QC implementation
- [`hypotheses.html`](hypotheses.html) — legacy hypothesis results, with attribution caveats
- [`irregularities.md`](irregularities.md) — open evidence flags
- [`sources.md`](sources.md) — official and secondary provenance
- [`README.md`](../README.md) — standing charter and current decision
