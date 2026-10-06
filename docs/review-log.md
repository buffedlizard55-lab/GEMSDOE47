# Review log and correction history

All dates are UTC. This log preserves the audit trail; a historical claim shown in a correction block is not current evidence.

## Superseding correction — 2026-10-06

An earlier project addendum incorrectly recommended the historical d-cat/annulus TIFF using a modeled score of 0.34912 and a claimed 0.34837 “75% conformal floor.” It treated three selected rungs from a monotone deletion family as exchangeable calibration examples and relied on unauthenticated participant-score-to-file mappings, including the alleged 0.2778 H33-2-B2 association. **Those performance and guarantee claims are withdrawn.** The TIFF is a delete-only subset of a published sibling network, not an independent detector. It is retained for historical review only and must not be uploaded.

An earlier in-repository leaderboard copy recorded 0.3345 as rank 1 and DARD at rank 5. The latest saved one-time observation in this session records rank 1 at 0.3774 (name not retained), DARD at 0.3195/#7, and `extradr19` at 0.2778/#13. No participant row authenticates a TIFF filename or hash. No automated leaderboard monitor is implemented.

## Current task review — 2026-10-06

### Pass 1 — implement and verify

- H47-B implementation, preregistration, experiment report, and ten focused tests are recorded in `gemsdoe47/magnetic.py`, `scripts/run_h2_experiment.py`, `tests/test_magnetic.py`, and `docs/preregistered-h2.md`.
- The experiment selected 5 px / 500 m and compared H47-B, a single-scale baseline, and a fixed-seed random control on the frozen 4 × 4 block split with 300 m guards.
- Locked-test pooled DTI was 0.027553 (H47-B), 0.025639 (baseline), 0.037159 (random). H47-B failed the random comparison. The six-block conformal calculation had a zero clipped floor and unverified exchangeability.
- The TIFF passed a local format/range audit and was copied to `docs/downloads/` only through `--publish-research-only`, with `research-not-submittable` in the filename and a machine-readable `RESEARCH_ONLY_NOT_FOR_PORTAL` status. No promoted/submission TIFF was published.
- The accessible-artifact audit compared 334 exact-grid rasters from 55 visible sibling repositories: zero exact positive-mask matches, max equal-mass Jaccard 0.01119. The tracked `docs/h47b-uniqueness-audit-20261006.json` now records all comparison rows, inventory paths/blob IDs, and the two grid-mismatch exclusions; scope remains bounded, not global.

### Pass 2 — bug, assumption, and attribution review

- **Gate result preserved:** no submission slot recommendation. A modest win over the single-scale baseline is insufficient because H47-B lost to random and its lower floor was zero; the public-mirror screen cannot confer slot eligibility under any outcome.
- **Research-only publication hardening:** removed H47-B's former non-research publication path. Its runner now always sets `slot_eligible: false`, exposes only `--publish-research-only`, uses a filename containing `research-not-submittable`, and refuses to overwrite that tracked file with different bytes. Added CLI/report tests.
- **Conformal review:** corrected the interpretation. The nominal 6/7 level is conditional on unverified exchangeability; two of six calibration blocks have no truth. No positive performance floor is claimed.
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

## H47-QC follow-up — 2026-10-06, fixed Arena branch

### Pass 1 — implement the frozen top-ranked hypothesis

- Read the standing charter and produced the four-item ranked H47-QC hypothesis shortlist before candidate code or DTI scoring. The selected method combines quality-screened geothermometer consensus with aligned RTP/isostatic-gravity gradients.
- Froze the input hashes, grouping, thresholds, weights, kernel/support, 5,000-point matched-budget controls, block roles, spacing sweep, conformal calculation, and fail-closed gate in `docs/preregistered-h47qc-20261006.md` before implementation.
- Implemented a label-blind builder in `src/gems47/geochem_consensus.py` and the full block sweep in `scripts/run_h47qc.py`. The feature builder does not read `labels.tif` or the label-derived `dist_known_fault_px` field; labels are opened only after score fields are built.
- Built the uniquely named all-finite binary research TIFF and an adjacent short note. SHA-256 is `3866b60cf91b4f6bff2ef694153550aa97a744a3091a57ef9f83da41e16b91b2`; 5,000 positive cells, all values in `[0,1]`, one-band float32, EPSG:32611, 100 m.
- The public-catalogue block screen selected 6 px / 600 m. H47-QC locked-test pooled DTI was **0.01316894**, below geochemistry-only **0.01419481**; random-within-support was 0.01285767. The 6-block split-conformal nominal level was **6/7 = 85.7%** and the clipped lower block-DTI floor was **0.0**. Fifty-four emitted cells overlap known public-catalogue labels. The preregistered gate failed; do not upload or spend a slot.

### Pass 2 — scientific, code, provenance, and attribution review

- Confirmed the top-ranked idea was genuinely new only within the explicitly reviewed implementation inventory; the source columns remain mirror-derived and their exact canonical GDR definitions were not verified.
- Downloaded and Git-blob-verified all 336 TIFF blobs from the previously captured 55-repository public inventory. Against the 334 exact-grid one-band rasters: zero exact mask matches; maximum top-5,000 equal-mass Jaccard **0.00210442**, maximum positive-support Jaccard **0.00244346**. This is bounded artifact uniqueness, not global novelty or validation.
- Rechecked the label-blind boundary, weight formula, support intersection, spacing selection, fixed block roles, controls, and report/hash linkage. Corrected the sample-template SHA-256 transcription in the preregistration to match the pinned manifest.
- Scientific review found and corrected two historical overclaims: (1) the 0.2778 participant row is not authenticated to H33-2-B2, which the owner marks “UNSCORED”; deleting only catalogue-masked pixels cannot explain a score rise under the staff-described mask semantics; (2) the earlier 102.7% recall-at-`F/K=8.02` claim contradicted the displayed equation. The corrected illustrative values are 82.05% for 0.3195 and 98.13% for the one-time 0.3774 public-leader reference; `F/K=8.02` itself is unverified.
- Reworked current-facing pages to keep the one-click artifact conspicuously **NOT PROMOTED / DO NOT SUBMIT**, update the stale leader reference, bound source and score claims, and prohibit using an unlimited round to bypass the holdout gate. README retains the project charter for future sessions.
- A final narrative audit removed unverified claims that 706/716 official 1 m tiles were available, that the LATI `K` estimate was model-free, that the owner-reported mask comparison proved scorer internals, or that the 0.2778 association definitively falsified a hypothesis. The 3DEP exact-footprint coverage remains unmeasured. The NaN scan is now described as a demonstrated failure mode, not the proven cause of the missing historical rejection.

### Pass 3 — full brief, tests, artifact and release check

- `.venv/bin/ruff check .` and `git diff --check`: passed.
- `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`: **68 passed, 2 skipped**. The skips are optional tests requiring mirrored inputs; these inputs were available for the separate H47-QC run.
- `PYTHONPATH=src .venv/bin/python -m pytest tests -q`: **106 passed, 2 skipped, 2 subtests passed**.
- `src/gems47_metric.py`: **8/8** self-checks passed. `scripts/verify_grid.py`: **16/16** checks passed.
- The final H47-QC GeoTIFF was reopened and passed the repository's read-back format/range checks: exactly 5,000 emissions, all finite, values `{0,1}`, no nodata sentinel, no out-of-footprint emissions. The local validator's `recommended_for_upload` is a *format-only* result; the scientific gate remains closed.
- The final runner was rerun after adding a transparent implementation note about the one-pixel finite-difference support erosion. Scores and the TIFF remained byte-identical: pooled DTI 0.0131689425, spacing 6 px, clipped floor 0.0, TIFF SHA-256 `3866b60cf91b4f6bff2ef694153550aa97a744a3091a57ef9f83da41e16b91b2`.
- The evidence JSON in `evidence/` and identical GitHub-Pages copy in `docs/` have matching bytes. The report's candidate SHA-256 matches the TIFF, and the uniqueness audit references the same final hash.
- Current non-archive site pages have 191 relative links checked with zero missing; the unit suite's site checks also pass. The verbatim `docs/prev-session/` historical snapshot is intentionally unchanged.
- No competition portal access, upload, slot, leaderboard polling, or private-target claim was made. The PR/merge on the current fixed branch remains pending until remote checks are verified.

## Historical negative screens retained

- H1 radiometric-halo first screen: full-domain matched-mass catalogue DTI 0.0156 vs 0.0369 seeded uniform control; negative screening evidence, not a spatial holdout.
- H47-A acquisition-invariant edge screen: implementation exists, but no authorized aligned acquisition pair or valid spatial holdout result is recorded.
- H47-B: negative result above; do not retune against the same locked blocks and call it independent.
