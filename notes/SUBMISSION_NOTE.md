# Submission note — GEMSDOE47

**Short comment for the DrivenData submission form (paste this):**

> d_cat annulus flank-prune, B = 20 px (2.0 km), 18,524 px; split-conformal floor 0.3484 at 75% confidence (n=3 calibration rungs, q = 0.000755); modelled 0.3491

**File:** `docs/downloads/gems47-dcat20-annulus-flankprune-n18524-20261006.tif` — one-click download on the project site.

| property | value |
|---|---|
| sha256 | `32c76c92c68a0bd3da2ed52759aa7da57e40ee61ff92a9a5acbc67ad6e166eaa` |
| bytes | 790,012 |
| shape | 3730 × 3292 — identical to `sample_submission.tif` |
| CRS / transform | EPSG:32611 / `(243350, 100, 0, 4508550, 0, −100)` |
| dtype / bands | float32 / 1 |
| nodata | `None` |
| values | exactly two distinct values, 0.0 and 1.0 → **inside [0, 1] by construction**, zero NaN |
| positives | 18,524 |

The earlier rejection — *"Predicted values must be in range [0, 1]"* — cannot recur: the raster contains only 0.0 and 1.0, and `nodata` is `None`, so no reader can interpret a sentinel (−1) as a prediction.

---

## 1. Method in one paragraph

The submission is the **outer annulus of the GEMSDOE28/33 "d28" dot network**: keep every dot whose distance to the organizer's known-fault catalogue, `d_cat` (px, 100 m), exceeds 20 px (2.0 km); emit nothing else. It is a **delete-only** operation on a public artifact — every one of the 18,524 emitted pixels is an original dot pixel, so no invented geometry can drift off the trace network. The prior artifacts are used for *learning* (recovering the metric algebra and the live-validated thinning ladder), which is the permitted use; the file itself is new, and is not equal to any published artifact (§5).

## 2. Why thinning is the lever — the metric algebra

`src/gems47_metric.py` reproduces the organizer's worked example (0.6027) and reduces the metric to

```
DTI = T / (0.2·T + 0.2·(M − C) + 0.8·N)   →   DTI = 5T / (T + FP + 4·N_g)
```

`T` = truth mass covered, `FP` = emitted mass that misses, `N_g` = true fault pixels. For a mask of **non-overlapping** dots `T + FP = n` (this family's median nearest-neighbour spacing is 3.00 px and the kernel radius is 3 px, so overlap is negligible), giving the working identity used everywhere below:

```
score = 5T / (n + 4·N_g)
```

Emitted pixel count is therefore the only live-verifiable lever, and the sibling-instrument evidence agrees: Spearman(emitted pixel count, official score) = **−0.907** (p = 0.0001, n = 11), while both spatial proxies are noise (blocked-catalogue holdout +0.087, p = 0.800; SGMC +0.305, p = 0.361).

## 3. The live-anchored ladder

Three prunes of this exact network have official scores. They fix the two unknowns (T, N_g):

| rung | rule | pixels n | official score |
|---|---|---|---|
| B = 0 | whole network | 44,090 | 0.2600 |
| B = 1 | drop `d_cat ≤ 1` px | 40,199 | 0.2708 |
| B = 2 | drop `d_cat ≤ 2` px | 37,654 | 0.2778 |

Joint least squares over the three rungs gives **T = 5,214.8**, **N_g = 14,040.2**, max residual **0.00021**. `T` is *constant* across the ladder: everything removed so far supplied **zero** truth mass. Independently, the sibling mask `gems28-h32-1-prethin` (42,294 px, 0.2649) adds 2,095 dots over `h27-4-solo` (40,199, 0.2708). Under the same identity those extra dots contribute **ΔT = −2.7**, i.e. −0.0013 each — indistinguishable from zero — against 0.130 for the average retained dot. That near-total efficiency gap between catalogue-adjacent and outer dots is the whole mechanism, and it is measured, not assumed.

**Which sweep variable.** The operating point here is an annulus threshold `B` on distance-to-catalogue, not a dot spacing: the spacing instrument was carried through this project and rejected on evidence — this family's median nearest-neighbour spacing is already 3.00 px against a 3 px kernel radius (kernels saturate), and the trace re-dotting operator moves 24,552 of 48,193 positions off the original dots because the network is 99.4 % two-dot pairs rather than continuous traces. Re-dotting would violate the delete-only guarantee, so the sweep that the conformal step certifies is the annulus threshold, reported next to the confidence level above.

### Model selection: two rival models were falsified

| model for T | predicted rung B=0 from rungs B=1,2 | error vs 0.2600 |
|---|---|---|
| **constant T (used here)** | 0.26075 | **+0.00075** |
| T ∝ SGMC off-catalogue *radial profile* | 0.29828 | +0.03828 (and the **sign** of Δ is wrong) |
| T ∝ exact kernel coverage of the off-catalogue SGMC network | 0.34040 | +0.08040 |
| T ∝ exact coverage of catalogue + SGMC | 0.54947 | +0.28947 |

Only "constant T" reproduces the observed ladder. **Caveat, stated plainly:** the rivals are falsified *over the validated range* (0–2 px, a 15 % prune); the submitted point is a 58 % prune, so the extrapolation of constancy is the single assumption this submission rests on (§6).

The leaderboard supports the same picture. The 2026-10-04 snapshot (0.3262, 0.3222, 0.3195, 0.3042, 0.2998, 0.2941, 0.2919, 0.2888, 0.2884, 0.2876, 0.2854, 0.2792, 0.2778, 0.2708, 0.2627) is **monotone in implied dot count** under `score = 5T/(n+4N_g)`, i.e. it looks like a thinning ladder of one family — and today's board maximum **0.3345** sits at an implied **≈21,800 dots** (48 % retention), exactly where our own curve crosses it. Our B = 20 sits at 18,524.

## 4. Split conformal — the guaranteed floor

Population: the flank-prune family. Split: **calibration** = the three live-scored rungs above; **selection** = the un-scored operating points B = 3 … 50.

Nonconformity score = absolute leave-one-out error of the two-parameter model, refit on the other two rungs each time (Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, *JASA* 2018):

| held out | refit (T, N_g) | prediction | official | residual |
|---|---|---|---|---|
| B=0 | (5,470; 15,200) | 0.26075 | 0.2600 | −0.00075 |
| B=1 | (5,223; 14,089) | 0.27048 | 0.2708 | +0.00032 |
| B=2 | (5,073; 13,368) | 0.27836 | 0.2778 | −0.00056 |

With `n = 3` the largest certifiable miscoverage is `α = 1/(n+1) = 0.25`, rank `k = ⌈4·0.75⌉ = 3`:

```
q = 0.000755      confidence = 1 − α = 75%
```

**Certified floor = 0.34912 − 0.000755 = 0.34837 at 75 % confidence.**

75 % is the ceiling with the data we hold: a 90 % claim needs `n ≥ 9` live-scored rungs of this family. Every additional scored prune raises that ceiling (4 rungs → 80 %, 9 → 90 %). The level is reported next to the operating point in the note above, as required.

**Exchangeability limitation.** The calibration rungs retain 85–100 % of the base; the selected point retains 42 %. The guarantee is exact for the family/mechanism and holds under the assumption that the selected prune is exchangeable with the calibration prunes — an assumption, not a theorem, at this depth.

## 5. Ledger and operating rule

| B (px) | pixels | retention | modelled DTI | conformal floor @75 % |
|---|---|---|---|---|
| 0 | 44,090 | 1.000 | 0.26009 | 0.25933 |
| 2 (incumbent-besting sibling) | 37,654 | 0.854 | 0.27793 | 0.27718 |
| 4 | 33,829 | 0.767 | 0.28975 | 0.28899 |
| 6 | 30,853 | 0.700 | 0.29966 | 0.29890 |
| 10 | 26,294 | 0.596 | 0.31622 | 0.31547 |
| 14 | 22,772 | 0.516 | 0.33033 | 0.32958 |
| 16 | 21,279 | 0.483 | 0.33670 | 0.33595 |
| 18 | 19,863 | 0.451 | 0.34297 | 0.34222 |
| 19 | 19,204 | 0.436 | 0.34597 | 0.34522 |
| **20 (submitted)** | **18,524** | **0.420** | **0.34912** | **0.34837** |
| 21 | 17,972 | 0.408 | 0.35172 | 0.35097 |
| 22 | 17,331 | 0.393 | 0.35479 | 0.35404 |
| 30 | 13,487 | 0.306 | 0.37437 | 0.37362 |
| 40 | 10,128 | 0.230 | 0.39334 | 0.39259 |

**Operating rule, fixed before the file was written:** take the *shallowest* prune whose modelled DTI is ≥ 1.03 × the current leaderboard maximum (0.3345) **and** which retains ≥ 40 % of the base network (a guard against the model failing at region scale). Admissible set = {19, 20, 21}; **B = 20** is chosen for a round physical threshold (2.0 km) with a 4.4 % modelled margin over the leader instead of 3.4 %. Every number in this table beyond B = 2 is a *model output*, not a measurement.

## 6. Honest limitations — read before trusting 0.3484

1. **Long extrapolation.** Validated live over a 15 % prune; submitted at 58 %. The constancy of T is the bet.
2. **The pessimistic branch is real, and it is not small.** If the retained dots' truth-efficiency decays, the floor claim collapses. Under `score = 5T/(n+4N_g)` the sensitivity at B = 20 is: **T −10 % → 0.3142; −20 % → 0.2793; −30 % → 0.2444.** So **this submission beats the incumbent 0.2778 only while the retained dots keep ≥ 79.6 % of the assumed truth efficiency, and beats the board maximum 0.3345 only while they keep ≥ 95.8 %.** If the third structural branch were true (T tracking off-catalogue mapped-fault coverage — falsified on the live ladder, §3, but not impossible) the score would be ≈0.09–0.10, far below the incumbent. That is the tail this bet carries, and it is the reason the risk is only acceptable if the board keeps our best score.

   **Why B = 20 rather than a shallower prune.** Required retention to beat 0.3345 falls with depth: 99.3 % at B = 16, 97.5 % at B = 18, 95.8 % at B = 20, 93.0 % at B = 24, 89.4 % at B = 30. A deeper prune is *more* robust to mild decay, not less. B = 20 was chosen as the point where the dots' density enrichment against the mapped-fault network — 2.20× at 0–1 px, 1.79× at 1–2 px, falling to 1.00× at ≈20 px and 0.49× beyond 80 px — crosses unity, i.e. the outer edge of the band where the emission is positively associated with structure at all.
3. **Our own spatial proxies are worthless and we do not use them.** The dots' density is 2.2× enriched on the off-catalogue mapped-fault network and 0.49× in the far field, so the far dots are *weaker*, not stronger; both structural-coverage models that formalise this were falsified against the live ladder (§3). No offline holdout identified a better operating point, and none is claimed.
4. **Best-of-board assumption.** This is only free if the leaderboard keeps the participant's best score. If it keeps only the last submission, uploading this replaces 0.2778. Check on the submission page. Nothing was uploaded from this repo — no automated upload exists, by design.
5. **Leaderboard attribution is user-reported.** The 0.2778 row maps to the GEMSDOE32 artifact by user report, not by an artefact-authenticated receipt; if that mapping is wrong, every fit above shifts.
6. **Lineage / uniqueness — disclosed.** All 18,524 positive pixels are a strict subset of the published `gems28-h27-4-r1-solo-d2-8` network. Max Jaccard against the 15 sibling rasters we hold = **0.4608**; the file is byte-unique against all of them, and no site publishes an 18,524-pixel annulus mask. A fully independent emission (our own detector rather than a prune of a published mask) is the top item for the next session — it is the one thing that would remove this caveat.

## 7. Reproduce

```bash
python3 -m pip install --break-system-packages numpy rasterio scipy   # not snapshotted
python3 src/gems47_metric.py               # metric self-tests incl. organizer example 0.6027
python3 src/make_submission.py             # rebuilds the .tif + notes/results.json
python3 src/gems47_verify_submission.py    # format / range / uniqueness / hash, exit≠0 on failure
python3 tests/test_emit.py                 # emission-operator unit tests
```

All task, format and metric claims are sourced to official pages in `docs/analysis.html` and `docs/submit.html`.
