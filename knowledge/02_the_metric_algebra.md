# The DTI metric algebra — everything that follows from four published formulas

Reusable research base. All five reductions below are asserted in
`tests/test_metric.py` against a literal O(N²) transcription of the published
formulas and against the organiser's own worked example.

## 0. The published metric

```
k(d)   = max(1 − d/R, 0),                     R = 300 m  = 3 px at 100 m
TP_w   = Σ_{g∈G}    max_{x: d(x,g)≤R} p(x)·k(d(x,g))
FP_w   = Σ_{x:p(x)>0} p(x)·[1 − max_{g∈G} k(d(x,g))]
FN_w   = Σ_{g∈G}    [1 − max_{x: d(x,g)≤R} p(x)·k(d(x,g))]
DTI    = TP_w / (TP_w + α·FP_w + β·FN_w),     α = 0.2, β = 0.8
```

Worked example (page 967): a single vertical ground-truth line gives
TP_w = 3.00, FP_w = 1.89, FN_w = 2.00 → **0.60**.

## 1. The kernel, enumerated

25 integer pixel offsets have `k > 0` (those with `dy² + dx² ≤ 8`; `d = 3 px`
gives exactly 0 and contributes nothing):

| dy²+dx² | d (px) | k(d) | count | contribution |
|---|---|---|---|---|
| 0 | 0 | 1.000000 | 1 | 1.000000 |
| 1 | 1 | 0.666667 | 4 | 2.666667 |
| 2 | √2 | 0.528595 | 4 | 2.114382 |
| 4 | 2 | 0.333333 | 4 | 1.333333 |
| 5 | √5 | 0.254644 | 8 | 2.037152 |
| 8 | 2√2 | 0.057191 | 4 | 0.228764 |

**Σ k = 9.3802978105** — the maximum credit a single unit dot can deliver, and
therefore the bound `Σ_x κ(x) ≤ 9.3803·K`.

## 2. Two exact reductions

```
FN_w = K − T                                    (term-wise complements over g)
FP_w = S − Φ,   S = Σ_x p(x),  Φ = Σ_x p(x)·κ(x),  κ(x) = max_{g∈G} k(d(x,g))
```

`κ` is a **max over the truth set**, and `k` is decreasing, so `κ(x)` is simply the
kernel at the *nearest* truth pixel. Hence

```
DTI   = T / (α·(T + S − Φ) + β·K)               ← the design equation
1/DTI = α + α·(F/T) + β·(K/T)
```

Everything about this competition is contained in that second line: the score is
governed by **two ratios**, wasted-mass-to-credit `F/T` and truth-size-to-credit
`K/T`. Neither is improved by emitting more mass.

## 3. The marginal rule

```
d(DTI) > 0  ⇔  dT·(1/DTI − α) > α·dF
```

For the common case of one unit dot with `dT = k` and `dF = 1 − k` this collapses
to

```
k > α·DTI
```

| DTI | bar α·DTI | maximum paying distance |
|---|---|---|
| 0.2600 | 0.0520 | 2.844 px ≈ **284 m** |
| 0.2778 | 0.0556 | 2.833 px ≈ 283 m |
| 0.3195 | 0.0639 | 2.808 px ≈ 281 m |
| 0.3262 | 0.0652 | 2.804 px ≈ 280 m |

**A common error, propagated through several sibling repositories:** writing the
bar as `α·s/(1 − α·s)` = 0.0549 at s = 0.26. The correct value is `α·s` =
**0.0520**; the published form is **5.5 % too high**, so any emission threshold
built on it stops too early. (IR-47-010.)

## 4. Scale identity — offline algebra, not a submission plan

Under the displayed local DTI formula, with a fixed truth, mask, footprint and scorer, positive scaling
of a soft prediction gives `T(λp) = λT(p)` and `F(λp) = λF(p)`, while `K` is unchanged. Thus

```
DTI(λp) = λT / (λα(T + F) + βK)      ⇒      1/DTI(λ) is linear in 1/λ
```

Exact returns at multiple scales could identify these terms **if** the organizer uses the same formula,
masking, and scaling semantics. That scorer behavior and its private target are not available here. The
previous proposal to collect anchor/scale/null-add returns was a measurement idea—not a geological
detector—and is **not authorized for any competition slot**, even in an unlimited round. Do not assume
null-added pixels have zero marginal credit, do not claim the probe cannot lower a rank, and do not use
public score probes to imply private-set performance. Retain the identity for offline algebra only.

## 5. Required recall for a target score

```
x = T/K = (αρ + β)/(1/DTI − α),     ρ = F/K
```

| Target DTI | x at ρ = 0 | x at ρ = 1 | x at ρ = 8.02 (illustrative only) |
|---|---|---|---|
| 0.2600 | 21.94 % | 27.43 % | 65.93 % |
| 0.2708 | 22.90 % | 28.63 % | 68.83 % |
| 0.2778 (participant row; file unmapped) | 23.53 % | 29.41 % | 70.71 % |
| 0.3195 (public rank 7, one-time capture) | 27.30 % | 34.13 % | 82.05 % |
| 0.3262 (older #1 snapshot; superseded) | 27.92 % | 34.90 % | 83.89 % |
| **0.3774 (one-time public #1)** | **32.66 %** | **40.82 %** | **98.13 %** |

Here `ρ = F/K`; the 8.02 column is only an algebraic scenario, **not a verified current
incumbent ratio**. An earlier version mislabeled recall requirements at this ratio and claimed that
0.3195 required 102.73 % recall. That contradicts the displayed equation: for `ρ = 8.02`, it requires
82.05 %, while the one-time public leader reference 0.3774 requires 98.13 %. The earlier “impossible”
claim is retracted. A high required recall in a hypothetical ratio scenario is not a forecast; exact
private-target `T`, `F`, and `K` remain unknown.

The expression also has a mathematical ceiling as `T/K → ∞` at fixed `F/K`, but no fixed ceiling is
identified without a defensible hidden-target mass and false-positive ratio. Do not compare the public
leaderboard score to a fitted ceiling as if it were validated truth.

## 6. What can and cannot be inferred about a reported 0.2778

It is not a discovery, it is precision. Emitted mass along the family's
trajectory:

| Raster | Emitted px S | DTI | Covered 300 m kernel integral | Kernel credit retention |
|---|---|---|---|---|
| h19-5 solid backbone | 121,131 | 0.1922 | 449,693 | 1.000 |
| d1.5 (Poisson thin, 1.5 px) | 60,069 | 0.2477 | 383,645 | 0.854 |
| d2.8 (Poisson thin, 2.4 px) | 44,090 | **0.2600** | 341,261 | 0.759 |
| h27-4-r1-solo (rank-1 corroboration) | 40,199 | 0.2708 | — | — |
| h33-2-b2 (flank-pruned) | 37,654 | **0.2778** | 302,510 | — |

On the owner-reported lineage, mass fell **69 %** from h19-5 to the alleged h33-2-b2 while the covered kernel integral fell only **33 %**. This is consistent with sparse thinning retaining higher-credit pixels and improving precision relative to the emitted mass. However, the public 0.2778 participant row is not mapped to that TIFF by an organizer receipt; the H33-2-B2 owner page marks the file **UNSCORED**.

The owner-described final step removes dots within 2 px of the given catalogue. Under the working mask semantics in `knowledge/01_the_gems_target_population.md`, those dots are zeroed before both score sums; deleting only masked cells therefore cannot itself raise DTI. The attribution of the 0.2778 value to that operation is unsupported and may be false. The defensible interpretation is narrower: the reported family trajectory is compatible with thinning that removed low-marginal-credit **evaluated** mass faster than it removed kernel credit. Which exact file and operation produced the public 0.2778 score remains unresolved.

## 7. Two numerical traps in the expectation algebra

When the truth set is modelled as independent Bernoulli with intensity `q`:

```
E[κ(x)] = Σ_{j=1..6} k_j·(Q_{j−1}(x) − Q_j(x)),
Q_j(x)  = Π_{rings 1..j} Π_{δ∈ring} (1 − q(x+δ)),   Q_0 = 1
```

**Trap A — the first-order form is an upper bound, not an estimate.** Replacing
`max` by `sum` gives `Φ ≈ ⟨q, a⟩` with `a(x) = Σ_{y∈D} k(d(x,y))`. That is valid
only while `c(x) = Σ_y q(y)k(d(x,y)) ≪ 1`, and it is **unbounded** whereas
`κ ≤ 1` forces `Φ ≤ S`. Measured over-estimate: **+0.8 %** at q ~ 0.002,
**+7.8 %** at q ~ 0.02, **+87.4 %** at q ~ 0.2. On a concentrated belief field
with a dense emission it drove FP_w to **−47,502** and the predicted DTI to
**1.6459** — impossible for the real metric.

**Trap B — the ring-product form loses precision.** Subtracting nearly equal
products at q ~ 2e-3 lost ~2e-4 per pixel, which over 150,000 dots again pushed
FP_w negative (−28.2). Use the algebraically equivalent stable form

```
E[κ] = 1 − Σ_{m=1..6} (k_m − k_{m+1})·Q_m,     k_7 := 0
```

which only ever subtracts non-negative terms from 1, so `E[κ] ∈ [0,1]` by
construction. Validated against 600-draw Monte-Carlo at three densities
(z = −0.58, +0.28, −0.17).

**Trap C — boundary fill.** In the local proxy implementation, shifting `1 − q` and filling out-of-grid positions
with `0.0` artificially implied `q = 1` there. This was a boundary-handling bug, not evidence of real
hidden truth beyond the grid. It inflated `E[κ]` along all four edges and made dense/sparse calculations
disagree by 29 %. The corrected fill is `1.0`. (IR-47-014.)
