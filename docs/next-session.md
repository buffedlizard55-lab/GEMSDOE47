# Next-session handoff — written 2026-10-07 after the H60–H64 round

**Read the standing brief in `README.md` first.** Status in one line: **H60 is published,
preregistered, gate-passed and is the file to submit; H50 is the labelled fallback; no slot has
been spent.**

## What happened this round (all committed, `evidence/h60/` + `docs/data/h60-*.json`)

1. The slate H60–H64 was preregistered and committed (`5ea987b`) **before** any score:
   `docs/research/h60-hypotheses-preregistered.md`.
2. Two external rasters were added to `registry/data_manifest.json` and hash-verified
   (`ext_tiger_road_distance_m`, `ext_blm_closed_claim_distance_m`) for the noise masks.
3. `scripts/run_h60_screen.py` ran the frozen 41-block screen (blocks byte-equal to
   `evidence/h50/blocks.json`; H50 anchor reproduced bit-for-bit at 0.16588059959214113):
   **H60 passed the gate** (primary 0.2879 vs anchor 0.1659; independent SGMC 0.1938 vs random
   0.0698; conformal floor 0.0989 at ≥90.91 %), **H62 passed but lost the SGMC tie-break**
   (0.2458 / 0.1850), **H61 refuted** (0.1636 — per-trace reallocation does not help),
   **H63 refuted** (0.1567 — catalogue-adjacency gating hurts).
4. `scripts/run_h64_instruments.py`: far-from-catalogue peaks beat near ones (lappos ρ +0.581 vs
   +0.273); the road/claim masks *improve* the instrument-leaderboard correlation (step +0.592
   vs +0.449); `coh100` anti-correlates (−0.532). This is the mechanism evidence for the masks.
5. `scripts/build_submission_h60.py` built and published the artifact
   (`docs/downloads/gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif`, SHA-256
   `4ee074230a305fce6768012fc33380bf196c89170e70050a77cf4a44d74ef14c`, 37,654 dots, 17/17
   read-back checks, 0 exact matches, max Jaccard 0.0217) + ZIP + note + receipt + NaN-outside
   fallback. `scripts/update_site_h60.py` moved the site to H60 (H50 demoted to labelled
   fallback everywhere, including the register and the executive summary).
6. Corrections published: IR-2026-10-07-B (lidar stack is owner-derived, not organiser-supplied),
   IR-2026-10-07-C (H50 screen had 41 blocks, not 61), IR-2026-10-07-D (H61 min-1 floor deviation
   + emitted-mass aggregation bug; no score changed). `docs/h50.md` was already known empty —
   the H50 evidence lives on `docs/h50.html` and `evidence/h50/`.

## Priority order for the next session

1. **Submit H60** if a slot is to be spent at all (eligibility/quota checks first, in the
   authenticated portal). Note field: `h60 lidar-scarp d2p0 conformal90`. Keep the receipt.
2. **Independent-instrument program (highest scientific value, no slot needed).** The primary
   instrument derives from the same owner-built lidar stack the field reads. Candidates, all
   free/official: USGS Quaternary fault compilation (Qfaults — hash-pinned `Qfaults_GIS.zip`
   sha256 `447eadc5…` is already fetchable per `docs/data/official-download-probes.json` in an
   unrestricted session), Nevada Bureau geologic map contact traces, the SGMC at finer thresholds.
   Goal: an instrument with zero shared code path with the field.
3. **Spacing below 2.0 px (preregister first).** H60's selection-half mean rises monotonically to
   the sweep edge (0.2844 at 2.0). Extend the sweep to 1.4–2.4 with the conformal guarantee made
   simultaneous over the extended set. Watch block capacity: at 1.6 px the masked domain may not
   hold block budgets (17,889 of 21,198 already at 2.0) — record under-emission, never hide it.
4. **Domain/mask ablation (preregister first).** The mask radii (250 m road / 150 m claim) were
   frozen pre-score. H64 says the masks *help* the instruments, but the radius values were never
   swept. A 3×3 radius grid is one screen.
5. **H62 mixture re-audit.** It passed the gate and lost only the tie-break; its whole-map
   emission is untested. If a second submission window ever justifies a second candidate, H62 at
   its own operating point is the honest runner-up — build the artifact only under a fresh gate.

## Known traps (do not rediscover)

- `.cache/gems_data` and `.venv` are NOT persisted: `python3 scripts/restore_data.py --group all`
  then `python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt -r
  requirements-research-lock.txt` (~20 s; system python3 lacks rasterio).
- `greedy_spaced_pixels` raises when a restricted domain cannot hold the budget at a spacing —
  use `h60._greedy_up_to` (binary-search cap) and report the actual emitted mass.
- `emit_trace` requires the domain to hold the budget at the spacing (true for every real block;
  starved synthetic grids in tests must be ≥300×300).
- Module-level helpers must be defined before their callers in `h60.py` (edit-ordering trap).
- The legacy site renderer is retired — hand-edit or use the assertion-checked
  `scripts/update_site_h60.py` pattern; every replacement asserts it matched.
- DrivenData queries remain prohibited (Terms); the leaderboard snapshot stays dated 2026-10-06.
- Every H60/H62/H63 primary-instrument number must carry the circularity warning: the primary
  instrument derives from the same owner-built lidar stack the fields read — necessary, never
  sufficient; sgmc_offcat is the independent floor.

## Test and lint state at handoff

`python -m pytest tests -q` → 315 passed, 2 skipped (needs-data skips in a clean checkout:
the H60 artifact tests plus the H50 artifact tests). Ruff clean on `src/`, `scripts/`, `tests/`.
