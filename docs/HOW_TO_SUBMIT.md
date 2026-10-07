---
title: Submission readiness and safe checklist
layout: default
nav_order: 2
---

# Submission guide — gated; not an upload request

> **Stop: no file in this repository is currently approved for submission. Do not upload the research TIFFs or spend a competition slot.** The prominent H47-C1 file is research-only and failed its predeclared holdout gate. H47-B, H47-QC, H47-GSA, H47-MAXCOV, and H48 artifacts are also research-only or superseded.

## Current artifact and local format status

The H47-C1 file is [`gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif`](downloads/gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif), SHA-256 `e6eea1956b8f76ffef2f4867a6e2ac0bef078c0c61c3711e44eb07e93cb089d0`, 152,396 bytes. It has one float32 band on the EPSG:32611, 100 m grid with matching dimensions/bounds. Raw samples are finite and in [0,1]; an internal TIFF validity mask marks the outside-footprint pixels null. Its 15/15 local read-back checks are not an organizer test or acceptance receipt.

The published [official format instructions](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) specify null or NaN outside the data bounds. Unmasked zero-outside all-finite H47-B single-scale, H47-GSA, H47-MAXCOV, H47-QC, H48-APEX/repack, and older Session-3 variants fail the explicit outside-nodata check. Separate NaN-outside variants follow owner-supplied mirror conventions only; portal acceptance is unverified. The bytes and parser receipt for the earlier rejection are unavailable, so its cause remains unknown.

## Promotion gate

H47-C1 pooled public-catalogue DTI is 0.177872 versus 0.180216 for the locked ordinary-terrain baseline. It wins 11/22 truth-bearing test blocks (15 required); the nominal 90% marginal block lower-bound estimate is zero under unverified block exchangeability. These are public-catalogue proxy results, not estimates of a private score. The gate is closed.

H47-GSA results remain exploratory; results that include H33-2-B2 at assumed DTI 0.2778 are conditional because the participant-level score is not authenticated to that TIFF. The d2.8 raster is the **owner-reported d2.8 reference**, not a separately established spatially blocked holdout best. H47-SAF's sensitivity sign change is bracketed only between tested assumed DTIs 0.2200 and 0.2400. Neither item changes the closed gate.

## Future checklist — only after a new candidate passes review

1. Confirm that the candidate has beaten the separately established spatially blocked holdout best under the preregistered rule, with matched controls, the required confidence level, and no unresolved provenance blocker. A zero or unsupported assumption-conditional lower bound keeps the gate closed.
2. Confirm bounded uniqueness against accessible prior artifacts. Do not claim global uniqueness from a limited inventory.
3. Reopen the exact TIFF bytes. Check one float32 band, EPSG:32611, 100 m resolution, training-data bounds/transform, in-footprint values in [0,1], and null/NaN outside. Retain the exact SHA-256 and local validation receipt.
4. Verify current eligibility, upload instructions, and any current per-user quota directly in the authenticated organizer portal. Public official pages checked 2026-10-06 do not establish current per-user quota or slot accounting. Do not infer upload count or cost from three historical λ-scaling score observations; no diagnostic is characterized as free.
5. Only after independent review and explicit authorization, follow the current organizer form's sequence, submit the approved bytes, and retain the organizer's exact receipt, timestamp, filename, and score. Local validation never substitutes for portal acceptance.

The same selected file is described by official materials as serving both prize rounds; confirm operative instructions in the live portal. No portal access, account action, upload, or slot use was performed for this review.
