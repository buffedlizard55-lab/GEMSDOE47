# Next-session handoff — H49 review and GitHub publication

**Read `README.md` §0 before any work.** The complete available brief is preserved there, along with the current H49 decision, exact hashes and assumptions.

## Current decision

The current research TIFF is `docs/downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif`, SHA-256 `f2cec409ce3bec5a2805f1fab9a12ab7f72394f8be79cc365134ce43708c6060`, 409,124 bytes, 37,612 positive pixels. It passes 19 gating format/read-back checks; the whole-grid range flag is informational. Its pinned public-inventory uniqueness audit is bounded to 54 visible repositories and 565 comparisons. It is **not** globally certified unique, scientifically promoted, organizer-scored or accepted.

**Do not upload this TIFF or spend a weekly submission slot.** The nominal fixed-arm 90% split-conformal statistic is 0.03184 at spacing 2.8 px / 280 m, based on 19 calibration 8×8 blocks and order statistic `k=18`, targeting public SGMC off-catalogue block DTI. Exchangeability and independent prospective fixation of the rule are assumptions; SGMC includes non-fault contacts; the final mean rule was amended after results. Both candidate arms have negative 90% paired-improvement lower bounds versus the H33-labelled reference.

## Verified checks at handoff

- Focused TIFF/H49 tests: 29 passed.
- Full suite: 254 passed, 1 known Rasterio `PendingDeprecationWarning`, 2 subtests passed.
- Ruff: clean.
- `scripts/update_site_h49.py --check`: 0 problems.
- `scripts/build_site_s3.py --check`: 124 tracked docs files checked; all changes within declared owned pages or H49 marker blocks.
- No DrivenData upload was made; there is no organizer score or acceptance receipt.

## Immediate GitHub task

Work only on `arena/24b6e85a-gemsdoe47`. Fetch `origin/main`, reconcile it into this branch without switching branches, rerun validation on the reconciled tree, create a PR from this branch, check CI, and merge only if all required checks pass. Do not mark the PR complete until GitHub confirms the merge.

## Scientific work that remains

1. Keep the H49 slot gate closed.
2. Define a prospective candidate protocol and collect a fresh spatially blocked holdout not reused from H49; require positive paired improvement over the holdout best plus matched-mass and shifted/random controls.
3. Verify actual free official 1 m data files, licensing and footprint coverage before treating H50 LiDAR as viable.
4. If an organizer receipt becomes available, resolve whether any H33 score maps to the exact H33 TIFF hash. Current owner evidence calls H33 unscored / 0.2747 projected.
5. Rebuild old inversion outputs only after the missing exact `data/reference/` TIFFs are restored.

Re-read `docs/REMAINING_WORK.md`, `docs/COMPLIANCE.md`, `docs/H49_RESULTS.md` and `docs/RESEARCH_HYPOTHESES.md` before changing the artifact or decision.
