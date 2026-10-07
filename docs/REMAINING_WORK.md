---
title: Remaining work and limitations
layout: default
nav_order: 7
---

# Remaining work and limitations

> **Current decision: H49 is a downloadable research artifact, not an authorized competition submission.** It did not clear the paired spatial-holdout improvement gate. Maximize P(Win): preserve the weekly slot until a prospectively specified candidate beats the current holdout best. Own the Outcome: keep the exact bytes, caveats, failures and source records reviewable.

## Current H49 state

The file `gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif` is 409,124 bytes, SHA-256 `f2cec409ce3bec5a2805f1fab9a12ab7f72394f8be79cc365134ce43708c6060`, with 37,612 positive pixels. It is a one-band float32 GeoTIFF on the 3292 × 3730 EPSG:32611, 100 m official grid. Its self-contained internal mask matches the 5,167,373-cell footprint, and masked reads are null exactly outside. All 19 gating format/read-back checks pass; the whole-grid raw `[0,1]` check is reported separately as an informational flag. This is format validation for these bytes, not scientific validation or organizer acceptance.

The pinned visible-public-inventory audit covered 54 repositories and 565 comparisons (555 inventory blobs plus 10 local-history rasters), with zero exact mask/value matches and maximum Jaccard 0.292575. Three inventory entries were excluded from direct pixel comparison, and no repository inventory fetch failed. The audit is bounded: inaccessible, unpublished, deleted, later-published and otherwise non-inventoried files are outside its scope. Do not claim global uniqueness.

The nominal fixed-arm split-conformal order statistic is 0.03184 at 90% for spacing 2.8 px / 280 m. Its unit is one 8×8 spatial block; `n=19`, `k=18`; the target is block DTI on public USGS SGMC traces more than 300 m from the given catalogue. Validity assumes exchangeable blocks and a rule fixed independently of calibration outcomes. SGMC includes non-fault contacts, geological-block exchangeability is unverified, and the shipped mean-maximizing rule was amended after results. This is not a guarantee for the full adaptive procedure, private labels, paired improvement or leaderboard score.

The H49 mean-rule arm has a positive descriptive public-proxy mean but its 90% split-conformal lower bounds on paired improvement over the H33-labelled reference are negative for both selection and calibration halves. The saved floor-rule arm also fails the paired-improvement criterion. **Do not upload H49 or spend a weekly slot on it.** No competition upload, organizer score receipt or acceptance receipt exists.

## GitHub publication status

The fixed session branch `arena/24b6e85a-gemsdoe47` has been reconciled with `origin/main` at `525dab76f10facca1382872d65b15fded04697ae`. PR [#21](https://github.com/buffedlizard55-lab/GEMSDOE47/pull/21) was opened from that branch. Both GitHub Tests runs passed on the initially opened head; the PR page is authoritative for checks on later commits and the final merge status/commit.

## Remaining scientific work, in priority order

1. **Find a genuinely stronger candidate.** Write a prospective protocol before scoring. Use a fresh spatially blocked holdout not reused from the 39 H49 blocks, matched-mass and shifted/random controls, and a positive paired-improvement lower-bound criterion. Keep the slot gate closed on ties, unstable folds, failed controls or an unsupported/negative lower bound.
2. **Verify higher-resolution data before depending on it.** The ranked queue proposes a conditional USGS 3DEP / GeoDAWN H50 LiDAR idea, but exact 1 m files, license, bytes and footprint coverage are not verified in this sandbox. Do not treat H50 as viable until an official free source is actually obtained and checked.
3. **Resolve H33 score attribution if an organizer receipt becomes available.** The H33/H27 mask relationship is verified from pinned files, but no receipt maps 0.2778 to the H33 hash; its pinned owner README says unscored and calls 0.2747 a projection. Reduced off-target mass is a plausible mechanism, not an established causal explanation.
4. **Refresh the old inversion only if its exact reference TIFFs are restored.** `scripts/run_inversion.py` cannot produce a new JSON because `data/reference/` lacks required inputs. Existing score-conditioned values remain conditional owner-label arithmetic, not organizer observations.
5. **Retain the research record and re-run checks after any artifact change.** The exact TIFF hash, format receipt, conformal certificate, public audit, source references, ranked hypotheses and review checklist are linked from `README.md` and the Pages site. Any byte change requires rebuilding the receipt and both audits.

## Non-claims and scope boundaries

- The public SGMC/PM0200 proxy is not the hidden competition target; SGMC contains non-fault contacts. No public-proxy DTI is a leaderboard forecast.
- A nominal fixed-arm split-conformal statistic is conditional on exchangeability and prospective rule fixation. Re-partitions reusing the same blocks are sensitivity diagnostics, not independent validation samples.
- A file-format pass does not establish scientific improvement, bounded uniqueness outside the recorded inventory, portal acceptance or an organizer score.
- The H33 filename-to-score mapping and all competition upload/score receipts remain unresolved in this repository.
- `README.md` preserves the complete available structured brief and discloses that the original verbatim chat transcript was not present in the checkout; unavailable wording has not been reconstructed.
