# Erratum — H65 consensus-rank inversion (2026-10-08), corrected before publication

**Status: corrected. The published screen receipt (`evidence/h65/screen.json`) and every
downstream artifact use the corrected field. The first run's numbers are preserved
below so the correction is auditable.**

## What happened

The first run of `scripts/run_h65_screen.py` (2026-10-08, ~02:20 UTC) built the H65
scarp-consensus field through `gems47.h65._lexicographic_rank`, which assigned the
**largest** rank value to the **lowest**-priority cell: `order[0]` (the highest-priority
cell, np.lexsort's primary key first) received `r[0] = 1/n`, the smallest value, because
the rank vector was assigned in sort order instead of reverse sort order. A greedy
top-ranked emitter therefore picked the *worst* cells first — the H65 arm emitted its
dots where **no** lidar channel fired, ranked by *lowest* amplitude tie-break.

The bug was caught by `tests/test_h65.py::test_lexicographic_rank_is_tie_free_and_in_unit_interval`
(asserting the highest-priority cell receives the largest value), which failed on the
first test run — before any artifact was built or published.

## The fix

`src/gems47/h65.py::_lexicographic_rank` now assigns `r[::-1]`, so the highest-priority
cell (consensus count descending, then H60 channel-rank-max descending — exactly the
preregistered definition) receives 1.0 and the greedy emitter picks it first. No other
arm used the helper (H66/H67/H68 reuse `h60`/`rank_scale` machinery whose convention is
already "highest rank = largest value"), so only H65's numbers changed. The
preregistration (`docs/research/h65-hypotheses-preregistered.md`) is unchanged: the
fix implements the frozen definition; the buggy version implemented its reverse.

## First run (buggy field) — preserved numbers

| arm | spacing | selection mean | pooled primary | pooled SGMC | floor | verdict |
|---|---:|---:|---:|---:|---|
| h65 (inverted rank) | 4.6 px | 0.023144 | 0.015698 | 0.066988 | 0.0000 | refuted (artefact of the bug) |
| h66 | 2.0 px | 0.260859 | 0.277174 | 0.202465 | 0.098901 | passed 1–4 |
| h67 | 2.8 px | 0.183113 | 0.206925 | 0.192903 | 0.104529 | passed 1–4 |
| h68 | 2.8 px | 0.267847 | 0.278337 | 0.214547 | 0.099274 | passed 1–4 |
| h60 (incumbent, unchanged) | 2.0 px | 0.284379 | 0.287891 | 0.193813 | 0.098901 | — |
| h50 (anchor, unchanged) | 2.8 px | 0.163039 | 0.165881 | 0.122083 | 0.095701 | — |

Anchors reproduced bit-for-bit in both runs (h50 0.16588059959214113, h60
0.2878910923835811), so the block design, instruments and emitter were identical; only
the H65 field values were inverted.

## Corrected run (published)

| arm | spacing (argmax floor) | pooled primary | pooled SGMC | floor | verdict |
|---|---:|---:|---:|---:|---|
| **h65 (consensus, corrected)** | **2.0 px** | **0.291870** | **0.198403** | **0.097575** | **passed 1–4 AND beats_incumbent_h60** |
| h66 | 2.0 px | 0.277174 | 0.202465 | 0.098901 | passed 1–4 |
| h67 | 2.8 px | 0.206925 | 0.192903 | 0.104529 | passed 1–4 |
| h68 | 2.8 px | 0.278337 | 0.214547 | 0.099274 | passed 1–4 (frozen winner by SGMC tie-break) |
| h60 (incumbent) | 2.0 px | 0.287891 | 0.193813 | 0.098901 | — |

The corrected H65 field beats the H60 incumbent on **both** instruments on the
selection half (primary +1.4 %, SGMC +2.4 %) and is the only arm passing the frozen
`beats_incumbent_h60` condition, so under the preregistered promotion rule **H65
replaces H60 as the primary artifact**. H68 remains the frozen winner by the SGMC
tie-break and is published as a labelled validated candidate.

## Why the correction matters scientifically

The inverted field's refutation (0.0157 primary) was a refutation of a bug, not of the
consensus hypothesis. The corrected field shows the hypothesis is the round's
strongest: requiring several independent lidar operators to fire at the same cell beats
the single-channel maximum on the primary instrument, on the independent SGMC
population, and on four of the five secondary lidar instruments (lapneg 0.3212, step
0.3264, union 0.4071 vs H60's own numbers). This is the mechanism the preregistration
argued for: H60's per-cell max lets one noisy channel spend the budget; consensus
requires independent operators to agree.

Registered as IR-2026-10-08-D in `docs/irregularities.html`.
