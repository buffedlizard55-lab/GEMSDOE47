# Next-session handoff — written 2026-10-08 after the H65–H70 round and the PR #28 reconciliation

**Read the standing brief in `README.md` first.** Status in one line: **H60 passed the local
preregistered scientific gate and survived a six-challenger round; organizer acceptance is untested;
no portal upload or slot use is authorized or performed in this review. H47-C1 remains not promoted
and its gate remains closed.**

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
