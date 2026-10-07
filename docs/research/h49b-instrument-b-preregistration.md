# H49 addendum — preregistration of the Instrument-B (SGMC off-catalogue) emission sweep

**Created:** 2026-10-07 UTC, **written before the sweep was run.** This addendum does not modify
`docs/research/h49-hypotheses-preregistered.md`; it records the original plan, the first H49 output, and the then-frozen rule.

> **Post-run correction notice (2026-10-07):** Instrument B is a public USGS SGMC proxy, not the organizer's hidden target or a population established to resemble it. The local mirror is owner-supplied, not organizer-authenticated. The later operating rule was amended after the repeated-split results were inspected; those re-splits reuse the same blocks and do not independently validate the amended rule. Any nominal 90% conformal calculation is conditional on unverified exchangeability and does not provide private/global coverage. The comparator labelled 0.2778 is only an **owner-reported d2.8 reference** with unverified score/file mapping. The written H49 TIFF fails the published null-or-NaN-outside requirement. See [corrected H49 report](../H49_RESULTS.md) and [format audit](../data/h49-format-contract-audit.json). **No slot is authorized.**

## What the first H49 run showed (evidence, not hypothesis)

`evidence/sweep/sweep_h49.json` — 39 usable 8×8 spatial blocks, 15,555 scored rows, 983 s; five
prevalence-matched catalogue instruments (PM0200 / PM0112 / PM0294 / A1 / A2).

1. The frozen ranking key (PM0200 selection-half mean DTI) selected
   `R2_scarp9_topo / oriented4 (H49-A) / s2.8_d14_b3` with a 90 % calibration-half floor of
   **0.01489** on PM0200 (n = 18 blocks, k = 18) and +0.377 % over the isotropic control at the
   same operating point (`evidence/h49/conformal_selection.json`). H49-A therefore "wins" the
   preregistered key by a margin far inside noise; H49-B (`R7_scarp9_polarity`) does **not** win.
2. **The winning density is at the boundary of the swept grid.** Pooled over blocks, PM0200 recall
   of the held-out catalogue truth rises 0.072 (4.0/1000) → 0.106 (7.37/1000) → 0.155 (14.0/1000)
   and is still climbing; the fixed-seed random control rises the same way (0.0297 → 0.0449 →
   0.0559). No swept density is interior, so "14.0 per 1000" is a grid artefact, not an optimum.
3. The marginal rule from the metric's algebra fixes when a dot pays:
   `dDTI > 0  ⟺  w > 0.2·DTI`, i.e. the bar is ~0.016 at DTI 0.08 on Instrument A. Instrument A
   measures ordering against *mapped* faults, which a topographic detector sees well; its marginal
   credit stays far above the bar, so it can only ever push density up. Instrument A is documented
   (`src/gems47s3/holdout.py`, IR-47-PROXY-01/02) as optimistic for the *field* and structurally
   wrong for the *emission-density* question, because the organiser's truth is by construction
   absent from the given catalogue.

## The open question this addendum answers

**What emission density maximises DTI against faults that are NOT in the given catalogue?**
Instrument B (SGMC traces > 300 m from the catalogue: 61,664 px in 2,077 components) is the only
independent real-fault population available in this checkout, and the repository already designates
it for *selection*: its truth is not drawn from the catalogue, the full catalogue is used as the
organiser's mask, and the emission domain is therefore exactly the competition domain.

## Frozen design (before running)

- **Folds:** `holdout.build_offcatalogue_folds` with the same 8×8 spatial blocking as the first
  sweep, `prevalence="p0200"` (0.200 % — the midpoint of the model-free |G| bracket), seed 20261007.
  Whole components only, so no part of a scored trace is left visible.
- **Field:** the frozen round-2 recipes, unchanged: `R2_scarp9_topo` (control) and
  `R7_scarp9_polarity` (H49-B). No new transform is introduced in this round.
- **Emitters:** `nms_disk` (isotropic control) and `nms_oriented` with across-strike radius 4.0 px
  (H49-A). Identical emitted mass for both at every operating point (the budget cap does that).
- **Grid:** spacing {2.8, 3.6} px × density {2.0, 4.0, 7.37, 14.0, 25.0, 40.0} per 1,000 scored px ×
  catalogue flank buffer {2.0, 3.0} px, plus a fixed-seed spaced random control at every point.
  The density range is extended upward by design, because the first run's optimum sat on the upper
  boundary; if the optimum is still on the boundary after this run, that is the reported finding and
  the grid is extended once more, never re-tuned per instrument.
- **Split:** one seeded 50/50 permutation of the usable blocks into a **selection half** and a
  **calibration half**. Roles are disjoint: the arm is chosen on the selection half only and the
  certified floor is computed on the calibration half only.
- **Selection rule (frozen):** maximise the **90 % conformal floor computed inside the selection
  half** on Instrument B; ties broken by (i) the selection-half mean DTI on Instrument B, (ii) the
  selection-half 90 % floor on Instrument A, (iii) the *lower* density, (iv) the larger spacing,
  (v) the isotropic emitter before the oriented one. Mass discipline before ornament.
- **Certified quantities (reported next to the chosen spacing):** the 90 % single-split floor on the
  Instrument-B calibration half (primary claim), the same floor at α = 0.05 / 0.20 / 0.25 / 0.30,
  the leave-one-out worst floor, the DKW mean floor, the empirical violation rate on the
  *calibration* half and on the *selection* half, and the repeated-split (400 ×) distribution of the
  floor with the empirical violation rate of the whole select-then-certify procedure. The Instrument-A
  floor is certified on the same split and reported beside it, labelled as the optimistic instrument.
- **Gates (unchanged):** positive certified Instrument-B floor; chosen arm beats the isotropic
  control at the same operating point on the Instrument-B selection half; beats the frozen incumbent
  (`data/reference/h33-2-b2-zeros.tif`) and the random control on both instruments; format read-back
  passes; uniqueness audit vs every prior raster in the repository. Failure is published as failure.
- **Honest limits, restated:** SGMC also contains pre-Quaternary and lithologic contacts, so
  Instrument B is optimistic about topographic detectors; blocks are not geologically exchangeable;
  no DrivenData credentials exist here, so every input is a hash-pinned mirror.
