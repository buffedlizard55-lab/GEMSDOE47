# H50 hypothesis draft and protocol audit — 7 October 2026

**Status: exploratory, not a successful preregistered promotion.** The initial draft was written
before the H50 run, but no immutable pre-run commit was made. It reused the 39 H49 blocks
and split seed, so these cannot be called fresh holdout evidence. This corrected document
retains the intended hypotheses and actual implementation, rather than claiming an untouched test.

## Ranked hypothesis slate

Expected improvements are ordinal research judgments, not numerical forecasts. All implemented
inputs were recovered autonomously from hash-pinned owner mirrors; this verifies bytes, not
official portal provenance. The source registry and metadata audit remain authoritative.

| Rank | Hypothesis / layers | Physical rationale and missing-fault possibility | Prior overlap / cost |
|---|---|---|---|
| 1 | Reservoir-temperature corridor modulation: GDR mirrored geothermometer columns + band 19 `det_elev_slope` | Warm subsurface-water indicators may identify permeable corridors beneath cover; multiply an existing scarp field by a broad temperature prior. Neither temperature nor a scarp proves a new fault. | Related to existing H47-QC chemistry and H47-GSA warm-spring priors; continuous corridor weighting differs from point-only QC. Low cost; implemented. |
| 2 | Radiometric contrast: GeoDAWN mirrored K/Th uint8 channels + scarp field | Changes in radiometric composition might mark alteration or lithologic boundaries; a structural cue could help distinguish fault-related changes. | Related to H1 and GEMSDOE46 radiometric work; not a newly discovered family. Low/medium cost; implemented only as a contrast ablation. |
| 3 | En-echelon relay-gap connectors: slope/scarp ridges | Short connecting structures between offset segments could be omitted in a catalogue. | Already queued as H49-D; not new. High cost; not implemented. |
| 4 | Fine seismicity-density residual: `deq_n100a15`, `ieq_n100a15` | A local residual could suggest an unmapped active structure, but smoothed source fields may have no local information. | Regional seismicity context already exists; only the proposed residual differs. Low cost; not implemented, semantics/resolution unverified. |
| 5 | Conductive edge + gravity edge: `cond_surf` band 17, gravity horizontal gradient band 18 | A buried boundary could affect both conductivity and density; fluids and lithology are confounders. | Overlaps GEMSDOE32 clay-cap hypotheses. Medium cost; not implemented. |

**Requirement gap:** this is not five demonstrably novel hypotheses. Three overlap earlier queues,
and two are refinements. No claim of suite-wide novelty or established physical discoveries is made.
No unavailable external product is described as viable. Raw 1 m DEM data remain unacquired here.

## What the implementation actually does

- H50a: per-cell maximum of temperature weights across CSV rows; use median of available plausible
  geothermometer estimates (0–300 C), otherwise measured temperature; weight `(T-30)/170` clipped
  to [0,1]. Smooth at sigma 40 pixels (4 km), rank, multiply R7 by `.35 + .65*rank` and rerank.
  Repeated stations are NOT independent observations. Sampling density and maximum aggregation
  can bias this prior. The label-derived `dist_known_fault_px` column is not used.
- H50b: `log1p(K_uint8)-log1p(Th_uint8)`, sigma 2 smoothing, unsigned scarp transform at radius 5,
  rank, add weight 1.5 to R7's geometric mean. **Not a calibrated physical K/Th ratio**, and
  **no orientation-concordance test was implemented**. The earlier description overclaimed both.
- H50c combines both. Controls: R2, R7, fixed-seed random. Five spacings 1.5/2.8/3.6/4.6/5.8,
  buffers 2/3, sharp and sigma-1.85 blurred fields. Density cap 7.37 per 1,000 scored cells.
- Public SGMC components >300 m from known catalogue, p0200 subsampling, 8×8 grid, 39 retained
  blocks. The existing helper drops empty/low-truth blocks and clips components to block regions.
  These are selected proxy blocks, not all future geography or independently sampled private faults.
- Original selection: maximise selection-half mean (20 blocks); inspect calibration (19 blocks).
  Chosen H50a/disk/1.5/b3. Mean .107874/.101015, nominal-90% lower statistic **0**.
  R7 same-domain selection reference .103312. The coded 3×random and positive-floor gates fail.
- The later draft filtered candidates by their calibration floors and selected R7/2.8/b3 after
  seeing results. This is calibration-dependent selection, not the original rule. Its .03184
  claimed certificate is **withdrawn**. No confidence guarantee transfers to a different emitter.
- Export now uses newly computed H50a inference, not a prior submission raster. Global allocation
  differs from block quotas and is not covered by the block diagnostic. Research-only, no upload.

## Sources and verification limits

- [Official metric/format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official reference code](https://github.com/drivendataorg/gems-prize-reference-solution)
- [GDR 1391 compilation](https://gdr.openei.org/submissions/1391)
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [Lei et al. author manuscript](https://www.stat.berkeley.edu/~ryantibs/papers/conformal.pdf)

These are manual-review source links. Government/DrivenData payloads were not freshly downloaded
from those hosts in this restricted sandbox. Existing official-source receipts are dated records.
Generic citations in the first draft did not verify its specific alteration or geothermal
mechanism claims; those claims are now hypotheses, not facts attributed to unread papers.
