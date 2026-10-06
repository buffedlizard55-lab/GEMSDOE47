# Portal checklist — do not use before promotion

**Current status: gate CLOSED; do not submit.** No validated candidate, source data, holdout report, or TIFF exists in this repository.

- **Reserved project/candidate identifier:** `GEMSDOE47_H47A_GeoDAWNInvariant_v1` (draft, not a scored entry)
- **Final filename pattern:** `GEMSDOE47_H47A_GeoDAWNInvariant_v1_<UTC timestamp>_<SHA256 first 12>.tif`
- **Draft portal note:** “Research candidate testing magnetic/radiometric lineament persistence across overlapping GeoDAWN surveys with differing acquisition geometry; source: USGS GeoDAWN, DOI 10.5066/P93LGLVQ. Not validated or approved for upload yet.”

Before any upload:

1. Confirm H47-A passed its preregistered, spatially blocked, ≥300 m guarded holdout at matched mass and beat the recorded incumbent with per-fold/control results.
2. Verify the file is a newly generated prediction, not a prior TIF or placeholder; retain exact inputs, code revision, output checksum and validation report.
3. Re-open the exact output and validate one float32 band, exact official shape/CRS/transform, finite in-footprint values in `[0, 1]`, and NaNs outside the explicit feature-derived footprint.
4. Have a human review the portal name, note and current official instructions. A candidate identifier is not proof of global uniqueness; the build timestamp and checksum make this artifact uniquely traceable.
5. Submit manually through an authorized DrivenData account. This repo does not bypass login, upload, or spend a weekly slot.
6. Save the portal receipt and associate that receipt with the filename/hash only after organizer confirmation.

The current [HTML checklist](portal-checklist.html) is easier to read on the project site. Related gates: [`hypotheses.md`](hypotheses.md), [`irregularities.md`](irregularities.md), and [`next-session.md`](next-session.md).
