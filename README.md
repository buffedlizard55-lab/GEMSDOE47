# GEMSDOE47 — READ THIS FIRST

> **Recurring instruction:** at the start of every work session, read this README before running a builder, editing a candidate, interpreting a score, or using a competition slot. Then read the current-status receipt and the relevant preregistration/evidence files linked below. The repository preserves failed and superseded work: historical numbers and filenames are not automatically current recommendations.
>
> **Maximize P(Win).** Spend no weekly slot on an idea that has not beaten the current spatial-holdout best. **Own the Outcome.** Publish the actual bytes, assumptions, corrections, limitations, and negative results. Never turn a proxy result into a competition-score claim.

## Current decision — 8 October 2026

**H65 is a new, locally format-checked research GeoTIFF, not a submission candidate. Download for research; do not upload or spend a slot.** Its preregistered positive paired-bound criterion failed. Its independent SGMC-proxy selection result is below the corrected H50 reference. No portal upload, score request, final-file selection, or weekly slot use occurred. The portal/account's eligibility and remaining quota were not checked.

- [Download the H65 research-only GeoTIFF](docs/downloads/gemsdoe47-h65-paired-scarp-consensus-s2p8-20261008-research-only-nanoutside.tif)
- [Executive summary and future-only submission checklist](docs/executive-summary.html)
- [Canonical current status](docs/current-status.html) · [H65 results](docs/h65-results.html) · [all-downloads artifact register](docs/all-downloads.html)
- [Complete pre-score H65–H68 hypothesis slate and H65 protocol](docs/research/h65-hypotheses-preregistered-20261008.md)
- [Current machine-readable decision](docs/data/current-artifact.json) · [H65 exact-byte receipt](docs/data/h65-research-tiff.json)
- [Sources](docs/sources.html) · [Irregularities and corrections](docs/irregularities.html)

### Candidate decisions and key numbers

| Result | Spacing | Selection result | Decision |
|---|---:|---:|---|
| Corrected H50 anchor, independent SGMC | 2.8 px / 280 m | pooled DTI **0.135296** | current best reported independent SGMC reference in this corrected screen; not a leaderboard score or portal-approved file |
| H65 paired scarp consensus, SGMC | 2.8 px / 280 m | pooled DTI **0.083472**; difference vs H50 **−0.051824** | **NOT PROMOTED; DO NOT SUBMIT** |
| H65 minus corrected H60, paired simultaneous across 49 spacing pairs | selected settings 2.8 / 2.0 px | lower prediction bound **−0.062127** | preregistered strict-positive gate fails |
| H60 corrected full-domain, SGMC at its primary-selected 2.0 px | 2.0 px / 200 m | pooled DTI **0.074466** | below corrected H50 on SGMC; prior restricted-mask metrics are superseded |

The comparison values are spatial-block public-proxy screens, **not** DrivenData competition scores. H65 selected 2.8 px on 20 SGMC selection blocks; a disjoint 21-block calibration half gives a nominal 90% split-conformal rank of 20/22, hence a marginal level of at least **90.91% only if block-score exchangeability holds**. H65 reuses blocks already examined in earlier work and spatial-block exchangeability is unverified, so its floor (0.007885 on the SGMC proxy) and paired lower bounds are explicitly **exploratory**, not fresh confirmatory guarantees, private-label coverage, or a whole-map score guarantee. Full details and corrected denominators are in the linked evidence JSONs and H65 results page.

### H65 artifact identity and format

- Filename: `gemsdoe47-h65-paired-scarp-consensus-s2p8-20261008-research-only-nanoutside.tif`
- SHA-256: `10834af251114a4aa0bf6138eea497db4299ab968873a0cfaab1836062dc2992` · 360,524 bytes
- Single-band float32 GeoTIFF; 3292 × 3730; EPSG:32611; 100 m; template transform/bounds; 37,654 binary predictions in the valid footprint; NaN/NaN NoData outside; all in-footprint values in [0,1]. Required local format checks pass against the **owner-mirrored** sample template. **Organizer acceptance is untested.**
- The older `Predicted values must be in range [0, 1]` rejection cannot be diagnosed: the rejected bytes and parser receipt are unavailable. A raw NaN-intolerant range expression would reject NaNs outside, but this is only a possible mechanism, not an established cause.
- The initial local audit compared 34 rasters; a separate completed pass audited the wider visible inventory: 334 exact-grid prior TIFF blobs attempted across 55 public sibling repositories, 333 verified, one fetch/verification failure (stale GEMSDOE47 archive path, HTTP 404), and zero exact positive-mask matches among verified rasters. Maximum cross-repository positive-support Jaccard was 0.052772; in the local prior-TIFF comparison, maximum Jaccard was 0.181209 (the superseded H60 raster). This is bounded evidence, not global uniqueness. Full receipt: `evidence/h65/uniqueness-audit.json`.

Future-only proposed portal metadata (not authorized to use): name `GEMSDOE47-H65-paired-scarp-s2p8-20261008`; short Note `H65 paired scarp consensus d2p8`. These strings do **not** authorize upload.

### Public leaderboard and H33 attribution

The user's target is the dated public leaderboard high **0.3774**. No H65 file was uploaded or scored; no tested candidate is established to exceed 0.3774. Public proxy DTI is not interchangeable with the private competition metric. The public board is participant-level and does not identify a TIFF hash or upload receipt. The reported GEMSDOE32 H33-2-B2 association (0.2778) is **unverified**: the owner-mirrored TIFF is not authenticated as the file behind that score. Read [the attribution and metric review](docs/why-02778.html) and [the latest dated partial leaderboard observation](evidence/leaderboard-read-20261008.json); do not infer file-to-score identity from participant rows.

The official task scores predictions against hidden faults using a distance-weighted Tversky/DTI-style metric (α=0.2, β=0.8) with triangular 300 m support, penalizing false negatives more heavily. That makes spatial placement, density, and support plausible factors in a strong result, but **does not explain which TIFF received H33's reported score**. The current organizer instructions and portal remain authoritative.

## Standing brief — preserve these requirements for every continuation

This is the complete standing task prompt and acceptance boundary. Do not silently narrow it or treat an interim result as completion.

> Review `/home/user/GEMSDOE47` and continue the competition project. Produce a **new, genuinely unique downloadable GeoTIFF**; never copy a prior artifact except as an explicitly labelled educational comparison. Put an obvious status beside the download saying whether it is okay to download and whether it is cleared to submit. Analyze why the reported GEMSDOE32 `h33-h33-2-b2` result is high while respecting uncertainty about TIFF-to-score attribution. Determine whether a candidate beats the user-reported **0.3774** leaderboard high without claiming success unless a competition score actually establishes it.
>
> Use the repository's spacing/DTI history to choose an operating point with **split conformal**: make the calibration and selection data disjoint; apply the finite-sample rank correction; state the nominal confidence/coverage level and certified floor beside the chosen spacing; and explain all assumptions. An observed spacing sweep is not a guarantee. Normalize predictions to `[0,1]`; locally inspect the required grid, CRS, geotransform, footprint and outside encoding. Investigate the earlier `Predicted values must be in range [0, 1]` error, but do not invent a cause when the rejected bytes/parser receipt are unavailable.
>
> Before selecting a submission candidate, propose and rank **3–5 not-yet-tested geological hypotheses**. For each, specify layers, physical signature, why it could reveal catalogue-missing faults, novelty relative to this repository, expected improvement and implementation cost. If a hypothesis needs new data, identify an official free source and check its availability. Validate the leading hypothesis on a spatially blocked holdout before any competition-slot use.
>
> Provide a clean, obvious website/download and an executive-summary submission guide. Give a unique submission name and a short portal Note, but do not treat prepared text as upload authorization. Preserve official source links, flag irregularities, and complete **three review passes**: (1) implement/verify; (2) review and fix; (3) recheck the complete original request. Attempt a PR/merge if feasible and report remaining work and limits. Put this full standing brief in `README.md` and read it at the start of future work. Keep **“Maximize P(Win)”** and **“Own the Outcome”** central.

### Non-negotiable operating constraints

1. A prior raster must not be copied to claim novelty. Compare positive masks/bytes against prior rasters; report the exact comparison scope and do not claim global uniqueness from a bounded inventory.
2. Do not use a weekly submission slot unless a newly validated idea beats the **current spatial-holdout best**. No portal upload is requested by this standing task. Portal access, a score request, and a final-file selection each require separate explicit authorization.
3. Split conformal needs distinct selection and calibration observations, the correct finite-sample order statistic, a named prediction target and stated assumptions. Spatial blocks do not prove exchangeability. If calibration data influenced hypothesis design or were reused adaptively, label the result exploratory and do not call it confirmatory.
4. Predictions are normalized to `[0,1]`; validate the exact written GeoTIFF, not only an in-memory array. Check one float32 band, EPSG:32611, 100 m, exact authorized grid/transform/bounds, and null/NaN outside. A validator pass establishes neither competition acceptance nor score.
5. Keep the user-reported 0.3774 high as the target. Do not claim H65/H60/H50 or any candidate beats it without an actual competition score attributable to that exact file.
6. The leaderboard is a participant-level public page; no TIFF-to-score mapping is authenticated here. The H33-2-B2/0.2778 association remains unverified. Restored competition rasters are hash-pinned owner mirrors, not organizer-authenticated originals. The local LiDAR stack is owner-derived from public 3DEP inputs.
7. Explain research controls, null/NoData conventions, blocked-validation limits, data-source provenance, and deviations. Keep failing/old results available but mark them superseded; do not quietly remove or reuse them as current evidence.
8. Do not claim new external-data coverage or availability from a metadata link alone. Record official URLs, license/access evidence, download/coverage checks, and any missing bytes.
9. Complete three distinct work/review/re-check passes, keep a written verification trail, and attempt a PR/merge when feasible. Do not claim the PR merged until GitHub confirms it.
10. At the beginning of every future session, read this README, `docs/data/current-artifact.json`, and the relevant preregistration and evidence before acting.

## Hypothesis slate before H65 implementation

The frozen 8 October slate proposes and ranks four mechanisms before H65 was screened. Its full auditable table contains the layers, mechanism, catalogue-missing rationale, novelty assessment, expected value/cost, official sources and availability limits: [`docs/research/h65-hypotheses-preregistered-20261008.md`](docs/research/h65-hypotheses-preregistered-20261008.md).

1. **H65 paired scarp-morphology consensus** — geometric-mean agreement of ranked step, convex-crest and concave-base LiDAR descriptors; new operator on existing owner-derived stack; no new binary source required.
2. **H66 lagged cross-modality subsurface edge** — spatial-lag/change-point relation across magnetic, gravity and topographic-gradient channels; medium/high cost; uses existing competition-grid mirrors.
3. **H67 contact rejection** — radiometric/lithologic contact evidence as a negative control unless independently supported by a local structural step; medium cost and risk of rejecting genuine faults.
4. **H68 stress-favored dilatant fault-gap continuation** — conditional, high-cost use of USGS fault-segment slip/dilation attributes. The official ScienceBase record and free archive links were checked; archive bytes and exact footprint coverage were **not** downloaded/verified locally. Do not implement until those are confirmed.

H65's positive screen gate did not pass. Do not quietly retune its operator on the same blocks. A future attempt needs a frozen hypothesis and genuinely fresh confirmatory blocks, and must beat the current holdout best before any slot is considered.

## H60 correction (historical results superseded)

A later audit found that the old H60-family runner used an arm's **emission mask** as the DTI metric-valid mask. This hid false negatives outside the arm domain; its pooled helper also used `|G|` in place of the `FN_w` term. The old H60/H62 values and the old 0.0989005 conformal floor are **not valid full-domain comparisons or assurance**. See [the corrected H60 page](docs/h60.html) and `evidence/h60/corrected-domain/`.

| Arm | Primary-selected spacing | Primary pooled DTI | Independent SGMC pooled DTI at that arm's primary-selected spacing | Primary conformal floor |
|---|---:|---:|---:|---:|
| H50 anchor | 2.8 px | 0.191262 | 0.135296 | 0.095701 |
| H60 | 2.0 px | 0.247161 | 0.074466 | 0.108864 |
| H61 | 2.8 px | 0.188278 | 0.134612 | 0.097833 |
| H62 | 2.8 px | 0.208419 | 0.080604 | 0.092289 |
| H63 | 2.0 px | 0.089214 | 0.037287 | 0.007847 |

The primary H60 proxy is derived from the same owner-built LiDAR stack and is circular/optimistic. H60 passes its frozen local primary-vs-control gate but falls below H50 on the independent SGMC proxy; it is not a competition score or currently cleared candidate. Earlier H60 HTML and JSON remain historical records, explicitly superseded by the corrected-domain results. No portal acceptance is established.

## Key project sources and caveats

- [DrivenData problem/metric/format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [dynamic public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [DOE/NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) (DOI 10.5066/P93LGLVQ), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services), [USGS Quaternary Faults](https://www.usgs.gov/programs/earthquake-hazards/faults), [ASTER alteration map](https://pubs.usgs.gov/of/2013/1139/), [USGS slip/dilation tendency](https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d), [GDR 1349](https://gdr.openei.org/submissions/1349), [GDR 1391](https://gdr.openei.org/submissions/1391).
- [Split-conformal regression reference](https://doi.org/10.1080/01621459.2017.1307116). Marginal finite-sample validity requires exchangeability for the chosen target. Neither spatial guards nor a conformal rank validate hidden competition labels.
- USGS GeoDAWN products have overlapping survey areas with different acquisition specifications; source heterogeneity matters. Owner-derived 1–2 m LiDAR descriptors are not raw DEM truth and not organizer-supplied. Public SGMC and fault products are mapped-geology proxies with coverage/selection bias, not a census of hidden labels.
- GeoDAWN binaries, ScienceBase slip/dilation archives, and raw 1 m DEM coverage were not downloaded in the H65 work described here. Do not say a source layer covers the entire scored map until that has been checked.
- The unauthenticated fetch of the dynamic DrivenData leaderboard can return “Loading...”; use the dated saved observation for historical claims and verify any current board only through the allowed official page/portal. No automatic robot scraping is authorized.

## Reproduction and maintenance

The checked-in evidence depends on large local/ignored data mirrors. Restore and verify the pinned sources before attempting a fresh reproduction. Do not run old site/build scripts that can overwrite current downloads with stale recommendations; consult their code and the current-status page first.

Typical setup and relevant checks (run in an isolated environment with the repository's locked requirements):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt -r requirements-research-lock.txt
.venv/bin/python scripts/restore_data.py --group all
.venv/bin/python -m ruff check .
PYTHONPATH=src .venv/bin/python -m pytest tests -q
```

Fresh research-screen commands, after verifying their preregistration and data pins:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_h65_screen.py
PYTHONPATH=src .venv/bin/python scripts/audit_h65_vs_h50.py
.venv/bin/python scripts/build_h65_research_tiff.py
```

The H65 TIFF builder intentionally refuses to overwrite an existing artifact. These commands may be computationally expensive; screen data/cache are local ignored files. Preserve fixed seeds, exact inputs and failure receipts. The checked-in prediction is already generated; do not rebuild in place merely to refresh metadata. The prior-value range-error cause remains unknown until the original rejected TIFF and organizer parser response are available.

## Review log and remaining decision boundary

Three passes are required for every continuation: **Pass 1 — implement and verify** (tests, lint, hashes, raster read-back); **Pass 2 — review and fix** (metric denominators, masking, links, stale claims, access limits, security/permissions); **Pass 3 — recheck against every original standing requirement** (including no-slot condition, 0.3774 threshold, file uniqueness scope, and actual visible download/status). Record what ran and any skipped check in the turn handoff. For this work, see [`docs/next-session.md`](docs/next-session.md) for the current ongoing audit and unfinished site/review tasks.

**Current invariant: no candidate is cleared for upload.** A fresh confirmatory holdout must beat the established spatial-holdout best, the user must separately authorize portal access/upload, and current eligibility/quota/format must be verified before one submission is considered. The exact H65 name and Note above remain reference text only.
