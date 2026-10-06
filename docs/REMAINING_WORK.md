---
title: Remaining work and limitations
layout: default
nav_order: 7
---

# Remaining work and limitations

Written as the brief requires: after the PR, list what is left and what this cannot do.
Nothing here is a hedge — each item is a specific, actionable gap with the reason it is open.

---

## A. Blocking: the submission has not been uploaded

**The GitHub token in this environment is invalid** (`gh api user` → `Bad credentials`;
`git push` → `Invalid username or token`). The two commits exist on the local branch
`arena/e1835de8-gemsdoe47` and the working tree is saved, but they could not be pushed, the pull
request could not be opened, and it could not be merged onto `main`.

**To finish:** reconnect GitHub in Arena, then

```bash
git push -u origin arena/e1835de8-gemsdoe47
gh pr create --base main --head arena/e1835de8-gemsdoe47 \
             --title "$(cat .github/PR_TITLE.txt)" --body-file .github/PR_BODY.md
gh pr merge --merge --delete-branch
```

`.github/PR_BODY.md` is the finished pull-request description. GitHub Pages then needs to be pointed
at `docs/` on `main` (repository → Settings → Pages → source: *Deploy from a branch*, folder
`/docs`); the site will be at `https://buffedlizard55-lab.github.io/GEMSDOE47/`.

**And the actual submission still has to be uploaded by a human**, because the DrivenData
submission form is login-gated and this environment holds no DrivenData credentials. The file,
its SHA-256, the submission name and the ≤200-character note are all on the front page of the
site; the click-by-click steps are in [HOW_TO_SUBMIT](HOW_TO_SUBMIT.md).

---

## B. Limitations of the result

### B1. The holdout cannot forecast the organiser's score — and that is not fixable locally

Every DTI in `evidence/sweep/sweep_a.json` is scored against **held-out components of the given
catalogue**. The organiser scores against faults that are *not* in the given catalogue, chosen by
an expert panel for geothermal relevance, from sources it will not disclose
(DrivenData thread 11527). So:

* the holdout is a valid **ordering** instrument (it ranks fields and operating points);
* it is **not** a level instrument (0.088 on `PM0200` does not mean 0.088 on the leaderboard);
* it is structurally invalid for arms that prune near the catalogue (`IR-47-PROXY-02`) — the
  shipped 0.2778 artifact scores 0.004 on it, below random, because its dots were deleted from
  exactly where the fold truth sits.

The conformal floor is a floor **on this instrument** and is labelled that way everywhere it
appears. No claim is made that 0.0134 is a floor on the public DTI.

### B2. The conformal guarantee is conditional on exchangeability, which geology violates

The theorem is exact *given* exchangeable units. The units here are spatial blocks, and the Basin
and Range is not i.i.d.: blocks differ in strain regime, basin-fill depth, exposure and mapping
history. Evidence that this bites:

* On the single pre-registered split the selection half violated the 90 % floor in **23 %** of
  blocks, against a nominal 10 %.
* Over 400 independent random splits of the same blocks the mean violation rate is **8.7 %**,
  i.e. correctly calibrated.

So the mis-coverage on the shipped split is **split luck**, not a failure of the theorem — but it
is a direct measurement of how much block heterogeneity there is. The number quoted on the site is
therefore the 5th percentile of the floor distribution over splits (0.01343) rather than the
single-split value (0.04477). A reviewer who wants the stronger number should read it as
conditional on one draw.

At α = 0.05 the bound is **vacuous** (needs n ≥ 19 usable calibration blocks; 12 are available).
No 95 % statement is made anywhere in this repository.

### B3. The emitted mass rests on an assumed coverage

The algebraic ceiling `S_max = G·(c/target − 0.8)/0.2` is model-free in `G` and `target` but
**assumes a coverage `c = T/|G|`**. At c = 0.60 and |G| = 8,000 the ceiling is 43,117 px and the
shipped 37,612 px sits under it. At the coverage the incumbent *demonstrably* achieved (c = 0.48)
the ceiling is 28,094 px — **below what was shipped**. If the new field's coverage is no better
than the incumbent's, the shipped mass is past the ceiling for the stated target.

This is the single largest open risk and it is quantified, not hidden: the full sensitivity table
is on the front page and in `evidence/conformal/selection.json → mass_ceiling`. A sparser variant
(`density 4.0` per 1000 → ≈20,400 px) is inside the ceiling at every coverage and every |G| in the
bracket, and costs about 15 % of holdout mean DTI. It is one flag away:

```bash
python3 scripts/build_submission_s3.py --name gemsdoe47-scarp9-sparse \
    --note "..." # then edit the density in the frozen selection, or re-run run_conformal.py
```

### B4. Five of the ten drafted hypotheses were refuted, and one of the survivors is unproven

`knowledge/06` records H47-B (magnetic braid number), H47-C (drainage-azimuth asymmetry), H47-D
as formulated (strain-partitioning Laplacian), H47-E (signed basement step) and H47-F
(corroboration count) as **refuted by measurement**, with numbers. H47-A (catalogue-vacancy
residual) survives as a weak-but-plausible gate; recipe `R5_scarp9_vacancy` tests it and it did
**not** win the sweep, so it is not in the shipped field. It remains untested at other gate powers
and scales.

### B5. No external data could be obtained, so the highest-leverage idea is untested

`knowledge/04` §1.1: the **GeoDAWN EarthMRI / 3DEP LiDAR** on the Open Energy Data Initiative is
the single highest-leverage acquisition available — H47-1 is the strongest signal in the shipped
stack *at 100 m on a detrended slope*, and Giddens & Faulds (2025) mapped the same structures from
1 m LiDAR across ~499,178 km². `data.openei.org` is unreachable from this sandbox and
`1m_DEM_links.csv` is login-gated, so it is recorded as **not viable here** rather than proposed
as if it were.

Also unobtainable: the 10 m 3DEP DEM, USGS SGMC bytes, NBMG Map 167 bytes, the GDR submissions
1391 and 1349. The six `derived_*` rasters in `data/reference/` are copies from earlier family
repositories; `/tmp` is not persisted, so if they are lost they must be re-derived from the named
public sources.

### B6. Band `tc` is ambiguous and is excluded on measurement

The raster metadata says *"Tilt angle **or** total curvature"*; the competition data page
describes a top-of-crustal magnetic source depth estimate. Different quantities, different units,
different signs (`IR-47-01`). Measured tie-aware AUC against the catalogue: **0.4476 — inverted**.
Excluded from every recipe. If the organiser clarifies which quantity it is, H47-B deserves a
re-test, because a true tilt-angle product *is* an edge detector and might behave differently.

### B7. Compute envelope

No GPU, ~3 GB RAM, 2 CPUs. A U-Net or FaultSEG run — the approach in the organisers' own reference
solution, and the one Hermant et al. show beats classical methods on PR-AUC (0.595 vs 0.449) — is
not possible here. The shipped field is entirely classical geomorphometry. That is a real ceiling
on what this repository can reach, and it is why the reference solution's architecture is cited
rather than reproduced.

---

## C. Remaining work, in priority order

| # | task | why it is next | cost |
|---|---|---|---|
| 1 | **Upload the TIF** and record the returned public DTI | it is the only instrument that can forecast the real score; everything else is ordering | 1 submission slot |
| 2 | Reconnect GitHub, push, open the PR from `.github/PR_BODY.md`, merge to `main`, enable Pages on `/docs` | the brief requires a merged PR and a live site | minutes |
| 3 | **Re-run the selector with the returned public DTI as a new anchor** | one real score collapses the \|G\|-and-coverage ambiguity in B3 far more than any local instrument can | `scripts/run_inversion.py` + `run_conformal.py`, ~10 min |
| 4 | Ship the sparse variant (density 4.0 → ≈20,400 px) as the *second* slot if the first under-performs | it is inside the algebraic ceiling at every coverage and every \|G\| in the bracket (B3) | one flag |
| 5 | Increase blocks to 8×8 so a 95 % bound stops being vacuous (B2) | n ≥ 19 usable calibration blocks | one sweep, ~50 min |
| 6 | Obtain GeoDAWN EarthMRI LiDAR and re-run the transform search at 1 m/10 m (B5) | largest single expected gain; H47-1 is already the best 100 m signal | network access + ~1 day |
| 7 | Re-test H47-A at other gate powers/scales, and H47-C on a real flow-accumulation DEM | both are plausible and unrefuted-at-other-settings (B4) | ~1 h |
| 8 | Add a *negative*-control field (shuffled ranks) to every sweep run | makes the lift numbers self-auditing instead of relying on a stored random baseline | ~20 lines |
| 9 | Ask the organiser to disambiguate band `tc` (B6) on the forum | cheap, and it either restores or permanently retires a whole band family | one post |
| 10 | Wire `scripts/build_site.py` into a GitHub Action so the site regenerates on every push | the brief asks the site to solve "manually checking everything"; a scheduled action would also refresh the leaderboard table | ~30 lines of YAML |

---

## D. What was verified, and how

So that "verify line by line" is a checkable claim rather than an assertion:

| claim | how it is checked | where |
|---|---|---|
| the three official rasters are the official bytes | SHA-256 + byte count against pins recorded from the official download | `scripts/fetch_data.py --verify-only`, `evidence/data_restoration.json` |
| the grid is the required grid | width/height/CRS/transform/band count asserted on every read | `src/gems47s3/grid.py::Grid._assert_grid` |
| the metric implementation is the published metric | brute-force O(\|G\|·\|P\|) transcription compared against the fast path; the published worked example reproduced to the printed 0.60 | `tests/test_metric_s3.py` |
| the algebraic identities hold | proved by test, including `FN_w = \|G\| − TP_w`, `T ≥ M`, and the credit bar | `tests/test_metric_s3.py` |
| binary beats soft | the `v`-cancellation argument tested numerically at five values of `v` | `tests/test_metric_s3.py::test_binary_is_optimal_over_soft_scaling` |
| the conformal quantile is the theorem's quantile | Monte-Carlo coverage at three α over 4,000 draws, plus an explicit regression test for the `k = ceil((n+1)α)` error that was found and fixed | `tests/test_conformal.py` |
| the emitter honours its spacing | pairwise distance of every emitted pair asserted at four spacings, for both the NMS and the Poisson-disk rule | `tests/test_emission_raster.py` |
| the scarp filter samples across strike, not along it | a step in each of the two orientations must be detected by its own normal | `tests/test_emission_raster.py::test_scarp_step_samples_across_strike_not_along_it` |
| the shipped raster is legal | re-opened from disk, 15 checks, fail-closed, receipt written | `src/gems47s3/raster.py::validate_submission`, `evidence/submission/checks-*.json` |
| the submission is unique | Jaccard and containment against all 18 reference artifacts, plus SHA-256 | `evidence/submission/bundle.json → uniqueness` |
| every number on the site is generated | the site is built by reading `evidence/*.json`; a missing receipt prints an explicit "not yet generated" line instead of a value | `scripts/build_site.py` |

**53 tests pass.** `python3 -m pytest tests/ -q`.
