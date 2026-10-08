# Historical H47-C1 validation protocol and promotion boundary

> This file records the frozen H47-C1 test and its negative result; it is not the current candidate protocol. H60 later passed a separate local scientific gate, but organizer acceptance is untested and no upload or slot use is authorized or performed in this review. H47-C1 remains not promoted with its gate closed. See [current status](current-status.html) and [H60 evidence](h60.html).

The historical primary experiment was [H47-C1](research/h47c-hypotheses-preregistered.md), frozen before fitting/scoring.
Its [complete receipt](data/profile-screen.json) and [all spacing/block components](data/profile-spacing-history.csv)
are deployed. H47-B and [H47-QC](preregistered-h47qc-20261006.md) are separate historical negative experiments. H47-QC's full [screen report](h47qc-screen-20261006.json) records the independent
geothermometer-consensus screen and its failed gate: pooled test DTI 0.0131689425 versus 0.0141948068 for
the geochemistry-only ablation, at 6 px / 600 m. Its nominal split-conformal level is 6/7 under unverified
block-score exchangeability; its assumption-conditional lower-bound estimate is 0.0. It remains research-only, not for upload.

## Fixed C1 rule and result

Same mass/domain/truth across profile, selection-only best raw/terrain baseline, and fixed-seed random.
Require pooled and mean wins over both controls, at least 10 truth-bearing test blocks, wins in at least
2/3 of those blocks, and a positive assumption-conditional split-conformal lower-bound estimate for the declared proxy target. C1 fails the pooled-baseline and fold-win gates; its assumption-conditional lower-bound estimate is zero. **Not promoted; no slot.** Mirror-only data, unverified exchangeability and private-label mismatch
are additional boundaries, not solved by a positive mean.

Selection 21 blocks and calibration 21 are disjoint roles; test 23 is not a tuning set. Max-residual band is
simultaneous over 5 settings at nominal 90%, rank 20. It predicts one exchangeable catalogue-block vector,
not pooled map/private DTI. Every assumption-conditional lower-bound estimate is 0.0000. No adaptive history or difficult-block deletion.

A documented control-flow bug first overwrote locked 2.8px with 5.8px. The original record is retracted;
correction changed no trained predictions or per-setting scores, proved byte-for-byte. It is not a second
independent model experiment and no new parameter was chosen using test results.

## Requirements for a future hypothesis

1. Source/license/byte/coverage feasibility and authorized input provenance; no login bypass.
2. Novel physical signal and competing explanations, preregistered before scoring.
3. Fresh, guarded evaluation design; known C1 results cannot be reused as untouched validation for tuning.
4. Comparable, same-mass/domain controls; all folds, zero cases, exact components and hashes.
5. Statistical target/unit/rank/coverage clearly scoped; exchangeability not assumed proved by a guard.
6. Strict actual TIFF/ZIP read-back and bounded prior-art audit. A research file can be published with a
   prominent closed gate; only a scientifically promoted/eligible file can be recommended for a slot.
7. Entrant checks rules/eligibility and uses an authorized portal. Retain the exact uploaded SHA, submission
   ID, score and organizer receipt. A public participant row is not a file-to-score receipt.

The repository does not upload automatically. DrivenData monitoring is disabled without recorded written
permission; the permitted-source Pages feed never converts owner projections into verified scores.
