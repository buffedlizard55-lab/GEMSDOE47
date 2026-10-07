# H49 round — blocked-sweep results, review findings, and limits

*Generated 2026-10-07 13:07 UTC by `scripts/report_h49.py` from the evidence files. Every figure below is read out of a committed JSON receipt; nothing here is typed by hand.*

## The two instruments

- **Instrument A** (`evidence/sweep/sweep_h49.json`): 39 usable 8×8 spatial blocks, 15,555 scored rows, five prevalence-matched instruments built from the *given* catalogue (PM0200, PM0112, PM0294, A1, A2). Truth = whole catalogue components held out of the visible catalogue. It measures *ordering against mapped faults* and is optimistic for any topographic field.
- **Instrument B** (`evidence/sweep/sweep_h49b.json`): 39 usable 8×8 blocks, 4,719 scored rows, truth = USGS SGMC traces more than 3 px (300 m) from the given catalogue, whole components, prevalence-matched to `p0200`. The given catalogue is masked in full, consistent with the public scoring clarification, but SGMC includes lithologic contacts and other non-fault traces. Treat Instrument B as a public proxy, not the organizer's hidden target population.

Both sweeps use one seeded 50/50 split: 20 selection blocks and 19 calibration blocks (with instrument-specific usable-block counts). The halves are disjoint for a fixed arm. However, the workflow later chose between the floor and mean rules after reviewing the full sweep/re-split results, so the calibration half is not an auditable untouched holdout for the final adaptive rule.

## Selected operating point — research-only; slot gate closed

The artifact remains downloadable for review, but **do not spend a submission slot**. The published selection procedure is not prospectively auditable from the repository, and the paired 90 % conformal lower bound on improvement over the incumbent is negative.

`R7_scarp9_polarity` · `disk` · spacing **2.8 px (280 m)** · density **7.37 per 1,000 scored px** · catalogue-flank buffer **3 px (300 m)**

- shipped rule: maximise the selection-half mean DTI on Instrument B (amendment; see the module docstring)
- saved floor-rule arm (`docs/research/h49b-instrument-b-preregistration.md`) selected `R2_scarp9_topo` / `oriented4` / `s3.6_d14_b2`; its nominal fixed-arm Instrument-B floor is 0.05519. The addendum says it was written before the sweep, but Git history cannot independently verify that: the addendum, sweep evidence and certificate first appear together in commit `409c407` (2026-10-07 03:35 UTC); the sweep file records generation at 03:17 UTC. This is not proof the draft was late, only that prospective timing is not auditable from this repository.
- amendment: The mean-rule stability summary comes from 400 Monte Carlo re-partitions of the same 39 spatial blocks; observations are reused, so these are not 400 independent validation samples. The floor-rule ranking is sensitive to the few lower-tail order statistics among about 20 selection blocks. This documents why the rule was amended, not prospective evidence: the calibration results were already visible in the full analysis, so neither fixed-arm certificate proves validity for the adaptive workflow.

## Nominal split-conformal diagnostic — assumptions and scope

For a rule fixed independently of calibration outcomes, the Instrument-B order statistic is 0.03184 at nominal 90 % (α = 0.1, n = 19 calibration blocks, order statistic k = 18). This is conditional on exchangeable spatial blocks and a fixed rule. Since the mean-rule change was made after the sweep, and the same 39 blocks informed that change, do **not** interpret this as a prospective guarantee for the complete adaptive procedure, for a geographic subregion, or for the organizer's private labels.

| quantity | Instrument B (SGMC off-catalogue, primary) | Instrument A (PM0200, corroborating) |
|---|---:|---:|
| nominal fixed-arm floor (α = 0.1) | **0.03184** | 0.01828 |
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

**Repeated-partition stability diagnostic** (400 Monte Carlo re-partitions of the same 39 blocks; block observations are reused, so these are not independent validation samples): floor p05 0.01793, median 0.03847, mean 0.04391; mean violation rate on the other half 0.0807 vs nominal α = 0.1. This summarizes sensitivity/stability only; it does not create new holdout evidence or restore prospective validity to the rule amendment.

Across those reused-block re-partitions, the mean rule selects: `R7_scarp9_polarity/disk/s2.8_d7.37_b3` 221× (55 %), `R7_scarp9_polarity/disk/s2.8_d14_b3` 84× (21 %), `R2_scarp9_topo/oriented4/s2.8_d14_b3` 52× (13 %), `R2_scarp9_topo/disk/s2.8_d14_b3` 32× (8 %). The saved floor rule selects R2_scarp9_topo/disk/s2.8_d14_b3 129×, R7_scarp9_polarity/disk/s2.8_d14_b3 127×, R2_scarp9_topo/oriented4/s3.6_d14_b3 105×. These frequencies are conditional on this same set of 39 blocks and are not evidence from new geology.

### Paired differences versus the incumbent

Positive means the candidate beats the H33 reference mask on that same block. The Student-t lower bound is assumption-dependent; the split-conformal lower bound is an order statistic for a fresh exchangeable block, conditional on a fixed arm. Both candidate arms have a negative conformal lower bound, so a positive per-block improvement is not established at 90 %, even though the sample mean is positive.

| arm | half | n | mean ΔDTI | candidate / incumbent wins | paired-mean one-sided 90% t LCB | paired-difference 90% conformal lower bound | sign-test p (greater) |
|---|---|---:|---:|---:|---:|---:|---:|
| shipped arm | selection | 20 | +0.03221 | 13 / 7 | +0.01671 | -0.03342 | 0.1316 |
| shipped arm | calibration | 19 | +0.03890 | 15 / 4 | +0.02138 | -0.01050 | 0.0096 |
| rule described as preregistered | selection | 20 | +0.01896 | 12 / 8 | +0.00379 | -0.05947 | 0.2517 |
| rule described as preregistered | calibration | 19 | +0.02657 | 14 / 5 | +0.00862 | -0.02479 | 0.0318 |

## Descriptive screen checks — not slot authorization

| gate | value | pass |
|---|---|---|
| positive nominal fixed-arm Instrument-B floor | 0.03184 | **True** |
| credible at α (k ≤ n) | k = 18, n = 19 | **True** |
| beats the fixed-seed random control on the B selection mean | 0.10329 vs 0.05750 | **True** |
| descriptive B selection-half mean vs the 0.2778-labelled H33 reference | 0.10329 vs 0.07108 | **True** (post-selection comparison) |
| shipped arm is the isotropic emitter itself | True | — |
| independently auditable preregistration + positive 90% paired-improvement floor | not satisfied | **False — do not spend a slot** |

## The written artifact

- `gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif` — 17 local/archive raster comparisons, maximum positive-mask Jaccard 0.292575 (`docs/downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif`), maximum containment 0.452701, local exact-match flag `is_unique = True`. This bounded local check is not a global uniqueness proof.
- Pinned public inventory: 54 commit-pinned public repositories; 555 comparable inventory blobs plus 10 local-history rasters (565 comparisons total); 0 exact mask/value matches; maximum Jaccard 0.292575 (GEMSDOE47/docs/downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif); 3 entries excluded from direct comparison (2 not single band exact grid, 1 not single tiff zip); 0 repository inventories failed. The inventory is scoped to visible public owner repositories, not global; `global_unique_proven = False`. Full machine-readable receipt: `evidence/h49/pinned-public-inventory-uniqueness.json`. Website copy: `docs/data/pinned-public-inventory-uniqueness.json`.
- 37,612 unit dots = 7.370 per 1,000 scored px = 0.7279 % of the footprint; engine `nms_disk (field-ordered isotropic NMS)`
- exact published TIFF: 409,124 bytes, SHA-256 `f2cec409ce3bec5a2805f1fab9a12ab7f72394f8be79cc365134ce43708c6060`; one float32 band, 3292 × 3730, EPSG:32611, no nodata tag; internal mask matches the 5,167,373-cell official footprint and masked reads are null outside.
- format/read-back: 19/19 gating checks pass (`all_checks_passed = True`); informational whole-grid range flag is True; raw full-grid cells are finite in [0,1], with 37,612 positives. Binary values True; portal note 168/200 chars.
- The largest local overlap is 0.2926 Jaccard and 0.4527 containment. It is a different mask, but still shares the same broad persistence/density detector lineage; the polarity-scored field and larger catalogue buffer are incremental changes, not an independent detector family. See the pinned public-inventory audit for a bounded exact-grid check.

## The density question this round actually settled

Within these particular public proxies, the mapped-fault instrument tends to reward more emitted mass while the SGMC proxy has an interior peak. This is a descriptive sweep result, not evidence that the SGMC peak matches the organizer's hidden target or that the selected point is optimal on the leaderboard.

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

## Paired block comparisons (descriptive results; no private-label score)

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

The strike-aligned emitter does not show a robust gain over the disk emitter on these blocks. The candidate polarity field has a higher selection-half mean than the alternative field in this sweep, but its paired lower bound does not establish a fresh-block improvement; moreover, Instrument B is a mixed geological-contact proxy. These results do not establish that the polarity feature detects uncatalogued faults. The published mask uses the disk emitter with the R7 polarity-scored field, but its mean-rule choice was made after seeing the full analysis and remains research-only.

## What this round does *not* claim

- No organizer/leaderboard score is authenticated for this TIFF. The only score-like values here are block-level DTI measurements on public proxies.
- Instrument B is SGMC-derived; lithologic contacts and other non-fault traces may act as false positives. It is not the private target map.
- Spatial-block exchangeability is an assumption, not established fact. The 400 re-splits reuse the same 39 blocks and are sensitivity diagnostics only.
- Git history cannot establish that the B rule was fixed before sweep results; the shipped mean rule is a post-results amendment. No full-procedure or unconditional conformal guarantee is claimed.
- A positive sample mean/t lower bound is not a positive 90% conformal lower bound on paired improvement for a new block. Neither candidate arm passed that promotion criterion.
- The H49-A strike-aligned emitter and H49-B polarity transform are descriptive hypotheses, not validated geological discoveries. See `docs/RESEARCH_HYPOTHESES.md`.
