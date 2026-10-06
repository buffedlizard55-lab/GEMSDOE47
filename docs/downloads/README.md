# Download directory — research artifacts only

**No TIFF in this directory is submission-eligible. Do not upload any of them to DrivenData.** Eight TIFFs are retained: one site-linked primary research artifact, one same-mask diagnostic encoding, and six historical research files. The one-click file promoted on the site is a reproducibility artifact, not a recommendation.

## Current visible research artifact

- `gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-nanoutside.tif` — newly generated single-scale control; 18,524 binary predictions; 309,530 bytes; SHA-256 `dc71c807fbca2cd398f394bcd91b10ecec6b46fe89c2d61f5b1c058fef672811`. Strict local GeoTIFF validation passes against an explicit binary footprint derived from finite cells in the mirrored `sample_submission.tif`: one float32 band, EPSG:32611, 100 m grid, `[0,1]` on that mask, and NaN nodata/outside. **This is format validation only, not scientific validation or organizer acceptance.** The training-features-derived footprint disagrees with both the mirrored sample and labels (1,540 feature-only pixels; 3,061 template pixels invalid in features), so the authorized official evaluation footprint is unresolved. The candidate failed the known-catalogue-mask proxy screen against H47-B and random control; the proxy is not the hidden missing-fault target. See [`../analysis.md`](../analysis.md), [`../../evidence/conformal_spacing_audit_20261006.json`](../../evidence/conformal_spacing_audit_20261006.json), and [`../../docs/irregularities.md`](../irregularities.md).

## Same-mask diagnostic encoding

- `gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-allfinite.tif` — 257,898 bytes; SHA-256 `c640b71c7c57066dd77bbd42fcb6c436d0a8c201de6b0ec1d88ab25976089501`. Same positive prediction mask, encoded with zeros outside and no NaN nodata tag. It fails the strict NaN-outside validator and is retained only to investigate a possible NaN-intolerant portal range-check hazard; the historical portal error cause is unknown. It is not the visible/site-linked research artifact and must not be uploaded.

## Historical research files retained for audit

- `gems47-h47b-tmiup150-xscale-persist-n18524-research-not-submittable-20261006.tif` — earlier H47-B cross-scale raster; its locked local DTI is against the known-fault catalogue-mask proxy only. See [`../validation-h47b-20261006.md`](../validation-h47b-20261006.md).
- `gems47-dcat20-annulus-flankprune-n18524-20261006.tif` — delete-only subset of a published sibling mask; not an independent detector and not eligible under the no-copy requirement. See [`../analysis.md`](../analysis.md).
- `gems47-h47gsa-37654px-20261006T153105Z-0c44aea00e-allfinite.tif` and `gems47-h47gsa-37654px-20261006T153105Z-0c44aea00e-nan.tif` — earlier H47-GSA research variants.
- `gems47-h47maxcov-37654px-20261006T153105Z-fe9598facc-allfinite.tif` and `gems47-h47maxcov-37654px-20261006T153105Z-fe9598facc-nan.tif` — earlier maximum-coverage research variants.

Filename uniqueness and local GeoTIFF format checks do not establish scientific performance, organizer acceptance, or a score-to-file mapping. Keep research-only labels intact. Any future promoted artifact must be a distinct new prediction with its own preregistered hypothesis, exact-byte record, and independent holdout evidence; do not overwrite or relabel these files.
