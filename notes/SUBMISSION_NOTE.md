# Submission note status — 2026-10-06

> ## STOP — no portal submission is authorized
>
> There is no eligible submission in this repository. **Do not upload** either TIFF under `docs/downloads/`. H47-B is a research artifact that failed the preregistered holdout/control gate; the older d-cat/annulus TIFF is a delete-only subset of a published sibling mask. No submission slot is recommended.

## H47-B research artifact (not a portal file)

- **Research filename:** `gems47-h47b-tmiup150-xscale-persist-n18524-research-not-submittable-20261006.tif`
- **SHA-256:** `7e5df9d01689e438e8379ebd4763ed803de02e94826f43da37c33c16380d669b`
- **Local format audit:** one-band float32, EPSG:32611, 3292 × 3730, 100 m, GDAL transform `(243350, 100, 0, 4508550, 0, -100)`, 18,524 positive pixels, in-footprint values `[0,1]`, NaN outside.
- **Promotion status:** `NOT_PROMOTED`.
- **Locked-test pooled DTI:** H47-B 0.027553; single-scale baseline 0.025639; fixed-seed random 0.037159.
- **Conformal:** six calibration blocks, nominal 6/7 only under unverified exchangeability, clipped lower bound 0.0. No positive performance floor.
- **Uniqueness scope:** zero exact positive-mask matches among 334 accessible exact-grid TIFF artifacts in 55 visible sibling repositories; maximum equal-mass Jaccard 0.01119. This is not global uniqueness and does not overcome the failed gate.

Full protocol and results: [`docs/preregistered-h2.md`](../docs/preregistered-h2.md), [`docs/validation-h47b-20261006.md`](../docs/validation-h47b-20261006.md), and [`docs/h47b-screen-report-20261006.json`](../docs/h47b-screen-report-20261006.json).

## Retired claims

The former note claimed modeled DTI 0.34912 and a 0.34837 conformal floor at 75%. Both performance claims are withdrawn. The calibration rungs were selected from a monotone deletion family rather than demonstrated exchangeable calibration examples; the alleged 0.2778 file/score mapping was not organizer-authenticated; and the chosen prediction was a long extrapolation. See [`docs/analysis.md`](../docs/analysis.md) and the explicitly archived [`results-retired-unverified-20261006.json`](results-retired-unverified-20261006.json). Do not quote the retired values as current performance or a guarantee.

## Future portal note

No note is authorized for the current research TIFF. If a genuinely new candidate later passes the spatially blocked holdout, control, provenance, uniqueness, and exact-byte format gates, write a new short note tied to that exact output and receipt. Do not reuse a draft method description or claim any score without an organizer receipt linking the uploaded file hash to that score.
