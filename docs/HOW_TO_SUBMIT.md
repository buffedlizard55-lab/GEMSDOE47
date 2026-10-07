---
title: Submission readiness and safe checklist
layout: default
nav_order: 2
---

# Submission guide — H50 is the file to submit

> **One file in this repository is approved for submission: H50.**
> Download [`gems47-h50-slopeanom-s2p8-20261007-allfinite.tif`](downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif) (SHA-256 `97e3c3816cd6b458d01e34d7022f871935bb57710e3982a11d9edaec13e91a17`, 291,321 bytes) from the
> [top of the landing page](index.html) and upload it. The older H47-C1, H47-QC, H49,
> H48, H47-B, H47-GSA and H47-MAXCOV files are research-only and are **not** to be
> uploaded.

## Current artifact and local format status

The H50 file is [`gems47-h50-slopeanom-s2p8-20261007-allfinite.tif`](downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif), SHA-256 `97e3c3816cd6b458d01e34d7022f871935bb57710e3982a11d9edaec13e91a17`, 291,321 bytes,
37,654 dots at 2.8 px / 280 m. It has **one float32 band** on the EPSG:32611,
100 m grid with matching dimensions, bounds and affine transform. Every value is
finite and inside [0,1]; the values are 0.0 and 1.0 only. There is **no NoData
tag** and every cell outside the competition footprint is 0.0, so a
NaN-intolerant range reading `np.all((v >= 0) & (v <= 1))` returns True on all
12,279,160 cells. That convention is the direct answer to the reported portal
rejection `"Predicted values must be in range [0, 1]"` and matches the
owner-reported family-best raster byte convention.

The published [official format instructions](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
specify null or NaN outside the data bounds. This file writes zeros there instead, which does not
satisfy that wording literally; it is published because the owner-reported family-best artifact
used exactly this convention and was scored. A NaN-outside fallback is published alongside it as
[`gems47-h50-slopeanom-s2p8-20261007-nanoutside.tif`](downloads/gems47-h50-slopeanom-s2p8-20261007-nanoutside.tif) if the portal ever rejects the zeros
convention. The bytes and parser receipt for the earlier rejection are unavailable, so its cause
remains unknown and no portal-acceptance claim is made for either variant.

## Operating point and its guarantee

| Item | Value |
| --- | --- |
| Spacing | 2.8 px / 280 m |
| Budget | 37,654 unit dots |
| Selection | mean DTI on 20 spatially blocked blocks (selection half) |
| Certification | disjoint 21 blocks (calibration half), max-residual one-sided split conformal, Lei et al. JASA 2018 Algorithm 2 |
| Residual rank | 20 of 22 |
| Finite-sample coverage | at least 90.91 % **conditional on block-score exchangeability** |
| Certified holdout floor | 0.0957 DTI |
| Note for the DrivenData form | `h50 slope-anomaly d2p8 conformal90` |

Blocked-holdout pooled DTI 0.165881 against 0.049421 for the owner-reported d2.8 reference,
0.048252 for the previous holdout best (H47-C1) and 0.047049 for mass-matched fixed-seed spaced random. The
validation instrument is the off-catalogue 1 m lidar scarp-peak population, a proxy that shares
the slope quantity with the field's input band; these are proxy numbers, not private-score
estimates.

## Why the earlier files are not submittable

* **H47-C1** pooled public-catalogue DTI 0.177872 versus the locked baseline's 0.180216; it wins
  11/22 truth-bearing test blocks where 15 were required; its assumption-conditional
  lower-bound estimate is 0.0000.
* **H47-QC** selected 6 px / 600 m with locked pooled DTI 0.0131689425, below its own
  geochemistry-only ablation at 0.0141948068.
* **H49** is all-finite with no NoData tag, so it fails the published null-or-NaN-outside rule;
  its nominal 90 % proxy lower bound assumes unverified exchangeability and its selection rule was
  amended post hoc.
* The 0.2778 figure attached to `h33-2-b2` is owner-reported and the owner's own page marks that
  submission unscored; it is a comparator, never an authenticated incumbent.

## Upload checklist

1. Confirm you are logged in to the [official competition 306 portal](https://www.drivendata.org/competitions/306/competition-doe-gems/).
2. Download [`gems47-h50-slopeanom-s2p8-20261007-allfinite.tif`](downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif) from the top of [index.html](index.html), or the
   [`gems47-h50-slopeanom-s2p8-20261007.zip`](downloads/gems47-h50-slopeanom-s2p8-20261007.zip) which also contains the note and the receipt.
3. Verify the SHA-256 is `97e3c3816cd6b458d01e34d7022f871935bb57710e3982a11d9edaec13e91a17` before uploading.
4. Paste `h50 slope-anomaly d2p8 conformal90` into the optional Note field.
5. Retain the organiser's exact receipt, timestamp, filename and score.
6. Generative-AI assistance (Arena.ai coding agent) is disclosed in the repository README and in
   the official narrative.

No portal access, account action, upload, or slot use was performed for this review.
