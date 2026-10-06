# Next-session plan — continue from the verified state

> **Session 2026-10-06 (H48) — state at hand-off.** H48 is implemented, runs end to end
> (`PYTHONPATH=src ./venv47/bin/python scripts/build_h48.py --stage all [--source apex]`, 117–160 s) and
> produced the project's **most novel artifact so far** —
> `docs/downloads/gems47-h48-mscl-apex-192-28124px-20261006T202949Z-allfinite.tif`, 28,124 px,
> max equal-mass Jaccard **0.0095** against all 13 prior rasters (previous record 0.0457), format
> **21/21**. **The gate is closed**: it loses the SGMC-off-catalogue blocked frame (0.0878 vs 0.0989)
> and its split-conformal floor is **0.1149 at level 46.15 %** (cross-conformal, n=12, family m=7,
> k=6), below the live 0.2600 incumbent. Receipts: `evidence/h48_apex_build.json`,
> `evidence/h48_build.json`; site: `docs/index.html`, `docs/executive-summary.html#h48`,
> `docs/all-downloads.html`.
>
> **Ordered next actions for the H48 line.** (1) Do **not** spend a slot on the apex arm until either
> the frame disagreement or the certificate changes; if a slot is spent anywhere, spend it on the
> λ-probe (three scores recover T, F, K exactly by inverting `1/DTI(λ) = (alpha + beta*K/T)/lambda + ...`),
> which is strictly more informative per slot. (2) If the apex arm is to be certified rather than
> probed, **pre-declare the operating point** — a family of 1 is worth 92.31 % at n = 12 against
> 46.15 % for a family of 7 (IR-47-019). (3) The SGMC loss says the apex set is *not yet* a
> catalogue-adjacent mapper; the cheapest honest fix is an emission that keeps the lineage's proven
> coverage and adds apex dots only where the lineage has nothing within 300 m — but measure its
> Jaccard against the priors first, because that is the trap IR-47-017 documents. (4) Do not re-tune
> the belief model to make the apex arm look better: it is a similarity regressor (IR-47-016) and
> re-tuning it only re-selects the incumbent.
>
> **Known limitations carried forward.** Nothing has been scored (no portal credentials). The 12-13
> returned scalars are the only truth and they are partly nested thinnings of one field. The two local
> truth frames disagree. The 3DEP 1 m DEM remains unreachable from this sandbox.


> **Current state (2026-10-06 UTC): no eligible submission and no slot recommendation.** H47-B is a research-only TIFF; it lost to the fixed-seed random control on locked spatial blocks, and its assumption-conditional conformal lower floor was 0.0. The legacy d-cat/annulus TIFF is a delete-only subset of a published mask. Old 0.34912/0.34837 performance claims and the earlier 0.3345 rank-1 board snapshot are superseded. Do not repeat those claims.

## Ordered actions

1. **Keep the slot closed.** Do not upload either TIFF in `docs/downloads/`. H47-B's local format pass and low similarity to accessible artifacts do not establish scientific promotion.
2. **Establish authorized data provenance.** The official DrivenData data page is login-gated. If this work continues under an authorized entrant account, preserve the exact official feature, catalogue-label and sample-template bytes/hashes and compare them with the group-hosted `GEMSDOE24` mirror. Do not bypass login. The current H47-B report is explicitly based on mirror files.
3. **Build a comparable incumbent.** No artifact-authenticated, comparable spatially blocked “current best” has been established. Build and save a reproducible baseline plus fold report with the official task formula, adequate truth counts and disjoint guarded spatial cores. Do not treat leaderboard scores or the historical TIFF as an incumbent.
4. **Resolve next-candidate feasibility before coding.** First inspect official USGS QFFD geometry/metadata for H47-C and count its footprint coverage; the available local summary CSV is not trace geometry. If coverage is insufficient, assess official ASTER alteration polygons (H47-D) or INGENIOUS temporal well/spring records (H47-F), counting and mapping coverage before proposing implementation. Record licenses and source URLs.
5. **Rank and preregister a genuinely new detector.** State the physical signature, missing-catalogue rationale, known confounders, controls, exact inputs/hashes, split assignment, mass, metric and promotion gate. Do not tune on a locked block. H47-B's existing held-out data must not be recycled as an independent test for a re-tuned version.
6. **Run the full evaluation.** Compare against the current spatial holdout best and same-mass random/domain controls, report pooled and per-block DTI, label coverage, calibration assumptions and failure regions. No slot unless the predeclared rule passes.
7. **Audit the candidate file.** Build a new TIFF only from a promoted output; validate exact bytes/grid/range/nodata, assign a unique filename and note, and compare against accessible historical artifacts. Repeat the uniqueness check if new repositories or artifacts become visible; never claim global uniqueness from the current inventory.
8. **Update the site and release only after evidence.** Keep research downloads conspicuously labeled. A distinct, newly promoted candidate may be linked at the top only after full review; H47-B itself must remain research-only and must never be renamed or relabeled as a submission. Submit manually through an authorized portal account and retain the organizer receipt.
9. **Delivery gate.** Complete the three review passes, full test suite, Ruff, local HTML-link checks, and GitHub CI. Open/merge a PR only when all evidence and wording are consistent. This repository never submits automatically and does not monitor the leaderboard.

## Current source boundaries

- **Official pages reviewed:** DrivenData problem/data/rules/leaderboard pages; USGS GeoDAWN, QFFD, 3DEP, ASTER; DOE INGENIOUS; NASA/USGS sources listed in [`sources.md`](sources.md).
- **Not directly acquired here:** official raw GeoDAWN archives and authenticated competition inputs. H47-B used a public owner-hosted mirror.
- **No authenticated file-to-score receipt:** public participant rows, including 0.2778, do not identify a TIFF.
- **Latest saved public-board observation:** rank 1 = 0.3774 (name not retained); DARD = 0.3195/#7; `extradr19` = 0.2778/#13. The old 0.3345/#1 snapshot is stale. No automated monitoring.
- **Current bounded uniqueness finding:** H47-B had zero exact positive-mask matches among 334 exact-grid rasters from 55 visible sibling repositories; maximum equal-mass Jaccard 0.01119. The full inventory and comparison rows are in the linked JSON audit. It is not a global uniqueness claim or submission authorization.

## Continue from these files

- [`validation-h47b-20261006.md`](validation-h47b-20261006.md), [`h47b-screen-report-20261006.json`](h47b-screen-report-20261006.json), and [`h47b-uniqueness-audit-20261006.json`](h47b-uniqueness-audit-20261006.json)
- [`preregistered-h2.md`](preregistered-h2.md) — frozen H47-B protocol
- [`hypotheses.md`](hypotheses.md) — original candidate ranking plus post-screen status
- [`irregularities.md`](irregularities.md) — open evidence flags
- [`sources.md`](sources.md) — official and secondary provenance
- [`README.md`](../README.md) — standing charter and current decision
