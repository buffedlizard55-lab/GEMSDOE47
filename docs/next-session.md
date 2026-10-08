# Next-session handoff — 8 October 2026

**Start with `README.md` and the current artifact receipt.** Current decision: **H65 is research-only, not promoted, do not upload or spend a slot.** No portal action, score request, final selection, or slot use occurred. The user has now explicitly asked to create and merge a PR; that work is still pending until GitHub confirms it.

## Current deliverables

- New H65 research TIFF: `docs/downloads/gemsdoe47-h65-paired-scarp-consensus-s2p8-20261008-research-only-nanoutside.tif`, 360,524 bytes, SHA-256 `10834af251114a4aa0bf6138eea497db4299ab968873a0cfaab1836062dc2992`. Local format checks pass against the owner-mirrored grid; organizer acceptance is unknown.
- H65 selected spacing: 2.8 px / 280 m; selection/calibration 20/21; rank 20/22; nominal 90%, finite-sample marginal level at least 20/22 = 90.91% only under unverified block exchangeability. Proxy floor 0.007885. Blocks were previously examined, so H65 is exploratory.
- Promotion fails: independent SGMC selection pooled DTI 0.083472 vs corrected H50 0.135296 (−0.051824). H65−H60 simultaneous paired lower bound −0.062127; preregistered positive-bound criterion fails. No score establishes that any candidate beats the user-reported 0.3774 leaderboard high.
- Prepared future-only name/comment (not authorized to use): `GEMSDOE47-H65-paired-scarp-s2p8-20261008` / `H65 paired scarp consensus d2p8`.
- Hypotheses H65–H68 were preregistered before H65 screening in `docs/research/h65-hypotheses-preregistered-20261008.md`, with layer details, physical signatures, novelty boundaries, expected value/cost, official source links and data-availability caveats.

## Work completed in this continuation

1. Completed the broad prior-TIFF uniqueness audit: 334 exact-grid blobs attempted from a historical inventory of 55 visible sibling repositories; 333 were verified and 1 stale GEMSDOE47 archive path returned HTTP 404. There were zero exact positive-mask matches among verified rasters; maximum cross-repository positive-support Jaccard was 0.052772. Local prior-TIFF maximum was 0.181209 against H60. This is bounded evidence, not global uniqueness. Full machine receipt: `evidence/h65/uniqueness-audit.json`; audit hash is recorded in the H65 receipt/current status.
2. Reconciled `docs/data/h65-research-tiff.json` with the current builder-source SHA. **That hash was recorded during receipt reconciliation after the TIFF was generated; the exact pre-edit builder source from generation time was not retained.** Rechecked the TIFF SHA and byte count; the TIFF itself was not rebuilt or changed.
3. Copied screen, spacing, H50 comparison, uniqueness and corrected H60-family evidence into `docs/data/` for deployment-safe links. Updated page references to these deployed copies.
4. Replaced/updated root and docs landing pages, H65 results, executive summary, current status, submission boundary, artifact register, H60 corrected-history page, hypotheses, leaderboard, sources and irregularity pages. Replaced stale legacy upload aliases with explicit current no-submit boundaries. H60's old restricted-emission-domain scores/floor are labelled superseded; corrected full-domain results are shown.
5. Replaced README with this standing brief, current results/decision, exact H65 artifact contract, full task and no-slot constraints, historical H60 correction, ranked hypotheses, source caveats, reproduction guidance and three-pass protocol. `README.md` must be read before future work.
6. Preserved the 8 October partial leaderboard observation with its limitations: raw page/timestamp not retained; subsequent unauthenticated fetch returned only “Loading...”. No participant row is treated as a TIFF-score receipt; H33-2-B2 / 0.2778 remains unverified.
7. Updated stale site tests for the H65 no-submit state and exact current artifact. The full suite last run: **303 passed, 21 skipped, 13 subtests passed, 1 Rasterio PendingDeprecationWarning**. Ruff: **All checks passed**. Re-run once more after the final test/receipt edit before committing.

## Three-pass review record

- **Pass 1 — implement and verify:** H65 screen/artifact, local read-back, exact SHA/format, corrected H60-family full-domain runner, machine receipts and local/broad uniqueness checks. The old H60 scoring-domain and FN aggregation errors are preserved and documented.
- **Pass 2 — review and fix:** found/reconciled stale H60 “current candidate” copy, outdated README/site/submission aliases, broken docs-only links to root `evidence/`, and tests that still asserted H60 as current. Replaced those links with deployed `docs/data/` copies, corrected the copy and tests, and surfaced the one inventory-fetch failure rather than hiding it.
- **Pass 3 — recheck against original request:** no-submit status is prominent beside the download; H33 attribution and 0.3774 target are explicitly uncertain/untested; split-conformal rank/coverage/floor and exchangeability/adaptivity limits are stated; 4 preregistered geological hypotheses and official source checks are linked; output is normalized and exact-byte grid/CRS/transform/range/outside encoding are checked; uniqueness is bounded and one 404 is recorded. The full test/lint/link review passed before the last small test assertion was added; rerun as above.

## Remaining next steps

1. Run `PYTHONPATH=src .venv/bin/python -m pytest tests -q`, `.venv/bin/python -m ruff check .`, `git diff --check`, and confirm the exact TIFF and builder hashes.
2. Review final diff/status for unintended files and stale claims. Do not add `.venv` or ignored data/cache.
3. Commit and push **only** to `arena/e84433ec-gemsdoe47`.
4. Create a PR from this branch to `main` with `gh`; wait for checks, fix any failures, and merge if GitHub reports it is mergeable. Report the PR/merge URL and status. Do not claim completion until confirmed.

## Non-negotiable boundary

No candidate is cleared for competition upload. A new hypothesis must beat the current spatial-holdout best on fresh preregistered confirmation; user authorization and authenticated account/slot/format checks are separate prerequisites. Local public-proxy DTI is not a competition score. Do not upload or spend a weekly slot in this review.
