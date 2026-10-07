# Knowledge base 01 — exact DTI algebra and conditional score-label inversion

The metric algebra below is derived from the official formula and regression-tested. **Every score-to-file attribution in the historical inversion is owner-reported and unverified against an organizer receipt.** In particular, the H33 0.2778 label is not authenticated to its exact TIFF; see `knowledge/05_why_02778_and_can_we_beat_it.md` for the correction. Calculations in `evidence/inversion/live_anchor_inversion.json` that consume those labels are conditional sensitivity analyses, not observed scores or recovered hidden truth. Reproduce the algebra checks with `python3 -m pytest tests/test_metric_s3.py -q`; the old inversion script is not a score-authentication tool.

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
matches the locally restored historical reference files: **all eleven artifacts in the prior
corpus are exactly `{0.0, 1.0}`** (verified by reading every file — see `data/reference/README.md`).
This is a file-format observation, not authentication that the organizer scored those exact bytes.

---

## 5. What the old score-conditioned calculations can say

An earlier inversion used eleven owner-reported score labels alongside locally restored TIFFs. The formulas below are valid **only if** each reported label belongs to the exact raster bytes being measured. That mapping has not been proven by organizer receipts, and the pinned H33 owner record calls H33 unscored with 0.2747 projected. Therefore:

- Do not report the old `|G| ≥ 5,764` or `5,764 ≤ |G| ≤ 15,179` values as measured bounds on hidden truth.
- Do not interpret `dScore`, `nested_removal_analysis`, or inferred `T` values in `evidence/inversion/live_anchor_inversion.json` as measured effects.
- They may be retained as **what-if arithmetic** under the recorded assumptions, not as evidence that pruning raised a score.

The H33/H27 mask relation itself remains verified: H33 has 37,654 positives and is a strict subset of a 40,199-positive H27 parent; the 2,545 parent-only pixels all lie within 2 px of catalogue labels (1,201 at 1 px, 1,344 at 2 px). This is a statement about masks, not hidden truth. A different GEMSDOE27 all-increments TIFF has 41,507 positives and is not the parent. See the pinned sources and caveats in `knowledge/05_why_02778_and_can_we_beat_it.md`.

## 6. Same-mass comparisons are not score receipts

The H33 and H34 reference masks both contain 37,654 positive pixels, and their public owner materials carry different numeric labels (0.2778 and 0.0778). Without exact upload receipts, the labels cannot establish a three-point causal comparison, much less prove that coherent lineament placement explains a 3.6× organizer-score difference. The masks can still be compared on a public proxy, but that is a distinct experiment with its own truth-source limitations.

## 7. Marginal-credit arithmetic is a hypothesis generator, not hidden-label evidence

The credit-bar derivation in §3 is exact for an added unit of prediction mass under the metric. At a hypothetical DTI of 0.2778 it gives a break-even new kernel credit of 0.05556. It does **not** identify the true kernel credit of any removed H33 pixel. The official mask excludes catalogue pixels themselves, not an automatic 200 m neighborhood; a nearby off-catalogue prediction can still cover a hidden fault, while a non-matching prediction remains penalized. No hidden labels are available here to resolve those cases.

The old perfect-field density table and `T`/`|G|` inversion are idealized what-if calculations. They are not a leaderboard forecast, validated geological discovery, or reason to spend a weekly slot. Current H49 public-proxy results and its closed slot gate are reported in `docs/H49_RESULTS.md`.

---

## 8. Required output format and current internal-mask contract

The official format page specifies a single-band float32 GeoTIFF on EPSG:32611, 100 m grid, width 3292 × height 3730, bounds and transform matching the supplied grid, values in [0,1], and null/NaN outside the footprint. See the [official page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).

The current H49 writer uses a self-contained internal TIFF mask that exactly matches the supplied official footprint; masked reads are null exactly outside. The rebuilt `gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif` (SHA-256 `f2cec409ce3bec5a2805f1fab9a12ab7f72394f8be79cc365134ce43708c6060`) has one float32 band, the exact 3292 × 3730 EPSG:32611 grid/transform, and an internal mask equal to all 5,167,373 footprint cells. Raw samples are finite and in [0,1] across the entire grid (outside samples are zero), with no nodata tag, no sidecar and no second band. Read-back of the exact bytes passes all 19 gating checks plus the separate informational whole-grid-range flag; the earlier H49 copy failed the strict mask contract. This format pass does **not** establish scientific promotion, uniqueness outside the declared bounded audit scope, or organizer acceptance.
