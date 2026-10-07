# Historical method — H47-C1

> This page documents the earlier H47-C1 screen; it is not the current H49 prediction or a recommendation to submit. The current H49 artifact, evidence, closed slot gate and limitations are in [H49 results](H49_RESULTS.html), the [executive guide](executive-summary.html), and the [current receipt](data/current-artifact.json).

See the [full readable H47-C1 method](method.html), [frozen preregistration](research/h47c-hypotheses-preregistered.md)
and [historical screen receipt](data/profile-screen.json).

- Four cross-directions, 13 samples, affine-detrended odd erf step versus even Gaussian channel/ridge.
  Widths 1/2 sampling steps (100m axial, sqrt(2)*100m diagonal), not raw 1m morphology or ages.
- Raw19, raw+terrain26 and profile33 controlled HGB regressors; fixed settings and training-only targets.
  180,000 inverse-probability-weighted samples; positive-kernel cap 90,000. No prior mask/coordinate or
  catalogue-distance feature. Known catalogue labels are permitted training supervision only.
- 16×16 blocks/20px guards. Roles: 64 training, 21 selection, 21 calibration, 23 test. Valid support
  uses 41×41 raw validity minimum filter, not isfinite alone on finite float32-min sentinels.
- Five unit-dot spacings at matched quota. Selection/calibration frozen before test interpretation.
  Max-over-settings residuals; rank ceil(22×.9)=20, zero floors. Selected 2.8px/280m; ordinary baseline 3.6px.
- Test pooled .177872 vs .180216 baseline, 11/22 block wins, 15 required; zero nominal-90% marginal floor.
  No private/global/pooled/geographic-conditional guarantee. This is a public-catalogue re-screen, not
  pristine public labels or an organizer private test.
- The historical global 37,654-dot H47-C1 TIFF used a different quota allocation and excluded exact
  catalogue pixels; it was outside the reported conformal target. Its 15/15 local format checks apply
  only to those older bytes; they are not the H49 receipt or evidence of organizer acceptance.

All H47-C1 fit/field/history hashes and the technical selection-variable correction are preserved.
That screen was not promoted and used no weekly slot. The current H49 research output is assessed separately;
its slot gate is closed and its 19/19 gating format checks are recorded in the current-artifact receipt.
