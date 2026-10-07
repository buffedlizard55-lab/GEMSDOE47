# Exact competition DTI — useful reductions without hidden-truth overclaims

Source: [official performance metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric).
For this competition α=.2, β=.8, R=300 m / 3 pixels; k(d)=max(1−d/R,0).

## Exact components

```text
T = Σ_g max_x p(x) k(d(x,g))        weighted true credit
K = |G|                            evaluated truth-pixel count
S = Σ_x p(x)                       evaluated prediction mass
Φ = Σ_x p(x) max_g k(d(x,g))
F = S − Φ; FN = K − T
D = T / (.2 (T+F) + .8 K)
1/D = .2 + .2 F/T + .8 K/T          when T>0
```

Evaluate candidate and controls on the same truth/domain. Public catalogue holdout uses catalogue as
local proxy truth; official scoring excludes known pixels and uses unseen expert labels. Those are
not interchangeable targets. If G is empty, T=Φ=0, F=S, D=0. EDT on an empty truth mask must not
invent implicit exterior truth; a regression test covers that earlier bug.

## Exact finite-change rule at fixed truth

Provided both denominators are valid and K is unchanged:

```text
D(new)>D(old)  iff  ΔT (1−.2D(old)) − .2D(old) ΔF > 0
```

At D=0 any positive finite ΔT improves score. This avoids division by zero. Removing low-credit/high-FP
predictions can help; adding more dots does not automatically help. The lone-dot shortcut k>.2D applies
only when **ΔT=ΔΦ=k and ΔF=1−k**, not generally to fault lines.

## Why separated prediction dots do not justify T=Φ

A single prediction at the center of seven collinear truth pixels has T=3, Φ=1, S=1, F=0, K=7.
Exact D=3/(.2×3+.8×7); the shortcut 3/(.2×1+.8×7) is wrong. Prediction separation prevents overlap
between predicted supports; it does not prevent one dot crediting several truth pixels.

## Uniform scaling and non-identifiability

```text
D(λp) = λT / (.2λ(T+F)+.8K)
1/D(λp) = .2(1+F/T) + .8K/(λT)
```

For K,T>0 lowering λ lowers D. Even exact measurements identify ratios F/T and K/T, not absolute
T,F,K or a unique hidden map. Rounded, correlated/adaptive history with unverified file-score mapping
is even less identifying. The old λ-probe recommendation and “model-free K=12,348” claim are withdrawn. Three historical λ-scaling
score observations do not establish a count of new uploads or used slots, and do not establish a per-user
quota. Public official pages checked 2026-10-06 leave current quota/slot accounting unknown. No diagnostic
cost is inferred or called free; no slot is justified by an algebraic inversion experiment.

## What would be required to improve the reported 0.2778?

At fixed F,K, required credit ratio is
`T_target/T_base = [D_target/(1−.2D_target)]/[D_base/(1−.2D_base)]`.
That is about 16% extra weighted credit for .3195, and 39% for .3774. These are **conditional scenarios**,
not forecasts; hidden F,K,T are not established. Owner mass-pruning narratives plausibly explain a gain,
but the alleged H33/B2 .2778 filename/hash mapping is not organizer-authenticated.

## Conformal scope

A marginal prediction band for one future exchangeable block is not a confidence interval for pooled
DTI, nor a conditional geographic/private guarantee. Simultaneous max-residual calibration protects
five-setting choice only under its assumptions. C1's 21 calibration vectors yield rank 20 and **zero assumption-conditional lower-bound estimates
at every setting**; no difficult calibration block was discarded. The nominal 90% marginal statement
requires exchangeability, which is unverified.
