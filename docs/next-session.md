# Next-session handoff — written 2026-10-08 after the H65–H70 round

**Read the standing brief in `README.md` first.** Status in one line: **H60 is published,
gate-passed and is still the file to submit; H50 is the labelled fallback; the H65–H70 challenger
round was negative and built no artifact; no slot has been spent.**

## What happened this round (all committed, `evidence/h65/` + `docs/data/h65-*`)

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
   **no challenger displaced H60.** Closest: H68 relaxed masks wins primary (0.2950) but loses
   SGMC; H69 strict masks wins SGMC (0.2013) but loses primary; H66 (0.2781/0.1983) and H65
   (0.2623/0.1969) beat SGMC but lose primary; H62 re-audit loses both; **H67 refuted**
   (0.0342/0.0420, below random on both — catalogue-tip geometry is anti-predictive).
   Independent recomputation from `spacing-history.csv` matches the receipt to 1e-12.
4. Mechanism notes: the emitter returns byte-identical dot sets at 1.6/1.8/2.0 px (verified
   directly), so 2.0 px sits on a plateau and the downward extension bracketed the optimum
   (1.4 px strictly worse everywhere); H60's 250/150 m mask radii sit at the Pareto middle of a
   real primary-vs-SGMC tradeoff; H60's max-of-six aggregation remains the best
   primary-instrument field (step-only wins the step secondary but loses lappos).
5. Published: `docs/h65.html` round page (+ links from h60/index/executive-summary/method),
   README session-6 section, IR-2026-10-08-E (H50 docstring correlation values were stale;
   committed JSON controls, no score changed). The post-hoc bar was NOT relaxed for the
   near-misses — that is what preregistration is for.

## Priority order for the next session

1. **Submit H60** if a slot is to be spent at all (eligibility/quota checks first, in the
   authenticated portal). Note field: `h60 lidar-scarp d2p0 conformal90`. Keep the receipt.
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
- The legacy site renderer is retired — hand-edit reviewed pages directly and keep the tests
  green; regenerate the root `index.html` mirror from `docs/index.html` with the
  `fix_site_h60.py` prefix logic if the landing page changes.
- DrivenData queries remain prohibited (Terms); the leaderboard snapshot stays dated 2026-10-06.
- Every H60/H62/H65/H66/H68/H69 primary-instrument number must carry the circularity warning:
  the primary instrument derives from the same owner-built lidar stack the fields read —
  necessary, never sufficient; sgmc_offcat is the independent floor. (H67 is exempt — and
  failed anyway.)

## Test and lint state at handoff

`python -m pytest tests -q` → 326 passed, 2 skipped (needs-data skips in a clean checkout:
the H60 artifact tests plus the H50 artifact tests). Ruff clean on every file this session
touched; repo-wide `ruff check .` still carries pre-existing errors in files this session did
not touch — do not "fix" those opportunistically.
