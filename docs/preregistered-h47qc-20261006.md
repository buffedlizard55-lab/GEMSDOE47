# Preregistered screen — H47-QC geothermometer consensus

**Frozen:** 2026-10-06 UTC, before H47-QC code, score surfaces, or DTI results. **Scope:** public-catalogue screening on owner-hosted mirror bytes. This is not an authenticated private-label test and cannot authorize an upload by itself.

## 1. Hypothesis

A spring/well location is more plausible as evidence of a concealed, fault-controlled fluid pathway when (a) at least two mirror-exported reservoir geothermometer estimates are elevated and mutually concordant, (b) its measured outlet water is cooler than the estimated reservoir, and (c) the location is near a co-located, directionally aligned magnetic and gravity edge. The chemistry establishes a geothermal-fluid clue; the edge conjunction is the structural cue. Neither component alone proves a fault, a hidden fault, or a commercially useful geothermal reservoir.

This tests a specific static chemistry-consensus operator. It does not test H47-F's temporal persistence (no date field exists in the available CSV), and it does not treat the CSV's `dist_known_fault_px` as a feature.

## 2. Inputs, provenance, and fixed constants

| Input | SHA-256 | Use |
|---|---|---|
| `.cache/gems_data/external/gdr_wellspring_in_footprint.csv` | `122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea` | Location, water temperature, and the three mirror-exported geothermometer fields only; **never** `dist_known_fault_px` |
| `.cache/gems_data/training_features.tif` | `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` | `rtp` and `iso_grav_anom` for structural edges |
| `.cache/gems_data/labels.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | Evaluation truth only; not read by candidate-field construction |
| `.cache/gems_data/sample_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | Grid/footprint only |
| `.cache/gems_data/external/geodawn_extensions_u8.tif` | `a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b` | Matched-mass H47-B persistence and single-scale comparison only |

The CSV and rasters are hash-pinned owner-hosted mirrors. The CSV manifest attributes the point data to DOE INGENIOUS GDR submission 1391 / DOI 10.15121/1881483 (CC BY 4.0), but these mirror hashes do not authenticate any organizer download. Exact canonical definitions for the three CSV fields were not found in the GDR page's summary; the export labels are used literally and interpretation as reservoir temperatures is provisional.

## 3. Frozen feature construction

### 3.1 Source grouping and quality screen

1. Group CSV rows by Unicode-normalized, stripped, case-folded `name` plus the integer 100 m `row` and `col`. This prevents repeated layer rows at the same named grid location from being counted as independent source points. It does not prove distinct wells or sampling events.
2. For each of `geothermquartz_c`, `geothermchalc_c`, and `geothermcat_c`, retain only finite values in `[0, 300] °C`; use the within-group median for each available method.
3. Require at least two available method medians, a median across methods of at least `80 °C`, and a max-minus-min range across available method medians no larger than `30 °C`.
4. For `temp_c`, retain only finite values in `[-5, 100] °C`; use the within-group median and require one to be present. `temp_c` is treated as measured outlet water temperature based on the mirror column label, not as an authenticated field definition.
5. Define `T_res` as the median retained geothermometer estimate, `spread = max − min`, and `T_out` as the measured outlet median. Define the fixed point weight:

   `w = exp(−spread / 30) × clip((T_res − 80) / 120, 0, 1) × clip((T_res − T_out) / 120, 0, 1)`.

   All terms are in `[0,1]`. Zero-weight groups do not create a source. No chemistry threshold, kernel width, or score coefficient will be tuned on a holdout.
6. Deposit each positive `w` at its row/column. Smooth the weighted source grid with a Gaussian kernel of `σ = 10 px` (1,000 m), `mode="constant"`, `truncate=4`; this makes the source influence exactly zero beyond 40 pixels (4,000 m). Candidate support is that 4 km neighborhood intersected with valid `rtp`/gravity pixels and the template footprint. No catalogue-distance buffer or catalogue mask is used during prediction generation.

### 3.2 Structural edge and interaction

1. Read the named `rtp` and `iso_grav_anom` bands. A cell is valid only if it is in the template footprint and both values exceed the repository's float32-min nodata sentinel threshold (`> −1e30`).
2. For each layer, compute a masked Gaussian smooth with `σ = 2 px`, divide the smoothed value sum by smoothed validity weight, and retain cells with at least 99% Gaussian support. Use centered finite differences to compute gradient vector `(gx, gy)` and magnitude.
3. Normalize each magnitude by its own 99th percentile over the common valid support, clip to `[0,1]`, and calculate axial gradient agreement:

   `A = abs(g_rtp · g_gravity) / (|g_rtp| |g_gravity| + 1e−12)`.

   `E = sqrt(m_rtp × m_gravity) × A`.

   A zero/near-zero edge contributes zero. This is an uncalibrated structural-edge agreement, not a physical-depth inversion.
4. The H47-QC ranking score is `Q = geochem_influence × E` inside candidate support and zero elsewhere. No training labels, catalogue distances, prior submission rasters, or leaderboard-derived coefficients enter `Q`.

### 3.3 Emission operating points

- Fixed budget: **5,000** binary points. Rationale: a sparse, high-confidence detector is being tested; this is deliberately lower than H47-B's 18,524-point operating point. Every comparator will be re-emitted at the same 5,000-point budget, so the principal comparisons are mass matched.
- Spacing sweep: greedy Euclidean minimum separation `d ∈ {2,3,4,5,6}` pixels (200–600 m). Tie order is descending score, then ascending row-major flat index. Every requested mass must be reached; otherwise that configuration fails rather than silently backfilling from outside its support.
- Select H47-QC spacing using **only** the mean per-block DTI on selection blocks; exact ties favor the larger spacing. Do not choose the output by calibration/test DTI.
- One binary `1.0` is emitted at each selected point; all other cells are zero. The output is an uncalibrated normalized mask, not a calibrated probability raster.

## 4. Comparators, blocked evaluation, and decision rule

### Fixed block design

Use the existing preregistered H47-B 4×4 equal rectangular blocks, 3-pixel/300 m guard on every edge, and exact repository DTI implementation. Block IDs are row-major from 0 at upper-left. Roles, unchanged from H47-B:

- Selection: `{1,4,7,10,13}`
- Calibration: `{0,3,6,9,12,15}`
- Locked test: `{2,5,8,11,14}`

The 300 m guards prevent direct overlap of scored block cores; they do **not** prove block independence or exchangeability. Truth pixels are the `labels.tif == 1` public catalogue mask. This is a proxy screen against known catalogue geometry, not the challenge's private newly mapped fault target. Blocks with no public catalogue truth score zero; they are not dropped after seeing results.

### Frozen comparators

At the same fixed 5,000-point budget, run the same `{2,3,4,5,6}` spacing sweep for:

1. H47-B cross-scale `TMI_up150` magnetic-edge persistence (recomputed from its pinned mirror input);
2. its single-scale magnetic-edge baseline;
3. the univariate GDR geothermometer-influence field (`geochem_influence`, ablation);
4. the magnetic/gravity structural-edge field `E` (ablation);
5. a fixed-seed uniform random rank over the same H47-QC candidate support; and
6. a fixed-seed uniform random rank over the full competition footprint.

Each comparator selects spacing by the same five selection blocks and tie rule. The two random fields are sanity controls, not stochastic significance tests. The historical H47-B 18,524-point locked-test score is reported for context only, not treated as a mass-matched comparator to this 5,000-point operating point.

### Promotion gate (fail closed)

No portal upload / slot use unless all are true:

1. H47-QC is selected without test/calibration labels in the feature builder and reaches exactly 5,000 points at the chosen spacing.
2. Its locked-test **pooled** DTI is strictly greater than every matched comparator's locked-test pooled DTI, including both random controls and H47-B at equal mass.
3. The selected point has a strictly positive assumption-conditional split-conformal lower bound and its limitations are acceptable. Any zero floor fails this condition.
4. Provenance, artifact-format, exact-byte, uniqueness-scope, and scientific review gates pass.

A failure at any step leaves only a conspicuously labeled research TIFF. This protocol does not claim that a pass predicts a public leaderboard score or proves private-set superiority.

## 5. Split-conformal calculation

For the selected spacing, let `μ` be the mean of its five selection-block DTIs. On `n = 6` calibration-block DTIs, compute one-sided residuals `r_i = μ − DTI_i`, sort them, and use rank `ceil((n+1)(1−α))` with `α = 1/(n+1) = 1/7`. Thus the maximum nontrivial nominal marginal level under this split is `6/7 = 85.7%`. The lower prediction bound is `clip(μ − q, 0, 1)` for the selected residual quantile `q`.

The level is only assumption-conditional on exchangeability of calibration and future **block DTI** values. Spatial dependence, acquisition differences, uneven catalogue support, and the public-catalogue/private-target mismatch are unverified. A reported positive floor would not be a guarantee for every cell, private labels, or a leaderboard. A zero floor is vacuous and blocks promotion.

## Implementation disclosure (review note; no post-result tuning)

A review of the scored implementation found one support detail not explicit in the frozen prose above: before centered finite differences, `structural_edge_agreement` erodes the common 99%-supported surface by one pixel so every retained gradient uses a valid centered stencil. This conservative validity guard was present in the implementation before any H47-QC DTI scoring, was not tuned on labels, and is recorded in the machine-readable run report. It makes the gradient-normalization/support domain slightly smaller than a literal reading of “common valid support.” This is disclosed as a protocol-description omission, not represented as a pre-frozen threshold change; the candidate still fails the preregistered gate.

## 6. Expected failure modes / no claims

- The same sample generates several related thermometers; formula agreement is not independent evidence. Water type, disequilibrium, dilution, evaporation, contamination, uncertain metadata, or incorrect export semantics can yield false agreement.
- Thermal locations are biased toward explored and already known systems. A concealed fault need not host a sampled spring/well, and high reservoir temperature does not determine a fault trace.
- Gravity/magnetic gradients also mark lithologic contacts, intrusions, survey seams, and processing boundaries. The joint edge is not unique to faults.
- The block holdout measures transfer to *public known-fault catalogue pixels only*. It does not validate detection of withheld new-fault pixels.
- The 2026 public leader reference (0.3774) and the older 0.3195 target are leaderboard/account-level observations; they are not comparable to this local proxy DTI and do not identify this file's score.
- A bounded scan shows NaNs fail a NaN-intolerant `[0,1]` check, but the original rejected TIFF is unavailable and its root cause is unverified. The research artifact therefore uses finite zeros outside the template footprint; the byte-level audit checks all values remain finite in `[0,1]`. This is a local format choice, not organizer-confirmed acceptance or diagnosis of the earlier rejection.
