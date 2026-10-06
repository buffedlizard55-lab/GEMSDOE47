# GEMSDOE47 — standing charter

> **This file is the project's standing brief. Re-read it at the start of every session and
> treat it as the source of truth for what "done" means.** Everything below the rule is the
> user's brief; everything above it is status.

**Status (2026-10-06):** submission built and verified — `docs/downloads/gems47-dcat20-annulus-flankprune-n18524-20261006.tif`
(18,524 px, sha256 `32c76c92…`, modelled DTI **0.34912**, split-conformal floor **0.34837 at 75 % confidence**).
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
   18,524 pixels are a subset of a published artifact. Take hypothesis H1 or H2 from
   `notes/HYPOTHESES.md`, run it through the blocked-holdout *sanity* filter (not the futile promotion
   gate — see the flagged irregularity in that file), and package the first mask whose pixels are
   ours end to end. That removes the lineage caveat and is the highest-value work left.
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
