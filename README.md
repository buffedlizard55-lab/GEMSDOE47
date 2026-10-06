# GEMSDOE47 — standing charter, current status, and three screened hypotheses

> **Decision as of 2026-10-06 UTC: no submission is eligible and no slot is recommended.**
> Three distinct candidate screens are now documented: H47-B (magnetic persistence), H47-GSA
> (strain/alteration/discharge), and H47-QC (geothermometer consensus × aligned gravity/magnetic
> edges). Each was tested against a stated local holdout/control protocol; none passed its promotion
> gate. The research TIFFs are clearly marked **RESEARCH ONLY — NOT FOR SUBMISSION**. A format pass,
> file uniqueness, or public-catalogue score is not a scientific promotion.
>
> **Core values:** **Maximize P(Win)** · **Own the Outcome**. Preserve the slot until a genuinely new,
> unique prediction beats the current spatially blocked holdout best under a preregistered, adequately
> controlled test.

## Current decision record

| Item | Current evidence | Decision |
|---|---|---|
| **H47-GSA** — geodetic strain × hydrothermal alteration × thermal discharge *(later screen)* | Exploratory cross-fitted LATI (owner-reported score/file mappings, not receipt-authenticated): paired out-of-fold deltas **−0.0611** and **−0.0450**. Its local covered 300 m integral was **99,916** vs **341,261** for the comparator; those are not organizer scores. | **NOT PROMOTED**; do not spend a slot. |
| **H47-B** — cross-scale `TMI_up150` magnetic-edge persistence *(earlier screen)* | Locked-test pooled DTI **0.02755**; tuned single-scale baseline **0.02564**; fixed-seed random control **0.03716**. The candidate **lost to random noise**. Assumption-conditional conformal lower floor **0.0**. | **NOT PROMOTED**; do not spend a slot. |
| **H47-QC** — geothermometer consensus × aligned RTP/isostatic-gravity edge *(current screen)* | Frozen 5,000-point/4×4-block test selected **6 px / 600 m**; locked-test pooled DTI **0.013169**, below the geochemistry-only ablation **0.014195**. Fixed split-conformal nominal level **85.7%**; clipped lower DTI floor **0.0**. Fifty-four emitted pixels overlap the known public catalogue. | **NOT PROMOTED**; do not spend a slot. |
| H47-SAF — strike-aligned catalogue-flank re-occupation *(later session)* | The 12-row owner-reported fit was highly sensitive to a 13th value alleged to be 0.2778: the fit flipped (reported LOO +55.7% to −64.0%; break-even 0.2200). But the 0.2778 participant score is not authenticated to the H33-2-B2 TIFF, which its owner marks **UNSCORED**. | **ATTRIBUTION-SENSITIVE / UNRESOLVED**; do not treat as independently falsified or validated. |
| H47-SGMC — state geologic-map catalogue-difference transfer | Adding it worsened an owner-reported LOO fit (0.008124 → 0.009279); the inferred `K` share was 0.5%. Score/file mappings are not authenticated. | **Not supported in that exploratory fit.** |
| Downloadable artifacts | H47-GSA and H47-B remain as previously documented. The H47-QC file is `gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.tif`: single-band float32, EPSG:32611, 100 m, 5,000 binary pixels, all-finite `[0,1]`, SHA-256 `3866b60cf91b4f6bff2ef694153550aa97a744a3091a57ef9f83da41e16b91b2`; 54 emitted cells overlap known-catalogue labels. | [One-click download and short note](docs/downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.md). **Research only; not slot-eligible.** |
| Uniqueness | H47-GSA: max Jaccard **0.0457** against 13 local scored rasters. H47-B: zero exact matches among **334** exact-grid rasters. H47-QC: zero exact matches among the same **334**; max equal-mass Jaccard **0.002104**, max positive-support Jaccard **0.002443**. | Bounded to the captured, accessible artifacts; not global uniqueness, organizer provenance, score attribution, or performance. |
| Public leaderboard | One-time read 2026-10-06: rank 1 **0.3774** (participant name not preserved), DARD **0.3195 at #7**, `extradr19` **0.2778 at #13**. An earlier same-date read gave rank 1 = 0.3345 and DARD at #5; the later observation supersedes it. | Participant scores do **not** identify TIFFs or receipts. No TIFF-to-score mapping is authenticated (IR-47-002). |
| The reported `"Predicted values must be in range [0, 1]"` rejection | A bounded audit shows NaN is a reproducible failure mode: **12/12** scanned `-nan` variants fail a NaN-intolerant check, while **17/17** all-finite variants pass. The original rejected bytes are unavailable, so its exact cause is **unverified**. | The H47-QC research artifact is all-finite `[0,1]` (zeros outside the footprint, nodata unset); this is a safe local format choice, not proof of portal acceptance. |

Details: [H47-QC preregistration](docs/preregistered-h47qc-20261006.md) ·
[H47-QC blocked-screen results](evidence/h47qc-screen-20261006.json) ·
[H47-QC accessible-artifact audit](evidence/h47qc-uniqueness-audit-20261006.json) ·
[H47-QC one-click research TIFF and note](docs/downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.md) ·
[H47-B validation report](docs/validation-h47b-20261006.md) ·
[H47-B uniqueness audit](docs/h47b-uniqueness-audit-20261006.json) ·
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
> 1. A **unique, newly generated candidate** GeoTIFF, different from accessible prior GEMSDOE artifacts.
>    Publish it as a visibly research-only download if it fails the scientific gate; call it submission-
>    eligible only after every promotion gate passes. Copying a previous submission is acceptable *only*
>    for learning and education — never as the deliverable.
> 2. The TIF must be **easy to download** from the GitHub Pages site: an obvious one-click download at
>    the very top of the site and in the executive summary.
> 3. Fix the reported submission error **`"Predicted values must be in range [0, 1]"`**. Deliver a
>    single-band float32 GeoTIFF on the official EPSG:32611, 100 m grid and exact template bounds, with
>    finite values in `[0,1]`. The chosen research files use `0.0` outside the template footprint because
>    NaNs fail a NaN-intolerant range check; organizer acceptance of that convention is not inferred.
> 4. Give the submission a **unique name** plus a short distinguishing note for the DrivenData
>    submission form's optional **"Note"** field (for example `clustering with k=25`).
> 5. A **GitHub Pages site** with a clean, simple, user-friendly, organized UI containing all relevant
>    information and official verified source links.
> 6. An **executive-summary subpage** explaining exactly how to submit to the contest.
> 7. Scientifically assess the reported **0.2778** result without assuming that the participant score
>    maps to `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: the official board is participant-level,
>    the H33-2-B2 owner page says “UNSCORED”, and no organizer receipt maps a file hash to that score.
>    Use the DTI algebra and accessible byte evidence to separate supported mass/precision mechanisms
>    from speculation. Treat **0.3774** (one-time public rank-1 observation, 2026-10-06) as the latest
>    leader reference; **0.3195** was rank 7, not the current top. Never infer private-set performance.
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
> - Known limitation acknowledged in the brief itself: no DrivenData portal credentials are available.
>   The core rasters and listed external layers were restored from hash-pinned mirrors (see §2), but
>   `1m_DEM_links.csv` is not present in this checkout and exact USGS 3DEP tile coverage is unverified.

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
| Hidden new-fault mass `K` in the scored split | Historical LATI analysis estimated **12,348 px** under an owner-reported score/file mapping; fitted-shape estimates were 15,638–21,477. These are not authenticated truth counts. | `evidence/lati_fit.json`, `evidence/flank_mass.json`; caveats in `docs/analysis.md` |
| Does the hidden truth hug the catalogue? | A 12-row owner-reported fit suggested 67% of fitted `K` within 150 m (×19.5 enrichment). The alleged 13th-point reversal depends on an unauthenticated 0.2778/H33-2-B2 mapping; **conclusion unresolved**. | `evidence/flank_sensitivity.json`; `docs/analysis.md` |
| Does any *a priori* geological layer beat the incumbent out of fold? | The stored LATI cross-fit was negative (−0.0611/−0.0450), but participant-score/file mappings are not authenticated; treat as exploratory. | `evidence/crossfit_validation.json`; `docs/analysis.md` |
| Why is 0.2778 high? | DTI algebra makes sparse precision valuable. The owner-reported family trajectory is consistent with mass falling 69% while covered kernel credit fell 33%, but the 0.2778 participant row is **not authenticated to H33-2-B2 or its alleged final deletion**. | `knowledge/02_the_metric_algebra.md`; `docs/analysis.md` |
| How demanding are the old 0.3195 target and the current 0.3774 leader? | Under an **illustrative, unverified** `F/K = 8.02` scenario, the metric algebra gives `T/K ≈ 82.05%` and `98.13%`, respectively. The earlier 102.7% “impossible” claim was inconsistent with its stated ratio and is retracted. | `knowledge/02_the_metric_algebra.md`; `docs/analysis.md` |
| What did the bounded range audit establish? | NaN pixels fail a NaN-intolerant `[0,1]` check; the original rejected bytes are unavailable, so the cause of that specific rejection is unverified. | `evidence/range_error_diagnosis.json`; limitation in `docs/irregularities.md` |

### LATI — an exploratory model, not authenticated leaderboard supervision

Thirteen prior submission rasters were recovered byte-exactly, but their score-to-file associations
are owner-reported and are not backed by organizer receipts. **LATI** (Leaderboard-Anchored Truth
Inversion) treats those provisional pairs as *hypothetical measurements* of a hidden label field;
`T = ⟨q, w_p⟩` is algebraically linear in an assumed truth intensity `q`. It replaces the earlier
family’s self-referential truth model
(`π ~ exp(−d(H19-5)/1.85 px)` — a scatter around the group’s own best field, which cannot falsify the
field it was built from). It ships with positive controls (proximity to submitted rasters: ranks #1–#6
of 72), a negative control (spatially shuffled layer: rank #71), permutation nulls (all 14 top layers
beaten 10/10), and a 700× binned fast path verified to 1.1e-05 DTI. See [docs/method.html](docs/method.html).

## 2. Data provenance — no DrivenData credentials were needed

Every local input byte is hash-pinned and reproducible. `scripts/restore_data.py` restores all **23** files
(3 competition-format rasters, 7 external layers, 12 prior-submission rasters, 1 reference raster) from
the owner's sibling repositories through the GitHub Contents API and verifies each SHA-256 and byte
count before use. These mirrors are not authenticated organizer downloads and the score/file mappings
are not receipts:

```
python3 scripts/restore_data.py --group all      # 23/23, ALL_VERIFIED=True, ~30 s
```

Restored bytes live in `.cache/gems_data/` (**git-ignored**, ~507 MB). Nothing large is committed.
Receipt: [`data/restore_receipt.json`](data/restore_receipt.json). The pins prove **mirror
consistency, not organiser authentication** — the portal is login-walled.

## 3. Layout

The repository retains earlier H47-B/H47-GSA code and a separate H47-QC research screen. Historical
artifacts remain for audit; current-facing documentation has been revised to label unverified mappings,
negative screens, and research-only outputs explicitly.

```
README.md                     this file - charter, decision record, standing brief
index.html                    the earlier session's root landing page (site integrity tests gate it)
docs/
  index.html                  the canonical site: artifact + gate verdict first
  executive-summary.html      future-only submit workflow, promotion gate, 0.2778 attribution limits, target algebra
  hypotheses.html             historical owner-reported hypothesis screens
  hypotheses-round2-20261006.md  current ranked shortlist and H47-QC result
  method.html                 exploratory LATI proxy; score/file links unauthenticated
  evidence.html               historical numbers, caveats and H47-QC results
  irregularities.html         IR-47-001 ... IR-47-015
  leaderboard.html · analysis.{html,md} · sources.{html,md} · submit.html
  portal-checklist.{html,md} · method.md · hypotheses.md · prior-results.md
  irregularities.md · validation-protocol.md · validation-h47b-20261006.md
  preregistered-h2.md · preregistered-h47qc-20261006.md · review-log.md · next-session.md
  prev-session/               the three superseded landing pages, preserved verbatim
  downloads/                  current and earlier research-only artifacts
  prior-results.csv · prior-output-manifest.csv
gemsdoe47/                    earlier session: candidate, magnetic, spatial, validation
src/gems47_*.py               earlier session: metric, blocks, emit, verify_submission
src/gems47/                   grid, metric, features, H47-QC consensus, blocks and LATI
scripts/
  restore_data.py             restore and SHA-256-verify the 23 manifest inputs
  verify_grid.py              re-derive every grid constant from restored bytes (16 checks)
  run_h47qc.py                frozen public-catalogue screen; research-only, never portal-eligible
  lati_fit.py · lati_controls.py · test_flank.py · flank_sensitivity.py · screen13.py
  crossfit_validate.py        legacy exploratory fit with unauthenticated score/file associations
  ship.py                     legacy H47-GSA build; not promotion or upload authorization
  build_h1_candidate.py · build_h47a.py · run_h2_experiment.py · package_submission.py
  check_competition_data.py · validate_submission.py           (earlier session)
tests/                        both suites: 68 unittest + 106 pytest (optional mirror-dependent tests may skip)
registry/                     sources, data manifest, observations, irregularities
knowledge/                    the reusable research base (brief item 11)
notes/                        the earlier session's hypotheses, knowledge, results
evidence/                     every machine-readable result quoted by the later session
pyproject.toml                ruff config; per-file ignores scoped to src/gems47 and scripts only
```

## 4. Reproduce the checks and current research screen

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
export PYTHONPATH=src

python3 scripts/restore_data.py --group all      # restore 23 manifest inputs and verify hashes
python3 scripts/verify_grid.py                   # 16/16 grid checks
.venv/bin/ruff check .
.venv/bin/python -m unittest discover -s tests    # 68 passed; optional mirror tests may skip
.venv/bin/python -m pytest tests -q               # 106 passed; optional mirror tests may skip
.venv/bin/python scripts/run_h47qc.py             # frozen public-catalogue screen; research-only output
```

`run_h47qc.py` never authorizes upload; its current result is **NOT PROMOTED**. The legacy `ship.py`
build is not a submission workflow. Do not upload any research artifact or spend a slot without a new
preregistered detector beating the blocked-holdout gate.

Built under 2 vCPU, 3 GB RAM, ~19 GB disk, and a network that reaches only `pypi.org`, `github.com`,
`api.github.com` and `codeload.github.com` from a shell.

## 5. Remaining work

1. **Audit 1 m DEM coverage before investing.** The official USGS 3DEP 1-meter collection is public,
   but exact usable tile coverage/acquisition within the competition template and the current leader's
   inputs are unknown. The accessible inventory had only pre-derived 100 m LiDAR scarp layers, which
   ranked poorly in owner-reported exploratory fits. Fine-scale terrain is a plausible data gap, not a
   proven score lever; proceed only after coverage verification and a preregistered spatial holdout.
2. **Do not spend slots on the λ-probe.** Although `1/DTI(λ)` is linear in `1/λ` under the local
   metric assumptions, the probe is not a geological detector and has not beaten the blocked holdout.
   It is not authorized under the standing no-slot rule, even in an unlimited round.
3. **Retrieve the staff answer in forum thread 11527** — which data the experts used. Retry via
   `…/11527/10` or `…/11527?print=true` (IR-47-006).
4. **Resolve the 0.2778 attribution** (IR-47-002) only if an organizer receipt, exact file hash, or
   equivalent primary record becomes available. The public row belongs to participant `extradr19`, but
   the board does not identify TIFFs; until mapped, the flank analysis remains attribution-sensitive.
5. **Do not re-test H47-4 / H47-B.** Deep-source magnetic continuity via `TMI_up150` was independently
   proposed by both sessions; the earlier one built it, preregistered a gate, and it **lost to a
   fixed-seed random control** (0.02755 vs 0.03716) with a conformal lower floor of 0.0. Closed.
6. **Treat sparse precision as a testable hypothesis, not a proven 0.2778 explanation.** The owner-
   reported family trajectory is consistent with pruning low-credit mass, but the score-to-file mapping
   and precise causal operation remain unresolved. Any future candidate still needs a preregistered,
   target-relevant blocked holdout gain before a slot can be considered.

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
