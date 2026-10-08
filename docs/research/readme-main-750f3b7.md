> **ARCHIVE ONLY — NOT CURRENT SUBMISSION OR SLOT ADVICE.** Score-to-TIFF associations (especially H33-2-B2 / 0.2778) are unverified; every dependent fit, score inversion, “incumbent” comparison, causal pruning claim, and hidden-mass bound is conditional or withdrawn. Use “owner-reported d2.8 reference,” not “incumbent.” H47-SAF is bracketed only between assumed DTI 0.2200 and 0.2400. The 2026-10-06 public-page check was incomplete and is superseded by the 2026-10-07 review of the [DOE/NLR official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), which states up to three scoring/feedback submissions per week and one final selected file. This does not reveal account-specific eligibility, used/remaining opportunities, or selection state. The 7 October 2026 official-board observation in the current review is partial: rank 1 = 0.3774 and 0.3195 = rank 7, with no TIFF attribution; the older body text calling 0.3195 the current top is superseded. No diagnostic cost is inferred or called free. See the current [README](../../README.md) and [corrected analysis](../../docs/analysis.html).

> ADDITIVE MAIN-SNAPSHOT ARCHIVE. Preserve session 3/H48 history; not a current slot recommendation. Adaptive-history floors and hidden-mass assertions are not recertified by C1.

# GEMSDOE47 — standing charter, current status, and two independent negative results

> **Decision as of 2026-10-06 UTC: no submission is eligible and no slot is recommended.**
> This repository now contains the work of **three independent sessions on the same brief**. The first
> two each built a detector, preregistered a gate, and **closed the gate**; their two downloadable
> artifacts are passed then-current local checks and had bounded uniqueness results; a later format audit found several all-finite zero-outside files fail the published outside-null/NaN requirement. All remain **RESEARCH ONLY — NOT FOR SUBMISSION**. A format
> pass is not a scientific promotion.
>
> **The third session (merged 2026-10-06, PR #8) does not change that decision.** It built a
> different detector, ran the random/shifted control whose absence closed the first two gates, and
> **passed it** — but it has not been through cross-fitted LATI, and its own holdout shows the
> optimizer's-curse signature. Its artifact is marked **CONTROL-PASSED · NOT LATI-VALIDATED · NO
> SLOT RECOMMENDED YET**. Its code is namespaced to `src/gems47s3/` and its pages to
> `docs/session3.html`, so nothing of the first two sessions is overwritten
> (`scripts/build_site_s3.py --check` asserts all 44 of their `docs/` files are byte-identical, and
> that the one change to `docs/index.html` is additive).
>
> **Core values:** **Maximize P(Win)** · **Own the Outcome**. Preserve the slot until a genuinely new,
> unique prediction beats the current spatially blocked holdout best under a preregistered, adequately
> controlled test.

## Current decision record

| Item | Current evidence | Decision |
|---|---|---|
| **H48-APEX** — multi-scale curvature lineament consensus (MSCL), catalogue-clear apex emission *(this session)* | 5 bands × 3 apertures structure-tensor curvature transform → cross-domain consensus rank; emitted set = 3×3 local maxima of the consensus at rank ≥ 192, 2.5 px separation, 28,124 px. **Unique**: max equal-mass Jaccard **0.0095** vs all 13 prior rasters (previous project record 0.0457). 21/21 historical local checks; these did not test the published outside-null requirement, which the all-finite zero-outside artifact fails. assumption-conditional lower-bound estimate **0.1149 at nominal family level 46.15%** (exchangeability and score/raster mapping unverified; not a private-score floor) (cross-conformal n=12, family m=7 Bonferroni, k=6; m=1 channel 92.31% but lower-bound estimate −0.1403; split-half n=6 level **0.000** — no non-vacuous family guarantee exists at n=6). Local blocked proxy: `catalogue` **0.0335** vs owner-reported d2.8 reference geometry **0.0067** (not a score receipt; mapping unverified), `sgmc_offcatalogue` **0.0878** vs **0.0989** (loss). | **NOT PROMOTED**; gate closed on two grounds (SGMC frame; assumption-conditional lower-bound estimate below the assumed 0.2600 comparator). Artifact published as the primary download, labelled RESEARCH ONLY. |
| **H48 repack** — owner-reported d2.8 reference field one-to-one snapped onto the consensus ridge, +15 % new ground *(this session)* | Wins **both** local blocked proxy frames vs the owner-reported d2.8 reference geometry (0.0404 / 0.1081 vs 0.0067 / 0.0989) and passed 21/21 historical local checks (not an outside-null format check), but **re-issues a prior geometry**: 59.2 % of its pixels are the 0.2600 field's and 66.9 % of the owner-supplied H33-2-B2 raster's (score association unverified) → max equal-mass Jaccard **0.4400**. | **REJECTED on the standing brief's uniqueness rule.** Moved to `docs/downloads/superseded/` as evidence. |
| **IR-47-016 — the belief model is a similarity regressor** *(this session)* | `control_prox_d2.8` (a distance-rank to the owner-reported 0.2600 field) carries β = 3.229 of the M2 fit vs β = 1.289 for the new MSCL layer and β = 0.635 for shear rate. The model therefore scores any reference-shaped field 0.18–0.20 and the genuinely novel apex set 0.086 **regardless of geology**. Certificates built on it are upper-bounded by how similar a candidate is to a prior submission. | Documented; the apex verdict is reported as *assumption-conditional* and the local blocked frames are quoted alongside. |
| **H47-GSA** — geodetic strain × hydrothermal alteration × thermal discharge *(later session)* | Cross-fitted LATI: paired out-of-fold deltas **−0.0611** and **−0.0450** vs owner-reported d2.8 reference geometry; score/raster association is unverified. Loses on **all five** truth frames, including the exact, model-free covered 300 m kernel integral (**99,916** vs **341,261**). In-fold advantage was **+0.30** — pure optimizer’s curse. | **NOT PROMOTED**; do not spend a slot. |
| **H47-B** — cross-scale `TMI_up150` magnetic-edge persistence *(earlier session)* | Locked-test pooled DTI **0.02755**; tuned single-scale baseline **0.02564**; fixed-seed random control **0.03716**. The candidate **lost to random noise**. Assumption-conditional split-conformal lower-bound estimate **0.0**. | **NOT PROMOTED**; do not spend a slot. |
| H47-SAF — strike-aligned catalogue-flank sensitivity *(historical research)* | Its sign changes only between tested assumed DTIs **0.2200 and 0.2400**. The bracket is conditional on an unverified H33 association and is not an exact break-even, authenticated score/TIFF comparison, or causal verdict. | **Conditional scenario only**; no submission or slot recommendation. |
| H47-SGMC — state geologic-map catalogue-difference transfer | Adding it **worsened** LOO (0.008124 → 0.009279); the fitted truth puts **0.5 %** of `K` there. | **FALSIFIED**. |
| Downloadable artifacts | **This session (H48): `gems47-h48-mscl-apex-192-28124px-20261006T202949Z-allfinite.tif`** — 1 band, float32, EPSG:32611, 3730 × 3292, 100 m, 28,124 positive pixels, values {0,1}, **0** on masked catalogue pixels, **0** outside the footprint, every pixel finite and in [0,1], SHA-256 `8ccde09e97c631c9ac5df0d7aed4ee0850ea0480fe3c4c2831d399e05e0e08d5`, 176,159 B, 21/21 checks. **Third session:** `gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif` — 1 band, float32, EPSG:32611, 3292 × 3730, 100 m, **37,612** positive pixels, values {0,1}, all 12,279,160 cells finite and in [0,1], **no nodata tag**, SHA-256 `f3f840b7880b7540ac6260b6b791ea55b2a875646c28401b01960096dc2da291`, 15/15 format checks, `strongest_range_guarantee=True`. `gems47-h47gsa-…-allfinite.tif` — 37,654 px, SHA-256 `7bfc92ac536cf83a5caf24a815353ba151862f5ad2fbec4461b89353bafb3146`, 21/21. Earlier session: `gems47-h47b-tmiup150-…`, SHA-256 `7e5df9d01689e438e8379ebd4763ed803de02e94826f43da37c33c16380d669b`, 18,524 px. | Published for transparent review. **Not slot-eligible.** The complete register with hashes and statuses is [`docs/all-downloads.html`](docs/all-downloads.html). |
| **Session-3 candidate** — across-strike step in `det_elev_slope`, persisted **1.9 km along strike** (`scarp(det_elev_slope, r=9)`) × `curv(2.5)` × `detrend(2.5)` × `slope_var(5)`, rank-scaled, weighted geometric mean *(third session)* | **Passes the control that closed both gates above.** At matched mass, spacing and flank buffer on identical folds it beats a uniform random field through the identical emitter by **6.02× / 6.17× / 6.61×** on the three prevalence-matched frames and **4.75×** on the isolated-component frame; A > B on **87 of 94** blocks (`evidence/control/controls.json`). Precision-at-40k against expert-mapped fault **0.5049** vs **0.0861** random. **But:** not cross-fitted-LATI validated, and its holdout shows calibration mean **0.0968** → selection mean **0.0606**, a **37 %** out-of-fold drop. | **CONTROL-PASSED · NOT LATI-VALIDATED**; do not spend a slot on it yet. |
| Uniqueness | **H48-APEX (this session): max equal-mass Jaccard 0.0095 against all 13 prior scored rasters — the best novelty figure recorded in this repository.** Third session: max Jaccard **0.0144**, max containment **0.0277**, against **18** reference artifacts. Later session: **0.0457** against the 13. Earlier session: **zero** exact positive-mask matches against **334** exact-grid TIFFs in 55 visible `buffedlizard55-lab` GEMSDOE repositories; max equal-mass Jaccard **0.01119**. | Supports uniqueness against accessible artifacts. **Not a global uniqueness proof** and not a performance result. |

| Public leaderboard | One-time read 2026-10-06: rank 1 **0.3774** (participant name not preserved), DARD **0.3195 at #7**, `extradr19` **0.2778 at #13**. An earlier same-date read gave rank 1 = 0.3345 and DARD at #5; the later observation supersedes it. | Participant scores do **not** identify TIFFs or receipts. No TIFF-to-score mapping is authenticated (IR-47-002). |
| The reported `"Predicted values must be in range [0, 1]"` rejection | **Cause unknown.** The old scan applied a NaN-intolerant raw-array range test to sibling TIFFs; NaNs outside are permitted by the published format wording. That scan does not reproduce the organizer parser or explain the earlier rejection. The rejected bytes and parser receipt are unavailable. | The historical primary artifact was all-finite with zeros outside and no nodata tag, so it fails the published outside-null check. Separate NaN-outside variants follow an owner-supplied mirror convention only; portal acceptance is unverified. |

Details: [session-3 front page](docs/session3.html) ·
[session-3 controls](evidence/control/controls.json) ·
[session-3 conformal selection](evidence/conformal/selection.json) ·
[session-3 remaining work](docs/REMAINING_WORK.html) ·
[session-3 compliance check](docs/COMPLIANCE.html) ·
[H47-B validation report](docs/validation-h47b-20261006.md) ·
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
   controls. Ties, unstable folds, missing labels, failed controls, or a zero/unsupported assumption-conditional lower-bound estimate
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
| Does any *a priori* geological layer beat the fixed comparator out of fold? | **No.** In-fold +86.4 % LOO collapsed to −0.053 out of fold | `evidence/crossfit_validation.json` |
| What does the owner-reported 0.2778 association suggest? (unverified) | Conditional precision-pruning hypothesis only; neither the score/file association nor a causal gain is established. | `knowledge/05_why_02778_and_can_we_beat_it.md` |
| Illustrative fixed-ratio algebra for 0.3195 | Would require 102.7% weighted recall under one unverified ratio scenario; this does not establish that 0.3195 is unreachable | `docs/evidence.html` |
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
  executive-summary.html      historical workflow, conditional 0.2778 analysis, and evidence limits
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

1. **Re-open the H48-APEX gate with one scored slot, or do not spend one.** The apex field is the only
   artifact here that is both unique (0.0095) and derived from this project's own detector; its DTI is
   *unknown*, because the belief model cannot score it (IR-47-016). Two honest options: (a) spend one
   weekly slot on it as an information-gathering probe and use the returned scalar to calibrate, or
   (b) spend the slot on the λ-probe first, which is strictly more informative per slot.
2. **Certify with m = 1, not by fitting more.** With n=12 returns, a family of 7 costs the certificate
   46.15% level; a single pre-registered operating point would be certified at 92.31%. The lever is a
   pre-registered operating point, not a bigger sweep.
3. **Use the 1 m DEM.** The competition supplies links to 716 USGS 3DEP 1 m tiles; only pre-derived
   100 m LiDAR scarp rasters were reachable. Every LiDAR-derived layer ranked poorly here
   (`lidar_coh100`, `lidar_strike`, `lidar_valid` among the worst of 72), which is exactly what
   resampling metre-scale scarps to 100 m should do. Largest untested lever.
4. **Spend three slots on the λ-probe.** `1/DTI(λ)` is linear in `1/λ`, so an anchor, a λ = 0.5 scaling
   and a null-addition recover `T`, `F`, `K` **exactly** — conditioning 56×–1380× better than reading
   four decimals. It would also settle whether scoring is restricted to a public chunk (IR-47-011).
5. **Retrieve the staff answer in forum thread 11527** — which data the experts used. Retry via
   `…/11527/10` or `…/11527?print=true` (IR-47-006).
6. **Keep the 0.2778 attribution unverified** (IR-47-002). The dated participant-level observation lists
   `extradr19` at 0.2778 but does not identify a TIFF/hash. H33-2-B2-dependent analyses are
   hypothetical/conditional, not authenticated results or a verdict.
7. **Do not re-test H47-4 / H47-B.** Deep-source magnetic continuity via `TMI_up150` was independently
   proposed by both sessions; the earlier one built it, preregistered a gate, and it **lost to a
   fixed-seed random control** (0.02755 vs 0.03716) with an assumption-conditional split-conformal lower-bound estimate of 0.0. Closed.
8. **Do not infer causality from an unverified association.** Owner narratives connect score labels and pruning, but the participant-to-TIFF mapping and causal effect are not authenticated.

## 6. Honest limitations

1. **Nothing was scored.** No DrivenData credentials exist here. Every projection is a model output and
   is labelled UNSCORED.
2. **Thirteen scalars are the entire ground truth**, six of them nested thinnings of one field. A
   three-equation solve on that nested triple alone had condition number **3,136** and collapsed.
3. **The 0.2778 attribution is contested** and decides a major verdict, so the sign-change bracket (0.2200–0.2400), not an exact break-even, is
   reported instead of a conclusion.
4. **The local frames disagree.** SGMC ranks the near-uniform lattice best (0.2499) although it scored
   0.0904 live; the blocked catalogue holdout ranks the flank-pruned arm worst (0.0046) although it is
   reportedly the family best. No local instrument settles this.
5. **Optimizer’s curse is ≈0.30 DTI** and was measured. Every in-fold number in this repository is
   decorative.
6. **The H48 certificate is assumption-conditional, and the assumption is known to be weak.** The 13
   calibration returns are partly nested thinnings of one field (h33-2-b2 ⊂ d2.8, containment 1.000), so
   exchangeability with a *new* candidate is an assumption, not a property. The bound is a bound on the
   public-test DTI of a probe raster, not on the private expert label set.
7. **The apex arm has no measured truth frame that supports it.** It wins the weak `catalogue` frame 5×
   and loses the independent `sgmc_offcatalogue` frame by 11%. Nothing local resolves that, which is
   exactly why it is not promoted.
8. **The two sessions used different gates** (five truth frames + cross-fitting, vs a preregistered
   locked-test / random-control / assumption-conditional conformal lower-bound protocol). They agree on the verdict, but the
   protocols are not yet unified — see `docs/next-session.md`.
