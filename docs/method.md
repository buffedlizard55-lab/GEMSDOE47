# Method notes and status

## H47-B — tested public-catalogue screen (NOT PROMOTED)

H47-B is a cross-scale magnetic-edge persistence screen implemented in `gemsdoe47/magnetic.py` and `scripts/run_h2_experiment.py`. It uses a quantized, rank-encoded `TMI_up150` channel from a group-hosted GeoDAWN mirror, not raw physical-unit magnetic grids. The feature score is an uncalibrated screening transform, not a fault probability, physical tilt-angle/depth estimate, or organizer-approved prediction.

The exact scales, mask-support thresholds, score normalization, fixed 18,524-pixel emission mass, spacing sweep, block assignment, guard, controls, conformal calculation and promotion rule were frozen in [`preregistered-h2.md`](preregistered-h2.md) before scoring. The experiment selected 5 px/500 m. On five locked blocks, pooled DTI was 0.027553 for H47-B, 0.025639 for the tuned single-scale baseline, and 0.037159 for a fixed-seed random control. The assumption-conditional conformal lower floor clipped to 0.0. Five of 16 blocks had no catalogue truth. The candidate therefore failed the metric screen; do not submit it. Because all H47-B labels/features were read from a group-hosted public mirror, this screen is permanently research-only: its runner always sets `slot_eligible` to false and has no non-research publication path.

Full block details, output metadata, hash and bounded artifact comparison are in [`validation-h47b-20261006.md`](validation-h47b-20261006.md). The TIFF in `docs/downloads/` is named `research-not-submittable` and is published only for transparent review.

## Older screens and historical TIFF

- H47-A (`gemsdoe47/candidate.py`, `scripts/build_h47a.py`) implements a cross-acquisition edge-agreement screen, but no valid geological holdout result supports it.
- H1 (`scripts/build_h1_candidate.py`) is a radiometric-ratio/LoG halo screen. The first public-catalogue matched-mass screen scored 0.0156 against 0.0369 for random and did not promote.
- `gems47-dcat20-annulus-flankprune-n18524-20261006.tif` is a delete-only subset of a published network. It is a historical learning artifact, not a unique detector.
- The prior 0.34912 modeled score and purported 0.34837 conformal floor are retired. Their score-to-file inputs were not organizer-authenticated and their selected rungs do not justify exchangeable conformal calibration. See [`analysis.md`](analysis.md).

## Scientific and metric boundaries

The official [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) defines the distance-weighted Tversky index. `src/gems47_metric.py` is a local implementation of that stated formula with regression checks; it is not the organizer's private scoring service. H47-B uses public mirror labels for a spatial screening test only. Those labels are not the hidden expert target, and empty blocks do not establish absence of faults.

A future detector requires a new dated preregistration and a valid spatial holdout against an established current best. The feature source must be acquired with permitted provenance, exact grid/coverage measured, and important alternatives/negative controls reported. Do not retune H47-B on its locked blocks and claim independent validation.
