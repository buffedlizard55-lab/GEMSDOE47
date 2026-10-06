# Next steps, ranked by expected value

Reusable research base. Ordered by (information gained + score gained) per unit of
effort, given what this project screened. **Boundary:** the LOO/LATI screens use owner-reported
participant-score/raster associations without organizer receipts. Treat those fits as exploratory
sensitivity analyses, not authenticated leaderboard supervision or verified hidden truth.

## 1. Audit 1 m DEM coverage first; this is an unverified data gap, not a proven score lever.

The official [USGS 3DEP 1-meter DEM collection](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e)
is public. This project has **not** verified exact tile coverage, acquisition dates,
licensing/availability for the competition footprint, or the current leader's inputs.
The accessible sibling inventory contained only pre-derived **100 m** LiDAR scarp
rasters. Fine-scale terrain could plausibly preserve metre-scale scarp morphology
that aggregation obscures, but this remains a physical motivation—not evidence of
private-set score gain.

The historical screen does not establish otherwise. Owner-reported fits ranked
`lidar_coh100`, `lidar_strike`, and `lidar_valid` among the **worst of 72**, while
`lidar_upface_max` reached rank 21. A one-time public leaderboard observation
recorded rank 1 at **0.3774**, above the older 0.3262 snapshot, but the leader's name,
TIFF, and features are unknown. Forty-four repositories converged on 0.26–0.28
using the same 100 m layers in an earlier saved inventory. These are reasons to
investigate resolution and data coverage, not proof that 1 m topography caused the
leaderboard gap.

**Action:** first intersect official USGS tile footprints and metadata with the
competition template and confirm adequate, authorized, usable coverage. Only then
consider native-resolution scarp morphology (openness, local relief, directional
curvature), with a frozen spatially blocked holdout and matched controls. If
implemented, detect candidate features at native resolution before aggregating the
*detections* to the 100 m submission grid; do not simply average elevations and
assume a gain. No competition slot is authorized without passing the standing gate.

## 2. Do not spend competition slots on the λ-probe.

`1/DTI(λ)` is linear in `1/λ`, so an anchor, λ = 0.5 scaling, and a null-addition of
known mass could identify `T`, `F`, and `K` under the metric assumptions. This is an
information probe, not a geological detector, and it does not beat the spatially
blocked holdout best. It is therefore **not authorized under the standing no-slot
rule**, even if a round advertises unlimited submissions. Reconsider only after a
new candidate independently passes its promotion gate and only if the information
would change a decision without compromising that gate.

The design may still inform offline algebra. It must not be used to imply private
scorer behavior or to spend a slot merely to collect a score.

## 3. Retrieve the staff answer in thread 11527.

Which data the NLR/USGS experts actually used — GeoDAWN lidar, 1 m 3DEP DEM,
magnetics/radiometrics, imagery, field mapping, geologic maps — and whether the new
faults are surface scarps or buried/geophysical picks. One post would settle the
field question directly. The page renders a collapsed post list; retry via
`…/11527/10` or `…/11527?print=true`.

## 4. Attack precision, not coverage.

The exact private-target waste ratio is unknown. Under the illustrative `F/K = 8.02` scenario,
0.3195 requires `T/K ≈ 82.05 %`, while the observed 0.3774 public leader would require ≈98.13 %.
An earlier claim of 102.7 % at this ratio was a formula/label mismatch and is withdrawn. The family
trajectory is consistent with precision gained by pruning mass, but its exact 0.2778 file attribution
and causal mechanism remain unresolved.

Concrete: rank every emitted dot by its marginal credit under the best available
belief, and delete the tail below `α·DTI`. Then re-spend the freed budget only
where the marginal rule still accepts.

## 5. Resolve the 0.2778 attribution (IR-47-002).

One contested number decides whether the strongest hypothesis this project
generated — catalogue-flank re-occupation — is **not resolved**. A sensitivity analysis on the
owner-reported values gives a break-even of **0.2200**, but the public 0.2778 participant row has no
organizer-authenticated TIFF mapping, and the H33-2-B2 owner page calls that file **UNSCORED**. Do not
use 0.2778 as a 13th H33-2-B2 observation unless an organizer receipt or equivalent file/hash record
resolves the attribution. Treat the break-even as conditional sensitivity, not a falsification.

## 6. H47-4 deep-source magnetic continuity — already screened, closed.

The `TMI_up150` persistence idea was implemented as H47-B and evaluated on the
frozen 4×4 public-catalogue block split. It scored 0.027553 at 18,524 points and
lost to a matched fixed-seed random control (0.037159); its conformal lower floor
was zero. Do not rebuild it or retune the locked blocks as if a repeat were
independent evidence. The result is a negative screen, not proof that magnetic
data cannot help.

## 7. Historical screens not supported in owner-reported fits — not universal falsification

| Idea | Status | Evidence and limitation |
|---|---|---|
| Isotropic catalogue-flank re-occupation (0–300 m) | **Attribution-sensitive / unresolved** | Conditional break-even 0.2200; the alleged 0.2778 H33-2-B2 mapping is unauthenticated, so the 13-value fit cannot establish falsification. |
| Strike decomposition of the flank (along / across / tip / bend) | **Not supported in the exploratory fit** | The six variants were within 1.4% LOO; score/file mappings are not authenticated and this does not show orientation is generally uninformative. |
| SGMC catalogue-difference transfer | **Not supported in the owner-reported LOO screen** | Adding it worsened LOO (0.008124 → 0.009279); the fitted proxy assigned 0.5% of K there. This is not a private-target test. |
| Catalogue-as-truth blocked holdout | **Conditional limitation** | If the evaluator masks catalogue truth and predictions from both sums, K = 0 and DTI is undefined/vacuous; exact portal behavior is not established. |
| Selecting on in-fold scores | **Methodologically biased** | In-fold optimization is optimistic by construction; the reported ≈0.30 DTI gap and cross-fit deltas are exploratory, not authenticated private outcomes. |
| Gradients of `cond_surf`, `depth_to_base_surf`, `iso_grav_anom` | **Poor in the exploratory fit** | Reported LOO deltas −89.7%, −72.7%, −64.4%; not an exhaustive gradient search. |
| `thermal_hot_prox` (temperature class) | **Poor in the owner-reported fit** | It ranked poorly while broad `thermal_warm_prox` entered selection; neither establishes a general causal effect. |
| Volcanic vent proximity | **Limited coverage** | The restored mirror lists 21 vents; this does not prove vents carry no signal. |

## 8. What is known and worth keeping

| Quantity | Value | How / limitation |
|---|---|---|
| Hidden new-fault mass K in the scored split | **Historical estimate: 12,348 px** under an owner-reported mapping; fitted-shape estimates 15,638–21,477 | `r13-lattice` diffuse-probe calculation; score/file association is unauthenticated, so none is a verified private truth count. |
| Masking semantics | Staff wording and an owner-reported mask comparison are **consistent** with excluding known pixels from both sums | No organizer receipt validates those file/score mappings or exact portal implementation. |
| Strongest predictor in the fitted proxy | Proximity to the owner-reported incumbent field (SSR 0.0086 of 72 layers) | Exploratory LATI fit with a shuffled-layer negative control; not a validated hidden-truth model. |
| Layers selected in a 13-observation LOO screen | `geod_shearrate`, `geod_2ndinv`, `rad_ThK` (**low**), `ieq_n100a15`, `tmi_hg`, `geod_dilaterate`, `tmi_vg` (**low**), `rad_Th` (**low**), `dcat_band_3_6`, `deq_n100a15`, `rad_UTh`, `thermal_warm_prox` | Owner-reported score/raster associations; 41/65 improved in that LOO screen, but none is validated by private labels. |
| Whether any of them survives **cross-fitting** | **Not demonstrated** | The saved cross-fit used an a-priori pool and reported negative out-of-fold deltas; mappings remain unauthenticated. |

The H47-QC result is the latest direct research screen in this checkout: it selected
6 px / 600 m at 5,000 points, scored 0.013169 on the locked public-catalogue test
blocks, lost to its geochemistry-only ablation (0.014195), and had an 85.7% nominal
split-conformal level with a **0.0** clipped lower DTI floor. It is not promoted.

**No current candidate is eligible for any submission slot, including an unlimited
round.** A future idea must first beat the current spatially blocked holdout best on
a preregistered test, with meaningful controls, adequate target-relevant labels,
and a defensible positive performance floor; then it needs provenance, exact-byte,
uniqueness-scope and scientific review. Public-catalogue screening is not proof of
private newly mapped fault performance.
