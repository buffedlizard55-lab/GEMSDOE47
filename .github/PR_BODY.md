## Summary

This PR updates GEMSDOE47's current research artifact, evidence report, Pages site, and review records for H49. It does **not** authorize a competition submission. The weekly-slot gate stays closed because the shipped mean-rule selection was amended after results, its prospective timing cannot be independently audited, and the 90% split-conformal lower bounds on paired improvement over the H33-labelled reference are negative for both candidate arms.

**Research TIFF:** `gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif`
**SHA-256:** `f2cec409ce3bec5a2805f1fab9a12ab7f72394f8be79cc365134ce43708c6060`
**Size / positives:** 409,124 bytes / 37,612 positive cells
**Status:** research-only; no DrivenData upload, score receipt, or acceptance receipt exists.

The top-level Pages download, single-TIFF ZIP, executive summary, unique artifact name, and short portal note remain obvious for research review, with explicit instructions not to spend a slot on H49.

## Evidence and changes

- Rebuilt and read back the exact TIFF bytes on the official 3292 × 3730 EPSG:32611 100 m grid. The internal mask matches all 5,167,373 footprint cells; masked reads are null exactly outside; raw cells are finite in `[0,1]`; no nodata tag or sidecar. **19/19 gating checks pass**; the whole-grid range check is separately labeled informational.
- Published a pinned public-inventory audit over 54 visible repositories: 555 inventory blobs plus 10 local-history rasters, zero exact mask/value matches, maximum Jaccard 0.292575. Three entries were excluded from direct comparison and no repository inventory fetch failed. This is bounded scope, not proof of global uniqueness or geological discovery.
- Corrected the H49-B paired contrast to the candidate-minus-reference direction and added a regression test: R7 polarity minus R2 topographic field has selection mean `+0.006423` and 90% lower bound `−0.009412`; calibration mean `+0.002483` and lower bound `−0.016209`. Both lower bounds remain negative.
- Reported the nominal 90% fixed-arm split-conformal statistic beside spacing `2.8 px / 280 m`: value `0.03184`, one 8×8 spatial block as the unit, `n=19`, `k=18`, target = public SGMC off-catalogue block DTI. Exchangeability and independent prospective rule fixation are assumptions; SGMC includes non-fault contacts; the final mean-rule amendment means this is not a guarantee for the complete adaptive procedure, paired improvement, private labels, or a leaderboard score.
- Corrected H33 reporting: the pinned H33 and H27 masks have an exact subset relation, but no organizer receipt maps 0.2778 to the H33 TIFF hash; the pinned owner README calls H33 unscored and 0.2747 a projection. Pruning is a plausible mechanism, not a proven causal score explanation.
- Preserved four ranked future geological hypotheses, their layers/signatures, novelty, qualitative effect/cost and source-access status. H50 LiDAR remains conditional until actual free official files, licensing and coverage are verified.
- Updated README with the complete available structured brief and disclosed that the original verbatim transcript was not present in the checkout. Updated the current requirements, remaining-work, method, H33/H49 evidence, and next-session records; retired the misleading historical Pages publisher behind an explicit overwrite opt-in.

## Validation

- `.venv/bin/python -m pytest tests -q`: **238 passed, 16 data-dependent tests skipped** because the restored competition rasters are not present in this clean checkout; 1 Rasterio pending-deprecation warning, 2 subtests passed.
- `.venv/bin/python -m ruff check .`: clean.
- `.venv/bin/python scripts/update_site_h49.py --check`: 0 problems.
- `.venv/bin/python scripts/build_site_s3.py --check`: tracked docs are byte-identical to `main` outside declared session-owned pages and H49 marker regions.
- `git diff --check`: clean.

## Scope and remaining limitations

No organizer score or acceptance is claimed. H49's SGMC/PM0200 measurements are public-proxy results, not a private-target forecast. Spatial-block exchangeability and prospective rule fixation remain assumptions; repeated partitions reuse the same blocks. The public uniqueness audit cannot cover inaccessible, unpublished, deleted, later-published, or unindexed work. The H33 score-to-file mapping remains unresolved. A future candidate needs a prospectively locked protocol and a fresh spatially blocked holdout that beats the current holdout best, with matched-mass and shifted/random controls, before any slot is considered.
