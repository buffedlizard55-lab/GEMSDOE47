# H65–H68 — preregistered hypothesis slate, 2026-10-08 (GEMSDOE47, session 6)

> Written and committed **before** any score in this round is computed. The
> blocked-holdout design, the instruments, the controls, the field definitions, the
> conformal operating-point rule and the promotion gate below are frozen. Nothing in
> this document may be edited after the first score exists; corrections go to a
> separate erratum file. Identifier note: H51–H58 are used by the sibling repositories
> GEMSDOE48/50/52 and H60–H64 by session 5, so this session's candidates are numbered
> H65–H68 to keep family-wide identifiers unique.

## Standing orders this round answers

1. Generate a **unique** TIF submission for the competition — never a copy of a prior
   GEMSDOE submission — with an unambiguous OK-to-download-and-submit label.
2. Pick the operating point (spacing) with **split conformal prediction** (Lei, G'Sell,
   Rinaldo, Tibshirani & Wasserman, JASA 2018, Algorithm 2) on our own spacing sweep: a
   guaranteed floor, not an observed maximum. The confidence level is reported next to
   the chosen spacing in the submission notes.
3. Study the family-high owner-reported 0.2778 (GEMSDOE32 `h33-2-b2`) and answer, with
   measurements, why it scored highest and whether we can beat it.
4. Beat the current leaderboard top (0.3774) — the honest route is a candidate that
   beats the current holdout best on the frozen blocked holdout, on an instrument the
   field does not read.

## What session 5 established (the incumbent)

**H60** — the per-cell maximum of the emission-domain ranks of six scarp channels of the
owner-derived 1 m lidar stack, masked ≥250 m from TIGER roads and ≥150 m from BLM
closed claims — is the current primary. On the frozen 41-block holdout (20 selection /
21 calibration, seed 500610): pooled selection-half DTI **0.287891** on the primary
lidar-peak instrument (`lappos_t200_d3`) and **0.193813** on the independent SGMC
off-catalogue population, against the H50 anchor's 0.165881 / 0.122083, mass-matched
random's 0.046288 / 0.069761 and the owner-reported d2.8 reference's 0.049421 /
0.089879. H64 (instrument refinement) measured: **far-from-catalogue** lidar peaks
correlate better with the 13 owner-reported scores than near ones (lappos +0.581 far vs
+0.273 near); the road/claim masks improve the instrument-leaderboard correlation
(step +0.592 masked vs +0.449 unmasked); `coh100` peaks anti-correlate (−0.532).
H62 (additive 50/50 slope+lidar mixture) passed the gate but lost the SGMC tie-break
(0.245762 / 0.184971). H63 (catalogue-adjacency-gated lidar) was **refuted** (0.156660
/ 0.162911): hugging the catalogue hurts.

## What the h33-2-b2 measurement established (evidence/h33_reference_analysis.json)

The owner-reported 0.2778 raster (`reference/h33-2-b2-zeros.tif`, hash-pinned mirror
from GEMSDOE32; attribution unverified — participant-level leaderboard, no organiser
receipt links the row to this TIFF) is measured, not assumed:

* **37,654 unit dots** at 2.8 px minimum spacing (nearest-neighbour median 3.0 px),
  all off-catalogue, all on the evaluated domain — the family-standard budget.
* It is a **strict subset** of the scored d2.8 raster
  (`gems24-h25-1-dotted-h19-5-d2-8`, 44,090 dots, owner-reported 0.2600; mask Jaccard
  0.854) and of the h19-5 powerlaw raster (121,131 dots, 0.1922). h33-2-b2 is the
  d2.8 emission **pruned from 44,090 to 37,654 dots**.
* **22,447 of its 37,654 dots (59.6 %) sit inside the TIGER-road / BLM-closed-claim
  noise masks** that H60 excludes — the pruned emission spends most of its budget on
  the loudest non-tectonic step sources.
* The pruning mechanism is verified algebraically on this raster: deleting the
  lowest-credit dots leaves TP unchanged (1047.8) while FP falls tenfold, raising the
  whole-map lappos proxy DTI from 0.0555 (all 37,654 dots) to 0.0865 (top 3,765).
  The owner-reported 0.2600 → 0.2778 move is this mechanism: **mass discipline on an
  existing field, not a new geological signal.**

**Consequence for this round:** the 0.2778 route (prune an existing field harder) is
closed to us as a *scientific* strategy — it is a precision play on the h19-5 field,
and our uniqueness gate (max mask Jaccard < 0.5 against every prior raster) would
reject a re-pruning of the same emission. The open route is a **better field**, which
is what H65–H68 test. Our budget stays at the family-measured-best 37,654 unit dots.

## The scientific argument, stated before measurement

* The organiser's own framing: participants should submit predictions for what they
  **truly believe** are faults, "as opposed to simply optimizing for the existing
  labels" (thinkgeoenergy, quoting the organisers). The hidden labels are
  expert-mapped **new** faults; the catalogue is masked out of scoring
  (staff thread 11516). What the experts map is what metre-scale topography reveals —
  which is why the off-catalogue lidar-scarp-peak population is the only local proxy
  whose DTI is positively rank-correlated with the 13 owner-reported scores.
* H60 ranks the lidar scarp *amplitude*; its residual error is the noise that a single
  channel's maximum admits (one operator can fire on a road cut, a terrace riser, a
  resampling seam). **Consensus across independent operators** is the untested
  refinement of the winning mechanism.
* The competition is a **geothermal** prize: the target is fault structure indicative
  of geothermal resources. A fault that hosted or hosts fluid leaves a second,
  independent signature: **hydrothermal alteration**, mapped from airborne
  gamma-ray spectrometry. The USGS GeoDAWN surveys over this exact footprint were
  flown by USGS/DOE *to collect information on undiscovered geothermal resources*
  (USGS GMEQ GeoDAWN page). Airborne Th/K is the standard alteration index:
  argillic alteration leaches potassium, so Th/K rises over altered ground
  (Chiozzi et al. 2006, Th/K 7–11 in K-depleted kaolin vs ~3.6 unaltered; Gnojek &
  Prichystal 1985; Glen & Earney, GRC: "alteration is often manifest as prominent
  shifts in K concentrations"). A scarp that is also a Th/K high is a **sealed,
  formerly or presently active fluid conduit** — the hidden-vent population. No arm in
  GEMSDOE1–54 has ever combined the lidar stack with radiometrics.
* H64 measured that **far-from-catalogue** lidar peaks correlate better with the
  scores, and H63 refuted the near pole. The far pole — emitting only where the
  catalogue is silent beyond one kernel radius — is the untested emission-domain
  variant with instrument-level support.
* The lidar stack carries nine amplitude channels; H60 froze six. `ex_max` (max 2 m
  slope in excess of the 30 m regional slope) and `relief` (local relief) are
  independent scarp operators with pinned semantics (GEMSDOE24
  `data/external/lidar_scarp_features.json`). `coh100` is excluded (H64:
  anti-correlates, −0.532); `strike`/`ex_mean` are not max-amplitudes.

## The slate (ranked by expected DTI improvement × implementation cost)

### H65 — scarp-consensus field (rank 1: best expected holdout gain per unit cost)

* **Layers.** The six H60 lidar channels (`step_max`, `lappos_max`, `lapneg_max`,
  `upface_max`, `downface_max`, `cross_max`) + `valid` + TIGER road distance + BLM
  closed-claim distance.
* **Physical signature.** Per cell, the **count of channels whose amplitude exceeds
  its frozen instrument threshold** (t200 for lappos/lapneg/cross/upface/downface;
  t150 for step — the same thresholds the frozen instruments use), ranked
  lexicographically: consensus count descending, then the H60 channel-rank-max
  descending as the amplitude tie-break. A real, continuous fault scarp is
  simultaneously a topographic step, a crest convexity, a base concavity and a
  facing break — independent operators agree at the same cell. Road cuts, terrace
  risers, paleo-shorelines and single-channel artifacts fire on fewer operators.
* **Why it should catch a catalogue-missing fault.** Catalogue absence is a *mapping*
  gap, not a *geometric* one; geometric consensus is independent of mapping status.
  H60's per-cell max lets one noisy channel spend the budget on a non-tectonic step;
  consensus requires independent operators to agree.
* **How it differs from anything already implemented.** H60 = per-cell **max** of
  channel ranks (one operator suffices); H65 = amplitude-tie-broken **consensus
  count** (several must agree). No prior arm in GEMSDOE1–54 used channel consensus as
  an emission field.
* **Definition (frozen).** `consensus = Σ_c 1[channel_c > thr_c]` over the six
  channels; field = lexicographic rank of (consensus, channel-rank-max) over the H60
  emission domain, tie-free by construction. Cost: low (reuses H60 machinery).

### H67 — alteration-corroborated lidar field (rank 2: largest expected scientific gain; medium cost)

* **Layers.** The H60 lidar field + the **USGS GeoDAWN contractor Th/K ratio grid**
  (`external/geodawn_extensions_u8.tif`, band `ThK`; DOI 10.5066/P93LGLVQ; u8 rank
  quantisation 1st–99th percentile, 0 = nodata; hash-pinned with its metadata sidecar
  `external/geodawn_extensions.json`) + road/claim masks.
* **Physical signature.** **Structure + fossil heat.** Additive 50/50 rank mixture
  (the H62 mechanism, λ frozen at 0.5) of the H60 lidar field and the rank of Th/K
  over the emission domain. Hydrothermal alteration leaches potassium (argillic) or
  adds it (potassic); either way Th/K is the standard airborne-radiometric
  alteration index. A scarp coincident with an alteration high is a sealed fluid
  conduit — the hidden geothermal vent the competition rewards.
* **Why it should catch a catalogue-missing fault.** The catalogue maps *structure*;
  radiometrics map *fossil fluid flow*. Their intersection is the population with a
  geothermal reason to exist but no map entry — the "truly believe" target. The
  GeoDAWN surveys cover this footprint and were acquired for undiscovered geothermal
  resources (USGS GMEQ page).
* **How it differs from anything already implemented.** No prior arm in GEMSDOE1–54
  combined the lidar stack with radiometrics. H50's scan tried magnetic / gravity /
  curvature / ruggedness **multiplicatively** on the slope field (every product
  degraded it); an **additive rank mixture** of lidar + radiometrics has never been
  tried. Radiometrics are independent of the lidar instrument, so the
  independent-instrument corroboration stays honest.
* **Definition (frozen).** `field = rank_scale(0.5 · rank(h60) + 0.5 · rank(ThK))`
  over `domain = H60 domain AND ThK > 0`. Cost: medium (one new raster read + index).

### H66 — far-field lidar field (rank 3: instrument-supported, uncertain magnitude; low cost)

* **Layers.** The H60 field + the catalogue mask (`labels.tif`) through a Euclidean
  distance transform.
* **Physical signature.** The H60 scarp-amplitude ranking restricted to cells **more
  than 3 px (300 m, one metric-kernel radius) from every catalogue pixel** — the
  completely-unmapped-system pole. The organiser's "new fault" definition spans both
  poles ("newly mapped geometry of an existing fault system" and unmapped systems);
  H63 refuted the near pole (0.156660 / 0.162911), and H64 measured far peaks
  correlating better with the 13 scores (lappos +0.581 far vs +0.273 near).
* **Why it should catch a catalogue-missing fault.** The hidden labels are
  expert-mapped new faults; mapping effort has already been spent near the catalogue,
  so the strongest *unexplained* scarp population sits where the catalogue is silent.
* **How it differs from anything already implemented.** No prior arm gated or
  weighted emission by catalogue distance in the far direction; H63 gated near only
  and was refuted.
* **Definition (frozen).** `domain = H60 domain AND d_cat > 3.0 px`; field = the H60
  field values on that domain. Cost: low.

### H68 — extended-channel lidar field (rank 4: incremental; lowest cost)

* **Layers.** H60's six channels + `ex_max` (max 2 m slope in excess of the 30 m
  regional slope) + `relief` (local relief) — the two remaining max-aggregated
  amplitude channels of the 12-band stack with pinned semantics. `coh100` excluded
  (H64: anti-correlates −0.532); `strike`, `ex_mean` are not max-amplitudes.
* **Physical signature.** The same rank-max mechanism over **eight** channels:
  short-wavelength steepness excess and local relief are independent scarp operators
  not in H60's frozen six.
* **Why it should catch a catalogue-missing fault.** A scarp is a local relief
  anomaly and a short-wavelength steepness excess, not only a band-passed step.
* **How it differs from anything already implemented.** H60 froze six channels; H68
  extends the rank-max to the remaining documented amplitude channels. This is the
  most H60-like arm (a parameter extension) and is ranked last for novelty.
* **Definition (frozen).** `field = rank_scale(per-cell max of the ranks of the
  eight channels)` over the H60 emission domain. Cost: lowest.

## Frozen screen design (identical to sessions 4–5; nothing re-tuned)

* **Blocks.** The exact 41 blocks (8×8 contiguous, 3 px guard, seed 500610,
  20 selection / 21 calibration), re-derived and asserted byte-equal to
  `evidence/h50/blocks.json` before anything is scored.
* **Budget.** 37,654 unit dots (family standard; also the h33-2-b2 budget).
* **Spacings.** (2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.6) px — the frozen sweep.
* **Instruments.** Primary `lappos_t200_d3`; the frozen seven lidar-peak instruments
  plus the independent SGMC off-catalogue population — exactly `run_h60_screen.py`.
* **Arms.** `h65`, `h66`, `h67`, `h68` + anchors `h50`, `h60` (frozen definitions,
  reproduced) + mass-matched spaced random control + the owner-reported d2.8
  reference + H47-C1 raster controls.
* **Emission.** Greedy top-ranked spaced selection; the lidar-domain arms cap at
  domain capacity at small spacings (session-5 deviation IR-2026-10-07-D) and the
  actual mass is recorded in every row.
* **Conformal operating-point rule (this round's methodological change).** Per arm,
  on the primary instrument: selection matrix (20 blocks × 7 spacings), calibration
  matrix (21 × 7); `gems47.conformal.simultaneous_lower_bounds(selection,
  calibration, coverage=0.90)` (max-over-settings one-sided split conformal, Lei et
  al. JASA 2018 Algorithm 2 / Theorem 2.2); the operating point is
  `choose_operating_point` = **argmax of the certified lower bound** (ties: selection
  mean, then spacing) — the spacing with the greatest *guaranteed* floor, not the
  greatest observed mean. The reported confidence level is
  `finite_sample_coverage_at_least_if_exchangeable = k/(n+1)` with
  `k = ceil((n+1)·0.90) = 20`, `n = 21` → **≥ 90.909 %**. The guarantee is
  assumption-conditional on block-level exchangeability; it covers one future
  exchangeable block's proxy DTI, never the private leaderboard.
* **Promotion gate (frozen, six conditions).**
  1. `beats_h50_by_10pct` — pooled primary selection DTI ≥ 1.10 × the H50 anchor's
     0.165881.
  2. `positive_conformal_floor` — certified floor at the conformal-chosen spacing > 0.
  3. `sgmc_beats_random` — pooled SGMC selection DTI ≥ the random control's at the
     same spacing.
  4. `beats_random_3x_primary` — pooled primary selection DTI ≥ 3 × the random
     control's at the same spacing.
  5. `beats_incumbent_h60` — pooled primary selection DTI > H60's frozen 0.287891
     **AND** pooled SGMC selection DTI > H60's frozen 0.193813. Only an arm passing
     this condition replaces H60 as the primary (OK-to-submit) artifact. An arm
     passing 1–4 but not 5 is published as a **validated candidate**, clearly labelled
     "not the recommendation while H60 stands" — the slot is not spent on it.
  6. Build-time — bounded uniqueness (0 exact matches, max mask Jaccard < 0.5 against
     every prior raster reachable from this checkout) and 17/17 strict read-back
     format checks.
* **Winner rule.** Among arms passing 1–4: highest pooled SGMC selection DTI,
  tie-break the certified conformal floor (the session-5 rule, frozen).

## Provenance limits (do not drop)

* The restored rasters are hash-pinned owner mirrors, not organiser-authenticated
  bytes; the owner-reported public scores are not organiser receipts.
* The lidar stack is **owner-derived** from USGS 3DEP 1 m DEM tiles (706/716; work
  resolution 2 m; per-channel meanings pinned in GEMSDOE24
  `data/external/lidar_scarp_features.json`), NOT organiser-supplied. USGS 3DEP
  products carry no use restrictions.
* The GeoDAWN Th/K grid is a contractor product derived from the USGS GeoDAWN release
  (DOI 10.5066/P93LGLVQ); bytes are u8 ranks, not physical units; 0 = nodata. USGS
  data release; retain attribution.
* The primary lidar-peak instrument shares its terrain modality with every
  lidar-reading field (H60, H65, H66, H68); their primary-instrument numbers are
  optimistic by construction. H67's Th/K component is independent of it, and the SGMC
  off-catalogue population is independent of both.
* Spatial separation does not establish geological exchangeability; every conformal
  floor is conditional on that assumption.
* The screen spends no competition submission slot and reads no private label.
