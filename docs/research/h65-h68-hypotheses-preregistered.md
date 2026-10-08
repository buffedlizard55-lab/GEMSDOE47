# H65–H68 preregistered geological hypotheses and H65 test protocol

**Frozen before scoring:** 2026-10-08 UTC  
**Status at freeze:** hypotheses and protocol only; no H65–H68 score or artifact had been computed.  
**Purpose:** choose the next experiment without reading the calibration half or spending a competition slot.

## Evidence boundary

The competition's private new-fault labels are unavailable. The only local validation populations are proxies:
(1) owner-derived local peaks in a lidar-scarp stack built from USGS 3DEP 1 m DEM tiles, and (2) off-catalogue
SGMC traces. The lidar population shares a data lineage with H65 and is therefore optimistic; SGMC is the
independent tie-break. Neither is a leaderboard guarantee. The owner-reported `0.2778` association is not an
organizer receipt. No portal upload is authorized by this protocol.

Official/manual-review sources:

* USGS 3DEP lidar/DEM program and data access: https://www.usgs.gov/3d-elevation-program and
  https://apps.nationalmap.gov/downloader/
* USGS Quaternary Fault and Fold Database: https://www.usgs.gov/programs/earthquake-hazards/faults
* USGS Geologic Map of the United States / SGMC release: https://doi.org/10.5066/F7WH2N65
* BLM MLRS mining-claim data: https://www.blm.gov/services/geospatial/GISData/nevada
* Census TIGER/Line roads: https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
* Split conformal primary paper: https://doi.org/10.1080/01621459.2017.1307116

Hash-pinned local provenance and actual obtainability are recorded in `registry/data_manifest.json`,
`data/restore_receipt.json`, and `docs/data/official-download-probes.json`. The local 3DEP stack is derived
and quantized, not raw lidar; this limitation remains material.

## Ranked slate (ranked before implementation)

| Rank | ID | Specific layers and physical signature | Why it can detect an off-catalogue fault | Difference from this repository | Expected DTI improvement | Implementation cost / viability |
|---:|---|---|---|---|---|---|
| 1 | **H65: dense en-echelon scarp train** | Owner-derived 3DEP `step_max`, `lappos_max`, `lapneg_max`, `upface_max`, `downface_max`, `cross_max`; use H60's maximum-of-channel-ranks scarp field but test 1.4–2.4 px inhibition spacing. This targets closely spaced, discontinuous synthetic/antithetic scarps and relay-zone steps. | Young Basin-and-Range faults may occur as distributed 140–240 m scarp segments rather than one catalogue-scale trace. H60's selection score rose to its lower 2.0 px sweep boundary, so its inhibition radius may suppress genuine nearby segments. Road and closed-claim masks retain a physical-artifact control. | No implemented or published repository candidate tests H60 below 2.0 px; this is a new spatial point-process representation, not a copy of H60's dot support. | **High relative to available proxy evidence**; direction is preregistered, magnitude unknown. | **Low**; all layers are restored and hash-verified. |
| 2 | **H66: polarity-paired breakline** | 3DEP `lappos_max` and `lapneg_max` plus `step_max`; target a positive-curvature crest and negative-curvature toe separated by 1–4 cells, with a step-height response between them. | A true degraded scarp has paired crest/toe curvature even when absent from mapped traces; isolated road crowns and single-pixel processing seams often lack the expected ordered pair after road masking. | H49 used magnetic polarity; H60 takes a max over lidar channels. No current field explicitly pairs opposite lidar curvature polarities with spatial ordering. | Medium–high, with lower artifact risk than a channel max. | Medium; no new data. |
| 3 | **H67: cross-scale scarp persistence** | Owner-derived 3DEP step/curvature channels, recomputed or approximated at 100, 200, 400 and 800 m support; target ridges persistent over adjacent scales but not broad regional slopes. | Fault scarps can remain coherent over several supports while drainage microtopography is scale-local. This could retain subtle buried/off-catalogue breaks and suppress ephemeral channels. | H51 is persistence of the competition slope-anomaly field, not multi-scale persistence of lidar scarp morphology. | Medium. | Medium–high; official 3DEP source is obtainable, but the current local stack is quantized. A faithful recomputation needs the official tile list/raw 1 m DEM windows, which are not presently restored. Viable only after that source is obtained. |
| 4 | **H68: geologic-contact-normal scarp concordance** | 3DEP scarp crest/toe channels plus SGMC geologic contacts; compute local contact tangent, then retain scarps whose gradient normal is concordant and which lie beyond the scored catalogue mask. | Concealed or unmapped continuations can express as topographic breaks aligned with lithologic contacts outside the USGS/INGENIOUS fault catalogue. | SGMC currently serves as an instrument; no promoted repository field conditions lidar morphology on contact-normal geometry. | Medium but higher leakage/overfitting risk. | Medium; SGMC is restored/hash-pinned and official. |

H65 ranks first because it uses available official-source-derived bytes, follows a monotone boundary signal already observed
without looking at a new calibration result, and changes only one interpretable operating parameter. H67 is not treated as
currently viable because raw official 1 m windows/tile-list coverage are not present in this checkout.

## Frozen H65 blocked-holdout test

1. Reuse **exactly** H50/H60's 41 nonempty contiguous blocks, 3-pixel (300 m) guard, budgets, roles, and seed
   500610; assert each block ID, bounds, budget and role against `evidence/h50/blocks.json` before scoring.
2. Prediction field/domain are byte-identical definitions to H60: maximum rank of the six lidar-scarp channels,
   valid-lidar cells, at least 250 m from TIGER roads, at least 150 m from BLM closed mining claims, and outside
   the organizer-provided catalogue mask.
3. Sweep spacings **[1.4, 1.6, 1.8, 2.0, 2.2, 2.4] px**. This set is frozen now. Under-capacity is reported,
   never silently replaced. Budget is 37,654 globally and apportioned exactly as in H60.
4. Primary score: block DTI against `lappos_t200_d3`. Independent score/tie-break: pooled selection-half DTI
   against `sgmc_offcat`. Also report the same five secondary lidar populations as H60.
5. The **selection half alone** chooses spacing by highest mean block DTI; exact ties choose the **larger** spacing
   (the conservative lower-density rule). Calibration scores remain unopened to selection.
6. Certify all six spacings simultaneously with the existing max-residual one-sided split-conformal routine at
   nominal 90% coverage. With 21 calibration blocks the rank is `ceil((21+1)*0.90)=20`, hence finite-sample
   coverage is at least 20/22 = **90.91%**, conditional on exchangeable block score vectors. This is marginal
   coverage for one future proxy block, not a private-score floor.
7. Promotion gate (all required):
   * selected spacing is **strictly below 2.0 px**;
   * pooled selection-half primary DTI is **strictly greater than H60's frozen 0.2878906732538241**;
   * selection-half mean block DTI is **strictly greater than H60's frozen 0.2844223590618498**;
   * simultaneous conformal lower bound is **strictly positive**;
   * pooled SGMC DTI is at least H60's frozen **0.1938127159974765** (non-inferiority);
   * exact whole-map artifact has no exact match in the accessible inventory, maximum positive-support Jaccard < 0.5,
     and passes every format/read-back check.
8. If conditions 1–5 fail, do not build or promote H65. If they pass, build exactly one all-finite [0,1] artifact
   plus a clearly labelled NaN-outside fallback, then run conditions 6 and uniqueness checks. No competition upload
   occurs in this repository workflow.

## Predeclared interpretation

A pass supports only this claim: on the frozen proxy design, denser H60 scarp emission improved both the primary
blocked proxy and did not degrade the independent SGMC proxy, with an assumption-conditional block-level conformal
floor. It does **not** establish that a leaderboard score exceeds 0.2778 or 0.3774. A failure means the 2.0 px H60
artifact remains primary and H65 is retained as a negative experiment.
