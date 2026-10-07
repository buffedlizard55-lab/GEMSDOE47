> **Historical draft inherited from main; DO NOT use as the current PR body.** It contains stale merge shape, test counts, submission-readiness and score-attribution claims. See `README.md` and `docs/review-log.md` for the current project record.

---

## Merge shape — read this first

`main` had already absorbed **two prior sessions on this same brief**, and its recorded decision is
*"no submission is eligible and no slot is recommended"*. Its branch history is also **unrelated**
to this one (`git merge-base` returns nothing), so this is an `--allow-unrelated-histories` merge.
Nothing of main's is overwritten:

* **This session's package is namespaced** `src/gems47/` → **`src/gems47s3/`**; main's
  `src/gems47/` is untouched. Same for `tests/test_metric_s3.py`, `docs/hypotheses-s3.md`,
  `scripts/build_submission_s3.py`, `README-session3.md`.
* **`scripts/build_site_s3.py --check` asserts it**: all **44** of main's `docs/` files are
  byte-identical to `main`, and the one sanctioned change (`docs/index.html`) is verified
  *additive* — all 367 of main's lines survive in order, 47 added.
* The only content conflict in the whole merge was `.gitignore`, resolved as a documented union.
* **main's CI gates now pass on the merged tree**: `ruff check .` clean (195 errors in session-3
  code fixed, plus a `src/gems47s3/*` entry in `pyproject.toml`'s `per-file-ignores` mirroring
  main's `src/gems47/*` for the same stated reasons); `unittest discover -s tests` 68 tests OK;
  `pytest` **152 passed, 8 skipped**, including main's `tests/test_site.py` site-integrity suite,
  which session-3's pages are held to rather than exempted from.
* One pre-existing bug in main's suite fixed on the way: `tests/test_shipped.py::
  test_training_nodata_is_float32_min_not_nan` took no fixture, so it raised `RasterioIOError`
  instead of skipping in a data-less checkout. CI never saw it because CI names its test files
  explicitly. It now takes the module's `tmpl` guard like its siblings.

**main's gate status is unchanged by this PR.** The header badge on `docs/index.html` still reads
*GATE CLOSED — NO SUBMISSION RECOMMENDED*. Session 3's artifact is published as
**CONTROL-PASSED · NOT LATI-VALIDATED · NO SLOT RECOMMENDED YET**.

## The control that main's standard requires

Both prior gates closed on the same missing control, so session 3 ran it:
`scripts/control_random_and_shifted.py` → `evidence/control/controls.json`. At **matched mass,
matched spacing and matched flank buffer on identical folds**:

| frame | A: shipped dots | B: random field, identical emitter (20 seeds) | C: A translated 45–60 px | D: same mass, wrong places | A ÷ B | A > B |
|---|---|---|---|---|---|---|
| `PM0112` | **0.00908** | 0.00151 (sd 0.00106) | 0.00126 | 0.00195 | **6.02×** | 23/24 |
| `PM0200` | **0.01380** | 0.00224 (sd 0.00131) | 0.00193 | 0.00212 | **6.17×** | 24/25 |
| `PM0294` | **0.01497** | 0.00227 (sd 0.00115) | 0.00210 | 0.00235 | **6.61×** | 23/25 |
| `A1` isolated | **0.00857** | 0.00180 (sd 0.00093) | 0.00122 | 0.00185 | **4.75×** | 17/20 |

Arm C is the important one: it preserves the candidate's density and clustering and destroys only
its *alignment* with the geology, so A ≫ C means the placement is doing work and not merely the
dot count. `A1` is the cleanest frame — isolated components are by construction >3 px from the rest
of the catalogue, so the flank prune cannot be anti-correlated with the truth there.

**`IR-47-CODE-09`: the first run of this control reported the opposite result and was wrong.** It
pruned the controls against the *visible* catalogue while the shipped raster had been pruned
against the *full* catalogue, so the controls could place dots within 2 px of the fold truth and
the candidate structurally could not. It reported A/B = 0.28–0.31 — *"loses to random by 3.5×"*,
which is exactly how main's H47-B died (0.02755 vs 0.03716). Fixing the asymmetry reversed the
verdict. Both runs are recorded in the script's docstring and the commit message, because a
reviewer seeing only one of them would reach the opposite conclusion about the same bytes.

**Why no slot is recommended anyway.** The candidate has not been through main's promotion
instrument: cross-fitted LATI with paired out-of-fold deltas against the incumbent on all five
truth frames. Its own holdout shows the optimizer's-curse signature — calibration mean 0.0968
against a selection mean of 0.0606, a 37 % out-of-fold drop. It stays positive, which H47-GSA did
not, but a positive drop is not a promotion. It also inherits main's ceiling: same 100 m layers
that forty-four repositories converged on at 0.26–0.28, and a 0.5–3 m scarp averaged into a 100 m
pixel is below the noise floor of the resampled product.

## Corrections adopted from main

* Public leaderboard rank 1 is **0.3774** (main's later same-date read), not the 0.3345 this
  session started from. Both are recorded rather than silently reconciled.
* `IR-47-002`: the attribution of 0.2778 to a specific TIFF is **contested**. Session 3's nesting
  arithmetic (40,199 − 2,545 = 37,654, verified as an exact subset) is a fact about the bytes, not
  proof of which bytes earned which score. `docs/why-02778.html` is labelled accordingly.
* `docs/_config.yml` was deleted: `docs/.nojekyll` is present, so Jekyll never runs and a config
  file there would imply a build that does not happen. Session-3 pages are rendered to HTML into
  main's existing skin instead.

---

## What this delivers

A **unique, format-verified GeoTIFF submission** for DrivenData competition 306 (DOE GEMS Prize,
GeoDAWN / NW Nevada), the evidence and code behind every number in it, and a GitHub Pages site
whose first screen is the download button.

| | |
|---|---|
| **File** | `docs/downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif` |
| **SHA-256** | `f3f840b7880b7540ac6260b6b791ea55b2a875646c28401b01960096dc2da291` |
| **Bytes** | 316,497 |
| **Submission name** | `gemsdoe47-scarp9-persistence-s2.8-d7.37-b2` |
| **`Note (optional)`** (152/200) | `Across-strike slope step persisted 1.9km; binary dots, 280m spacing, 200m off known-fault flanks; 37.6k px; spacing fixed by split conformal, 90% floor.` |
| **Positive pixels** | 37,612 (0.7279 % of the footprint) |
| **Format** | 1 band, float32, EPSG:32611, 3292 × 3730, transform `(100, 0, 243350, 0, -100, 4508550)`, **no nodata tag**, every one of the 12,279,160 cells finite and in [0,1], values exactly `{0.0, 1.0}` |
| **Uniqueness** | max Jaccard **0.0144** and max containment **0.0277** against all 18 reference artifacts (thresholds 0.5 / 0.9) |

## The field

`R2_scarp9_topo` — a weighted geometric mean (an AND, which buys the precision the metric's
0.2-per-unit false-positive tax makes the binding term) of four rank-scaled transforms of
`det_elev_slope`:

```
scarp(r=9)^3  *  curv(2.5)  *  detrend(2.5)  *  slope_var(5)
```

`scarp` is the across-strike two-sided mean difference, smoothed **1.9 km along the strike**,
maximised over four strikes. It is the physically correct detector for a normal-fault scarp — a
straight, laterally persistent *step* — and the along-strike persistence is what separates a scarp
from a canyon rim, a stream bank or an alluvial-fan edge, which is the documented false-positive
mode of fault-mapping models in this province (Hermant et al. 2025).

Measured precision of the top 40,000 pixels against expert-mapped Quaternary fault: **0.5049**
against a random baseline of **0.0861** (5.9×); at 10,000, **0.6543**. The shipped 0.2778 artifact
scores 0.0607 on the same statistic — *below* random, because it was deliberately flank-pruned.
The persistence radius is an interior optimum, not a boundary: r=5 → 0.4611, r=9 → **0.5049**,
r=13 → 0.4691, r=17 → 0.4403, r=31 → 0.3880.

## The operating point, and why it is not "the observed best"

Two hard pre-filters, declared in `scripts/run_conformal.py` before the sweep is read:

1. **Algebraic mass ceiling.** With `M = T` and coverage `c = T/|G|`,
   `DTI = cG/(0.2·S + 0.8·G)`, so `S_max(target, G, c) = G·(c/target − 0.8)/0.2`. At the stated
   target 0.3195, `|G| = 8,000` (inside the 5,764–15,179 bracket inverted from the organiser's own
   eleven published scores) and `c = 0.60`, `S_max = 43,117 px`. **90 of the 180 swept operating
   points emit past that ceiling and were dropped**: they are not risky, they are arithmetically
   incapable of reaching the target. The local holdout cannot see this, because its absolute DTI is
   depressed for unrelated reasons.
2. **Degenerate-fold filter.** Folds with truth < 50 px are dropped uniformly across every
   instrument and operating point.

Then a declared 50/50 mean-risk objective on the *worst* prevalence-matched instrument: the
organiser scores one chunk, which is a mass-weighted aggregate over many block-sized regions, so
the calibration **mean** is the estimator of the chunk score and the conformal **floor** is the
risk control. Ranking by the mean alone is the "observed best" trap; ranking by the floor alone
selects for density, because dense emission homogenises block outcomes and flatters the minimum —
while the ceiling makes dense emission pointless.

**Result: spacing 2.8 px (280 m), density 7.37 per 1000 scored px, catalogue flank buffer 2 px
(200 m)** — mean-risk 0.923, worst normalised mean 0.925, worst normalised floor 0.920, worst
instrument `PM0294`.

The emitted mass (37,612 px) is within 0.1 % of the incumbent's 37,654 px and the flank policy is
identical, so the comparison against 0.2778 isolates the field.

## Split conformal prediction

Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, *JASA* 113(523):1094–1111, 2018
([DOI](https://doi.org/10.1080/01621459.2017.1322365)). Unit of exchangeability: the **spatial
holdout block**. 25 blocks, whole catalogue components held out, 12 calibration / 13 selection,
split once before any scoring.

| | |
|---|---|
| certified 90 % floor, **split-robust** (5th percentile over 400 random splits) | **0.01343** |
| certified 90 % floor, single pre-registered split | 0.04477 |
| mean empirical violation rate over 400 splits | **0.0873** vs nominal α = 0.10 |
| 95 % floor | **vacuous** — needs n ≥ 19 usable calibration blocks; 12 available |

The single pre-registered split violated its own 90 % floor in 23 % of selection blocks. That is
reported rather than hidden, and diagnosed: over 400 independent splits of the same blocks the mean
violation rate is 8.7 %, i.e. correctly calibrated, so the mis-coverage is **split luck in one draw
of a high-variance block population**, not a failure of the theorem. Hence the quoted number is the
split-robust 5th percentile.

A separate measurement worth noting: the empirical violation rate falls monotonically with emitted
density (17.6 % at 2 per 1000 → **10.0 % at 24 and 40 per 1000**), because sparse emission makes
block outcomes geologically idiosyncratic and strains exchangeability. `evidence/conformal/calibration_audit.json`.

## The holdout, and what it cannot say

Prevalence-matched and spatially blocked. The organiser's own scores bracket the hidden truth at
**5,764 ≤ |G| ≤ 15,179 px**, a prevalence of 0.112–0.294 % — four to ten times *sparser* than the
given catalogue's 1.18 %. Folds are therefore subsampled by whole component to 0.112 %, 0.200 % and
0.294 % (`PM0112/PM0200/PM0294`); `A1` (isolated components) and `A2` (flanking components) are
reported as diagnostics.

| instrument | new field, calib mean | shipped 0.2778 artifact |
|---|---|---|
| `PM0112` | 0.0587 | 0.0031 |
| `PM0200` | **0.1040** | **0.0043** |
| `PM0294` | 0.1057 | 0.0041 |
| `A1` isolated | 0.0583 | 0.0028 |
| `A2` flanking | 0.1298 | 0.0060 |

The artifact's near-zero score is a property of the instrument, not of the artifact
(`IR-47-PROXY-02`): its dots were deleted from within 2 px of the *whole* catalogue and the fold
truth *is* catalogue. The instrument is valid for ordering and for arms that do not prune near the
catalogue; it is **not** a forecast of the public DTI, and no floor on this site is presented as one.

## Two decisions that came out of measurement rather than taste

* **The obvious off-catalogue proxy is a trap.** USGS SGMC traces > 300 m from the given catalogue
  (61,664 px, 2,077 components) are the only substantial real-fault population here that the
  catalogue lacks — and they are exposed mountain bedrock: median detrended elevation **+115 m** vs
  **−69 m** for the given catalogue, median `det_elev_slope` **13.0** vs **5.1**, median
  depth-to-basement **105 m** vs **321 m**. `height_only` reaches precision-at-40k **0.3325** on
  that target, beating every fault-specific transform tried. Selecting against it would have shipped
  `lrm(det_elev_slope, 9)` — best on SGMC (0.260), **1.2× random** against the population that
  matters. `knowledge/02`.
* **Adding external fault catalogues is worth zero.** Of 59,065 QFaults-v2 pixels in the footprint,
  exactly **1** lies more than 300 m from the given catalogue; of 58,251 INGENIOUS prior pixels,
  **0** do. The training labels already contain the newest public Quaternary compilation. This
  closes the research direction that occupied GEMSDOE22–32. `knowledge/04` §1.5.

## Bugs found and fixed during review (pass 2)

Recorded because each one would have silently corrupted a result:

| id | bug | effect if left |
|---|---|---|
| `IR-47-CODE-01` | `conformal_quantile` used `k = ceil((n+1)α)` and the k-th **smallest** value for the lower side | **over-stated the guarantee**; caught by Monte-Carlo coverage test |
| `IR-47-CODE-02` | `rank_scale` mapped ties to one value | whole plateaus collapsed to a single emitted pixel (283 px/block where ~2,000 were expected) |
| `IR-47-CODE-03` | `nms_disk` broke ties by 8-connected labelling | tied pixels at 1 < d ≤ min_dist both survived, violating the spacing constraint |
| `IR-47-CODE-04` | `t_scarp` sampled **along** the strike instead of across it; `t_openness` computed a mid-slope measure, not openness; `t_detrend` carried dead code | the winning transform would not have been found |
| `IR-47-CODE-05` | `run_inversion` nested-pair rows are filename strings, not dicts; and the \|G\|-floor denominator was `1 − 0.8·DTI` instead of `1 − DTI` | `TypeError`; and every \|G\| floor wrong |
| `IR-47-CODE-06` | the sweep's scored domain did not intersect `valid` | 3,073 footprint pixels carrying the float32 sentinel were emittable, and created tie plateaus |

## Irregularities flagged

`IR-47-01` band `tc` is described in the raster metadata as "Tilt angle **or** total curvature"
while the data page describes a magnetic source depth estimate; measured AUC 0.4476 (inverted) →
excluded. · `IR-47-02` the feature-valid domain and the submission footprint are not nested: 3,073
footprint pixels carry the sentinel in ≥1 band and 1,540 all-band-valid pixels lie outside the
footprint. · `IR-47-03` `h27-4-d2.8` holds 40,199 px here, not the 44,090 in earlier family
ledgers. · `IR-47-04` two SGMC copies differ (82,151 vs 83,593). · `IR-47-05` the brief's "0.3195
is the current highest" was rank 5 on 2026-10-06; the leader was **0.3345**. Both are carried.

## The format rejection, fixed

`"Predicted values must be in range [0, 1]"` has two distinct mechanisms, and both are closed:
(i) a value outside [0,1] — the official `training_features.tif` stores 7,113,320 out-of-footprint
cells as the float32 sentinel `-3.4028234663852886e38`; (ii) a `nodata` **tag** whose value is
outside [0,1] (`nan` or the sentinel), which a validator can read as a predicted value. The shipped
raster writes every cell as a finite float32 in [0,1] with **no nodata tag at all** — the
configuration shared by all six reference artifacts that never drew a format complaint.
`validate_submission` re-opens the written bytes (never trusting the in-memory array) and gates 15
checks fail-closed.

## Checks

* **53 tests pass** — `python3 -m pytest tests/ -q`
* all three official rasters match their SHA-256 pins — `python3 scripts/fetch_data.py --verify-only`
* the shipped TIF re-reads as 1 band float32 EPSG:32611 3292×3730, transform exact, nodata absent,
  all cells finite, min 0.0 / max 1.0, zero NaN, zero sentinel, values `{0,1}`, 37,612 positive px
* every number on every docs page is read out of `evidence/*.json` at build time by
  `scripts/build_site.py`; a missing receipt prints an explicit "not yet generated" line rather than
  a placeholder value

## Remaining work and limitations

`docs/REMAINING_WORK.md`. The headline: the submission has **not been uploaded** (the GitHub token
in this environment is invalid, and the DrivenData submission form is login-gated), and the largest
open risk is B3 — the mass ceiling assumes a coverage `c`; at the coverage the incumbent
demonstrably achieved (0.48) the ceiling is 28,094 px, *below* the 37,612 px shipped. A sparse
variant (density 4.0 → ≈20,400 px) is inside the ceiling at every coverage and every |G| in the
bracket and costs ~15 % of holdout mean DTI.
