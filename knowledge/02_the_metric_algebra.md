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

## 4. The exact scale identity — a measurement device

Both `T` and `F` are homogeneous of degree 1 in `p`, so

```
DTI(λp) = λT / (λα(T + F) + βK)      ⇒      1/DTI(λ) is LINEAR in 1/λ
```

Three exact DTI returns from scaled versions of one fixed prediction would solve
for `T`, `F` and `K` in closed form, subject to the same target/mask and exact score
semantics:

* **S1 ANCHOR** — λ = 1, the selected prediction
* **S2 SCALE** — λ = 0.5
* **S3 NULL-ADD** — anchor plus N predictions placed where credit is expected to be
  near zero, so their marginal FP cost is approximately α·N

The algebraic conditioning estimate is **56×–1380×** better than solving from one
rounded four-decimal return in the analyzed setup. This is a measurement design,
not a submission recommendation: the predicted score ordering is not guaranteed
for private labels, and probes may consume upload allowance or affect which final
submission is selected. The probe set is designed but **not authorized or spent**;
verify current official rules and opportunity cost before any use.

## 5. Required recall for a target score

```
x = T/K = (αρ + β)/(1/DTI − α),     ρ = F/K
```

| Target DTI | x at ρ = 0 | x at ρ = 1 | x at ρ = 8.02 (incumbent) |
|---|---|---|---|
| 0.2600 | 21.94 % | 27.43 % | 82.42 % |
| 0.2708 | 22.90 % | 28.63 % | 86.03 % |
| 0.2778 | 23.53 % | 29.41 % | 88.49 % |
| **0.3195** | 27.30 % | 34.13 % | **102.73 % — impossible** |
| 0.3262 | 27.92 % | 34.90 % | **104.98 % — impossible** |

At the assumed incumbent waste ratio the 0.3195 target **cannot be reached in
this algebraic scenario** because the required weighted recall exceeds 100 %.
This is not a private-score forecast: the waste ratio and target score are
participant-history quantities, and the 2026-10-06 saved public snapshot placed
0.3195 at rank 7, not rank 1. The equation illustrates why reducing wasted mass
can matter; it does not show that any proposed detector will do so.

A perfect-knowledge ceiling follows only under the same scoring and coverage
assumptions. It should not be compared to the current leaderboard as a calibrated
prediction or used to infer what data the organizer evaluated.

## 6. Conditional arithmetic for the reported 0.2778 — attribution unresolved

The public leaderboard records a participant-level 0.2778 row, but not a TIFF hash
or upload receipt. The GEMSDOE32 owner page marks H33-2-B2 unscored, so the alleged
score/file mapping is contested. The table combines owner-reported values and
raster-derived counts; it is not proof that the H33 TIFF earned 0.2778.

If the mapping and metric interpretation were correct, reducing low-credit
emissions while retaining higher-credit mass could improve precision. That general
mechanism is consistent with the DTI equation, but it does not identify the cause
of a participant's score. Emitted mass along the reported family trajectory:

| Raster | Emitted px S | DTI | Covered 300 m kernel integral | Kernel credit retention |
|---|---|---|---|---|
| h19-5 solid backbone | 121,131 | 0.1922 | 449,693 | 1.000 |
| d1.5 (Poisson thin, 1.5 px) | 60,069 | 0.2477 | 383,645 | 0.854 |
| d2.8 (Poisson thin, 2.4 px) | 44,090 | **0.2600** | 341,261 | 0.759 |
| h27-4-r1-solo (rank-1 corroboration) | 40,199 | 0.2708 | — | — |
| h33-2-b2 (flank-pruned; mapping contested) | 37,654 | **0.2778 reported, not file-authenticated** | 302,510 | — |

Raster mass fell **69 %** from h19-5 to H33-2-B2 while the covered public-catalogue
kernel integral fell only **33 %**. This is a raster-derived coverage/mass comparison,
not proof that the score changed for that reason. H33's construction prunes a
2-pixel neighbourhood around the catalogue; that neighbourhood includes off-catalogue
pixels and should not be described as entirely masked. Local masking evidence supports
excluding known-catalogue cells before both sums, so deleting cells that are wholly
excluded would not change DTI. The contribution of nearby off-catalogue cells depends
on private truth credit, which is unavailable here.

**Conclusion:** precision is a plausible general explanation for a high score under
the metric, but the project cannot claim “H33 won because of precision” without a
file-level score receipt and confirmed evaluation semantics. See the attribution
caveat in `docs/analysis.md`.

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

**Trap C — boundary fill.** Shifting `1 − q` and filling out-of-grid positions
with `0.0` means `q = 1` there, i.e. *certain hidden truth beyond every border*.
That inflated `E[κ]` along all four edges and made the dense and sparse paths
disagree by 29 %. The fill must be `1.0`. (IR-47-014.)
