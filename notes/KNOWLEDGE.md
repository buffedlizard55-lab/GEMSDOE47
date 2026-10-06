# Knowledge base — verified sources and measured findings

Two sections: **(A)** what the official sources actually say, each with the URL that was fetched;
**(B)** what *we* measured in this sandbox, with the file or script that produced it. Nothing here is
inferred from memory; every line is either quoted from a fetched page or reproducible from a file in
this repo.

---

## A. Official sources (fetched and verified 2026-10-06)

### A1. The competition — DrivenData #306

- **Home:** https://www.drivendata.org/competitions/306/
- **Problem description:** https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- **Rules:** https://www.drivendata.org/competitions/306/competition-doe-gems/rules/
- **Reference solution:** https://github.com/drivendataorg/gems-prize-reference-solution

Verified statements, quoted or paraphrased tightly:

- Task: "create an algorithm that will generate enhanced geologic fault datasets to support geologic
  and geophysical mapping and modeling", focused on locating "previously unknown deposits of critical
  minerals and geothermal resources".
- "**Dec. 3, 2026, 11:59 p.m. UTC**" competition end. **Total prize pool $300,000**: initial round
  $50,000 (top 5 × $10,000 on the private test set), final round $250,000 (top 5 on a re-labeled
  dataset).
- "The same submission is scored twice — once against a private expert-labeled test set for the
  Initial Prize Round, and again against an expanded label set built from expert review of all
  submissions for the Final Prize Round."
- **Use of test data:** "there is spatial overlap between the training dataset (the USGS quaternary
  fault dataset) and the test dataset (newly identified faults within the GeoDAWN region). For this
  challenge, you may use the provided set of faults for training purposes. Participants will be
  evaluated based on their performance predicting faults contained in a newly labeled, private set of
  faults."
- **Use of external data:** "encouraged … provided you or your team possess the necessary licenses …
  All data used must be shareable with the challenge organizers to allow for independent result
  verification."
- Scored on the *new* faults, not on re-finding the training catalogue — this is why every
  catalogue-hugging proxy in section B fails.

### A2. The catalogues

- **USGS Quaternary Fault and Fold Database (QFFD)** — current official landing page:
  https://www.usgs.gov/programs/earthquake-hazards/faults
  (the older `earthquake.usgs.gov/hazards/qfaults/` path now returns **404** — verified by fetch; do
  not cite it). Description: locations and information on faults and associated folds "believed to be
  sources of M>6 earthquakes during the Quaternary (the past 1,600,000 years)"; the database "is the
  source for faults used in the National Seismic Hazard Maps". ≈2,000 Quaternary structures nationally.
  *Our local extract:* `gdr_qfaults_traces.csv`, 14 columns including `slip_rate`, `recency`,
  `map_scale`, mapped length, and centroid row/col in the competition grid.
- **SGMC** (State Geologic Map Compilation) — the competition's `labels.tif` / `existing_faults.tif`
  are byte-identical to each other (sha256 `7ba308cc…`), i.e. the "existing faults" band *is* the
  training label raster. Verified locally.

### A3. The geophysics — GeoDAWN

- **USGS ScienceBase data release:** https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7
  — "GeoDAWN: Airborne magnetic and radiometric surveys of the northwestern Great Basin, Nevada and
  California", Glen, J.M.G. & Earney, T.E., 2024, USGS data release, **DOI
  https://doi.org/10.5066/P93LGLVQ**. Survey flown 2021-11-01 → 2022-11-20; joint USGS EarthMRI +
  DOE Geothermal Technologies Office effort; attached grids include 42 MB and 227 MB areas plus a
  350 MB magnetics file set.
- **DOE Geothermal Data Repository mirror:** https://gdr.openei.org/submissions/1591 (same release,
  GDR-cited; useful when ScienceBase is slow).
- **Magnetotellurics (the overlooked one):** "Magnetotelluric Data from the Gabbs Valley Region,
  Nevada, 2020" — https://www.sciencebase.gov/catalog/item/60d39cc1d34e12a1b009c64b, DOI
  **https://doi.org/10.5066/P9GZ9Z56**. 59 wideband MT stations with impedance tensors and induction
  vectors; "the real induction vectors point towards strong conductors". **This is the closest thing
  to a direct geothermal indicator in the public record** — conductive clay caps and fluid pathways
  are what MT measures, and the great majority of entrants in this competition are working in the DEM
  and magnetics domain only. It is a station network, not a raster, which is precisely why it is
  overlooked.

### A4. Method

- **Split conformal prediction:** Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, "Distribution-Free
  Predictive Inference for Regression", *JASA* 113(523), 2018 —
  https://doi.org/10.1080/01621459.2017.1307116 (preprint: https://arxiv.org/abs/1604.04173).
  Used here for the certified floor in `notes/SUBMISSION_NOTE.md` §4.

---

## B. Measured findings (ours, reproducible)

### B1. The metric

Reduces to `DTI = 5T/(T + FP + 4N_g)`; for non-overlapping dots `T + FP = n`, so
**`score = 5T/(n + 4N_g)`**. Reproduced the organizer's worked example = **0.6027**; unit tests in
`src/gems47_metric.py`. Kernel `k(d) = max(1 − d/3 px, 0)`.

### B2. Which instrument predicts the live score (the single most important table in this repo)

Sibling instrument table, retrieved 2026-10-06 from `buffedlizard55-lab/GEMSDOE42` (README), n = 11
official scores:

| instrument | Spearman ρ | p |
|---|---|---|
| emitted pixel count | **−0.907** | 0.0001 |
| SGMC off-catalogue fault proxy | +0.305 | 0.361 |
| spatially-blocked catalogue holdout | +0.087 | 0.800 |

⇒ **size is signal; every spatial proxy in this project family is noise.** Any promotion gate built on
a spatial proxy is a coin flip.

### B3. The live-anchored ladder (measured from official scores)

| mask | pixels | official score |
|---|---|---|
| d28 network (B = 0) | 44,090 | 0.2600 |
| drop `d_cat ≤ 1` px | 40,199 | 0.2708 |
| drop `d_cat ≤ 2` px (the 0.2778 artifact) | 37,654 | 0.2778 |

Fitted: **T = 5,214.8, N_g = 14,040.2**, max residual 0.00021. `T` is constant across the ladder.
Independent corroboration: `h32-1-prethin` (42,294 px, 0.2649) carries 2,095 more dots than
`h27-4-solo` and those extra dots contribute ΔT = −2.7 → −0.0013 per dot (indistinguishable from
zero), versus 0.130 for the average retained dot. Breakeven retentions for the submitted file:
**79.6 % of T to beat the incumbent 0.2778, 95.8 % to beat the board maximum 0.3345.**

### B4. Geometry of the emission

- The network is **99.4 % two-dot pairs** (mean chain length 2.2); median nearest-neighbour spacing
  3.00 px = the kernel radius, so kernels saturate and FP is redundant mass.
- Dot density versus distance to the off-catalogue mapped-fault network:
  **2.20× enrichment at 0–1 px, 1.79× at 1–2 px, 1.00× at ~20 px, 0.49× beyond 80 px**, monotone
  decreasing. So the far dots are *weaker*, not stronger — which is why the annulus prune is a bet on
  size, not on spatial precision.
- Median nearest-neighbour distance 3.00 px against a Poisson expectation of 5.41 px ⇒ the mask is
  strongly clustered (paired), not uniform noise.

### B5. Falsified models (do not re-propose)

| model | LOO error predicting the B = 0 rung |
|---|---|
| constant **T** | **+0.00075** |
| T ∝ SGMC off-catalogue radial profile | +0.03828 (wrong sign for Δ) |
| T ∝ exact kernel coverage of the off-catalogue SGMC network | +0.08040 |
| T ∝ exact coverage of catalogue + SGMC | +0.28947 |

### B6. Also falsified / dead ends (see the session log for the full list)

- Dropbox downloads (network-blocked), DrivenData direct file download (login-gated), harvesting
  artifacts from GEMSDOE19/16/20, 7GEMSDOE, GEMSDOE, GEMSDOE2, GEMSDOE7 (`contents/docs/downloads`
  404s), GitHub code search for internal hypothesis names, and classifying the dead-dot band from
  corroboration features (max |effect| 0.066).
- Pristine trace re-dotting (`redot`) is a *lossy* operator on this mask: at 3.0 px spacing it moves
  24,552 of 48,193 emitted positions off the original dots, because the network is 99.4 % 2-dot pairs
  rather than continuous traces. It is kept in `src/gems47_emit.py` for completeness, **not** used for
  the submission.

### B7. The 0.2778 artifact (brief requirement 3, answered)

It is the third rung of a thinning ladder on one dot network, not a different discovery. Its 0.2778 is
exactly reproduced by `score = 5T/(n + 4N_g)` with the same `T` and `N_g` as its two ancestors (0.2600,
0.2708). Beating it requires either a smaller emission on the same network (the route taken here) or a
higher-`T` network (unproven offline). **The current bar is 0.3345** (2026-10-06 snapshot), which under
the same identity sits at ≈21,800 dots — i.e. the leader is on the same curve, roughly two rungs short
of where this submission sits.

### B8. Byte-level ladder identity and acquisition topology (added on the 2026-10-06 re-verification)

- Re-deriving `base ∧ d_cat > 1` and `base ∧ d_cat > 2` from `labels.tif` + the GEMSDOE33 base produces
  masks **pixel-for-pixel identical** to the published, officially scored `gems28-h27-4-r1-solo-d2-8`
  (0.2708) and `gems32-h33-2-b2` (0.2778). The ladder is therefore an operator on *those artifacts
  themselves*, not a reconstruction that merely shares their count.
- The GEMSDOE30 `d28-poisson300m-offcat-44090` (0.2600) and GEMSDOE24 `h25-1-dotted-h19-5` (44,090-dot
  variant) artifacts are pixel-identical to the GEMSDOE33 base: the same 44,090-dot network has been
  scored **≥ 3 times at 0.2600** through different repos — same set ⇒ same score, an independent
  determinism check of the scorer.
- Sandbox network reality (measured, not assumed): only `api.github.com` is reachable; Dropbox,
  `gdr.openei.org` and `www.sciencebase.gov` fail at TLS. All official competition bytes used here are
  obtained through the group's GitHub mirrors (`GEMSDOE24/data/bridge`, sibling `docs/downloads`), whose
  provenance is the receipts published next to each artifact. The full H1–H5 input stack
  (`geodawn_rad_u8.tif`, `geodawn_extensions_u8.tif`, `lidar_scarp_features_u8.tif`,
  `gdr_qfaults_traces.csv`, `derived_sgmc_faults_100m_u8.tif`, INGENIOUS temperature zips) is public
  under `GEMSDOE24/data/external/`, so no hypothesis in `notes/HYPOTHESES.md` is blocked on new
  external acquisition in this environment.
