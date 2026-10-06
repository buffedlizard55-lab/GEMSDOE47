# H47-A implementation note — screening score only

**State:** implementation added; **no GeoDAWN or competition raster was available to run it**. Unit tests use small synthetic arrays only. There is no geological result, calibration, holdout score, or submission file.

## Reproducible surface definition

`gemsdoe47/candidate.py` implements a deliberately small, inspectable first test:

1. Require the two magnetic grids (and optional two radiometric grids) to be pre-aligned exactly; no hidden reprojection or resampling occurs.
2. Compute centered finite-difference gradient magnitude and direction on valid pixels. Exclude the one-pixel stencil around nodata so a mask edge cannot be mistaken for a geological edge.
3. Normalize each acquisition's positive valid-pixel edge magnitude independently by its 99.5th percentile; clip the strongest values at 1. (Zero gradients are excluded so a very sparse edge field does not collapse to a zero scale.)
4. In each independent modality, take the weaker acquisition's normalized edge support and multiply by axial orientation agreement, `abs(cos(theta_A - theta_B))`. Reversed gradient sign therefore still represents the same unoriented lineament.
5. If both magnetic and radiometric pairs exist at a pixel, average their paired support. If only one modality is valid there, use that modality.
6. An optional flight-line-direction factor is `1 - penalty × alignment × normalized strength`. The default penalty is **0**; its value must be chosen only on locked training folds, never by leaderboard feedback.
7. Write NaN outside the joint valid gradient support. Output values are in `[0,1]` by construction but are **not calibrated probabilities** and are not suitable for submission without a separate model/holdout decision.

The full implementation, per-input robust scales and SHA-256 sidecar are in `gemsdoe47/candidate.py` and `scripts/build_h47a.py`. A typical local invocation after authorized data are obtained and explicitly aligned is:

```bash
python -m pip install -r requirements.txt
python scripts/build_h47a.py \
  --mag-a data/geodawn/area1_mag_aligned.tif \
  --mag-b data/geodawn/area2_mag_aligned.tif \
  --rad-a data/geodawn/area1_rad_aligned.tif \
  --rad-b data/geodawn/area2_rad_aligned.tif \
  --template data/ACTUAL_OFFICIAL_SAMPLE_FILENAME.tif \
  --out data/derived/h47a_screening.tif
```

Omit both `--rad-*` arguments when the radiometric pair is unavailable. The script fails if grids do not match; alignment parameters must be recorded in a separate source-preparation receipt before use. It writes only under ignored `data/` or `artifacts/` folders and tags the GeoTIFF `VALIDATION_STATUS=NOT_RUN`.

## Known scientific limits

- An edge in a magnetic/radiometric product can result from lithology, remanent magnetization, processing, a mosaic seam, or acquisition artifacts—not only a fault.
- Independent per-survey quantile scaling can elevate weak/noisy edges. The robust scale is a transparent heuristic, not physical calibration.
- One-pixel gradients are sensitive to noise and may miss broad, low-amplitude or non-linear structures.
- A line that happens to be parallel to a flight direction can be geological. The optional penalty is a control to test, not a justified default.
- H47-A requires actual valid overlap between acquisitions. Catalog text says surveys overlap; exact grid and competition-footprint coverage have not been computed.
- Spatial blocking the known public fault catalogue does not establish discovery of private expert faults. Final-round scoring can differ.

## Synthetic tests are not results

`tests/test_candidate.py` checks deterministic math properties: same-edge support, axial orientation, orthogonal-edge rejection, nodata suppression, and optional flight-line penalty. It does not contain Nevada observations and must never be presented as a score or evidence that H47-A works geologically.
