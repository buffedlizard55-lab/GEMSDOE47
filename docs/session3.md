---
title: Session 3 — historical research screen
layout: default
nav_order: 1
---

# Session 3 artifact — historical, research-only

> **Correction and status:** The long-form Session 3 report from the prior main branch described a TIFF as a submission, assumed the H33-2-B2-to-0.2778 association, used “incumbent” for owner-reported rasters, and included unsupported quota/capacity and causal language. That report is preserved with a withdrawal notice at [`docs/research/retired/session3-original-20261006.md`](research/retired/session3-original-20261006.md). This page replaces it; no Session 3 TIFF is approved for upload.

The file `gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif` is a historical research artifact, SHA-256 `f3f840b7880b7540ac6260b6b791ea55b2a875646c28401b01960096dc2da291`, 316,497 bytes. It contains 37,612 positive unit dots and finite zeros outside with no nodata tag. Under the published requirement that values outside the bounds be null or NaN, this unmasked zero-outside encoding fails the explicit local outside-nodata check. It is not portal-tested and must not be uploaded.

The local Session 3 proxy experiment compared its own emitted field with random, shifted, and rank-flipped controls on blocks derived from the public catalogue. Those measurements are not private scores, do not authenticate any historical participant-to-TIFF pairing, and do not establish a causal effect from deleting masked pixels. The apparent cross-session comparison with a 0.2778-labeled H33 raster is only a conditional geometry comparison: the participant-level 0.2778 observation has no organizer-authenticated TIFF association.

**Decision: research-only; not promoted; no slot authorized.** The current primary H47-C1 screen is separately reported on the [main landing page](index.html) and also failed its preregistered promotion gate. See the [corrected results](RESULTS.md), [attribution note](why-02778.md), and [README](../README.md).
