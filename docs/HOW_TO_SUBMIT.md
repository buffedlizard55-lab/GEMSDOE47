---
title: Submission readiness and exact upload checklist
layout: default
nav_order: 2
---

# Submission guide — H60 is the file to submit

> **OK TO DOWNLOAD AND SUBMIT:** [`gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif`](downloads/gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif)
>
> SHA-256: `4ee074230a305fce6768012fc33380bf196c89170e70050a77cf4a44d74ef14c`
>
> Name: `GEMSDOE47-H60-lidarscarp-s2p0-20261007`
>
> Note: `h60 lidar-scarp d2p0 conformal90`

H60 is the current primary. H50 is a **VALID FALLBACK**, not the recommendation. H47-C1, H47-QC,
H49, H50a, H51 and H65 are research-only or superseded and must not be uploaded.

## Why the exact H60 bytes are locally submission-ready

The published file has one float32 band, width 3292 × height 3730, EPSG:32611, 100 m pixels and the
competition template's affine transform. All 12,279,160 values are finite and in [0,1]; values are only
0.0 and 1.0. There is no NoData tag and cells outside the mirrored footprint are 0.0. This deliberately
avoids the reported `Predicted values must be in range [0, 1]` failure under a NaN-intolerant portal check.
Seventeen strict read-back checks pass. Local checks do not prove organizer acceptance.

The official instructions say null or NaN outside data bounds, so the all-finite convention does not satisfy
that sentence literally. The [NaN-outside fallback](downloads/gems47-h60-lidarscarp-s2p0-20261007-nanoutside.tif)
is available, but can fail a NaN-intolerant range parser. Start with the clearly designated all-finite file
above because it directly addresses the actual range rejection. Save the exact portal receipt either way.

## Operating point and conformal statement

| Item | H60 value |
|---|---|
| Spacing | 2.0 px / 200 m |
| Budget | 37,654 unit dots |
| Selection | 20 spatially blocked blocks |
| Calibration | 21 disjoint spatial blocks |
| Procedure | max-residual one-sided split conformal, simultaneous over 7 spacings |
| Residual rank | 20 of 22 |
| Finite-sample coverage | at least 90.91%, **conditional on block-score exchangeability** |
| Certified proxy-block floor | 0.0989 DTI |

The guarantee is marginal for one future exchangeable proxy block. It is not a private-label, pooled-map or
leaderboard guarantee. H60's selection-half pooled score was 0.287891 on the lidar-derived primary instrument
and 0.193813 on the independent SGMC off-catalogue population. The primary instrument shares lidar lineage
with the field and is optimistic; SGMC is the independent corroboration.

## Exact upload sequence

1. Sign in and confirm eligibility on the [official competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/).
2. Read the [official problem/format page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
   and [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). Verify current quota/deadline in the
   authenticated portal; this repository cannot authenticate those live account facts.
3. Download the H60 all-finite TIFF linked at the top. Do **not** rename another artifact as H60.
4. Verify SHA-256 equals `4ee074230a305fce6768012fc33380bf196c89170e70050a77cf4a44d74ef14c`.
5. Choose **Submit → Make new submission**, select that one TIFF, and paste
   `h60 lidar-scarp d2p0 conformal90` into the optional Note field.
6. Retain the organizer's exact receipt, uploaded bytes, timestamp, filename and score. If rejected, retain the
   exact error and bytes before trying the labelled fallback encoding.
7. Disclose Arena.ai generative-AI assistance in the required narrative.

No portal login, upload or competition slot was used by this repository workflow.

## Latest negative experiment

H65 preregistered a 1.4–2.4 px H60 spacing extension. Selection chose 2.2 px, not the required sub-2.0 point,
so one of five frozen prebuild conditions failed. It was **not built and is not OK to submit**. The result
otherwise improved the proxy metrics (primary pooled 0.291533, SGMC 0.205420, conformal floor 0.099207 at
≥90.91% conditional coverage), but changing the gate after reading those scores would be post-hoc.
[H65 report](h65.html).
