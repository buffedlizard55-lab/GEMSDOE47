# What the scores do—and do not—tell us

**Evidence cutoff:** official sources and pages checked on 2026-10-06 UTC. The competition leaderboard is volatile. This is a research note, not a score forecast.

## First correction: 0.2778 is not verified as the H33 TIFF's score

The user-provided history associates `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` with **0.2778**. The public [GEMSDOE32 landing page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html), however, calls that artifact **UNSCORED**, describes 0.2747 as a *model projection*, and says no organizer score exists for the candidate. The current official public leaderboard shows **participant** rows, not TIFF filenames; the 0.2778 row is participant `extradr19`. A row score cannot establish which file produced it. GEMSDOE41's dated audit also labels the H33 filename-to-score mapping as user-reported and unauthenticated. Therefore:

- “H33-2-B2 earned 0.2778” is **not independently verified** from the official leaderboard or the linked artifact page.
- The exact causal question “why did this TIFF get 0.2778?” is **not answerable from evidence currently available**.
- The defensible answer is conditional: if the group did submit a corresponding file under a team account, sparse emission and catalogue-flank pruning are plausible reasons it could perform well, but this is a hypothesis, not a measured attribution.

## The board moved beyond the prompt's 0.3195

A one-time read of the [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) on 2026-10-06 UTC showed:

| Rank | Participant | Best public DW-Tversky |
|---:|---|---:|
| 1 | alexoktaba | **0.3345** |
| 2 | nchuzhoy | 0.3262 |
| 3 | kinghorton42 | 0.3222 |
| 4 | Batik Shirt Brothers | 0.3218 |
| 5 | DARD | 0.3195 |
| 13 | extradr19 | 0.2778 |

This is a dated public snapshot, not a private-test score or final award result. The leaderboard does not associate a participant's score with a particular raster. Automated polling is intentionally not implemented: DrivenData's [Terms of Use](https://www.drivendata.org/termsofuse/) prohibit robot/spider or other automatic access for monitoring/copying, and also prohibit manual monitoring/copying without prior written consent. The site links the live board and retains this dated snapshot instead.

## What is scientifically plausible about a sparse H33-style result?

The official [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) specifies a distance-weighted Tversky score with `alpha = 0.2`, `beta = 0.8`, and a triangular kernel with 300 m support. In the published formula, false positives are penalized less than false negatives, and predictions closer to truth receive more credit than distant predictions. This favors *useful coverage*, not simply dense probability everywhere.

The official equations define three coupled terms: distance-weighted true positives, false positives weighted by distance from the nearest truth, and false negatives reduced by the best nearby prediction. Adding confidence at one pixel can change more than one term; its marginal value depends on its nearest-truth kernel, whether it becomes the best cover for one or several truth pixels, and the existing prediction/label geometry. Therefore there is no single `alpha`-only pixel-ranking shortcut in this note. Use the pinned official reference scorer on whole holdout maps. A 300 m rasterization tolerance is a scoring feature, not permission to draw arbitrary blobs.

If an H33-2-B2-like file really was submitted, a plausible mechanism is that it removed some redundant prediction mass near already mapped traces while retaining enough nearby coverage of genuinely new faults. Its own project page reports an internal live-mirror improvement and a projected score, but also marks the file unscored. Without the exact prediction bytes, official submission receipt, and labels, we cannot separate a successful scientific detector from a fortunate budget change or a filename/score mismatch.

## What would be needed to claim a genuine improvement?

1. The authorized competition feature/label/template files and checksums.
2. A preregistered, spatially blocked, 300 m-guarded holdout. Model fitting and feature selection must exclude the held-out block; scoring a full-map fit against its training labels is leakage.
3. A same-mass comparison to the best local holdout baseline, fold-level results, and null controls. Existing-label holdout is only a proxy: the private target is expert-labeled faults absent from the public USGS database, so success on known traces does not prove discovery performance.
4. A candidate-to-leaderboard mapping backed by an organizer submission receipt. Public participant best scores alone do not supply this mapping.
5. A final one-file decision that considers the contest's expanded-label final round, not just a public score. The official competition page explains the two-round expert-review structure.

## Current decision

This repository contains no competition rasters, model, incumbent holdout result, or prior TIF. The top-ranked new candidate in [`hypotheses.md`](hypotheses.md) is H47-A, but it cannot be validated until authorized competition inputs are available. The submission gate is therefore **CLOSED**. No previous TIFF was copied and no unvalidated/zero placeholder is presented as a competitive submission.
