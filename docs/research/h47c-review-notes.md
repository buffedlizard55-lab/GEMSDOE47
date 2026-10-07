# H47-C1 review corrections — preserve, do not erase, the first run

## Pass 1

Protocol and implementation were committed on the fixed session branch at
`cc14ad84fbace93bdd0c2a7bc8b520170e082bb3` **before** fitting/scoring. Synthetic mechanism,
rank, label-isolation and arithmetic tests passed. The screen completed on restored, hash-pinned
mirrors. No competition upload occurred.

## Pass 2 · selection-variable bug (IR-C1-001)

The calibration stage correctly selected **2.8 px** before any test scoring. However the later
`for spacing in SPACINGS` test loop overwrote the same Python variable with the last grid value,
**5.8 px**. The final gate and candidate mask incorrectly used 5.8 px. This was discovered by comparing
the pre-test lock log against the final report, **before a TIFF was published**.

The original run's report, full spacing history and block assignments are preserved under
`evidence/retired-profile-pass1/` with an explicit `retraction.json`. They are not eligible
validation results. No model, feature, target, sampling seed, split, spacing grid, confidence level,
fixed-baseline selection, or gate threshold has been changed in response to their scores.

Correction: rename the loop variable to `sweep_spacing`; assert that final spacing equals both the
recomputed conformal choice and the pre-test lock receipt; add the same check to the exporter.
Rerun the frozen screen. Compare all three prediction-field hashes and the score-history hash to the
superseded run: a control-flow correction must not alter trained predictions or per-setting scores.
This is a documented technical correction, not an independent second geological experiment.

## Other bugs found during repository review

- `src/gems47_metric.py` applied SciPy EDT to an empty truth set. EDT then measures to an implicit
  exterior pixel and invents near-corner false-positive relief. Empty truth now has exactly FP =
  prediction mass, TP = 0, DTI = 0; a regression test covers it.
- `src/gems47/hypotheses.py` used double-angle tensor coordinates as a strike vector and swapped
  row/column components in its dot product. Correct with half-angle `atan2` and `dx*tx + dy*ty`.
  Old orientation-specific evidence is not re-certified by this code correction.
- The marginal-gain helper incorrectly rejected positive credit at zero DTI. The non-singular exact
  condition is `dT*(1-alpha*DTI) - alpha*DTI*dF > 0`, including DTI = 0.
- Some documents and `ship.py` claimed unlimited separate Phase 2 submissions. Official pages checked
  2026-10-06 describe one selected file for both rounds but do not establish current per-user quota or slot
  accounting. Failed research arms must not be recommended for a fictional unlimited-submission phase; verify
  operative rules in the authenticated portal before any future action.
- The sparse-dot shortcut `DTI=T/(0.2*N+0.8*G)` is not generally exact. The exact denominator is
  `0.2*(T+S-Phi)+0.8*G`. A dot can cover several truth pixels, so `T` need not equal `Phi`, even when
  prediction supports do not overlap. A one-dot/seven-truth-pixel regression test demonstrates it.
- Mirrored band 6 describes `tc` as magnetic curvature, whereas the official overview includes
  radiometric counts. A sibling reports contractor-grid correlation consistent with counts. That
  sibling claim is not organizer authentication. The new physical hypothesis does not depend on
  resolving this ambiguity; generic raw-band baselines use the numerical column without claiming
  a physical interpretation. Band 15 also has conflicting basement/conductive-base descriptions.

## Pass 3 checklist (completed results appended after independent re-verification)

- Verify corrected lock, unchanged field/history fingerprints, held-out components, equal mass,
  all zero-truth blocks, conformal rank/assumptions and secondary target mismatch.
- Reopen the actual new TIFF and single-member ZIP; check range, internal mask, CRS, shape, transform,
  null outside the template footprint, exact prediction fingerprint and strict JSON receipts.
- Audit current accessible prior outputs at pinned repository commits/blobs. Low overlap is not proof
  of geological novelty; no exact match is only a bounded uniqueness finding.
- Test every new module in CI, not only the three legacy pytest files; verify all deployed links stay
  inside the Pages artifact or point to explicit GitHub/official external URLs.
- Refresh sources without inventing current data after a network/login/parser failure. Record last
  successful observation, last attempt, provenance class and timestamps separately.

## Pass 3 completed — 2026-10-06 UTC

Independent final recheck: 160 pytest tests + 2 subtests pass, no local skips; unittest 70/70; Ruff and
JS syntax clean; 16 grid checks; actual preview TIFF HTTP200 and SHA match; 15 serialized format checks.
Raw spacing CSV recomputes the rank/zero band, original 2.8px choice and failed gate. Current/archived
HTML links, assets and Pages deployment boundaries checked; home and summary offer the actual new TIFF
before the large introduction. All fitted field/history hashes unchanged across the technical correction.

Expanded CI initially tried a data-dependent legacy test without restoring data; corrected marker
selection, while real new TIFF/ZIP bytes still run in CI. Later Tests workflow 37534139423 is green.
Legacy local-template paths corrected to the canonical restored cache, eliminating two local skips.

Source Terms review disabled unpermitted DrivenData robot monitoring. The automatic feed covers
permitted government/owner sources and explicitly retains the dated board. Official GDR trace/paleo
archives acquired/rasterized on runner (82,871 line-covered footprint pixels; 244 paleo point cells),
not used in C1 and not hidden labels. USGS byte/coverage limitations are separate; never equate a green
job with a successful source. Final scientific status remains NOT PROMOTED, zero floor, no slot.

Exact final remote check/PR/merge/deployment receipts are updated separately in the three-pass JSON.
The complete available user brief, source links, and score history remain in README and are to be reviewed
at the start of future work. Winning goal unmet.


### Official-source receipt update after additive reconciliation

Runner 37536709561 verified all three public archives and coverage. USGS national traces: 82,841
footprint cells (58,800 exact-catalogue); GDR traces: 82,871 (58,876 exact-catalogue); paleo point
cells: 244. These all_touched pixel counts are not fault counts or expert-new truth. The earlier
USGS expansion-budget issue was fixed by reading geometry only, not the 203MB attribute table or
GDB. No vector trained C1. Sources, hashes and runner attestation are in the deployed JSON.
