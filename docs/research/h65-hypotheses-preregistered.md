# H65–H70 — preregistered hypothesis slate, 2026-10-08 (GEMSDOE47, session 6)

> Written and committed **before** any score in this round is computed. The blocked-holdout
> design, the instruments, the controls, the field definitions and the promotion gate below
> are frozen. Nothing in this document may be edited after the first score exists; corrections
> go to a separate erratum file. Identifier note: H51–H58 are used by the sibling
> repositories GEMSDOE48/50/52 as of 2026-10-07 and H60–H64 by GEMSDOE47 session 5, so this
> session's candidates are numbered H65–H70 to keep family-wide identifiers unique. **Flag
> for review:** sibling numbering after 2026-10-07 was not re-checked from this sandbox; if a
> sibling has since claimed H65+, renumber this slate before building any artifact.

## Where this comes from

Session 5 shipped **H60** (per-cell maximum of the emission-domain ranks of six scarp
channels of the owner-derived 1 m lidar stack, road/claim masked, 2.0 px, 37,654 dots) after
it passed a six-condition gate on the frozen 41-block spatially blocked holdout, and published
two refutations (H61 per-trace reallocation, H63 catalogue-adjacency gating) plus the H64
instrument study. The session-5 handoff (`docs/next-session.md`) named the next steps; this
slate executes them in priority order:

1. *Spacing below 2.0 px.* H60's selection-half mean rises **monotonically to the sweep
   edge** (0.2844 at 2.0 px; H62 likewise at 0.2326), so the operating point was never
   interior. This round extends the sweep downward.
2. *Domain/mask ablation.* H64 measured that the road/claim masks **improve** the
   instrument–leaderboard correlation (step +0.592 masked vs +0.449 unmasked), but the radii
   (250 m road / 150 m claim) were frozen guesses, never swept.
3. *Field refinement.* H64 ranked the lidar channels by leaderboard correlation: step
   (+0.592) > lappos/lapneg (+0.576) > cross (+0.438) > upface (+0.328). H60's max-of-six
   aggregation may dilute the sharpest channel with the noisiest ones — untested until now.
4. *H62 runner-up re-audit.* H62 passed the old gate and lost only the SGMC tie-break; its
   extended-sweep operating point is untested.
5. *Independent-instrument program.* H64 stratified lidar peaks; this round adds the
   remaining channel (`downface_max`), SGMC threshold/stratification variants, and — as an
   explicitly exploratory diagnostic — the 21 INGENIOUS volcanic-vent pixels. USGS QFaults
   trace geometry remains unobtainable from this sandbox (see below) and is **not** proposed
   as viable this round.

## Provenance carried into this round

* The lidar stack is **owner-derived** from USGS 3DEP 1 m DEM tiles (706/716; tile list
  OCR-recovered from the competition PDF; pinned at `registry/data_manifest.json`), NOT
  organiser-supplied (IR-2026-10-07-B).
* The restored rasters are hash-pinned owner mirrors, not organiser-authenticated bytes; the
  13 owner-reported scores are not organiser receipts; the h33-2-b2 → 0.2778 attribution
  remains an assumption (IR-47-002). The d2.8 raster is the **owner-reported d2.8
  reference**, never an incumbent.
* Block-score exchangeability is unverified; every conformal statement is
  assumption-conditional and covers one future block's proxy DTI, not the private leaderboard.

## The scientific argument, stated before measurement

* H60's primary-instrument gain (+73% over H50) comes with a circularity warning: the primary
  instrument derives from the same owner-built stack the field reads. Its *independent*
  evidence is the SGMC off-catalogue gain (0.1938 vs 0.0698 random, 0.1221 H50) and the
  13-artifact rank correlations. **Anything that displaces H60 as the file to submit must
  therefore beat H60 on the SGMC instrument**, where H60 cannot be circular — the gate below
  requires exactly that.
* H64's channel ranking (step > lappos ≈ lapneg > cross > upface) plus the far > near
  stratification (lappos +0.581 far vs +0.273 near) says the leaderboard-ordered signal lives
  in sharp, far-from-catalogue steps — not in catalogue-hugging emission (H63 refuted at
  0.1567) and not in single-channel noise spikes. H65/H66 test the two aggregation poles of
  that claim; H67 tests a non-lidar mechanism (tip propagation) with zero shared code path.
* Smaller spacing is not free mass: the noise-masked lidar domain held only 17,889 of the
  21,198-dot selection budget at 2.0 px. Smaller spacings raise domain capacity (more dots
  fit), so under-emission should ease downward — every row records actual emitted mass, and
  any arm that cannot place its budget is reported, not hidden.

## The slate (ranked by expected DTI improvement × implementation cost)

### H65 — step-only lidar field (rank 1, the round's primary candidate)

* **Layers.** The owner-derived lidar stack channel `step_max` (10 m-scale minus 50 m-scale
  slope), plus the `valid` channel and the TIGER road / BLM closed-claim distance rasters at
  the frozen H60 radii (250 m / 150 m).
* **Physical signature.** The scarp's own step height at 2 m work resolution, unmixed: a
  Quaternary normal-fault scarp is first and foremost a topographic step, and the H64 study
  measured step peaks (masked) as the single population most rank-correlated with the
  owner-reported leaderboard ordering (+0.592).
* **Why it should catch a catalogue-missing fault.** Same argument as H60 (metre-scale
  topography is blind to mapping status; masks remove road cuts and mine scars), sharpened:
  the max-of-six H60 field lets the weakest channels (upface +0.328, cross +0.438) spend
  budget on cells the best channel rejects. Ranking step alone concentrates the same budget
  on the highest-evidence cells.
* **How it differs.** H60 = per-cell maximum of six channel ranks, re-ranked. No arm has
  emitted on a single lidar channel as a field.
* **Definition (frozen).** `rank_scale(step_max)` over the H60 emission domain (evaluated &
  valid-lidar & noise-ok at 250/150 m); greedy spaced selection on the extended sweep;
  budget 37,654; capped emission with recorded mass (same `_emit_up_to` rule as H60).
* **Cost.** Trivial given H60 exists.

### H66 — Borda-mean (consensus) lidar field (rank 2)

* **Layers.** The same six channels, `valid`, and masks as H60.
* **Physical signature.** Multi-template consensus: a real scarp responds jointly across the
  Sare et al. (2019) template family (step + crest convexity + base concavity together),
  while DEM noise, terrace risers and single-template artifacts spike in one channel only.
  The mean of the six channel ranks rewards corroborated cells; the max rewards any spike.
* **Why catalogue-missing.** Same as H65; the aggregation pole is the opposite of H60's
  ("any evidence") and of H65's ("best single evidence"): "corroborated evidence".
* **How it differs.** Mean-of-ranks aggregation has never been tried; every previous
  combination was max (H60), additive mixture across families (H62), or multiplicative AND
  gates (H50-E, all harmful).
* **Definition (frozen).** Per-cell mean of the six emission-domain channel ranks, then
  `rank_scale` over the H60 domain; otherwise identical emission to H65.
* **Cost.** Trivial.

### Extended spacing sweep 1.4–3.2 px (rank 3, applies to every arm)

* Not a new field: the operating-point refinement the handoff prioritised. Frozen settings
  {1.4, 1.6, 1.8, 2.0, 2.4, 2.8, 3.2} px — seven settings, so the conformal rank arithmetic
  matches the H60 round exactly (rank 20 of 22 at 0.90 nominal), while 2.0 and 2.8 stay in
  the set for bit-for-bit anchor reproduction. Settings above 3.2 are dropped: no surviving
  arm selected above 3.2 (only the refuted H63 chose 4.0).
* Selection rule unchanged: maximise the selection-half mean, tie-break toward larger
  spacing (identical to the H60 round for comparability).

### H68 / H69 — mask-radius ablation of the H60 field (rank 4)

* **Layers / signature.** Identical to H60; only the noise-mask radii change. H68 (relaxed):
  road < 150 m, closed claim < 100 m excluded. H69 (strict): road < 400 m, closed claim <
  250 m excluded. Radii are chosen now, symmetric around the frozen H60 values on a roughly
  doubling/halving ladder, and are not tuned after seeing scores.
* **Why.** H64 proved masks help but never tested the radius values. Relaxed masks enlarge
  the domain (more capacity at small spacings, more fault-adjacent roads kept); strict masks
  purify it (fewer non-tectonic steps, less capacity). One of the two directions should win
  on the independent instrument if the radius matters at all.
* **How it differs.** Radius values have never been swept; H60/H62/H63 all used 250/150 m.
* **Definition (frozen).** Each arm recomputes the H60 field definition (channel-rank-max +
  `rank_scale`) over its own domain (evaluated & valid & noise-ok at its radii); capped
  emission with recorded mass. Recomputation (not reuse of H60's values) is required because
  the relaxed domain contains cells H60 never ranked.
* **Cost.** Trivial.

### H67 — catalogue-tip-proximity field (rank 5, the genuinely new geology)

* **Layers.** `labels.tif` catalogue geometry only — no lidar, no slope band. Candidate tip
  pixels are catalogue pixels with **exactly one** catalogue neighbour in 8-connectivity
  (isolated single pixels have zero neighbours and are not tips); the tip-distance raster is
  the Euclidean distance transform to the nearest tip pixel.
* **Physical signature.** Fault-tip propagation: Quaternary systems grow and link at their
  tips, where displacement tapers below mapping resolution and scarps step blind into basin
  fill. New expert mapping extends systems at tips far more often than it discovers isolated
  far-field faults — the staff-noted "newly mapped geometry of existing fault systems" pole,
  but at tip geometry specifically rather than H63's refuted whole-trace adjacency.
* **Why catalogue-missing.** Tips are sub-resolution by definition: the mapped trace ends
  where the scarp became unmappable, so the catalogue-missing continuation sits within a few
  hundred metres of the mapped tip. This field has **zero shared code path** with the lidar
  stack, so its primary-instrument numbers carry no circularity warning — a clean
  independent-mechanism test.
* **How it differs.** Nothing in GEMSDOE1–54 or this repository has emitted on tip geometry.
  H63 gated *emission* to near-catalogue cells (refuted); H67 *ranks* the full evaluated
  domain by tip proximity, which is the opposite direction of information flow (field, not
  gate) and targets tips, not traces.
* **Definition (frozen).** Field = `rank_scale(1 / (1 + d_tip))` over the plain evaluated
  domain (footprint minus catalogue, no lidar-valid or noise restriction); full-budget
  greedy spaced emission (`h50.emit`, raises if infeasible — the 5.1M-cell domain holds the
  budget at every swept spacing).
* **Cost.** Low (one labelling pass + one distance transform). Highest risk: H63's refutation
  warns that catalogue-hugging hurts; tips are the last catalogue-geometry hypothesis with a
  distinct mechanism.

### H62 re-audit (rank 6, not new — the honest runner-up)

* The H62 additive 50/50 mixture passed the old gate (0.2458 / 0.1850) and lost only the SGMC
  tie-break. It is re-screened on the extended sweep at no extra implementation cost. If the
  extended sweep promotes it over H60 under the new gate, its whole-map emission (untested)
  would be built only under a fresh artifact gate.

### H70 — instrument refinement study, part 2 (infrastructure, not a field)

* **Question.** Same as H64: which off-catalogue proxy population best reproduces the
  leaderboard ordering of the 13 scored artifacts — now covering the populations H64 left
  out: `downface_max` peaks (near ≤3 px / far >3 px / road-claim-masked), SGMC at finer and
  coarser catalogue-distance thresholds (>100 m, >200 m, >500 m vs the frozen >300 m), SGMC
  near (off-catalogue, ≤3 px) vs far (>3 px), and the 21 INGENIOUS volcanic-vent pixels as an
  explicitly exploratory diagnostic (n reported; no conclusion may rest on it).
* **Method.** Identical machinery to H64: whole-map DTI of each of the 13 restored scored
  rasters against each population, Spearman/Kendall vs owner-reported scores, two-sided
  permutation p (20,000 draws, seed 20261008 — the seed differs from H64's because the
  population list differs; the method is identical).
* **Cost.** Low. Results are diagnostics, reported whatever the gates say.

## Frozen blocked-holdout design (identical to the H60 screen except the sweep)

* 8 × 8 contiguous blocks, 3 px guard, roles by `numpy.random.default_rng(500610)` —
  re-derived and asserted **byte-equal** to `evidence/h50/blocks.json` before anything is
  scored. Budget split across blocks in proportion to evaluated pixels, 37,654 total.
* Spacings **{1.4, 1.6, 1.8, 2.0, 2.4, 2.8, 3.2}** px (seven settings).
* Primary instrument: **`lappos_t200_d3`** (frozen from the H50/H60 screens for
  comparability). Secondary: lapneg t200 d3, step t150 d3, cross t200 d3, upface t200 d3,
  union t200 d3, SGMC off-catalogue (>300 m, whole components — frozen definition).
* Controls: fixed-seed spaced **random** field (same greedy emitter, spacing and per-block
  budget, plain evaluated domain); the **owner-reported d2.8 reference** raster; **H47-C1**;
  the **H50 emission** (design anchor, must reproduce 0.16588059959214113 pooled @2.8) and
  the **H60 emission** (incumbent anchor — the current file to submit — must reproduce its
  pooled @2.0 of 0.287891 to 1e-9).
* Conformal: max-over-settings one-sided split conformal at 0.90 (`gems47.conformal.
  simultaneous_lower_bounds`, Lei et al. JASA 2018 Algorithm 2), selection half chooses the
  operating point, calibration half certifies it, per arm.
* Dropped arms: H61 and H63 stay refuted and are not re-screened; their verdicts stand.

## Frozen promotion gate (displacing H60 as "the file to submit")

A challenger (H65/H66/H67/H68/H69, or H62 on its re-audit) is promoted over H60 only if
**all** of:

1. pooled selection-half primary-instrument DTI ≥ **H60's** pooled selection-half primary
   DTI at H60's selected spacing (no regression; circular-optimistic for the lidar-reading
   arms H65/H66/H68/H69/H62, and an independent-mechanism test for H67);
2. **positive** simultaneous split-conformal floor at the selected operating point (0.90
   nominal, same max-residual machinery);
3. pooled selection-half **sgmc_offcat** DTI ≥ **H60's** pooled sgmc_offcat DTI (independent
   superiority: the new file must beat H60 where H60 cannot be circular), and ≥ the
   spacing-matched random control's sgmc value;
4. ≥ 3 × the spacing-matched random control on the primary instrument;
5. uniqueness: zero exact positive-mask matches against every comparable prior raster
   reachable from this checkout **including H60 itself**, and max Jaccard < 0.5 (exact
   number reported either way; computed by the artifact builder);
6. format: single-band float32 GeoTIFF, EPSG:32611, official transform/shape, every cell
   finite in [0,1], 0.0 outside the footprint, all strict read-back checks pass (computed
   by the artifact builder).

If several challengers pass, the winner is the one with the **highest pooled selection-half
sgmc_offcat DTI** (the most independent instrument), tie-broken by the higher conformal
floor, then the higher pooled primary. If no challenger passes, **H60 remains the file to
submit** and every result above is published as research-only with its receipts. No
competition submission slot is spent by anything in this document; an artifact, if promoted,
is published for the owner to upload.

## Honesty boundaries (do not drop when publishing)

* The primary instrument derives from the same owner-built stack that the lidar-reading
  challengers read; their primary-instrument numbers are optimistic by construction and are
  never quoted without this sentence. H67 is exempt (catalogue geometry only).
* The 13 owner-reported scores are not organiser-authenticated per-TIFF receipts; the
  h33-2-b2 → 0.2778 attribution remains an assumption (IR-47-002).
* Block-score exchangeability is unverified; every conformal statement is
  assumption-conditional and covers one future block's proxy DTI, not the private leaderboard.
* The restored rasters are hash-pinned owner mirrors, not organiser-authenticated bytes.
* USGS QFaults trace geometry (the best "manually compiled regional fault map" instrument)
  is named but not obtainable from this sandbox; only the centroid/attribute GDR CSV is
  on-hand (`traces_usable: 0`, confirmed by column inspection 2026-10-08). The hash-pinned
  `Qfaults_GIS.zip` (sha256 447eadc5…, fetched by the family's GitHub runner on 2026-10-06
  per `docs/data/official-download-probes.json`) remains the documented route for a future
  unrestricted session. It is not proposed as viable here.
