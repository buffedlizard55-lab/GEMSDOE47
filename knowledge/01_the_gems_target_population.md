# The GEMS target population — what the hidden labels actually are

Reusable research base. Everything here is sourced; see `registry/sources.json`
for the `verified_this_session` flag on each item.

## 1. The task

Find **newly identified faults indicative of geothermal resources** in the Nevada
Great Basin, on a 100 m grid, as a per-pixel probability in `[0, 1]`. The supplied
labels are faults from the **USGS Quaternary fault compilation** and **INGENIOUS**.
The scoring targets faults that are **not** in those compilations.

## 2. The definition of "new fault" — the single most actionable fact

> "'new fault' means 'any fault pixel not already captured by USGS/INGENIOUS' and
> **can include newly mapped geometry of an existing fault system**."
> — DrivenData staff (`chrisk-dd`), community thread 11536, 2026-09-23
> https://community.drivendata.org/t/where-do-you-draw-the-line/11536

Two consequences that dominate every design decision:

1. The target population is **off-catalogue**. Pixels already in USGS/INGENIOUS
   are not "new faults" no matter how confident the detection.
2. But "off-catalogue" is **not** "far from the catalogue". Newly mapped geometry
   *of an existing system* — trace continuations past mapped endpoints, splays,
   relay ramps, parallel strands, stepovers — sits immediately adjacent to mapped
   traces. The target is a **halo that is adjacent to but not on** the catalogue.

## 3. Masking — staff wording and limits of the empirical clue

> "Pixels corresponding to known USGS/INGENIOUS faults are masked / excluded from
> evaluation, so they do not count towards penalty terms. ... for scoring purposes
> it should not matter whether these known faults are included with predictions or
> not."
> — DrivenData staff (`chrisk-dd`), thread 11516, 2026-09-16
> https://community.drivendata.org/t/scoring-clarification-masked-pixels-and-re-evaluation/11516

**Masked-catalogue prediction mass should earn no credit and should be irrelevant to scoring if the organizer's mask is applied to both prediction and truth.** If only the false-positive penalty were masked, those predictions would instead cost α per unit; that alternative must not be silently assumed.

A byte comparison of the recovered mirrors shows that `8GEMSDOE_Hedge-v2_submission.tif` is identical
to `gemsdoe-ens12-adopted-7f00890a.tif` off the catalogue and adds catalogue pixels at p = 1. The
associated owner-reported scores are both 0.1563 to four decimals, but no organizer receipt binds
those hashes to that return. The staff statement and comparison are **consistent** with known pixels
being excluded from both sums; they do not verify the portal implementation.

**Local working assumption only:** `mask_mode="zero"` removes known cells from both sums. Under that
rule, deleting only masked predictions cannot improve DTI. Since the 0.2778 participant row is not
mapped to H33-2-B2 by an organizer receipt, do not claim that its alleged catalogue deletion caused the
score change.

### Conditional consequence for catalogue-based holdouts

If an evaluator masks the known catalogue from both truth and prediction, a holdout whose truth is
only the catalogue has empty `truth & evaluated`, `K = 0`, and DTI ≡ 0 for every candidate. This is a
conditional property of that interpretation, not proof of the portal's internals. Do not infer scorer
behavior from owner-reported nonzero values on local catalogue frames; those mappings are not
organizer-authenticated. Such a frame is not used for candidate selection here. (IR-47-005.)

## 4. The grid

| Quantity | Value |
|---|---|
| Shape | 3730 × 3292 = 12,279,160 px |
| CRS | EPSG:32611 (UTM 11N) |
| Geotransform | (100.0, 0.0, 243350.0, 0.0, −100.0, 4508550.0) |
| Bounds (m) | 243350 / 4135550 / 572550 / 4508550 |
| Resolution | 100 m |
| Footprint (`labels != −1`) | 5,167,373 px — identical to `isfinite(sample_submission)` |
| Catalogue-marked labels (`labels == 1`) | 60,988 px; staff describes these as masked/excluded |
| **Local proxy scoring domain** (footprint ∧ ¬catalogue) | **5,106,385 px**; not a verified private scorer mask |
| `labels.tif` | int8, nodata −1 |
| `sample_submission.tif` | float32, 1 band, nodata nan, values {0,1}, **60,988 ones — all on `labels==1`, so it is not all-zero** |
| `training_features.tif` | float32, 19 bands, nodata **−3.4028234663852886e+38** |

**The nodata sentinel is not NaN.** `np.isfinite()` returns True for the float32
minimum, so any statistic computed without special-casing it treats −3.4e38 as a
measurement. All 19 bands carry it; 3,061 pixels inside the footprint do too.
(IR-47-001.)

### The 19 supplied bands, in file order

`mag_anom`, `rtp`, `tmi_hg`, `geod_2ndinv`, `iso_grav_anom_slope`, `tc`,
`geod_shearrate`, `geod_dilaterate`, `tmi_vg`, `deq_n100a15`, `iso_grav_anom_vg`,
`det_elev`, `iso_grav_anom`, `tmi`, `depth_to_base_surf`, `ieq_n100a15`,
`cond_surf`, `iso_grav_anom_hg`, `det_elev_slope`.

Read back from the TIFF descriptions rather than from documentation. Per-band
valid counts and ranges: `evidence/training_band_stats.json`.

## 5. What was NOT retrieved

The staff answer in thread **11527** ("How were the new test faults identified?
Data sources and fault types") did not render — the page shows a collapsed post
list and only the two questions plus two non-staff replies came through. That
answer would state directly which data the NLR/USGS experts used, and is the
single most valuable missing fact in this competition. Retry via the last-post URL
(`…/11527/10`) or the print view (`…/11527?print=true`). Nothing was guessed at in
its place. (IR-47-006.)

## 6. The organiser's reference solution does not optimise the metric

`drivendataorg/gems-prize-reference-solution` (U-Net + Monte-Carlo CV benchmark,
John Lipor, PSU) trains with
`smp.losses.TverskyLoss(alpha=0.2, beta=0.8, mode="binary")` — a **patch-level,
unweighted, undistanced** Tversky loss. The notebook contains **no DTI scorer at
all**: no `k(d) = max(1 − d/R, 0)`, no 300 m buffer, no global max-over-neighbours
reduction. Patch-level Tversky and global distance-weighted Tversky have different
optima. (IR-47-004.)

Config, for reuse: `MC=5`, `patch_size=128`, `test_proportion=0.5`,
`batch_size=32`, `epochs=5`, `init_lr=1e-4`, `smp.Unet(resnet18, imagenet)`,
`AdamW`, augmentations `RandomResizedCrop(scale 0.5–1.0, ratio 0.75–1.33,
bilinear) + HFlip + VFlip + RandomRotation(30)`.

## 7. Derived layers available in this project's mirror

| Layer | Bands | Notes |
|---|---|---|
| `lidar_scarp_features_u8.tif` | `ex_max, ex_mean, step_max, lapneg_max, lappos_max, downface_max, upface_max, cross_max, relief, coh100, strike, valid` | sibling-derived 100 m layers described as LiDAR scarp features; claimed 1 m source provenance and exact tile coverage/acquisition were not independently verified (IR-47-012) |
| `geodawn_rad_u8.tif` | `K, Th, U, TC` | GeoDAWN radiometrics |
| `geodawn_extensions_u8.tif` | `ThK, UK, UTh, TMI_up150` | ratios + **150 m upward-continued TMI**; persistence was screened as H47-B and not promoted |
| `derived_sgmc_faults_100m_u8.tif` | 1 | 83,593 px, of which **62,122 px** lie >300 m off the given catalogue |
| `gdr_qfaults_traces.csv` | — | 1,126 traces with slip rate, recency, dip, slip sense, length, centroids |
| `gdr_wellspring_in_footprint.csv` | — | 27,092 spring-chemistry / water-well points with temperature and three geothermometers |
| `gdr_volcanic_vents_in_footprint.csv` | — | 21 vents (too few to carry signal) |
