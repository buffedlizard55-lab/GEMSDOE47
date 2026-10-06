# Reusable knowledge and evidence boundaries — 2026-10-06

> This note separates official source facts from local/mirrored measurements and owner-reported claims. A catalog link is not proof of file acquisition or footprint overlap; an owner claim is not an organizer receipt.

## Competition and metric — official sources

- DrivenData [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) defines fault prediction and the distance-weighted Tversky index (DTI). The metric implementation in `src/gems47_metric.py` transcribes the published weighted TP/FP/FN formula and includes local component regression checks; it is not a private organizer scoring service.
- The official [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) requires login for data access. The H47-B files were obtained from a group-hosted mirror; hashes identify bytes but do not independently authenticate them as organizer downloads.
- The [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) is a participant-level moving display. The latest saved one-time observation is rank 1 at 0.3774 (name not retained), DARD 0.3195/#7, `extradr19` 0.2778/#13. It does not expose a TIFF filename/hash mapping. No automated monitoring is implemented.
- The official [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) is a public baseline, not an official best model or a per-file scoring receipt.

## DTI interpretation

The organizer's formula uses distance-weighted `TPw`, `FPw`, `FNw`, with `FNw = Ng − TPw` for bounded predictions. It can be written as:

```text
DTI = 5 × TPw / (TPw + FPw + 4 × Ng)
```

Further reduction to a presumed number of binary “dots” requires assumptions about pixel values and distance-weighted false-positive penalties. Do not infer hidden labels, file identities or expected scores from participant ranks or a monotone pruning curve.

## Geology and official external data

- [USGS GeoDAWN](https://doi.org/10.5066/P93LGLVQ) is an official airborne magnetic/radiometric release for the northwestern Great Basin. The official raw archive was not downloaded directly in this session. H47-B used a rank-encoded `TMI_up150` channel from a group mirror; it is not physical magnetic units, a vertical derivative, or a tilt-depth estimate.
- Faulds et al.'s [blind Southern Gabbs Valley geothermal system](https://pubs.usgs.gov/publication/70201803) supports the plausibility of concealed systems without obvious surface expression. It does not establish a magnetic-edge detector's skill.
- [Salem et al. (2007)](https://doi.org/10.1190/1.2821934) describes tilt-depth analysis. H47-B did not implement that method.
- Official feasibility sources for future work include [USGS QFFD](https://www.usgs.gov/programs/earthquake-hazards/faults), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [USGS ASTER alteration data](https://mrdata.usgs.gov/surficial-mineralogy/ofr-2013-1139/), [DOE INGENIOUS GDR 1391](https://gdr.openei.org/submissions/1391), [NASA Sentinel-1](https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/sentinel-1), and [USGS water services](https://waterservices.usgs.gov/). Their exact footprint coverage, local acquisition, and licensing have not all been measured; do not describe them as implemented or validated.

## H47-B screen result (local; mirror labels)

- Frozen protocol: [`docs/preregistered-h2.md`](../docs/preregistered-h2.md). Full result: [`docs/validation-h47b-20261006.md`](../docs/validation-h47b-20261006.md).
- Selected spacing 5 px/500 m; locked-test pooled DTI H47-B 0.027553, tuned single-scale baseline 0.025639, fixed-seed random 0.037159. H47-B lost to random.
- Six calibration blocks gave a mechanical nominal 6/7 calculation only under unverified exchangeability; the clipped lower floor was 0.0. Five of 16 blocks had no catalogue truth.
- **Decision: NOT PROMOTED; no slot.** A format-valid TIFF and low similarity to visible prior artifacts do not repair this result.
- Bounded uniqueness audit: zero exact positive-mask matches among 334 accessible exact-grid TIFFs from 55 visible sibling repositories; maximum equal-mass Jaccard 0.01119. Not a global proof.

## Retired and unverified items

- The old `0.34912` modeled score and `0.34837` “75% conformal floor” are withdrawn. The old calibration rungs were selected points from one monotone family; score-to-file links were not organizer-authenticated; the target was extrapolated.
- The historical `gems47-dcat20-annulus-flankprune` TIFF is a delete-only subset of a published artifact and is not a new detector.
- The alleged H33-2-B2 → 0.2778 pairing is unverified; the GEMSDOE32 page marks that candidate unscored.
- The prior checked-in board value 0.3345 at rank 1 is superseded by the later saved 0.3774 observation; the top participant name was not retained.

For complete references and access boundaries, see [`docs/sources.md`](../docs/sources.md). For open issues, see [`docs/irregularities.md`](../docs/irregularities.md).
