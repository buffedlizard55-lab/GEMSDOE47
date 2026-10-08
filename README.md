# GEMSDOE47 — H60 is the submission: new inference, auditable evidence

> **Read the standing brief below at the start of every work session.**
> **Maximize P(Win)**: publish a genuinely new candidate only after it beats every control on a
> spatially blocked holdout — then submit it.
> **Own the Outcome**: publish negative results, corrections, actual bytes and limits — never an invented win.

## OK TO DOWNLOAD AND SUBMIT — the H60 GeoTIFF

**[Download the H60 single-band GeoTIFF (this is the file to submit)](docs/downloads/gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif)** ·
[ZIP with note + receipt](docs/downloads/gems47-h60-lidarscarp-s2p0-20261007.zip) ·
[H60 evidence page](docs/h60.html) ·
[Executive summary and official submission sequence](docs/executive-summary.html) ·
[GitHub Pages](https://buffedlizard55-lab.github.io/GEMSDOE47/)

A genuinely new hypothesis, **not a copy of any prior GEMSDOE submission**. The field is the
per-cell **maximum of the ranks of six scarp channels of the owner-derived 1 m lidar stack**
(`step_max`, `lappos_max`, `lapneg_max`, `upface_max`, `downface_max`, `cross_max` — the stack was
built by the owner's CI from USGS 3DEP 1 m DEM tiles on the competition's own tile list, pinned at
`registry/data_manifest.json`; it is *not* organiser-supplied), restricted to cells at least
**250 m from a TIGER road** and **150 m from a BLM closed mining claim**, so the detector sees
tectonic steps rather than road cuts and mine scars. Every previous family field ranked a *proxy*
of the scarp; H60 ranks the scarp evidence itself. The round was **preregistered** (slate, frozen
design, six-condition gate committed at `5ea987b` **before** any score was computed:
[docs/research/h60-hypotheses-preregistered.md](docs/research/h60-hypotheses-preregistered.md)).

- Filename: `gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif`
- Name: `GEMSDOE47-H60-lidarscarp-s2p0-20261007`
- **Short Note for the DrivenData form: `h60 lidar-scarp d2p0 conformal90`** (34 characters)
- TIFF SHA-256: `4ee074230a305fce6768012fc33380bf196c89170e70050a77cf4a44d74ef14c`
- Actual bytes: **298,994**. Full width **3292 × height 3730**, EPSG:32611, 100 m.
- One float32 band, **37,654 unit dots** at 2.0 px / 200 m over the off-catalogue evaluated domain
  intersected with the noise-masked valid-lidar domain (1,610,706 of 5,106,385 cells).
- **Every one of the 12,279,160 cells is finite and inside [0,1]**; the values are 0.0 and 1.0 only.
  No NoData tag; 0.0 outside the footprint. This is the direct answer to the reported portal
  rejection `"Predicted values must be in range [0, 1]"`. A NaN-outside fallback is published
  alongside it (`gems47-h60-lidarscarp-s2p0-20261007-nanoutside.tif`).
- **17/17 strict read-back checks pass. Organizer acceptance has not been tested.**
- **Bounded uniqueness:** 35 prior rasters compared — **zero exact matches**, maximum mask Jaccard
  **0.0217** (the most novel artifact this repository has published).

### The H60–H64 round (7 October 2026) — one winner, two refutations, one refinement

| Arm (selection half, pooled DTI) | Primary: lidar lappos peaks | Independent: SGMC off-catalogue | Verdict |
|---|---:|---:|---|
| **H60 lidar scarp-crest field** | **0.287891** | **0.193813** | **PROMOTED (gate passed; winner)** |
| H62 additive 50/50 mixture | 0.245762 | 0.184971 | passed, lost the SGMC tie-break |
| H50 slope-anomaly anchor | 0.165881 | 0.122083 | reproduced bit-for-bit (design check) |
| H61 per-trace reallocation of H50 | 0.163632 | 0.121525 | **refuted** — trace-proportional spreading does not help |
| H63 catalogue-adjacency-gated lidar | 0.156660 | 0.162911 | **refuted** — hugging the catalogue hurts |
| Owner-reported d2.8 reference | 0.049421 | 0.089879 | control |
| Mass-matched spaced random | 0.046288 | 0.069761 | control |

H64 (instrument refinement, 13 owner-reported artifacts, Spearman ρ vs reported DTI): **far-from-catalogue
peaks correlate better than near ones** (lappos +0.581 far vs +0.273 near), **the road/claim masks improve
the instrument-leaderboard correlation** (step +0.592 masked vs +0.449 unmasked), and `coh100` peaks
anti-correlate (−0.532). These three facts are *why* H60's design choices won and why H63 failed.
Evidence: `evidence/h60/` (screen, spacing history, instrument refinement, artifact profile) — deployed
copies at `docs/data/h60-*.json`.

Two implementation deviations are recorded rather than hidden (IR-2026-10-07-D): the preregistered H61
min-1 per-trace allocation floor over-emitted (649 dots for a 294 budget) and was replaced by
deterministic largest-remainder allocation; and the lidar-domain arms cap emission at domain capacity at
small spacings (H60 placed 17,889 of the 21,198-dot selection budget at 2.0 px — it outperforms the
anchor with 84 % of the mass).

### H65 spacing extension (8 October 2026) — negative gate, no TIFF built

Four fresh hypotheses (H65–H68) were ranked and preregistered at commit `b73bb64` before scoring.
H65 tested H60's direct lidar-scarp field at 1.4–2.4 px on the same frozen 41-block design. Selection
chose **2.2 px**, not the preregistered **strictly below 2.0 px** direction, so one of five prebuild
conditions failed and no H65 artifact was built. The other proxy results were favorable — pooled primary
DTI **0.291533** vs H60 0.287891, independent SGMC **0.205420** vs 0.193813, and a simultaneous
split-conformal floor **0.099207** at at least **90.91%** conditional coverage — but changing the gate
after reading those values would be post-hoc. H60 therefore remains the file to submit. Evidence:
[H65 report](docs/h65.html), [preregistration](docs/research/h65-h68-hypotheses-preregistered.md), and
`evidence/h65/`.

### H50 — valid fallback, superseded as primary by H60 on 2026-10-07

**[Download the H50 GeoTIFF (labelled fallback)](docs/downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif)** ·
[H50 evidence page](docs/h50.html). H50 passed the same promotion gate in the previous round and remains a
valid, format-checked, unique submission option. The field is the rank of official band 19
(`det_elev_slope`) *above its own 25 px (2.5 km) Gaussian regional level*, validated against
**off-catalogue local maxima of the owner-derived 1 m lidar scarp stack** (USGS 3DEP 1 m tiles; the
"organiser-supplied" wording in earlier H50-era text was a provenance error — corrected, see
IR-2026-10-07-B), the only local truth population whose DTI is *positively* rank-correlated with the
owner-reported public scores. The current recommendation is H60, which beat H50 on **both** the primary
instrument (+73 %) and the independent SGMC instrument (+59 %) under the same frozen 41-block design.

### H51 (sibling session, merged from `main` 2026-10-07) — not recommended while H50 exists

A sibling session published `docs/downloads/gems47-h51-multiscale-s2p8-20261007-allfinite.tif`
(multi-scale slope-anomaly persistence, 2.8 px, 37,654 dots; evidence page
[docs/h51.html](docs/h51.html)). It passes the format checks, but its own receipt records
**maximum mask Jaccard 0.8543** against a prior raster: 34,696 of its 37,654 dots are the H50
slope-anomaly raster's dots (measured directly in this session). It is therefore a
**near-duplicate of the published H50 emission**, not an independent candidate; submitting it
while H50 exists would spend a slot on substantially the same prediction. It is retained for
audit and is **not** the file to submit. H60's maximum Jaccard against every prior raster,
including H51, is **0.0217**.

- Filename: `gems47-h50-slopeanom-s2p8-20261007-allfinite.tif`
- Name: `GEMSDOE47-H50-slopeanom-D2p8-20261007`
- **Short Note for the DrivenData form: `h50 slope-anomaly d2p8 conformal90`** (31 characters)
- TIFF SHA-256: `97e3c3816cd6b458d01e34d7022f871935bb57710e3982a11d9edaec13e91a17`
- Actual bytes: **291,321**. Full width **3292 × height 3730**, EPSG:32611, 100 m.
- One float32 band, **37,654 unit dots** at 2.8 px / 280 m over the evaluated domain (competition
  footprint minus the USGS/INGENIOUS catalogue, which is masked out of scoring).
- **Every one of the 12,279,160 cells is finite and inside [0,1]**; the values are 0.0 and 1.0 only.
  No NoData tag; 0.0 outside the footprint. This is the direct answer to the reported portal
  rejection `"Predicted values must be in range [0, 1]"` and matches the byte convention of the
  owner-reported family-best raster. The official page says null or NaN outside the bounds, which
  zeros do not satisfy literally; a NaN-outside fallback is published alongside it.
- **17/17 strict read-back checks pass. Organizer acceptance has not been tested.**
- **Bounded uniqueness:** 31 prior rasters compared (every restored sibling submission, the
  owner-reported d2.8 reference, this repository's published downloads, the two legacy submission
  TIFFs) — **zero exact matches**, maximum mask Jaccard **0.0456**.


### H50a template-format checkpoint — research only, retained from `main`

A sibling session exported `docs/downloads/gems47-h50a-corridor-s1p5-b3-20261007-4096e1f9d19b-template-nanoutside.tif`
(SHA-256 `6dfe602d35b0f0755eae9a7a8bcc2e6f81efaf291f97341d588ee818b2e07cc5`) plus a finite-mask
diagnostic variant. It has one float32 band, finite in-footprint values in [0,1], and raw NaN /
NaN NoData exactly outside the mirrored sample-template mask; the strict local template-mask check
passes. Its nominal 90 % public-proxy floor is **0.0000** and its blocks were previously
inspected, so its promotion gate is closed. **It is not the file to submit.** Full checks,
receipts and the spacing sweep: [h50a.html](docs/h50a.html) and `evidence/h50/` on `main`.

### H50 operating point (fallback), certified by split conformal prediction

| Item | Value |
|---|---|
| Spacing | **2.8 px / 280 m** |
| Budget | 37,654 unit dots |
| Selection | 20 spatially blocked blocks (selection half) |
| Certification | 21 disjoint blocks (calibration half), max-residual one-sided split conformal, Lei et al. JASA 2018 Algorithm 2 |
| Residual rank | 20 of 22 |
| Finite-sample coverage | **at least 90.91 %, conditional on block-score exchangeability** |
| Certified holdout floor | **0.0957 DTI** |

Selection on the selection half only; the calibration half, which the choice never saw, then
certified it. Simultaneous over the seven spacings in the sweep. Geological exchangeability is
**unverified**, so this is a conditional guarantee and **not** a private-label, pooled-map or
leaderboard guarantee.

### H50 blocked-holdout gate — it passed (previous round)

| Blocked-holdout comparison (selection half, off-catalogue lidar-scarp instrument) | Pooled DTI | Mean block DTI |
|---|---:|---:|
| **H50 slope-anomaly field** | **0.165881** | **0.163039** |
| Owner-reported d2.8 reference raster | 0.049421 | 0.046088 |
| H47-C1, the previous holdout best | 0.048252 | 0.041460 |
| Mass-matched fixed-seed spaced random | 0.047049 | 0.037786 |

Forty-one contiguous blocks (20 selection + 21 calibration) with a 3 px guard; roles assigned
before any score was computed; blocks
with few or no truth pixels kept. **No competition submission slot was spent** to obtain this result
and no private label was read.

## Earlier research artifacts — retained, and NOT the file to submit

**H47-C1 · RESEARCH ONLY · DO NOT UPLOAD.** `docs/downloads/gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif`
(SHA-256 `e6eea1956b8f76ffef2f4867a6e2ac0bef078c0c61c3711e44eb07e93cb089d0`). Its locked holdout gate
failed: pooled public-catalogue DTI 0.177872 against the frozen baseline's 0.180216, 11/22
truth-bearing blocks where 15 were required, assumption-conditional lower-bound estimate 0.0000.
**H50a, H47-QC, H48, H49, H47-B, H47-GSA and H47-MAXCOV are likewise research-only or superseded.**
Full register with hashes and verdicts: [all-downloads.html](docs/all-downloads.html).

### Cross-session research status and claim boundaries

H60 is the current primary artifact and is OK to download and submit; H50 is the labelled
fallback. Every earlier artifact
(H47-C1, H47-QC, H48, H49, H47-B, H47-GSA, H47-MAXCOV) remains research-only and is retained
for audit.

**Every H47-GSA and H47-MAXCOV raster remains research-only; none is promoted or authorized for upload.** The
H47-GSA model, fits, cross-fit comparisons and conditional score inversions are exploratory. Any result that
uses the alleged H33-2-B2 / 0.2778 pairing is a hypothetical scenario, because no organizer receipt authenticates
the participant score to that TIFF. Refer to the d2.8 raster as the **owner-reported d2.8 reference**, not an
incumbent. Reserve “incumbent” for a separately established spatially blocked holdout best; a participant
score or owner-supplied raster alone does not establish one.

H47-SAF's tested sensitivity changes sign **between assumed DTI 0.2200 and 0.2400 only**. This is a coarse-grid
bracket, not an exact break-even or a causal verdict; it depends on the unverified H33 association. No claim
that deleting predictions on masked pixels caused a score gain is supported. Deleting predictions exactly on
masked pixels cannot by itself improve DTI; effects of pruning nearby, evaluated pixels require paired
measurement on the evaluated domain.

**Format boundary:** Published instructions require null or NaN outside the data bounds. The unmasked all-finite H47-B single-scale diagnostic, H47-GSA, H47-MAXCOV, H47-QC, H48-APEX/repack, and older Session-3 files write zeros outside and fail the explicit outside-nodata check; they remain research-only. H48's future research writer now emits NaN outside, which
follows an owner-supplied mirror convention only and does not establish portal acceptance. H47-C1 is
different: it has finite raw samples plus an internal validity mask marking outside cells null; its local
checks are not organizer acceptance.

Keep the metric ratios distinct. With `x=T/K`, `ρ=F/K`, `α=0.2`, and `β=0.8`,
`x=(αρ+β)/(1/DTI−α)`. With `f=F/T`, instead use
`x=β/[1/DTI−α(1+f)]`. `ρ` and `f` have different denominators and are not interchangeable. For example,
`ρ=8.02` is illustrative, not a verified participant ratio; these equations do **not** show that DTI 0.3774
is unreachable. Three historical λ-scaling score observations are not a verified count of new uploads or slots;
no upload cost is inferred and the diagnostic is not characterized as free. See [analysis](docs/analysis.html),
[irregularities](docs/irregularities.md), and [next-session handoff](docs/next-session.md).


## Earlier H47-QC screen — research-only, separate from H47-C1

[Download the H47-QC 5,000-pixel GeoTIFF](docs/downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.tif) ·
[Short identification note](docs/downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.md) ·
[Full screen report](docs/h47qc-screen-20261006.json) ·
[Bounded uniqueness audit](docs/h47qc-uniqueness-audit-20261006.json)

**RESEARCH ONLY · FAILED PROMOTION GATE · DO NOT UPLOAD · NO SLOT AUTHORIZED.** H47-QC's locked-test
pooled public-catalogue DTI was **0.0131689425**, below its geochemistry-only ablation (**0.0141948068**);
selected spacing was **6 px / 600 m**. The nominal split-conformal level was 6/7 (85.7%) only under
unverified block-score exchangeability; its clipped assumption-conditional lower-bound estimate was **0.0**, not a private-target or
map-wide guarantee. The 5,000 binary float32 pixels are finite in [0,1] on the 100 m EPSG:32611 grid; the historical all-finite TIFF writes unmasked zeros outside the footprint and fails the published null/NaN-outside check.
The TIFF SHA-256 is `3866b60cf91b4f6bff2ef694153550aa97a744a3091a57ef9f83da41e16b91b2`.
Its bounded public-inventory audit found no exact positive-mask match among inspected artifacts, but that is
not global uniqueness or performance evidence. A separate post-merge check against all 12 other same-grid
TIFFs currently published in this repository also found no exact mask match (maximum positive-support
Jaccard 0.003175 against H47-GSA; H47-QC/H47-C1 Jaccard 0.000915). H47-QC is a separate earlier experiment,
not a replacement for or promotion of the later H47-C1 result above.

## Preregistration, correction and review

Five ranked physical hypotheses were written **before implementation** in
[`docs/research/h47c-hypotheses-preregistered.md`](docs/research/h47c-hypotheses-preregistered.md).
Protocol and tested implementation were committed at `cc14ad84fbace93bdd0c2a7bc8b520170e082bb3` before fit/scoring.

A test-loop variable overwrote pre-test-selected **2.8** with final sweep value **5.8**. Pass 2 caught it
before a TIFF was published. The first run is retained/retracted in `evidence/retired-profile-pass1/`.
Technical correction `7aa938e` changed no features, models, split, seed, emission budget, spacing grid or gate.
Every trained prediction-field hash and the full spacing history match byte-for-byte across runs;
only final interpretation/emission now honors the original lock. See
[correction/review notes](docs/research/h47c-review-notes.md) and
[control-flow recheck](evidence/profile-control-flow-recheck.json).

Other fixes: empty-truth EDT phantom corner credit; tensor half-angle / row-column strike geometry;
zero-DTI marginal credit; portable H33 reference path; skipped-large restoration falsely labeled
verified; CI missing function-based tests; inactive but dangerous legacy builders deleting/replacing
all downloads. Legacy LATI build entry points are now disabled by default; they exit before reading cache or writing artifacts. They cannot approve a slot. Historical orientation/model/hidden-mass evidence is not recertified.

## Autonomous recovery / training / inference / validation

No manually placed data is needed to reproduce the **mirror-based research** pipeline:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt -r requirements-research-lock.txt
.venv/bin/python scripts/restore_data.py --group all
PYTHONPATH=src .venv/bin/python scripts/verify_grid.py
PYTHONPATH=src .venv/bin/python scripts/run_profile_experiment.py
PYTHONPATH=src .venv/bin/python scripts/build_profile_submission.py
.venv/bin/python scripts/audit_prior_artifacts.py --candidate docs/downloads/gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif
PYTHONPATH=src .venv/bin/python -m pytest tests -q
.venv/bin/python -m ruff check .
```

**23/23 files / ~507 MB restored and verified** by digest **and byte size**. Large arrays, model weights,
raw archives and caches stay ignored. Reproducible pins establish mirror identity, not authenticated
DrivenData provenance. Source recipes and exact numerical/parser versions are saved. The fixed screen
runs in about four minutes on 2 CPU cores; scratch feature/model arrays are under 1 GB per content key.
The legacy site renderer is retired because it can overwrite reviewed pages with stale claims; do not run it.

CI collects **all non-data pytest tests**, including physical mechanisms, block label isolation,
finite conformal ranks, exact selected-choice regression, source-policy/failure handling and actual
new TIFF/ZIP bytes. Restored-grid tests are run locally; they are explicitly marked `needs_data`.

## Auditable automatic feed and source boundaries

- `docs/data/` contains the actual deployed screen, spacing CSV, hash receipts and bounded source inventory;
  no broken `../evidence` paths in the docs-only Pages deployment.
- Pages refreshes permitted official-government/owner source availability and hashes on push/manual
  dispatch and a daily schedule. Failures are retained as failures; stale observations are labeled.
- **DrivenData Terms prohibit robot/spider monitoring**. No written permission or authorized API feed
  is recorded, so automatic DrivenData queries are disabled. The dated participant board is retained,
  not silently presented as live. This limitation narrows the automatic-feed requirement rather than
  bypassing Terms. [Terms](https://www.drivendata.org/termsofuse/) · [Sources](docs/sources.html).
- Public official archives are independently probed on a GitHub-hosted runner; availability/coverage
  is whatever the receipt actually says, never implied by a green workflow. Those vectors do not train C1.
- Staff withholds hidden data sources/types/coverage. Raw 1m_DEM_links.csv and 1 m DEM tiles were not
  acquired. Quantized 100 m lidar descriptors are not raw lidar. Band 6 `tc` and band 15 depth metadata
  remain disputed. [Irregularities](docs/irregularities.html).
- The official overview checked on 2026-10-06 listed **December 3, 2026, 23:59 UTC**. The public official
  pages checked that day do **not** establish a current per-user quota or slot-accounting rule. They describe
  one selected file for both rounds; verify the live portal/rules before any future action. Do not infer a
  permitted upload count or cost from score observations.
- Generative-AI assistance by an Arena.ai coding agent must be disclosed in the official narrative.
  Entrant eligibility, authorized account use and any organizer receipt cannot be certified here.

## What to do next

1. **H60 is published and is the file to submit** (H50 is the labelled fallback). Confirm
   eligibility, upload instructions and any per-user quota in the authenticated organiser portal
   before uploading; public pages do not establish current quota. Retain the organiser's receipt,
   timestamp, filename and score. Disclose generative-AI assistance in the required narrative.
2. **Do not rename or re-label the earlier negative runs (H47-C1, H47-QC, H48, H49, H61, H63) as
   promoted.** They stay research-only in the register; H61/H63 refutations are part of the H60
   evidence.
3. **Independent-instrument work remains the priority.** H60's primary instrument derives from the
   same owner-built lidar stack the field reads, so its numbers are optimistic by construction.
   The SGMC off-catalogue population is the current independent floor (0.1938 vs 0.0698 random).
   A structurally independent instrument (regional fault map, Quaternary-fault compilation,
   geologic map contact traces) would further de-circularise selection.
4. **The spacing optimum may be below 2.0 px.** H60's selection-half mean is monotone down to the
   sweep edge (0.2844 at 2.0, the smallest swept spacing); the preregistered sweep stopped there.
   A preregistered 1.4–2.4 extension is a legitimate next screen, with the conformal guarantee
   made simultaneous over the extended set.
5. **Emission under-capacity is information, not noise.** At 2.0 px the noise-masked domain holds
   only 17,889 of the 21,198-dot block budget on the selection half; the whole-map artifact
   emitted the full 37,654. A budget-vs-domain-capacity trade-off (or larger mask radii with more
   room per block) is untested.
6. Obtain the official 1 m tile CSV/coverage before calling any higher-resolution detector viable.
   Process bounded tile windows, not an unbounded hundreds-of-GB mosaic in Git.

[Current next-session handoff](docs/next-session.md) · [Reusable knowledge](docs/knowledge.html) ·
[Historical pre-C1 README (explicitly superseded)](docs/research/readme-preC1-20261006.md)

---

## 0. Read this first — the standing project brief

This section is the user's brief. It is kept near the top on purpose: **re-read it at the start of every
session**, because every decision above is answerable to it.

> ### MAXIMUM URGENCY / HIGHEST URGENCY MUST BE FOLLOWED
>
> Build, inside this repository, a project that can place at the top of the DrivenData **Geologic
> Enhanced Mapping System (GEMS) Prize Challenge** leaderboard (competition 306,
> https://www.drivendata.org/competitions/306/competition-doe-gems/).
>
> **Deliverables**
>
> 1. A **unique** competition submission GeoTIFF, different from all of the prior GEMSDOE sites listed
>    below. Copying a previous submission is acceptable *only* for learning and education — never as the
>    deliverable.
> 2. The TIF must be **easy to download** from the GitHub Pages site: an obvious one-click download at
>    the very top of the site and in the executive summary.
> 3. Fix the reported submission error **`"Predicted values must be in range [0, 1]"`**. Values must be
>    strictly within [0, 1], single-band float32, EPSG:32611, 100 m resolution, the same bounds as the
>    training data, null/nan outside the bounds.
> 4. Give the submission a **unique name** plus a short distinguishing note for the DrivenData
>    submission form's optional **"Note"** field (for example `clustering with k=25`).
> 5. A **GitHub Pages site** with a clean, simple, user-friendly, organized UI containing all relevant
>    information and official verified source links.
> 6. An **executive-summary subpage** explaining exactly how to submit to the contest.
> 7. **Study why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (GEMSDOE32) scored the family best
>    0.2778**, answer with PhD-level reasoning, and use that to attempt a submission scoring
>    **> 0.2778** and ultimately **> 0.3774** (saved 2026-10-06 leaderboard top; verify the live board manually).
> 8. Before implementing: generate **3–5 candidate geological hypotheses not yet tried**, each naming
>    the specific layer(s), the physical signature targeted (edge detection, curvature transform, etc.),
>    why it should catch a fault *missing* from the USGS/INGENIOUS catalogue rather than one already in
>    it, and how it differs from anything already implemented. Rank by expected DTI improvement and
>    implementation cost.
> 9. **Validate the top candidate on a spatially-blocked holdout set before spending a weekly submission
>    slot.** Never spend a slot on an unvalidated idea.
> 10. If a candidate needs new external data, name the specific free official source and confirm it is
>     obtainable before proposing it as viable.
> 11. Store gathered knowledge from official verified sources as a reusable research base for other
>     projects.
> 12. Autonomous end-to-end: no manual input required; self-research, self-review, self-improve; **flag
>     irregularities**; provide links for manual review.
> 13. Three passes: (1) implement completely and verify; (2) review for bugs, missing requirements, bad
>     assumptions and edge cases and fix them; (3) re-check the whole implementation against the original
>     request and improve accuracy, reliability, completeness and code quality.
> 14. Create a pull request and merge it onto `main`. Report remaining work and limitations.
>
> **Standing constraints**
>
> - "Read the entire prompt." "Verify working line by line — no hallucinations." Work line by line from
>   **official, verified, trusted sources**; provide links for manual review; flag every irregularity.
> - No manual input — the agent must complete all tasks on its own.
> - Contrarian but smart; think outside the box while staying grounded in proper scientific research;
>   find data sources others overlook.
> - Do not spend a submission slot on an idea that has not beaten the current holdout best.
> - Arena core values as focal points: **Maximize P(Win)** and **Own the Outcome**.
> - Known limitation acknowledged in the brief itself: there are no DrivenData credentials, so
>   `training_features.tif`, `labels.tif`, `sample_submission.tif` and `1m_DEM_links.csv` cannot be
>   downloaded from the portal. (They were recovered from hash-pinned mirrors instead — see §2.)

### Hard requirements, in priority order

1. **Unique prediction.** Compare the candidate against accessible historical artifacts before any
   upload; record exact-match and similarity results, scope and limitations. Do not call uniqueness
   global unless all relevant prior submissions are authoritatively available.
2. **Holdout before a slot.** Do not use a submission slot for an idea that has not beaten the current
   spatially blocked holdout best under a preregistered rule. Use equal prediction mass where
   appropriate, a ≥300 m guard consistent with the metric kernel, fold-level results, and nontrivial
   controls. Ties, unstable folds, missing labels, failed controls, or a zero or unsupported assumption-conditional lower bound
   keep the gate closed.
3. **Conformal honesty.** Use split conformal only where the exchangeability unit and target are
   defensible. State sample count, rank, nominal level and assumptions. Never call an
   assumption-conditional result a distribution-free guarantee for private labels or a leaderboard
   score. Do not reuse the retired `0.34837` claim.
4. **Valid output.** Read back the exact output bytes. Enforce a single-band GeoTIFF, official
   grid/CRS/transform, allowed nodata footprint, finite in-footprint values in [0, 1], and an audit
   receipt. A format pass does not establish scientific validity or organizer acceptance.

---


## Preserved supplied score history — user claims, not organizer receipts

| User-reported submission label | User-reported public score | Source/context |
|---|---:|---|
| `gems-submission-20260925T001403Z-7f00890a` | 0.1563 | GEMSDOE |
| `gems6_hgb88-topk03_33cec71ff0` | 0.0286 | 6GEMSDOE |
| `pindrop-v4-nodes-20260925T152420Z-f347b70daa` | 0.1193 | GEMSDOE3 |
| `pindrop-v4-discovery-20260925T152423Z-37f9d5b855` | 0.0830 | GEMSDOE3 |
| `pindrop-v4-ridge-20260925T152422Z-4e03fc9705` | 0.1152 | GEMSDOE3 |
| `gemsdoe2-dual-family-union-20260925T160406Z-f68e590f` | 0.1560 | GEMSDOE2 |
| `gems-submission-20260926T163915Z-237f0063` | 0.0343 | GEMSDOE4 |
| `gems-submission-20260926T175114Z-7f00890a` | 0.1563 | 5GEMSDOE |
| `lidarscarp-ridge-top2pct-36c3a3f341c8` | 0.1461 | 7GEMSDOE |
| `Hedge-v2_submission` | 0.1563 | 8GEMSDOE |
| `2314b599` | 0.0107 | GEMSDOE9 |
| `gems-structural-area06-v1` | 0.0202 | 11GEMSDOE |
| `r7-nms3-dem10-scarp_0c9199f14e62` / `_allfinite` | 0.1294 | 12GEMSDOE |
| `gems-tso1-20260929T005627Z-conj_alteration_mag` | 0.0782 | 15GEMSDOE |
| `GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f` | 0.0020 | 14GEMSDOE |
| `17GEMSDOE_F-ensemble-2pct_20260930T050626Z` | 0.0187 | 17GEMSDOE |
| `H19-C_20260930T212401Z_c11e495e` | 0.0297 | 18GEMSDOE |
| `h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan` | 0.1894 | 19GEMSDOE |
| `h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan` | 0.1922 | 19GEMSDOE |
| `h16-continuation-20260927T065521077735Z-3431b83c7c` | 0.0461 | GEMSDOE10 |
| `h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686` | 0.0921 | GEMSDOE10 |
| `H25-ctx-ridge-20260927T232947704150Z-6452ae1d00` | 0.1280 | GEMSDOE10 |
| `h28-dotted-ridge-20260928T020256236880Z-6452ae1d00` | 0.1839 | GEMSDOE10 |
| `20261001_r13-lattice-s5_v2_nan-outside` | 0.0904 | 13GEMSDOE |
| `h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan` | 0.1855 | 16GEMSDOE |
| `h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan` | 0.0976 | 16GEMSDOE |
| `h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan` | 0.0360 | 16GEMSDOE |
| `h16-continuation` | 0.0461 | GEMSDOE10 |
| `h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan` | 0.1890 | 20GEMSDOE |
| `h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan` | 0.1859 | 20GEMSDOE |
| `h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan` | 0.1002 | GEMSDOE22 |
| `h23-b-dti-optimal-emission-10pct-20261002-86176698-nan` | 0.0748 | GEMSDOE22 |
| `h30-arrangement-matched-habitat-20261002-0d4e02e8-nan` | 0.1352 | GEMSDOE23 |
| `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | GEMSDOE24 |
| `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | GEMSDOE25 |
| `dilcond-oof-v1-20261003-47629f496133-nan` | 0.1223 | GEMSDOE26 |
| `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | GEMSDOE27 |
| `h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan` | 0.2708 | GEMSDOE28 |
| `h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan` | 0.2649 | GEMSDOE28 |
| `efd28-repro-20261003-1cc7dc534d51-nan` | 0.2600 | GEMSDOE29 |
| `repo-c0-habitat-emission-20261003-a4d439b07426-nan` | 0.0041 | GEMSDOE29 |
| `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | GEMSDOE30 |
| `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | GEMSDOE31 |
| `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | GEMSDOE32 (filename/score link **not authenticated**) |
| `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | GEMSDOE33 |
| `h34-scatter-q50-arr-matched-20261004T223317Z` | 0.0778 | GEMSDOE34 |
| `h35-06-aaa86efb25-20261004T225420098147Z-candidate` | 0.0418 | GEMSDOE35 |
| `h40-e-disc-h40e-30k-zeros` | not supplied | GEMSDOE39 |

The prompt also listed several artifacts with no score. They remain “score not supplied,” not zero. The table intentionally preserves exact user-supplied identifiers and does not imply that similarly named TIFFs are byte-identical.


## Preserved source URLs

- **DrivenData GEMS overview** (official): https://www.drivendata.org/competitions/306/competition-doe-gems/
- **Official target, metric and GeoTIFF format** (official): https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- **Official background and research resources** (official): https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- **Competition downloads (login required)** (official): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- **Official participant leaderboard** (official): https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- **September 2026 official rules** (official): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- **Staff clarification: catalogue pixels excluded in both rounds** (official): https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516
- **Staff withholds test-data sources, types and coverage** (official): https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527?print=true
- **USGS GeoDAWN data release** (official): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- **USGS Quaternary faults / current GIS downloads** (official): https://www.usgs.gov/programs/earthquake-hazards/faults
- **USGS free elevation products** (official): https://www.usgs.gov/3d-elevation-program
- **USGS ASTER hydrothermal alteration** (official): https://mrdata.usgs.gov/surficial-mineralogy/ofr-2013-1139/
- **DOE GDR INGENIOUS, CC BY 4.0** (official): https://gdr.openei.org/submissions/1391
- **Organizer-provided CPU/GPU reference solution** (official): https://github.com/drivendataorg/gems-prize-reference-solution
- **Lei et al. split conformal, author manuscript** (primary_research_or_software): https://www.stat.berkeley.edu/~ryantibs/papers/conformal.pdf
- **Sare et al. 2019 scarp templates** (primary_research_or_software): https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018JB016886
- **GDAL internal TIFF nodata masks** (primary_research_or_software): https://gdal.org/en/stable/drivers/raster/gtiff.html
- **Rasterio nodata-mask documentation** (primary_research_or_software): https://rasterio.readthedocs.io/en/stable/topics/masks.html
- **GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html
- **6GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/6GEMSDOE/
- **GEMSDOE3** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html
- **GEMSDOE2** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html
- **GEMSDOE4** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE4/
- **5GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html
- **7GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/7GEMSDOE/
- **8GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/8GEMSDOE/
- **GEMSDOE9** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html
- **11GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html
- **12GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html
- **15GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html
- **14GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html
- **17GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/17GEMSDOE/
- **18GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/18GEMSDOE/
- **19GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html
- **GEMSDOE10** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE10/
- **13GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/13GEMSDOE/
- **16GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html
- **GEMSDOE21** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE21/
- **20GEMSDOE** (secondary_owner_page): https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html
- **GEMSDOE22** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html
- **GEMSDOE23** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE23/
- **GEMSDOE24** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE24/
- **GEMSDOE25** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE25/
- **GEMSDOE26** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE26/
- **GEMSDOE27** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE27/
- **GEMSDOE28** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE28/
- **GEMSDOE29** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html
- **GEMSDOE30** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE30/
- **GEMSDOE31** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE31/docs/
- **GEMSDOE32** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html
- **GEMSDOE33** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE33/
- **GEMSDOE34** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html
- **GEMSDOE35** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html
- **GEMSDOE36** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE36/docs/
- **GEMSDOE37** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE37/
- **GEMSDOE38** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html
- **GEMSDOE39** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE39/
- **GEMSDOE40** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html
- **GEMSDOE41** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html
- **GEMSDOE42** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html
- **GEMSDOE43** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html
- **GEMSDOE44** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE44/docs/
- **GEMSDOE45** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE45/
- **GEMSDOE46** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE46/
- **GEMSDOE47** (secondary_owner_page): https://buffedlizard55-lab.github.io/GEMSDOE47/

Named-only requested siblings: 48GEMSDOE/49GEMSDOE. The visible public inventory contains GEMSDOE48/GEMSDOE49; no nonexistent alternate Pages URL is fabricated.

## Additive reconciliation of concurrent main work

While C1 ran, PRs #8–#11 merged session 3 and H48. Their code, data receipts, results and TIFFs are
preserved additively: [Session 3](docs/session3.html), [H48 research](docs/research.html),
[all historical artifacts](docs/all-downloads.html), [original session3 brief](README-session3.md).
All remain non-promoted; no pooled/private score comparison across their differing proxy frames is
valid. H48's adaptive-history lower-bound calculation is not recertified as finite-sample coverage by this merge.

Namespace collision resolved without changing C1's frozen conformal bytes: H48's original implementation
is preserved byte-for-byte as `src/gems47/h48_conformal.py`, with only its caller imports adjusted.
The relocated H47-B/annulus files stay in `docs/downloads/superseded/`; references are synchronized.
Current C1 artifact, original code/data/history hashes and gate result do not change. New artifact
comparisons and the whole merged suite are rechecked before PR merge.


### Official-source receipt update after additive reconciliation

Runner 37536709561 verified all three public archives and coverage. USGS national traces: 82,841
footprint cells (58,800 exact-catalogue); GDR traces: 82,871 (58,876 exact-catalogue); paleo point
cells: 244. These all_touched pixel counts are not fault counts or expert-new truth. The earlier
USGS expansion-budget issue was fixed by reading geometry only, not the 203MB attribute table or
GDB. No vector trained C1. Sources, hashes and runner attestation are in the deployed JSON.

### Preserved H47-B follow-up — supplemental, not the current download

The later single-scale H47-B control remains available as a [separate audit page and research-only TIFF](docs/h47b-mask-audit-20261006.html); it does **not** replace H47-C1 as the site’s current primary artifact. The single-scale locked pooled known-catalogue-mask proxy DTI was 0.02563947, below H47-B cross-scale (0.02755344) and fixed-seed random (0.03715911). The nominal 6/7 (~85.7%) split-conformal calculation assumes unverified block-score exchangeability and clips to a zero assumption-conditional lower-bound estimate; it is not missing-fault or private-score coverage.

Its local strict format pass uses the explicit mirrored sample-template mask. That mask differs from the feature-derived footprint by 1,540 feature-valid cells outside and 3,061 sample/label cells invalid in features; official footprint semantics and portal acceptance remain unknown. The historical range-error cause is not proved. The paired all-finite TIFF is only an encoding diagnostic. See [IR-23](docs/irregularities.md) and the [complete artifact register](docs/all-downloads.html).

## Publication receipt

* H50 screen, field scans, budget profile and instrument ranking: `evidence/h50/`.
* Artifact builder: `scripts/build_submission_h50.py`; site updater: `scripts/update_site_h50.py`.
* Detector: `src/gems47/h50.py`; tests: `tests/test_h50.py`.
* Published artifact and receipts: `docs/downloads/gems47-h50-slopeanom-s2p8-20261007-*` and
  `docs/data/h50-artifact.json`.
* Site pages: `docs/index.html`, `docs/executive-summary.html`, `docs/h50.html`,
  `docs/all-downloads.html`, `docs/HOW_TO_SUBMIT.md` / `.html`, `docs/submit.html`,
  `docs/portal-checklist.html`.
* H50a sibling artifacts from `main` are preserved and registered as research-only.
* Test suite: 288 passed, 1 skipped, 7 subtests passed (before the `main` merge).
* Generative-AI assistance (Arena.ai coding agent) is disclosed here and in the official narrative.

**Remaining work and limitations for the next session**

1. Instrument L is slope-sharing and therefore optimistic for a slope field; it is a proxy, never a
   private-label or leaderboard guarantee. A structurally independent second instrument is the top
   priority.
2. Block-score exchangeability is assumed and unverified, so the 0.0957 floor is conditional.
3. The budget of 37,654 dots is justified by the credit bar and the family-best mass regime, not by
   the instrument: on Instrument L the marginal dot keeps paying up to 120,000 dots, so L cannot
   determine the budget.
4. The artefact writes zeros outside the footprint, which does not satisfy the official
   "null or NaN outside data bounds" wording literally. A NaN-outside fallback is published beside
   it; if the portal rejects the zeros convention, switch to the fallback and record the receipt.
5. No organiser receipt links any participant score to a TIFF. 0.2778 stays an owner-reported
   comparator, never an authenticated incumbent.
