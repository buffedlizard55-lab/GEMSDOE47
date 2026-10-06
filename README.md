# GEMSDOE47 — DOE GEMS Prize research project

> **Persistent project charter — reread this file at the beginning of every session before changing code, data, hypotheses, or submission status.**

**Charter date:** 2026-10-06 UTC

**Current state:** research and fail-closed submission infrastructure only. No competition files, holdout result, or submission TIFF is present in this repository. **The submission gate is CLOSED.**

## User brief and non-negotiable outcome

Build a useful, auditable project for the DOE GEMS Prize that can produce **a new, unique, single-band GeoTIFF submission**, rather than copying any artifact from the listed GEMSDOE sites. Study the strongest named submission and current competition evidence; formulate and rank 3–5 genuinely distinct geological hypotheses *before implementation*; and validate the leading candidate on a spatially blocked holdout before recommending that a scarce weekly submission slot be used. The clean GitHub Pages site must put a one-click TIFF download at its beginning when—and only when—a valid, promoted TIFF exists, and must have an executive-summary subpage explaining submission. Prevent the portal's reported `[0, 1]` value-range error. Include a unique submission name, short portal note, research and official source links, the user's brief and Arena values in this charter, three implementation/review passes, and line-by-line verification. If required data or validation cannot be obtained, state the blocker, do not invent results, identify the exact free official source needed, and flag limitations, future work, and irregularities. Create and merge a pull request if repository permissions and tooling permit.

### Arena core values for this project

- **Maximize P(Win)** — pursue the best expected *generalizing* discovery of new faults, not a cosmetic leaderboard bump. Use controls, spatial holdouts, and uncertainty; do not spend a submission slot on an unvalidated guess.
- **Own the Outcome** — trace every result to the exact source, code, input hashes, and raster bytes; disclose failures, access blockers, score-attribution gaps, and uncertainty plainly. A file is not a result just because it has a plausible name.

## Hard rules

1. **Never copy a prior submission raster.** Prior sites and identifiers may be studied for lessons only. A new build must have a unique, reproducible name and its own source-to-output receipt. Historical files are not in this checkout, so byte-level deduplication of all prior team artifacts is currently impossible.
2. **No slot before validation.** A candidate must beat a recorded incumbent on preregistered spatial blocks with a guard at least as wide as the official 300 m distance support, at matched prediction mass and with per-fold/control results. A catalogue holdout is only a proxy for the private expert labels.
3. **No fabricated data, results, scores, or attribution.** Official participant leaderboard rows do not map to filenames. The reported H33-2-B2 / 0.2778 pairing is user-reported, not independently tied to a public organizer receipt; GEMSDOE32 labels that candidate unscored.
4. **Do not bypass login or automate leaderboard monitoring.** The official DrivenData data page requires a logged-in entrant. No credentials are available here. DrivenData's published terms restrict automated monitoring/copying and manual monitoring/copying absent written permission.
5. **Audit the persisted TIFF bytes.** The final single-band float32 GeoTIFF must match the official grid/CRS and contain finite values only in `[0, 1]` inside the valid footprint; outside-footprint pixels must be NaN. Re-open the written output and validate it against the official template and an explicit feature-derived footprint mask before publishing a download.
6. **Keep evidence distinctions explicit.** “Listed on an official catalog” is not “downloaded”; “public score” is not “this TIFF scored”; “screening surface” is not “calibrated probability”; “candidate” is not “validated”.
7. **Three passes are required.** Pass 1: scope/data and science review. Pass 2: implementation, edge cases, and tests. Pass 3: user-facing docs/site, linkage, and end-to-end audit. Record findings and fixes; do not label the work fully validated when a required external input is unavailable.
8. **Branch discipline.** Work only on `arena/7c38688b-gemsdoe47`. PRs, if created, must use this branch.

## Current evidence and decision

- A one-time public leaderboard read on **2026-10-06 UTC** showed `alexoktaba` at **0.3345** (rank 1); `DARD` at 0.3195 was rank 5 and `extradr19` at 0.2778 rank 13. This is a moving, participant-level public snapshot—not a private/final result and not a TIFF mapping. See [`docs/leaderboard.html`](docs/leaderboard.html), [`docs/leaderboard-snapshot-2026-10-06.json`](docs/leaderboard-snapshot-2026-10-06.json), and the [official live board](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- The strongest specifically named artifact available for methodological study is the owner-described **H33-2-B2** candidate in [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html). Its page calls it **UNSCORED**; the public 0.2778 score is shown for a participant, not a filename. See [`docs/analysis.md`](docs/analysis.md) for the attribution audit and conditional metric reasoning.
- Four distinct candidates were ranked before detector implementation. **H47-A**, testing acquisition-invariant lineament support across overlapping USGS GeoDAWN surveys, is the first to test. It is a hypothesis only; no GeoDAWN products were downloaded and overlap with every target tile is unverified. See [`docs/hypotheses.md`](docs/hypotheses.md).
- The official DrivenData [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirects unauthenticated users to login. The needed free official source is the data page itself. Its public problem page names `training_features.tif` and `1m_DEM_links.csv`, and says raster/vector labels plus a sample submission are available on the login-gated download page; the exact label/template download basenames could not be verified here. Obtain the official feature raster, a suitable official label raster, sample-submission GeoTIFF, and DEM-link CSV through an authorized entrant account. Do not guess hidden filenames or bypass the login. For H47-A, the free official supplement is [USGS GeoDAWN ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ); catalog-listed downloads have not been acquired here.
- **No training data, model, holdout baseline/result, or TIFF exists. No hypothesis has been tested. The submission gate is CLOSED; do not spend a slot.**

## Site, proposed name, and portal note

The live site source is the repository root (`main:/` in GitHub Pages settings). Start at the [GEMSDOE47 GitHub Pages site](https://buffedlizard55-lab.github.io/GEMSDOE47/); its [Executive Summary](https://buffedlizard55-lab.github.io/GEMSDOE47/docs/executive-summary.html) explains the submission gate. At present the prominent TIFF control is intentionally disabled rather than linked to a fabricated or copied file.

**Reserved candidate identifier (not an existing file or approved submission):** `GEMSDOE47_H47A_GeoDAWNInvariant_v1`

**Draft portal note:** “Research candidate testing magnetic/radiometric lineament persistence across overlapping GeoDAWN surveys with differing acquisition geometry; source: USGS GeoDAWN, DOI 10.5066/P93LGLVQ. Not validated or approved for upload yet.”

Do not use this name or note in the portal until a new artifact has passed the documented holdout gate. Once promoted, create a collision-resistant filename using UTC timestamp and output SHA-256; refresh the site link only to that exact verified file. The portal requires the user's authorized account; this repository will not submit or consume a weekly slot.

## Start-of-session checklist

1. Reread this charter, then [`docs/irregularities.md`](docs/irregularities.md), [`docs/next-session.md`](docs/next-session.md), and [`docs/sources.md`](docs/sources.md).
2. Inspect `git status` and confirm the active branch remains `arena/7c38688b-gemsdoe47`.
3. Check for authorized official inputs under ignored `data/`; record file hashes and metadata before analysis.
4. Check whether the official leaderboard/rules have changed only by a permitted manual review; record a new timestamp, never scrape it.
5. Keep the gate closed until a reproducible blocked-holdout report is available and the output TIFF passes the byte-level validator.

## Project map

- [GitHub Pages home](https://buffedlizard55-lab.github.io/GEMSDOE47/) — opening section and gated TIFF download area.
- [Executive Summary](https://buffedlizard55-lab.github.io/GEMSDOE47/docs/executive-summary.html) — concise scientific and submission summary.
- [`docs/hypotheses.md`](docs/hypotheses.md) — preregistered four-hypothesis shortlist and validation gate.
- [`docs/analysis.md`](docs/analysis.md) — public score context, metric interpretation, and limits of causal attribution.
- [`docs/prior-results.md`](docs/prior-results.md) — user-reported prior IDs/scores clearly separated from official verification.
- [`docs/sources.md`](docs/sources.md) — official and research source register with acquisition status.
- [`docs/irregularities.md`](docs/irregularities.md) — open blockers and range-error audit notes.
- [`docs/next-session.md`](docs/next-session.md) — actionable continuation plan and limitations.
- [`docs/portal-checklist.md`](docs/portal-checklist.md) — filename, draft note, and safe manual submission checklist.
- [`docs/method.md`](docs/method.md) — inspectable H47-A screening-score definition and scientific limits.
- [`docs/validation-protocol.md`](docs/validation-protocol.md) — locked spatial-fold and package-promotion rule; no holdout has run.
- [`docs/review-log.md`](docs/review-log.md) — findings and fixes from the three review passes.
- [`gemsdoe47/candidate.py`](gemsdoe47/candidate.py) — H47-A aligned-grid screening math (not a calibrated model).
- [`gemsdoe47/spatial.py`](gemsdoe47/spatial.py) — deterministic block-fold splitter with conservative guard-cell purge.
- [`gemsdoe47/validation.py`](gemsdoe47/validation.py) and [`scripts/validate_submission.py`](scripts/validate_submission.py) — output-byte and `[0, 1]` range validator.
- [`scripts/build_h47a.py`](scripts/build_h47a.py) — local screening-surface builder; no download or promotion.
- [`scripts/package_submission.py`](scripts/package_submission.py) — fail-closed local packager, requiring a reviewed holdout report.
- [`tests/`](tests/) and [CI workflow](.github/workflows/tests.yml) — synthetic unit tests and static site-link checks; these are not geology/holdout results.

## Development and verification

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check gemsdoe47 scripts tests
python -m unittest discover -s tests -v
```

The test suite uses synthetic arrays/GeoTIFFs in temporary directories; it does not read competition data or produce a submission. After authorized downloads, run `python scripts/check_competition_data.py --labels LABEL_RASTER_BASENAME --template SAMPLE_TEMPLATE_BASENAME` from the repository root. Relative label/template names are resolved under ignored `data/`; the exact basenames must come from the logged-in official download page.

## External official references

- [DOE GEMS Prize — competition home](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem description and scoring / output specification](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official rules (NLR PDF 96647)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN release, DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)
- [USGS ASTER alteration data](https://mrdata.usgs.gov/surficial-mineralogy/ofr-2013-1139/)
- [DOE Geothermal Data Repository, INGENIOUS record 1391](https://gdr.openei.org/submissions/1391)
- [NASA Sentinel-1 / ASF search](https://www.earthdata.nasa.gov/data/tools/asf-search)
- [USGS Water Services](https://waterservices.usgs.gov/)

**Last charter refresh:** 2026-10-06 UTC. Update the date and evidence—not the gate status—only when new sources or reproducible results justify the change.
