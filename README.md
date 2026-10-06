# GEMSDOE47 — standing charter and current status

> **Decision as of 2026-10-06 UTC: no submission is eligible and no slot is recommended.** The current linked TIFF is a **research-only artifact, explicitly not for portal submission**. Its local GeoTIFF format audit passed, but H47-B failed its preregistered spatial-screen promotion gate. A format-valid file is not a scientifically validated submission.
>
> **Core values:** **Maximize P(Win)** · **Own the Outcome**. Preserve the slot until a genuinely new, unique prediction beats the current spatially blocked holdout best under a preregistered, adequately controlled test.

## Current decision record

| Item | Current evidence | Decision |
|---|---|---|
| H47-B cross-scale magnetic-edge persistence | Locked-test pooled DTI: **0.02755**; tuned single-scale baseline **0.02564**; fixed-seed random control **0.03716**. Assumption-conditional conformal lower floor **0.0**. | **NOT PROMOTED**; do not spend a slot. |
| H47-B research GeoTIFF | One-band float32; EPSG:32611; 3292 × 3730; 100 m; all in-footprint values in [0, 1]; NaN outside; 18,524 positive pixels. SHA-256 `7e5df9d01689e438e8379ebd4763ed803de02e94826f43da37c33c16380d669b`. | Download exists only for transparent review; it is **not slot-eligible**. |
| Accessible-artifact comparison | Compared against 334 exact-grid TIFF artifacts found in 55 visible `buffedlizard55-lab` GEMSDOE repositories. Zero exact positive-mask matches; maximum equal-mass Jaccard **0.01119**. | Supports uniqueness only against those accessible artifacts; **not a global uniqueness proof** and not a performance result. |
| Historical `gems47-dcat20-annulus-flankprune` TIFF | Delete-only subset of a previously published mask. Its old score extrapolation and claimed conformal floor were not validly supported. | Retained for audit/history only; **not a unique detector and not for submission**. |
| Public leaderboard evidence | The latest saved one-time public read records rank 1 at **0.3774** (participant name not preserved), DARD **0.3195 at #7**, and `extradr19` **0.2778 at #13**. | Participant scores do not identify TIFFs or submission receipts. No TIFF-to-score mapping is authenticated. |

Detailed results and limitations: [H47-B validation report](docs/validation-h47b-20261006.md), [full bounded uniqueness audit](docs/h47b-uniqueness-audit-20261006.json), [leaderboard/source-attribution analysis](docs/analysis.md), and [irregularity register](docs/irregularities.md). The downloadable artifact is at the very top of the [project site](index.html) and is visibly marked **RESEARCH ONLY — NOT FOR SUBMISSION**.

## Standing brief

### Goal

Develop a scientifically defensible, **unique** GeoTIFF prediction for the DOE Geothermal Energy from Mines and Smart (GEMS) Prize, DrivenData competition #306, targeting faults newly identified by experts in the GeoDAWN region. A prior artifact may be studied for learning, but the delivered prediction must not be a copy, prune, or relabeling of an earlier submission. Novelty is necessary, not sufficient: the detector must also earn a valid spatial holdout gain.

### Hard requirements, in priority order

1. **Unique prediction.** Compare the candidate against accessible historical artifacts before any upload; record exact-match and similarity results, scope, and limitations. Do not call uniqueness global unless all relevant prior submissions are authoritatively available.
2. **Holdout before a slot.** Do not use a submission slot for an idea that has not beaten the current spatially blocked holdout best under a preregistered rule. Use equal prediction mass where appropriate, a ≥300 m guard consistent with the metric kernel, fold-level results, and nontrivial controls. Ties, unstable folds, missing labels, failed controls, or a zero/unsupported lower floor keep the gate closed.
3. **Conformal honesty.** Use split conformal only where the exchangeability unit and target are defensible. State sample count, rank, nominal level, and assumptions. Never call an assumption-conditional result a distribution-free guarantee for private labels or a leaderboard score. Do not reuse the retired `0.34837` claim.
4. **Valid output.** Read back the exact output bytes. Enforce a single-band GeoTIFF, official grid/CRS/transform, allowed nodata footprint, finite in-footprint values in [0, 1], and an audit receipt. A format pass does not establish scientific validity or organizer acceptance.
5. **Traceable identity.** Give an eligible output a unique descriptive filename and short truthful note. Record source/code/template hashes. Never label a research-only artifact as a submission candidate.
6. **Candidate-first research.** Before implementing a new detector, rank 3–5 distinct geological hypotheses by expected DTI improvement and implementation cost. For each, specify the official/free data source and actual availability, target physical signature, why it might reveal a fault missing from existing catalogues, key confounders, and a falsifiable test. Do not describe a listed dataset as acquired or footprint-relevant until measured.
7. **Analyze prior scores cautiously.** Investigate the reported 0.2778 artifact and other participant scores, but treat user/site claims as claims until an organizer receipt links a score to an exact file hash. Never infer a TIFF's score from a participant-level leaderboard row or filename similarity.
8. **Sources and site.** Keep official source links and provenance boundaries in the repository. Put a clearly labeled, one-click `.tif` download at the top of the site—even if it is explicitly research-only—and provide an executive-summary subpage with accurate manual submission steps. Do not create a false “live feed.”
9. **Terms and safety.** Use official, trusted sources and provide links for manual review. Do not bypass login, request/store credentials, scrape the leaderboard, or automate portal submission. A user/team member with authorized access must perform any eventual submission manually and follow the current rules.
10. **Iterative review.** Work autonomously and line by line. Complete an implementation/verification pass, a bug/assumption review and repair pass, and a full-brief recheck. Run the whole test suite and lint. Keep a review log and list unresolved work.
11. **Delivery.** Open and merge a PR only after evidence, docs, site, tests, and branch checks are ready. If a source or score cannot be verified, say so rather than guessing.

### Non-negotiable project values

- **Maximize P(Win)**: select methods for expected held-out/private performance, not a flattering public-label number or score ladder.
- **Own the Outcome:** preserve receipts, disclose negative results, protect scarce submission slots, and never substitute a copied artifact or unverifiable claim for evidence.

## Research and verification references

- [Official DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — task, metric, and raster contract.
- [Official competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login-gated data access; mirrored inputs used for H47-B are not independently authenticated downloads.
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — moving participant-level results only.
- [USGS GeoDAWN DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) — magnetic/radiometric survey release; H47-B used a rank-encoded mirror channel, not the raw official archive.
- [Project source register](docs/sources.md) · [ranked hypotheses](docs/hypotheses.md) · [validation protocol](docs/validation-protocol.md) · [manual submission guide](docs/submit.html).

## Reproduction and checks

The H47-B experiment was run against pinned public-mirror inputs; its preregistration is frozen at [`docs/preregistered-h2.md`](docs/preregistered-h2.md). Re-run only if the exact ignored inputs are available and hash-verified:

```bash
.venv/bin/python scripts/run_h2_experiment.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
```

Re-running the screen does not authorize an upload. The TIFF under `docs/downloads/` is explicitly research-only. See [`docs/next-session.md`](docs/next-session.md) for the next actions and [`docs/review-log.md`](docs/review-log.md) for the correction history.
