# Next-session handoff — written 2026-10-08 after the H65–H70 round and the PR #28 reconciliation

**Read the standing brief in `README.md` first.** Status in one line: **H60 passed the local
preregistered scientific gate and survived the six-challenger H65–H70 round; the second slate
H71–H74 then found H71 beating H60 on both holdout instruments (held back by the frozen
uniqueness bar) and built H74 as a gate-passing unique candidate; organizer acceptance is untested;
no portal upload or slot use is authorized or performed in these reviews. H47-C1 remains not
promoted and its gate remains closed.**

## What happened this round (session 6 + merge)

1. The slate H65–H70 was preregistered and committed alone (`ebf9abf`) **before** any score:
   `docs/research/h65-hypotheses-preregistered.md`. Displacement gate: beat H60 on BOTH the
   primary lidar-peak instrument AND the independent SGMC population, plus a positive conformal
   floor.
2. `scripts/run_h70_instruments.py` (H70, seed 20261008): downface peaks (+0.350 far) are the
   weakest lidar channel yet; SGMC variants show a reverse distance gradient (−0.355 at >100 m …
   +0.278 near) with the frozen >300 m population at −0.025; 21 volcanic vents uninformative
   (+0.207, p = 0.52). Full 34-row ladder: `knowledge/07_h50_h64_h70_instrument_ladder.md`.
3. `scripts/run_h65_screen.py` ran the frozen 41-block screen with an extended 1.4–3.2 px sweep
   (H50/H60 anchors reproduced bit-for-bit; blocks asserted byte-equal to `evidence/h50/`):
   **no challenger displaced H60.** Closest: H68 relaxed masks leads primary (0.2950) but loses
   SGMC; H69 strict masks leads SGMC (0.2013) but loses primary; H66 (0.2781/0.1983) and H65
   (0.2623/0.1969) beat SGMC but lose primary; H62 re-audit loses both; **H67 refuted**
   (0.0342/0.0420, below random on both — catalogue-tip geometry is anti-predictive).
   Independent recomputation from `spacing-history.csv` matches the receipt to 1e-12. This
   executed the prior handoff's items 3 (sub-2.0 px sweep), 4 (mask ablation) and 5 (H62
   re-audit).
4. Mechanism notes: the emitter returns byte-identical dot sets at 1.6/1.8/2.0 px (verified by
   direct set comparison on H50 and H60 blocks plus identical 20-block DTI vectors for all six
   lidar arms), so 2.0 px sits on a plateau and the downward extension bracketed the optimum
   (1.4 px strictly worse for every arm); H60's 250/150 m mask radii sit at the Pareto middle of
   a real primary-vs-SGMC tradeoff; H60's max-of-six aggregation remains the best
   primary-instrument field (step-only leads the step secondary but loses lappos).
5. Published: `docs/h65.html` round page (+ pointers from h60/index/executive-summary/method),
   README session-6 section, IR-2026-10-08-A/B/C/E, and IR-2026-10-08-D (resolved: the lint pass
   it called for landed via PR #28). The post-hoc bar was NOT relaxed for the near-misses —
   that is what preregistration is for.
6. **Merge reconciliation with `main` (PR #28, commit `8708545`).** The sibling session
   reconciled the site to a no-upload boundary (the all-finite H60 encoding does not satisfy the
   published null/NaN-outside wording; the NaN-outside variant is inspection-only; organizer
   acceptance untested), fixed repo-wide ruff, and rewrote `tests/test_site.py` with 17
   boundary/byte-encoding tests. This merge adopts their pages and tests as base: session-6
   content was re-applied with adapted semantics ("current local candidate", never "file to
   submit"), the session-6 site-fixer scripts were removed (they encoded the superseded
   upload-ready wording), and the root `index.html` mirror was regenerated from the reconciled
   `docs/index.html`. The root-mirror regression test survives in rewritten form (pure
   mirror-freshness, no upload language).

## Priority order for the next session

1. **No portal action in this review.** If a later attempt is separately authorized, first
   confirm eligibility and account state in the authenticated portal; the official DOE/NLR rules
   state up to three scoring/feedback submissions per week and one final selected file, but do
   not show this account's remaining opportunities. Review the NaN-outside TIFF and its
   exact-byte audit; do not use the all-finite diagnostic or current ZIP as the upload file.
2. **Independent-instrument program (highest scientific value, no slot needed).** The primary
   instrument still derives from the same owner-built lidar stack the field reads. Candidates,
   all free/official: USGS Quaternary fault compilation (Qfaults — hash-pinned `Qfaults_GIS.zip`
   sha256 `447eadc5…` is already fetchable per `docs/data/official-download-probes.json` in an
   unrestricted session), Nevada Bureau geologic map contact traces. Goal: an instrument with
   zero shared code path with the field.
3. **A preregistered combined criterion (preregister first).** H68 won primary-only and H69 won
   SGMC-only. If the next round wants a single displacement score (e.g. a weighted combination
   or a Pareto rule), the weights/rule must be frozen BEFORE any score is read — the H65 numbers
   above are now known and cannot calibrate that choice without bias.
4. **New fields, not new spacings.** The 1.4–3.2 px sweep bracketed the optimum and the emitter
   has coarse equivalence classes (1.6/1.8/2.0 identical sets), so further spacing grids are
   low-value. Untried field ideas from the prereg: off-lidar fields (C2 geophysical lag, C4
   drainage/paleodischarge — see `docs/hypotheses.html`), finer field-dependent emission
   spacings, H62-style mixtures at their own operating points (runner-up only, fresh gate).
5. **Refuted and closed (do not rerun):** catalogue-adjacency gating (H63), per-trace
   reallocation (H61), tip proximity (H67). No catalogue-geometry field survives.

## Known traps (do not rediscover)

- `.cache/gems_data` and `.venv` are NOT persisted: `python3 scripts/restore_data.py --group all`
  then `python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt -r
  requirements-research-lock.txt` (~20 s; system python3 lacks rasterio).
- `greedy_spaced_pixels` raises when a restricted domain cannot hold the budget at a spacing —
  use `h60._greedy_up_to` (binary-search cap) and report the actual emitted mass.
- `emit_trace` requires the domain to hold the budget at the spacing (true for every real block;
  starved synthetic grids in tests must be ≥300×300).
- Module-level helpers must be defined before their callers in `h60.py` (edit-ordering trap).
- Parallel `edit_file` calls to the SAME file are unreliable — edit sequentially, grep-verify.
- The historical site renderers and H50/H60 page updaters fail closed (exit 2, `DISABLED:`) —
  they would restore stale upload recommendations. Hand-edit reviewed pages; keep the no-upload
  boundary strings and the exact-byte pins the site tests assert.
- The root `index.html` is a generated mirror of `docs/index.html` (Pages serves `main:/`).
  After any landing-page edit, regenerate: repoint every relative `href`/`src` under `docs/`
  and set `data-base="docs/"`. The mirror-freshness test fails otherwise.
- DrivenData queries remain disabled under the Terms boundary; the latest permitted manual
  public-board observation is dated 2026-10-07 and is not a live feed.
- Every H60/H62/H65/H66/H68/H69 primary-instrument number must carry the circularity warning:
  the primary instrument derives from the same owner-built lidar stack the fields read —
  necessary, never sufficient; sgmc_offcat is the independent floor. (H67 is exempt — and
  failed anyway.)

## Test and lint state at handoff

`python -m pytest tests -q` → 327 passed, 2 skipped (needs-data skips in a clean checkout).
`python -m ruff check .` → clean (PR #28 fixed the pre-existing errors; CI enforces it).
CI parity: `python -m pytest tests -q -m 'not needs_data'` → 307 passed, 1 skipped,
21 deselected; `PYTHONPATH=src python -m unittest discover -s tests` → 93 tests OK.

## The H71–H74 round (session-6 SECOND slate, 8 October 2026) — reconciled with the H65–H70 round

A second concurrent session-6 slate (preregistered at
`docs/research/h71-hypotheses-preregistered.md` before any score; renumbered H71–H74 during the
additive reconciliation with the H65–H70 sibling above — the fields, design and numbers are
unchanged, the renumbered screen reproduces the original receipt exactly, and the published
artifact bytes are identical) screened four new hypotheses on the same frozen 41-block holdout
with this round's methodological change: **the operating point is the argmax of the certified
split-conformal lower bound** (`gems47.conformal.choose_operating_point`), not the observed
maximum.

* **H71 scarp-consensus** (count of lidar channels firing at the same cell, amplitude-tie-broken):
  **0.291870 primary / 0.198403 SGMC at 2.0 px (floor 0.0976)** — the ONLY arm beating the H60
  incumbent (0.287891 / 0.193813) on BOTH instruments, consistent across the secondary lidar
  instruments (lapneg 0.3212, step 0.3264, union 0.4071). Requiring several independent operators
  to agree beats the single-channel maximum: the mechanism the preregistration argued for.
* **H74 eight-channel lidar** (H60's six + `ex_max` + `relief`): 0.278337 / 0.214547 at 2.8 px
  (floor 0.0993) — the frozen winner by the SGMC tie-break and the round's best
  independent-instrument DTI.
* **H72 far-field lidar**: 0.277174 / 0.202465 at 2.0 px (floor 0.0989).
* **H73 alteration-corroborated** (lidar + GeoDAWN Th/K, 50/50): 0.206925 / 0.192903 at 2.8 px —
  the round's best certified floor (0.1045).
* All four passed the four control conditions; none was refuted. Anchors H50/H60 reproduced
  bit-for-bit.

**Artifacts built** (17/17 read-back checks each; 37,654 unit dots each; both all-finite and
NaN-outside encodings published; organizer acceptance of either encoding untested):

* **H74** `gems47-h74-lidar-8ch-s2p8-20261008-allfinite.tif` — SHA-256
  `a0e82ce0e2f8cfa11b9759d47ec36ec259923d8137b0057a557e4701d245c50c`, 307,486 bytes —
  **validated candidate**: gate-passing valid submission (conditions 1–4 + uniqueness),
  OK to download, NOT the recommendation while H60 stands. Portal note
  `h74 lidar 8-channel d2p8 conformal90`.
* **H71** `gems47-h71-scarpconsensus-s2p0-20261008-allfinite.tif` — SHA-256
  `cbae340361811abb7e7f6d0a1712d9adad087562c24479cb98439d5561225a17`, 298,948 bytes —
  **research artifact, NOT OK TO SUBMIT while the uniqueness bar stands**: it beat H60 on both
  instruments (conditions 1–5) but its emission overlaps the H60 incumbent artifact at mask
  Jaccard 0.5119 ≥ 0.5, failing frozen condition 6; unique (0.0067) against every scored prior
  submission. IR-2026-10-08-J.

**Honesty items:** an inverted consensus-rank bug was caught by
`tests/test_h71.py::test_lexicographic_rank_is_tie_free_and_in_unit_interval` before any artifact
was built, fixed (`r[::-1]`), and the screen re-run — both runs' numbers preserved in
`evidence/h71/erratum-consensus-rank-20261008.md` (IR-2026-10-08-I). The tie-break tension
(SGMC negatively rank-correlated with the owner-reported scores vs the primary positively
correlated) is IR-2026-10-08-G. The 0.2778 question was answered with measurements
(`scripts/analyze_h33_reference.py` → `evidence/h33_reference_analysis.json`): h33-2-b2 is the
scored d2.8 emission pruned 44,090 → 37,654 dots (strict mask subset, Jaccard 0.854), 59.6 % of
its dots inside the road/claim noise masks; the 0.2600 → 0.2778 move is the DTI pruning algebra —
mass discipline on an existing field, not a new signal.

## Priority order for the next session (after both rounds)

1. **Owner decision on the slot.** H60 remains the local candidate. H74 is a valid, unique
   alternative if the owner accepts the primary-instrument trade-off. H71 is the strongest
   science but is blocked by the frozen uniqueness bar — do **not** amend that bar after the
   scores (H49 failure mode); submitting H71 would be an explicit, recorded owner decision
   overriding a self-imposed discipline.
2. **Uniqueness-bar-compliant H71 variant.** The 0.5119 overlap comes from emitting the same
   budget at the same spacing over the same domain with correlated fields. A preregistered
   variant (different budget, domain restriction, or hybrid tie-break) could clear the bar.
3. **Independent-instrument program.** The primary instrument shares the lidar modality with
   every lidar-reading field; H73's Th/K component is independent of it. The GeoDAWN Th/K and
   U/K grids are already restored and hash-pinned (USGS GeoDAWN release, DOI
   10.5066/P93LGLVQ); USGS MRData ASTER alteration is named but not fetchable from this
   sandbox; QFaults/NBMG M167 are already inside the training labels (closed).
4. **H73 λ sweep or Th/K ablation.** The alteration arm kept the second slate's best certified
   floor (0.1045) but diluted the primary instrument; isolate whether the radiometric
   component carries signal.
5. **Convergence check across the two rounds.** H66 (sibling, consensus-MEAN) and H71 (second
   slate, consensus-COUNT) are different consensus definitions with opposite outcomes — worth a
   preregistered head-to-head if consensus is revisited.

## Known traps (do not rediscover)

- Two session-6 slates exist: the sibling H65–H70 (negative; `src/gems47/h65.py`,
  `evidence/h65/`, `docs/h65.html`) and this second slate H71–H74 (`src/gems47/h71.py`,
  `evidence/h71/`, `docs/h71.html`). Do not merge their identifiers; both are published.
- `h71._lexicographic_rank` assigns the LARGEST value to the HIGHEST-priority cell (fixed
  2026-10-08; the first version was inverted — see the erratum). The test pins the direction.
- The uniqueness audit reports `max_jaccard` (all priors, including this repo's published
  artifacts) and `max_jaccard_vs_scored_priors` separately.
- `scripts/update_site_h71.py` is idempotent and regenerates the root `index.html` mirror
  (Pages serves `main:/`); every replacement asserts it matched.
- DrivenData queries remain prohibited (Terms); the leaderboard snapshot stays dated.
- Every conformal floor is assumption-conditional on block exchangeability and covers one future
  exchangeable block's proxy DTI — never the private leaderboard.
