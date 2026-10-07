# What the 0.2778 H33 label does — and does not — establish

> **Conclusion:** the raster relationship is real; the score attribution is not authenticated to those exact bytes. It is not established that deleting the near-catalogue pixels raised an organizer score from 0.2708 to 0.2778. The previous claim that it was a “natural experiment with the organiser’s own scoring function” was too strong and is withdrawn here.

This note separates four questions that were previously conflated:

1. Do the H33 and H27-labelled rasters have the stated pixel relationship? **Yes, within the locally restored, hash-pinned files.**
2. Are the numeric public-score labels linked to those exact TIFF bytes by an organizer receipt? **No receipt has been found.**
3. Does the official DTI algebra make catalogue-flank pruning a plausible mechanism? **Yes, conditionally; it does not identify which dots match hidden truth.**
4. Does any of this establish an organizer score or justify a submission slot for H49? **No.**

## 1. Byte-level artifact audit

The restored H33 reference is byte-identical to a public `GEMSDOE32` zero-outside TIFF at the commit-pinned path below. Its SHA-256 is `c55bafc470054e8271d1cb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9` (37,654 positive pixels). The relevant H27 parent is **not** the separate 41,507-positive all-increments TIFF in `GEMSDOE27`; it is the 40,199-positive `GEMSDOE28` artifact with SHA-256 `2fc94a38d77f74d4f4ed1a97a83e7bb71a1ceea090515ec641e6681cc47c44c8`.

Set arithmetic on those exact-grid masks gives:

- Parent: 40,199 positive pixels.
- H33: 37,654 positive pixels.
- Parent-only: 2,545 pixels; H33-only: 0 pixels.
- Every removed parent pixel is within Euclidean distance ≤2 pixels (200 m at 100 m/pixel) of a given-catalogue label: 1,201 at exactly 1 pixel and 1,344 at exactly 2 pixels.
- Therefore the H33 mask is a strict subset of that parent mask. This proves the **mask transformation**, not that either mask earned a score.

| Item | Pinned identity / source | What it supports |
|---|---|---|
| H33 zero-outside TIFF | [`GEMSDOE32` path](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/b983924b57781edd29b8e249c4923bf33d9902f6/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) · SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9` | Public mirrored bytes and positive mask |
| H33 owner narrative | [`GEMSDOE32` README at the same commit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/b983924b57781edd29b8e249c4923bf33d9902f6/README.md) · recorded README SHA-256 `4b58a9f14d016d71906a7d07d4c9ce41079eb3f2f48187ed91e8020cafbb143a` | Secondary owner report; its H33 section calls the file **UNSCORED** and 0.2747 a projection |
| H27 parent | [`GEMSDOE28` downloadable parent](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/f0cffdfc672ee13702038e7c00224f1e578b446e/docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-allfinite.tif) · SHA-256 `2fc94a38d77f74d4f4ed1a97a83e7bb71a1ceea090515ec641e6681cc47c44c8` | Correct 40,199-positive parent used for the strict-subset test |
| Confusable H27 variant | `GEMSDOE27` all-increments TIFF, 41,507 positives | A different mask; not the parent in the calculation above |

The exact source paths, checksums and set comparison are preserved in `docs/data/h47b-candidate-uniqueness-20261006.json`, `evidence/h47b-uniqueness-audit-20261006.json`, and the pinned owner inventory `docs/data/prior-inventory-20261006.json`. Treat the H33 and parent SHA-256 values above as identities of public mirrors, not authenticated organizer upload/download receipts.

## 2. Score provenance: why the causal sentence is withdrawn

The number **0.2778** occurs as a public-leaderboard observation at rank 13 under participant `extradr19` in the saved board snapshot. The number **0.2708** also appears in historical owner narratives. No organizer submission receipt has been found that maps either number to the exact SHA-256-pinned raster above.

More importantly, the H33 owner README at the pinned commit describes its H33-2-B2 TIFF as **UNSCORED** and calls **0.2747 a projection**. The same owner README's audit notes that the GEMSDOE28 page itself says “NO GEMSDOE28 SCORE” and describes 0.2701 as a projection; it identifies a same-valued public-board entry for another participant as a coincidence, not a receipt. These owner statements are not organizer truth either, but they directly contradict treating the H33 filename label as authenticated scoring evidence.

So this statement is **not supported**:

> “Deleting 2,545 pixels raised the organizer score from 0.2708 to 0.2778.”

The defensible wording is:

> “The H33 reference mask is a 2,545-pixel subset of a 40,199-pixel H27 parent, with every removed pixel within 200 m of a catalogue label. Historical filenames/owner materials carry 0.2708 and 0.2778 labels, but the H33 owner record calls it unscored and no organizer receipt maps either score to these exact files. A score increase caused by the pruning is therefore an unverified hypothesis.”

`evidence/inversion/live_anchor_inversion.json` retains conditional calculations from the old analysis. Its `reported_public_dti`, `dScore` and “nested removal” quantities use owner-reported labels; they are not score receipts and must not be cited as a measured intervention. Its latent `T`/`|G|` inversions additionally assume the particular metric identity and model constraints declared in that JSON. They do not recover hidden truth or validate the score-to-file link.

## 3. What the official metric algebra does support

The official metric page publishes a triangular 300 m kernel, `k(d)=max(1-d/300m,0)`, and weighted TP, FP, FN terms. The repository transcription and brute-force regression test are in `src/gems47s3/metric.py` and `tests/test_metric_s3.py`; the official reference is [DrivenData’s performance metric page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric). The staff clarification says given-catalogue pixels are excluded exactly from evaluation and that there is **no buffer** around a known trace: a nearby prediction remains penalized unless it covers hidden new-fault truth ([official clarification, posts 2 and 4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)).

For a prediction `p` and hidden truth set `G`, write `T=TP_w`, `S=Σp`, and `M=Σ p(x) max_g k(d(x,g))`. Since `FN_w=|G|-T` and `FP_w=S-M`,

```
DTI = T / (0.2·(T + S − M) + 0.8·|G|).
```

If one adds one unit of prediction mass and it earns exactly a new kernel-weighted credit `w`, the denominator rises by 0.2. At a current DTI `s`, that single marginal addition improves the ratio only when `w > 0.2s`; for `s=0.2778`, the break-even weight is 0.05556. This is an **algebraic marginal condition**, not a claim that the 2,545 removed pixels have zero credit, not an estimate of their actual hidden-label hits, and not proof that the H33 edit caused a public score change.

The exact-catalogue mask does not automatically make every nearby pixel worthless. The removed H33 pixels are off the catalogue but close to it; some could still lie within 300 m of an unmapped fault. Without the hidden truth (or a score receipt), their individual `T`, `M` and marginal DTI contribution are unknown.

## 4. Revised scientific interpretation

The H33 mask is consistent with a potentially useful design idea: avoid spending prediction mass on neighborhoods of known faults when the target is *new* faults, while retaining coherent lineament structure. The metric's 0.2 FP weight explains why precision and unnecessary mass can matter. However:

- A strict subset relation says nothing about the hidden labels.
- The historical public score labels are not tied to these TIFF hashes.
- The score could change because the files, evaluated chunk, submission identity, or other pipeline details differ; the causal attribution cannot be isolated from the saved records.
- The H33 owner’s own record describes the candidate as unscored / projected.
- Public holdout comparisons are proxy results. Instrument B is built from SGMC, which contains lithologic contacts and other non-fault traces, and is not the organizer’s private target.
- H49’s selected mean-rule arm was adopted after reviewing results; the 400 re-partitions reuse the same 39 spatial blocks. The 90% paired-difference conformal lower bound versus the H33 reference is negative for both candidate arms. Do not spend a slot on H49.

Accordingly, the answer to **“why did H33 score 0.2778?”** is: the available evidence does not establish that this exact H33 TIFF received that score, so a causal explanation of the score is not currently possible. The best supported hypothesis is that reduced off-target mass may help under the published metric, but it needs a receipt-linked score or a prospectively locked spatial holdout to test.

## 5. Sources and reproducibility

- [Official competition overview and target](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Official metric and output-format rules](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official staff clarification on catalogue masking and no buffer](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)
- [Pinned `GEMSDOE32` owner README](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/b983924b57781edd29b8e249c4923bf33d9902f6/README.md) — secondary; explicitly calls H33 unscored and 0.2747 projected.
- [H33/H27 set-audit receipt](../docs/data/h47b-candidate-uniqueness-20261006.json) — byte/mask scope only.
- [H49 results and gate decision](../docs/H49_RESULTS.md) — public-proxy observations, selection caveats and no slot authorization.
- Recompute the local mask arithmetic only after restoring the pinned reference files; do not regenerate or overwrite any organizer score receipt, and do not promote conditional inversion values as observed scores.
