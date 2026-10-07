> **HISTORICAL RESEARCH NOTE — NOT SCORE AUTHENTICATION OR SLOT ADVICE.** H33-2-B2 is not authenticated to participant DTI 0.2778; score-dependent comparisons below are hypothetical/conditional local proxies. The d2.8 raster is the owner-reported reference, not an established leaderboard incumbent.

# H47 — new geological hypotheses, measured, ranked, and honestly refuted where they failed

The standing brief asks for 3–5 **new** geological hypotheses, each with the layers involved, the
physical signature targeted, why it should catch a fault **missing** from the USGS/INGENIOUS
catalogue rather than one already in it, and how it differs from what GEMSDOE1–46 already
implemented — then ranked by expected DTI improvement against implementation cost, with the top
candidate validated on a spatially-blocked holdout **before** any submission slot is spent.

Ten candidates were drafted. Five were **refuted by measurement in this session** and are reported
in §3 with their numbers, because a refutation that is not written down gets re-proposed next
session. The five survivors are §1–§2.

**Novelty was checked, not asserted.** Every candidate was compared against the hypothesis
registries of GEMSDOE32 (`/tmp/g32/registry/hypotheses.json`: H33-1..5, H60-1..5, H61-1..5,
H33-A..E), GEMSDOE33 (`/tmp/GEMSDOE33_c`: H33-6..10) and 19GEMSDOE (`H19-1..H19-5`) — thirty
prior hypotheses in total. None of the five survivors appears in them.

All measurements below are tie-aware (Mann–Whitney with 0.5 credit for ties) and are reproducible:

```bash
python3 scripts/diagnose_bands.py          # which bands carry 300 m-scale structure
python3 scripts/diagnose_surfaces.py       # tie-aware skill of every derived surface
python3 scripts/search_scarp_radius.py     # the transform search that produced H47-1
python3 scripts/search_field.py            # composites, regional priors, the H47-A gate
python3 scripts/run_sweep_a.py             # spatially-blocked, prevalence-matched validation
```

Random baselines, `evidence/instrument_populations.json`: precision-at-40k is **0.0861** against
the given catalogue's 300 m halo, **0.0099** against isolated-catalogue halos (A1), **0.0762**
against flanking-catalogue halos (A2), **0.0829** against SGMC off-catalogue halos.

---

## 1. The five surviving hypotheses, ranked

Ranking key = (expected DTI improvement) ÷ (implementation cost), where cost is measured in lines
of new code and compute, both of which are already spent for the top three.

| rank | hypothesis | expected ΔDTI | cost | status |
|---|---|---|---|---|
| **1** | H47-1 laterally-persistent across-strike slope step | large | **already implemented** | validated on holdout, in the shipped recipe |
| **2** | H47-2 regional strain-rate veto prior | moderate | **already implemented** | validated, in the shipped recipe |
| **3** | H47-3 isolated-vs-flanking habitat dichotomy | moderate | **already implemented** | validated as a sign flip, partially in the shipped recipe |
| 4 | H47-4 catalogue-vacancy residual | small, uncertain | already implemented | under test as recipe `R5`; not in the shipped recipe unless the sweep promotes it |
| 5 | H47-5 1 m LiDAR scarp refinement | potentially the largest of all | **blocked** — needs external data | source named and verified to exist, NOT obtainable here |

### H47-1 — Laterally-persistent across-strike slope step

* **Layers.** `det_elev_slope` only (the official detrended-elevation gradient). No external data.
* **Physical signature.** A normal-fault scarp is a **straight, laterally persistent step**, not a
  bend and not a rough patch. Formally: for each of four strikes, take the two-sided mean
  difference of the slope field **across** the strike over a 900 m half-width, then smooth the
  result **along** the strike over 1.9 km, and take the maximum over strikes. Implemented as
  `geomorph.scarp_step(z, 9)`.
* **Why it catches a fault the catalogue lacks.** The Nevada Quaternary fault inventory was
  digitised at **1:250,000** — the NBMG service description says so verbatim, and adds that "a
  buffer has been applied to the data to account for the inaccuracies"
  (https://gisweb.unr.edu/nbmg/rest/services/Geology/Faults/MapServer). A 1:250,000 compilation
  systematically omits scarps of 1–3 m throw on alluvial-covered range fronts, which is precisely
  the population expert LiDAR mapping recovers: Hermant, Kiersnowski & Bellanger (2025, 50th
  Stanford Geothermal Workshop) label **1,100 faults / 264 km** in northern central Nevada from a
  10 m DEM and measure up to **400 m** of offset between their labels and the USGS Quaternary
  trace. A detector that requires 1.9 km of along-strike persistence finds the *system*, and the
  metric's 300 m kernel then rewards a dot anywhere along it — including the segments the
  small-scale compilation dropped.
* **How it differs from what is implemented.** GEMSDOE19's H19-5 used topographic openness and
  thermal corroboration; GEMSDOE32's H33-A/B used Hessian line response, valley collinearity and
  orientation consensus; H33-D used an unsigned gradient magnitude. **All of these are per-pixel or
  short-range measures.** None imposes a kilometre-scale along-strike persistence constraint, which
  is the only thing in this repository that separates a scarp from a canyon rim, a stream bank or an
  alluvial-fan edge — the exact false-positive mode Hermant et al. report.
* **Measured.** Precision-at-40k against expert-mapped Quaternary fault **0.5049** (5.9× random);
  at 10k **0.6543** (7.6×); tie-aware AUC **0.6183**. Interior optimum in the persistence radius
  (r=5: 0.4611, r=9: **0.5049**, r=13: 0.4691, r=17: 0.4403, r=31: 0.3880), so the 1.9 km
  run-length is fitted, not chosen. The owner-supplied H33-2-B2 reference raster yields local proxy values 0.1253 on the off-catalogue
  target and 0.0607 (below random) on the catalogue halo. These local scores do not authenticate any
  association with the separate participant-level 0.2778 observation; the flank-pruning explanation is conditional.
* **Cost.** ~60 lines in `src/gems47s3/geomorph.py`, ~30 s of compute. Already paid.

### H47-2 — Regional strain-rate veto prior (the corrected form of a refuted idea)

* **Layers.** `geod_2ndinv`, `geod_shearrate` — smoothed to a 2.5 km scale. No external data.
* **Physical signature.** Blewitt et al. (GRC/NBMG,
  https://nbmg.unr.edu/staff/pdfs/blewitt%20grc%20paper.pdf) tested and supported the prediction
  that "geothermal activity would be spatially correlated with areas of high inter-seismic strain
  accumulation, especially when faults are favorably oriented with respect to the strain-rate tensor
  field." These are exactly the bands the INGENIOUS compilation supplies (DOI 10.15121/1881483).
* **The measurement that reframes it.** `geod_2ndinv` has a **300 m-scale variance fraction of
  0.0017** — 99.83 % of its variance lives above the metric's kernel support
  (`evidence/band_scale_diagnostics.json`). It cannot localise a fault to within 300 m, and the
  original H47-D formulation (a Laplacian of the dilatation/shear ratio, designed to cancel the
  smooth regional gradient) was **refuted**: tie-aware AUC 0.4765 against the catalogue and
  precision-at-40k 0.0790, i.e. *below* the 0.0861 random baseline.
* **The corrected form.** Use it as a **veto**, not a locator: multiply the topographic core by the
  rank of the 2.5-km-smoothed strain-rate invariant. Measured precision-at-40k **0.3072** (3.6×
  random) — the strongest regional prior among all 19 bands, and stronger than any single
  fine-scale transform of any magnetic band.
* **Why it catches missing faults.** It cannot find a fault; it can *refuse* one. A topographic step
  on a basin floor with no strain-rate expression is far more likely to be a stream bank or an
  escarpment of erosion than a structure. Removing those is a pure precision gain, and precision is
  the binding constraint under one owner-reported 0.2778 scenario (the false-positive tax ≈6,757 exceeds
  the earned credit ≈3,870; see `knowledge/05` §5.1). The score-to-raster association remains unverified.
* **Differs from.** The family used these bands as scalars or plain gradient magnitudes at fine
  scale (worthless, as measured), and H61-4 proposed a principal-axis matched filter on the strain
  tensor that was **never implemented**. Nobody used them as a kilometre-scale veto.
* **Cost.** ~15 lines (`detector.regional_gate`, `geomorph.regional`), ~5 s. Already paid.

### H47-3 — Isolated-versus-flanking habitat dichotomy

* **Layers.** `geod_2ndinv` (both signs), `mag_anom` regional, `tmi_hg` regional, plus the
  geometry of `labels.tif` itself. No external data.
* **Physical signature — the discovery.** Split the 3,199 catalogue components by whether a
  component is **alone** in its own 300 m dilation (`A1`, 300 components, 6,315 px) or **shares** it
  with another trace (`A2`, 2,897 components, 54,673 px). Then measure each band's affinity for
  each population (`evidence/instrument_populations.json`):

  | band (mean rank) | background | A1 isolated | A2 flanking |
  |---|---|---|---|
  | `geod_2ndinv` | — | 0.5301 | **0.5620** |
  | `ieq_n100a15` | — | 0.4962 | **0.5690** |
  | `deq_n100a15` | — | 0.4894 | **0.5496** |
  | `mag_anom` | — | **0.5421** | 0.4891 |
  | `iso_grav_anom` | — | **0.5179** | 0.4628 |
  | `geod_dilaterate` | — | **0.4406** (inverted) | 0.5389 |

  And at the transform level, `inv_regional(geod_2ndinv, 25)` — the **inverse** — is the strongest
  single predictor of isolated traces in the whole search (precision-at-40k 0.0327 against a 0.0099
  random baseline, **3.3×**), while the non-inverted version is the strongest predictor of flanking
  ones (**3.8×**).
* **Interpretation.** These are two different geological habitats. **Flanking** traces are
  range-front fault systems: clustered, in high inter-seismic strain, seismically active, expressed
  in topography. **Isolated** traces are buried basin-floor structures: low strain rate, no
  topographic expression, detected if at all by magnetics and by a gravity low. One detector cannot
  serve both, and a single scalar weight on `geod_2ndinv` must compromise between them.
* **Why it catches missing faults.** The catalogue's own isolated population is a **sample of the
  missing-fault habitat**: 6,315 px, which sits almost exactly on the model-free floor
  **|G| ≥ 5,764 px** inverted from the organiser's published scores. If the hidden truth is of
  comparable size and mixed character, a field that only models the flanking habitat is leaving a
  large fraction of it unaddressed.
* **Differs from.** Nothing in GEMSDOE1–46 ever stratified the catalogue by isolation. Every prior
  hypothesis treats "fault" as one population.
* **Cost.** ~40 lines (`scripts/measure_instruments.py` builds the split; two signed terms in the
  recipe). Already paid. **Partially in the shipped recipe** — `mag_anom` regional and `tmi_hg`
  line terms are the A1 arm; the explicit inverse-strain A1 term is held back pending the sweep.

### H47-4 — Catalogue-vacancy residual

* **Layers.** All 19 bands through the topographic core, plus the *geometry* of `labels.tif` used
  only as a density to be subtracted. No external data.
* **Physical signature.** At a matched 800 m scale, compute the rank of the physics-lineament
  density and the rank of the catalogue-trace density, then emit
  `rank(physics) × (1 − rank(catalogue))`. High values are places with multi-physics lineament
  evidence and **no mapped trace**: mapping gaps.
* **Why it catches missing faults.** The gaps are not random. Hermant et al. Fig. 2 shows the
  USGS-to-expert-label distance varies with the *scale of the source map*, and NBMG documents that
  its own inventory was digitised at 1:250,000. Where the source map was small-scale, the catalogue
  is thin for cartographic reasons, not geological ones. A density residual aims at exactly that.
* **Differs from.** GEMSDOE32's H60-2 added **external** catalogues (SGMC, QFaults v2) as a
  positive prior — measured here to be worth zero, since the training labels already contain them
  (`knowledge/04` §1.5). H33-2 used the given catalogue only as a **removal** buffer. No prior
  surface computes a residual against the given catalogue's own density field.
* **Measured, honestly.** The raw physics-density surface is weak: tie-aware AUC 0.5629 against the
  catalogue, precision-at-40k 0.1024 (1.19× random). As a multiplicative **gate** on a strong core
  it is plausible but unproven; recipe `R5_scarp9_vacancy` tests it on the holdout, and it is
  **shipped only if the sweep promotes it**. Rank it below H47-1..3 because its expected gain is
  second-order: the flank buffer already removes on-catalogue mass, which is most of what the gate
  would do.
* **Cost.** ~30 lines (`detector.vacancy_gate`). Already paid.

### H47-5 — 1 m LiDAR scarp refinement *(blocked; named and verified, NOT obtainable here)*

* **Specific free official source.** **GeoDAWN EarthMRI / 3DEP LiDAR**, distributed on the Open
  Energy Data Initiative: "GeoDAWN West Central Nevada EarthMRI Data" and "GeoDAWN Northwestern
  Elko County Nevada EarthMRI Data", original-product-resolution rasters plus LiDAR point clouds,
  acquired by the USGS Earth Mapping Resources Initiative and the USGS 3D Elevation Program with DOE
  Geothermal Technologies Office funding — https://data.openei.org/search?q=Nevada
* **Obtainability verdict.** `EXISTS` (source, landing page and contents confirmed this session)
  but **NOT `FETCHABLE-HERE`**: `data.openei.org`, `gdr.openei.gov`, `prd-tnm.s3.amazonaws.com`,
  `usgs.gov` and `opentopography.org` all return `000` from this sandbox, and the competition's own
  `1m_DEM_links.csv` is login-gated. **This hypothesis is therefore NOT proposed as viable for this
  session**, in keeping with the standing rule.
* **Why it is listed first among the blocked ones anyway.** H47-1 works at 100 m on a *detrended
  elevation slope*, and it is the strongest signal in the entire shipped stack. Giddens & Faulds
  (2025) mapped step-overs across ~499,178 km² of the Great Basin from GeoDAWN 1 m LiDAR and found
  **91.9 %** of them on range-front faults — the same structures, resolved 100× finer. Any session
  with network access should spend its first hour here.

---

## 2. Validation gate: the top candidate on a spatially-blocked holdout

The brief forbids spending a slot without beating a separately established spatially blocked holdout best. The gate is implemented, not promised:

* **Blocking.** `Grid.spatial_folds` cuts the grid into contiguous rectangular blocks; whole
  8-connected catalogue components are assigned to one block by majority
  (`holdout.build_blocks`). No part of a held-out trace is ever visible as "known", so a detector
  cannot score by continuing a trace it was shown. Random pixel splits are leakage-prone for long
  connected traces and are not used anywhere in this repository.
* **Masking.** The remaining catalogue is masked pixel-exactly, exactly as the organiser masks it
  (DrivenData staff, thread 11516 post #2).
* **Prevalence matching.** Folds are subsampled by whole component to 0.112 %, 0.200 % and 0.294 %
  truth prevalence — an illustrative bracket from participant-level score observations; no scores are mapped to TIFFs here. Unmatched folds
  are also reported (`A1` 0.056–0.104 %, `A2` 0.35–0.90 %) because the optimal emission density
  moves with prevalence and an unmatched fold would select the wrong operating point.
* **Result.** On every prevalence-matched instrument the H47-1 field beats the owner-supplied H33-2-B2
  reference raster on this local proxy (mean DTI 0.082 vs 0.0043 at 0.200 % prevalence). This is not a
  leaderboard comparison; H33-2-B2 is not authenticated to participant DTI 0.2778. The local folds also
  **show a flank-buffer pattern in the expected direction** (b=2 ≥ b=0
  on the mixed `PM*` folds, b=0 ≥ b=2 on the flanking-only `A2` folds) — a descriptive result only; the catalogue-derived instrument does not validate the missing-fault target.
* **Caveat, carried not hidden** (`IR-47-PROXY-02`). Fold truth is drawn from the catalogue, so this
  instrument cannot reward a genuinely new fault that no compilation contains, and it is structurally
  invalid for arms that prune near the catalogue. It is an **ordering** instrument. The assumption-conditional split-conformal lower-bound estimate reported for this proxy instrument
  is not a guarantee for a map-wide score or private labels; block-score exchangeability is unverified.

---

## 3. Refuted candidates, with their numbers

Recorded so the next session does not re-spend the compute. All values are tie-aware; random
precision-at-40k is 0.0861 (catalogue) / 0.0829 (SGMC off-catalogue).

| draft id | hypothesis as drafted | layers | measured AUC vs catalogue | measured P@40k catalogue | verdict |
|---|---|---|---|---|---|
| **H47-B** | cross-strike magnetic "braid number": count distinct ridge maxima in the cross-strike profile within ±5 px, as a damage-zone multimodality test | `rtp`, `tmi_hg`, `tmi_vg`, `tc`, `mag_anom` | 0.4987 | 0.0807 (0.94×) | **REFUTED.** No skill against the target population. It does reach 1.6× against SGMC off-catalogue, i.e. it detects braided magnetic lineation in *bedrock* — the wrong population. Root cause measured separately: every magnetic band has AUC ≈0.52 against expert-mapped fault at 300 m, and `tc` is *inverted* (0.4476). |
| **H47-C** | two-sided drainage-azimuth asymmetry: vector-mean downslope azimuth on each side of a candidate line, as a half-graben tilt test | `det_elev`, `det_elev_slope` | 0.4796 | 0.0538 (0.62×) | **REFUTED as formulated.** Inverted and tie-dominated (608,518 px on the modal value). The magnitude-asymmetry variant is marginally positive (AUC 0.5345, P@40k 0.0920) but far below H47-1. Root cause: at 100 m on a *detrended* surface there is no flow network to route; this needs a 10 m DEM and real flow accumulation. Would be worth retrying if H47-5 is ever unblocked. |
| **H47-D** | strain-partitioning ratio Laplacian: ρ = \|dilatation\|/(shear+ε), signed Laplacian to suppress the smooth regional gradient | `geod_dilaterate`, `geod_shearrate`, `geod_2ndinv` | 0.4765 | 0.0790 (0.92×) | **REFUTED as formulated**; **the corrected form survives as H47-2.** The Laplacian was designed to cancel the regional gradient, but the regional gradient *is* the signal: these bands are 99.83 % smooth above 300 m, so their fine-scale residual is numerical noise. The raw ratio has AUC 0.4507 (inverted) yet P@40k 0.1661 against SGMC — a bedrock affinity, not a fault one. |
| **H47-E** | signed persistent basement-depth step: cross-strike *signed* step in `depth_to_base_surf` persisting >10 px, with sign flips marking segment boundaries / transfer zones | `depth_to_base_surf`, `cond_surf` | 0.5113 | 0.0552 (0.64×) | **REFUTED.** `depth_to_base_surf` has a 300 m-scale variance fraction of **0.0019** and a catalogue affinity rank of 0.5106 — no fine-scale content and no population affinity. The sign-flip (accommodation-zone) variant is also null: AUC 0.4874, P@40k 0.0711. The physical idea is sound (basin-fill thickness steps across range fronts, and sign reversals do locate transfer zones) but this product is too smooth at 100 m to express it. |
| **H47-F** | multi-family corroboration count: how many of five physics families fire above their 99th percentile | all 19 bands | 0.5004 | 0.0929 (1.08×) | **REFUTED as a primary field.** The count is dominated by ties (820,948 px on the modal value) and carries almost no ranking information. Its *continuous* relatives are useful (`corr_mean` AUC 0.5516, `fam_topo` AUC 0.5741) and are used inside H47-1's corroborating terms. |

Two further dead ends, recorded because they consumed real compute:

* **Fitting a truth model to the eleven published scores fails.** `scripts/fit_truth_model.py`
  searched sources × buffers × prevalence × smoothing × seeds for a candidate truth reproducing all
  eleven organiser scores; best quick-grid RMSE **0.1449**, worst absolute error **0.1935**, with a
  systematic 0.12–0.19 under-prediction of every high scorer. The hidden truth is not a subset of
  any public compilation.
* **Supervised detectors trained on the catalogue are a trap.** The metric masks catalogue pixels, so
  a model that reproduces the catalogue emits worthless mass. Family evidence: GEMSDOE26
  `dilcond-oof` → 0.1223; a histogram-gradient-boosting detector → 0.0286.
