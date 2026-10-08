---
title: Corrected requirements audit
layout: default
nav_order: 8
---

# Corrected requirements and review status — 7 October 2026

> **No competition upload or slot use is authorized or performed in this review.** H60's local scientific promotion gate passed; that does not establish organizer acceptance or override the explicit no-upload instruction. H47-C1 remains research-only, not promoted, and its gate remains closed. See [current status](current-status.html).

## Current decision and requirement audit

| Requirement / claim | Status | Evidence and boundary |
|---|---|---|
| Current research candidate | **H60 locally promoted; not organizer-accepted** | H60 passed its preregistered 41-block gate. Primary off-catalogue lidar-peak pooled DTI is 0.287891, but the instrument shares the owner-derived lidar stack read by H60 and is circular/optimistic. Independent SGMC off-catalogue pooled DTI is 0.193813. These are local public-proxy results, not hidden-label or leaderboard scores. See [`h60-artifact.json`](data/h60-artifact.json). |
| H60 file format and encoding | **Two variants; only one matches outside wording locally** | [`h60-encoding-audit.json`](data/h60-encoding-audit.json) reopens exact committed bytes. The NaN-outside TIFF has 5,167,373 finite valid-mask cells and 7,111,787 NaNs outside. The all-finite variant has zeros outside and fails the published null/NaN-outside wording, despite passing its 17 local builder checks and raw [0,1] range test. Organizer acceptance of either variant is untested. |
| Historical range-error diagnosis | **Unknown** | The rejected TIFF bytes and organizer parser receipt are unavailable. Neither local encoding proves the cause or guarantees portal acceptance. |
| H47-C1 promotion gate | **Closed; not promoted** | C1's pooled catalogue-proxy DTI is 0.177872 versus 0.180216 for its ordinary-terrain baseline; 11/22 truth-bearing test blocks improve, below the preregistered 15 required. Its assumption-conditional lower-bound estimate is zero. H60 is a separate later experiment and does not change C1's result. |
| H50 and H51 | **Historical / not current submission recommendations** | H50 is superseded by H60; its all-finite zero-outside encoding does not literally match the official outside requirement. H51 is a near-duplicate of H50 (maximum mask Jaccard 0.8543), not an independent candidate. |
| Split-conformal interpretation | **Conditional, not a private-score guarantee** | H60's rank is 20/22, with nominal marginal coverage 90.91% and lower floor 0.0989005, conditional on block-score exchangeability. Exchangeability is unverified; the instrument is public proxy data. |
| Bounded uniqueness | **Limited audit, not a global proof** | H60 compared with 35 prior rasters: zero exact matches and maximum mask Jaccard 0.021707. This does not establish global uniqueness or geological discovery. |
| Public leaderboard | **Dated participant observation only** | The saved official observation checked 7 October 2026 has rank 1 = 0.3774; 0.3195 was rank 7. Neither row identifies a TIFF or hash. The H33-2-B2 / 0.2778 association remains unverified. |
| Submission rules / weekly allowance | **Public rules cap known; account state unknown** | The [DOE/NLR official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) states up to three scoring/feedback submissions per week and one final selected file for the competition's rounds. It does not reveal this entrant's eligibility, submissions already made, remaining weekly opportunities, or selection state. Verify those in the authenticated portal; no account access is available here. |
| Score observations vs. upload history | **Not interchangeable** | Historical score rows, including λ-scaling observations, are not upload receipts and do not prove which bytes were submitted or the account's remaining opportunities. No diagnostic cost is inferred or called free. |
| Official data / provenance | **Access limitation retained** | The competition data tab redirects unauthenticated users to login. Restored inputs are hash-pinned mirrors, not authenticated organizer downloads. No private labels, private score, or organizer receipt mapping a score to a TIFF is claimed. |

## Manual-review sources

- [Official GeoTIFF format, target, and metric instructions](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DOE/NLR official rules PDF (submission allowance and disclosure)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Source register and dated observations](sources.html)
- [H60 scientific evidence](h60.html)
- [Exact-byte format audit](data/h60-encoding-audit.json)
- [Three-pass review log](review-log.md)

## Actions not taken

This documentation review did not restore competition data, run an H60 scoring pipeline, log in to DrivenData, upload a file, request a score, use a feedback opportunity, make a final selection, or spend a competition slot. Local validation is not organizer acceptance or a private performance result.
