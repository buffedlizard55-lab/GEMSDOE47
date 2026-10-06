# Next research steps — evidence-weighted and slot-safe

Reusable research base. This note supersedes earlier next-step advice that recommended spending three λ-probe slots or treated the Final Prize Round as unlimited. The official competition description says one submission is selected for scoring across the initial and final prize rounds; exact upload allowances and deadlines must be checked in the authorized participant portal. No submission is recommended by this repository.

## Current decision

- H47-B selected d=5 px / 500 m; locked-test pooled DTI 0.02755344.
- Its single-scale 400 m edge control selected d=5 px / 500 m; locked-test pooled DTI 0.02563947.
- A fixed-seed random control reached 0.03715911. Both candidate arms lost to this control.
- Six calibration blocks gave a nominal 6/7 = 85.7% marginal level only under exchangeability; spatial block exchangeability is unverified, two calibration cores are empty, and the clipped lower bound is 0.000.
- The new single-scale TIFF passes 17/17 local format checks and had no exact positive-mask match in the bounded 334-artifact search. These are not evidence of performance or organizer acceptance.
- Do not submit either TIFF. Do not run a score-measurement probe unless the current portal rules and a human owner explicitly approve its opportunity cost.

Full machine-readable results: `evidence/conformal_spacing_audit_20261006.json` and `evidence/conformal_candidate_uniqueness_20261006.json`; narrative: `docs/analysis.md` and `docs/executive-summary.html`.

## Ranked unbuilt geological hypotheses

The next shortlist is in [`docs/hypotheses.md`](../docs/hypotheses.md). It is qualitative and prospective; there is no defensible numeric DTI forecast from the small, nested, partly contested score/file history.

1. **Native-resolution 3DEP scarp/channel coherence.** Detect metre-scale scarps on 1 m DEM samples before aggregation. Best possible new surface-geometry signal; high cost and high false-positive risk. 3DEP is free, but the exact footprint tile set and mosaic have not been obtained/verified here.
2. **ASTER alteration mineralogy × independent structure.** Use USGS mineral classes and an independent structure cue to find exposed alteration along unmapped corridors. Official map data are listed, but no footprint intersection was retrieved; strong lithology/exposure confounding.
3. **Active-strain / magnetic-edge concordance.** Combine strain and magnetic orientation explicitly, with strong ablation and random-alignment controls. Component screens were weak, so this has a low–medium prior; mirror bands are not organizer-authenticated.
4. **Time-normalized thermal/geochemical station residuals.** Only proceed if DOE GDR records contain repeated, well-located measurements. Existing GSA already tested static point proximity; temporal residuals are a different operator, not a claim that thermal data are new.

For every candidate: pin input hashes and block IDs; freeze an operator and guard band; use matched mass or justify another comparison; include random, spatial-permutation and domain controls; report per-fold values and empty-label cores; and require a gain over a reproducible current holdout best before any slot discussion. A spatially blocked test against the public catalogue is only a screening proxy for the organizer's private target.

## Highest-value data work (not yet a model result)

### 1. Verify and acquire the exact 3DEP tiles

USGS [3DEP products and services](https://www.usgs.gov/core-science-systems/ngp/3dep/about-3dep-products-services) are public/free, and the competition description references 1 m DEM links. The previous environment could not retrieve some direct USGS endpoints. Before proposing implementation as viable, verify the exact tile list from the authorized competition materials, fetch the files via a working official service, record URLs, checksums, CRS/vertical datum and coverage gaps, then mosaic without resampling away 1 m features.

### 2. Verify the official input and label semantics

The local feature, label and sample files are hash-pinned public mirrors, not files downloaded from an authenticated participant portal. The official data page redirects unauthenticated clients to login. Keep mirror-derived results explicitly separate from organizer scoring; an authorized owner may compare official bytes to the pinned mirrors.

### 3. Resolve only through an authorized score receipt

The saved public board is participant-level and contains no TIFF hashes. The H33-2-B2/0.2778 link is contested: the owner page labels the file unscored. Do not scrape, poll, or repeatedly copy leaderboard content; DrivenData's [Terms of Use](https://www.drivendata.org/termsofuse/) restrict automated monitoring and require prior written consent for manual monitoring/copying. If an owner has an authorized submission receipt mapping an exact file hash to a score, record that receipt; otherwise leave the attribution unresolved.

## Retired or corrected advice

- **Do not spend three submissions on the λ-probe.** Its scale identity is mathematically valid under fixed metric semantics, but submission slots and final-entry selection can carry opportunity cost. No portal allowance or risk-free status was established.
- **Do not describe a Final Prize Round as unlimited.** The official description says one submission is selected for scoring across rounds; it does not establish unlimited uploads. Verify current portal terms.
- **Do not state that NaNs caused the reported `[0,1]` rejection.** The rejected TIFF and organizer diagnostic are missing. NaNs fail a common range expression in a local sample, which is only a plausible failure mode. The all-finite candidate passes local checks; portal acceptance is untested.
- **Do not state that the H33-2-B2 TIFF scored 0.2778.** The leaderboard row is unlinked, and the owner page marks that artifact unscored.
- **Do not call H47-B deep-source continuity unbuilt.** Cross-scale magnetic-edge persistence was already tested and not promoted; new magnetic ideas need genuinely different operators and fresh controls.
- **Do not claim a positive conformal performance floor.** The current clipped bound is zero and spatial exchangeability has not been demonstrated.

## Source and method references

- Competition metric/format/round description: [official problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
- USGS [3DEP](https://www.usgs.gov/core-science-systems/ngp/3dep/about-3dep-products-services), USGS [ASTER/MRData OFR 2013-1139](https://mrdata.usgs.gov/surficial-mineralogy/ofr-2013-1139/), USGS [Quaternary faults](https://www.usgs.gov/programs/earthquake-hazards/faults), and DOE [INGENIOUS GDR submission 1391](https://gdr.openei.org/submissions/1391).
- Split-conformal exchangeability result: [Lei et al. (2018), arXiv](https://arxiv.org/abs/1604.04173), [publisher DOI](https://doi.org/10.1080/01621459.2017.1307116). Spatial block exchangeability remains an unverified assumption here.
