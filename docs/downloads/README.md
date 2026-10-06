# Download directory — research artifacts only

**There is no submission-eligible TIFF in this directory. Do not upload any file here to DrivenData.**

| Artifact | Research status |
|---|---|
| `gems47-h47b-tmiup150-xscale-persist-n18524-research-not-submittable-20261006.tif` | H47-B. GeoTIFF format audit passed, but the preregistered spatial holdout/control gate failed; the conformal lower bound is zero under the stated conditional assumptions. Retained for research review only. See [`../validation-h47b-20261006.md`](../validation-h47b-20261006.md). |
| `gems47-h47gsa-37654px-20261006T153105Z-0c44aea00e-allfinite.tif` and `gems47-h47gsa-37654px-20261006T153105Z-0c44aea00e-nan.tif` | H47-GSA. The associated cross-fit is conditional on adding H33-2-B2 at an assumed DTI 0.2778; the score/file mapping is unverified. The observed paired deltas are negative in both folds. Not promoted. |
| `gems47-h47maxcov-37654px-20261006T153105Z-fe9598facc-allfinite.tif` and `gems47-h47maxcov-37654px-20261006T153105Z-fe9598facc-nan.tif` | H47-MAXCOV. Matched-budget re-emission of the owner-reported d2.8 reference field, not an independently validated detector; its LATI evidence shares the same conditional H33 scenario. Not promoted. |
| `gems47-dcat20-annulus-flankprune-n18524-20261006.tif` | Historical delete-only subset of a sibling mask; not an independent detector and not eligible under the unique-TIFF requirement. See [`../analysis.md`](../analysis.md). |

The all-finite and NaN files are diagnostic variants, not independent candidates. All-finite files write zeros outside the supplied footprint and do not satisfy the published null/NaN-outside wording; the NaN variant follows the available mirrored sample convention but fails a NaN-intolerant raw range comparison. Neither is recommended for upload or establishes portal acceptance. Being distinct from sampled files or matching a participant-level leaderboard score does not establish private-target performance or an authenticated score-to-file mapping. Keep the research labels and hashes intact. Any future promoted artifact must be a genuinely distinct prediction with its own hypothesis identity, must beat the established spatially blocked holdout best under the preregistered rule, and must pass the project gate before a portal slot is considered.
