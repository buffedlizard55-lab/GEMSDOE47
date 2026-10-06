# Spatial holdout, validation, and promotion protocol

## Current state

Two public-catalogue screens have run; neither is a future plan or private-target validation. H47-B used 4 × 4 disjoint block cores with a 3-pixel/300 m guard, five selection blocks, six calibration blocks, and five locked-test blocks. It scored 0.027553 pooled on locked blocks, versus 0.025639 for the tuned single-scale baseline and 0.037159 for the fixed-seed random control; its assumption-conditional split-conformal lower floor was 0.0. Five blocks had no catalogue truth. See [`validation-h47b-20261006.md`](validation-h47b-20261006.md) and [`preregistered-h2.md`](preregistered-h2.md).

H47-QC separately used a frozen 4 × 4 block split, selected 6 px / 600 m, and scored 0.0131689425 on its locked test versus 0.0141948068 for the geochemistry-only ablation. Its six-block split-conformal nominal level was 6/7 = 85.7%, with a clipped lower floor of 0.0 under unverified block-score exchangeability. Its preregistered gate failed. See [`preregistered-h47qc-20261006.md`](preregistered-h47qc-20261006.md) and [`h47qc-screen-20261006.json`](h47qc-screen-20261006.json).

**No candidate is promoted and no slot is authorized.** H47-B and H47-QC use distinct candidate definitions and holdout screens; do not compare their raw DTI values as if they were one standardized leaderboard.

The experiment used group-hosted mirrors, not authenticated organizer downloads. The local DTI implementation was transcribed from the official [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/); it is not an organizer-run private scorer. A public-label score cannot establish performance on expert-private labels.

## Requirements before the next candidate is scored

1. **Authorized provenance.** Obtain available competition inputs through an authorized route. Record each exact file hash, metadata, label semantics, source URL, license/terms and any differences from group-hosted mirrors. Do not bypass login or use credentials not authorized for this project.
2. **Current holdout best.** Establish a reproducible, scientifically defensible spatially blocked baseline using the same target, footprint, metric implementation and comparable spatial test areas. Store code/input hashes and per-fold outputs. Historical participant scores and the old d-cat/annulus TIFF are not incumbents.
3. **New preregistration.** Before calculating held-out results, freeze the distinct physical hypothesis, inputs, code revision, feature transforms, emission mass, spatial fold assignment, guard, matching rules, random/domain controls, metric, selection rule, conformal design (if defensible), and promotion criteria. Do not reuse H47-B's locked blocks to tune H47-B and then call them an independent test.
4. **Spatial separation and label coverage.** Use projected coordinates in metres. Reserve geographically distinct blocks and purge at least 300 m around held-out boundaries for this 100 m grid, so the official 300 m kernel cannot transfer direct credit between folds. Record positive truth counts and prediction mass per block before interpreting block scores. Empty blocks are uninformative about geological discovery and cannot count as positive evidence.
5. **Comparable evaluation.** Score the incumbent and candidate on the same disjoint held-out cores with matched emitted mass (or a preregistered justified alternative), pooled metric components and per-block DTI. Include a fixed-seed random/spatially matched control and relevant domain/ablation controls. Report both pooled and unweighted block summaries; neither should conceal an adverse result.
6. **Conformal restraint.** If split conformal is used, define the exchangeability unit and target before scoring, use independent calibration blocks, report sample count, rank, raw residuals, nominal coverage, clipped floor, label coverage and all assumptions. Spatial dependence means exchangeability is not established merely by separating blocks. A zero floor, empty/degenerate calibration blocks, or an indefensible assumption does not satisfy a positive-floor gate.
7. **Promotion rule.** Require the new candidate to beat the current spatially blocked holdout best and the preregistered controls under the fixed rule, with adequate label coverage and a scientifically meaningful result. The comparison must not depend on leaderboard feedback. A tie, failed control, unstable fold pattern, failed/zero lower floor where required, changed hash, or missing receipt closes the slot gate.
8. **New unique raster.** Only after promotion, generate a new prediction (not a copy/prune), compare it against accessible prior TIFF artifacts, save exact-match and similarity results plus search scope, then write to the current official sample-submission profile and re-open/audit the exact bytes.
9. **Manual portal action.** Only an authorized team member may submit manually after checking current rules, limits and form instructions. Save an organizer receipt that ties submission ID, uploaded SHA-256 and score. Never infer a file's score from the participant leaderboard.

## Existing implementation boundaries

- `scripts/package_submission.py` is a fail-closed packager for the older H47-A report schema. It does not score a holdout, authenticate a report, or validate H47-B; a package script is not scientific approval.
- `scripts/run_h2_experiment.py` is permanently research-only because H47-B used public-mirror labels and features; it always records `slot_eligible: false` and has no non-research publication option. `--publish-research-only` is the only way it can copy a TIFF to `docs/downloads/`, and it uses an unmistakable research-only filename/status. A separate, authorized-input hypothesis requires a new protocol and candidate identity.
- `scripts/validate_submission.py` checks raster profile/value conditions against provided local files. It cannot authenticate official provenance or guarantee organizer acceptance.
- `docs/promotion-report.schema.json` is a data-shape aid for the legacy packager, not evidence that the current candidate passed.

## Interpretation

A gain on spatially held-out public catalogue traces can screen for spatial overfit, but the public catalogue is not the hidden expert target. A format-valid TIFF, a unique mask, or a public leaderboard row is not by itself evidence of future/private performance. The slot stays unused until the entire chain is supported by reproducible evidence.
