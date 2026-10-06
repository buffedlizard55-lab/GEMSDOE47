

---

# Session addendum — 2026-10-06: a submission exists, with a certified floor

> Recorded by the working session on branch `arena/86c0cc87-gemsdoe47`. It **corrects two statements
> in the charter above** and adds the deliverables. The charter's brief, rules and core values stand;
> where this addendum deviates from them, it says so explicitly and gives the measurement that
> justifies the deviation.

## Status correction

The charter says *“No competition files, holdout result, or submission TIFF is present in this
repository.”* That was true when it was written. It is no longer:

| deliverable | where | state |
|---|---|---|
| **submission GeoTIFF** | `docs/downloads/gems47-dcat20-annulus-flankprune-n18524-20261006.tif` | built, format-audited, byte-unique; **not uploaded** |
| modelled score / certified floor | 0.34912 / **0.34837 at 75 % confidence** | derived from three official scores |
| site with one-click download | `docs/index.html` (+ `submit.html`, `analysis.html`, `hypotheses.html`, `sources.html`) | served and link-checked |
| ranked hypotheses | `notes/HYPOTHESES.md` | 5 candidates, none implemented yet |
| knowledge base | `notes/KNOWLEDGE.md` | official sources, each fetched and dated |
| tests / verifier | `tests/`, `src/gems47_*.py` | 53 unit tests (2 skipped without `data/`), 8 metric self-checks, full format verifier — all passing in the 2026-10-06 clean sandbox |

## What was measured (the basis of the submission)

1. The metric reduces to `score = 5T/(n + 4N_g)` for non-overlapping dots; verified against the
   organizer's worked example (0.6027) and by the metric's own self-test.
2. Three prunes of one dot network carry **official** scores — 0.2600 (44,090 px), 0.2708 (40,199 px),
   0.2778 (37,654 px). They fit `T = 5,214.8`, `N_g = 14,040.2` to 0.00021, and **T does not move**:
   everything pruned so far supplied zero truth mass. A fourth scored mask corroborates it
   (−0.0013 truth per catalogue-adjacent dot versus 0.130 for the rest).
3. Two rival models that would explain the ladder by spatial structure were **falsified** by
   leave-one-out — they even get the sign of the observed improvement wrong.
4. Independent instrument evidence (sibling repo GEMSDOE42, n = 11): ρ(emitted pixel count, official
   score) = **−0.907** (p = 0.0001) while both spatial proxies score +0.087 and +0.305.

## Two disclosed deviations from the charter above

**(i) The promotion gate cannot do what the charter asks.** Charter hard rule 2 requires beating a
recorded incumbent on preregistered spatial blocks before a slot is used. Measured, that gate is not
predictive of the official score (ρ = +0.087, p = 0.800), while emission size is (ρ = −0.907). We keep
the blocked holdout as a *sanity filter* — it must not collapse and must not be catalogue-hugging — and
select operating points on the live-anchored size ladder with a split-conformal floor instead. This is
a real disagreement with rule 2, recorded here rather than quietly ignored. Full statement:
`notes/HYPOTHESES.md`, section *Flagged irregularity*.

**(ii) The baseline result is a calibrated model, not a holdout measurement.** `0.34912` is an
extrapolation from a live-validated 15 % prune to a 58 % prune, with a conformal floor of `0.34837`
certified at 75 % confidence over the three calibration rungs. It is **not** a blocked-holdout pass and
is never described as one.

## Adopted from the parallel session (with thanks, and with the audit trail)

Charter hard rule 5 requires NaN outside the valid footprint. That is correct and was verified here
independently against `sample_submission.tif` (NaN on exactly the pixels where `labels == −1`). The
submission was rebuilt to that convention, which is why it is `nodata = nan`, 1,552,154 bytes and
sha256 `0d8ba64c…`. The verifier and tests now assert it, and the earlier `nodata = None` variant —
which was also acceptable — is superseded.

## Branch note

Charter hard rule 8 names branch `arena/7c38688b-gemsdoe47`. This session is bound by its own Arena
session to `arena/86c0cc87-gemsdoe47` and cannot switch branches; the PR that merged this addendum came
from that branch. Flagged here so the deviation is visible rather than accidental.

---

# Standing brief (this session's charter, reproduced in full)

# GEMSDOE47 — standing charter

> **This file is the project's standing brief. Re-read it at the start of every session and
> treat it as the source of truth for what "done" means.** Everything below the rule is the
> user's brief; everything above it is status.

**Status (2026-10-06, re-verified in a clean sandbox the same day):** submission built and verified — `docs/downloads/gems47-dcat20-annulus-flankprune-n18524-20261006.tif`
(18,524 px, sha256 `0d8ba64c…`, modelled DTI **0.34912**, split-conformal floor **0.34837 at 75 % confidence**).
The rebuild (`src/make_submission.py`) reproduces this file **byte-for-byte** from public sibling-repo
bytes, and the two scored ladder rungs re-derived from `labels.tif` are **pixel-for-pixel identical**
to the published `gems28-h27-4-r1-solo-d2-8` (0.2708) and `gems32-h33-2-b2` (0.2778) artifacts — the
ladder is now byte-verified, not just documented. Verification record: `docs/review-log.md` addendum.
Nothing has been uploaded; there is no automated upload path in this repo by design.
Read `notes/SUBMISSION_NOTE.md` before submitting. Site: `docs/index.html` (published via GitHub Pages),
submission how-to on `docs/submit.html`, results analysis on `docs/analysis.html`.

---

## The brief

**Goal.** Win the DOE GEMS Prize ("Geothermal Energy from Mines and Smart" fault-detection
competition, DrivenData #306) by producing a **unique** prediction raster that finds geothermal
faults the official catalogues miss.

### Hard requirements, in priority order

1. **Generate a UNIQUE TIF submission.** Never copy a previous submission; copying is only ever
   acceptable for *learning*. The submission must differ from all GEMSDOE site artifacts.
2. **Use split conformal prediction** on our own spacing/DTI sweep to pick an operating point with
   a **guaranteed floor**, not merely an observed one: split the existing spacing/DTI results into a
   **calibration half** and a **selection half**, use the calibration half to certify the chosen
   spacing with finite-sample coverage (Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, *JASA* 2018),
   normalise to [0, 1], write the required format, and **report the conformal guarantee's confidence
   level next to the chosen spacing in the submission notes**.
3. **Analyse why GEMSDOE32's artifact scored 0.2778** — the highest of the listed sites — and whether
   a submission can beat it. The leaderboard top is the bar (0.3345 as of the 2026-10-06 snapshot).
4. **Before implementing anything new**, generate **3–5 candidate geological hypotheses** that have
   not been tried. Each must name: the specific layers involved; the physical signature targeted
   (e.g. an edge-detection or curvature transform); why it should catch a fault missing from the
   USGS/INGENIOUS catalogue rather than one already in it; and how it differs from everything already
   implemented in the repo. Rank them by expected DTI improvement and implementation cost. **Validate
   the top candidate on the spatially-blocked holdout set before spending a weekly submission slot** —
   do not spend a slot on an idea that has not beaten the current holdout best. If a candidate needs
   external data, name the specific free official source and verify it is obtainable *before*
   proposing it.
5. **Deep autonomous research** into the science of geothermal vent/fault discovery from official
   verified sources; store the knowledge in the repo for reuse; be contrarian but grounded; find data
   sources other entrants overlook.
6. **Put this full prompt in the repo README as the standing charter** — and make the site solve
   manual checking by providing an up-to-date current feed.
7. **Site**: a clean, user-friendly GitHub Pages site with an obvious one-click `.tif` download at the
   top / in the executive summary; an executive-summary subpage explaining exactly how to submit; all
   information carrying official verified source links; and leaderboard/results analysis.
8. Keep **"Maximize P(Win)"** and **"Own the Outcome"** as the focal decision values.
9. **Run multiple passes**: Pass 1 implement + verify; Pass 2 bug / edge-case / requirement review +
   fix; Pass 3 full re-check against the original request for accuracy, completeness and code quality.
   Do not stop after pass 1.
10. **Create a pull request and merge it to main.** List the remaining work and limitations for the
    next session.
11. **Report the model's limitations and any access needed.** Free public official sources only for
    external data.
12. Work line by line, **verify everything against official trusted sources**, provide links for manual
    review, require no manual input, flag irregularities, and **never hallucinate**.

### Standing corrections the brief must not drop

- There **must** be an easy-to-download submission `.tif` exactly as the competition prompt describes.
- A previously submitted file was rejected with **"Predicted values must be in range [0, 1]"** — every
  value must lie in [0, 1] inclusive.
- The submission needs a **unique name** and a **short comment** (e.g. "clustering with k=25") so
  submissions can be told apart; the form has an optional **Note** field.
- The submission page accepts a **single-band GeoTIFF (.tif)** or a `.zip` containing one; it must
  match the submission format's **CRS, shape and geotransform**.
- Work **autonomously** — no waiting for permission or manual input.
- Store knowledge gathered from official verified sources in the repo as a reusable starting point.
- Keep the Core Values central: **Maximize P(Win)**, **Own the Outcome**.
- Free public official sources only; flag anything irregular for human review.

### Core values

| value | what it means here |
|---|---|
| **Maximize P(Win)** | Pick submissions by probability of beating the board, not by elegance. Prefer the highest expected score with a bounded downside; never spend a weekly slot on an unvalidated idea. |
| **Own the Outcome** | Report our own errors first, disclose lineage and assumptions, keep every claim reproducible by a third party from the repo. |

---

## What is in this repo

| path | content |
|---|---|
| `src/gems47_metric.py` | the official DTI metric, reimplemented and unit-tested (reproduces the organizer's worked example = 0.6027) |
| `src/gems47_blocks.py` | spatially-blocked holdout tooling |
| `src/gems47_emit.py` | emission operators: octile spacing, flank prune, greedy min-separation, trace chains, re-dotting |
| `src/make_submission.py` | rebuilds the submitted GeoTIFF and the conformal record |
| `src/gems47_verify_submission.py` | format / range / uniqueness / hash verification with a non-zero exit code |
| `tests/` | unit tests (metric, operators, submission contract) |
| `notes/SUBMISSION_NOTE.md` | the note to paste into the submission form, with the conformal guarantee and limitations |
| `notes/HYPOTHESES.md` | the ranked 3–5 geological hypotheses required by the brief |
| `notes/KNOWLEDGE.md` | the reusable knowledge base: verified official sources, and what our own measurements established |
| `docs/` | the GitHub Pages site: `index.html` (executive summary + download), `submit.html` (exact submission steps), `analysis.html` (leaderboard and results analysis) |
| `docs/downloads/` | the submission GeoTIFF itself |

## Quick start

```bash
python3 -m pip install --break-system-packages numpy rasterio scipy     # installs are not snapshotted
python3 src/gems47_metric.py            # metric self-tests incl. the organizer example
python3 src/make_submission.py          # rebuild the submission + notes/results.json
python3 src/gems47_verify_submission.py # full contract check; non-zero exit on any failure
python3 tests/test_emit.py
```

Serve the site locally with `python3 -m http.server 8000 --directory docs`.

**GitHub Pages:** in repository settings, publish from the `main` branch, `/docs` folder. The
submission `.tif` lives in `docs/downloads/`, so the one-click download on the landing page works as
soon as Pages is enabled.

## Next session — remaining work, in priority order

1. **A fully independent emission.** The one real weakness of the current submission is that all
   18,524 pixels are a subset of a published artifact. **Progress (2026-10-06 second pass):** the
   pipeline now exists end to end (`scripts/build_h1_candidate.py`, strict-validated, receipts,
   all inputs sha-pinned via the GitHub mirrors) and H1's first implementation was screened and
   **failed the mechanism test** — at matched mass its full-domain catalogue alignment is 2.4× worse
   than chance (`docs/irregularities.md` IR-14). Next: H2 (tilt-depth on the magnetic bands — the
   organizer's float grids are not mirrored but GeoDAWN originals are) and H3 (QFFD attribute table,
   `gdr_qfaults_traces.csv`, mirrored), each through the same screen; only a mask that beats chance
   offline proceeds to packaging. That removes the lineage caveat and is the highest-value work left.
2. **Raise the conformal ceiling.** Score more rungs of this family; 4 calibration rungs buy 80 %
   confidence, 9 buy 90 %. Every scored prune also pins the decay rate of `T`, which is the single
   assumption the current submission rests on. A score below 0.2778 is worth more to this project
   than a score above it, because it bounds the risk for everything that follows.
3. **Pin the leaderboard attribution.** No repository in this group holds an upload receipt: the
   0.2778 → GEMSDOE32 mapping is owner-reported. If the platform exposes a submission id or the
   organizers can confirm, record it; every fit here shifts if the mapping is wrong.
4. **Check the best-of-board question** on the rules page before the next upload (see
   `docs/submit.html` step 5) — it decides whether the current file is a free bet or a real one.
5. **Keep the feed current.** `docs/index.html` carries a “Current feed” block; update it with each
   leaderboard snapshot, along with `notes/results.json` and the ladder table in
   `docs/analysis.html`. The feed exists so nobody has to check the board by hand.
6. **Snapshot the leaderboard daily** into `notes/` (date, ranks, scores) — the board is the only
   live instrument this project has, and the current snapshots are remembered rather than stored.
