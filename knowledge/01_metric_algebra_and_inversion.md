# Knowledge base 01 — metric algebra and conditional owner-reported scenarios

> **Historical scenario note:** Score/file associations in this legacy analysis are not organizer-authenticated. In particular, H33-2-B2 is not verified to participant DTI 0.2778. Treat every inversion using such pairs as hypothetical; this page does not establish private truth mass, causal gain, or that DTI 0.3195 is unreachable. See the corrected [attribution note](../docs/why-02778.md).

The metric identities below are algebraic; the historical score-derived examples are conditional on their unverified inputs. Reproduce
with `python3 scripts/run_inversion.py` → `evidence/inversion/live_anchor_inversion.json`, and
`python3 -m pytest tests/test_metric_s3.py -q`.

Source of truth: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric

---

## 1. The published metric

With R = 300 m = exactly 3.0 px at 100 m, α = 0.2, β = 0.8:

```
k(d)   = max(1 - d/R, 0)
TP_w   = Σ_{g∈G}  max_{x: d(x,g)≤R}  p(x)·k(d(x,g))
FP_w   = Σ_{x: p(x)>0}  p(x)·[1 - max_{g∈G} k(d(x,g))]
FN_w   = Σ_{g∈G}  [1 - max_{x: d(x,g)≤R} p(x)·k(d(x,g))]
DTI    = TP_w / (TP_w + α·FP_w + β·FN_w + ε)
```

Published worked example: `TP_w = 3.00, FP_w = 1.89, FN_w = 2.00 → "0.60"`. The exact value is
`3.00/4.978 = 0.6026516673…`; the page prints two decimals. Regression-tested.

**Lattice weights.** On the 100 m grid only these kernel values are ever realised:

| d (px) | 0 | 1 | √2 | 2 | √5 | 2√2 | 3 |
|---|---|---|---|---|---|---|---|
| k(d) | 1.000 | 0.667 | 0.529 | 0.333 | 0.255 | 0.057 | 0.000 |

---

## 2. Two exact identities

**(i) `FN_w = |G| − TP_w`.** Immediate from the definition, and it collapses DTI to three
scalars. With `T = TP_w`, `S = Σ_x p(x)`, `M = Σ_x p(x)·max_g k(d(x,g))`:

```
FP_w = S − M
DTI  = T / ( 0.2·(T + S − M) + 0.8·|G| )
```

Solving for `T`:

```
T = DTI · ( 0.2·(S − M) + 0.8·|G| ) / (1 − 0.2·DTI)
```

Both forms are proved in `tests/test_metric_s3.py` against `dti_bruteforce`, a literal O(|G|·|P|)
transcription of the published equations.

**(ii) `T ≥ M`, with equality iff every emitted pixel is the unique best cover of the truth it
hits.** Proof sketch: assign each emitted pixel `x` to the truth pixel `g*(x)` attaining
`max_g k(d(x,g))`. Then `M = Σ_x p(x)·k(d(x,g*(x)))`. Each `g` receives credit in `T` from its own
best pixel, which is at least as large as any pixel assigned to it, so summing over the assignment
partitions gives `T ≥ M`. This is why `M ≈ T` is a *conservative* simplification for a sparse
emission and not an arbitrary one.

---

## 3. The credit bar — the only decision rule that matters

Add one unit of mass at a pixel whose realised kernel weight against its best truth pixel is `w`,
and which becomes that truth pixel's best cover. Then `dT = w` and

```
d(denominator) = α·(dT + dFP_w) = α·(w + (1 − w)) = α = 0.2
```

so

```
dDTI > 0   ⟺   w > α·DTI = 0.2·DTI                                  (CREDIT BAR)
```

At DTI 0.2778 the bar is **0.0556**; against the lattice table that means a dot pays only within
**2.83 px = 283 m**, and only if it is the best cover.

**Redundant mass never helps.** A dot whose truth pixel is already better covered has `dT = 0` and
`d(denominator) = 0.2·(1 − w) ≥ 0`, which is exactly zero only at `w = 1`. Duplicating a trace is
free at best and costly otherwise.

> **Correction to a formula that circulated in earlier family repositories.** The bar is
> `α·DTI`, *not* `α·s/(1 − α·s)`. The latter does not follow from the metric and materially
> mis-prunes at s ≈ 0.27. `src/gems47s3/metric.py::credit_bar` implements the correct form and the
> module docstring records the error.

> **Correction to a test that was wrong.** An earlier assertion in this repository claimed
> redundant mass *always* hurts. It does not: `d(denominator) = 0.2·(1 − w)` is exactly zero at
> `w = 1`. The test is now named
> `test_redundant_mass_hurts_unless_it_sits_exactly_on_truth`.

> **Correction to a |G| floor formula.** The model-free floor denominator is `1 − DTI`, not
> `1 − 0.8·DTI`. All floors in `evidence/inversion/` were recomputed after the fix.

---

## 4. Binary is optimal — proof and consequence

For a pixel of value `v` whose best-cover weight is `w`: `dT = v·w`, `d(denominator) = α·v`. Hence

```
sign(dDTI) = sign( v·w·D − T·α·v ) = sign( w − α·T/D ) = sign( w − α·DTI/(1) )   (v cancels)
```

The **sign does not depend on `v`**. Down-weighting a pixel that clears the bar only shrinks its
positive contribution; up-weighting one that does not only enlarges the penalty. Therefore a
`{0,1}` mask is the optimum of the whole soft family, and a graded probability map is strictly worse
than its own thresholding.

This is tested numerically in `tests/test_metric_s3.py::test_binary_is_optimal_over_soft_scaling` and
matches practice: **all eleven scored reference artifacts are exactly `{0.0, 1.0}`** (verified by
reading every file — see `data/reference/README.md`).

---

## 5. Conditional hidden-truth calculations under unverified score/raster mappings

`S_active` = positive pixels inside the footprint and off the given catalogue (the only pixels that
can be scored).

| owner-supplied artifact | S_active | assumed DTI label (not organizer-authenticated) | conditional \|G\| bound | dots ≤2 px of catalogue |
|---|---|---|---|---|
| owner-supplied H33-2-B2 raster (score link unverified) | 37,654 | **assumed 0.2778 scenario** | 2,897 | **0** |
| `h27-4-r1` solo d2.8 | 40,199 | 0.2708 | 2,986 | 2,545 |
| `h33d` tip / step-over | 41,865 | 0.2632 | 2,991 | 3,894 |
| `h19-5` dotted d2.8 | 44,090 | 0.2600 | 3,098 | 6,436 |
| `d2.8` poisson off-catalogue | 44,090 | 0.2600 | 3,098 | 6,436 |
| `h19-5` dotted d1.5 | 60,069 | 0.2477 | 3,956 | 8,769 |
| topo gap-closure on d1.5 | 61,328 | 0.2449 | 3,978 | 8,875 |
| `h19-5` solid | 121,131 | 0.1922 | **5,764 ← binding** | 17,326 |
| `h30` arrangement-matched habitat | 91,533 | 0.1352 | 2,862 | 8,296 |
| `h34` scatter q50 arr-matched | 37,654 | 0.0778 | 635 | 0 |
| `h35-06` candidate | 39,530 | 0.0418 | 345 | 5,365 |

**Conditional algebra only.** If the owner-reported DTI labels are assumed to belong to these rasters, and `T ≤ |G|` and `M ≥ 0`,
`DTI ≤ T/(0.2·S) ≤ |G|/(0.2·S_active)` rearranges to

```
|G|  ≥  0.2 · DTI · S_active / (1 − DTI)
```

Under those assumptions, the solid-artifact row yields **|G| ≥ 5,764 px**; this is not a verified hidden-truth bound.

**Scenario upper bound.** The nested owner-supplied pair `h27-4-r1` ⊃ `h33-2-b2` gives, under `M ≈ T` and the unverified score/raster associations,
`ΔT = 85 − 0.0056·|G|`, and the assumed score differences imply a scenario upper bound `|G| ≤ 15,179` under the listed conditions. Monotonicity `T_solid ≥ T_d1.5 ≥ T_d2.8` yields weaker scenario bounds `|G| ≤ 37,838` and `|G| ≤ 69,694`. These are not measurements of hidden truth.

```
5,764  ≤  |G|  ≤  15,179 px           0.112 % ≤ prevalence ≤ 0.294 %
```

against a given-catalogue prevalence of 1.1803 %. These are scenario values, not an observed hidden-truth range or a validated prevalence bracket; they do not constrain the official holdout design or establish that the hidden truth is four to ten times sparser than the catalogue.

---

## 6. Byte-level geometry and conditional placement scenarios

The owner-supplied `h33-2-b2` and `h34-scatter-q50` rasters have **identical mass (37,654 px)** and an **identical catalogue-flank property (0 dots within 2 px)**. Under owner-reported score labels, a conditional algebraic comparison is **0.2778 vs 0.0778**; no organizer receipt maps either label to a TIFF.

Under `M ≈ T`: `T₁ = 2,092 + 0.2222·|G|`, `T₂ = 586 + 0.0622·|G|`. At |G| = 8,000 that is
`T₁ = 3,870` (48 % coverage) against `T₂ = 1,084` (14 %).

This conditional scenario does not establish a causal gain, authenticate the 0.2778 mapping, or falsify a hidden-truth distribution. It is a byte-level comparison plus an unverified score-association hypothesis.

---

## 7. Limits of the owner-reported 0.2778 scenario

At `S = 37,654`, `T ≈ 3,870`, `M ≤ T`, `|G| = 8,000`:

```
false-positive tax    0.2·(S − M)  ≈  6,757
earned credit         T            ≈  3,870
missed-fault penalty  0.8·(|G|−T)  ≈  3,304
                      DTI = 3,870 / 13,931 = 0.2778
```

**Within this illustrative scenario only**, the assumed false-positive tax exceeds the assumed credit. The counterfactual (`S → 9,675`, `M = T = 3,870`, `|G| = 8,000`) yields DTI ≈ **0.464** under those assumptions; it is not an observed score or a forecast, and it does not establish a causal pruning gain or a comparison with a current leader.

For completeness, the density trade-off under a *perfect* field (dots exactly on the trace, spacing
`s` along it, mean kernel weight over the covered truth pixels):

```
s = 2   →  DTI ≈ 0.862
s = 2.8 →  DTI ≈ 0.804
s = 3   →  DTI ≈ 0.714
s = 4   →  DTI ≈ 0.714
s = 6   →  DTI ≈ 0.556
```

So **for a perfect field denser is better**, and sparsity only pays through miss-removal. That is
why an exploratory sweep can inspect density in both directions from an owner-reported reference density. Any spacing choice must use the prespecified split-conformal proxy rule and report its nominal level and assumptions; it is not a private/global guarantee.

---

## 8. Published format and unresolved historical rejection

From the official page and from reading every scored reference artifact:

* single band, `float32`, EPSG:32611, 100 m, **3730 rows × 3292 cols**, transform
  `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`;
* values in **[0, 1]**;
* outside the footprint: "null or nan" per the page.

The earlier `"Predicted values must be in range [0, 1]"` error remains unexplained because the rejected bytes and parser receipt are unavailable. Local checks on current research TIFFs do not establish what the organizer parser accepted or why the earlier file was rejected:

1. **a value outside [0,1].** The official `training_features.tif` uses the float32 sentinel
   `-3.4028234663852886e38` for its 7,113,320 out-of-footprint cells. Any pipeline that carries a
   band value through unmasked, or normalises by a min that is the sentinel, writes it out.
2. **a `nodata` tag whose value is outside [0,1]** — `nan` or the sentinel. A validator can read the
   tag itself as a "predicted value".

A local inventory of owner-supplied sibling TIFFs records several `nodata=nan` rasters and other encodings; those owner-reported labels do not establish portal acceptance or map leaderboard rows to files. The published page allows null or NaN outside bounds. The current H47-C1 research TIFF has finite in-range interior values and an internal validity mask; its fifteen local read-back checks are not an organizer test. Unmasked all-finite zero-outside variants fail the explicit outside-nodata check. The original rejected bytes and parser receipt remain unavailable, so neither the exact cause nor acceptance of any variant is established.
