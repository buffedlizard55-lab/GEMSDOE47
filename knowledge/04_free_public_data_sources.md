# Knowledge base 04 — overlooked free / public data sources, contrarian but grounded

Standing rule from the brief: *if a candidate needs new external data, name the specific free
official source and check obtainability before proposing it as viable.* Each entry below therefore
carries an explicit **obtainability verdict** at two levels:

* `EXISTS` — the source, its DOI/landing page and its contents were confirmed this session
  (search + the family's own fetched copies).
* `FETCHABLE-HERE` — this sandbox can actually download the bytes.

Almost nothing geoscientific is `FETCHABLE-HERE` (see `knowledge/03` §5: every USGS/OPENEI/NBMG
host is blocked). That is stated plainly rather than glossed, because proposing a data-dependent
hypothesis without saying so would be exactly the hallucination the brief forbids.

---

## 1. Tier 1 — directly relevant to this competition's footprint, free, official

### 1.1 GeoDAWN EarthMRI / 3DEP LiDAR — *the* missing ingredient

* **What.** "GeoDAWN West Central Nevada EarthMRI Data" and "GeoDAWN Northwestern Elko County
  Nevada EarthMRI Data": original-product-resolution rasters **and LiDAR point clouds**, collected
  under the USGS Earth Mapping Resources Initiative (EarthMRI) and the USGS 3D Elevation Program
  (3DEP) with DOE Geothermal Technologies Office funding.
* **Where.** Open Energy Data Initiative — https://data.openei.org/search?q=Nevada
  `[EXISTS]` `[not FETCHABLE-HERE]`
* **Why it matters.** The competition ships `det_elev` at 100 m. `scripts/diagnose_bands.py`
  measured that only three of the nineteen bands carry appreciable variance at the metric's own
  300 m scale, and that the best single transform of the shipped topography reaches tie-aware AUC
  0.618 against expert-mapped fault. A 1 m DEM would let the same across-strike step filter resolve
  scarps of 1–3 m throw, which is the actual population the expert panel maps from LiDAR.
* **This is the `1m_DEM_links.csv` the competition references.** That file is login-gated; OEDI is
  the public route to the same acquisition.
* **Prior family measurement.** GEMSDOE10 reduced eight 1 km² 1 m USGS 3DEP tiles
  (`NV_WestCentral_EarthMRI_2020_D20`) to Topographic Openness + LRM over 71,974 competition cells
  — i.e. only 1.4 % of the footprint. `[FAMILY LEDGER]` **Contrarian point:** the family treated
  1 m LiDAR as a small-sample enrichment. The measured result here says topography is the *only*
  band family with 300 m-scale fault skill, so covering the whole footprint with it is the single
  highest-leverage data acquisition available, not a marginal one.
* **Verdict for this session:** NOT VIABLE (unobtainable). Recorded as the top recommendation for
  any session with network access.

### 1.2 NBMG Map 167 — Quaternary faults in Nevada

* **What.** dePolo, C.M. (2008). *Quaternary faults in Nevada.* NBMG Map 167, 1:1,000,000, age of
  last rupture and movement type.
* **Where.** https://pubs.nbmg.unr.edu/Quaternary-faults-in-Nevada-p/m167.htm — free downloads
  including the geospatial PDF; direct zip
  https://data.nbmg.unr.edu/public/freedownloads/m/m167.zip ; interactive
  https://gisweb.unr.edu/QuaternaryFaults/ `[EXISTS]` `[not FETCHABLE-HERE]`
* **Why it matters — and the caveat that makes it more useful than it looks.** The NBMG ArcGIS
  service description states verbatim:

  > "Fault traces were originally digitized at **1:250,000 scale** and spatial error can be
  > significant when viewing faults at larger scales. … Locations are only certain at the scale of
  > the original mapping extent, causing accuracy to vary as the map is zoomed. **A buffer has been
  > applied to the data to account for the inaccuracies.**"

  https://gisweb.unr.edu/nbmg/rest/services/Geology/Faults/MapServer `[EXISTS]`

  A 1:250,000 digitisation has a nominal positional error of roughly 100–250 m; the service itself
  ships a 100 m buffer layer. That is **independent, official confirmation** of Hermant et al.'s
  2025 measurement (up to 400 m between USGS Quaternary faults and expert LiDAR labels). The given
  catalogue is therefore *systematically* offset from the true trace position at exactly the scale
  the metric resolves (300 m). Two consequences used in this repository:
  1. never treat a catalogue pixel as pixel-exact truth for trace *position*;
  2. a prediction that is a good trace but laterally offset by 1–3 px still scores — so emission
     should be *along* coherent lineaments, which is what `scarp_step` with a 1.9 km along-strike
     run produces.

### 1.3 NBMG Open Data portal (ArcGIS Hub)

* https://data-nbmg.opendata.arcgis.com/pages/geohazards and `/pages/web-applications` `[EXISTS]`
* Free `.csv` / `.kml` / shapefile downloads: Quaternary faults, earthquakes by magnitude,
  geothermal energy layers, mining districts, renewable energy, soils.
* Note the portal states the Quaternary faults "have been adapted and modified from NBMG M167 and
  the USGS Quaternary Fault and Fold Database" — so it is not independent of §1.2, and using both
  would double-count.

### 1.4 USGS State Geologic Map Compilation (SGMC)

* Horton, J.D. (2017), *The State Geologic Map Compilation (SGMC) geodatabase of the conterminous
  United States* (ver. 1.1, August 2017), USGS data release, **DOI 10.5066/F7WH2N65**;
  **superseded by DOI 10.5066/P1A3DQZK**. ScienceBase item `5888bf4fe4b05ccb964bab9d`; report
  Horton, San Juan & Stoeser (2017) USGS Data Series 1052, 46 p.
  https://www.sciencebase.gov/catalog/item/5888bf4fe4b05ccb964bab9d `[EXISTS]` `[not FETCHABLE-HERE]`
* Public domain. Contains a dedicated **fault-structures** layer.
* **Measured this session** (`evidence/offcatalogue_populations.json`): rasterised to the
  competition grid it holds 82,151 px, of which **61,664 px in 2,077 components lie more than
  300 m from the given catalogue**. That is the only substantial real-fault population in this
  environment that the given catalogue lacks.
* **And it is rejected for selection.** `knowledge/02` shows those traces are high, steep,
  shallow-basement mountain bedrock — median detrended elevation **+115 m** vs **−69 m** for the
  given catalogue, median `det_elev_slope` **13.0** vs **5.1**, median depth-to-basement **105 m**
  vs **321 m**. Optimising against SGMC builds a bedrock-contact detector.
* **The contrarian use of SGMC is as a NEGATIVE control, not as truth.** A field that scores well
  against SGMC-offcat but no better than the fixed comparison baseline on held-out catalogue components has
  learned "mountain", not "fault". That test is exactly what caught the
  `lrm(det_elev_slope, r=9)` candidate, which was the best transform on SGMC-offcat (precision
  0.260) and only 0.106 on the given catalogue — barely above the 0.086 random baseline.

### 1.5 QFaults v2 and the INGENIOUS QFaults prior — measured, and useless

* Geothermal Data Repository QFaults v2, and `qfaults_prior_u8` from the INGENIOUS compilation
  (DOI 10.15121/1881483).
* **Measured:** of 59,065 QFaults-v2 pixels in the footprint, exactly **1** lies more than 300 m
  from the given catalogue; of 58,251 prior pixels, **0** do.
* **Conclusion, stated because it kills a whole family of ideas:** the competition's training
  labels already contain the newest public Quaternary fault compilation. Any strategy of the form
  "add an external fault catalogue as a prior" is worth **zero** here. GEMSDOE32's H60-2 arm
  (SGMC/QFaults additive prior) was aiming at a target that does not exist.

---

## 2. Tier 2 — free, official, and genuinely under-used by the family

| source | what it adds | obtainability |
|---|---|---|
| **USGS Geophysics, Heat Flow, and Slip & Dilation Tendency Data** (Nevada Geothermal Machine Learning Project), DeAngelo, J. et al., NBMG, 1 June 2021, GDR submission 1349 — https://gdr.openei.org/submissions/1349 | fault **slip and dilation tendency** per segment, heat flow, geophysics for northern Nevada. This is the layer that turns "there is a structure here" into "this structure is open to fluid". | `[EXISTS]` `[not FETCHABLE-HERE]` |
| **INGENIOUS 2-m temperature probes, springs & wells, aqueous geochemistry, sinter/tufa** (GDR 1391) | direct surface expression of a *working* hydrothermal system. Family measurement: of 27,092 GDR well/spring records, 7,859 are thermal/geochemical anomalies and **75.7 % lie >500 m from any known fault**; of 594 two-metre-probe anomalies **86.9 %** >500 m off; of 281 sinter/tufa sites **73.0 %** >500 m off. | `[EXISTS]` `[not FETCHABLE-HERE]`; 2,700 probe px and 244 paleo px are already rasterised in `data/reference/` |
| **Nevada Play Fairway Analysis** packages (Granite Springs Valley etc.) on OEDI | geologic map + sinter/tufa + slip & dilation tendency + Quaternary faults + LiDAR, pre-co-registered by NBMG for exactly this purpose | `[EXISTS]` `[not FETCHABLE-HERE]` |
| **USGS 3DEP / The National Map** | 10 m and 1 m elevation nationally | `[EXISTS]` `[not FETCHABLE-HERE: prd-tnm.s3.amazonaws.com blocked]` |
| **USGS Quaternary Fault and Fold Database** | the national Q-fault source behind NBMG M167 | `[EXISTS]` `[not FETCHABLE-HERE: earthquake.usgs.gov blocked]`; **and §1.5 shows it is already inside the training labels** |
| **BLM / NV Division of Minerals geothermal lease and permitting data** | where industry *believed* there was a resource, independent of any fault catalogue — a weak but genuinely orthogonal label | `[EXISTS]` via NBMG open-data portal |

---

## 3. Contrarian conclusions that follow from the measurements, not from taste

1. **Adding external fault catalogues is worthless.** §1.5: the training labels already contain
   them. The entire "prior catalogue" research direction that occupied GEMSDOE22–32 is closed.
2. **The binding constraint is resolution, not information.** Sixteen of nineteen bands are >96.5 %
   smooth above 300 m (`evidence/band_scale_diagnostics.json`). The only bands that can localise a
   fault are `tmi_vg`, `det_elev_slope` and `tmi_hg`, and of those only the topographic one has
   real skill against expert-mapped fault. Everything else can only act as a **veto prior** — which
   is how `detector.regional_gate` uses it, and which is why `geod_2ndinv` smoothed to 2.5 km
   reaches precision 0.287 (3.3× random) as a *prior* while contributing nothing at 300 m.
3. **Persistence along strike is worth more than any new dataset tried here.** Going from a
   per-pixel edge response to an across-strike step required to persist 1.9 km moved
   precision-at-40k from 0.247 to 0.505 — a doubling — with zero new data. Longer persistence
   monotonically rejected stream banks, canyon rims and fan edges, which is precisely the failure
   mode Hermant et al. document.
4. **A proxy that flatters you is worse than no proxy.** The SGMC off-catalogue holdout ranked
   `lrm` first and `scarp` fourth; the correct population ranked `scarp` first and `lrm` below the
   random baseline at 40k. Selecting on the flattering instrument would have shipped a mountain
   detector. `knowledge/02` records the measurement that caught it.
5. **The catalogue's own positional error is a feature to exploit, not noise to suppress.** §1.2:
   official documentation says traces were digitised at 1:250,000 with a 100 m buffer applied, and
   Hermant et al. measure up to 400 m offset from expert LiDAR labels. At a 300 m kernel, the
   correct response is to emit along coherent lineaments near — but not on — the catalogue, which
   is what the 2 px flank buffer plus 2 px spacing does.
