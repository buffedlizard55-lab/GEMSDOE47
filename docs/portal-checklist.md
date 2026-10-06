# Pre-upload checklist (future promoted candidates only)

> **Current decision: STOP. Do not upload H47-B or the historical d-cat/annulus TIFF.** H47-B failed its holdout/control gate; the older TIFF is derived by pruning a published mask.

Use this list only after a new candidate has passed independent scientific review:

- [ ] Candidate prediction is genuinely new, not copied or pruned from a prior submission.
- [ ] Authorized input provenance, code revision, preregistration, fold assignment and output are hash-pinned.
- [ ] Candidate beats the current spatially blocked holdout best and appropriate controls under a frozen rule; guard is at least 300 m, mass is matched or justified, and label coverage is adequate.
- [ ] Per-fold and pooled results, negative controls, failure regions and missing-label blocks are reported.
- [ ] Any conformal result states calibration count, quantile rank, nominal coverage, target, and unverified assumptions; it is not overstated as a guarantee.
- [ ] Accessible historical artifacts were compared, with exact/similarity results and scope limitations.
- [ ] Final file is reopened and audited against the current official sample-submission template: one band, required type, CRS, shape, transform, nodata convention and every in-footprint value in [0,1].
- [ ] Unique descriptive filename and truthful short note are recorded with the exact file SHA-256.
- [ ] Current official competition rules, portal instructions, accepted archive types and slot limits are checked manually immediately before the upload.
- [ ] An authorized team member submits manually and saves the organizer receipt ID, timestamp, exact uploaded hash, status and returned score.

See [`submit.html`](submit.html) for the step-by-step manual guide and [`validation-h47b-20261006.md`](validation-h47b-20261006.md) for the current negative screen.
