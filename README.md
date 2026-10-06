# GEMSDOE47 — standing charter, current status, and two independent negative results

> **Decision as of 2026-10-06 UTC: no submission is eligible and no slot is recommended.**
> This repository contains the work of **two independent sessions on the same brief**. Both built a
> detector, both evaluated a preregistered gate, and **both closed the gate**. Every downloadable TIFF is
> documented as **RESEARCH ONLY — NOT FOR SUBMISSION**. The new single-scale d=5 file passes the strict
> local validator only against an explicit mask derived from the mirrored sample template; a different
> feature-derived footprint fails. The authorized official footprint is unresolved. The candidate also
> loses to H47-B and random control on a known-fault-catalogue proxy, not the hidden missing-fault target.
>
> **Core values:** **Maximize P(Win)** · **Own the Outcome**. Preserve the slot until a genuinely new,
> unique prediction beats the current spatially blocked holdout best under a preregistered, adequately
> controlled test.

## Current decision record

| Item | Current evidence | Decision |
|---|---|---|
| **H47-GSA** — geodetic strain × hydrothermal alteration × thermal discharge *(later session)* | Cross-fitted LATI: paired out-of-fold deltas **−0.0611** and **−0.0450** vs the incumbent. Loses on **all five** truth frames, including the exact, model-free covered 300 m kernel integral (**99,916** vs **341,261**). In-fold advantage was **+0.30** — pure optimizer’s curse. | **NOT PROMOTED**; do not spend a slot. |
| **H47-B** — cross-scale `TMI_up150` magnetic-edge persistence *(earlier session)* | Locked-test DTI against the known-fault catalogue-mask proxy: **0.02755**; tuned single-scale proxy **0.02564**; fixed-seed random proxy **0.03716**. These are not scores on the hidden missing-fault target. The candidate **lost to the random control**; the proxy-target conformal lower bound is **0.000**. | **NOT PROMOTED**; do not spend a slot. |
| H47-SAF — strike-aligned catalogue-flank re-occupation *(later session)* | **+55.7 %** LOO on 12 observations (67.1 % of fitted `K` within 150 m, ×19.5 enrichment). Adding the disputed H33-2-B2 observation *as if* it were the 0.2778 row changes LOO to **−64.0 %** and gives break-even 0.2200. The participant score is not authenticated to that TIFF. | **Attribution-contingent**: falsified if the disputed mapping is true; otherwise inconclusive. |
| H47-SGMC — state geologic-map catalogue-difference transfer | Adding it **worsened** LOO (0.008124 → 0.009279); fitted `K` mass there is **0.5 %** under the included score/file assumptions. | **Negative screen**, conditional on the 13-observation record. |
| New unique research TIFF | `gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-nanoutside.tif`; SHA-256 `dc71c807fbca2cd398f394bcd91b10ecec6b46fe89c2d61f5b1c058fef672811`; 309,530 bytes; one-band float32, EPSG:32611, 3730 × 3292, 100 m, 18,524 binary predictions. In-footprint values are [0,1], with NaN nodata/outside. **Strict local validator passes only when given an explicit binary footprint derived from finite cells in the mirrored sample template.** The training-features-derived footprint differs by 1,540 feature-only pixels and 3,061 sample/label pixels invalid in features; the official evaluation footprint is unresolved. | **RESEARCH ONLY — NOT FOR SUBMISSION.** It loses the proxy screen and is not a promoted discovery model; format validity is not scientific validation or organizer acceptance. |
| Candidate uniqueness | The new positive mask has 0 exact matches against **334/334** verified exact-grid TIFF blobs from 55 visible sibling repositories (max equal-mass Jaccard **0.01290**, max support Jaccard **0.02010**) and **19/19** independent exact-grid local prior TIFFs (0 exact matches; max equal-mass/support Jaccard **0.02055**, the earlier H47-B TIFF; the paired all-finite encoding of this same mask is excluded). Remote blob hashes and byte counts matched the saved inventory; the prior remote mask comparison is reused because the all-finite diagnostic's positive mask was verified identical, while 19 local priors were rerun for this encoding. | Two bounded snapshots only; not global uniqueness or performance evidence. See `evidence/conformal_candidate_uniqueness_20261006.json`. |
| H47-B split-conformal spacing result | The sweep selected `d=5 px / 500 m` on five selection blocks. Six calibration blocks give nominal marginal coverage **6/7 = 85.7%** for a diagnostic DTI against the known-fault catalogue-mask proxy, with clipped lower prediction bound **0.000**. Two calibration cores have no mask pixels; spatial exchangeability is unverified. | This is not calibration for missing-fault labels or a private leaderboard score. No positive proxy floor or private-leaderboard guarantee. |
| Existing downloadable research artifacts | H47-GSA all-finite SHA-256 `7bfc92ac536cf83a5caf24a815353ba151862f5ad2fbec4461b89353bafb3146`; H47-B cross-scale SHA-256 `7e5df9d01689e438e8379ebd4763ed803de02e94826f43da37c33c16380d669b`. | Published for transparent review. **Not slot-eligible.** |
| Uniqueness | Later session: max Jaccard **0.0457** against all 13 restored scored rasters. Earlier session: **zero** exact positive-mask matches against **334** exact-grid TIFFs in 55 visible `buffedlizard55-lab` GEMSDOE repositories; maximum equal-mass Jaccard **0.01119**. | Supports uniqueness against accessible artifacts. **Not a global uniqueness proof** and not a performance result. |
| Public leaderboard | One-time read 2026-10-06: rank 1 **0.3774** (participant name not preserved), DARD **0.3195 at #7**, `extradr19` **0.2778 at #13**. An earlier same-date read gave rank 1 = 0.3345 and DARD at #5; the later observation supersedes it. | Participant scores do **not** identify TIFFs or receipts. No TIFF-to-score mapping is authenticated (IR-47-002). |
| The reported `"Predicted values must be in range [0, 1]"` rejection | **Root cause not verified.** The rejected TIFF and organizer-side check are unavailable. A separate artifact sample shows a NaN-intolerant range expression can reject allowed NaNs; this is only a plausible parser hazard. | The primary TIFF's strict local audit passes against an explicit sample-template-derived mask, while the features-derived mask disagrees. This establishes neither the official footprint nor organizer acceptance. See IR-25 and `docs/irregularities.md`. |

Details: [H47-B validation report](docs/validation-h47b-20261006.md) ·
[uniqueness audit](docs/h47b-uniqueness-audit-20261006.json) ·
[LATI method](docs/method.html) · [cross-fitted validation](evidence/crossfit_validation.json) ·
[flank sensitivity](evidence/flank_sensitivity.json) ·
[leaderboard / source attribution](docs/analysis.md) ·
[irregularity register (earlier session)](docs/irregularities.md) ·
[IR-47-001…020 (later session)](docs/irregularities.html)

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
> 3. Investigate the reported submission error **`"Predicted values must be in range [0, 1]"`** without
>    claiming an unverified root cause. Values must lie within [0, 1], single-band float32, EPSG:32611,
>    100 m resolution, with the template grid/bounds and the organizer's documented outside-bounds
>    convention; verify the exact written TIFF locally, while distinguishing local checks from portal acceptance.
> 4. Give the submission a **unique name** plus a short distinguishing note for the DrivenData
>    submission form's optional **"Note"** field (for example `clustering with k=25`).
> 5. A **GitHub Pages site** with a clean, simple, user-friendly, organized UI containing all relevant
>    information and official verified source links.
> 6. An **executive-summary subpage** explaining exactly how to submit to the contest.
> 7. **Study why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (GEMSDOE32) was reported alongside
>    a family-best 0.2778**, answer with rigorous metric/mechanistic reasoning, and attempt a higher score
>    only after resolving score-to-file attribution and passing the holdout gate. The 0.2778-to-TIFF link is
>    contested; the latest saved public snapshot shows rank 1 at 0.3774, while 0.3195 is a participant-level
>    row, not the current top or a verified TIFF score.
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
> 15. Apply split conformal to the repository's own spacing/DTI history with a frozen selection,
>     calibration and locked-test split. Report the exchangeability unit, sample size, order-statistic rank,
>     nominal level, empty-label blocks, clipped lower bound and limitations. Do not present a spatial-block
>     result as an assumption-free guarantee or use it to authorize a slot when the positive floor is zero.
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
| Does the hidden truth hug the catalogue? | 12 owner-reported score/file pairs support this in the fitted reconstruction (67 % of `K` within 150 m, ×19.5). Assuming the contested H33-2-B2 ↔ 0.2778 mapping is true flips the leave-one-out result; without an official receipt, the 13th point cannot resolve the hypothesis. | `evidence/flank_sensitivity.json`; `registry/observations.jsonl` |
| Does any *a priori* geological layer beat the incumbent out of fold? | No candidate passed the cross-fitted gate; the precise magnitude depends on the 13-observation history, including one contested mapping. | `evidence/crossfit_validation.json` |
| Why is 0.2778 associated with H33? | Not established. If the contested mapping were true, the metric arithmetic is consistent with reducing low-credit mass; it does not prove the artifact earned that participant-level score. | `knowledge/02_the_metric_algebra.md`; `docs/analysis.md`; `IR-47-002` |
| Can the model algebra reach 0.3195 at the incumbent’s waste ratio? | Under the fitted model, no: it requires 102.7 % weighted recall. This is conditional algebra, not a private-score forecast; 0.3195 was rank 7 in the saved public snapshot, not its top row. | `docs/evidence.html`; `docs/analysis.md` |
| What caused the range rejection? | Unknown; the rejected file and portal diagnostic are unavailable. NaNs are one plausible local failure mode, not a verified cause. | `evidence/range_error_diagnosis.json`; `docs/irregularities.md` |

### LATI — the instrument the later session built

Thirteen prior prediction files were recovered byte-exactly with owner-reported DTI values; twelve
score/file pairs are transcribed from owner materials, while the H33-2-B2 / 0.2778 pair has an explicit
attribution conflict (the site marks that TIFF unscored and the public participant row has no artifact
receipt). **LATI** (Leaderboard-Anchored Truth Inversion) treats the numbers as *measurements of the
hidden label set* only under those assumptions: `T = ⟨q, w_p⟩` is exactly linear in the unknown truth
intensity `q`, so each included owner-reported DTI under its recorded pairing contributes one equation. It replaces the earlier family’s self-referential truth model
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

The repository preserves both prior work streams and adds the current negative screening result.

```
README.md                     standing brief, decision record, reproduction and limitations
index.html                    primary root landing page; unique research TIFF + no-slot decision
docs/
  index.html                  secondary research landing page, consistent with root decision
  executive-summary.html      download, conformal result, metric attribution, future instructions
  hypotheses.html/.md         four unbuilt hypotheses plus data/novelty caveats
  analysis.html/.md           locked results, conformal, bounded uniqueness and score limits
  method.html                 LATI algebra, identifiability, controls and cross-fitting
  evidence.html               number ledger with contested-score caveats
  submit.html                 fail-closed workflow for a future promoted candidate
  sources.{html,md}            official and secondary source provenance
  irregularities.{html,md}     evidence flags; review before asserting causes
  validation-h47b-20261006.md  preregistered H47-B test and limits
  next-session.md              ordered work and no-slot decision
  prev-session/                superseded pages retained as historical archive
  downloads/                   generated TIFFs; every current candidate is research-only
src/gems47/ and gemsdoe47/     candidate, metric, grid, spatial and validation code
scripts/
  build_footprint_mask.py derives a binary mask from finite, unmasked sample-template cells (not provenance)
  conformal_spacing_audit.py  frozen selection/calibration/test sweep and TIFF build
  audit_candidate_uniqueness.py compares exact-grid masks with pinned public Git blobs
  restore_data.py / verify_grid.py / crossfit_validate.py / ship.py and prior utilities
tests/                         metric, grid, site, conformal and artifact checks
registry/                      manifests, owner reports, irregularities
knowledge/                      reusable metric, target and next-step notes
notes/                          retired historical claims; do not reuse as current evidence
evidence/                       machine-readable screening and bounded-uniqueness results
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

1. **Assess the unbuilt hypotheses before data spend.** Start with the native-resolution USGS 3DEP
   scarp/channel operator, but do not call it available until the exact 1 m tile list, downloads,
   vertical datum, coverage and gaps are checked. The other prospective ideas—ASTER alteration classes,
   strain/magnetic concordance, and time-normalized GDR station residuals—are ranked with source and
   availability caveats in `docs/hypotheses.md`.
2. **Do not spend the λ-probe slots by default.** Its scale identity is mathematically useful, but there
   is no verified risk-free upload allowance and the final-entry opportunity can be scarce. Any probe
   requires current official rules plus an authorized owner's explicit approval.
3. **Resolve the 0.2778 mapping only through an authorized receipt.** The public participant row has no
   TIFF hash; GEMSDOE32 marks H33-2-B2 unscored. Do not poll/copy the leaderboard repeatedly or infer
   the file mapping. See IR-47-002 and the Terms of Use notice.
4. **Do not re-run H47-B or call it unbuilt.** Cross-scale `TMI_up150` edge persistence already failed
   against the fixed-seed random control (0.02755 vs 0.03716); the new single-scale control is lower
   (0.02564) and also loses to random. The conformal lower bound is 0.000.
5. **Do not delete emissions solely from the general precision identity.** Whether a pixel's mass is
   harmful depends on the organizer's mask and truth credit. The H33 score/file pair is contested, and
   the local masking experiment indicates known-catalogue cells are excluded before both sums.

## 6. Honest limitations

1. **No new artifact received an organizer score in this session.** No DrivenData credentials are
   present; candidate metrics are local scores against public mirrors and an incomplete catalogue.
2. **The historical score/file set is small and dependent.** Thirteen owner-reported records are not
   thirteen independent authoritative observations; one H33-2-B2 / 0.2778 pairing is contested and
   several predictions are nested variants.
3. **The 0.2778 attribution is unresolved.** The public row has no TIFF hash/receipt and the owner page
   marks H33-2-B2 unscored. Metric arithmetic can explain possible precision effects, not causation.
4. **Local proxy frames disagree.** A public SGMC frame can favor a diffuse lattice while other catalogue
   blocks favor different masks. These are not private-label validations and cannot resolve score
   attribution.
5. **Optimizer's curse is substantial** in the retrospective LATI screen. Do not use in-fold LOO as
   promotion evidence; require a frozen spatial holdout, ablations, and controls.
6. **The two historical work streams used different screens.** Their results should not be collapsed
   into one calibrated ranking. The present H47-B split uses five selection, six calibration, and five
   locked-test blocks; spatial exchangeability remains unverified and its lower bound is zero.
7. **The portal range-error cause and authorized footprint are unknown.** The rejected TIFF and organizer
   diagnostic are unavailable. The new NaN-outside TIFF passes strict local checks only against the
   explicit mask derived from the mirrored sample; the training-features footprint disagrees. Neither
   mask provenance nor local validity guarantees organizer acceptance.
8. **No live leaderboard feed is implemented.** DrivenData's Terms restrict automated monitoring and
   require prior written consent for manual monitoring/copying. Use the official link, not copied polling.
