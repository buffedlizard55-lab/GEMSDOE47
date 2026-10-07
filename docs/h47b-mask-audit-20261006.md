# H47-B single-scale follow-up and footprint-mask audit — 2026-10-06

> **Historical research artifact only. NOT PROMOTED. Do not upload or spend a competition slot.**
> The site’s current primary research download remains H47-C1. This H47-B follow-up is linked only as a supplemental audit; it does not replace or alter the C1 page or receipt.

## Result first

The H47-B single-scale control was a negative candidate. On the local known-catalogue-mask proxy, its locked-test pooled DTI was **0.02563947**, below both the preceding H47-B cross-scale arm (**0.02755344**) and the fixed-seed random control (**0.03715911**). The mean of the five test-block DTI values was 0.01099731, also below random at 0.02181179. These are local diagnostic resemblance scores against known catalogue pixels—not scores for hidden missing faults and not leaderboard results. The organizer says known USGS/INGENIOUS fault pixels are masked from evaluation ([staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)).

The nominal split-conformal calculation used six calibration blocks at a selected 5-pixel / 500 m spacing: rank 6 of 6, nominal `6/7 ≈ 85.7%` marginal coverage **only under exchangeability of the block proxy scores**. Spatial exchangeability is unverified; two calibration blocks contain no catalogue-mask pixels; the clipped assumption-conditional lower-bound estimate is **0.0**. The finite-sample result follows [Lei et al. (2018)](https://arxiv.org/abs/1604.04173) and relies on exchangeability. It is not a guarantee about spatially dependent blocks, the global raster, private labels, or a competition score. No slot is authorized.

## Supplemental artifact

- **[Download the H47-B single-scale NaN-outside TIFF](downloads/gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-nanoutside.tif)** — 309,530 bytes; SHA-256 `dc71c807fbca2cd398f394bcd91b10ecec6b46fe89c2d61f5b1c058fef672811`.
- Single-band float32, 3292 × 3730, EPSG:32611, 100 m, transform `(243350, 100, 0, 4508550, 0, -100)`, 18,524 positive pixels, in-mask values in `[0,1]`, NaN outside the selected local footprint.
- The strict local read-back check **passes only with an explicit footprint mask derived from the mirrored `sample_submission.tif`**. It is a format check against that chosen local mask, not organizer acceptance or scientific validation.
- The paired all-finite diagnostic has the same positive mask, 257,898 bytes, SHA-256 `c640b71c7c57066dd77bbd42fcb6c436d0a8c201de6b0ec1d88ab25976089501`. It uses zeros outside and no NaN nodata tag, so it fails the strict NaN-outside check. It is retained to compare encodings, not as a candidate.

### The footprint discrepancy is unresolved

The mirrored `sample_submission.tif` and `labels.tif` each contain **5,167,373** valid cells. The validity mask inferred from `training_features.tif` contains **5,165,852** cells. A windowed comparison found **1,540 feature-valid cells outside** the sample/label footprint and **3,061 sample/label cells invalid in the feature raster**. Therefore the selected local validator mask is not interchangeable with the feature-derived mask. The authoritative organizer evaluation footprint and mask provenance remain unresolved; do not infer them from this mirror. The candidate does not pass strict validation when the feature-derived footprint is substituted.

Reproduction and counts: [machine-readable footprint comparison](data/h47b-footprint-comparison-20261006.json), [IR-23](irregularities.md), and the [mask reproduction script](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/arena/ccc6b8f7-gemsdoe47/scripts/build_footprint_mask.py). The exact original rejected upload and parser receipt are not available here. Consequently, the historical cause of the reported `"Predicted values must be in range [0, 1]"` error is **unknown**. The all-finite diagnostic illustrates a possible NaN-intolerant-check hazard; it does not prove what the organizer rejected or which nodata convention the portal accepts. Local validation never establishes portal acceptance.

## Bounded uniqueness—not a global claim

A bounded audit found zero exact positive-mask matches among **334 verified exact-grid sibling artifacts** and **19 independent local prior TIFFs**. The maximum equal-mass Jaccard was approximately **0.012905** in the remote comparison and **0.020550** in the local comparison. For the remote comparison, the verified all-finite companion was used to establish the same positive mask; the remote inventory was not refetched for the NaN-outside byte encoding. The paired diagnostic is not an independent prior model. This says nothing about unpublished, deleted, private, unindexed, or later-published artifacts, and does not establish geological novelty, performance, or portal eligibility. See the [deployed uniqueness receipt](data/h47b-candidate-uniqueness-20261006.json).

## Reproducibility and review trail

- The fuller H47-B cross-scale screen, frozen block roles, calibration arithmetic, controls, and its distinct superseded raster are documented in [`validation-h47b-20261006.md`](validation-h47b-20261006.md). Do not conflate the cross-scale arm with this single-scale control.
- Machine-readable screen and spacing results: [deployed audit JSON](data/h47b-conformal-spacing-audit-20261006.json).
- The artifact is separately listed in the [complete download register](all-downloads.html); the current C1 one-click download remains at the top of the [homepage](index.html) and [executive summary](executive-summary.html).
- The data used for the H47-B screen came from a public group-hosted mirror, not an authenticated organizer download. Hashes identify those local bytes; they do not authenticate provenance.

## Interpretation and next step

The H47-B single-scale TIFF is retained so its format, mask choice, hash, uniqueness scope, and negative control result are reviewable. It is not a scientifically validated discovery or slot-eligible submission. Keep it distinct from the newer H47-C1 research artifact and the separate H48 and Session 3 research. Do not change any of their current status or interpret cross-task proxy scores as comparable.