# Review log and correction history

All dates are UTC. This log preserves the audit trail; a historical claim shown in a correction block is not current evidence.

## Superseding correction — 2026-10-06

An earlier project addendum incorrectly recommended the historical d-cat/annulus TIFF using a modeled score of 0.34912 and a claimed 0.34837 “75% conformal floor.” It treated three selected rungs from a monotone deletion family as exchangeable calibration examples and relied on unauthenticated participant-score-to-file mappings, including the alleged 0.2778 H33-2-B2 association. **Those performance and guarantee claims are withdrawn.** The TIFF is a delete-only subset of a published sibling network, not an independent detector. It is retained for historical review only and must not be uploaded.

An earlier in-repository leaderboard copy recorded 0.3345 as rank 1 and DARD at rank 5. The latest saved one-time observation in this session records rank 1 at 0.3774 (name not retained), DARD at 0.3195/#7, and `extradr19` at 0.2778/#13. No participant row authenticates a TIFF filename or hash. No automated leaderboard monitor is implemented.

## Initial H47-B implementation review — 2026-10-06

### Pass 1 — implement and verify

- H47-B implementation, preregistration, experiment report, and ten focused tests are recorded in `gemsdoe47/magnetic.py`, `scripts/run_h2_experiment.py`, `tests/test_magnetic.py`, and `docs/preregistered-h2.md`.
- The experiment selected 5 px / 500 m and compared H47-B, a single-scale baseline, and a fixed-seed random control on the frozen 4 × 4 block split with 300 m guards.
- Locked-test pooled DTI against `labels.tif == 1` (the known-fault catalogue-mask resemblance proxy) was 0.027553 (H47-B), 0.025639 (baseline), and 0.037159 (random). These are diagnostic proxy values, not missing-fault target scores; H47-B failed the random comparison. The six-proxy-block conformal calculation had a zero clipped floor and unverified spatial exchangeability.
- The TIFF passed a local format/range audit and was copied to `docs/downloads/` only through `--publish-research-only`, with `research-not-submittable` in the filename and a machine-readable `RESEARCH_ONLY_NOT_FOR_PORTAL` status. No promoted/submission TIFF was published.
- The accessible-artifact audit compared 334 exact-grid rasters from 55 visible sibling repositories: zero exact positive-mask matches, max equal-mass Jaccard 0.01119. The tracked `docs/h47b-uniqueness-audit-20261006.json` now records all comparison rows, inventory paths/blob IDs, and the two grid-mismatch exclusions; scope remains bounded, not global.

### Pass 2 — bug, assumption, and attribution review

- **Gate result preserved:** no submission slot recommendation. A modest win over the single-scale baseline is insufficient because H47-B lost to random and its lower floor was zero; the public-mirror screen cannot confer slot eligibility under any outcome.
- **Research-only publication hardening:** removed H47-B's former non-research publication path. Its runner now always sets `slot_eligible: false`, exposes only `--publish-research-only`, uses a filename containing `research-not-submittable`, and refuses to overwrite that tracked file with different bytes. Added CLI/report tests.
- **Conformal review:** corrected the interpretation. The nominal 6/7 level is only for a future comparable block-level DTI against the known-catalogue-mask proxy and is conditional on unverified spatial exchangeability; two of six calibration blocks have no catalogue-mask pixels. It provides no missing-fault or leaderboard coverage claim, and no positive proxy floor is claimed.
- **Post-score target-semantics correction:** `labels.tif == 1` is the known USGS/INGENIOUS fault-catalogue mask excluded from actual off-catalogue evaluation. The local DTI and conformal result are resemblance-proxy diagnostics, not missing-fault validation/coverage. No data, block assignments, formulas, or scores changed. The original frozen preregistration SHA-256 is retained in `docs/h47b-screen-report-20261006.json`, alongside the hash of the clarified document.
- **Source review:** H47-B feature/label/template files are group-hosted mirrors, not authenticated organizer downloads. Local DTI code is a formula implementation of the public problem description, not an organizer-run scorer.
- **Score review:** no mapping from participant leaderboard rows to TIFF hashes is available. The 0.2778/H33-2-B2 relationship remains unverified and the owner page marks that candidate unscored.
- **Uniqueness review:** low similarity to the searched artifacts does not prove global uniqueness or scientific value. The historical d-cat TIFF's lineage makes it ineligible under the no-copy requirement despite byte uniqueness.
- **Site review:** the top download and executive-summary page use unmistakable “RESEARCH ONLY / DO NOT SUBMIT” language; submission instructions are future-candidate-only and manual. Prior modeled/conformal claims and stale board values are removed from current-facing pages and preserved only as retired history.
- **Legacy packager review:** `scripts/package_submission.py` remains H47-A-only and does not authorize H47-B. Its schema is now version 2 and names a pinned local formula implementation rather than implying an organizer-run scorer; it remains a human-reviewed packaging aid, not scientific approval.

### Pass 3 — full brief and release check

Local review is complete; remote checks and the requested PR merge are pending.

- `.venv/bin/python -m unittest discover -s tests -v`: **68 tests passed**. This includes restored synthetic DTI tests, site/link/metadata checks, the research-only H47-B publication guard, the bounded uniqueness-record consistency check, and fail-closed retired-entrypoint checks.
- `.venv/bin/python -m ruff check .` and `git diff --check`: passed.
- `src/gems47_metric.py` self-test: 8/8 passed. The exact tracked H47-B research TIFF was reopened against the local mirrored template/footprint: PASS, SHA-256 `7e5df9d01689e438e8379ebd4763ed803de02e94826f43da37c33c16380d669b`.
- Parsed the JSON ledgers/reports and checked the full uniqueness audit invariants: 55 repositories, 425 tracked paths, 336 unique blobs, 334 exact-grid comparisons, 2 disclosed grid mismatches, zero exact positive-mask matches. All HTML local-link/accessibility checks passed in the unit suite.
- The H47-B spatial experiment was **not rerun** after the already-observed locked result; subsequent edits harden publication/status wording and non-scoring formatting only. No new scientific result is claimed.
- PR **#5** was opened from the fixed branch `arena/ff217a74-gemsdoe47` to `main`; its initial required GitHub `test` check passed. This review-log follow-up must also pass checks before merge. The GitHub PR history is the authoritative record of final-head checks and merge state; neither merge nor format validity changes H47-B's `NOT_PROMOTED` scientific status.

## NaN-outside artifact and footprint-scope follow-up — 2026-10-06

### Pass 1 — implement and verify

- Generated a new single-scale d=5 research TIFF at `docs/downloads/gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-nanoutside.tif`: 309,530 bytes, SHA-256 `dc71c807fbca2cd398f394bcd91b10ecec6b46fe89c2d61f5b1c058fef672811`; one-band float32, EPSG:32611, 100 m, exact sample-template grid, NaN nodata/outside, `[0,1]` in-footprint, 18,524 positive cells.
- `scripts/validate_submission.py` passes when given a binary footprint mask built from finite, unmasked cells in the mirrored sample template. The strict validator records 5,167,373 valid and 7,111,787 outside pixels, zero invalid-inside cells, zero non-NaN outside cells, and no range violations.
- Added `scripts/build_footprint_mask.py` and tests. It emits a one-band uint8 mask, preserves the template grid, hashes both inputs/outputs, and explicitly disclaims provenance/organizer semantics.

### Pass 2 — bug, assumption, and edge-case review

- Windowed comparison found that the local sample and label footprints each contain 5,167,373 pixels, while the 19-band feature-valid footprint contains 5,165,852. There are 1,540 feature-valid cells outside the sample/label footprint and 3,061 sample/label cells invalid or masked in features. Validation against the feature-derived footprint therefore fails in both directions; the report records the exact 1,540/3,061 validator messages. IR-25 and IR-47-020 flag the mismatch. Neither mirror-derived footprint is claimed as the authenticated official evaluation footprint.
- Kept the paired all-finite TIFF only as a non-primary diagnostic (SHA-256 `c640b71c7c57066dd77bbd42fcb6c436d0a8c201de6b0ec1d88ab25976089501`); it has the same positive mask but fails strict validation because its nodata tag is unset. The NaN-intolerant range probe is described as a plausible parser hazard only; the historical portal rejection cause remains unknown.
- Updated the uniqueness evidence for the NaN-outside primary against 19 independent local prior TIFFs and retained the prior 334-artifact remote mask comparison only after verifying the paired all-finite diagnostic has the identical positive mask on the candidate grid. There are zero exact matches; max equal-mass Jaccard is 0.012905 remote and 0.020550 local. This remains a bounded inventory result, not global uniqueness or a performance claim.
- Corrected the root and docs landing pages, executive summary, analysis, submission guide, download manifest, and irregularity records so the primary download, exact SHA-256, explicit-mask audit scope, no-slot decision, and uncertainty are consistent. Future instructions now demonstrate the mask-builder and validator commands conditionally on authorized instructions.

### Pass 3 — whole-brief and release review

- Rechecked the result against the standing brief: the reported 0.2778 score remains unattributed; four prospective hypotheses remain unbuilt and ranked; split conformal is limited to a known-catalogue-mask proxy with six calibration blocks, rank 6/6, nominal 6/7 under unverified exchangeability, and zero clipped lower floor; the tested candidate still loses to H47-B and random control. No competition slot is recommended.
- Verification: 79 unittest tests passed with 2 skips; pytest reports 113 passed, 2 skipped, and 2 passing subtests. Ruff, `git diff --check`, and JSON parsing passed. The research TIFF passed the strict CLI validator only when supplied the generated sample-template mask; the feature-derived mask failure is captured in the JSON report.
- Pull request creation and merge are the remaining release actions; final PR checks and merge state will be recorded after the remote operation.

## Historical negative screens retained

- H1 radiometric-halo first screen: full-domain matched-mass catalogue DTI 0.0156 vs 0.0369 seeded uniform control; negative screening evidence, not a spatial holdout.
- H47-A acquisition-invariant edge screen: implementation exists, but no authorized aligned acquisition pair or valid spatial holdout result is recorded.
- H47-B: negative result above; do not retune against the same locked blocks and call it independent.
