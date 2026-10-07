# H49 research hypotheses — frozen before implementation

**Created:** 2026-10-07 UTC. Read the README standing brief and `docs/why-02778.md` first.
**Core values:** Maximize P(Win); Own the Outcome. No automated competition uploads.

## What this round must answer

The standing brief's highest-urgency deliverable is a **unique** competition GeoTIFF that is easy to
download, whose operating point is fixed by **split conformal prediction** on this repository's own
spacing/DTI sweep, with the **conformal confidence level reported next to the chosen spacing**. The
previous round's published artifact reports a nominal 90 % floor of 0.04477 while its own bundle
records `cleared_floor: false` and empirical selection-half violation rates of 0.167–0.308 against a
nominal 0.10 (`evidence/submission/bundle.json`). That inconsistency is treated here as an
irregularity to fix, not as a number to repeat.

Two prior results bound the search, both reproduced in this round from the restored bytes:

1. **The metric's algebra.** With `T = TP_w`, `S = Σp`, `M = Σp·max_g k`, `|G|` the hidden truth
   count, `DTI = T / (0.2·(T + S − M) + 0.8·|G|)` and `FN_w = |G| − TP_w` identically. When every
   emitted pixel is the unique best cover of its truth pixel (`M = T`) this collapses to
   **`DTI = T / (0.2·S + 0.8·|G|)`**, so at fixed truth a submission is improved only by raising
   credit `T` or lowering emitted mass `S`. A single added dot pays iff its realised kernel weight
   `w > 0.2·DTI`.
2. **Where the family's 0.2778 came from** (`docs/why-02778.md`): sparse emission and coherent
   lineament placement, with catalogue-flank mass deleted. Its measured precision at 40 k pixels is
   0.1253 against SGMC off-catalogue fault versus 0.5049 for `scarp(det_elev_slope, r=9)` — a 4×
   precision gap on the only independent real-fault population available here.

The two new hypotheses below both attack the **denominator**, not the numerator: they remove mass
that cannot earn credit, or they make each unit of mass cover a *different* truth pixel. Neither
claims to find a fault no public compilation contains; that claim would need the private labels.

## Ranked shortlist (ordinal research priorities, not DTI forecasts)

| Rank / ID | Layer(s) | Physical signature and transform | Why it could credit faults the catalogue misses | Difference from everything implemented | Expected effect / cost / feasibility |
|---|---|---|---|---|---|
| **1 · H49-A: orientation-aligned anisotropic thinning ("trace-following emission")** | Any field; here `det_elev_slope` (band 19) through the frozen `scarp` r = 9 recipe, plus the structure tensor `(theta, coherence)` that `scripts/build_surfaces.py` already computes. | The fault trace is a 1-D curve. Replace the isotropic Euclidean spacing rule (`nms_disk`, `poisson_disk`) with an **elliptical exclusion zone aligned to the local strike**: forbid neighbours within `b_across` perpendicular to the strike, allow them as close as `a_along` along it. | It does not localise anything new. It stops paying the 0.2-per-unit tax on second and third pixels sampled across the same ridge: at matched mass `S`, the budget that a disk spends on cross-strike duplicates is redirected along the trace, where each dot can be the best cover of a *different* hidden truth pixel. Under `DTI = T/(0.2S + 0.8\|G\|)` that is a strict gain whenever duplicates exist. | Every emitter, control and prior artifact in this repository and in the score history uses an isotropic exclusion (GEMSDOE10 `placement.dot_nms`, GEMSDOE32 `emission.dot_thin`, this repo's `nms_disk`/`poisson_disk`). `oriented_blur` reshapes the **field**; nothing reshapes the **sampling geometry**. | **Small, sign known from the algebra**; cost **low** (one vectorised function, structure tensor already cached). **Test first.** |
| **2 · H49-B: signed scarp-polarity coherence across two half-widths** | `det_elev` (band 12) and `det_elev_slope` (band 19). | Compute the **signed** across-strike step at half-widths 5 px (500 m) and 9 px (900 m) (`geomorph.signed_scarp_step`, already present as the unexecuted H47-E form). Keep a pixel only where the two scales agree in sign, then persist the signed response with a 1.5 km along-strike boxcar and take the magnitude. | Polarity is a physical invariant of a normal fault: the same side stays up along the trace. Stream banks, terrace edges, fan margins and lithologic contacts are symmetric or flip sign along their length, so an amplitude-only detector keeps them and a polarity test rejects them. Rejecting them raises precision, which is the binding term at the incumbent's mass. | This repo's `scarp`, `curv`, `openness`, ridge/LRM and `line` transforms are all **unsigned**; the H47-C1 odd/even template *fit* that failed its gate is a different operator (per-pixel profile fitting, not multi-scale sign agreement). | **Moderate, uncertain**; cost **medium** (one new transform). Confounder: displaced non-normal faults and antithetic scarps. |
| **3 · H49-E: depth-to-basement gradient ridge gated by co-directionality** | `depth_to_base_surf` (band 15), `iso_grav_anom_hg` (band 18), `det_elev_slope` (band 19). | Horizontal-gradient ridges of the basement-depth surface, retained only where their azimuth agrees with the local scarp-field strike within ±20°. | A fault buried under basin fill has no scarp; its basement offset can still appear as a depth-gradient ridge that no surface compilation contains. | This repository uses band 15 only as a smooth **regional veto** (`detector.regional_gate`) and records a metadata dispute about its meaning; no prior arm uses its directional gradient as a positive locator. | **Low–moderate**, high confounder risk (interpolation streaks); cost **medium**. **Conditional.** |
| **4 · H49-C: footwall/hanging-wall long-wavelength asymmetry** | `det_elev` (band 12) detrended; `iso_grav_anom` (band 13). | Paired means of the detrended elevation (and isostatic gravity) at ±1.5–3 km from a candidate trace — i.e. **beyond** the 300 m kernel and the 900 m scarp half-width — tested for a persistent one-sided contrast. | Half-graben geometry survives erosion of the scarp face, so a degraded or partly buried range-front fault still shows a one-sided basin. | No existing term compares *side means about a candidate lineament*; the regional gates multiply by a smooth prior and never test one-sidedness. | **Low–moderate**; cost **medium-high** (orientation-consistent side sampling). |
| **5 · H49-D: relay/stepover linkage-zone detector** | The scarp field itself, catalogue-free. | Find pairs of near-parallel, along-strike-overlapping ridge segments with a 1–4 km lateral step and no through-going trace; emit on the connecting ramp. | Map compilations carry the through-going trace and frequently omit the short linkage ramp — which is the classic extensional geothermal upflow site. | GEMSDOE45 grew fault **tips** along strike; this searches **pairs** and the gap between them. | **Moderate, high variance**; cost **high**. **Not attempted this round.** |

Ranking is by expected marginal DTI per unit of implementation cost under the algebra above:
H49-A (cheapest, sign of the effect is fixed by the metric), H49-B (orthogonal physical
discriminant), H49-E, H49-C, H49-D.

## Frozen validation and selection design (written before any code)

- **Grid and instruments unchanged** from the round-2 design so results stay comparable:
  `src/gems47s3/grid.py` `Grid`, `all_bands_finite()` support, catalogue masked exactly as the
  organiser masks it, five instruments `PM0200, PM0112, PM0294, A1, A2` defined in
  `scripts/run_sweep_a.py` with the prevalence bracket 0.112 %–0.294 % inverted from the
  organiser's own published scores (`evidence/inversion/live_anchor_inversion.json`).
- **Finer spatial blocking, therefore more exchangeable units:** 8×8 contiguous blocks
  (64 cells, minimum 5 000 px, minimum 30 truth px) instead of 6×6. More blocks is the only way to
  make `alpha = 0.10` a tail quantile rather than a second-order statistic.
- **Disjoint roles (this is the fix for the inconsistency above):**
  one seeded 50/50 split into a **selection half** and a **calibration half**.
  The operating point is chosen using **selection-half** scores only; the floor is then computed on
  the **calibration half**, which the choice never saw. The selection conditional guarantee is
  therefore a genuine split-conformal statement, not a maximum of dependent order statistics.
- **Ranking key (preregistered):** maximise the primary-instrument (`PM0200`) **mean selection-half
  DTI**, tie-broken by the worst normalised mean across the five instruments, then by larger
  minimum spacing. Ranking by the mean on a disjoint half is admissible precisely because the
  certification half is not used for the choice; this is the "calibration half certifies what the
  selection half chose" the brief asks for.
- **Certified quantities, all reported next to the chosen spacing:**
  1. single-split conformal floor at `alpha` and at `alpha/1` (no union bound is claimed, because at
     these block counts `ceil((n+1)(1-alpha/m)) > n` for any useful `m` — recorded as a limitation);
  2. the same floor at 90 %, 75 % and 80 % so a reviewer can pick the level;
  3. the **repeated-split distribution** of the floor over 400 independent 50/50 splits, with the
     empirical violation rate of the floor on the held-out half (an honest audit of the whole
     select-then-certify procedure, including the union-over-candidates effect);
  4. the DKW/Massart mean floor, labelled as a bound on a *mean over blocks*, not on a single block.
- **Controls, at matched emitted mass:** the isotropic `nms_disk` emitter on the same field, the
  frozen `R2_scarp9_topo` field, and a fixed-seed spaced random mask. A candidate that does not beat
  the isotropic control on the primary instrument's selection half does not get submitted.
- **Submission gate (unchanged from the standing brief):** positive certified floor, no failed
  format check on the written bytes, and a bounded uniqueness audit against every restored prior
  raster plus this repository's own published downloads. Failure is published as failure.

## Source and interpretation limits (unchanged and re-stated)

- The target is fault geometry, not a proven geothermal system; the organiser withholds test-data
  sources, types and coverage (DrivenData community thread 11527, 23 September 2026).
- Instruments A1/PM* draw truth from the given catalogue, so they measure **ordering**, not the
  organiser's level (`IR-47-PROXY-01/02`). Instrument B (SGMC off-catalogue, >300 m from the given
  catalogue) is the only independent real-fault population here and is optimistic about topographic
  detectors because SGMC also carries non-fault contacts.
- Spatial blocks are **not** exchangeable in a geological sense; Basin-and-Range and Walker Lane
  blocks differ. Every floor is reported with its leave-one-out worst case and with the empirical
  violation audit rather than as an unconditional distribution-free guarantee.
- No DrivenData credentials exist in this checkout; every input is a hash-pinned owner mirror
  (`registry/data_manifest.json`), not an organiser-authenticated byte stream.
