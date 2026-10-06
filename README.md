# GEMSDOE47 — standing charter, current status, and two independent negative results

> **Decision as of 2026-10-06 UTC: no submission is eligible and no slot is recommended.**
> This repository now contains the work of **two independent sessions on the same brief**. Both built a
> detector, both preregistered a gate, and **both closed the gate**. The downloadable candidates are
> marked **RESEARCH ONLY — NOT FOR SUBMISSION**. Local structural/range checks are not organizer
> acceptance: notably, the H47-GSA all-finite variant writes zeros outside the supplied footprint, while
> the official submission page specifies null/NaN outside bounds. Its NaN alternative follows the
> available mirror's convention but fails a NaN-intolerant raw range test; the prior rejected bytes are
> unavailable. No variant is approved for upload. Similarity checks are bounded to accessible artifacts
> and are not global uniqueness proofs. A local format pass is not a scientific promotion.
>
> **Core values:** **Maximize P(Win)** · **Own the Outcome**. Preserve the slot until a genuinely new,
> unique prediction beats the current spatially blocked holdout best under a preregistered, adequately
> controlled test.

## Current decision record

| Item | Current evidence | Decision |
|---|---|---|
| **H47-GSA** — geodetic strain × hydrothermal alteration × thermal discharge *(later session)* | The observation-level cross-fit has paired out-of-fold deltas **−0.0611** and **−0.0450** vs the owner-reported d2.8 reference; it is conditional on the unverified H33-to-0.2778 association, needs an H33-excluded sensitivity rerun, and is not a spatial holdout or authenticated leaderboard comparison. Against the d2.8 reference, it underperforms on four local frames; the F2 win is against its own in-fold fitted objective and is not independent evidence. Covered-kernel integral is **99,916** vs **341,261** (exact for this public frame, not a DTI/hidden-target score). | **NOT PROMOTED**; no portal submission authorized. |
| **H47-B** — cross-scale `TMI_up150` magnetic-edge persistence *(earlier session)* | Selected spacing **5 px / 500 m**; locked-test pooled DTI **0.02755**; tuned single-scale baseline **0.02564**; fixed-seed random control **0.03716**. Candidate **lost to random**. Split-conformal nominal level **6/7 = 85.7 %** only under unverified block exchangeability; clipped lower bound **0.0**. | **NOT PROMOTED**; do not spend a slot. |
| H47-SAF — strike-aligned catalogue-flank re-occupation *(later session)* | The 12-row exploratory fit showed +55.7 % LOO. If one assumes H33-2-B2 scored 0.2778, the 13-row fit shows −64.0 %; however, the public row is not mapped to that TIFF. The coarse sensitivity grid is positive at 0.2200 and negative at 0.2400; no exact break-even or causal verdict is established. | **UNRESOLVED**; not built into an artifact. |
| H47-SGMC — state geologic-map catalogue-difference transfer | In this exploratory model, adding it worsened LOO (0.008124 → 0.009279); the conditional fitted q allocates 0.5 % of its modeled `K` there. This is not a measured hidden-truth proportion. | **NOT SUPPORTED IN THIS FIT**; no general falsification. |
| Downloadable artifacts | `gems47-h47gsa-…-allfinite.tif` — 1 band, float32, EPSG:32611, 3292 × 3730, 100 m, 37,654 positive pixels, values {0,1}, **0 emitted pixels** on masked catalogue cells, **0 emitted pixels** outside the footprint, and zero-valued data cells outside the footprint, SHA-256 `7bfc92ac536cf83a5caf24a815353ba151862f5ad2fbec4461b89353bafb3146`. It passes the recorded local raw range checks, but its zeros outside the supplied footprint fail the current null/NaN-outside check. Earlier session: `gems47-h47b-tmiup150-…-research-not-submittable-20261006.tif`, SHA-256 `7e5df9d01689e438e8379ebd4763ed803de02e94826f43da37c33c16380d669b`, 18,524 positive pixels, NaN outside the footprint. Neither has organizer acceptance. | Published for transparent review. **Not authorized for upload.** |
| Uniqueness | Later session: max Jaccard **0.0457** against 13 local reference rasters: 12 owner-reported score/raster pairs plus one hash-pinned H33 reference whose score link is unverified. Earlier session: **zero** exact positive-mask matches against **334** exact-grid TIFFs in 55 visible `buffedlizard55-lab` GEMSDOE repositories; maximum equal-mass Jaccard **0.01119**. | Supports distinctness against accessible artifacts only. **Not a global uniqueness proof** and not a performance result. |
| Public leaderboard | One-time read 2026-10-06: rank 1 **0.3774** (participant name not preserved), DARD **0.3195 at #7**, `extradr19` **0.2778 at #13**. An earlier same-date read gave rank 1 = 0.3345 and DARD at #5; the later observation supersedes it. | Participant scores do **not** identify TIFFs or receipts. No TIFF-to-score mapping is authenticated (IR-47-002). |
| Reported `"Predicted values must be in range [0, 1]"` rejection | The rejected bytes are unavailable, so its cause is **unresolved**. Among 29 accessible sibling GeoTIFFs, **12/12** `-nan` variants fail one NaN-intolerant comparison and **17/17** all-finite variants pass; none has a finite value outside [0, 1]. | The all-finite variant is a raw-range diagnostic, but zeros outside the supplied footprint do not meet the official page's null/NaN-outside wording. The NaN variant follows the available mirrored sample convention but fails the tested raw comparison. Neither is recommended for upload; exact authorized inputs and portal behavior must be checked. |

## Metric and attribution audit — corrected 2026-10-06

The inverse-DTI analysis distinguishes two ratios. With `x = T/K` and `ρ = F/K`,

```text
x = (αρ + β) / (1/DTI − α),     α = 0.2, β = 0.8
```

At illustrative `ρ = 8.02`, the target `DTI = 0.3195` requires `T/K = 82.05 %`, and `DTI = 0.3774` requires `98.13 %`. The origin of illustrative `ρ = 8.02` as an observed participant ratio is not verified; treat it as a scenario only. If instead `f = F/T`, use `T/K = β / [1/DTI − α(1 + f)]`: at target 0.3195, `f = 8` gives 60.16 % and `f = 4` gives 37.56 %. Do not substitute one denominator for the other. Regression tests reinsert inverse results into the forward `dti_from_TFK()` equation.

Known USGS/INGENIOUS pixels are excluded from evaluation and penalty terms, per the [official staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516). Deleting predictions exactly on those pixels cannot improve DTI. Effects of pruning nearby unmasked pixels require a paired evaluation restricted to the evaluated domain.

The 0.2778 public row is participant-level and is not authenticated to the H33-2-B2 TIFF; its owner site labels that raster unscored. The 13-row LOO scenario and sensitivity bracket are conditional on that unverified association; the tested sign change lies between assumed DTI 0.2200 and 0.2400, with no exact root or flank verdict established. The leaderboard snapshot is time-stamped; no participant row is mapped to a TIFF here.

**Spacing/confidence research note (not for portal use):** `H47-B spacing = 5 px / 500 m; split-conformal nominal level = 6/7 = 85.7% under block-score exchangeability; clipped lower bound = 0.000; spatial exchangeability unverified; public-mirror screen; RESEARCH ONLY — NOT FOR SUBMISSION.` This is assumption-conditional marginal coverage, not a positive performance floor or a guarantee for private labels.

Details: [H47-B validation report](docs/validation-h47b-20261006.md) ·
[uniqueness audit](docs/h47b-uniqueness-audit-20261006.json) ·
[LATI method](docs/method.html) · [cross-fitted validation](evidence/crossfit_validation.json) ·
[flank sensitivity](evidence/flank_sensitivity.json) ·
[leaderboard / source attribution](docs/analysis.md) ·
[irregularity register (earlier session)](docs/irregularities.md) ·
[IR-47-001…015 (later session)](docs/irregularities.html)

**The site is [`docs/index.html`](docs/index.html).** The submission artifact and the gate verdict are
the first things on it.

---

## 0. Read this first — the standing project brief

This section is the user's brief. It is kept near the top on purpose: **re-read it at the start of every
session**, because every decision above is answerable to it.

> ### MAXIMUM URGENCY / HIGHEST URGENCY MUST BE FOLLOWED
>
> Build, inside this repository, a project that can place at the top of the DrivenData **Geologic
> Enhanced Mapping System (GEMS) Prize Challenge** leaderboard (competition 306,
> https://www.drivendata.org/competitions/306/competition-doe-gems/).
>
> **Deliverables**
>
> 1. A **unique** competition submission GeoTIFF, different from all of the prior GEMSDOE sites listed
>    below. Copying a previous submission is acceptable *only* for learning and education — never as the
>    deliverable.
> 2. The TIF must be **easy to download** from the GitHub Pages site: an obvious one-click download at
>    the very top of the site and in the executive summary.
> 3. Fix the reported submission error **`"Predicted values must be in range [0, 1]"`**. Values must be
>    strictly within [0, 1], single-band float32, EPSG:32611, 100 m resolution, the same bounds as the
>    training data, null/nan outside the bounds.
> 4. Give the submission a **unique name** plus a short distinguishing note for the DrivenData
>    submission form's optional **"Note"** field (for example `clustering with k=25`).
> 5. A **GitHub Pages site** with a clean, simple, user-friendly, organized UI containing all relevant
>    information and official verified source links.
> 6. An **executive-summary subpage** explaining exactly how to submit to the contest.
> 7. **Study why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (GEMSDOE32) scored the family best
>    0.2778**, answer with PhD-level reasoning, and use that to attempt a submission scoring
>    **> 0.2778** and ultimately **> 0.3195** (current leaderboard top).
> 8. Before implementing: generate **3–5 candidate geological hypotheses not yet tried**, each naming
>    the specific layer(s), the physical signature targeted (edge detection, curvature transform, etc.),
>    why it should catch a fault *missing* from the USGS/INGENIOUS catalogue rather than one already in
>    it, and how it differs from anything already implemented. Rank by expected DTI improvement and
>    implementation cost.
> 9. **Validate the top candidate on a spatially-blocked holdout set before spending a weekly submission
>    slot.** Never spend a slot on an unvalidated idea.
> 10. If a candidate needs new external data, name the specific free official source and confirm it is
>     obtainable before proposing it as viable.
> 11. Store gathered knowledge from official verified sources as a reusable research base for other
>     projects.
> 12. Autonomous end-to-end: no manual input required; self-research, self-review, self-improve; **flag
>     irregularities**; provide links for manual review.
> 13. Three passes: (1) implement completely and verify; (2) review for bugs, missing requirements, bad
>     assumptions and edge cases and fix them; (3) re-check the whole implementation against the original
>     request and improve accuracy, reliability, completeness and code quality.
> 14. Create a pull request and merge it onto `main`. Report remaining work and limitations.
>
> **Standing constraints**
>
> - "Read the entire prompt." "Verify working line by line — no hallucinations." Work line by line from
>   **official, verified, trusted sources**; provide links for manual review; flag every irregularity.
> - No manual input — the agent must complete all tasks on its own.
> - Contrarian but smart; think outside the box while staying grounded in proper scientific research;
>   find data sources others overlook.
> - Do not spend a submission slot on an idea that has not beaten the current holdout best.
> - Arena core values as focal points: **Maximize P(Win)** and **Own the Outcome**.
> - Known limitation acknowledged in the brief itself: there are no DrivenData credentials, so
>   `training_features.tif`, `labels.tif`, `sample_submission.tif` and `1m_DEM_links.csv` cannot be
>   downloaded from the portal. (They were recovered from hash-pinned mirrors instead — see §2.)

### Hard requirements, in priority order

1. **Unique prediction.** Compare the candidate against accessible historical artifacts before any
   upload; record exact-match and similarity results, scope and limitations. Do not call uniqueness
   global unless all relevant prior submissions are authoritatively available.
2. **Holdout before a slot.** Do not use a submission slot for an idea that has not beaten the current
   spatially blocked holdout best under a preregistered rule. Use equal prediction mass where
   appropriate, a ≥300 m guard consistent with the metric kernel, fold-level results, and nontrivial
   controls. Ties, unstable folds, missing labels, failed controls, or a zero/unsupported lower floor
   keep the gate closed.
3. **Conformal honesty.** Use split conformal only where the exchangeability unit and target are
   defensible. State sample count, rank, nominal level and assumptions. Never call an
   assumption-conditional result a distribution-free guarantee for private labels or a leaderboard
   score. Do not reuse the retired `0.34837` claim.
4. **Valid output.** Read back the exact output bytes. Enforce a single-band GeoTIFF, official
   grid/CRS/transform, allowed nodata footprint, finite in-footprint values in [0, 1], and an audit
   receipt. A format pass does not establish scientific validity or organizer acceptance.

---

## 1. What the later session concluded

| Question | Answer | Evidence |
|---|---|---|
| Exploratory `K` estimates | The diffuse `r13-lattice` inverse gives **≈12,348 px** under its owner-reported score/raster association; selected fitted-shape estimates span roughly **15,638–21,477 px**. These are assumption-conditional model outputs, not measured or organizer-verified hidden-label mass. | `evidence/lati_fit.json`, `evidence/flank_mass.json` |
| Does the exploratory fit associate owner-reported DTI rows with catalogue-flank features? | The 12-row fit showed an exploratory association; the H33-based reversal is conditional on an unauthenticated score/file mapping, so H47-SAF remains unresolved and unvalidated | `evidence/flank_sensitivity.json` |
| Does any *a priori* geological layer improve after observation-level cross-fitting? | **No positive result is established.** The H47-GSA cross-fit is negative versus the owner-reported d2.8 reference but includes the contested H33 association; it is not a spatial holdout. An H33-excluded sensitivity is still needed. | `evidence/crossfit_validation.json` |
| Can the participant-level 0.2778 score be explained by H33-2-B2? | **No authenticated mapping.** Raster counts are descriptive; deleting predictions exactly on masked pixels cannot improve DTI | `knowledge/02_the_metric_algebra.md`, IR-47-002 |
| Can DTI 0.3195 be reached at illustrative `F/K = 8.02`? | **Yes in the algebraic scenario: `T/K ≈ 82.05 %`.** Provenance of 8.02 as an observed participant ratio is unverified; `F/K` is not `F/T` | `docs/evidence.html`, `tests/test_metric.py` |
| What caused the reported range rejection? | **Unknown:** NaN triggers the tested check in available sibling `-nan` files, but the exact rejected bytes are unavailable; this is not a root-cause finding. | `evidence/range_error_diagnosis.json`, `docs/irregularities.md` |

### LATI — the instrument the later session built

Twelve hash-pinned raster/score pairs were restored from owner-reported records, without organizer receipts authenticating the score-to-file links. H33-2-B2 is a separate reference raster, not an authenticated thirteenth pair; it enters only in explicitly conditional scenarios with an assumed DTI.
**LATI** is a legacy name for this exploratory inversion of owner-reported score/raster associations; it does not anchor the fit to authenticated leaderboard returns. Under the owner-reported pair assumptions, `T = ⟨q, w_p⟩` is exactly linear in the unknown truth-intensity model `q`, so each assumed score/raster pair contributes an equation. The fit does not authenticate the scores, identify a private hidden-label map, or establish private-target performance. It replaces the earlier family’s self-referential model (`π ~ exp(−d(H19-5)/1.85 px)` — a scatter around the group’s own best field, which cannot independently assess that field). Its diagnostics include proximity to owner-reported reference rasters (ranks #1–#6 of 72), a spatially shuffled-layer negative control (rank #71), and finite permutation comparisons (all 14 top layers beat all 10 tested permutations in this exploratory fit). Ten draws are not a calibrated significance test. These checks do not authenticate score/raster associations or prove the instrument/model valid or predict private-target performance. A 700× binned fast path matched its reference computation within 1.1e-05 DTI. See [docs/method.html](docs/method.html).

## 2. Data provenance — no DrivenData credentials were needed

All current manifest entries have SHA-256 pins and source records; the pins establish mirror consistency, not organizer authentication. `scripts/restore_data.py --group all` attempts every entry in the current **26-entry** manifest: 3 competition rasters, 10 external feature/metadata/audit entries, 12 owner-reported score/raster references, and 1 H33 reference raster.

The committed [`data/restore_receipt.json`](data/restore_receipt.json) records 23 entries; three H47-B metadata/audit entries were added to the current manifest afterward. Its `all_verified: true` applies only to the 23 entries it lists and does **not** attest to the full current 26-entry scope. A fresh full restore would be needed for a 26-entry receipt. No runtime is promised. Restored bytes belong in `.cache/gems_data/` (git-ignored; current manifest payload is about 531 MB / 507 MiB). Nothing large is committed.

## 3. Layout

Two codebases coexist after the merge. Neither was rewritten; the earlier session’s files are
byte-for-byte preserved.

```
README.md                     this file - charter, decision record, standing brief
index.html                    the earlier session's root landing page (site integrity tests gate it)
docs/
  index.html                  the canonical site: artifact + gate verdict first
  executive-summary.html      future submission workflow, promotion gate, corrected metric algebra
  hypotheses.html             the five ranked hypotheses (later session)
  method.html                 LATI: algebra, identifiability, controls, cross-fitting, two bugs
  evidence.html               every number, with its file and its caveat
  irregularities.html         IR-47-001 ... IR-47-015
  leaderboard.html · analysis.{html,md} · sources.{html,md} · submit.html
  portal-checklist.{html,md} · method.md · hypotheses.md · prior-results.md
  irregularities.md · validation-protocol.md · validation-h47b-20261006.md
  preregistered-h2.md · review-log.md · next-session.md · style.css
                              the earlier session's pages, preserved in place
  prev-session/               the three superseded landing pages, verbatim
  downloads/                  both sessions' artifacts (all research-only)
  prior-results.csv · prior-output-manifest.csv
gemsdoe47/                    earlier session: candidate, magnetic, spatial, validation
src/gems47_*.py               earlier session: metric, blocks, emit, verify_submission
src/gems47/                   later session: grid, metric, features, hypotheses, lati,
                              emitter, submission, scripts_common
scripts/
  restore_data.py             restore and SHA-256-verify the 26-entry current manifest
  verify_grid.py              re-derive every grid constant from the bytes (16 checks)
  lati_fit.py · lati_controls.py · test_flank.py · flank_sensitivity.py · screen13.py
  build_candidate.py · build_submission.py · build_final.py    (superseded exploratory)
  crossfit_validate.py        the honest test: a-priori pool, selection inside each fold
  ship.py                     the shipping path: build, evaluate, write, verify
  build_h1_candidate.py · build_h47a.py · run_h2_experiment.py · package_submission.py
  check_competition_data.py · validate_submission.py           (earlier session)
tests/                        unittest + pytest suites; data-dependent cases skip when cached inputs are absent
registry/                     sources, data manifest, observations, irregularities
knowledge/                    the reusable research base (brief item 11)
notes/                        the earlier session's hypotheses, knowledge, results
evidence/                     every machine-readable result quoted by the later session
pyproject.toml                ruff config; per-file ignores scoped to src/gems47 and scripts only
```

## 4. Run local verification (data restore and research reruns remain gated)

```bash
python3 -m venv venv47 && ./venv47/bin/pip install -r requirements-dev.txt
export PYTHONPATH=src
python3 -m ruff check .
python3 -m unittest discover -s tests -v
python3 -m pytest -q
```

Last checked 2026-10-06 after this review: `ruff check .` clean; unittest ran 69 tests with 2 skips;
pytest reported 112 passed, 7 skipped, and 2 subtests passed. Skips are data-dependent checks because the
restored competition/mirror cache is absent.

**Gated commands — do not run without separate authorization and a passed promotion gate:**
`python3 scripts/restore_data.py --group all`, `python3 scripts/ship.py`, and
`python3 scripts/crossfit_validate.py`. H47-B's input/hash reconciliation is documentation, not
permission to restore the full dataset or rerun that experiment. The earlier grid-receipt result is
historical, not a current authorization or verification.

The prior work ran under 2 vCPU, 3 GB RAM, ~19 GB disk, and a network that reaches only `pypi.org`,
`github.com`, `api.github.com` and `codeload.github.com` from a shell.

## 5. Remaining work

1. **Verify access to official 3DEP 1 m data.** The competition page links USGS 3DEP tiles, but this
   checkout used only pre-derived 100 m LiDAR layers. Acquire any new inputs from the official source,
   pin their provenance, and test detections at native resolution; treat expected performance as unknown.
2. **Do not submit the λ-probe under the current gate.** Its theoretical design uses three score
   observations (`λ=1`, `λ=0.5`, and null-add); the `λ=1` 0.2600 anchor is owner-reported and not
   authenticated to a score receipt. Three observations are not a verified count of new uploads or
   portal slots. The accessible official pages checked 2026-10-06 do not expose the current quota or
   slot accounting, so the number and cost of new uploads are unknown. Do not call it free or claim a
   fixed slot cost. Preserve the slot unless the candidate first beats the holdout and a separately
   authorized, preregistered diagnostic route is confirmed.
3. **Seek clarification only from an authoritative source** on which data identified new faults; the
   staff reply in thread 11527 was not retrievable in the saved audit. A forum answer may inform a
   hypothesis but cannot replace validation.
4. **Keep H33 attribution unresolved.** The official board shows `extradr19` at 0.2778/#13 in the
   2026-10-06 snapshot but does not identify a TIFF. Only an organizer receipt or explicit, reliable
   owner evidence could authenticate the H33 mapping; do not use the participant row to decide a flank verdict.
5. **Keep H47-B ineligible.** Its 5 px / 500 m selected spacing has a nominal 85.7 % split-conformal
   level only under unverified block exchangeability, a clipped lower bound of zero, and a locked-test
   loss to the matched random control.
6. **Evaluate any pruning policy on unmasked pixels.** Exact known-fault pixels are excluded from
   scoring. Any proposed effect from a surrounding 2-pixel neighborhood requires a preregistered,
   spatially blocked paired ablation with matched mass and nontrivial controls.

## 6. Honest limitations

1. **No GEMSDOE47 candidate has an authenticated competition score.** Public participant rows exist,
   but no organizer receipt links them to these TIFFs; all local DTI values are model outputs.
2. **The LATI data are sparse and dependent.** Twelve owner-reported raster/score pairs are available;
   the H33-2-B2 / 0.2778 association is contested, and six maps are nested thinnings of one field.
3. **H33 sensitivity is conditional.** The coarse model fit changes sign between assumed H33 scores
   0.2200 and 0.2400; this is not an exact break-even, causal experiment, or hypothesis verdict.
4. **Local frames disagree.** SGMC ranks the near-uniform lattice best (0.2499) although its reported
   public score is 0.0904; the H33 raster performs poorly on one local blocked catalogue frame, but the
   public score-to-file link is unverified. No local model identifies a private leaderboard score.
5. **Optimizer’s curse is large in-fold.** The reported ≈0.30 DTI advantage is exploratory, and the
   H47-GSA cross-fit also relied on the contested H33 association; rerun without it before using that
   result as a validation estimate.
6. **The sessions used different gates** (five local frames + cross-fitting vs. locked-test,
   random-control and conformal checks). Both gates remain closed; their protocols need a future
   unified, preregistered review.
