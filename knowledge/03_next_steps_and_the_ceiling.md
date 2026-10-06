# Next steps, ranked by expected value

Reusable research base. Ordered by (information gained + score gained) per unit of
effort, given what this project established and falsified.

## 1. Use the 1 m DEM. Nothing else is close.

The competition supplies links to **716 USGS 3DEP 1 m tiles** and this project
could only reach a sibling repository's pre-derived **100 m** LiDAR scarp rasters.
Fault scarps are a metre-scale phenomenon: a 0.5–3 m scarp averaged over a
100 m pixel is a 0.5–3 % elevation perturbation, below the noise floor of the
resampled product.

The evidence that this matters is in the screen itself. Every LiDAR-derived layer
ranked poorly — `lidar_coh100`, `lidar_strike` and `lidar_valid` were among the
**worst of 72**, and the best (`lidar_upface_max`) reached only rank 21 — while the
community leader sits at 0.3262 against a family best of 0.2778. Forty-four
repositories converged on 0.26–0.28 using the same 100 m layers.

**Action:** download the tiles from `1m_DEM_links.csv`, compute scarp morphology at
native resolution (openness, local relief, down-facing / up-facing curvature,
profile curvature), detect scarps as **1–3 m features**, and only then aggregate to
the 100 m submission grid — aggregating the *detections*, not the *elevations*.

## 2. Spend three slots on the λ-probe (H47-5).

`1/DTI(λ)` is linear in `1/λ`, so an anchor, a λ = 0.5 scaling and a null-addition
of known mass recover `T`, `F` and `K` **exactly** — conditioning 56×–1380× better
than reading four decimals off one return. All three probes can be built to score
below the anchor so they cannot cost rank.

This converts every later decision from "which frame do we trust?" into arithmetic.
A sibling repository designed the identical probes and never submitted them.

**Also settles IR-47-011**: if the null-addition's cost differs from `α·N`, the
scoring footprint is not the whole raster.

## 3. Retrieve the staff answer in thread 11527.

Which data the NLR/USGS experts actually used — GeoDAWN lidar, 1 m 3DEP DEM,
magnetics/radiometrics, imagery, field mapping, geologic maps — and whether the new
faults are surface scarps or buried/geophysical picks. One post would settle the
field question directly. The page renders a collapsed post list; retry via
`…/11527/10` or `…/11527?print=true`.

## 4. Attack precision, not coverage.

At the incumbent's waste ratio `F/T ≈ 8`, 0.3195 needs 102.7 % weighted recall —
impossible. Halve `F/T` and 0.3195 needs ≈55 %. The lever is **removing** mass, not
adding it, and the family's own trajectory already proves it
(`0.1922 → 0.2778` came entirely from cutting S by 69 %).

Concrete: rank every emitted dot by its marginal credit under the best available
belief, and delete the tail below `α·DTI`. Then re-spend the freed budget only
where the marginal rule still accepts.

## 5. Resolve the 0.2778 attribution (IR-47-002).

One contested number decides whether the strongest hypothesis this project
generated — catalogue-flank re-occupation — is alive or dead. The break-even is
**0.2200**: the flank is supported only if the flank-pruned raster scored at or
below that. Open the leaderboard and check whether a 0.2778 row exists and which
file it belongs to.

## 6. Build H47-4 (deep-source magnetic continuity).

Specified, data restored, unbuilt. `TMI_up150` in `geodawn_extensions_u8.tif` is a
**depth filter**: a lineament that survives 150 m of upward continuation is
basement-scale; one that vanishes is near-surface. The discriminator is the ratio of
continued to uncontinued edge response.

LATI independently fits **high `tmi_hg` (β = +8.55)** with **low `tmi_vg`
(β = −9.63)** — shallow horizontal-gradient contrast without the deep
vertical-gradient expression. That is the buried-structure signature, arrived at
from the leaderboard rather than from the physics, and it is the opposite of the
"high geophysical contrast" prior every sibling repository used.

## 7. What is now known to be dead ends — do not retry

| Idea | Verdict | Evidence |
|---|---|---|
| Isotropic catalogue-flank re-occupation (0–300 m) | **Falsified** | break-even 0.2200 vs reported 0.2778; `dcat_band_0_1.5` becomes the **worst of 65** layers (−227.6 %) once the flank-pruned raster is admitted |
| Strike decomposition of the flank (along / across / tip / bend) | **Unsupported** | all six variants tied within 1.4 % of each other on LOO — orientation carries no signal beyond distance |
| SGMC catalogue-difference transfer | **Falsified** | adding it worsened LOO (0.008124 → 0.009279); the fitted truth puts **0.5 %** of K there |
| Blocked holdout on the given catalogue as a selector | **Structurally unfit** | DTI ≡ 0 under the organiser's masking; unmasked, it rewards the opposite skill |
| Any selection on an in-fold score | **Structurally unfit** | optimizer's curse measured at ≈0.30 DTI; cross-fitted deltas −0.061 and −0.045 |
| Gradients of `cond_surf`, `depth_to_base_surf`, `iso_grav_anom` | **Exhausted** | −89.7 %, −72.7 %, −64.4 % LOO on 13 observations |
| `thermal_hot_prox` (temperature class) | **Dead** | worst layer on 12 observations; but *broad* discharge density (`thermal_warm_prox`, all 27,092 points) did enter the selection |
| Volcanic vent proximity | **Dead** | 21 vents in the footprint |

## 8. What is known and worth keeping

| Quantity | Value | How |
|---|---|---|
| Hidden new-fault mass K in the scored split | **12,348 px** model-free; 15,638–21,477 under fitted shapes | the `r13-lattice` diffuse probe; corroborated by `placeholder` (7,931), a uniform 12-observation fit (12,626) and a sibling's independent inference (12,691) |
| Masking semantics | zeroed before **both** sums | the Hedge-v2 / ens12 natural experiment |
| Strongest single predictor of the hidden truth | proximity to the successful incumbent field (SSR 0.0086 of 72 layers) | LATI screen, with a shuffled-layer negative control at 0.1761 |
| Layers that survive a 13-observation LOO screen | `geod_shearrate`, `geod_2ndinv`, `rad_ThK` (**low**), `ieq_n100a15`, `tmi_hg`, `geod_dilaterate`, `tmi_vg` (**low**), `rad_Th` (**low**), `dcat_band_3_6`, `deq_n100a15`, `rad_UTh`, `thermal_warm_prox` | 41 of 65 improved LOO |
| Whether any of them survives **cross-fitting** | **Not demonstrated** | a-priori pool, in-fold selection, out-of-fold scoring → SHIP = False |

That last row is the honest headline. A coherent physical story — actively
straining, hydrothermally altered, seismically and thermally active ground with
shallow magnetic contrast — emerges from the leaderboard returns and is *not*
contradicted by any independent frame. But it is not **validated** either, and the
project rule is not to spend a scarce slot on an unvalidated idea. The Final Prize
Round is not an unlimited-submission refuge: one selected submission is evaluated in
both rounds. The official overview currently lists December 3, 2026, 23:59 UTC as
the competition end. This failed arm is research-only and must not consume a slot.
