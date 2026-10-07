# H60–H64 — preregistered hypothesis slate, 2026-10-07 (GEMSDOE47, session 5)

> Written and committed **before** any score in this round is computed. The blocked-holdout
> design, the instruments, the controls, the field definitions and the promotion gate below
> are frozen. Nothing in this document may be edited after the first score exists; corrections
> go to a separate erratum file. Identifier note: H51–H58 are already used by the sibling
> repositories GEMSDOE48/50/52, so this session's candidates are numbered H60–H64 to keep
> family-wide identifiers unique.

## Where this comes from

The previous session shipped **H50** (rank of band 19 `det_elev_slope` above its 25 px
Gaussian regional level, emitted as 37,654 unit dots at 2.8 px spacing off the catalogue) and
its handoff (`docs/next-session.md`) named the next steps:

1. *Top priority:* a **second, structurally independent instrument** for the off-catalogue
   scarp population, because Instrument L (off-catalogue local maxima of the 1 m lidar scarp
   stack) shares the slope quantity with the H50 field's input band.
2. The **per-trace budget reallocation** emitter variant (the only untested emission variant
   from the H50 round).
3. Verified official high-resolution DEM coverage before proposing a 1 m detector.

This session attacks (1) and (2) directly, and adds the one field family nobody in the
GEMSDOE1–54 family has emitted: **the lidar scarp stack's own amplitude as the emission
field** (it has only ever been used as a truth population, as multiplicative corroborators
that failed, or inside the retired LATI fit).

## Provenance correction carried into this round (IR-2026-10-07-A)

The H50 documentation calls the 1 m lidar scarp stack "organiser-supplied". The restore
manifest (`registry/data_manifest.json`, entry `ext_lidar_scarp_features_u8`) is
authoritative and says otherwise: the stack was **derived by the owner's CI from USGS 3DEP
1 m DEM tiles** (706 of 716 tiles; tile list OCR-recovered from the competition PDF; work
resolution 2 m; quantisation rule and per-channel meanings in
`data/external/lidar_scarp_features.json` in GEMSDOE24 at the pinned ref). USGS 3DEP products
carry no use restrictions. All new text in this round says "owner-derived"; the H50 wording
is corrected in the README and flagged in the irregularities register. Nothing about the
bytes changes.

## The scientific argument, stated before measurement

* The only local proxy populations whose DTI is **positively** rank-correlated with the 13
  owner-reported public scores are off-catalogue local maxima of the owner-derived 1 m lidar
  scarp stack (`evidence/h50/instrument-ranking.json`: lappos t200 d5 Spearman +0.576
  p=0.044; lappos t200 d3 +0.548; cross t150 d3 +0.532; lapneg t150 d3 +0.504). Every
  fault-catalogue proxy is at zero or negative correlation.
* Among the seven *real-detector* submissions of the family (excluding the synthetic lattice
  and the placeholder), leaderboard score ≈ 3.4–5.0 × lappos-DTI, a roughly constant ratio:
  d2.8 0.26/0.0585 = 4.44, h33-2-b2 0.2778/0.0555 = 5.00, h19-5 4.31, h28 3.56,
  h25-ctx 3.40, hedge 3.82. The lattice is the counterexample that mass discipline matters
  (highest lappos-DTI of the 13, score only 0.0904), so budget stays at the family's
  measured-best ~37.6k unit dots.
* The hidden labels therefore behave, for every measured family emission, like a population
  that is *harder to hit than nothing but proportional in difficulty* to the lidar scarp
  population. The direct implication — untested until now — is that an emission that ranks
  the lidar scarp evidence **itself**, rather than a 100 m slope proxy of it, should dominate
  every previous family field on the same budget.
* Known noise sources for a lidar-scarp field, from the owner's own caveats: roads, channels,
  terrace risers, paleo-shorelines, landslides, mines. Two of these have on-grid distance
  rasters in the pinned family mirrors (US Census TIGER road distance; BLM closed-claim
  distance). H60 masks them at fixed radii chosen **now**: roads < 250 m, closed claims <
  150 m. These radii are not tuned after seeing scores.

## The slate (ranked by expected DTI improvement × implementation cost)

### H60 — lidar scarp-crest amplitude field (rank 1, the round's primary candidate)

* **Layers.** The owner-derived 1 m lidar scarp stack channels `step_max`, `lappos_max`,
  `lapneg_max`, `upface_max`, `downface_max`, `cross_max`, plus its `valid` channel, plus the
  TIGER road-distance and BLM closed-claim-distance rasters (new manifest entries, hash-
  pinned, from the same GEMSDOE24 ref as the stack itself).
* **Physical signature.** The scarp's own amplitude — step height, crest convexity, base
  concavity, up/down-facing and across-slope band-passed gradients — measured at 2 m and
  aggregated to 100 m. This is the *direct detector*, not the 100 m slope proxy (band 19)
  that H50 ranks.
* **Why it should catch a catalogue-missing fault.** The catalogue is a compilation of
  *mapped* traces assembled from older mapping; a vegetation-obscured or basin-interior
  Quaternary scarp is absent from it precisely because nothing except metre-scale topography
  reveals it. The stack measures that topography directly, so its ranking is blind to mapping
  status. The road/claim masks remove the loudest non-tectonic step sources named in the
  owner's caveats.
* **How it differs from anything already implemented.** No prior arm in GEMSDOE1–54 has
  emitted on the lidar channels as a field. GEMSDOE47 used them only as truth (Instrument L),
  as multiplicative corroborators (H50-E products — all degraded the slope field), and as one
  of 72 layers inside the retired LATI leaderboard fit. GEMSDOE48's H52/H54 added *small*
  gated lidar dot sets to the existing family-best surface; H60 is a from-scratch field on
  the same budget, which is a different hypothesis: that the lidar evidence alone, properly
  masked and spaced, is a better field than the corroborated-ridge chain.
* **Definition (frozen).** For each of the six channels: dequantise is monotone in the u8
  code, so rank the raw code over the emission domain; the field is the **per-cell maximum of
  the six channel ranks**, then `rank_scale` over the emission domain; cells with
  `valid == 0`, road distance < 250 m, or closed-claim distance < 150 m are excluded from
  emission. Emission: greedy spaced selection, spacings {2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.6},
  budget 37,654.
* **Cost.** Low (channels are already on-grid; two new hash-pinned mirrors).

### H61 — per-trace budget reallocation of the H50 field (rank 2)

* **Layers.** The H50 field itself (band 19 above its 25 px regional level, global rank).
* **Physical signature.** Fault truth is *elongated*: one dot per ~280 m along a trace covers
  the trace's kernel credit, so a budget spread across many traces can raise recall where a
  global greedy concentrates on the few strongest traces.
* **Why catalogue-missing.** Same argument as H50 (this changes the emitter, not the field);
  the untested variant named in the previous session's handoff.
* **How it differs.** The H50 emission is global greedy; the rejected H50-D arm was a
  per-pixel anisotropic *exclusion* rule. Per-trace *allocation* has never been run.
* **Definition (frozen).** Threshold the H50 field at its emission-domain 90th percentile;
  label connected components with 8-connectivity; inside each component rank the field
  within-component; allocate `max(1, round(BUDGET · area_k / total_area))` dots to component
  k; emit greedy spaced selection *within* each component at the swept spacing.
* **Cost.** Low–medium (one labelling pass; the greedy loop runs per component).

### H62 — additive slope-anomaly × lidar-amplitude mixture (rank 3)

* **Layers.** Band 19 (via the H50 field) + the H60 lidar field.
* **Signature.** A cell that is both a 100 m slope anomaly and a 1 m scarp is the strongest
  combined evidence; every previous combination in the family was **multiplicative** (AND
  gates, which discard), an additive 50/50 rank mixture has never been tried.
* **Definition (frozen).** `rank_scale(0.5·rank(H50 field) + 0.5·H60 field)` over the
  emission domain, same masks as H60, same sweep.
* **Cost.** Trivial given H60 and H50 exist.

### H63 — catalogue-adjacency-gated lidar field (rank 4)

* **Layers.** The H60 field restricted to cells within 10 px (1 km) of the catalogue.
* **Signature / rationale.** Staff state new faults can be *newly mapped geometry of existing
  fault systems*; the retired LATI fit put the strongest single geological weight on the
  0–1.5 px catalogue-distance band, and the family's strike-decomposition found along-strike
  continuation the best flank explainer. This arm tests the "hug the known systems" pole
  against H60's "everywhere the lidar says" pole.
* **Cost.** Trivial.
* **Note.** The H50 round measured that *excluding* a catalogue flank buffer hurts (0 px
  buffer best) — that is the opposite manipulation (removal, not requirement); H63 is not a
  re-try.

### H64 — instrument refinement study (infrastructure, not a field)

* **Question.** Which off-catalogue proxy population best reproduces the leaderboard
  ordering of the 13 scored artifacts — in particular, does stratifying lidar peaks by
  catalogue distance (≤3 px vs >3 px), or filtering them by the road/claim masks, sharpen
  the positive correlation? This is the "second, structurally independent instrument"
  priority approached the only way this sandbox allows (no USGS QFaults geometry is
  obtainable here: `earthquake.usgs.org` is unreachable from this sandbox, the GDR CSV
  carries centroids/attributes only, and the sibling GEMSDOE50 H56 probe measured
  `traces_usable: 0` from that CSV).
* **Method.** For each candidate population: DTI of each of the 13 restored scored rasters
  against it, Spearman/Kendall vs owner-reported scores, two-sided permutation p (20,000
  draws, seed 20261007) — the exact machinery of `evidence/h50/instrument-ranking.json`.
* **Populations (frozen list).** lappos/lapneg/step/cross/upface peaks at t200 d3 stratified
  by catalogue distance (near ≤3 px, far >3 px); the same with the H60 road/claim mask
  applied; `ex_max` and `coh100` peaks at t200 d3; `union_t200_d3` stratified near/far.
* **Cost.** Low. Results are diagnostics and are reported whatever the gates say.

## Frozen blocked-holdout design (identical to the H50 screen)

* 8 × 8 contiguous blocks, 3 px guard, roles assigned by `numpy.random.default_rng(500610)`
  before any score is computed, blocks with no evaluated pixel dropped before roles, blocks
  with zero truth kept. Budget split across blocks in proportion to evaluated pixels,
  37,654 total. Spacings {2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.6}.
* Primary instrument: **`lappos_t200_d3`** (off-catalogue local maxima of `lappos_max`,
  threshold 200, min-distance 3, valid lidar, inside footprint, off catalogue) — frozen from
  the H50 screen for comparability. Secondary instruments: lapneg t200 d3, step t150 d3,
  cross t200 d3, upface t200 d3, union t200 d3, SGMC off-catalogue (>300 m, whole
  components).
* Controls: fixed-seed spaced **random** field with the same greedy emitter, spacing and
  per-block budget as the candidate; the **owner-reported d2.8 reference** raster; **H47-C1**;
  and the **H50 emission itself** as the incumbent anchor.
* Conformal: max-over-settings one-sided split conformal at 0.90 (`gems47.conformal.
  simultaneous_lower_bounds`, Lei et al. JASA 2018 Algorithm 2), selection half chooses the
  operating point, calibration half certifies it, per arm.

## Frozen promotion gate

A new arm is promoted over H50 as "the file to submit" only if **all** of:

1. pooled selection-half primary-instrument DTI ≥ **1.10 ×** the H50 anchor's (for H60/H62/H63
   this comparison is circular-optimistic because the primary instrument is derived from the
   same stack the fields read; it is necessary, never sufficient);
2. **positive** simultaneous split-conformal floor at the selected operating point (0.90
   nominal, same max-residual machinery);
3. pooled selection-half **sgmc_offcat** DTI ≥ the mass-matched random control's sgmc value
   (independent-population floor: the field must beat random on an independently compiled
   fault population, not only on the quantity it reads);
4. ≥ 3 × the mass-matched random control on the primary instrument;
5. uniqueness: zero exact positive-mask matches against every comparable prior raster
   reachable from this checkout, and max Jaccard < 0.5 (exact number reported either way);
6. format: single-band float32 GeoTIFF, EPSG:32611, official transform/shape, every cell
   finite in [0,1], 0.0 outside the footprint, all strict read-back checks pass.

If several arms pass, the winner is the one with the **highest pooled selection-half
sgmc_offcat DTI** (the most independent instrument), tie-broken by the higher conformal floor.
If no arm passes, H50 remains the file to submit and every result above is published as
research-only with its receipts. No competition submission slot is spent by anything in this
document; the artefact, if promoted, is published for the owner to upload.

## Honesty boundaries (do not drop when publishing)

* The primary instrument is derived from the same owner-built stack that H60/H62/H63 read;
  their primary-instrument numbers are optimistic by construction and are never quoted
  without this sentence.
* The 13 owner-reported scores are not organiser-authenticated per-TIFF receipts; the
  h33-2-b2 → 0.2778 attribution remains an assumption (IR-47-002).
* Block-score exchangeability is unverified; every conformal statement is
  assumption-conditional and covers one future block's proxy DTI, not the private leaderboard.
* The restored rasters are hash-pinned owner mirrors, not organiser-authenticated bytes.
* USGS QFaults trace geometry (the best candidate "manually compiled regional fault map")
  is named but not obtainable from this sandbox; the hash-pinned `Qfaults_GIS.zip`
  (sha256 447eadc5…, fetched by the family's GitHub runner on 2026-10-06) is the documented
  route for a future unrestricted session.
