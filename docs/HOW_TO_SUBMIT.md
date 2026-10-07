---
title: H50 local review package and guarded submission checklist
layout: default
nav_order: 2
---

# H50 local review package — not organizer-approved

> **Current local status:** H50 is the last candidate that passed this repository's documented spatially blocked public-proxy promotion gate. It is **not organizer-accepted**, no leaderboard score is established, and no upload or competition-slot use is recorded. Local promotion and format read-back do not authorize an upload. Verify eligibility, live portal instructions, and slot/quota rules before any future submission.

**[Download the H50 NaN-outside GeoTIFF for review](downloads/gems47-h50-slopeanom-s2p8-20261007-nanoutside.tif)** ·
[Submission note](downloads/gems47-h50-slopeanom-s2p8-20261007-note.txt) ·
[H50 evidence page](h50.html) · [Machine-readable status receipt](data/h50-artifact.json)

- **Primary review file:** `gems47-h50-slopeanom-s2p8-20261007-nanoutside.tif`
- **SHA-256:** `2e32d8ed384692bc44ff768ca5d3814ed48d7b627ba3c818743ee13ab3538d5b` · **341,280 bytes**
- **Suggested form Name:** `GEMSDOE47-H50-slope-anomaly-s2p8-20261007` (suggestion only; not organizer-registered)
- **Short Note:** `h50 slope-anomaly d2p8 conformal90`

## Local serialized-TIFF read-back

The selected NaN-outside variant is one float32 GeoTIFF band on EPSG:32611, 3292 × 3730, 100 m, with transform `[100, 0, 243350, 0, -100, 4508550]`. Rasterio read-back of the serialized file found a NaN NoData tag, **5,167,373** finite cells inside the mirrored footprint, **7,111,787** NaNs outside, in-footprint values restricted to 0/1, and **37,654** positive dots, all inside the footprint. This is a local read-back against hash-pinned owner mirrors; it is **not an organizer validation or acceptance**.

The separate [all-finite diagnostic variant](downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif) has SHA-256 `97e3c3816cd6b458d01e34d7022f871935bb57710e3982a11d9edaec13e91a17` (291,321 bytes), no NoData tag, and finite zeros outside the footprint. It passes a local `[0,1]` range check but does **not** literally satisfy the published null/NaN-outside wording. The NaN-outside variant is therefore the primary review file. Neither encoding has been submitted to or accepted by the organizer.

The prior H49 exact TIFF remains archived as research-only and fails the outside-null/NaN check. H51 is newer but research-only: no fresh H51-specific frozen holdout exists, and H50's conformal calculation does not apply to H51. See [H51 status](h51.html).

## H50 public-proxy evidence (not a leaderboard score)

| Item | Result |
| --- | --- |
| Chosen spacing | **2.8 px / 280 m** |
| Nominal confidence / conditional lower floor | **90% / 0.095701 DTI**, residual rank 20 of 22 |
| Selection / calibration | 20 selection blocks / 21 disjoint calibration blocks |
| Candidate blocked public-proxy pooled DTI | **0.165881** |
| Owner-reported d2.8 reference pooled DTI | 0.049421 |
| H47-C1 comparator on that holdout | 0.048252 |
| Mass-matched spaced random control | 0.047049 |

The 90.91% finite-sample coverage calculation and positive lower floor are conditional on block-score exchangeability, which is **not verified**. The holdout is an owner-mirrored off-catalogue 1 m lidar scarp-peak proxy that shares slope information with H50's input field. It does not establish a private-label score, a map-wide guarantee, a leaderboard score, organizer acceptance, or an upload right. The 0.2778 H33-labelled participant score/file mapping is owner-reported and unverified; the owner's page marks that submission unscored.

## Guarded submission sequence — only if a future upload is separately authorized

No portal access, account action, upload, or slot use was performed in this review. These steps are conditional instructions, not a recommendation or authorization to submit now:

1. Open the [official competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/) and authenticated portal. Check the current eligibility requirements, official [GeoTIFF instructions](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), deadline, per-user quota, and slot-accounting rules. Public pages checked on 2026-10-06 did not establish the current per-user quota or slot accounting.
2. Confirm that this exact candidate remains separately authorized for an available slot. Do not upload H51 or a candidate that has not passed its own fresh frozen holdout gate. If authorization is absent, stop.
3. If authorized, download the linked **NaN-outside** H50 TIFF and verify the SHA-256 above before use. Do not substitute the all-finite diagnostic file unless current official instructions explicitly permit that encoding.
4. Where the form asks for a Name, the suggested unregistered text is `GEMSDOE47-H50-slope-anomaly-s2p8-20261007`. Where it offers a Note field, use exactly `h50 slope-anomaly d2p8 conformal90`.
5. Follow the portal's current file/ZIP workflow, submit only the authorized file, and retain the organizer's exact receipt, timestamp, filename, hash, score, and any parser response. A successful local check does not establish portal acceptance.
6. Disclose Arena.ai generative-AI assistance in the official narrative if required by the rules. Entrant eligibility and account authorization must be confirmed by the entrant.

## H50a template-format checkpoint — research only

A sibling session exported `gems47-h50a-corridor-s1p5-b3-20261007-4096e1f9d19b-template-nanoutside.tif` (SHA-256 `6dfe602d35b0f0755eae9a7a8bcc2e6f81efaf291f97341d588ee818b2e07cc5`). Its nominal 90% public-proxy floor is 0.0000 and its blocks were previously inspected, so its promotion gate is closed. The local template-mask check passes, but **do not submit H50a**. Full checks and receipts: [h50a.html](h50a.html).

## Why earlier files remain research-only

- **H51:** no fresh independent holdout; inherited H50 conformal values are not H51 evidence.
- **H49:** exact TIFF fails the published outside-null/NaN check. Former observed-range-scaled DKW mean floors 0.040976 (Instrument B) and 0.038014 (PM0200) are retracted; corrected fixed-support `[0,1]` floors are zero. The nominal paired lower prediction statistics against the H33-labelled reference are negative (−0.03342 selection; −0.01050 calibration), and the score/file mapping is unverified. See [corrected H49 results](H49_RESULTS.html).
- **H47-C1:** its locked public-catalogue holdout gate failed (pooled DTI 0.177872 versus 0.180216; 11/22 truth-bearing blocks won where 15 were required; lower-bound estimate 0.0000).
- **H47-QC:** its locked pooled DTI 0.0131689425 was below its geochemistry-only ablation 0.0141948068.
- The `0.2778` H33-labelled figure is owner-reported, not authenticated to a TIFF or leaderboard receipt; the owner's page marks the submission unscored. It is not an authenticated incumbent.

For hashes and statuses of all historical files, see the [artifact register](all-downloads.html).