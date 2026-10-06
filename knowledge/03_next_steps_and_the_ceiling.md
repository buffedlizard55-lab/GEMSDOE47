# Next steps, ranked by expected value

Reusable research base. Ordered by potential information value and effort, with
all unvalidated score claims treated as hypotheses rather than established gains.

## 1. Use the 1 m DEM. Nothing else is close.

The competition supplies links to **716 USGS 3DEP 1 m tiles** and this project
could only reach a sibling repository's pre-derived **100 m** LiDAR scarp rasters.
Fault scarps are a metre-scale phenomenon: a 0.5–3 m scarp averaged over a
100 m pixel is a 0.5–3 % elevation perturbation, below the noise floor of the
resampled product.

The earlier 72-layer screen found that its available 100 m LiDAR-derived layers
ranked poorly (`lidar_coh100`, `lidar_strike` and `lidar_valid` were near the bottom;
`lidar_upface_max` reached rank 21). That does not establish how a native-resolution
1 m DEM would perform. The latest saved one-time leaderboard snapshot, captured
2026-10-06, records rank 1 at **0.3774**; these are participant-level scores and do
not identify a raster or validate a geological explanation. Forty-four repository
outputs clustered around 0.26–0.28 in the older comparison, but their artifact
attributions are not all authenticated.

**Research action, subject to data provenance and the holdout gate:** first verify
that the official USGS 3DEP tiles linked for the competition are obtainable and
permitted for this use. If available, test native-resolution scarp morphology
(openness, local relief, directional curvature) and aggregate detections, not raw
elevations, to the submission grid. This is a hypothesis to test, not a predicted
performance gain. No slot is authorized until a distinct candidate beats the
spatially blocked holdout best and controls.

## 2. Do not spend slots on the λ-probe under the current gate (H47-5).

The scale identity makes `1/DTI(λ)` linear in `1/λ` for `DTI(λp)`, and a known-mass
null addition may provide a useful diagnostic if its assumptions hold. Earlier notes
stated a fixed three-slot cost without verifying whether the owner-reported λ=1
anchor can be authenticated and reused. The three observations describe the theoretical measurement design, not a verified
count of new portal uploads or submission slots. The accessible official pages checked
2026-10-06 do not expose current per-user quota or slot accounting, so the number and
cost of any new uploads are unknown; do not assume a free route. No λ-probe is
authorized now. Revisit only after checking the portal/organizer and preregistering
separately, and only if the resulting scores would identify a quantity not already
confounded by score-to-file attribution and the evaluation footprint.

## 3. Retrieve the staff answer in thread 11527.

Which data the NLR/USGS experts actually used — GeoDAWN lidar, 1 m 3DEP DEM,
magnetics/radiometrics, imagery, field mapping, geologic maps — and whether the new
faults are surface scarps or buried/geophysical picks. One post would settle the
field question directly. The page renders a collapsed post list; retry via
`…/11527/10` or `…/11527?print=true`.

## 4. Use the metric algebra without mixing ratios.

For `x = T/K` and `ρ = F/K`, the inverse is
`x = (αρ + β)/(1/DTI − α)`. If the input is instead `f = F/T`, use the distinct
identity `x = β/[1/DTI − α(1 + f)]`. `ρ = 8.02` has no verified incumbent
provenance and is only an illustrative scenario: it implies `T/K ≈ 82.05 %` for
DTI 0.3195, not an impossible value. Separately, if `F/T = 8`, the same target
requires `T/K ≈ 60.16 %`. Neither ratio can be inferred from a participant-level
leaderboard score without an authenticated prediction and score mapping.

The marginal rule `k > α·DTI` is a local add-one-pixel criterion under the metric's
assumptions; it is not by itself a validated selection procedure. Any deletion or
re-emission policy must be tested on the unmasked evaluated domain, in spatially
blocked folds, against matched-mass and nontrivial controls. Do not infer a gain
from the artifact-family mass trajectory alone.

## 5. Treat the 0.2778/H33-2-B2 link as unresolved (IR-47-002).

The one-time leaderboard read captured `extradr19` at 0.2778/#13, but the public
board does not identify TIFFs, hashes, or upload receipts. The GEMSDOE32 owner page
marks H33-2-B2 unscored, so the alleged file-to-score mapping remains unverified.
The tested sensitivity grid is a *conditional calculation*: under the assumed H33 mapping, LOO improvement is positive at DTI 0.2200 and negative by 0.2400. This brackets a coarse-grid sign change; it does not locate an exact root or establish whether the flank hypothesis is supported or refuted. Do not try to resolve the mapping by checking the participant-only leaderboard; only an authenticated organizer receipt or sufficiently explicit owner evidence could do so. Until then, keep H33 out of causal claims and promotion decisions.

## 6. H47-4/DMC: related magnetic screen already tested; not promoted.

The public-mirror H47-B experiment tested a cross-scale `TMI_up150` magnetic-edge
persistence screen at 5 px / 500 m. It lost to the fixed-seed random control on the
locked spatial test and was not promoted. That result does not show that magnetic
data cannot help, and the screen was not a full physical tilt-depth reconstruction.
A different raw-data depth discriminator would be a new, separately preregistered
hypothesis, not an unbuilt continuation of H47-B.

The conditional 13-row LATI fit reports **high `tmi_hg` (β = +8.55)** with **low
`tmi_vg` (β = −9.63)**. That scenario includes the unverified H33-to-0.2778
mapping, so the coefficients are exploratory and need an H33-excluded sensitivity
analysis before supporting any physical interpretation.

## 7. Exploratory screens not promoted — require new evidence before retry

| Idea | Verdict | Evidence |
|---|---|---|
| Isotropic catalogue-flank re-occupation (0–300 m) | **Unresolved** | the 12-row exploratory fit is positive; the conditional H33 sensitivity is positive at assumed DTI 0.2200 and negative by 0.2400, with no exact root; H33-to-0.2778 attribution is unverified |
| Strike decomposition of the flank (along / across / tip / bend) | **No incremental signal in this exploratory fit** | the tested variants were within 1.4 % of each other on 12-row LOO; this does not establish that orientation never helps |
| SGMC catalogue-difference transfer | **Not supported in this exploratory fit** | adding it worsened LOO (0.008124 → 0.009279); the conditional fitted q allocates **0.5 %** of its modeled K there; not a measured hidden-truth proportion or general falsification |
| Blocked holdout on the given catalogue as a selector | **Structurally unfit** | DTI ≡ 0 under the organiser's masking; unmasked, it rewards the opposite skill |
| Any selection on an in-fold score | **Structurally unfit** | optimizer's curse measured at ≈0.30 DTI; cross-fitted deltas −0.061 and −0.045 |
| Gradients of `cond_surf`, `depth_to_base_surf`, `iso_grav_anom` | **Not promoted in this screen** | conditional 13-row LOO changes were −89.7 %, −72.7 %, and −64.4 %; the H33 mapping is unverified |
| `thermal_hot_prox` (temperature class) | **Dead** | worst layer on 12 observations; but *broad* discharge density (`thermal_warm_prox`, all 27,092 points) did enter the selection |
| Volcanic vent proximity | **Dead** | 21 vents in the footprint |

## 8. What is known and worth keeping

| Quantity | Value | How |
|---|---|---|
| Exploratory K estimates (not measured hidden-label mass) | Diffuse-probe inverse ≈12,348 px under the owner-reported `r13-lattice` score/raster association; selected fitted-shape estimates ≈15,638–21,477 px | The owner-reported `placeholder` association yields ≈7,931; a separate uniform fit to the same twelve owner-reported pairs gives ≈12,626. A sibling repository reports ≈12,691 by a different route, but it is not authenticated independent confirmation. All values depend on unverified score/file associations or modeling assumptions. |
| Masking semantics | known USGS/INGENIOUS pixels are excluded from evaluation and penalty terms; deleting predictions exactly on them cannot improve DTI | official staff reply [11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516); the Hedge-v2 / ens12 comparison is observational and is not used to infer a causal gain |
| Best single-layer fit to the owner-reported DTI rows in this screen | proximity to the owner-reported d2.8 reference raster (SSR 0.0086 of 72 layers) | Exploratory 12-row LATI screen; shuffled-layer negative control had SSR 0.1761. This ranks in-sample fit to unauthenticated associations, not predictive validity or hidden-truth proximity. |
| Layers with positive LOO changes in the conditional 13-row screen | `geod_shearrate`, `geod_2ndinv`, `rad_ThK` (**low**), `ieq_n100a15`, `tmi_hg`, `geod_dilaterate`, `tmi_vg` (**low**), `rad_Th` (**low**), `dcat_band_3_6`, `deq_n100a15`, `rad_UTh`, `thermal_warm_prox` | 41 of 65 improved LOO under the assumed, unverified H33 mapping; not independently validated |
| Whether any of them survives **cross-fitting** | **Not demonstrated** | a-priori pool, in-fold selection, out-of-fold scoring → SHIP = False |

That last row is the honest headline. LATI is an exploratory inverse fit to
owner-reported score/raster associations, not a map of authenticated leaderboard
returns. The H47-GSA observation-level cross-fit was negative (−0.0611 and
−0.0450 versus the owner-reported d2.8 reference) and conditional on the
unverified H33 association; it is not a spatial holdout or private-target
validation. No candidate is validated for submission. Keep the gate closed; do not rely on an unverified
submission-limit exception or spend a slot until a new candidate beats the
spatially blocked holdout best and controls under a preregistered protocol.
