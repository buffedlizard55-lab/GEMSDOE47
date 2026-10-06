# Knowledge base 01 — the metric's algebra, and what the organiser's own scores imply

Everything here is derived from the published metric and the eleven published scores. Reproduce
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

## 5. What the eleven published scores imply about the hidden truth

`S_active` = positive pixels inside the footprint and off the given catalogue (the only pixels that
can be scored).

| artifact | S_active | public DTI | model-free \|G\| floor | dots ≤2 px of catalogue |
|---|---|---|---|---|
| `h33-2-b2` flank prune | 37,654 | **0.2778** | 2,897 | **0** |
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

**Lower bound.** Since `T ≤ |G|` and `M ≥ 0`,
`DTI ≤ T/(0.2·S) ≤ |G|/(0.2·S_active)` rearranges to

```
|G|  ≥  0.2 · DTI · S_active / (1 − DTI)
```

Binding from the solid artifact: **|G| ≥ 5,764 px**.

**Upper bound.** The nested pair `h27-4-r1` ⊃ `h33-2-b2` gives, under `M ≈ T`,
`ΔT = 85 − 0.0056·|G|`, and the deleted dots' mean credit must be ≥ 0 for the deletion to have
*lost* nothing... the observed gain requires mean credit per deleted dot below the bar, which caps
`|G| ≤ 15,179`. Monotonicity `T_solid ≥ T_d1.5 ≥ T_d2.8` gives the weaker |G| ≤ 37,838 and
|G| ≤ 69,694.

```
5,764  ≤  |G|  ≤  15,179 px           0.112 % ≤ prevalence ≤ 0.294 %
```

against a given-catalogue prevalence of 1.1803 %. **The hidden truth is four to ten times sparser
than the catalogue.** This is the single number that most constrains holdout design, and it is why
`src/gems47s3/holdout.py` prevalence-matches its folds to exactly this bracket.

---

## 6. The natural experiment that identifies placement, not mass

`h33-2-b2` and `h34-scatter-q50` have **identical mass (37,654 px)** and an **identical
catalogue-flank property (0 dots within 2 px)**, and score **0.2778 vs 0.0778 — 3.6× apart**.

Under `M ≈ T`: `T₁ = 2,092 + 0.2222·|G|`, `T₂ = 586 + 0.0622·|G|`. At |G| = 8,000 that is
`T₁ = 3,870` (48 % coverage) against `T₂ = 1,084` (14 %).

**Coherent lineament placement beats scattered placement by ~3.6× at identical cost.** This also
falsifies the "hidden truth is a ~1.85 px scatter shell around the catalogue surface" model that
GEMSDOE32 used to build its live-anchored truth: a scatter shell would have rewarded
`h34-scatter-q50`, and it did not.

---

## 7. Where 0.2778 loses its score

At `S = 37,654`, `T ≈ 3,870`, `M ≤ T`, `|G| = 8,000`:

```
false-positive tax    0.2·(S − M)  ≈  6,757
earned credit         T            ≈  3,870
missed-fault penalty  0.8·(|G|−T)  ≈  3,304
                      DTI = 3,870 / 13,931 = 0.2778
```

**The tax exceeds the credit.** At most ~10 % of emitted dots hit truth at weight 1 (~26 % at mean
weight 0.4). The unachievable-but-instructive counterfactual — keep the same hits, drop every miss
(`S → 9,675`, `M = T = 3,870`, `|G| = 8,000`) — gives DTI ≈ **0.464**, far above the 0.3345
leader. The opportunity is entirely in **precision of placement**.

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
why the sweep in `scripts/run_sweep_a.py` explores density in *both* directions from the incumbent's
7.37 px per 1000, and why the operating point is chosen by a guaranteed floor rather than by the
observed best.

---

## 8. Required output format, and the rejection that had to be fixed

From the official page and from reading every scored reference artifact:

* single band, `float32`, EPSG:32611, 100 m, **3730 rows × 3292 cols**, transform
  `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`;
* values in **[0, 1]**;
* outside the footprint: "null or nan" per the page.

The portal error the brief asks to fix — `"Predicted values must be in range [0, 1]"` — has two
distinct mechanisms, and `src/gems47s3/raster.py` closes both:

1. **a value outside [0,1].** The official `training_features.tif` uses the float32 sentinel
   `-3.4028234663852886e38` for its 7,113,320 out-of-footprint cells. Any pipeline that carries a
   band value through unmasked, or normalises by a min that is the sentinel, writes it out.
2. **a `nodata` tag whose value is outside [0,1]** — `nan` or the sentinel. A validator can read the
   tag itself as a "predicted value".

Measured across the eleven scored artifacts: three carry `nodata=nan` and 7,111,787 NaN cells and
were still scored, one carries `nodata=0.0`, and the rest carry **no nodata tag at all** with every
cell finite. The shipped GEMSDOE47 raster uses the configuration shared by all six artifacts that
never drew a format complaint: **every one of the 12,279,160 cells finite and in [0,1], no nodata
tag, min exactly 0.0, max exactly 1.0.** `validate_submission` re-opens the written bytes — it never
trusts the in-memory array — and gates fifteen checks fail-closed, emitting a `checks-*.json`
receipt.
