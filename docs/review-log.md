# Three-pass review and correction history

## C1 pass 1 — complete implementation and verify

- Five geological hypotheses ranked/preregistered before implementation; protocol and first tested screen
  committed at cc14ad84fbace93bdd0c2a7bc8b520170e082bb3 before fitting/scoring.
- All 23 pinned mirrors restored and verified; exact grid checks; three fixed HGB controls/features;
  training-only labels, deterministic guarded roles, same mass and all five spacings.
- Synthetic step/channel/slope, label-isolation, rational-rank, sparse-DTI and empty-truth tests executed.
- Full fit/inference/selection/calibration/test completed. No competition upload.

## C1 pass 2 — audit bugs, assumptions, edge cases; fix

- Found spacing-loop overwrite: pre-test lock 2.8px versus final erroneous 5.8px. Preserved and retracted
  first run; committed correction 7aa938e before rerun; asserted lock/selection again in exporter.
  Every trained field and full spacing history is byte-identical. No model/feature/seed/split/grid tuning.
- Corrected empty-truth EDT phantom credit, tensor half-angle/XY geometry, zero-DTI marginal rule,
  portable crossfit reference, skipped-large verification, failure receipts and legacy data paths.
- Strict interior input rejection before float32; atomic no-overwrite TIFF; one self-contained mask;
  actual serialized reopen and deterministic one-TIFF ZIP. Original range cause/portal acceptance unknown.
- Retired LATI builders require explicit educational opt-in, write ignored cache, never delete or replace
  the current public download. Fitted hidden mass and universal-ceiling claims withdrawn.
- Reviewed all-score/fold coverage: zero calibration results retained; all floors zero; 11/22 wins;
  candidate pooled loses to ordinary terrain. Slight mean gain is not cherry-picked into promotion.

## C1 pass 3 — original brief, scientific scope, release, CI

- New research TIFF/ZIP, actual pixel/hash/grid/mask/range checks and 561 bounded historical comparisons.
  No exact match, max Jaccard .0406165, 54 public inventories; 3 non-comparable objects explained.
- Downloads precede the large introduction on both home and summary; confidence/floor adjacent to spacing.
  Root/deployed/nested HTML, local assets and JSON receipts checked inside docs-only Pages artifact.
  Archived pages get a warning and repaired links, not current recommendations.
- CI now collects all new function tests, excludes only explicitly data-dependent grid tests, and reopens
  the actual new TIFF. Initial expanded-CI data-path failure was reproduced/fixed; later Tests workflow green.
- Source feed failures preserve last observation. DrivenData Terms prohibit robot/spider access: no written
  permission recorded, so automatic DrivenData traffic is disabled. Permitted official/owner feed remains
  scheduled; no fake live leaderboard. Source-policy tests prevent accidental requests.
- Official GDR trace/paleogeothermal bytes + coverage verified on GitHub-hosted runner; authenticated core
  data and raw 1 m DEM CSV/tiles remain unavailable. API-readable neutral receipts avoid inaccessible
  redirect-host artifact logs; neutral/green workflow does not imply every source download succeeded.
- Structured standing brief, available score identifiers/history and all source URLs preserved in README.
  Missing original verbatim chat wording is explicitly not fabricated. Winning goal remains unmet.

## Separate H47-QC screen — three-pass review

1. **Implement and verify:** four new geological hypotheses were ranked in [`hypotheses-round2-20261006.md`](hypotheses-round2-20261006.md) and the H47-QC protocol frozen in [`preregistered-h47qc-20261006.md`](preregistered-h47qc-20261006.md) before implementation. The candidate-building API does not read catalogue labels. The 5,000-pixel, 6 px / 600 m run and its inputs, split, score history and format checks are recorded in [`h47qc-screen-20261006.json`](h47qc-screen-20261006.json).
2. **Review bugs, assumptions and edge cases:** checked the held-out comparison against the matched geochemistry-only, random, H47-B-persistence and single-scale magnetic baselines. The candidate's pooled test DTI 0.0131689425 loses to the geochemistry-only 0.0141948068 ablation. The nominal split-conformal level is 6/7 (85.7%) only under unverified block-score exchangeability; the assumption-conditional lower-bound estimate is zero, not a private or map-wide performance guarantee.
3. **Re-check the brief, science and release:** the binary float32 artifact is finite and in [0,1] on the specified 100 m EPSG:32611 grid, but valid format is not scientific promotion or portal acceptance. The bounded audit found no exact positive-mask match in its inspected inventory; it does not prove global uniqueness. The local geochemistry table is a derived mirror, water-type/disequilibrium and exact field definitions remain limitations, and the labels are only a public-catalogue proxy. **H47-QC is a failed research screen: do not upload it or spend a slot.** Its TIFF hash and identification note are published in `docs/downloads/`.

Exact final test/check/PR/merge timestamps are recorded in `data/three-pass-review.json` and GitHub receipts.

## H47-B footprint audit and current-main reconciliation — three focused passes

### Pass 1 — preserve current main and identify the supplemental artifact

- Resolved the merge with `origin/main` by retaining the newer C1, H47-QC, H48, Session 3, source-feed, current-submission and site content as the baseline; no current C1/H47-QC artifact or gate was replaced.
- Kept the unique H47-B single-scale NaN-outside TIFF and its all-finite encoding diagnostic separate from the main C1 download. Added an H47-B audit page and artifact-register entries rather than reviving an older H47-B homepage.
- Checked both exact TIFF paths, sizes and SHA-256 values against the branch evidence before publishing links.

### Pass 2 — recheck science, format assumptions and claims

- Rechecked H47-B's negative locked-test comparison: pooled catalogue-mask proxy DTI 0.02563947 versus 0.02755344 for H47-B cross-scale and 0.03715911 for fixed-seed random. No leaderboard or missing-fault claim is made.
- Rechecked nominal rank 6/6 = 6/7 ≈ 85.7% conformal arithmetic, its unverified block-score exchangeability assumption, two empty calibration blocks, and the assumption-conditional lower-bound estimate of 0.0. No private/global guarantee follows.
- Reconciled the explicit mirrored sample-template mask with the feature-derived mask: 5,167,373 versus 5,165,852 valid cells, 1,540 feature-valid cells outside, 3,061 sample/label cells invalid in features. The official footprint and historical portal-error cause remain unknown; the finite diagnostic is not asserted to explain the old error.

### Pass 3 — integration and final release checks

- Added cross-links from current homepage, executive summary, irregularity page, README and complete artifact register while keeping C1 as the prominent current download.
- Synchronized the machine-readable irregularity registry copies and added regression coverage for current-download separation, H47-B links and the exact artifact digest.
- Final post-current-main-merge local run: pytest **242 passed, 1 skipped, 2 subtests passed**; the CI exclusion profile has **230 passed, 13 deselected, 2 subtests passed**; unittest **81 tests passed**; Ruff **PASS**. Site-link/asset checks are included in the suite. JSON/CSV parsing, both irregularity registry copies, and the two H47-B manifest hashes **PASS** (21 manifest rows). One upstream Rasterio `PendingDeprecationWarning` remains.
- Reopened the exact H47-B TIFF: explicit mirrored sample-template mask **PASS** (5,167,373 valid cells, 0 invalid inside, 0 non-NaN outside, SHA matches); feature-derived mask **fails as expected** (1,540 invalid inside, 3,061 non-NaN outside). This reproduces the local discrepancy, not organizer acceptance. `git diff --cached origin/main --check` **PASS**. No competition slot was used.
- Remote branch CI and PR state are pending observation; this review log must not describe them as green or merged until GitHub reports those results.

## Older corrections still in force

Retired annulus .34912 / .34837 private floor is withdrawn; adaptive nested history is not exchangeable
calibration, and deleting a prior mask is not a new detector. The earlier .3345 rank-1 board is superseded by
the dated .3774 observation; on 7 October 2026, 0.3195 was rank 7. H33 .2778 filename/hash association is
unverified, not an organizer receipt. Three λ-scaling score observations do not establish upload or slot use;
no λ-probe recommendation, upload cost, or “free diagnostic” claim remains. The 6 October note that quota was
unknown is superseded: the 7 October DOE/NLR rules review states up to three scoring/feedback submissions per
week and one final selected file for the competition's rounds. Account-specific eligibility, used/remaining
opportunities, and selection state still require the authenticated portal.


### Official-source receipt update after additive reconciliation

Runner 37536709561 verified all three public archives and coverage. USGS national traces: 82,841
footprint cells (58,800 exact-catalogue); GDR traces: 82,871 (58,876 exact-catalogue); paleo point
cells: 244. These all_touched pixel counts are not fault counts or expert-new truth. The earlier
USGS expansion-budget issue was fixed by reading geometry only, not the 203MB attribute table or
GDB. No vector trained C1. Sources, hashes and runner attestation are in the deployed JSON.


## Repository review continuation — 6 October 2026 (local)

- Corrected the published outside-null/NaN requirement across current guidance: unmasked all-finite zero-outside H47-B single-scale, H47-GSA, H47-MAXCOV, H47-QC, H48-APEX/repack, and Session-3 artifacts are research-only and fail that explicit check. The H48 research writer now emits NaN outside in future outputs; this follows an owner-supplied mirror convention only and does not establish portal acceptance.
- Kept H33-2-B2 / participant DTI 0.2778 unverified and dependent fits conditional; renamed H48 report fields to assumption-conditional lower bounds and marked outputs not slot-eligible. Updated ratio and quota/λ-observation caveats.
- Disabled the old score-ceiling runner and legacy site/submission renderers that could reproduce withdrawn assumptions. All legacy LATI build entry points now fail closed before cache reads or writes.
- Validation did not restore data, rerun H47-B, upload, spend a slot, or run a λ-probe. Final test/lint/PR status is reported in the current PR record, not inherited from prior counts.

## Current-main documentation reconciliation — 7 October 2026

- Fetched latest `main` at `c0180ed` (PR #26) and fast-forwarded the designated review branch from `ab160ae` before PR preparation. The H60–H64 round is the current repository state. Kept H47-C1's failed promotion gate explicitly closed; H60 is a separate locally promoted candidate.
- Reopened the exact H60 TIFFs with Rasterio 1.4.4. The all-finite TIFF (`4ee074…`) has all 12,279,160 cells finite in [0,1] but writes zeros outside and does not meet the published null/NaN-outside wording. The NaN-outside TIFF (`d75ab9…`) has 5,167,373 finite valid-mask cells, 7,111,787 outside NaNs and 37,654 positive cells; it matches that wording on local read-back. Neither encoding has organizer acceptance; prior rejected bytes/parser receipt remain unavailable. Added `docs/data/h60-encoding-audit.json` and linked the more cautious status through the submission guidance.
- Corrected current user-facing submission pages: distinguish scientific promotion from format/portal acceptance; retire the stale H47-C1/H50 current-file recommendations; mark the all-finite H60 ZIP as an audit bundle, not an upload bundle; preserve the explicit no-upload/no-slot instruction.
- Reconciled the rules statement to the official DOE/NLR PDF: up to three scoring/feedback submissions per week and one final selected file for the rounds. The entrant's eligibility, used/remaining weekly opportunities and portal selection state remain account-specific and unverified.
- Corrected the dated leaderboard summary: rank 1 was 0.3774 on the saved 7 October 2026 observation; 0.3195 was rank 7. Scores remain participant-level and are not mapped to TIFF hashes.
- Post-rebase local validation: `pytest tests -q` → 297 passed, 21 skipped, 13 subtests passed; `ruff check .` clean; all 151 repository JSON files parsed. The nine Markdown site pages were rendered with `build_site_s3.py`, and local HTML-link/receipt tests passed. GitHub CI, PR, and merge outcomes remain pending.
