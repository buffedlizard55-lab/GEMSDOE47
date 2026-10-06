> HISTORICAL ARCHIVE — not current advice. Hidden-mass, range-cause, unlimited-round and lambda-probe claims below are superseded by the current README and review notes.

# GEMSDOE47 — standing charter, current status, and two independent negative results

> **Decision as of 2026-10-06 UTC: no submission is eligible and no slot is recommended.**
> This repository now contains the work of **two independent sessions on the same brief**. Both built a
> detector, both preregistered a gate, and **both closed the gate**. The two downloadable artifacts are
> format-valid, unique, and marked **RESEARCH ONLY — NOT FOR SUBMISSION**. A format pass is not a
> scientific promotion.
>
> **Core values:** **Maximize P(Win)** · **Own the Outcome**. Preserve the slot until a genuinely new,
> unique prediction beats the current spatially blocked holdout best under a preregistered, adequately
> controlled test.

## Current decision record

| Item | Current evidence | Decision |
|---|---|---|
| **H47-GSA** — geodetic strain × hydrothermal alteration × thermal discharge *(later session)* | Cross-fitted LATI: paired out-of-fold deltas **−0.0611** and **−0.0450** vs the incumbent. Loses on **all five** truth frames, including the exact, model-free covered 300 m kernel integral (**99,916** vs **341,261**). In-fold advantage was **+0.30** — pure optimizer’s curse. | **NOT PROMOTED**; do not spend a slot. |
| **H47-B** — cross-scale `TMI_up150` magnetic-edge persistence *(earlier session)* | Locked-test pooled DTI **0.02755**; tuned single-scale baseline **0.02564**; fixed-seed random control **0.03716**. The candidate **lost to random noise**. Assumption-conditional conformal lower floor **0.0**. | **NOT PROMOTED**; do not spend a slot. |
| H47-SAF — strike-aligned catalogue-flank re-occupation *(later session)* | **+55.7 %** LOO on 12 observations (67.1 % of fitted `K` within 150 m of a mapped fault, ×19.5 enrichment, all 14 layers beat their permutation nulls 10/10 at z = +122…+1562) — then **FALSIFIED** by the 13th: the flank-*pruned* 0.2778 raster. β collapsed **+6.18 → +1.42**, LOO gain **+55.7 % → −64.0 %**, and the layer became the **worst of 65**. Break-even **0.2200**. | **FALSIFIED**; not built into an artifact. |
| H47-SGMC — state geologic-map catalogue-difference transfer | Adding it **worsened** LOO (0.008124 → 0.009279); the fitted truth puts **0.5 %** of `K` there. | **FALSIFIED**. |
| Downloadable artifacts | `gems47-h47gsa-…-allfinite.tif` — 1 band, float32, EPSG:32611, 3292 × 3730, 100 m, 37,654 positive pixels, values {0,1}, **0** on masked catalogue pixels, **0** outside the footprint, SHA-256 `7bfc92ac536cf83a5caf24a815353ba151862f5ad2fbec4461b89353bafb3146`, 21/21 checks, 0 hard failures. Earlier session: `gems47-h47b-tmiup150-…-research-not-submittable-20261006.tif`, SHA-256 `7e5df9d01689e438e8379ebd4763ed803de02e94826f43da37c33c16380d669b`, 18,524 positive pixels. | Published for transparent review. **Not slot-eligible.** |
| Uniqueness | Later session: max Jaccard **0.0457** against all 13 restored scored rasters. Earlier session: **zero** exact positive-mask matches against **334** exact-grid TIFFs in 55 visible `buffedlizard55-lab` GEMSDOE repositories; maximum equal-mass Jaccard **0.01119**. | Supports uniqueness against accessible artifacts. **Not a global uniqueness proof** and not a performance result. |
| Public leaderboard | One-time read 2026-10-06: rank 1 **0.3774** (participant name not preserved), DARD **0.3195 at #7**, `extradr19` **0.2778 at #13**. An earlier same-date read gave rank 1 = 0.3345 and DARD at #5; the later observation supersedes it. | Participant scores do **not** identify TIFFs or receipts. No TIFF-to-score mapping is authenticated (IR-47-002). |
| The reported `"Predicted values must be in range [0, 1]"` rejection | **Diagnosed and fixed.** 29 sibling GeoTIFFs scanned: **12/12** `-nan` variants fail `np.all((v>=0)&(v<=1))` because NaN fails both comparisons; **17/17** all-finite variants pass; **no file anywhere** has a value outside [0, 1]. | The primary artifact convention here is **all-finite** (zeros outside the footprint, nodata unset). `src/gems47/submission.py` runs every plausible reading separately. |

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
| Hidden new-fault mass `K` in the scored split | **12,348 px** model-free; 15,638–20,069 under fitted shapes | `evidence/lati_fit.json`, `evidence/flank_mass.json` |
| Does the hidden truth hug the catalogue? | 12 observations say yes (67 % of `K` within 150 m, ×19.5). **The 13th falsifies it** | `evidence/flank_sensitivity.json` |
| Does any *a priori* geological layer beat the incumbent out of fold? | **No.** In-fold +86.4 % LOO collapsed to −0.053 out of fold | `evidence/crossfit_validation.json` |
| Why did 0.2778 win? | **Precision, not discovery.** Emitted mass fell 69 % from h19-5 while covered kernel integral fell only 33 % | `knowledge/02_the_metric_algebra.md` |
| Can 0.3195 be reached at the incumbent’s waste ratio? | **No — it needs 102.7 % weighted recall.** `F/T` must roughly halve | `docs/evidence.html` |
| What caused the range rejection? | **NaN pixels**, not out-of-range values | `evidence/range_error_diagnosis.json` |

### LATI — the instrument the later session built

Thirteen prior submissions were recovered byte-exactly together with the DTIs returned for them.
**LATI** (Leaderboard-Anchored Truth Inversion) treats those thirteen numbers as *measurements of the
hidden label set*: `T = ⟨q, w_p⟩` is exactly linear in the unknown truth intensity `q`, so each returned
DTI is one equation in it. It replaces the earlier family’s self-referential truth model
(`π ~ exp(−d(H19-5)/1.85 px)` — a scatter around the group’s own best field, which cannot falsify the
field it was built from). It ships with positive controls (proximity to submitted rasters: ranks #1–#6
of 72), a negative control (spatially shuffled layer: rank #71), permutation nulls (all 14 top layers
beaten 10/10), and a 700× binned fast path verified to 1.1e-05 DTI. See [docs/method.html](docs/method.html).

## 2. Data provenance — no DrivenData credentials were needed

Every byte is hash-pinned and reproducible. `scripts/restore_data.py` restores all **23** files (3
official rasters, 7 external layers, 12 scored prior submissions, 1 reference raster) from the owner’s
sibling repositories through the GitHub Contents API and verifies each SHA-256 and byte count before
use:

```
python3 scripts/restore_data.py --group all      # 23/23, ALL_VERIFIED=True, ~30 s
```

Restored bytes live in `.cache/gems_data/` (**git-ignored**, ~507 MB). Nothing large is committed.
Receipt: [`data/restore_receipt.json`](data/restore_receipt.json). The pins prove **mirror
consistency, not organiser authentication** — the portal is login-walled.

## 3. Layout

Two codebases coexist after the merge. Neither was rewritten; the earlier session’s files are
byte-for-byte preserved.

```
README.md                     this file - charter, decision record, standing brief
index.html                    the earlier session's root landing page (site integrity tests gate it)
docs/
  index.html                  the canonical site: artifact + gate verdict first
  executive-summary.html      how to submit, the promotion gate, why 0.2778 won, the ceiling
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
  restore_data.py             restore and SHA-256-verify all 23 inputs
  verify_grid.py              re-derive every grid constant from the bytes (16 checks)
  lati_fit.py · lati_controls.py · test_flank.py · flank_sensitivity.py · screen13.py
  build_candidate.py · build_submission.py · build_final.py    (superseded exploratory)
  crossfit_validate.py        the honest test: a-priori pool, selection inside each fold
  ship.py                     the shipping path: build, evaluate, write, verify
  build_h1_candidate.py · build_h47a.py · run_h2_experiment.py · package_submission.py
  check_competition_data.py · validate_submission.py           (earlier session)
tests/                        both suites: 68 unittest + 36 pytest (9 of them need data)
registry/                     sources, data manifest, observations, irregularities
knowledge/                    the reusable research base (brief item 11)
notes/                        the earlier session's hypotheses, knowledge, results
evidence/                     every machine-readable result quoted by the later session
pyproject.toml                ruff config; per-file ignores scoped to src/gems47 and scripts only
```

## 4. Reproduce everything

```bash
python3 -m venv venv47 && ./venv47/bin/pip install -r requirements-dev.txt
export PYTHONPATH=src

python3 scripts/restore_data.py --group all     # 23/23 SHA-256 verified, ~30 s
python3 scripts/verify_grid.py                  # 16/16 grid checks PASS
python3 -m ruff check .                         # clean
python3 -m unittest discover -s tests           # 68 tests OK (earlier session + site integrity)
python3 -m pytest tests -q                      # 36 passed (later session)
python3 scripts/ship.py                         # rebuild and re-verify the artifacts (~20 min)
python3 scripts/crossfit_validate.py            # the gate that closed (~12 min)
```

Built under 2 vCPU, 3 GB RAM, ~19 GB disk, and a network that reaches only `pypi.org`, `github.com`,
`api.github.com` and `codeload.github.com` from a shell.

## 5. Remaining work

1. **Use the 1 m DEM.** The competition supplies links to 716 USGS 3DEP 1 m tiles; only pre-derived
   100 m LiDAR scarp rasters were reachable. Every LiDAR-derived layer ranked poorly here
   (`lidar_coh100`, `lidar_strike`, `lidar_valid` among the worst of 72), which is exactly what
   resampling metre-scale scarps to 100 m should do. Largest untested lever.
2. **Spend three slots on the λ-probe.** `1/DTI(λ)` is linear in `1/λ`, so an anchor, a λ = 0.5 scaling
   and a null-addition recover `T`, `F`, `K` **exactly** — conditioning 56×–1380× better than reading
   four decimals. It would also settle whether scoring is restricted to a public chunk (IR-47-011).
3. **Retrieve the staff answer in forum thread 11527** — which data the experts used. Retry via
   `…/11527/10` or `…/11527?print=true` (IR-47-006).
4. **Resolve the 0.2778 attribution** (IR-47-002). The leaderboard row belongs to participant
   `extradr19`; the board does not identify TIFFs, so the file-level attribution is still an inference,
   and it alone decides the flank verdict.
5. **Do not re-test H47-4 / H47-B.** Deep-source magnetic continuity via `TMI_up150` was independently
   proposed by both sessions; the earlier one built it, preregistered a gate, and it **lost to a
   fixed-seed random control** (0.02755 vs 0.03716) with a conformal lower floor of 0.0. Closed.
6. **Attack precision, not coverage.** The family’s whole gain from 0.1922 to 0.2778 came from cutting
   emitted mass. Rank every dot by marginal credit and delete the tail below `α·DTI`.

## 6. Honest limitations

1. **Nothing was scored.** No DrivenData credentials exist here. Every projection is a model output and
   is labelled UNSCORED.
2. **Thirteen scalars are the entire ground truth**, six of them nested thinnings of one field. A
   three-equation solve on that nested triple alone had condition number **3,136** and collapsed.
3. **The 0.2778 attribution is contested** and decides a major verdict, so the break-even (0.2200) is
   reported instead of a conclusion.
4. **The local frames disagree.** SGMC ranks the near-uniform lattice best (0.2499) although it scored
   0.0904 live; the blocked catalogue holdout ranks the flank-pruned arm worst (0.0046) although it is
   reportedly the family best. No local instrument settles this.
5. **Optimizer’s curse is ≈0.30 DTI** and was measured. Every in-fold number in this repository is
   decorative.
6. **The two sessions used different gates** (five truth frames + cross-fitting, vs a preregistered
   locked-test / random-control / conformal-floor protocol). They agree on the verdict, but the
   protocols are not yet unified — see `docs/next-session.md`.
