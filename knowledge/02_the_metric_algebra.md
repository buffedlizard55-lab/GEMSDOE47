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

The score can be expressed using two ratios, wasted-mass-to-credit `F/T` and
truth-size-to-credit `K/T`. Adding prediction mass changes both earned credit and
false-positive mass; whether that helps depends on the added pixels' marginal
credit, not on a blanket rule that more or less mass is always better.

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

Three **score observations** from one reference setup could, under the stated assumptions, solve for
`T`, `F` and `K` in closed form:

* **S1 ANCHOR** — λ = 1, a reference raster with an owner-reported 0.2600 score; the TIFF/score association is not authenticated
* **S2 SCALE** — λ = 0.5
* **S3 NULL-ADD** — the anchor plus N dots placed where no truth is expected, so
their marginal credit is approximately 0 and their cost is α·N

The algebraic design was checked against the metric implementation, but the experiment has **not** been
run. The three observations describe the measurement design, not a verified count of new portal uploads
or submission slots. The accessible official competition/rules pages checked 2026-10-06 do not state the
current per-user quota or slot accounting; the number and cost of any new uploads are unknown. Do not
assume a free route. H47-5 is **NOT AUTHORIZED** under the current holdout-before-slot gate. Do not
submit or run the portal probe without project approval and explicit organizer/portal confirmation.

## 5. Inverting the metric: name the denominator

Let `x = T/K` be weighted recall and `ρ = F/K` be false-positive mass per unit
truth mass. From the forward DTI equation,

```
1/DTI = α + (αρ + β)/x
x = T/K = (αρ + β)/(1/DTI − α),     ρ = F/K
```

This `ρ = F/K` is **not** `f = F/T`. If the ratio is instead stated as
`f = F/T`, the distinct identity is

```
1/DTI = α(1 + f) + β/x
x = T/K = β/[1/DTI − α(1 + f)]
```

The table below is a set of algebraic scenarios, not measurements of any
incumbent. In particular, the provenance of `ρ = 8.02` is unverified; it is
retained only to reproduce and correct the earlier illustrative column. Each
entry follows the inverse formula and was checked by substituting `T = x`,
`F = ρ`, `K = 1` into `dti_from_TFK()`.

| Target DTI | `T/K` at `ρ = F/K = 0` | at `ρ = 1` | at illustrative `ρ = 8.02` |
|---|---:|---:|---:|
| 0.2600 | 21.94 % | 27.43 % | 65.93 % |
| 0.2708 | 22.90 % | 28.63 % | 68.83 % |
| 0.2778 | 23.53 % | 29.41 % | 70.71 % |
| **0.3195** | **27.30 %** | **34.13 %** | **82.05 %** |
| 0.3262 (historical comparison) | 27.92 % | 34.90 % | 83.89 % |
| 0.3774 (latest saved rank-1 row, 2026-10-06) | 32.66 % | 40.82 % | 98.13 % |

Thus `ρ = 8.02` makes both 0.3195 and 0.3774 feasible under this model; it does
not establish that either is an incumbent's actual ratio. With `T/K ≤ 1`, the
largest feasible `F/K` at a target score is

```
ρ_max = (1/DTI − α − β)/α = (1/DTI − 1)/α   (when α + β = 1)
```

which is **10.6495** at DTI 0.3195 and **8.2485** at DTI 0.3774. At a fixed
`ρ = 8.02`, the model's maximum score at `T/K = 1` is about **0.3840**. With
perfect truth placement (`T = K`, `F = 0`), the DTI is **1.0**; there is no
0.78 “perfect-knowledge ceiling” implied by this equation.

For a separate illustration using `f = F/T`, DTI 0.3195 requires `T/K ≈ 60.16 %`
when `f = 8`, and `T/K ≈ 37.56 %` when `f = 4`. These are not the `ρ = F/K`
table entries. Neither calculation identifies the real ratios behind a
participant-level leaderboard score or maps that score to a TIFF.

## 6. Artifact descriptors are not a causal explanation of 0.2778

The following raster counts and covered-kernel integrals describe maps in the
recovered artifact family. They do **not** prove that a particular deletion
caused a DTI change. The alleged H33-2-B2-to-0.2778 association is unverified:
the public leaderboard records participant-level scores, not TIFF hashes or
filenames.

| Raster label in the artifact collection | Emitted px `S` | Reported/associated DTI* | Covered 300 m kernel integral | Kernel credit retention |
|---|---:|---:|---:|---:|
| h19-5 solid backbone | 121,131 | 0.1922 | 449,693 | 1.000 |
| d1.5 (Poisson thin, 1.5 px) | 60,069 | 0.2477 | 383,645 | 0.854 |
| d2.8 (Poisson thin, 2.4 px) | 44,090 | **0.2600** | 341,261 | 0.759 |
| h27-4-r1-solo (rank-1 corroboration) | 40,199 | 0.2708 | — | — |
| h33-2-b2 (flank-pruned; attribution contested) | 37,654 | **0.2778 not authenticated to this TIFF** | 302,510 | — |

Across those file descriptors, emitted count fell **69 %** from h19-5 to h33-2-b2
while the covered-kernel integral fell **33 %**. This is descriptive only: without
a verified score-to-file mapping and a controlled paired ablation on evaluated
pixels, it cannot explain a leaderboard improvement or establish what the hidden
truth contains.

**Masking correction.** Official DrivenData staff says known USGS/INGENIOUS fault
pixels are excluded from evaluation and do not count toward penalty terms
([thread 11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)).
Deleting predictions exactly on those masked pixels therefore cannot improve
DTI. A two-pixel pruning neighborhood also removes evaluated, unmasked pixels;
any effect of those pixels would need to be measured in a controlled ablation
on the evaluated domain. No such causal gain is established by the contested
H33 attribution.

Earlier notes called the `Hedge-v2`/`ens12` raster comparison a “natural experiment”; that label is
withdrawn. The rasters are byte-identical off the catalogue and differ on catalogue pixels, but the
0.1563 values are owner-reported and no organizer receipts link them to those exact files. The byte
comparison is descriptive, not an authenticated scoring experiment and not evidence of a causal gain
from deleting masked or nearby unmasked pixels. The official staff clarification in thread 11516 is
the basis for the stated masking rule.

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
