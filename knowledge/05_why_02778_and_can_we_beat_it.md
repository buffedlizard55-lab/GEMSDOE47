# H33-2-B2 and the participant-level 0.2778 observation: limits and conditional algebra

> **Score-to-raster attribution is unverified.** The public leaderboard is participant-level; no organizer receipt maps its 0.2778 row to the H33-2-B2 TIFF. Owner-supplied mirror hashes establish bytes only. Do not claim H33 earned 0.2778, and do not treat any dependent calculation as authenticated or conclusive.

The earlier long-form analysis that described a causal gain from deleting catalogue-flank pixels has been withdrawn. A local subset relation between mirrored TIFF masks, if verified, establishes a geometric relation between those bytes—not which file received a participant score and not a causal score improvement. Deleting predictions exactly on masked pixels cannot by itself improve DTI; effects of removing nearby evaluated pixels require paired evaluation.

Use the term **owner-reported d2.8 reference** for the d2.8 raster and its comparisons. Reserve “incumbent” for a separately established spatially blocked holdout best.

For evaluated prediction mass `S`, weighted true credit `T`, false-positive mass `F`, evaluated truth count `K`, and `Φ` the maximum-kernel overlap term, the metric is

```text
F = S − Φ
DTI = T / (α(T + F) + βK),   α = 0.2, β = 0.8
```

At fixed truth/domain, pruning can help only if avoided false-positive cost exceeds lost weighted truth credit. This mathematical possibility does not establish the cause of any unverified historical score.

Keep `ρ=F/K` distinct from `f=F/T`. With `x=T/K`,

```text
ρ = F/K:  x = (αρ + β) / (1/DTI − α)
f = F/T:  x = β / (1/DTI − α(1 + f))
```

They are not interchangeable. `ρ=8.02` is illustrative, not an authenticated participant ratio; the equations do not show that DTI 0.3195 is unreachable. H47-SAF's tested sign change is bracketed only between assumed DTI 0.2200 and 0.2400, not an exact break-even. All H47-GSA artifacts remain research-only.

Three historical λ-scaling score observations are not a verified count of new uploads or slots. Public official pages checked 2026-10-06 do not establish current per-user quota or slot accounting; no diagnostic cost is inferred or called free.

See the corrected [0.2778 attribution note](../docs/why-02778.md), [metric knowledge](02_the_metric_algebra.md), and [standing README](../README.md).
