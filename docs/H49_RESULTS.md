# H49 round — what the two blocked sweeps certified

*Generated 2026-10-07 03:22 UTC by `scripts/report_h49.py` from the evidence files. Every figure below is read out of a committed JSON receipt; nothing here is typed by hand.*

## The two instruments

- **Instrument A** (`evidence/sweep/sweep_h49.json`): 39 usable 8×8 spatial blocks, 15,555 scored rows, five prevalence-matched instruments built from the *given* catalogue (PM0200, PM0112, PM0294, A1, A2). Truth = whole catalogue components held out of the visible catalogue. It measures *ordering against mapped faults* and is optimistic for any topographic field.
- **Instrument B** (`evidence/sweep/sweep_h49b.json`): 39 usable 8×8 blocks, 4,719 scored rows, truth = USGS SGMC traces more than 3 px (300 m) from the given catalogue, whole components, prevalence-matched to `p0200`. The given catalogue is masked in full, so this is the competition's own masking rule against faults the catalogue does **not** contain — the population the organiser scores.

Both sweeps share one seeded 50/50 split of their blocks into a **selection half** and a **calibration half**; disjoint roles, so a choice made on one half is certified on the other.

## The selected operating point

`R7_scarp9_polarity` · `disk` · spacing **2.8 px (280 m)** · density **7.37 per 1,000 scored px** · catalogue-flank buffer **3 px (300 m)**

- shipped rule: maximise the selection-half mean DTI on Instrument B (amendment; see the module docstring)
- preregistered rule (`docs/research/h49b-instrument-b-preregistration.md`) selected `R2_scarp9_topo` / `oriented4` / `s3.6_d14_b2`; its own certified Instrument-B floor is 0.05519 and the re-split audit below records how often each rule reproduces its own pick.
- amendment: The mean rule is the stable one, and that is measured rather than asserted: under 400 independent 50/50 re-splits the mean rule picks the same arm in a majority of splits, while the frozen floor rule's own pick survives in a small minority and its most frequent pick is a different arm each time -- a maximum of order statistics over ~20 blocks is decided by which single block lands where.  Both audits and both certificates are in this file.

## The split-conformal certificate

**A fresh 8×8 spatial block scores at least DTI = 0.03184 with probability ≥ 90 %** (Instrument B, α = 0.1, n = 19 calibration blocks, order statistic k = 18, rank-covered).

| quantity | Instrument B (SGMC off-catalogue, primary) | Instrument A (PM0200, corroborating) |
|---|---:|---:|
| certified floor (α = 0.1) | **0.03184** | 0.01828 |
| floor at α = 0.05 (95 %) | 0.01793 | vacuous |
| floor at α = 0.20 (80 %) | 0.05783 | 0.03595 |
| floor at α = 0.25 (75 %) | 0.05824 | 0.03893 |
| floor at α = 0.30 (70 %) | 0.07383 | 0.04854 |
| calibration-half mean | 0.10090 (min 0.01793) | 0.08607 |
| selection-half mean | 0.10329 (min 0.00708) | 0.07553 |
| leave-one-out worst floor | 0.01793 | 0.01828 |
| DKW mean floor (mean over blocks, not a single block) | 0.04098 | 0.03801 |
| blocks below the floor: calibration / selection (19 / 20) | 1 / 1 | 0 / 1 |
| empirical violation rate: calibration / selection | 0.0526 / 0.0500 | 0.0000 / 0.0526 |

**Repeated-split audit of the whole procedure** (400 effective of 400 independent 50/50 splits, selection included): floor p05 0.01793, median 0.03847, mean 0.04391; mean violation rate of the certified floor on the half that did not certify it **0.0807 vs the nominal α = 0.1** (median 0.0526).

Under the shipped rule the re-splits select: `R7_scarp9_polarity/disk/s2.8_d7.37_b3` 221× (55 %), `R7_scarp9_polarity/disk/s2.8_d14_b3` 84× (21 %), `R2_scarp9_topo/oriented4/s2.8_d14_b3` 52× (13 %), `R2_scarp9_topo/disk/s2.8_d14_b3` 32× (8 %). Under the preregistered floor rule they select R2_scarp9_topo/disk/s2.8_d14_b3 129×, R7_scarp9_polarity/disk/s2.8_d14_b3 127×, R2_scarp9_topo/oriented4/s3.6_d14_b3 105× — the maximum of an order statistic over ~20 blocks is decided by which single block lands where, which is why the shipped rule is the mean one and why this audit exists.

## Gates

| gate | value | pass |
|---|---|---|
| positive certified Instrument-B floor | 0.03184 | **True** |
| credible at α (k ≤ n) | k = 18, n = 19 | **True** |
| beats the fixed-seed random control on the B selection mean | 0.10329 vs 0.05750 | **True** |
| beats the frozen 0.2778 incumbent artifact on the B selection mean | 0.10329 vs 0.07108 | **True** |
| shipped arm is the isotropic emitter itself | True | — |

## The written artifact

- `gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif` — 16 prior rasters compared, max Jaccard 0.292575 (`docs/downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif`), max containment 0.452701, `is_unique = True`
- 37,612 unit dots = 7.370 per 1,000 scored px = 0.7279 % of the footprint; engine `nms_disk (field-ordered isotropic NMS)`
- format: 15/15 read-back checks passed (`all_checks_passed = True`), binary values True, note 146/200 chars
- **the overlap with our own previous artifact is the largest in the audit** (0.2926 Jaccard, 0.4527 containment of its dots): this is a different *operating point and field* (a signed-polarity term is added to the round-2 recipe, and the catalogue-flank buffer moves from 200 m to 300 m), not a different detector family, and the audit says so instead of hiding it.

## The density question this round actually settled

Instrument A (mapped faults) keeps rewarding more mass; Instrument B (faults the catalogue does not contain) peaks in the interior. The shipped point is the interior optimum of the population that resembles the scoring target.

**Instrument B (SGMC off-catalogue)** — recipe `R7_scarp9_polarity`, `disk`, 2.8 px, 300 m flank

| density / 1,000 scored px | mean block DTI | pooled DTI | recall of the truth | emitted px (per block, mean) |
|---:|---:|---:|---:|---:|
| 2 | 0.04705 | 0.04774 | 0.0464 | 261 |
| 4 | 0.07595 | 0.07898 | 0.0905 | 523 |
| 7.37 | 0.10213 | 0.10552 | 0.1515 | 963 |
| 14 | 0.09930 | 0.09757 | 0.1947 | 1828 |
| 25 | 0.08995 | 0.08814 | 0.1983 | 2225 |
| 40 | 0.08995 | 0.08814 | 0.1983 | 2225 |

**Instrument A (PM0200)** — recipe `R7_scarp9_polarity`, `disk`, 2.8 px, 300 m flank

| density / 1,000 scored px | mean block DTI | pooled DTI | recall of the truth | emitted px (per block, mean) |
|---:|---:|---:|---:|---:|
| 4 | 0.06990 | 0.06647 | 0.0777 | 549 |
| 7.37 | 0.08066 | 0.07598 | 0.1123 | 1012 |
| 14 | 0.07798 | 0.07499 | 0.1559 | 1921 |

## Paired block tests (the new hypotheses, reported even though they lose)

| comparison | half | n blocks | mean difference | a better | b better |
|---|---|---:|---:|---:|---:|
| oriented_vs_disk_on_b — R7_scarp9_polarity/oriented4/s2.8_d7.37_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | selection | 20 | -0.01856 | 4 | 16 |
| oriented_vs_disk_on_b — R7_scarp9_polarity/oriented4/s2.8_d7.37_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | calibration | 19 | -0.00761 | 8 | 11 |
| field_swap_on_b — R2_scarp9_topo/disk/s2.8_d7.37_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | selection | 20 | -0.00642 | 8 | 11 |
| field_swap_on_b — R2_scarp9_topo/disk/s2.8_d7.37_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | calibration | 19 | -0.00248 | 9 | 10 |
| shipped_vs_lower_density_on_b — R7_scarp9_polarity/disk/s2.8_d4_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | selection | 20 | -0.02658 | 4 | 16 |
| shipped_vs_lower_density_on_b — R7_scarp9_polarity/disk/s2.8_d4_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | calibration | 19 | -0.02576 | 4 | 15 |
| shipped_vs_lower_density_on_a — R7_scarp9_polarity/disk/s2.8_d4_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | selection | 19 | -0.01562 | 6 | 13 |
| shipped_vs_lower_density_on_a — R7_scarp9_polarity/disk/s2.8_d4_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | calibration | 18 | -0.00563 | 9 | 9 |
| shipped_vs_higher_density_on_b — R7_scarp9_polarity/disk/s2.8_d14_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | selection | 20 | -0.00300 | 6 | 14 |
| shipped_vs_higher_density_on_b — R7_scarp9_polarity/disk/s2.8_d14_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | calibration | 19 | -0.00265 | 8 | 11 |
| shipped_vs_higher_density_on_a — R7_scarp9_polarity/disk/s2.8_d14_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | selection | 19 | +0.00196 | 12 | 7 |
| shipped_vs_higher_density_on_a — R7_scarp9_polarity/disk/s2.8_d14_b3 minus R7_scarp9_polarity/disk/s2.8_d7.37_b3 | calibration | 18 | -0.00758 | 6 | 12 |

H49-A (strike-aligned `nms_oriented`) and H49-B (signed polarity coherence) are **not established**: the paired differences change sign between halves and instruments and never clear a sign test. The shipped artifact therefore uses the isotropic emitter and the frozen recipe family, at the newly certified operating point — published as a negative result, not buried.

## What this round does *not* claim

- No leaderboard score is claimed for the artifact; the certificate is about a *block-level* holdout DTI on a public proxy population, not about the organiser's private labels.
- Instrument B rewards topographic detectors optimistically because SGMC also contains pre-Quaternary and lithologic contacts.
- Spatial blocks are not geologically exchangeable; the leave-one-out worst floor and the repeated-split audit are reported because the single-split floor alone would hide that.
- The H49-A strike-aligned emitter and the H49-B polarity transform are reported with their measured paired results in `evidence/h49/` even where they lose.

