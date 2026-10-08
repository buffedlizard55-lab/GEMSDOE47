---
title: Submission status and safe checklist
layout: default
nav_order: 2
---

# Submission status — local promotion is not portal acceptance

> **No competition upload or slot use is authorized or performed in this review.** H60 passed the repository's preregistered scientific promotion gate, but organizer acceptance has not been tested. The H47-C1 gate remains closed: C1 is still research-only and not promoted. See the [current status and exact-byte audit](current-status.html).

## H60: two encodings, different purposes

The public [official format instructions](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) require a single-band float32 GeoTIFF on the specified EPSG:32611 / 100 m grid, valid values in [0,1], and null or NaN outside the data bounds. The H60 bytes were reopened locally on 7 October 2026; the complete hashes and observations are in [`data/h60-encoding-audit.json`](data/h60-encoding-audit.json).

| Use | File | Exact local result | Status |
|---|---|---|---|
| Format-convention review | [`gems47-h60-lidarscarp-s2p0-20261007-nanoutside.tif`](downloads/gems47-h60-lidarscarp-s2p0-20261007-nanoutside.tif) | SHA-256 `d75ab9e282422d9592bc835c5cf719b22e6c564730de1f5fc42b57fc5bac2c01`; 351,392 bytes; 1 float32 band; 3292 × 3730; EPSG:32611; 100 m; NaN NoData; 5,167,373 finite valid-mask cells; 7,111,787 NaNs outside; valid values 0/1; 37,654 positive cells. | Matches the published null/NaN-outside convention on local read-back. **Organizer acceptance unknown; inspection only in this review.** |
| Range-check diagnostic | [`gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif`](downloads/gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif) | SHA-256 `4ee074230a305fce6768012fc33380bf196c89170e70050a77cf4a44d74ef14c`; 298,994 bytes; every cell finite and in [0,1]; no NoData tag; zeros outside. | The 17 local builder checks pass, but this file does **not** satisfy the published null/NaN-outside wording. Diagnostic only; do not present it as the format-conforming upload file. |

The existing ZIP contains the all-finite diagnostic plus a note and receipt; it does **not** contain the NaN-outside variant. It is an audit bundle, not an upload bundle. The cause of the previously reported `Predicted values must be in range [0, 1]` rejection remains unknown because the rejected bytes and parser receipt are unavailable. Neither encoding has been tested by the competition portal.

## Local scientific result — proxy evidence only

H60 was selected at 2.0 px / 200 m. Its preregistered 41-block screen reports pooled DTI 0.287891 on the primary owner-derived lidar-peak instrument and 0.193813 on the independent SGMC off-catalogue instrument. The primary instrument shares its owner-derived lidar stack with H60's input and is therefore circular; the SGMC result is independent corroboration. These are local public-proxy results, not hidden-label, leaderboard, or private-score results.

The one-sided split-conformal lower bound is 0.0989005 at rank 20/22 (90.91% marginal coverage), conditional on block-score exchangeability. That assumption is unverified and the bound is not a private-score guarantee. Bounded uniqueness compared 35 prior rasters, with zero exact matches and maximum mask Jaccard 0.021707; this is not proof of global uniqueness. See the [H60 evidence page](h60.html) and [machine-readable scientific receipt](data/h60-artifact.json).

H50 is an earlier locally promoted scientific candidate, superseded by H60 and not portal-accepted. Its all-finite zero-outside primary encoding also does not literally match the published outside-null/NaN instruction. H47-C1 remains not promoted: pooled proxy DTI 0.177872 vs. 0.180216 for its baseline, 11/22 truth-bearing blocks improved where 15 were required, and the assumption-conditional lower-bound estimate is zero.

## Published rules and account-specific limits

The [DOE/NLR official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) states up to **three scoring/feedback submissions per week** and one final selected file for the competition's rounds. This is the rules-level allowance; it does not reveal this entrant's eligibility, submissions already made, remaining weekly feedback opportunities, or portal selection state. Those account-specific facts require the authenticated portal. Do not infer upload events or remaining opportunities from score observations.

The saved official public leaderboard observation checked 7 October 2026 has rank 1 at 0.3774; 0.3195 was rank 7, not the leader. It is a dated participant-level observation, not a live score or a TIFF/hash receipt. The reported H33-2-B2 / 0.2778 mapping remains unverified. See the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) and [dated evidence](leaderboard.html).

## If a future portal attempt is separately authorized

1. Confirm current eligibility, operative deadline, the account's weekly feedback state, and its final-selection state in the authenticated portal. No credentials or account access are available to this repository.
2. Reopen and verify the exact intended TIFF against its SHA-256 and the official format page. The NaN-outside variant is the only H60 encoding here that matches the published outside-null/NaN wording locally; local checks do not guarantee portal acceptance.
3. Use the single TIFF unless the authenticated form explicitly requests an archive. Do not use the existing all-finite ZIP as an upload package.
4. Use the unique name `GEMSDOE47-H60-lidarscarp-s2p0-20261007` and optional Note `h60 lidar-scarp d2p0 conformal90`; do not state a proxy DTI as an organizer score.
5. Preserve the organizer's exact receipt, timestamp, filename, returned score, and the precise submitted bytes. Disclose generative-AI assistance as required by the rules.

**This checklist does not authorize an upload.** No portal login, upload, final selection, or competition slot use was performed for this review.
