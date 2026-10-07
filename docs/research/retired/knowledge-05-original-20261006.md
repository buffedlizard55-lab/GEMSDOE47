# Historical H33 attribution analysis — archived source

> **RETIRED / NOT VALIDATED.** Archived from the 2026-10-06 merge review. Its owner-reported score-to-TIFF associations, quota statements, causal interpretations, and upload/promotion advice were not verified and are withdrawn. The H33-2-B2 → 0.2778 mapping is unverified; dependent calculations are hypothetical only. Do not use this file to authorize a submission. The corrected current note is [`Historical H33 attribution analysis`](../../knowledge/05_why_02778_and_can_we_beat_it.md).

# Why GEMSDOE32 `h33-h33-2-b2` scored 0.2778, and whether it can be beaten

This is the PhD-level answer the standing brief asks for, and the design document the new
submission was built from. Every number below is reproducible:
`python3 scripts/run_inversion.py` → `evidence/inversion/live_anchor_inversion.json`, and
`python3 scripts/search_scarp_radius.py` → `evidence/scarp_radius_search.json`.

---

## 1. The artifact, exactly

`h33-2-b2` is not an independent model. It is **`h27-4-r1` minus a mask**, and the nesting is
exact:

```
h27-4-r1-solo-d2.8          40,199 positive px     scored 0.2708
  − dots within 2 px (200 m) of the given catalogue
                            −2,545 px
h33-2-b2                    37,654 positive px     scored 0.2778
```

Verified by set arithmetic on the two shipped rasters: 40,199 − 2,545 = 37,654, and the 37,654
pixels of `scored_h33-2-b2_0.2778.tif` are a strict subset of the 40,199 of
`scored_h27-4-d2.8_0.2708.tif`. **Deleting 6.3 % of the mass raised the score by 2.6 %.**

That single nested pair is a natural experiment with the organiser's own scoring function, and it
is worth more than any local proxy.

---

## 2. The mechanism, from the metric's algebra

With `T = TP_w`, `S = Σ_x p(x)`, `M = Σ_x p(x)·max_g k(d(x,g))` and `|G|` the number of hidden
truth pixels, the published DTI collapses exactly to

```
DTI = T / ( 0.2·(T + S − M) + 0.8·|G| )
```

because `FN_w = |G| − TP_w` identically (`tests/test_metric_s3.py` proves this against a brute-force
transcription of the published equations).

Two facts follow, and both are load-bearing.

**(a) The credit bar.** Adding one unit of prediction mass whose realised kernel weight is `w`, and
which becomes the sole best cover of a truth pixel, changes the denominator by exactly
`α = 0.2` and the numerator by `w`. So

```
dDTI > 0   ⟺   w > 0.2 · DTI
```

At DTI = 0.2778 the bar is **0.0556**. On the 100 m lattice the attainable weights are
`d = 0 → 1.000`, `1 → 0.667`, `√2 → 0.529`, `2 → 0.333`, `√5 → 0.255`, `2√2 → 0.057`, `3 → 0`.
So a dot only pays if it lands within **2.83 px = 283 m** of a hidden truth pixel *and* is that
pixel's best cover.

**(b) Redundant mass never helps.** A second dot whose truth pixel is already better covered
changes `T` by 0 and the denominator by `0.2·(1 − w) ≥ 0`, which is exactly 0 only at `w = 1`.
Duplicating a trace is free at best and costly otherwise. This is why spacing matters at all.

**Now apply (a) to the pruned dots.** Under the `M ≈ T` simplification (valid because `T ≥ M`
always, with equality when every emitted pixel is the unique best cover of the truth it hits —
proved by a Voronoi-partition argument in `src/gems47s3/metric.py`),

```
T_i = DTI_i · (0.2·S_i + 0.8·|G|) / (1 − 0.2·DTI_i)
```

gives `T_parent = 2,177` for `h27-4-r1` and `T_child = 2,092` for `h33-2-b2` at `|G| = 8,000`.
The 2,545 deleted dots therefore carried `ΔT = 85 − 0.0056·|G|` credit between them, i.e. a **mean
credit per deleted dot of at most 0.0334** at the model-free floor `|G| ≥ 5,764`, falling to zero
at `|G| ≈ 15,179`.

**0.0334 is below the 0.0556 bar.** Every one of those 2,545 dots was, on average,
value-destroying. The prune was not a lucky hyperparameter — it was the metric's own marginal rule
applied correctly, and the reason it worked is structural:

> The organiser **masks** the given catalogue's pixels out of evaluation (DrivenData staff,
> thread 11516 post #2, 2026-09-16). A dot on or beside a mapped trace can earn nothing, and
> post #4 of the same thread confirms there is **no buffer**: a predicted pixel near a known fault
> but far from new-fault truth is **fully penalised**.

So mass within 200 m of the catalogue is pure `0.2·(S − M)` tax with no possible `T`.

---

## 3. The second reason: 0.2778 is where the whole family's monotone trend ended

The family's public score history is a single, clean monotone sequence in emitted mass:

| artifact | positive px | public DTI |
|---|---|---|
| `h19-5-solid` | 121,131 | 0.1922 |
| `h30-arr-habitat` | 91,533 | 0.1352 |
| `topo-gap-d1.5` | 61,328 | 0.2449 |
| `h19-5-d1.5` | 60,069 | 0.2477 |
| `h19-5-d2.8` / `d28-poisson-offcat` | 44,090 | 0.2600 |
| `h33d-tip-stepover` | 41,865 | 0.2632 |
| `h27-4-d2.8` | 40,199 | 0.2708 |
| **`h33-2-b2`** | **37,654** | **0.2778** |
| `h34-scatter-q50` | 37,654 | 0.0778 |
| `h35-06` | 39,530 | 0.0418 |

Two things to read off this table.

1. **Sparsity paid, monotonically, and the family never pushed past 37,654 px.** From 121k to
   37.6k the score rose without a single reversal. The obvious extrapolation — go sparser still —
   was never tested. That is an unclaimed lever.
2. **Mass is not the mechanism.** `h34-scatter-q50` has *identical* mass (37,654 px) and an
   identical catalogue-flank property (0 dots within 2 px) and scores **0.0778** — 3.6× worse.
   Under `M ≈ T`, `T₁ = 2,092 + 0.2222·|G|` for `h33-2-b2` against `T₂ = 586 + 0.0622·|G|` for
   `h34`; at `|G| = 8,000` that is 3,870 credit (48 % coverage) against 1,084 (14 %).

   **Coherent lineament placement beats scattered placement by roughly 3.6× at identical cost.**
   This also falsifies a model the family used for live anchoring: that the hidden truth is a
   ~1.85 px scatter shell around the catalogue surface. A scatter shell would have rewarded
   `h34-scatter-q50`. It did not.

So the correct statement of *why 0.2778 won* is:

> **`h33-2-b2` sits at the intersection of the only two levers the family ever found — sparse
> emission and coherent lineament placement — and it is the only artifact that additionally removed
> the structurally worthless catalogue-flank mass. Its score is not a property of a better detector;
> it is the score of a mediocre detector that stopped paying tax.**

---

## 4. How big is the hidden truth? A model-free bracket

`FN_w = |G| − TP_w` and `TP_w ≤ |G|` give, for a binary prediction of mass `S`,

```
|G|  ≥  0.2 · DTI · S_active / (1 − DTI)
```

with `S_active` the positive pixels inside the footprint and off the catalogue. The most binding
artifact is `h19-5-solid` (DTI 0.1922, `S_active` 121,131):

```
|G| ≥ 0.2 × 0.1922 × 121,131 / 0.8078 = 5,764 px
```

Upper bounds come from monotonicity `T_solid ≥ T_d1.5 ≥ T_d2.8` plus the nested pair: the pair
gives **|G| ≤ 15,179**, the monotonicity chain gives |G| ≤ 37,838 and |G| ≤ 69,694.

```
5,764  ≤  |G|  ≤  15,179 px        on the public chunk
0.112 % ≤ prevalence ≤ 0.294 %     of the 5,167,373 px footprint
```

The given catalogue covers 1.1803 %. **The hidden truth is four to ten times sparser than the
catalogue.** Any holdout scored against full catalogue density therefore over-rewards dense
emission, which is exactly the error that made the family's solid surfaces score 0.19 where
thinned ones scored 0.26–0.28. This repository's holdout is prevalence-matched to the bracket for
that reason (`src/gems47s3/holdout.py`, `PREVALENCE_TARGETS`).

---

## 5. Can it be beaten? Yes — and the diagnosis says how

### 5.1 Where 0.2778 loses

At `S = 37,654`, `T ≈ 3,870`, `M ≤ T`, `|G| = 8,000`:

```
false-positive tax   0.2·(S − M)  ≈  6,757
earned credit        T            ≈  3,870
missed-fault penalty 0.8·(|G|−T)  ≈  3,304
                     DTI = 3,870 / 13,931 = 0.2778
```

**The tax exceeds the credit.** At most ~10 % of emitted dots hit truth at weight 1 (~26 % at mean
weight 0.4). The counterfactual is stark: keep the same hits, drop the misses
(`S → 9,675`, `M = T = 3,870`) and DTI ≈ **0.464** — far above the 0.3345 leader. That
counterfactual is not achievable (it assumes knowing which dots hit), but it locates the entire
opportunity in **precision**, not in coverage.

This is confirmed by the measured precision of the shipped artifact: the top 40,000 pixels of
`scored_h33-2-b2_0.2778.tif` have precision **0.1253** against SGMC off-catalogue fault and
**0.0607** against the given catalogue's 300 m halo — the latter *below* the 0.0861 random
baseline, which is the flank prune doing its job.

### 5.2 What this repository found that beats it

`scripts/search_scarp_radius.py` searched ten geomorphometric transforms × seven radii × five
bands and scored every candidate against the population the organiser actually scores —
expert-mapped Quaternary fault — with tie-aware statistics:

| candidate | precision@40k | precision@10k | tie-aware AUC | vs random 0.0861 |
|---|---|---|---|---|
| **`scarp(det_elev_slope, r=9)`** | **0.5049** | **0.6543** | **0.6183** | **5.9× / 7.6×** |
| `scarp(det_elev_slope, r=5)` | 0.4611 | 0.5859 | 0.6128 | 5.4× |
| `raw(geod_2ndinv)` regional prior | 0.3072 | — | 0.5583 | 3.6× |
| `scarp(det_elev_slope, r=13)` | 0.4691 | 0.6199 | 0.6158 | 5.4× |
| `lrm(det_elev_slope, r=9)` | 0.1059 | — | 0.5998 | 1.2× |
| every magnetic-band transform | 0.085–0.11 | — | ≈0.52 | ≈1.0× |
| shipped `h33-2-b2` artifact, top 40k | 0.1253 | — | 0.4988 | 1.5× |

`scarp` is an **across-strike** two-sided mean difference in the detrended-elevation *slope* field,
taken over a half-width of 9 px (900 m) and then **smoothed 19 px (1.9 km) along the strike**, with
the maximum taken over four strikes. It is the physically correct detector for a normal-fault
scarp — a straight, laterally persistent *step* — and it is the transform the family never tried:
prior work used curvature, openness and per-pixel ridge magnitude, which respond equally to canyon
rims, stream banks and alluvial-fan edges. The along-strike persistence requirement is what removes
those, and precision rises monotonically with persistence up to r=9 then turns over (r=13: 0.469,
r=17: 0.440, r=31: 0.388) — a clean interior optimum, not a boundary artefact.

Note what does **not** work: `det_elev` (as opposed to its slope) gives at best 0.0956, essentially
random, and every magnetic transform lands at 1.0–1.3× random. `scripts/diagnose_bands.py` explains
why: of the 19 bands only `tmi_vg` (high-frequency variance fraction 0.382), `det_elev_slope`
(0.181) and `tmi_hg` (0.175) carry structure at the metric's own 300 m scale. The other sixteen are
>96.5 % smooth above it and can only veto, never localise.

### 5.3 Measured on the holdout, against the same artifact

On the prevalence-matched, spatially-blocked holdout of `scripts/run_sweep_a.py` — whole catalogue
components held out inside contiguous blocks, the rest of the catalogue masked exactly as the
organiser masks it, exact DTI:

| instrument | truth prevalence | new field, mean DTI | shipped 0.2778 artifact, mean DTI |
|---|---|---|---|
| `PM0112` | 0.112 % (the \|G\| floor) | see `evidence/sweep/sweep_a.json` | 0.0031 |
| `PM0200` | 0.200 % (midpoint) | **0.082** | **0.0043** |
| `PM0294` | 0.294 % (the \|G\| ceiling) | 0.111 | 0.0041 |
| `A1` isolated components | 0.056–0.104 % | 0.065 | 0.0028 |
| `A2` flanking components | 0.35–0.90 % | 0.194 | 0.0060 |

The shipped artifact scores near zero on this instrument for a reason that must be stated plainly:
its dots were deliberately deleted from within 2 px of the *whole* catalogue, and the fold truth
*is* catalogue, so the instrument is measuring the artifact's designed anti-correlation with its own
truth (`IR-47-PROXY-02`). It is a valid comparison **only** for arms that do not prune near the
catalogue, and it is the reason the flank-buffer decision is justified from the organiser's nested
pair (§1) rather than from any local proxy.

### 5.4 The honest answer to "can we beat 0.2778?"

**Yes on the mechanism, with a caveat on the number.**

* The mechanism that produced 0.2778 — stop paying tax on catalogue-flank mass — is understood
  exactly and is reproducible from the metric's algebra. It is *not* a ceiling; it is a floor that
  any competent emitter clears.
* The mechanism that will produce a higher score is **precision of placement**, and the search above
  found a transform with 5.9× random precision at 40k against expert-mapped fault where the shipped
  artifact has 1.5×. That is a large, measured gap on the right population.
* The caveat: no local instrument can forecast the organiser's number, because the organiser's
  truth is a set of faults no public compilation contains, chosen by an expert panel for geothermal
  relevance. `PM*` folds are drawn from the catalogue and therefore measure *ordering*, not level.
  The claim this repository makes is a **relative** one — the new field dominates the shipped
  artifact on every prevalence-matched fold — and the conformal floor reported next to the chosen
  spacing is a floor on *that* instrument, labelled as such wherever it appears.
* What would actually settle it is one submission slot, spent only after the holdout gate the brief
  requires. That gate is implemented: `scripts/run_sweep_a.py` + `scripts/run_conformal.py` must
  both clear before `scripts/build_submission_s3.py` will emit a raster.

---

## 6. What was *not* the answer

Recorded so the next session does not re-spend the compute.

* **Fitting a truth model to the eleven published scores fails.** `scripts/fit_truth_model.py`
  built candidate truths from the SGMC and QFaults-prior off-catalogue pixels across a grid of
  sources × buffers × prevalence × smoothing × seeds and tried to reproduce all eleven organiser
  scores simultaneously. Best quick-grid RMSE **0.1449**, worst absolute error **0.1935**; the model
  under-predicts every high scorer by 0.12–0.19 and over-predicts `h30`/`h34`. Interpretation: the
  hidden truth is not a subset of any public compilation — it is expert LiDAR-mapped geometry absent
  from all of them. Use the algebraic bracket of §4 instead; do not spend more compute here.
* **Supervised detectors trained on the catalogue are a trap.** The metric masks catalogue pixels,
  so a model that reproduces the catalogue emits worthless mass. GEMSDOE26 `dilcond-oof` → 0.1223;
  the family's HGB → 0.0286. Everything must be framed as *off-catalogue* prediction.
* **External fault catalogues add nothing.** `knowledge/04` §1.5: of 59,065 QFaults-v2 pixels,
  exactly one is off-catalogue; of 58,251 INGENIOUS prior pixels, zero are.
* **Deep learning is not available here.** No GPU, 3 GB RAM. Hermant et al.'s siUNET needs 10 m DEM
  tiles and 7,700 label images; neither is obtainable in this environment.
* **The SGMC off-catalogue holdout is the wrong instrument.** `knowledge/02`. Selecting on it would
  have shipped `lrm(det_elev_slope, 9)`, a mountain detector with 1.2× random precision against the
  population that matters.
