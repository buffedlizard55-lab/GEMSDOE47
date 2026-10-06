---
title: Results
layout: default
nav_order: 3
---

# Results — every measurement, with the script that reproduces it

*Generated 2026-10-06 20:13 UTC by `scripts/build_site.py`.*

## 1. Which bands can localise a fault at all

`scripts/diagnose_bands.py` → `evidence/band_scale_diagnostics.json`.

`hf` is the fraction of a band's variance that survives removal of a 300 m smooth — the part of the signal living at the metric's own kernel support. `AUC|hf|` is the tie-aware AUC of that residual against the given catalogue.

| band | hf fraction | lag-3 px autocorr | AUC raw | AUC of 300 m residual |
|---|---|---|---|---|
| `tmi_vg` | **0.381477** | 0.44072 | 0.4867 | 0.523 |
| `det_elev_slope` | **0.18099** | 0.78774 | 0.5544 | 0.5655 |
| `tmi_hg` | **0.175173** | 0.75391 | 0.5289 | 0.5253 |
| `rtp` | **0.034893** | 0.9339 | 0.4981 | 0.5238 |
| `tmi` | **0.033179** | 0.94166 | 0.4884 | 0.5248 |
| `tc` | **0.023261** | 0.95932 | 0.4424 | 0.4965 |
| `deq_n100a15` | **0.009431** | 0.98901 | 0.553 | 0.5249 |
| `det_elev` | **0.006534** | 0.98813 | 0.4853 | 0.5481 |
| `iso_grav_anom_vg` | **0.003828** | 0.99267 | 0.5311 | 0.5314 |
| `iso_grav_anom_slope` | **0.00318** | 0.98616 | 0.5376 | 0.527 |
| `iso_grav_anom_hg` | **0.002986** | 0.98423 | 0.5042 | 0.5271 |
| `ieq_n100a15` | **0.002128** | 0.99692 | 0.5731 | 0.5394 |
| `cond_surf` | **0.002091** | 0.99528 | 0.4842 | 0.5076 |
| `depth_to_base_surf` | **0.001893** | 0.99665 | 0.5136 | 0.5302 |
| `geod_shearrate` | **0.001773** | 0.99672 | 0.5687 | 0.5418 |
| `geod_2ndinv` | **0.00173** | 0.99686 | 0.5715 | 0.5344 |
| `geod_dilaterate` | **0.001697** | 0.99656 | 0.5345 | 0.5512 |
| `mag_anom` | **0.001195** | 0.99385 | 0.4901 | 0.5267 |
| `iso_grav_anom` | **0.001177** | 0.99666 | 0.4602 | 0.5221 |

Only `tmi_vg`, `det_elev_slope` and `tmi_hg` carry appreciable 300 m-scale variance. The other sixteen are >96.5 % smooth above the kernel support and can act only as regional priors. This is why sixteen of the nineteen bands are used in `detector.regional_gate` and never as locators.

## 2. The two holdout instruments measure different populations

`scripts/measure_instruments.py` → `evidence/instrument_populations.json`. Full argument in [knowledge/02](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/02_the_two_instruments_measure_different_populations.md).

| population | pixels |
|---|---|
| footprint | 5,167,373 |
| given catalogue | 60,988 |
| within 300 m of the catalogue | 444,794 |
| SGMC traces > 300 m from the catalogue | 61,664 |
| A1 — isolated catalogue components | 300 components, 6,315 px |
| A2 — flanking catalogue components | 2897 components, 54,673 px |

**Random baselines for precision-at-40k:**

| target | random precision |
|---|---|
| catalogue | 0.08608 |
| sgmc_offcatalogue | 0.08289 |
| A1 | 0.00988 |
| A2 | 0.0762 |

Median band value by population — the decisive table:

| band | background | given catalogue | SGMC off-catalogue |
|---|---|---|---|
| `geod_2ndinv` | 19.4 | 25.0 | 18.6811 |
| `tc` | 18.5854 | 17.4192 | 15.822 |
| `det_elev` | -76.2795 | -68.7578 | 115.4244 |
| `depth_to_base_surf` | 315.7888 | 320.9888 | 104.8788 |
| `ieq_n100a15` | 738.6331 | 906.001 | 726.9 |
| `det_elev_slope` | 3.5833 | 5.1027 | 12.9884 |

SGMC off-catalogue traces are high, steep and shallow-basement — exposed mountain bedrock. The given catalogue is close to background on elevation and sediment thickness. The populations are nearly disjoint in terrain space, so the SGMC holdout measures *"is this a mountain"* and is **rejected for selection**. Selecting on it would have shipped `lrm(det_elev_slope, 9)`, which is the best transform on SGMC and only 1.2× random against the population that matters.

## 3. The transform search

`scripts/search_scarp_radius.py` → `evidence/scarp_radius_search.json`.

Random precision-at-40k: cat = **0.08613**, A1 = **0.00989**, A2 = **0.07624**

| band | transform | along-strike half-width | P@10k cat | P@40k cat | P@40k A1 | P@40k A2 | AUC cat |
|---|---|---|---|---|---|---|---|
| `det_elev_slope` | scarp | 9 px | 0.6543 | **0.50487** | 0.02485 | 0.48002 | 0.6183 |
| `det_elev_slope` | scarp | 13 px | 0.6199 | **0.46913** | 0.01745 | 0.45167 | 0.6158 |
| `det_elev_slope` | scarp | 5 px | 0.5859 | **0.46113** | 0.03215 | 0.42897 | 0.6128 |
| `det_elev_slope` | scarp | 17 px | 0.5897 | **0.44028** | 0.01625 | 0.42402 | 0.6092 |
| `det_elev_slope` | scarp | 21 px | 0.5623 | **0.4219** | 0.01535 | 0.40655 | 0.6014 |
| `det_elev_slope` | scarp | 25 px | 0.5331 | **0.4062** | 0.01475 | 0.39145 | 0.5942 |
| `det_elev_slope` | scarp | 31 px | 0.4822 | **0.38803** | 0.0148 | 0.37322 | 0.5833 |
| `det_elev` | scarp | 21 px | 0.0766 | **0.1016** | 0.00263 | 0.09897 | 0.5746 |
| `det_elev` | scarp | 17 px | 0.0672 | **0.09903** | 0.00385 | 0.09517 | 0.577 |
| `det_elev` | scarp | 13 px | 0.0558 | **0.09648** | 0.00308 | 0.0934 | 0.5792 |
| `det_elev` | scarp | 9 px | 0.0436 | **0.0956** | 0.00175 | 0.09385 | 0.5813 |
| `det_elev` | scarp | 25 px | 0.0712 | **0.09202** | 0.001 | 0.09102 | 0.5719 |

`scarp` = the across-strike two-sided mean difference, smoothed along the strike over `2r+1` px, maximised over four strikes. The interior optimum at r = 9 px (1.9 km of required along-strike persistence) is fitted, not chosen: precision rises to r = 9 then falls monotonically to r = 31.

Note what does *not* work: `det_elev` (as opposed to its slope) reaches at best 0.096, and every magnetic-band transform lands at 1.0–1.3× random.

## 4. Derived-surface skill, tie-aware

`scripts/diagnose_surfaces.py` → `evidence/surface_skill.json`. Naive rank statistics are useless here: a surface that is a plateau over 99 % of the grid reports AUC ≈ 1.0 under a `searchsorted('left')` rank. Every number below is tie-aware.

| surface | plateau fraction | AUC vs catalogue | P@40k catalogue | P@40k SGMC-offcat |
|---|---|---|---|---|
| `A_catalogue_density.npy` | 1.036 | 0.9678 | **0.88633** | 0.04065 |
| `E_persistence.npy` | 462687.545 | 0.5013 | **0.12552** | 0.06675 |
| `fam_strain.npy` | 0.399 | 0.5403 | **0.1211** | 0.05735 |
| `fam_grav.npy` | 0.101 | 0.5377 | **0.11707** | 0.07328 |
| `coherence.npy` | 0.000 | 0.5313 | **0.11167** | 0.05513 |
| `D_ratio.npy` | 0.002 | 0.4507 | **0.1071** | 0.16612 |
| `A_physics_density.npy` | 1.162 | 0.5629 | **0.10237** | 0.08455 |
| `corr_mean.npy` | 0.000 | 0.5516 | **0.0947** | 0.08135 |
| `corr_count.npy` | 820947.333 | 0.5004 | **0.09287** | 0.0863 |
| `C_drain_mag.npy` | 0.126 | 0.5345 | **0.092** | 0.00937 |
| `corr_max.npy` | 0.002 | 0.537 | **0.09173** | 0.07318 |
| `B_braid_count.npy` | 429994.833 | 0.4987 | **0.08167** | 0.12677 |
| `B_braid.npy` | 515993.800 | 0.4987 | **0.08067** | 0.13362 |
| `D_strain.npy` | 4.313 | 0.4765 | **0.07895** | 0.08035 |

Random baselines: 0.0861 (catalogue halo), 0.0829 (SGMC off-catalogue halo).

The shipped reference artifacts, on the same statistics:

| reference artifact | public DTI | P@40k catalogue | P@40k SGMC-offcat |
|---|---|---|---|
| `scored_h35-06_0.0418.tif` | 0.0418 | 0.20478 | 0.1664 |
| `scored_h34-scatter-q50_0.0778.tif` | 0.0778 | 0.0621 | 0.1291 |
| `scored_h19-5-solid_0.1922.tif` | 0.1922 | 0.1998 | 0.12618 |
| `scored_h27-4-d2.8_0.2708.tif` | 0.2708 | 0.1173 | 0.12573 |
| `scored_h33-2-b2_0.2778.tif` | 0.2778 | 0.06073 | 0.12532 |
| `scored_h33d-tip-stepover_0.2632.tif` | 0.2632 | 0.14447 | 0.12343 |
| `scored_h30-arr-habitat_0.1352.tif` | 0.1352 | 0.12923 | 0.122 |
| `scored_h19-5-d1.5_0.2477.tif` | 0.2477 | 0.19792 | 0.12087 |
| `scored_d28-poisson-offcat_0.2600.tif` | 0.2600 | 0.19515 | 0.1188 |
| `scored_h19-5-d2.8_0.2600.tif` | 0.2600 | 0.19515 | 0.1188 |
| `scored_topo-gap-d1.5_0.2449.tif` | 0.2449 | 0.19717 | 0.11828 |

`scored_h33-2-b2` sits **below** the random baseline on the catalogue halo (0.0607 vs 0.0861) because it was deliberately flank-pruned: its dots were deleted from within 200 m of the catalogue. That is the mechanism of its 0.2778, not a defect.

## 5. The inversion of the organiser's own scores

`scripts/run_inversion.py` → `evidence/inversion/live_anchor_inversion.json`.

| artifact | S_active | public DTI | model-free \|G\| floor | dots ≤2 px of catalogue |
|---|---|---|---|---|
| `scored_h33-2-b2_0.2778.tif` | 37,654.0 | 0.2778 | 2896.782387150374 | 0 |
| `scored_h27-4-d2.8_0.2708.tif` | 40,199.0 | 0.2708 | 2985.7074053757538 | 2545 |
| `scored_h33d-tip-stepover_0.2632.tif` | 41,865.0 | 0.2632 | 2991.0065146579805 | 3894 |
| `scored_h19-5-d2.8_0.2600.tif` | 44,090.0 | 0.26 | 3098.2162162162167 | 6436 |
| `scored_d28-poisson-offcat_0.2600.tif` | 44,090.0 | 0.26 | 3098.2162162162167 | 6436 |
| `scored_h19-5-d1.5_0.2477.tif` | 60,069.0 | 0.2477 | 3955.6270902565466 | 8769 |
| `scored_topo-gap-d1.5_0.2449.tif` | 61,328.0 | 0.2449 | 3978.076334260363 | 8875 |
| `scored_h19-5-solid_0.1922.tif` | 121,131.0 | 0.1922 | 5764.144144590246 | 17326 |
| `scored_h30-arr-habitat_0.1352.tif` | 91,533.0 | 0.1352 | 2861.9938945420904 | 8296 |
| `scored_h34-scatter-q50_0.0778.tif` | 37,654.0 | 0.0778 | 635.3244849273475 | 0 |
| `scored_h35-06_0.0418.tif` | 39,530.0 | 0.0418 | 344.8870799415571 | 5365 |

**Binding model-free floor: |G| ≥ 5764.144144590246 px**, from `scored_h19-5-solid_0.1922.tif`.

**Structural facts.** ['T >= M (Voronoi argument): every dot serving >=1 truth pixel contributes at least its own max weight to T.', 'T <= |G| and M <= S, since k <= 1.', '|G| >= 0.2*DTI*S_active/(1 - DTI): from T = DTI*(0.2(S-M)+0.8G)/(1-0.2DTI) with T <= G and M >= 0.', 'A dot whose truth pixel is already better covered changes the denominator by 0.2*(1-w) >= 0: redundant mass never helps.']

**Nested-pair natural experiment.**

| quantity | value |
|---|---|
| `parent` | scored_topo-gap-d1.5_0.2449.tif |
| `child` | scored_h19-5-d1.5_0.2477.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 1259.0 |
| `score_change` | 0.0028 |
| `T_parent` | 4346.024858371139 |
| `T_child` | 4332.682136746422 |
| `credit_lost` | 13.342721624717342 |
| `mean_credit_of_removed_dots` | 0.010597872616931963 |
| `credit_bar_at_child` | 0.04954 |

| quantity | value |
|---|---|
| `parent` | scored_topo-gap-d1.5_0.2449.tif |
| `child` | scored_h19-5-d1.5_0.2477.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 1259.0 |
| `score_change` | 0.0028 |
| `T_parent` | 4806.634392546949 |
| `T_child` | 4798.832417987081 |
| `credit_lost` | 7.80197455986854 |
| `mean_credit_of_removed_dots` | 0.006196961524915441 |
| `credit_bar_at_child` | 0.04954 |

| quantity | value |
|---|---|
| `parent` | scored_topo-gap-d1.5_0.2449.tif |
| `child` | scored_h19-5-d1.5_0.2477.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 1259.0 |
| `score_change` | 0.0028 |
| `T_parent` | 5630.6759479295915 |
| `T_child` | 5632.786503377313 |
| `credit_lost` | -2.1105554477217083 |
| `mean_credit_of_removed_dots` | -0.0016763744620506024 |
| `credit_bar_at_child` | 0.04954 |

| quantity | value |
|---|---|
| `parent` | scored_topo-gap-d1.5_0.2449.tif |
| `child` | scored_h19-5-d1.5_0.2477.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 1259.0 |
| `score_change` | 0.0028 |
| `T_parent` | 7278.7590586948745 |
| `T_child` | 7300.694674157778 |
| `credit_lost` | -21.935615462903115 |
| `mean_credit_of_removed_dots` | -0.01742304643598341 |
| `credit_bar_at_child` | 0.04954 |

| quantity | value |
|---|---|
| `parent` | scored_h27-4-d2.8_0.2708.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 2545.0 |
| `score_change` | 0.007 |
| `T_parent` | 3622.0946750867274 |
| `T_child` | 3571.5128909128543 |
| `credit_lost` | 50.581784173873075 |
| `mean_credit_of_removed_dots` | 0.01987496431193441 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h27-4-d2.8_0.2708.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 2545.0 |
| `score_change` | 0.007 |
| `T_parent` | 4134.206461980884 |
| `T_child` | 4097.641184193808 |
| `credit_lost` | 36.56527778707641 |
| `mean_credit_of_removed_dots` | 0.014367496183527078 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h27-4-d2.8_0.2708.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 2545.0 |
| `score_change` | 0.007 |
| `T_parent` | 5050.3867884631645 |
| `T_child` | 5038.8973783406045 |
| `credit_lost` | 11.489410122560002 |
| `mean_credit_of_removed_dots` | 0.004514502995111985 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h27-4-d2.8_0.2708.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 2545.0 |
| `score_change` | 0.007 |
| `T_parent` | 6882.747441427725 |
| `T_child` | 6921.409766634196 |
| `credit_lost` | -38.662325206470996 |
| `mean_credit_of_removed_dots` | -0.015191483381717484 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-d2.8_0.2600.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 3891.0 |
| `score_change` | 0.0108 |
| `T_parent` | 3683.145550711784 |
| `T_child` | 3622.0946750867274 |
| `credit_lost` | 61.050875625056506 |
| `mean_credit_of_removed_dots` | 0.01569027900926664 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-d2.8_0.2600.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 3891.0 |
| `score_change` | 0.0108 |
| `T_parent` | 4173.713080168777 |
| `T_child` | 4134.206461980884 |
| `credit_lost` | 39.506618187892855 |
| `mean_credit_of_removed_dots` | 0.010153332867615742 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-d2.8_0.2600.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 3891.0 |
| `score_change` | 0.0108 |
| `T_parent` | 5051.350210970465 |
| `T_child` | 5050.3867884631645 |
| `credit_lost` | 0.9634225073004927 |
| `mean_credit_of_removed_dots` | 0.0002476028032126684 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-d2.8_0.2600.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 3891.0 |
| `score_change` | 0.0108 |
| `T_parent` | 6806.624472573841 |
| `T_child` | 6882.747441427725 |
| `credit_lost` | -76.12296885388423 |
| `mean_credit_of_removed_dots` | -0.01956385732559348 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_d28-poisson-offcat_0.2600.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 3891.0 |
| `score_change` | 0.0108 |
| `T_parent` | 3683.145550711784 |
| `T_child` | 3622.0946750867274 |
| `credit_lost` | 61.050875625056506 |
| `mean_credit_of_removed_dots` | 0.01569027900926664 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_d28-poisson-offcat_0.2600.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 3891.0 |
| `score_change` | 0.0108 |
| `T_parent` | 4173.713080168777 |
| `T_child` | 4134.206461980884 |
| `credit_lost` | 39.506618187892855 |
| `mean_credit_of_removed_dots` | 0.010153332867615742 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_d28-poisson-offcat_0.2600.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 3891.0 |
| `score_change` | 0.0108 |
| `T_parent` | 5051.350210970465 |
| `T_child` | 5050.3867884631645 |
| `credit_lost` | 0.9634225073004927 |
| `mean_credit_of_removed_dots` | 0.0002476028032126684 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_d28-poisson-offcat_0.2600.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 3891.0 |
| `score_change` | 0.0108 |
| `T_parent` | 6806.624472573841 |
| `T_child` | 6882.747441427725 |
| `credit_lost` | -76.12296885388423 |
| `mean_credit_of_removed_dots` | -0.01956385732559348 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-d2.8_0.2600.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 6436.0 |
| `score_change` | 0.0178 |
| `T_parent` | 3683.145550711784 |
| `T_child` | 3571.5128909128543 |
| `credit_lost` | 111.63265979892958 |
| `mean_credit_of_removed_dots` | 0.017345037259000867 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-d2.8_0.2600.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 6436.0 |
| `score_change` | 0.0178 |
| `T_parent` | 4173.713080168777 |
| `T_child` | 4097.641184193808 |
| `credit_lost` | 76.07189597496927 |
| `mean_credit_of_removed_dots` | 0.011819747665470675 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-d2.8_0.2600.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 6436.0 |
| `score_change` | 0.0178 |
| `T_parent` | 5051.350210970465 |
| `T_child` | 5038.8973783406045 |
| `credit_lost` | 12.452832629860495 |
| `mean_credit_of_removed_dots` | 0.0019348714465289769 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-d2.8_0.2600.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 6436.0 |
| `score_change` | 0.0178 |
| `T_parent` | 6806.624472573841 |
| `T_child` | 6921.409766634196 |
| `credit_lost` | -114.78529406035523 |
| `mean_credit_of_removed_dots` | -0.01783488099135414 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_d28-poisson-offcat_0.2600.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 6436.0 |
| `score_change` | 0.0178 |
| `T_parent` | 3683.145550711784 |
| `T_child` | 3571.5128909128543 |
| `credit_lost` | 111.63265979892958 |
| `mean_credit_of_removed_dots` | 0.017345037259000867 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_d28-poisson-offcat_0.2600.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 6436.0 |
| `score_change` | 0.0178 |
| `T_parent` | 4173.713080168777 |
| `T_child` | 4097.641184193808 |
| `credit_lost` | 76.07189597496927 |
| `mean_credit_of_removed_dots` | 0.011819747665470675 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_d28-poisson-offcat_0.2600.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 6436.0 |
| `score_change` | 0.0178 |
| `T_parent` | 5051.350210970465 |
| `T_child` | 5038.8973783406045 |
| `credit_lost` | 12.452832629860495 |
| `mean_credit_of_removed_dots` | 0.0019348714465289769 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_d28-poisson-offcat_0.2600.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 6436.0 |
| `score_change` | 0.0178 |
| `T_parent` | 6806.624472573841 |
| `T_child` | 6921.409766634196 |
| `credit_lost` | -114.78529406035523 |
| `mean_credit_of_removed_dots` | -0.01783488099135414 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h19-5-d1.5_0.2477.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 61062.0 |
| `score_change` | 0.0555 |
| `T_parent` | 5764.144144590246 |
| `T_child` | 4332.682136746422 |
| `credit_lost` | 1431.4620078438238 |
| `mean_credit_of_removed_dots` | 0.023442763221706197 |
| `credit_bar_at_child` | 0.04954 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h19-5-d1.5_0.2477.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 61062.0 |
| `score_change` | 0.0555 |
| `T_parent` | 6121.672740130622 |
| `T_child` | 4798.832417987081 |
| `credit_lost` | 1322.840322143541 |
| `mean_credit_of_removed_dots` | 0.02166388788679606 |
| `credit_bar_at_child` | 0.04954 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h19-5-d1.5_0.2477.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 61062.0 |
| `score_change` | 0.0555 |
| `T_parent` | 6761.30001247972 |
| `T_child` | 5632.786503377313 |
| `credit_lost` | 1128.5135091024067 |
| `mean_credit_of_removed_dots` | 0.01848143704926807 |
| `credit_bar_at_child` | 0.04954 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h19-5-d1.5_0.2477.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 61062.0 |
| `score_change` | 0.0555 |
| `T_parent` | 8040.554557177919 |
| `T_child` | 7300.694674157778 |
| `credit_lost` | 739.8598830201418 |
| `mean_credit_of_removed_dots` | 0.012116535374212142 |
| `credit_bar_at_child` | 0.04954 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h19-5-d2.8_0.2600.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 77041.0 |
| `score_change` | 0.0678 |
| `T_parent` | 5764.144144590246 |
| `T_child` | 3683.145550711784 |
| `credit_lost` | 2080.9985938784616 |
| `mean_credit_of_removed_dots` | 0.02701157297904313 |
| `credit_bar_at_child` | 0.052 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h19-5-d2.8_0.2600.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 77041.0 |
| `score_change` | 0.0678 |
| `T_parent` | 6121.672740130622 |
| `T_child` | 4173.713080168777 |
| `credit_lost` | 1947.9596599618444 |
| `mean_credit_of_removed_dots` | 0.025284714112769103 |
| `credit_bar_at_child` | 0.052 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h19-5-d2.8_0.2600.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 77041.0 |
| `score_change` | 0.0678 |
| `T_parent` | 6761.30001247972 |
| `T_child` | 5051.350210970465 |
| `credit_lost` | 1709.949801509255 |
| `mean_credit_of_removed_dots` | 0.0221953219910081 |
| `credit_bar_at_child` | 0.052 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h19-5-d2.8_0.2600.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 77041.0 |
| `score_change` | 0.0678 |
| `T_parent` | 8040.554557177919 |
| `T_child` | 6806.624472573841 |
| `credit_lost` | 1233.9300846040787 |
| `mean_credit_of_removed_dots` | 0.016016537747486126 |
| `credit_bar_at_child` | 0.052 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_d28-poisson-offcat_0.2600.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 77041.0 |
| `score_change` | 0.0678 |
| `T_parent` | 5764.144144590246 |
| `T_child` | 3683.145550711784 |
| `credit_lost` | 2080.9985938784616 |
| `mean_credit_of_removed_dots` | 0.02701157297904313 |
| `credit_bar_at_child` | 0.052 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_d28-poisson-offcat_0.2600.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 77041.0 |
| `score_change` | 0.0678 |
| `T_parent` | 6121.672740130622 |
| `T_child` | 4173.713080168777 |
| `credit_lost` | 1947.9596599618444 |
| `mean_credit_of_removed_dots` | 0.025284714112769103 |
| `credit_bar_at_child` | 0.052 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_d28-poisson-offcat_0.2600.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 77041.0 |
| `score_change` | 0.0678 |
| `T_parent` | 6761.30001247972 |
| `T_child` | 5051.350210970465 |
| `credit_lost` | 1709.949801509255 |
| `mean_credit_of_removed_dots` | 0.0221953219910081 |
| `credit_bar_at_child` | 0.052 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_d28-poisson-offcat_0.2600.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 77041.0 |
| `score_change` | 0.0678 |
| `T_parent` | 8040.554557177919 |
| `T_child` | 6806.624472573841 |
| `credit_lost` | 1233.9300846040787 |
| `mean_credit_of_removed_dots` | 0.016016537747486126 |
| `credit_bar_at_child` | 0.052 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 80932.0 |
| `score_change` | 0.0786 |
| `T_parent` | 5764.144144590246 |
| `T_child` | 3622.0946750867274 |
| `credit_lost` | 2142.049469503518 |
| `mean_credit_of_removed_dots` | 0.02646727461947707 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 80932.0 |
| `score_change` | 0.0786 |
| `T_parent` | 6121.672740130622 |
| `T_child` | 4134.206461980884 |
| `credit_lost` | 1987.4662781497373 |
| `mean_credit_of_removed_dots` | 0.02455723666967006 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 80932.0 |
| `score_change` | 0.0786 |
| `T_parent` | 6761.30001247972 |
| `T_child` | 5050.3867884631645 |
| `credit_lost` | 1710.9132240165554 |
| `mean_credit_of_removed_dots` | 0.021140132753627187 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h27-4-d2.8_0.2708.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 80932.0 |
| `score_change` | 0.0786 |
| `T_parent` | 8040.554557177919 |
| `T_child` | 6882.747441427725 |
| `credit_lost` | 1157.8071157501945 |
| `mean_credit_of_removed_dots` | 0.014305924921541473 |
| `credit_bar_at_child` | 0.05416 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 5764.144144590246 |
| `removed_mass` | 83477.0 |
| `score_change` | 0.0856 |
| `T_parent` | 5764.144144590246 |
| `T_child` | 3571.5128909128543 |
| `credit_lost` | 2192.631253677391 |
| `mean_credit_of_removed_dots` | 0.02626629195679518 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 8000.0 |
| `removed_mass` | 83477.0 |
| `score_change` | 0.0856 |
| `T_parent` | 6121.672740130622 |
| `T_child` | 4097.641184193808 |
| `credit_lost` | 2024.0315559368137 |
| `mean_credit_of_removed_dots` | 0.024246577571508485 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 12000.0 |
| `removed_mass` | 83477.0 |
| `score_change` | 0.0856 |
| `T_parent` | 6761.30001247972 |
| `T_child` | 5038.8973783406045 |
| `credit_lost` | 1722.4026341391154 |
| `mean_credit_of_removed_dots` | 0.020633259869654103 |
| `credit_bar_at_child` | 0.05556 |

| quantity | value |
|---|---|
| `parent` | scored_h19-5-solid_0.1922.tif |
| `child` | scored_h33-2-b2_0.2778.tif |
| `assumed_nG` | 20000.0 |
| `removed_mass` | 83477.0 |
| `score_change` | 0.0856 |
| `T_parent` | 8040.554557177919 |
| `T_child` | 6921.409766634196 |
| `credit_lost` | 1119.1447905437235 |
| `mean_credit_of_removed_dots` | 0.013406624465945392 |
| `credit_bar_at_child` | 0.05556 |

10 of 24 artifact pairs are exact nestings.

**Caveats recorded by the inversion itself.**

* Reported scores are owner-reported public-leaderboard numbers, not organiser receipts held in this repo.
* Public-leaderboard scores are on the PUBLIC test chunk; the initial prize round is scored on the PRIVATE chunk, so |G| inferred here is the public-chunk truth size.
* The M=0 corner is pessimistic; real M>0 makes the inferred T smaller and |G| smaller.


The hidden public-chunk truth is four to ten times **sparser** than the given catalogue (1.18 % of the footprint). Every holdout in this repository is prevalence-matched to that bracket for this reason.

## 6. The holdout sweep and the conformal selection

`scripts/run_sweep_a.py` → `evidence/sweep/sweep_a.json`; `scripts/run_conformal.py` → `evidence/conformal/selection.json`.

21,539 scored configurations: 5 recipes × 3 spacings × 6 densities × 2 flank buffers × 5 instruments × 25 blocks.

### The shipped 0.2778 artifact, on the same folds

| instrument | mean DTI | min | max | blocks |
|---|---|---|---|---|
| `PM0200` | 0.0048 | 0.0000 | 0.0177 | 25 |
| `PM0112` | 0.0041 | 0.0000 | 0.0188 | 24 |
| `PM0294` | 0.0054 | 0.0012 | 0.0215 | 25 |
| `A1` | 0.0040 | 0.0002 | 0.0098 | 20 |
| `A2` | 0.0070 | 0.0016 | 0.0177 | 25 |

Near zero on every fold, for a reason stated plainly in `IR-47-PROXY-02`: its dots were deleted from within 2 px of the *whole* catalogue, and the fold truth *is* catalogue. The instrument is measuring the artifact's designed anti-correlation with its own truth. It is a valid comparison only for arms that do not prune near the catalogue — which is why the flank-buffer decision is justified from the organiser's nested pair instead.

### Best operating points per instrument (calibration-half mean)

| instrument | recipe | op | mean DTI | min DTI |
|---|---|---|---|---|
| `PM0200` | `R4_scarp9_topo_reg_mag` | `s2_d24_b2` | **0.0887** | 0.0491 |
| `PM0112` | `R2_scarp9_topo` | `s2_d7.37_b2` | **0.0621** | 0.0000 |
| `PM0294` | `R4_scarp9_topo_reg_mag` | `s2_d24_b2` | **0.1110** | 0.0747 |
| `A1` | `R2_scarp9_topo` | `s2_d7.37_b2` | **0.0572** | 0.0162 |
| `A2` | `R4_scarp9_topo_reg_mag` | `s2_d40_b2` | **0.1975** | 0.1375 |

### The chosen operating point

`R2_scarp9_topo` at `s2.8_d7.37_b2`, selected by max-min normalised conformal floor across instruments (worst = `PM0294` at 0.9203871827810638).

| instrument | calibration mean | conformal floor at α |
|---|---|---|
| `PM0200` | 0.0968 | 0.0448 |
| `PM0112` | 0.0554 | 0.0282 |
| `PM0294` | 0.1008 | 0.0561 |
| `A1` | 0.0541 | 0.0165 |
| `A2` | 0.1201 | 0.0717 |

### Top of the ranking under the declared rule

| recipe | operating point | mean-risk | worst norm. mean | worst norm. floor | worst instrument | calibration means by instrument |
|---|---|---|---|---|---|---|
| `R2_scarp9_topo` | `s2.8_d7.37_b2` (s=2.8, d=7.37, b=2.0) | **0.923** | 0.925 | 0.920 | `PM0294` | A1 0.0541, A2 0.1201, PM0112 0.0554, PM0200 0.0968, PM0294 0.1008 |
| `R4_scarp9_topo_reg_mag` | `s2.8_d7.37_b2` (s=2.8, d=7.37, b=2.0) | **0.824** | 0.836 | 0.813 | `A2` | A1 0.0488, A2 0.1085, PM0112 0.0517, PM0200 0.0932, PM0294 0.0931 |
| `R2_scarp9_topo` | `s2_d7.37_b0` (s=2.0, d=7.37, b=0.0) | **0.796** | 0.970 | 0.622 | `PM0112` | A1 0.0581, A2 0.1298, PM0112 0.0570, PM0200 0.1034, PM0294 0.1035 |
| `R2_scarp9_topo` | `s2_d7.37_b2` (s=2.0, d=7.37, b=2.0) | **0.795** | 1.000 | 0.591 | `PM0112` | A1 0.0583, A2 0.1298, PM0112 0.0587, PM0200 0.1040, PM0294 0.1057 |
| `R2_scarp9_topo` | `s2.8_d7.37_b0` (s=2.8, d=7.37, b=0.0) | **0.776** | 0.898 | 0.654 | `PM0112` | A1 0.0546, A2 0.1202, PM0112 0.0539, PM0200 0.0934, PM0294 0.0982 |
| `R4_scarp9_topo_reg_mag` | `s2.8_d7.37_b0` (s=2.8, d=7.37, b=0.0) | **0.675** | 0.824 | 0.526 | `PM0112` | A1 0.0485, A2 0.1083, PM0112 0.0484, PM0200 0.0895, PM0294 0.0910 |
| `R4_scarp9_topo_reg_mag` | `s4_d7.37_b2` (s=4.0, d=7.37, b=2.0) | **0.648** | 0.675 | 0.621 | `PM0112` | A1 0.0469, A2 0.0895, PM0112 0.0449, PM0200 0.0701, PM0294 0.0790 |
| `R3_scarp9_topo_reg` | `s2.8_d7.37_b0` (s=2.8, d=7.37, b=0.0) | **0.611** | 0.787 | 0.435 | `A1` | A1 0.0459, A2 0.1142, PM0112 0.0487, PM0200 0.0881, PM0294 0.0947 |
| `R3_scarp9_topo_reg` | `s2.8_d7.37_b2` (s=2.8, d=7.37, b=2.0) | **0.609** | 0.783 | 0.435 | `A1` | A1 0.0457, A2 0.1142, PM0112 0.0498, PM0200 0.0908, PM0294 0.0975 |
| `R2_scarp9_topo` | `s2.8_d4_b0` (s=2.8, d=4.0, b=0.0) | **0.600** | 0.721 | 0.479 | `A1` | A1 0.0540, A2 0.0936, PM0112 0.0501, PM0200 0.0909, PM0294 0.0831 |
| `R2_scarp9_topo` | `s2.8_d4_b2` (s=2.8, d=4.0, b=2.0) | **0.600** | 0.720 | 0.479 | `A1` | A1 0.0540, A2 0.0935, PM0112 0.0523, PM0200 0.0922, PM0294 0.0837 |
| `R2_scarp9_topo` | `s2_d4_b2` (s=2.0, d=4.0, b=2.0) | **0.590** | 0.718 | 0.462 | `PM0112` | A1 0.0567, A2 0.0932, PM0112 0.0512, PM0200 0.0953, PM0294 0.0832 |

Selection rule as declared in `evidence/conformal/selection.json`: hard pre-filters: (i) emitted mass must not exceed the algebraic ceiling S_max at which DTI can no longer reach the target, (ii) folds with truth < 50 px are dropped uniformly; then rank by 0.5*worst-normalised-calibration-mean + 0.5*worst-normalised-conformal-floor over the prevalence-matched instruments, ties broken toward the floor

Mass ceiling applied before ranking:

```json
{
 "target_dti": 0.3195,
 "assumed_nG_px": 8000,
 "assumed_coverage": 0.6,
 "s_max_px": 43117.37089201877,
 "s_max_density_per_1000": 8.44381512401019,
 "n_scored_domain_full_grid": 5106385,
 "formula": "S_max = G*(c/target - 0.8)/0.2",
 "sensitivity": {
  "G=5764_c=0.48": 20241.65258215962,
  "G=5764_c=0.6": 31066.065727699523,
  "G=5764_c=0.8": 49106.75430359937,
  "G=5764_c=1.0": 67147.44287949921,
  "G=8000_c=0.48": 28093.896713615017,
  "G=8000_c=0.6": 43117.37089201877,
  "G=8000_c=0.8": 68156.4945226917,
  "G=8000_c=1.0": 93195.61815336463,
  "G=10335_c=0.48": 36293.8028169014,
  "G=10335_c=0.6": 55702.253521126746,
  "G=10335_c=0.8": 88049.67136150235,
  "G=10335_c=1.0": 120397.08920187793,
  "G=15179_c=0.48": 53304.65727699529,
  "G=15179_c=0.6": 81809.8215962441,
  "G=15179_c=0.8": 129318.42879499217,
  "G=15179_c=1.0": 176827.0359937402
 },
 "operating_points_dropped": 90
}
```

## What the holdout can and cannot say

*It can* order fields and operating points, and it can certify a finite-sample floor **on that ordering instrument**. It reproduces the organiser's own flank-buffer effect in the right direction (b = 2 ≥ b = 0 on the mixed prevalence-matched folds, b = 0 ≥ b = 2 on the flanking-only folds), which is the independent check that it is not merely flattering the design.

*It cannot* forecast the public DTI. Its truth is drawn from the given catalogue, so it cannot reward a genuinely new fault that no compilation contains (`IR-47-PROXY-01`), and it is structurally invalid for arms that prune near the catalogue (`IR-47-PROXY-02`). Every floor on this site is labelled with the instrument it belongs to.

The one instrument that can forecast the public DTI is the organiser, and it charges a submission slot. The brief's rule is therefore enforced by construction: `scripts/build_submission_s3.py` reads the frozen choice from `evidence/conformal/selection.json` and never re-tunes it.
