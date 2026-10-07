# Knowledge base 03 — geothermal fault discovery: the verified literature

Reusable across sessions. **Every entry carries an official link.** Items marked
`[VERIFIED 2026-10-06]` were re-checked against the live source in this session; items marked
`[FAMILY LEDGER]` come from the GEMSDOE1–46 repositories' own source registries and were not
independently re-fetched here (the sandbox cannot reach every host — see §5).

---

## 1. The competition itself

| item | detail | link |
|---|---|---|
| Competition | The Geologic Enhanced Mapping System (GEMS) Prize Challenge, DrivenData #306 | https://www.drivendata.org/competitions/306/competition-doe-gems/ `[VERIFIED]` |
| Sponsor | U.S. DOE Office of Geothermal (OG), with the National Lab of the Rockies (NLR) | https://www.energy.gov/hgeo/articles/hydrocarbons-and-geothermal-energy-office-announces-300000-help-identify-hidden `[VERIFIED]` |
| Prize pool | $300,000; Initial Round $50 k + top 5 × $10 k; Final Round $100/70/40/25/15 k | competition page `[FAMILY LEDGER]` |
| Deadline | **3 December 2026** | DOE announcement: "submissions are due December 3, 2026" `[VERIFIED]` |
| Metric page | Distance-weighted Tversky, R = 300 m, α = 0.2, β = 0.8 | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ `[VERIFIED]` |
| Reference solution | PyTorch U-Net, `segmentation_models_pytorch` | https://github.com/drivendataorg/gems-prize-reference-solution `[VERIFIED]` |
| Two rounds, one submission | the same submission is scored against a private expert-labelled test set (Initial) and again against an expanded label set built from expert review of **all** submissions (Final); only the top five advance | https://www.thinkgeoenergy.com/us-doe-announces-prize-challenge-for-discovery-of-hidden-geothermal-systems/ `[VERIFIED]` |
| Explicit framing | "The challenge is to address incomplete and potentially inaccurate ground truth data, thus encouraging participants to submit predictions for what they **truly believe** are faults … as opposed to simply optimizing for the existing labels." | same thinkgeoenergy page, quoting the organisers `[VERIFIED]` |

That last line is the single most important sentence in this knowledge base. The organiser is
telling competitors that the label set is **not** the target. Every design decision in this
repository that trades local-proxy score for physical plausibility is justified by it.

### 1.1 Scoring clarifications (official staff answers)

* Known USGS/INGENIOUS fault pixels "are masked / excluded from evaluation, so they do not count
  towards penalty terms" — chrisk-dd, 2026-09-16,
  https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516 `[FAMILY LEDGER]`
* Post #4 of the same thread: there is **no buffer** around known faults. A predicted pixel near a
  known fault but far from new-fault truth is **fully penalised**. New-fault pixels may lie within
  300 m of a known trace. `[FAMILY LEDGER]`
* https://community.drivendata.org/t/11527 — the organisers will **not** disclose the data sources,
  fault types or coverage of the test faults; Phase-2 labels come from expert review of all
  Phase-1 submissions. `[FAMILY LEDGER]`

**Metric consequence:** in the stated off-catalogue target, known-catalogue pixels are not truth and prediction mass there can incur false-positive cost. Owner-reported H33-2-B2/H27-4 score labels are not organizer-authenticated to these rasters; no such score comparison is treated as verified here. See the corrected conditional analysis in `knowledge/05`.

---

## 2. Where the 19 bands come from

The band list matches, one for one, the contents of the **INGENIOUS Great Basin Regional Dataset
Compilation**:

> "Datasets consist of shapefiles, geotiffs, tabular spreadsheets, and metadata that describe:
> 2-meter temperature probe surveys, quaternary faults and volcanic features, geodetic shear and
> dilation models, heat flow, magnetotellurics (conductance), magnetics, gravity,
> paleogeothermal features (such as sinter and tufa deposits), seismicity, spring and well
> temperatures, spring and well aqueous geochemistry analyses, thermal conductivity, and fault
> slip and dilation tendency."

* Ayling, B. et al. (2022). *INGENIOUS – Great Basin Regional Dataset Compilation.* Geothermal
  Data Repository, GBCGE / NBMG / UNR. **DOI 10.15121/1881483**,
  https://gdr.openei.org/submissions/1391 `[VERIFIED 2026-10-06]`
* Project page: INnovative Geothermal Exploration through Novel Investigations Of Undiscovered
  Systems, 1 Feb 2021 – 30 Jun 2025, $10 M, collaborators USGS / UtahGS / IdahoGS / NREL / LBNL /
  NBMG / UNR — https://gbcge.org/current-projects/ingenious/ `[VERIFIED]`

Band-to-source mapping inferred from that list and the official band descriptions
(`training_features.tif` metadata, reproduced verbatim in `src/gems47s3/spec.py`):

| band | official description | INGENIOUS product |
|---|---|---|
| `tmi`, `rtp`, `tmi_hg`, `tmi_vg`, `mag_anom`, `tc` | total magnetic intensity and derivatives | magnetics |
| `iso_grav_anom`, `_slope`, `_hg`, `_vg` | isostatic gravity anomaly and derivatives | gravity |
| `cond_surf` | conductivity surface | magnetotellurics (conductance) |
| `geod_2ndinv`, `geod_shearrate`, `geod_dilaterate` | geodetic strain-rate tensor measures | geodetic shear and dilation models |
| `deq_n100a15`, `ieq_n100a15` | distance to / density of earthquakes (n = 100 km, a = 15°) | seismicity, earthquake density models |
| `det_elev`, `det_elev_slope` | detrended elevation and its slope | topography (GeoDAWN / 3DEP) |
| `depth_to_base_surf` | depth to basement surface | basin-fill thickness |

**Irregularity flagged:** `tc` is described in the raster metadata as *"Tilt angle **or** total
curvature — magnetic field derivative for edge detection"*. The competition's own data page lists
it as a top-of-crustal magnetic source depth estimate. The two are different quantities with
different units and different signs. Measured here: `tc` has tie-aware AUC **0.4476** against the
catalogue, i.e. *inverted* — catalogue pixels have systematically **low** `tc`. Whatever it is, it
is not an edge detector that fires on these faults, and it is excluded from every recipe.

### 2.1 The scientific basis of the geodetic bands

Blewitt et al., *Targeting of Potential Geothermal Resources in the Great Basin from Regional
Geodetic Strain Rate and Fault Slip Tendency*, GRC / NBMG —
https://nbmg.unr.edu/staff/pdfs/blewitt%20grc%20paper.pdf `[VERIFIED]`

> "geothermal activity would be spatially correlated with areas of high inter-seismic strain
> accumulation, especially when faults are favorably oriented with respect to the strain-rate
> tensor field."

This is the hypothesis `geod_2ndinv`, `geod_shearrate` and `geod_dilaterate` encode, and it is why
they carry real (if weak) signal: measured tie-aware AUC against the given catalogue is 0.5583,
0.5407 and 0.5276 respectively (`evidence/instrument_populations.json`) — the three strongest
smooth bands. It is also why they cannot *localise* anything: their 300 m-scale variance fraction
is 0.0017–0.0018 (`evidence/band_scale_diagnostics.json`), so they are 99.8 % smooth above the
metric's kernel support.

---

## 3. Fault detection from topography in the Basin and Range

### 3.1 Deep learning on LiDAR — the closest published analogue to this task

Hermant, C., Kiersnowski, C. & Bellanger, H. (2025). *Deep learning to map Quaternary faults in
northern central Nevada.* 50th Stanford Geothermal Workshop.
https://pangea.stanford.edu/ERE/pdf/IGAstandard/SGW/2025/Hermant.pdf `[FAMILY LEDGER — fetched, chunk 0 of 8]`

* Cited on the DrivenData "About" page — this is the organisers' own reference.
* 10 m 3DEP DEM; **expert manual labels: 1,100 faults / 264 km**, rasterised with a **50 m buffer**;
  fault-pixel proportion **6.5 %**; 128×128 px tiles; ~7,700 label images.
* siUNET (487,297 parameters) and FaultSEG; test PR-AUC **0.595** vs **0.449**; overfits after
  7 epochs.
* **Figure 2, right panel: the distance between USGS Quaternary faults and the TLS fault label can
  be up to 400 m.** Expert labels are *offset* from the given catalogue by up to 4 competition
  pixels. This is the empirical basis for hypothesis **H47-A** and for refusing to treat the
  catalogue as pixel-exact ground truth for the trace *position*.
* Documented failure mode: the models "falsely fire on coastline, canyon and stream morphology".
  This is the failure mode that `knowledge/02` shows an SGMC-selected field would walk straight
  into.

### 3.2 Structural settings that actually host geothermal systems

* Faulds, J.E., Coolbaugh, M. & Hinz, N. (2021). *Inventory of structural settings for active
  geothermal systems and late Miocene (<8 Ma) to Quaternary epithermal mineral deposits in the
  Basin and Range Province of Nevada.* **Nevada Bureau of Mines and Geology Report 58**, 26 p.
  `[FAMILY LEDGER — cited in the Seismica reference list, VERIFIED as a citation]`
* Giddens & Faulds (2025), step-overs across ~499,178 km² of the Great Basin using GeoDAWN 1 m
  LiDAR + 10 m 3DEP + NAIP: **91.9 % of identified step-overs are along range-front faults**;
  range-front step-overs are easier to see in steep gradients (an acknowledged detection bias).
  `[FAMILY LEDGER — abstract via web search]`
* Burgess, Q.P. & Faulds, J.E. (2023). *Characterizing a potential hidden geothermal system in
  Buffalo Valley, north-central Nevada.* `[VERIFIED as a citation in the Seismica reference list]`
* Paleoseismology of the Buffalo Valley, Buena Vista and southern Shoshone faults, central Basin
  and Range: "field and lidar observations indicate that deformation is distributed across
  **several parallel strands** that progressively displace alluvial fans."
  https://seismica.library.mcgill.ca/article/view/2648 `[VERIFIED]`

That last quote is the empirical basis for hypothesis **H47-B** (a damage zone is a *braid* of
sub-parallel strands, not one edge) — and it is a published observation from inside this province.

### 3.3 The geomorphometric transforms used, with their original citations

| transform | source | used here as |
|---|---|---|
| Local Relief Model (LRM) | Hesse, R. (2010), *Lidar detection of subsurface archaeological features*, Remote Sensing | `geomorph.lrm` |
| Topographic Position Index | Jenness, J. (2006), TPI applications, USDA/Forest Service | `geomorph.tpi` |
| Topographic openness | Yokoyama, R., Shirasawa, M. & Pike, R.J. (2002), *Visualizing topography by openness*, Photogrammetric Engineering & Remote Sensing 68(3):257–265 | `geomorph.openness` |
| Frangi/Sato line response | Frangi, A. et al. (1998), *Multiscale vessel enhancement filtering*, MICCAI; Sato, Y. et al. (1998) | `geomorph.line_response` |
| Structure tensor coherence / orientation | Bigun, J. & Granlund, G.H. (1987), *Optimal orientation detection of linear symmetry*, ICCV | `geomorph.orientation`, `geomorph.linearity` |
| Across-strike step persisted along strike | **this repository** — a scarp matched filter, not previously implemented in GEMSDOE1–46 | `geomorph.scarp_step` |

The last row is the transform that won the search (5.9× random precision at 40k, 7.6× at 10k;
`evidence/scarp_radius_search.json`). Its novelty is not the differential geometry — it is the
requirement that the step **persist along strike for ~1.9 km**, which is what separates a fault
scarp from a canyon rim, a stream bank or an alluvial-fan edge. Those are exactly the features
Hermant et al. report their models falsely firing on.

---

## 4. Split conformal prediction

Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R.J. & Wasserman, L. (2018).
*Distribution-Free Predictive Inference for Regression.* **JASA 113(523):1094–1111.**
DOI https://doi.org/10.1080/01621459.2017.1322365 · preprint https://arxiv.org/abs/1604.04173

The theorem used, verbatim in structure: with exchangeable calibration scores `s_1..s_n` and
`k = ceil((n+1)(1-α))`,

```
q_hat = the k-th smallest calibration score   (+inf if k > n)
P( s_new <= q_hat ) >= 1 - alpha              exactly, for every n, no distributional assumption
```

For a **lower** bound on a quantity `Y` (here DTI), score with `s = -Y`; the bound is then the
`k`-th **largest** `Y`. Two consequences this repository reports rather than hides:

* `k > n` ⇒ the bound does not exist. **A 90 % lower bound needs n ≥ 9 blocks; 95 % needs n ≥ 19**
  (`conformal.min_blocks_for_alpha`). With fewer usable blocks, no honest statement at that
  confidence level can be made at all.
* The guarantee is conditional on **exchangeability of the units**. The unit here is a spatial
  block, and geological blocks are not i.i.d. — the Basin and Range and the Walker Lane are
  different regimes. Every report therefore also carries the leave-one-block-out worst floor and a
  Dvoretzky–Kiefer–Wolfowitz/Massart mean floor,
  `eps = sqrt(log(2/alpha) / (2n))`, so a reviewer can see how much work the assumption is doing.

An earlier version of `src/gems47s3/conformal.py` used `k = ceil((n+1)α)` and the `k`-th *smallest*
value for the lower side. That returns a strictly larger number than the theorem supports and
therefore **over-states the guarantee**. It was caught by
`tests/test_conformal.py::test_empirical_coverage_meets_the_guarantee` (4,000 Monte-Carlo
repetitions against a lognormal) and fixed. Recorded here because an over-optimistic conformal
bound is exactly the kind of error that would let a submission slot be spent on a false claim.

---

## 5. Reachability from this environment (measured, not assumed)

| transport | status |
|---|---|
| `fetch_page` | works for drivendata.org, community.drivendata.org, pangea.stanford.edu PDFs, github.io |
| `web_search` | works |
| `git clone https://github.com/...` | works |
| `gh api` (metadata **and** raw blobs) | works — this is how the three official rasters were restored |
| `pip` from pypi.org | works |
| `curl` / `wget` to anything except pypi.org and github.com | **blocked** (`000`) |

Hosts confirmed unreachable by direct download in this sandbox: `github.io`, `drivendata.org`,
`dropbox.com`, `raw.githubusercontent.com`, `registry.opendata.aws`, `prd-tnm.s3.amazonaws.com`,
`sciencebase.gov`, `pangea.stanford.edu`, `earthquake.usgs.gov`, `services.azgs.arizona.edu`,
`gdr.openei.gov`, `data.openei.org`, `usgs.gov`, `opentopography.org`, `nbmg.unr.edu`.

**So "verified" here means the source, its DOI and its contents were confirmed through search and
through the family's own fetched copies — not that this sandbox downloaded the bytes.** Where a
hypothesis needs new external data, `knowledge/04` states explicitly which of these two levels of
verification was achieved.
