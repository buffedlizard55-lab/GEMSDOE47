# GEMSDOE47 — site source

GitHub Pages serves this directory. `index.html` is the landing page; its first element is the H47-QC
research-only download and a prominent closed-gate warning. No current file is authorized for submission.

| Page | Contents |
|---|---|
| `index.html` | The H47-QC research download, closed-gate finding, bounded range audit, historical frames, official sources |
| `executive-summary.html` | Future-candidate-only submission steps, current no-slot recommendation, 0.2778 attribution limits, and the current leader reference |
| `h47qc-screen-20261006.json` | H47-QC full blocked DTI sweep, calibrated-block order statistic, input hashes, and format audit |
| `h47qc-uniqueness-audit-20261006.json` | Bounded comparison of H47-QC against the 55-repository / 334-exact-grid-artifact inventory |
| `hypotheses-round2-20261006.md` | The four new candidate hypotheses ranked before the H47-QC implementation, with physics, catalogue rationale, overlap review, feasibility, and sources |
| `hypotheses.html` | Five legacy hypotheses, with a correction that the H33-2-B2 / 0.2778 attribution is not authenticated |
| `method.html` | Exploratory LATI proxy algebra, owner-reported mapping caveats, numerical corrections, and conditional masking evidence |
| `evidence.html` | Every number, with its source file |
| `irregularities.html` | IR-47-001 … IR-47-015 |
| `prior-results.csv` | 63 owner-reported rows of participant scores and raster references; associations are not organizer-authenticated |
| `prior-output-manifest.csv` | Every file this repository publishes or removed, with SHA-256 |
| `downloads/` | The shipped GeoTIFFs |

`downloads/` is committed on purpose — the deliverable must be reachable from the
live site with one click, and nothing else in this repository may be committed
that exceeds the size cap. All posted TIFFs are research-only and must not be uploaded. Large restored inputs stay in `.cache/`, which
`.gitignore` excludes; see `data/README.md`.
