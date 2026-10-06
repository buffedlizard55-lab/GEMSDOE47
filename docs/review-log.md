# Three-pass implementation and review log

**Date:** 2026-10-06 UTC

**Reviewer:** GEMSDOE47 project agent; this is an engineering/research checklist, not a geology peer review.

**Final state:** documentation, an H47-A screening implementation, a spatial-fold helper, a strict GeoTIFF validator, and a gated local packager are present. No official competition data, scientific holdout result, validated model, or submission TIFF is present. **Slot gate remains CLOSED.**

## Pass 1 — task, source, and scientific review

**Reviewed:** the official DrivenData problem description, competition home/data/leaderboard/terms links, official rules and reference-solution references; USGS GeoDAWN ScienceBase; USGS ASTER, Water Services and fault sources; NASA ASF/Sentinel-1; and owner-authored GEMSDOE32/41/42 evidence. See [`sources.md`](sources.md) and [`analysis.md`](analysis.md).

**Findings and fixes:**

- The public board is participant-level and had moved beyond the user's 0.3195 figure at the 2026-10-06 capture. A dated 0.3345 top-row snapshot now carries explicit moving-board/private-score caveats.
- The public 0.2778 row belongs to participant `extradr19`; no public evidence maps it to the H33-2-B2 TIFF. GEMSDOE32 marks that candidate **UNSCORED** and GEMSDOE41 calls the filename mapping unauthenticated. All pages and analysis preserve that distinction.
- The unauthenticated official problem page names `training_features.tif` and `1m_DEM_links.csv`, but does not expose exact label/template basenames. The data checker now accepts the entrant's actual paths instead of assuming a hidden filename.
- Re-read the official DTI equations; removed an over-simplified `alpha`-only marginal-pixel claim. The analysis now directs users to the official scorer because prediction changes affect coupled TP/FP/FN terms.
- Four distinct hypotheses were ranked before candidate detector implementation. H47-A is still a prior, not an observed win. No official data or spatial holdout could be obtained without an authorized entrant login; no slot is recommended.

## Pass 2 — implementation, edge cases, and tests

**Reviewed line-by-line:** `gemsdoe47/candidate.py`, `spatial.py`, `validation.py`, `scripts/check_competition_data.py`, `build_h47a.py`, `validate_submission.py`, and `package_submission.py`; also report schema, tests, and ignored-data rules.

**Findings and fixes:**

- Robust edge scaling originally risked collapsing sparse lineaments to a zero percentile. Scale now uses positive valid gradients; a sparse synthetic-line test protects the case.
- Masked integer arrays are converted safely to float64 before NaN filling; tiny arrays fail to an all-NaN/no-support surface rather than raising inside `numpy.gradient`.
- Nodata neighborhoods cannot create artificial edges; grid mismatches fail instead of silently resampling; research output writes atomically to ignored paths and carries a `NOT_RUN` receipt/tag.
- Spatial folds purge full neighboring blocks, reject empty post-purge training folds, use deterministic seeds, and are explicitly only a split helper—not a score. An initially chosen synthetic seed left no training points; that configuration was rejected rather than weakening the guard.
- The TIFF checker reads persisted bytes and checks one float32 band, reference geometry, NaN nodata, explicit feature-derived/binary footprint, all in-footprint values in `[0,1]`, and NaN outside. Synthetic tests cover range, nodata, masks, transform and band/type contracts.
- Packaging now requires a human-reviewed promotion report, authorized/preregistered blocked folds with ≥300 m guard, same emitted mass, pooled and mean gain, ≥2/3 fold wins, controls/ablations, hashes and code/scorer provenance; it reopens output bytes, checks pixels are unchanged, generates a timestamp+SHA filename, and does not submit. Tests explicitly reject failed or incomplete gates.
- No method has been evaluated on geological observations. Tests use synthetic arrays/files only and must not be quoted as a model score.

**Verification:** `python -m py_compile gemsdoe47/*.py scripts/*.py tests/*.py`; `ruff check gemsdoe47 scripts tests`; and `python -m unittest discover -s tests -v` passed. The final suite reported **32 tests, all passing**. JSON snapshot/schema parse checks passed. `scripts/check_competition_data.py` was smoke-tested against an empty directory and correctly exited 2 with the official login-gated source and no download attempt.

## Pass 3 — user site, links, and end-to-end audit

- Confirmed GitHub Pages is configured as a legacy root source on `main`, so `index.html` is at the repository root. The opening viewport puts the status/download control before other research content.
- The download control is visibly disabled with an explanation because there is no validated TIFF. No placeholder, old TIFF, or fabricated artifact is linked. The executive-summary subpage states the manual submission sequence and blockers.
- Markdown source links in static HTML point to GitHub's rendered `main` views; local `.html` links are checked by a test. This avoids relying on browser interpretation of `.md` URLs in the Pages build.
- Local HTTP smoke requests returned 200 for the home page, executive summary, leaderboard snapshot and portal checklist. Static tests verify page titles, descriptions, `lang=en`, internal targets, the disabled download gate, and no TIFF link while the gate is closed.
- Confirmed no synthetic test raster, competition input, candidate artifact or other test data remains in the checkout; runtime/temp files are ignored or cleaned up.

## Remaining blockers / what this review did not do

1. The official DrivenData data page requires authorized entrant login. The project has no credentials and does not bypass it. The exact free official data source is the competition's own [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/); H47-A additionally needs the official [USGS GeoDAWN ScienceBase products](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), whose catalog links have not been downloaded here.
2. Exact target/overlap coverage, current local incumbent, block configuration on actual labels, model scoring, and private-label performance remain unknown.
3. No actual submission TIFF or usable download can be delivered until authorized inputs are present and a candidate passes the locked spatial holdout. Do not submit, spend a slot, or edit the site to imply otherwise.
4. A passing synthetic test or format validator establishes software behavior, not geologic validity, leaderboard score, discovery of unmapped faults, or entrant eligibility.
