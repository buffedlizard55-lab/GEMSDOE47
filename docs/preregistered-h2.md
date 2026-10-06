# H47-B preregistration — cross-scale magnetic-edge persistence

**Frozen:** 2026-10-06 UTC, before scoring any H47-B configuration. **Purpose:** diagnostic resemblance screening against known-fault catalogue masks only—not evaluation of the competition's off-catalogue missing-fault target. No slot is authorized by this protocol.

**Post-score interpretation clarification (2026-10-06):** The original frozen protocol file at scoring had SHA-256 `4cb65d953e575d942f0b1db8d258a36fbc2c8caea32e3409da127d36eaa0c6c6`. After scoring, source review clarified that `labels.tif == 1` marks known USGS/INGENIOUS catalogue faults masked from the organizer's actual off-catalogue target (see the official [competition description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [staff masking clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)). This corrects the target interpretation only; the input bytes, label values, transforms, split, scoring, or results were not changed. All reported DTI and conformal results are diagnostic resemblance-proxy results, not validation or coverage for missing-fault predictions. The current clarifying document hash is recorded separately in the machine-readable screen report.

## Data and provenance

All files are from the group-hosted `buffedlizard55-lab/GEMSDOE24` GitHub mirror, not a direct authenticated DrivenData download. The public DrivenData data page redirects unauthenticated requests to login. The hashes below pin the exact bytes used; a mirror hash is not independent organizer authentication.

| file | SHA-256 | use |
|---|---|---|
| `work/external/geodawn_extensions_u8.tif` | `a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b` | Feature only; channel 4 is quantized `TMI_up150` |
| `work/bridge/labels.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | Reference labels for diagnostic proxy only (`1` known catalogue trace, `0` background, `-1` nodata); not the hidden missing-fault target |
| `work/bridge/sample_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | Output grid and footprint template |
| `work/external/acquisition_block_id_100m.tif` | `2c0785c4b3ec46c734d1be7a7aedbb3e816201100ab358033a3af074418c894a` | Descriptive subgroup audit only; never a model input |

The common grid is 3292 × 3730, EPSG:32611, 100 m pixels, GDAL-order geotransform `(243350, 100, 0, 4508550, 0, -100)`. The mirror manifest says band 4 is a contractor upward-continuation of total magnetic intensity to a 150 m grid. It also says the `uint8` values 1–255 are rank-encoded between per-channel 1st and 99th percentiles and 0 is nodata. **They are not physical magnetic units.** This protocol does not claim to implement the published tilt-depth method.

## Frozen transform and comparators

1. Convert valid band-4 bytes to a rank-scaled float `q = (byte - 1) / 254`; retain the band-4 valid mask. Do not use labels or the acquisition-block raster to build a score.
2. For each Gaussian scale `σ ∈ {2, 4, 8}` pixels (200, 400, 800 m), compute a normalized masked Gaussian smooth of `q`. Compute centered finite-difference `gx`, `gy`, edge magnitude `g = hypot(gx, gy)`, and axial normal orientation `θ = atan2(gy, gx)`. Exclude positions with less than 99% Gaussian support.
3. On the common supported footprint, divide each scale's `g` by its 99th percentile and clip to `[0, 1]`. Set persistence to `min(g₂, g₄, g₈)` and axial agreement to the minimum pairwise `abs(cos(θᵢ - θⱼ))`. The H47-B score is their product. The comparator is a single-scale `σ=4` edge-magnitude score, normalized by its own 99th percentile on that same support.
4. For each score field, build a deterministic greedy point mask in descending score order, with minimum Euclidean separation `d ∈ {2, 3, 4, 5, 6}` grid pixels. Every candidate must contain exactly **18,524** positive pixels across the template footprint; if any spacing cannot reach that mass, stop and report the failure rather than silently compare different masses. All other in-footprint pixels are 0; outside the template footprint is NaN.
5. Build one uniform-random control using seed `47062026`, the same footprint, mass, and spacing as the selected H47-B candidate. It is a sanity control, not a tuned competitor.

## Spatial evaluation, selection, and promotion rule

- Divide the raster into 4 × 4 equal rectangular spatial blocks. In each block, inset both prediction and catalogue arrays by a 3-pixel/300 m guard on every edge, then run the repository's exact DTI implementation with its 300 m/3-pixel kernel on that disjoint inner crop. The `catalogue` pixels are `labels.tif == 1`, the known-fault catalogue mask; the organizer's actual evaluation masks these pixels from the off-catalogue target. Thus all reported local DTI values are resemblance-proxy diagnostics, not missing-fault target scores. The guard omits cross-boundary matches and prevents pixels from being counted in two folds. Pool `TPw`, `FPw`, and `Ng` over disjoint block cores using the exact DTI identity. Blocks remain spatially correlated; this scoring guard does not establish statistical independence.
- Assign block IDs before reading any DTI results by `(row + column) mod 3`: **selection** = `{1,4,7,10,13}`; **calibration** = `{0,3,6,9,12,15}`; **locked test** = `{2,5,8,11,14}` (IDs are row-major from 0 at the upper-left). Keep the assignment fixed.
- Select H47-B's spacing as the one with the highest mean block DTI on the five selection blocks; break exact ties toward the larger spacing. Select the single-scale comparator's spacing by the same rule. Do not re-tune on calibration or test blocks.
- Report per-block DTI and positive-prediction count, mean block DTI, and pooled test DTI. **Promotion gate:** H47-B at its selection-picked spacing must beat the selection-picked single-scale comparator and the fixed-seed random control on the locked test blocks by pooled DTI. A tie, lower result, insufficient labels, or any mass mismatch closes the gate. No leaderboard score is imputed from this public-label screen.
- Retain a separate per-acquisition-block breakdown as descriptive heterogeneity only; it cannot change the selected spacing or promotion decision.

## Split-conformal floor

For the selected H47-B spacing, let `μ` be its mean DTI on selection blocks. On the six calibration blocks, compute one-sided residuals `rᵢ = μ − DTIᵢ`; sort them and use rank `ceil((n+1)(1−α))` with `n=6`, `α=1/7`. The lower bound is `clip(μ − q, 0, 1)`. At this sample size the largest nontrivial nominal marginal level is **6/7 = 85.7%**. Report the raw residuals, rank, quantile and clipped floor.

This is a finite-sample lower prediction bound for a future comparable block's DTI against the same known-catalogue-mask proxy **only if** selection/calibration/future proxy-block scores are exchangeable. Spatial autocorrelation, acquisition shifts and geology make that assumption doubtful and unverified. Therefore the reported level is explicitly *assumption-conditional*, not a proven guarantee for every map cell, the hidden missing-fault target, the official private-label score, or the DrivenData leaderboard. If block scores are degenerate or the floor is zero, the hypothesis does not satisfy the promotion gate.

## Known limitations before results

- A single upward-continued, rank-quantized TMI channel cannot provide a physically calibrated vertical derivative, reduced-to-pole tilt angle, source depth, or independent multi-height persistence.
- `labels.tif == 1` marks known USGS/INGENIOUS catalogue traces that the organizer masks from actual off-catalogue evaluation; the local DTI alignment is a resemblance proxy only, not validation of hidden missing-fault predictions.
- No official organizer feature stack or exact rejected TIFF bytes are available in this checkout.
- A successful public holdout screen would justify only a candidate for separate review; it would not prove private-set improvement or certify the reported 0.2778 artifact mapping.
