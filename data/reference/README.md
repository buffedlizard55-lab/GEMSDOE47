# Reference corpus — provenance

These rasters were copied into this working tree **for learning and calibration only**. They are
excluded from git (`.gitignore`); this file is the record of where each came from and what it is
worth, so the corpus can be rebuilt.

Every file is on the pinned competition grid: EPSG:32611, 100 m, 3730 rows × 3292 cols,
transform `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`.

**No file here is shipped as the GEMSDOE47 submission.** The submission is generated from the
official 19-band feature stack by `scripts/build_submission.py` and is asserted unique against
all of these by Jaccard distance and SHA-256 — see `evidence/submission/bundle.json`.

## Scored artifacts (filename encodes the reported public DTI)

| file | public DTI | positive px | source repository |
|---|---|---|---|
| `scored_h19-5-solid_0.1922.tif` | 0.1922 | 121,131 | 19GEMSDOE (`/tmp/g19`) |
| `scored_h19-5-d1.5_0.2477.tif` | 0.2477 | 60,069 | 19GEMSDOE |
| `scored_h19-5-d2.8_0.2600.tif` | 0.2600 | 44,090 | 19GEMSDOE |
| `scored_d28-poisson-offcat_0.2600.tif` | 0.2600 | 44,090 | GEMSDOE28 |
| `scored_topo-gap-d1.5_0.2449.tif` | 0.2449 | 61,328 | GEMSDOE28/29 |
| `scored_h27-4-d2.8_0.2708.tif` | 0.2708 | 40,199 | GEMSDOE27 (all-finite variant) |
| `scored_h33-2-b2_0.2778.tif` | **0.2778** | 37,654 | GEMSDOE32 (`/tmp/g32`) — family best |
| `scored_h33d-tip-stepover_0.2632.tif` | 0.2632 | 41,865 | GEMSDOE33 |
| `scored_h30-arr-habitat_0.1352.tif` | 0.1352 | 91,533 | GEMSDOE30 |
| `scored_h34-scatter-q50_0.0778.tif` | 0.0778 | 37,654 | GEMSDOE34 |
| `scored_h35-06_0.0418.tif` | 0.0418 | 39,530 | GEMSDOE35 |
| `unscored_h33-2b2-plus-h33-1.tif` | not submitted | 38,554 | GEMSDOE32 |

Ledger discrepancies found and recorded rather than smoothed over:

* `scored_h27-4-d2.8_0.2708.tif` in this all-finite variant holds **40,199** positive pixels, not
  the 44,090 that earlier family ledgers list for `h27-4-d2.8`.
* `scored_h34-scatter-q50` and `scored_h35-06` carry `nodata=nan` and 7,111,787 NaN cells, and
  were still scored by the organiser — so NaN outside the footprint is *accepted*. The shipped
  GEMSDOE47 raster is finite everywhere anyway, because that is the configuration shared by the
  six artifacts that never drew a format complaint.
* `scored_h33-2-b2_0.2778.tif` is **exactly** `scored_h27-4-d2.8_0.2708.tif` minus its 2,545 dots
  within 2 px of the given catalogue: 40,199 − 2,545 = 37,654. This nested pair is the natural
  experiment that `evidence/inversion/live_anchor_inversion.json` is built on.

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
