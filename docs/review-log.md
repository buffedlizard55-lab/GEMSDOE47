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
- The first remote CI run emitted Node.js 20 deprecation and `ubuntu-latest` migration warnings. Updated to `actions/checkout@v7`, `actions/setup-python@v7`, and pinned `ubuntu-24.04`; the latest PR workflow then completed successfully without those annotations.
- Confirmed no synthetic test raster, competition input, candidate artifact or other test data remains in the checkout; runtime/temp files are ignored or cleaned up.

## Remaining blockers / what this review did not do

1. The official DrivenData data page requires authorized entrant login. The project has no credentials and does not bypass it. The exact free official data source is the competition's own [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/); H47-A additionally needs the official [USGS GeoDAWN ScienceBase products](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), whose catalog links have not been downloaded here.
2. Exact target/overlap coverage, current local incumbent, block configuration on actual labels, model scoring, and private-label performance remain unknown.
3. No actual submission TIFF or usable download can be delivered until authorized inputs are present and a candidate passes the locked spatial holdout. Do not submit, spend a slot, or edit the site to imply otherwise.
4. A passing synthetic test or format validator establishes software behavior, not geologic validity, leaderboard score, discovery of unmapped faults, or entrant eligibility.

---

# Addendum — same-day verification pass in a clean sandbox (2026-10-06)

A later session re-ran the entire audit trail from a fresh checkout with **no cached reference data**,
downloading every input independently from GitHub. Results (all reproducible with the commands below):

| check | result |
|---|---|
| `python3 src/gems47_metric.py` | 8/8 self-tests pass, incl. a **new regression test on the organizer's worked example** (TP 3.00, FP 1.89, FN 2.00 → 0.602651, the page's "0.60") |
| `python3 -m unittest discover -s tests` | 53 tests, all pass (2 skipped: need `data/`) |
| base artifact sha256 vs GEMSDOE33 receipt | identical (`c5e07fad…`) |
| `labels.tif` vs `existing_faults.tif` | byte-identical, sha256 `7ba308cc…`, confirming `KNOWLEDGE.md` A2 |
| grid: labels / sample_submission / ours | 3730×3292, EPSG:32611, transform (243350, 100, 0, 4508550, 0, −100), float32, nodata NaN — identical |
| recompute `base ∧ d_cat > {0,1,2,20}` | 44,090 / 40,199 / 37,654 / 18,524 — all ladder claims reproduced from bytes |
| **rung identity** | re-derived B=1 mask ≡ published `gems28-h27-4-r1-solo-d2-8`; re-derived B=2 mask ≡ `gems32-h33-2-b2` — pixel-for-pixel |
| subset chain | our 18,524 ⊆ B=2 ⊆ B=1 ⊆ base, 0 violations; also ⊆ GEMSDOE30 d28-poisson and h32-1-prethin |
| uniqueness | vs 10 sibling rasters: max Jaccard 0.4920 (vs the superset 0.2778 artifact), next 0.4608; byte-unique to all |
| `python3 src/make_submission.py` | rebuilds `notes/results.json` and the GeoTIFF **byte-identically** (sha256 `0d8ba64c…`, 1,552,154 bytes) |
| `python3 src/gems47_verify_submission.py` | 19/19 PASS with reference data present |
| fit-space of (T, N_g) | varies with loss space; modelled score moves 0.34905–0.34925; conformal q exact at 0.000755; recorded floor 0.34837 inside the band (disclosed in `notes/SUBMISSION_NOTE.md` §3) |

Corrections made this pass: README status sha (`32c76c92…` was the superseded `nodata=None` variant; the
live file is `0d8ba64c…`); `SUBMISSION_NOTE` nodata sentence said "`None`" (text not synced with the
rebuild — the raster has carried NaN since the rebuild and the table in the same file said so).
`docs/review-log.md` above describes the pre-submission state of a parallel session ("gate closed, no
TIFF") and is kept as a historical record; this addendum supersedes its status section.

Network reality for future sessions (verified, not assumed): `www.dropbox.com`, `gdr.openei.org`, and
`www.sciencebase.gov` are **unreachable from this sandbox** (curl exit 35 / empty reply), while
`api.github.com` works. All external data must therefore be acquired through GitHub-hosted mirrors,
e.g. `buffedlizard55-lab/GEMSDOE24`: `data/bridge/{labels,existing_faults,sample_submission}.tif` and
`data/external/{geodawn_rad_u8.tif (26.6 MB), geodawn_extensions_u8.tif (27.1 MB),
lidar_scarp_features_u8.tif (36.9 MB), gdr_qfaults_traces.csv, derived_sgmc_faults_100m_u8.tif,
2m_temperature_probe_INGENIOUS_regional_data.zip, paleo_geothermal_regional.zip}` — the full input
stack for hypotheses H1–H5 is fetchable here without any new external source.
