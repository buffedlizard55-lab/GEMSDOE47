# Reference corpus — provenance

> **Owner-mirror inventory only; not a leaderboard receipt.** Filename labels and owner-reported scores are not authenticated by the organizer. The public 0.2778 observation is a dated participant-level row; no receipt maps it to H33-2-B2. Treat all dependent inversions and comparisons as conditional. Published instructions require null or NaN outside bounds; unmasked all-finite zero-outside variants fail the local outside-nodata check. NaN-outside siblings follow an owner-supplied mirror convention only; organizer acceptance and the earlier rejection cause are unknown.

These rasters were copied into this working tree **for learning and calibration only**. They are
excluded from git (`.gitignore`); this file is the record of where each came from and what it is
worth, so the corpus can be rebuilt.

Every file is on the pinned competition grid: EPSG:32611, 100 m, 3730 rows × 3292 cols,
transform `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`.

**No file here is shipped as the GEMSDOE47 submission.** The submission claim in this historical note refers to an earlier build path. Current artifacts and their status are identified in `docs/all-downloads.html`; bounded byte comparisons do not establish global uniqueness or organizer acceptance.

## Owner-supplied artifact labels (not verified public scores)

| file / owner-supplied filename | filename or owner-reported score label (unverified) | positive px | source repository |
|---|---|---|---|
| `scored_h19-5-solid_0.1922.tif` | 0.1922 | 121,131 | 19GEMSDOE (`/tmp/g19`) |
| `scored_h19-5-d1.5_0.2477.tif` | 0.2477 | 60,069 | 19GEMSDOE |
| `scored_h19-5-d2.8_0.2600.tif` | 0.2600 | 44,090 | 19GEMSDOE |
| `scored_d28-poisson-offcat_0.2600.tif` | 0.2600 | 44,090 | GEMSDOE28 |
| `scored_topo-gap-d1.5_0.2449.tif` | 0.2449 | 61,328 | GEMSDOE28/29 |
| `scored_h27-4-d2.8_0.2708.tif` | 0.2708 | 40,199 | GEMSDOE27 (all-finite variant) |
| `scored_h33-2-b2_0.2778.tif` | label says 0.2778; score-to-TIFF association unverified | 37,654 | GEMSDOE32 (`/tmp/g32`); owner-supplied raster only |
| `scored_h33d-tip-stepover_0.2632.tif` | 0.2632 | 41,865 | GEMSDOE33 |
| `scored_h30-arr-habitat_0.1352.tif` | 0.1352 | 91,533 | GEMSDOE30 |
| `scored_h34-scatter-q50_0.0778.tif` | 0.0778 | 37,654 | GEMSDOE34 |
| `scored_h35-06_0.0418.tif` | 0.0418 | 39,530 | GEMSDOE35 |
| `unscored_h33-2b2-plus-h33-1.tif` | not submitted | 38,554 | GEMSDOE32 |

Ledger discrepancies found and recorded rather than smoothed over:

* `scored_h27-4-d2.8_0.2708.tif` in this all-finite variant holds **40,199** positive pixels, not
  the 44,090 that earlier family ledgers list for `h27-4-d2.8`.
* `scored_h34-scatter-q50` and `scored_h35-06` carry `nodata=nan` and 7,111,787 NaN cells. Their owner-supplied appearance in a score history does not establish organizer acceptance of that encoding. Published instructions explicitly say null or NaN outside bounds; this available mirror convention is not portal verification. H47-C1's research raster instead has an internal mask, also not organizer-tested; its promotion gate remains closed. H60 is now locally promoted as a scientific candidate, and its separate NaN-outside variant matches the published outside convention on local read-back only. Neither H60 encoding has been organizer-tested; no upload or slot use was authorized or performed.
* The owner-supplied H33-2-B2 and H27-4-d2.8 rasters have a local geometric subset relation: 40,199 − 2,545 = 37,654 positive pixels under the retained masks. This byte-level relation does not authenticate either file-to-score mapping or establish a causal score effect; inversions using it are hypothetical.

## External geoscience priors, already rasterised to the competition grid

| file | positive px (in footprint) | source |
|---|---|---|
| `derived_sgmc_faults_100m_u8.tif` | 82,151 | USGS State Geologic Map Compilation (SGMC), public domain |
| `derived_gdr_qfaults_v2_100m_u8.tif` | 59,065 | Geothermal Data Repository QFaults v2 |
| `derived_gdr_volcanics_100m_u8.tif` | 6,776 | GDR volcanics |
| `derived_gdr_2m_probes_100m_u8.tif` | 2,700 | GDR two-metre temperature probes |
| `derived_gdr_paleo_100m_u8.tif` | 244 | GDR paleo sites |
| `qfaults_prior_u8.tif` | 138,416 total / 58,251 in footprint | INGENIOUS QFaults prior |

Copied from `/tmp/GEMSDOE30_c/data/external/` and `/tmp/GEMSDOE22_c/assets/external/`. Note that
`/tmp` is not persisted across sessions; the copies in this working tree are the only surviving
instances and the `derived_*` rasters would have to be re-derived from the named public sources.

**Measured this session** (`evidence/offcatalogue_populations.json`): of `derived_gdr_qfaults_v2`
(59,065 px) exactly **1 pixel** lies more than 300 m from the given catalogue, and of
`qfaults_prior_u8` (58,251 px in footprint) **zero** do. The given training labels already contain
the newest public Quaternary fault compilation, so neither can serve as an off-catalogue truth
source. Only `derived_sgmc_faults_100m_u8` supplies one: **61,664 px in 2,077 components** — and
`knowledge/02` shows that population is exposed mountain bedrock, so it is measured and rejected
for selection anyway.

A copy of `derived_sgmc_faults_100m_u8.tif` differs slightly from the copy under
`/tmp/g19/evidence/ci/` (82,151 vs 83,593 positive px); the version here is the GEMSDOE30 one and
all numbers in `evidence/` are computed from it.
