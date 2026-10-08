# Next-session handoff — written 2026-10-08 after the H65–H68 round

**Read the standing brief in `README.md` first** (including the session-6 directive). Status in
one line: **H60 is published, preregistered, gate-passed and remains the file to submit; H68 is the
new unique validated candidate (valid submission, not the recommendation); H65 is the round's best
science, published as a research artifact that is NOT OK to submit while the uniqueness bar stands;
no slot has been spent.**

## What happened this round (all committed; `evidence/h65/`, `docs/data/h65-*.json`,
`docs/data/h68-artifact.json`, `docs/data/h33-reference-analysis.json`)

1. The slate **H65–H68** was preregistered and committed **before** any score:
   `docs/research/h65-hypotheses-preregistered.md` (consensus, far-field, lidar+Th/K alteration,
   eight-channel; ranked by expected DTI improvement × cost; six-condition gate).
2. `scripts/analyze_h33_reference.py` measured the owner-reported d2.8 reference
   (`evidence/h33_reference_analysis.json`): **h33-2-b2 is the scored d2.8 emission pruned
   44,090 → 37,654 dots** (strict mask subset, Jaccard 0.854), 59.6 % of its dots inside the
   road/claim noise masks, and the 0.2600 → 0.2778 move is the DTI pruning algebra — mass
   discipline on an existing field, not a new signal. The re-pruning route is closed by the
   uniqueness gate.
3. `scripts/run_h65_screen.py` ran the frozen 41-block screen (blocks byte-equal to
   `evidence/h50/blocks.json`; anchors reproduced bit-for-bit) with this round's methodological
   change: **the operating point is the argmax of the certified split-conformal lower bound**
   (`gems47.conformal.choose_operating_point`), not the observed selection-half maximum.
4. Results (selection half, pooled DTI; certified floor at the chosen spacing):
   **H65 0.2919 / 0.1984 (floor 0.0976 @ 2.0 px) — the only arm beating the H60 incumbent
   (0.2879 / 0.1938) on BOTH instruments**; H68 0.2783 / 0.2145 (floor 0.0993 @ 2.8 px, frozen
   winner by the SGMC tie-break); H66 0.2772 / 0.2025; H67 0.2069 / 0.1929 (best floor 0.1045).
   All four passed the four control conditions. No arm was refuted this round.
5. **Implementation bug caught and fixed before publication (IR-2026-10-08-D):** the H65
   lexicographic rank initially assigned the largest value to the lowest-priority cell, so the
   first screen run measured the inverted field (H65 0.0157, recorded as refuted). A test
   (`tests/test_h65.py::test_lexicographic_rank_is_tie_free_and_in_unit_interval`) failed before
   any artifact was built; the helper was fixed and the screen re-run. Full record with both
   runs' numbers: `evidence/h65/erratum-consensus-rank-20261008.md`.
6. `scripts/build_submission_h65.py` built and published **two** artifacts (17/17 read-back
   checks each, NaN-outside fallbacks, ZIPs, notes, receipts):
   * **H68** `gems47-h68-lidar-8ch-s2p8-20261008-allfinite.tif` — SHA-256
     `a0e82ce0e2f8cfa11b9759d47ec36ec259923d8137b0057a557e4701d245c50c`, 307,486 bytes,
     37,654 dots at 2.8 px, unique (0 exact matches, max Jaccard 0.3066; 0.0082 vs scored
     priors) — **validated candidate, NOT the recommendation** (does not beat H60 on the
     primary instrument). Portal note `h68 lidar 8-channel d2p8 conformal90`.
   * **H65** `gems47-h65-scarpconsensus-s2p0-20261008-allfinite.tif` — SHA-256
     `cbae340361811abb7e7f6d0a1712d9adad087562c24479cb98439d5561225a17`, 298,948 bytes,
     37,654 dots at 2.0 px — **research artifact, NOT OK TO SUBMIT**: it beat H60 on both
     instruments (conditions 1–5) but its emission overlaps the H60 incumbent artifact at mask
     Jaccard **0.5119 ≥ 0.5**, failing frozen condition 6. Unique against every scored prior
     submission (max 0.0067). IR-2026-10-08-E.
7. `scripts/update_site_h65.py` (idempotent, asserted replacements) moved the site: H60 panel
   unchanged as PRIMARY; H68 panel added (OK to download, valid submission, not the
   recommendation); H65 notice added (NOT OK TO SUBMIT while the uniqueness bar stands, with the
   TIF link and the numbers); register rows; five irregularity entries IR-2026-10-08-A…E.
   `scripts/build_h65_page.py` rendered `docs/h65.html` from the receipts (no hand-typed
   numbers).
8. Every artifact note reports the conformal guarantee next to the chosen spacing: max-residual
   rank 20 of 22 (k = ceil(22 × 0.90)), **finite-sample coverage at least 90.91 % (confidence
   level 90.91 %)**, certified holdout floor, conditional on block exchangeability.

## Priority order for the next session

1. **Decide the slot question with the owner.** H60 remains the recommendation (it passed all six
   frozen conditions in its round). H68 is a valid, unique alternative if the owner accepts the
   primary-instrument trade-off. H65 is the strongest science but is blocked by the frozen
   uniqueness bar — do **not** amend that bar after the scores (H49 failure mode); if the owner
   wants H65 submitted, that is an explicit, recorded owner decision overriding a self-imposed
   discipline, not a silent rule change.
2. **Uniqueness-bar-compliant H65 variant (highest scientific value, no slot needed).** The
   0.5119 overlap with H60 comes from emitting the same budget at the same spacing over the same
   domain with correlated fields. A preregistered variant that keeps the consensus field but
   changes a *frozen-by-preregistration* degree of freedom (e.g. a different budget, a different
   emission domain restriction, or a consensus-amplitude hybrid tie-break) could clear the bar;
   it must be preregistered and re-screened before any artifact is built.
3. **Independent-instrument program.** The primary instrument shares the lidar modality with
   every lidar-reading field; H67's Th/K component is independent of it. Candidates, all
   free/official and already restored or named: the GeoDAWN Th/K + U/K grids (in hand), USGS
   MRData ASTER alteration (not fetchable here), NBMG Map 167 / QFaults (already inside the
   training labels — closed), SGMC at finer thresholds.
4. **Spacing below 2.0 px (preregister first).** H65's selection-half mean is still rising at the
   sweep edge (0.2876 at 2.0). Extend the sweep with the conformal guarantee made simultaneous
   over the extended set; watch block capacity and record under-emission.
5. **Mask-radius ablation (preregister first).** The 250 m road / 150 m claim radii were frozen
   pre-score and never swept; a 3×3 radius grid is one screen.
6. **H67 follow-up.** The alteration arm kept the best certified floor of the round (0.1045) but
   diluted the primary instrument; a λ sweep (0.25/0.5/0.75) or a Th/K-only ablation is one
   screen and would isolate whether the radiometric component carries signal.

## Known traps (do not rediscover)

- `.cache/gems_data` is NOT persisted across sandboxes: `python3 scripts/restore_data.py
  --group all` first (hash-pinned mirrors, ~523 MB, ALL_VERIFIED). System python3 has numpy /
  rasterio / scipy / scikit-learn installed via `pip install --break-system-packages`.
- `greedy_spaced_pixels` raises when a restricted domain cannot hold the budget at a spacing —
  use `h60._greedy_up_to` (binary-search cap) and report the actual emitted mass.
- `h65._lexicographic_rank` assigns the LARGEST value to the HIGHEST-priority cell (fixed
  2026-10-08; the first version was inverted — see the erratum). The test pins the direction.
- The uniqueness audit excludes the artifact's own stems; `max_jaccard_vs_scored_priors` is
  reported separately from `max_jaccard` (the latter includes this repo's published artifacts).
- `scripts/update_site_h65.py` is idempotent (re-runs are no-ops); every replacement asserts it
  matched. The legacy site renderer is retired.
- DrivenData queries remain prohibited (Terms); the leaderboard snapshot stays dated 2026-10-06.
- Every conformal floor is assumption-conditional on block exchangeability and covers one future
  exchangeable block's proxy DTI — never the private leaderboard. Never call it a
  distribution-free guarantee for private labels.
- The primary instrument derives from the same owner-built lidar stack the lidar fields read —
  necessary, never sufficient; the SGMC off-catalogue population is the independent floor, and
  its DTI is negatively rank-correlated with the owner-reported scores (tie-break tension,
  IR-2026-10-08-B).

## Test and lint state at handoff

`PYTHONPATH=src python3 -m pytest tests -q` → 329 passed, 2 skipped (needs-data skips in a
clean checkout). `python3 -m unittest discover -s tests` → 93 passed (site integrity).
`python3 -m ruff check` clean on every file touched this round (the 64 remaining repo-wide
errors are pre-existing legacy files).
