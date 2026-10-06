# H47-C research hypotheses — frozen before model implementation

Created 2026-10-06 UTC. Read README and the complete standing brief before working.
Core values: **Maximize P(Win)** and **Own the Outcome**. No automated competition uploads.

## Source and novelty boundary

The competition predicts **fault traces**, not geothermal vents or proven reservoirs. Fault presence
alone does not establish heat, fluid, permeability, or commercial viability. The official task and
about pages explain this distinction:
- https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/

The repository has already tested catalogue-flank/tip hypotheses, magnetic persistence,
radiometric-ratio halos, SGMC transfer, and leaderboard-fitted strain/alteration/thermal fields.
H47-B and H47-GSA failed their gates. Do not re-label them as new ideas. GEMSDOE45 already has
phase-parity and Kaplan–Meier tip methods. GEMSDOE46 has scarp/radiometric fusion and a
catalogue-supervised lineament model. Therefore “use LiDAR”, “use a boosted tree”, “grow tips”,
or “combine multiple layers” is **not** a novel hypothesis by itself.

The following ranks are qualitative research priorities, **not numerical DTI forecasts**. Each
is untested in this checkout at the time this document was written. Wider-family novelty is bounded
by accessible methods, not an exhaustive assertion about all competitors or unpublished code.

| Rank / ID | Specific layers | Physical signature and transform | Why it might find missing rather than merely repeat known faults | Distinction from existing code; confounders | Expected improvement / cost / feasibility |
|---|---|---|---|---|---|
| **1 · H47-C1: affine-detrended scarp profile versus channel profile** | Raw `det_elev` (training band 12), `det_elev_slope` (19), `iso_grav_anom` (13); all 19 raw bands only for a shared comparator. | Fit an odd, smoothed step profile after projecting out intercept and regional linear slope, in four orientations and two fixed widths. Contrast its residual-normalized response against an even valley/ridge template. Measure adjacent along-strike profile consistency; use gravity-normal agreement as a separate covariate, not a depth inversion. | A degraded, low-amplitude normal-fault scarp may be missed in older map compilations. An odd topographic step can persist where an amplitude-only ridge detector confuses channels, lithologic ridges, and relief. No catalogue-distance feature or prior submission geometry draws this field. | Earlier code uses gradients, Hessian/scarp maxima, scale persistence, catalogue geometry, or fitted proximity. It does not fit a slope-orthogonal odd step and competing even channel model to a transverse profile. This is a coarse-resolution test inspired by scarp physics, **not** a 1 m diffusion-age implementation. Channels, terrace edges, roads, landslides, and displaced/non-normal faults remain confounders. | **Moderate, uncertain**; highest information per CPU minute. **Low–medium**; raw bands restored and SHA-256 pinned. **Test first.** |
| **2 · H47-C2: offset, not coincident, geophysical contacts** | `iso_grav_anom`, `tmi` / `rtp`, `cond_surf`, `depth_to_base_surf` from the raw stack. | Cross-normal lagged gradient correlation and sign consistency across 100–800 m offsets, after removal of local linear trends; penalize zero-lag compositional boundaries. | A dipping covered contact can have laterally offset expressions at different sensing depths, unlike a perfectly co-located surface lithology edge. | The repository's independent raw gradients performed poorly; this targets *relative phase and spatial lag*, not gradient size or Euler depth. GEMSDOE32 has dip-projection work, so only this explicit lag-consistency test would be new locally. Lithology can also create offsets. Band 15's physical interpretation conflicts between mirrored metadata and the official problem description; resolve before claiming basement depth. | **Low–moderate, high variance**; **medium** cost. Bytes available, interpretation unresolved. **Conditional, not implemented now.** |
| **3 · H47-C3: radiometric compositional boundary as a negative control** | GeoDAWN `rad_K`, `rad_Th`, `rad_U` mirror; detrended terrain profiles and magnetic anomaly. | Fit local compositional contrasts, then down-rank magnetic contacts with a compositional boundary but no step-profile evidence. Test with and without the rejection term at matched mass. | Suppressing ordinary lithologic contacts may increase the precision of off-catalogue structural picks rather than add more magnetic edges. | H1 used ratios as an alteration detector; H47-GSA fitted low Th/K; GEMSDOE46 uses radiometrics as positive corroboration. This is an explicit **false-contact rejection** experiment. Altered genuine faults can themselves make compositional boundaries; never hard-delete without validation. | **Low–moderate**, precision-oriented; **low–medium** cost. Restored, quantized mirrors are available, but ratio magnitude is not physical concentration. **Deferred.** |
| **4 · H47-C4: paleodischarge-to-structure hydrologic residual** | DOE INGENIOUS **Paleo Geothermal Features** sinter/tufa points or polygons; official terrain and independent structural profiles. | Remove modern drainage/elevation bias, then find coherent topographic discontinuities near relict discharge deposits rather than distance-to-hot-spring alone. | Inactive or relocated discharge may preserve evidence for a fluid conduit without a present hot spring or a catalogued Quaternary scarp. | Existing code uses hot/warm well/spring proximity and volcanic vents, not drainage-conditioned relict deposits. Tufa need not imply high-temperature geothermal activity; fossil deposits are not new-fault labels. | **Low–moderate**, sparse evidence; **medium** cost. Official free CC BY 4.0 archive is listed at https://gdr.openei.org/files/1391/paleo_geothermal_regional.zip (82.04 kB on the source page). Direct sandbox HTTPS acquisition failed. **Not viable for validation until downloaded, licensed, and footprint coverage counted.** |
| **5 · H47-C5: signed 1 m scarp occupancy, not 100 m max pooling** | USGS 3DEP 1 m DEM tiles, not merely the twelve already-pooled LiDAR descriptors. | Fit a diffusion-inspired transverse step after planar-background removal; aggregate the *fraction* and along-strike connected length of agreeing subpixel profiles into each 100 m cell. | Small or vegetation-obscured degraded scarps may have low cell-average relief but repeated subpixel evidence. Occupancy suppresses isolated high-curvature speckles. | Existing LiDAR mirrors contain maxima/means of hand-crafted descriptors. They do not retain the count of profile fits or spatial connectivity within a cell. Requires raw elevation; cannot reconstruct it from max-pooled channels. Roads, water edges, and processing seams require negative controls. | **Potentially highest long-term**, not a claimed score increase; **high** I/O cost. Free official source: https://www.usgs.gov/3d-elevation-program and competition `1m_DEM_links.csv`. Public source availability is verified; complete tile bytes/coverage are **not acquired here**. **Conditional future experiment**, not an immediate viable claim. |

## Scientific basis and limits

1. The official GeoDAWN release distinguishes aeroradiometric surface-composition information from
   aeromagnetic subsurface-structure information, and documents acquisition-height/flight-line
   effects: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
   (DOI 10.5066/P93LGLVQ, CC0). This supports confounder analysis, not a fault guarantee.
2. Sare et al. (2019), *Regional-Scale Detection of Fault Scarps and Other Tectonic Landforms*,
   https://doi.org/10.1029/2018JB016886, describes curvature templates based on scarp diffusion at
   **≤2 m** resolution. H47-C1 does not reproduce that paper at 100 m or infer morphologic ages.
3. Hermant et al. (2025), supplied by the competition's about page,
   https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2025/Hermant.pdf, describes mapping
   heterogeneity, fault-controlled geothermal systems, and faults that can also be fluid barriers.
   Its reported map discrepancies are study-specific, not measured label error in this checkout.
4. The official INGENIOUS record https://gdr.openei.org/submissions/1391 lists paleogeothermal
   deposits, thermal observations, QFaults geometry and other features with CC BY 4.0 attribution.
5. USGS now lists actual QFFD GIS geometry at
   https://earthquake.usgs.gov/static/lfs/nshm/qfaults/Qfaults_GIS.zip and retires the old search
   interface (26 February 2026): https://www.usgs.gov/programs/earthquake-hazards/faults.
   A local centroid-summary CSV is not trace geometry. Known traces are not new-fault truth.
6. DrivenData staff explicitly **withholds** test-data sources, types and coverage:
   https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527?print=true
   (23 September 2026, post 7). Do not assume labels were derived exclusively from LiDAR or geophysics.

## Frozen validation design for H47-C1

- Build a deterministic 16×16 spatial grid; every block core is inset by **20 pixels / 2 km**.
  This exceeds the 300 m metric support and the planned transverse-profile stencil. No label-derived
  feature, catalogue distance, coordinate, previous prediction, or leaderboard response enters the model.
- Assign *all* nonempty feature-supported blocks using a fixed seeded shuffle (seed 470610):
  50% training; the remainder split approximately equally among **selection, calibration, test**.
  Training label rows and samples come **only** from training cores. All assigned blocks, including
  empty-truth ones, remain in all-population reports. Record truth-bearing conditional summaries too.
- A common feature-support mask is defined from raw input masks and a **20 pixel erosion**; no edge
  created by nodata fills is allowed to emit. Compare on the same support and report excluded labels.
- Fit CPU histogram-gradient-boosted regressors with frozen settings: 150 iterations, learning rate
  0.06, 15 leaves, L2 2, min leaf 100, no early stopping, fixed seed; target = the public catalogue's
  triangular-kernel proximity on *training blocks only*. Deterministically sample up to 180,000 training
  pixels (all positive kernel pixels, capped at 90,000; uniform sample from the remainder). Weight
  samples by inverse sampling probability. No calibration/test data choose model settings.
- **Incumbent pool:** raw 19-band predictor; raw bands plus ordinary Gaussian elevation gradient,
  Hessian invariants and tensor coherence. Select the better by selection-block pooled DTI only.
  This establishes a **local comparable baseline**, not authentication of a live-score file.
- **Candidate:** the exact same raw-plus-standard features plus frozen signed-step/channel/profile
  consistency and gravity-alignment descriptors. The top hypothesis is the only new detector tested.
- Emission sweep: Euclidean minimum spacing **1.5, 2.8, 3.6, 4.6, 5.8 pixels**; binary confidence 1
  on selected cells. Per-block mass = round(37,654 × block support / full footprint support), minimum
  one where support exists; the same mass applies to all models and random controls. Fail if a budget
  cannot be met; do not silently reduce the mass. A fixed-seed uniform-score spaced control is required.
- Split-conformal prediction: predict each spacing's block DTI with its **selection mean**. For each
  calibration block take **max over the five spacings** of (selection mean − observed block DTI).
  At predeclared nominal coverage **90%**, use the **ceil((n_cal+1)×0.9)**-th order statistic,
  augmenting by +infinity when the rank exceeds n_cal. Subtract this common quantile and intersect
  each lower bound with [0,1]. This simultaneous score prevents calibration-based spacing selection
  from invalidating the bound. Choose the largest lower bound, then largest selection mean, then
  largest spacing. Baseline spacings are picked on selection data, not the candidate's test.
- State explicitly: the finite-sample statement concerns the vector of five DTI scores on **one future
  exchangeable public-catalogue block** conditional on fixed fitted models/selection centers. It is
  marginal prediction coverage, not a confidence interval for mean DTI, not a guarantee for every block,
  not a guarantee for the full pooled nonlinear DTI, and **not a private leaderboard guarantee**.
  Spatial/geological exchangeability is unverified. Prior adaptive leaderboard scores are not valid
  calibration observations. No fabricated 0.34837 or other positive certified floor.
- Locked-test screen: candidate pooled and unweighted mean DTI must exceed the selection-picked
  incumbent and fixed-seed random; ≥2/3 of truth-bearing test blocks must improve; selected proxy floor
  must be positive. Label count and at least 10 truth-bearing test blocks are required. Report all failures.
- A **secondary diagnostic** uses SGMC faults >300 m from the catalogue on the same test cores and
  compares candidate with raw/structural baseline, fixed random, and restored H33-2-B2 at matched mass
  (rank distances to H33 dots only for the comparator). SGMC has known target mismatch; never tune its
  exclusion to reproduce the leaderboard or treat it as private truth.
- Even a screen pass cannot certify official eligibility: input bytes are mirror-pinned, no organizer
  file-to-score receipt exists, private new-fault labels are absent, and exchangeability is not verified.
  **No weekly slot is used in this session.** Failed outputs may be published as conspicuous
  **RESEARCH ONLY / NOT PROMOTED** artifacts to satisfy reproducibility and download requirements.
- Freeze and hash this protocol plus implementation before held-out scoring; preserve receipts, per-block
  spacing history, exact byte/pixel fingerprints, controls and three review passes. Do not adjust the test
  gate, confidence level, target or spacing grid after reading results.
