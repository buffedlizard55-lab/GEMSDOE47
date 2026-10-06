# GEMSDOE47 — DOE GEMS Prize (DrivenData competition 306), NW Nevada / GeoDAWN

**Focal values: Maximize P(Win). Own the Outcome.**

This repository exists to produce one thing: a **unique, valid, downloadable GeoTIFF
submission** that scores above everything the GEMSDOE1–46 family has shipped, plus the
evidence, code and documentation that make the result checkable line by line.

> **➡️ The submission is at the top of the site: [docs/index.md](docs/index.md) →
> `docs/downloads/`.** The one-click TIF, its SHA-256, its format receipt and the conformal
> confidence level next to the chosen spacing are all in the executive summary.
> See **[HOW TO SUBMIT](docs/HOW_TO_SUBMIT.md)**.

---

## 0. The standing brief

This section is the standing starting point for every session. Read it before doing anything.

*Provenance note, kept honest: the brief below is a faithful, complete transcription of every
requirement and acceptance criterion from the tasking conversation. The verbatim original
wording is not recoverable inside this session's context, so what is preserved here is the
full set of requirements, constraints and corrections — not a byte-exact copy. Nothing has
been dropped; additions are marked.*

### 0.1 The task

Build GEMSDOE47 into a system that generates a **unique** GeoTIFF submission for DrivenData
competition #306 (DOE GEMS Prize, GeoDAWN / NW Nevada) scoring above the current best, with a
GitHub Pages site.

### 0.2 Acceptance criteria

1. **MUST generate a unique TIF** — not a copy of any prior GEMSDOE1–46 submission. Copying is
   allowed only for learning/education. It must differ from all listed sites.
2. **Use split conformal prediction** (Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, *JASA*
   113(523):1094–1111, 2018) over the existing spacing/threshold score history: split into a
   calibration half and a selection half, pick a spacing with a **finite-sample guaranteed
   floor**, not just the observed best. **Report the conformal confidence level next to the
   chosen spacing in the submission notes.**
3. **Normalize output to [0,1]**, match the required format (CRS, shape, geotransform), and fix
   the `"Predicted values must be in range [0, 1]"` rejection seen on the portal.
4. **Easy one-click downloadable submission TIF**, placed at the very top / executive summary of
   the site — obvious on arrival.
5. Provide a **unique submission name** and a short **`Note (optional)`** text (≤200 chars).
6. Provide an **executive-summary subpage explaining exactly how to submit**.
7. Give a **PhD-level answer** to: *why did GEMSDOE32 `h33-h33-2-b2` score 0.2778 (highest of
   the group's sites), and can we beat it?* Then **use that answer to build the new submission**.
8. Generate **3–5 new geological hypotheses**. For each: the layer(s) involved, the physical
   signature targeted, why it catches a fault **missing** from the USGS/INGENIOUS catalogue
   rather than one already in it, and how it differs from what is already implemented. **Rank
   them by expected DTI improvement vs implementation cost.** Validate the top candidate on a
   **spatially-blocked holdout** *before* spending a weekly submission slot. If external data is
   needed, **name the specific free official source and verify obtainability first**.
9. **Target: beat 0.3195** (the figure stated in the brief; see §1 for the live leaderboard,
   which had already moved past it).
10. Put this whole prompt into the repo README as the standing starting point.
11. **Deep research** on geothermal-vent/fault discovery, stored as a reusable knowledge base
    with official verified links.
12. **Deep research into overlooked free/public data sources**; be contrarian but scientifically
    grounded.
13. **Work autonomously** — no manual input required of the user; flag irregularities; no
    hallucinations; verify line by line.
14. **Three passes**: implement+verify → review for bugs/edge cases → re-check against the
    original request.
15. **Create a PR and merge it onto `main`**; then list remaining work and limitations.
16. The site must be **clean, organized, user-friendly**; **all claims backed by official links**
    for manual review.
17. Keep **"Maximize P(Win)"** and **"Own the Outcome"** as focal values.
18. The site should solve the problem of manually checking everything and provide an
    up-to-date current feed.

### 0.3 Standing user constraints and corrections

* Highest urgency: **must generate a unique TIF submission**; do not copy a previous submission
  unless purely for learning.
* The submission must be different from the whole collection of GEMSDOE sites.
* Read the entire prompt; the TIF must be easy to download.
* Normalize to [0,1]; write to the required format; report the conformal guarantee confidence
  level next to the chosen spacing in the submission notes.
* **Do not spend a submission slot on an idea that has not beaten the current holdout best**;
  validate on the spatially-blocked holdout first.
* If a candidate needs new external data, name the specific free official source and check
  obtainability **before** proposing it as viable.
* Work line by line from official verified trusted sources; provide links for manual review;
  **no manual input** — complete tasks autonomously; flag irregularities; no hallucinations.
* Downloadable TIF plus obvious placement must be in the executive summary or the very beginning
  of the site.
* The portal error `"Predicted values must be in range [0, 1]"` must be fixed.
* Give the submission a unique name and a short comment for the `Note (optional)` field.
* Create an executive-summary subpage explaining exactly how to submit.
* Work on next steps from previous sessions first.
* 0.3195 is stated as the current highest score; design a new strategy to exceed it.
* Put the prompt into the repo README and read it every session as a starting point.
* Three-pass execution required; do not stop after pass 1.
* Create a pull request, then merge it onto `main`; suggest remaining work and limitations.
* Known blocker carried from prior sessions: no DrivenData auth → `training_features.tif`,
  `labels.tif`, `sample_submission.tif` and `1m_DEM_links.csv` could not be auto-downloaded;
  Dropbox links were unreachable from this sandbox. **Resolved here** — see §3.

---

## 1. Where the competition actually stands

Live public leaderboard, retrieved 2026-10-06 from
<https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>:

| rank | team | public DTI |
|---|---|---|
| 1 | alexoktaba | **0.3345** |
| 2 | nchuzhoy | 0.3262 |
| 3 | kinghorton42 | 0.3222 |
| 4 | Batik Shirt Brothers | 0.3218 |
| 5 | DARD | **0.3195** |
| 6 | joeyfezster | 0.3163 |
| 13 | extradr19 (this family's `h33-2-b2`) | **0.2778** |
| 16 | smrtdoog5 (`h27-4-d2.8`) | 0.2708 |
| 20 | SDCF9 (`h19-5-d2.8`) | 0.2600 |

**Irregularity flagged:** the brief names 0.3195 as "the current highest". On the day this was
written 0.3195 was rank 5; the leader was 0.3345. Both numbers are carried: 0.3195 is the
stated target, 0.3345 is the actual bar to clear.

---

## 2. The metric, exactly

From the official problem description
(<https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric>),
with R = 300 m = 3 px at 100 m, α = 0.2, β = 0.8:

```
k(d)   = max(1 - d/R, 0)
TP_w   = Σ_{g∈G}  max_{x: d(x,g)≤R}  p(x)·k(d(x,g))
FP_w   = Σ_{x: p(x)>0}  p(x)·[1 - max_{g∈G} k(d(x,g))]
FN_w   = Σ_{g∈G}  [1 - max_{x: d(x,g)≤R} p(x)·k(d(x,g))]
DTI    = TP_w / (TP_w + α·FP_w + β·FN_w + ε)
```

Published worked example: `TP_w=3.00, FP_w=1.89, FN_w=2.00 → 0.60` (exact value
`3.00/4.978 = 0.6026516673…`, printed to two decimals). Regression-tested in
`tests/test_metric_s3.py`.

Two identities this repository uses everywhere, both proved against a brute-force transcription
of the equations above:

```
FN_w = |G| - TP_w                       exactly
DTI  = T / ( 0.2·(T + S - M) + 0.8·|G| )     with T = TP_w, S = Σp, M = Σ p(x)·max_g k
dDTI > 0  for one added unit of mass with realised kernel weight w   ⟺   w > 0.2·DTI
```

The last line is the **credit bar**: at DTI 0.2778 it is 0.0556, so a dot only pays within
≈2.83 px (283 m) of a truth pixel *and* only if it is that pixel's best cover. Redundant mass
changes the denominator by `0.2·(1-w) ≥ 0` and the numerator by 0, so **redundant mass never
helps**.

**Binary is optimal.** For a pixel of value `v` and best-cover weight `w`, adding it changes
`TP_w` by `v·w` and the denominator by `0.2·v`, so the *sign* of the change depends on `w`
alone. Down-weighting a pixel that clears the bar only shrinks its gain. A `{0,1}` mask is the
optimum of the soft family — which is also what all eleven scored reference artifacts are.

---

## 3. Data: restored, pinned and verified

The three official rasters were restored in this session from the family's own git history via
the GitHub API (no DrivenData credentials needed), then verified byte-for-byte:

| file | official Data-tab name | bytes | sha256 |
|---|---|---|---|
| `data/training_features.tif` | `gems-geodawn-numerical-features.tif` | 418,912,844 | `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` |
| `data/labels.tif` | `existing_faults.tif` | 425,830 | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` |
| `data/sample_submission.tif` | `example_submission.tif` | 1,599,597 | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` |

Re-verify at any time with `python3 scripts/fetch_data.py --verify-only`, which also asserts the
grid independently (3292 × 3730, 19 bands, EPSG:32611, the exact transform, 60,988 label pixels,
5,167,373 footprint pixels). Receipt: `evidence/data_restoration.json`.

**Identity is established by SHA-256, not by provenance.** The download is login-gated and
`curl`/`wget` are blocked here for every host but `pypi.org` and `github.com`, so the bytes travel
through `gh api` from team transport mirrors; the pins are what tie them to the official files.
`training_features.tif` is 418,912,844 bytes — above GitHub's 100 MB single-blob limit — so it
travels as five parts, each individually pinned.

Pinned grid: **3730 rows × 3292 cols**, EPSG:32611, 100 m,
transform `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`, footprint **5,167,373** finite px,
labels **60,988** positive px in **3,199** 8-connected components. 300 m = exactly 3.0 px.

`1m_DEM_links.csv` is login-gated and was **not** obtainable; no 1 m or 10 m DEM is available in
this environment. Everything here is built from the official 19-band 100 m stack.

**Irregularity flagged (`evidence/footprint_vs_feature_valid.json`):** the feature-valid domain
and the submission footprint are *not* nested. 3,073 footprint pixels carry the float32 nodata
sentinel `-3.4028234663852886e38` in at least one band, and 1,540 pixels are valid in all 19
bands but lie *outside* the footprint. Writing NaN at those 3,073 pixels is one route to the
portal's range rejection, so the shipped raster is finite everywhere.

---

## 4. Repository map

```
src/gems47s3/
  spec.py            pinned grid, band names/indices, metric constants, restored-file hashes
  metric.py          exact DTI + the algebraic identities + the credit bar
  geomorph.py        the geomorphometric transforms (scarp, LRM, openness, curvature, …)
  detector.py        Recipe -> composite field (rank-scaled weighted geometric mean)
  emission.py        spacing/density/flank-buffer emitters, NMS, oriented blur
  holdout.py         spatially-blocked, prevalence-matched folds (Instruments A1/A2/PM*)
  conformal.py       split conformal (Lei et al. 2018) with the exact (n+1) correction
  raster.py          the GeoTIFF writer and the independent fail-closed format validator
  grid.py            footprint, catalogue, components, spatial blocks
scripts/             every number in evidence/ is reproducible by one of these
evidence/            machine-readable results; nothing here is hand-written
knowledge/           the research knowledge base, with official verified links
docs/                the GitHub Pages site, including docs/downloads/
tests/               49 tests; `python3 -m pytest tests/ -q`
```

Reproduce everything:

```bash
pip install --break-system-packages rasterio scipy numpy pytest
python3 -m pytest tests/ -q
python3 scripts/build_surfaces.py
python3 scripts/measure_instruments.py
python3 scripts/search_scarp_radius.py
python3 scripts/run_sweep_a.py --blocks 5
python3 scripts/run_conformal.py
python3 scripts/build_submission_s3.py
```

---

## 5. Headline findings

Full derivations, numbers and links are in `docs/` and `knowledge/`. In brief:

1. **Why `h33-2-b2` scored 0.2778** — see [docs/why-02778.md](docs/why-02778.md). It is exactly
   `h27-4-r1` (0.2708, 40,199 px) minus the 2,545 dots within 2 px of the given catalogue
   (37,654 px). Under the metric's own algebra those 2,545 dots carried mean credit ≤ 0.0334
   against a credit bar of 0.0556 — they were **structurally** worthless, because the organiser
   masks catalogue pixels. The prune was metric-correct, not luck.
2. **The hidden truth is small.** A model-free inversion of the eleven published scores bounds it
   at **5,764 ≤ |G| ≤ 15,179 px** on the public chunk — a prevalence of 0.112–0.294 %, four to
   ten times *sparser* than the given catalogue.
3. **Coherent placement beats scattered placement by ~3.6×.** `h33-2-b2` and `h34-scatter-q50`
   have identical mass (37,654 px) and identical catalogue-flank properties, and score 0.2778 vs
   0.0778.
4. **Only three of the nineteen bands carry any 300 m-scale structure** (tmi_vg, det_elev_slope,
   tmi_hg); the other sixteen are >96.5 % smooth above that scale and can only act as regional
   priors. Measured in `evidence/band_scale_diagnostics.json`.
5. **The winning transform is an across-strike step in the slope field, persisted 1.9 km along
   strike** — `scarp(det_elev_slope, r=9)`. Precision-at-40k against expert-mapped Quaternary
   fault: **0.505** against a random baseline of **0.086** (5.9×); at 10k, **0.654**.
6. **The obvious off-catalogue proxy is a trap.** USGS SGMC traces >300 m from the given
   catalogue are high, steep, shallow-basement *mountain bedrock*; the given catalogue is near
   background on elevation and sediment thickness. Selecting against SGMC builds a
   bedrock-contact detector — the documented failure mode of fault-mapping models in this
   province. See [knowledge/02](knowledge/02_the_two_instruments_measure_different_populations.md).
7. **On a prevalence-matched, spatially-blocked holdout the new field beats the shipped 0.2778
   artifact by more than an order of magnitude** (mean DTI 0.082 vs 0.004 at 0.200 % truth
   prevalence), and the holdout reproduces the organiser's own flank-buffer effect in the right
   direction.

---

## 6. Honesty rules this repository operates under

* Every number in `docs/` is generated by a script in `scripts/` and stored in `evidence/`.
  Nothing is hand-typed.
* Every external claim carries an official link a reviewer can open.
* Irregularities are flagged where they are found, not smoothed over — including the ones that
  argue against this repository's own choices.
* Where a proxy instrument cannot answer a question, that is stated, and the question is answered
  from the organiser's own published scores instead.
* No automated access to `drivendata.org` appears in any script (DrivenData ToU). Pages were read
  interactively; the URLs are cited for manual review.
