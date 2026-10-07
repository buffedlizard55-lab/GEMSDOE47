---
title: Research knowledge base
layout: default
nav_order: 6
---

> **RESEARCH-ONLY / ATTRIBUTION LIMIT.** H33-2-B2 → participant DTI 0.2778 is unverified; H48 and other score-dependent work is hypothetical/conditional, not authenticated or conclusive. Use “owner-reported d2.8 reference”; reserve “incumbent” for a separately established spatially blocked holdout best. Public official pages checked 2026-10-06 do not establish current per-user quota or slot accounting. Three λ-scaling score observations do not verify uploads/slots; no diagnostic cost is inferred or called free. See [current README](../README.md).

# Research knowledge base

*Generated 2026-10-06 20:13 UTC. The full text of each file is in `knowledge/` in the repository; this page is the index plus every official link, so a reviewer can check any claim without reading the code.*

| file | what it settles |
|---|---|
| [`00_index.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/00_index.md) | Knowledge base — index |
| [`01_metric_algebra_and_inversion.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/01_metric_algebra_and_inversion.md) | Knowledge base 01 — the metric's algebra, and what the organiser's own scores imply |
| [`01_the_gems_target_population.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/01_the_gems_target_population.md) | The GEMS target population — what the hidden labels actually are |
| [`02_the_metric_algebra.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/02_the_metric_algebra.md) | The DTI metric algebra — everything that follows from four published formulas |
| [`02_the_two_instruments_measure_different_populations.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/02_the_two_instruments_measure_different_populations.md) | The two candidate holdout instruments measure DIFFERENT fault populations |
| [`03_geothermal_fault_discovery_research.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/03_geothermal_fault_discovery_research.md) | Knowledge base 03 — geothermal fault discovery: the verified literature |
| [`03_next_steps_and_the_ceiling.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/03_next_steps_and_the_ceiling.md) | Next steps, ranked by expected value |
| [`04_free_public_data_sources.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/04_free_public_data_sources.md) | Knowledge base 04 — overlooked free / public data sources, contrarian but grounded |
| [`05_why_02778_and_can_we_beat_it.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/05_why_02778_and_can_we_beat_it.md) | Attribution limits and conditional algebra for the unverified H33-2-B2 / participant-DTI 0.2778 association |
| [`06_hypotheses_H47.md`](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/06_hypotheses_H47.md) | H47 — new geological hypotheses, measured, ranked, and honestly refuted where they failed |

---

## Every official link cited anywhere in this repository

* [Competition home (DrivenData #306, DOE GEMS Prize)](https://www.drivendata.org/competitions/306/competition-doe-gems/)
* [Performance metric — the authoritative definition of DTI](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric)
* [Live public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
* [Official reference solution (PyTorch U-Net)](https://github.com/drivendataorg/gems-prize-reference-solution)
* [Scoring clarification — are known USGS/INGENIOUS faults masked? (staff answer)](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)
* [Organisers will not disclose test-fault sources / types / coverage](https://community.drivendata.org/t/11527)
* [DOE announcement of the $300,000 GEMS Prize](https://www.energy.gov/hgeo/articles/hydrocarbons-and-geothermal-energy-office-announces-300000-help-identify-hidden)
* [INGENIOUS Great Basin Regional Dataset Compilation — the origin of all 19 bands (DOI 10.15121/1881483)](https://gdr.openei.org/submissions/1391)
* [USGS Geophysics, Heat Flow, Slip & Dilation Tendency (Nevada Geothermal ML Project)](https://gdr.openei.org/submissions/1349)
* [GeoDAWN EarthMRI / 3DEP LiDAR for western Nevada (Open Energy Data Initiative)](https://data.openei.org/search?q=Nevada)
* [NBMG Map 167 — Quaternary faults in Nevada (free download)](https://pubs.nbmg.unr.edu/Quaternary-faults-in-Nevada-p/m167.htm)
* [NBMG Quaternary Faults ArcGIS service — states traces were digitised at 1:250,000](https://gisweb.unr.edu/nbmg/rest/services/Geology/Faults/MapServer)
* [NBMG Open Data portal (geohazards)](https://data-nbmg.opendata.arcgis.com/pages/geohazards)
* [USGS State Geologic Map Compilation (SGMC), DOI 10.5066/F7WH2N65](https://www.sciencebase.gov/catalog/item/5888bf4fe4b05ccb964bab9d)
* [Hermant, Kiersnowski & Bellanger 2025 — deep learning to map Quaternary faults, N. Nevada](https://pangea.stanford.edu/ERE/pdf/IGAstandard/SGW/2025/Hermant.pdf)
* [Blewitt et al. — targeting geothermal resources from geodetic strain rate and slip tendency](https://nbmg.unr.edu/staff/pdfs/blewitt%20grc%20paper.pdf)
* [Lei, G'Sell, Rinaldo, Tibshirani & Wasserman 2018, JASA — split conformal prediction](https://doi.org/10.1080/01621459.2017.1322365)
* [Same, preprint](https://arxiv.org/abs/1604.04173)
* [Two-round structure and expert label expansion (independent report of the organiser's rules)](https://www.thinkgeoenergy.com/us-doe-announces-prize-challenge-for-discovery-of-hidden-geothermal-systems/)

---

## Obtainability, stated at two levels

`EXISTS` means the source, its DOI or landing page, and its contents were confirmed in this session. `FETCHABLE-HERE` means this sandbox can actually download the bytes. Almost nothing geoscientific is `FETCHABLE-HERE`: `curl`/`wget` are blocked for every host except `pypi.org` and `github.com`. Confirmed unreachable by direct download: `github.io`, `drivendata.org`, `dropbox.com`, `raw.githubusercontent.com`, `registry.opendata.aws`, `prd-tnm.s3.amazonaws.com`, `sciencebase.gov`, `pangea.stanford.edu`, `earthquake.usgs.gov`, `services.azgs.arizona.edu`, `gdr.openei.gov`, `data.openei.org`, `usgs.gov`, `opentopography.org`, `nbmg.unr.edu`.

Working transports: `fetch_page` (drivendata.org, community.drivendata.org, pangea.stanford.edu PDFs, github.io), `web_search`, `git clone`, and **`gh api` for metadata *and* raw blobs** — which is how the three official competition rasters were restored in this session without DrivenData credentials, then verified byte-for-byte against pinned SHA-256 values (`src/gems47s3/spec.py::PINS`).

No automated access to `drivendata.org` appears in any script, in keeping with the DrivenData Terms of Use. Competition pages were read interactively; the URLs above are cited for manual review.
