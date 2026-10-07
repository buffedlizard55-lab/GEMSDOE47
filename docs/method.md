# Current method — H47-C1

See the [full readable method](method.html), [frozen preregistration](research/h47c-hypotheses-preregistered.md)
and [actual screen receipt](data/profile-screen.json). This supersedes the legacy annulus/LATI release advice.

- Four cross-directions, 13 samples, affine-detrended odd erf step versus even Gaussian channel/ridge.
  Widths 1/2 sampling steps (100m axial, sqrt(2)*100m diagonal), not raw 1m morphology or ages.
- Raw19, raw+terrain26 and profile33 controlled HGB regressors; fixed settings and training-only targets.
  180,000 inverse-probability-weighted samples; positive-kernel cap 90,000. No prior mask/coordinate or
  catalogue-distance feature. Known catalogue labels are permitted training supervision only.
- 16×16 blocks/20px guards. Roles: 64 training, 21 selection, 21 calibration, 23 test. Valid support
  uses 41×41 raw validity minimum filter, not isfinite alone on finite float32-min sentinels.
- Five unit-dot spacings at matched quota. Selection/calibration frozen before test interpretation.
  Max-over-settings residuals; rank ceil(22×.9)=20, zero assumption-conditional lower-bound estimates. Selected 2.8px/280m; ordinary baseline 3.6px.
- Test pooled .177872 vs .180216 baseline, 11/22 block wins, 15 required; zero nominal-90% marginal lower-bound estimate under unverified exchangeability.
  No private/global/pooled/geographic-conditional guarantee. This is a public-catalogue re-screen, not
  pristine public labels or an organizer private test.
- Global 37,654-dot TIFF uses different quota allocation and excludes exact catalogue pixels; outside
  conformal target. Finite raw [0,1] plus internal validity mask; 15/15 local format checks, acceptance unknown.

All fit/field/history hashes and the technical selection-variable correction are preserved. This detector
is genuinely new inference, but not promoted. No weekly slot was used.
