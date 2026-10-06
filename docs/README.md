# GEMSDOE47 — site source

GitHub Pages serves this directory. `index.html` is the landing page and the
submission download is the first element on it.

| Page | Contents |
|---|---|
| `index.html` | The download, the headline finding, the range-error fix, all five frames, official sources |
| `executive-summary.html` | **Exactly how to submit** — nine steps, the note text, the recommendation, remaining work |
| `hypotheses.html` | The five hypotheses, ranked, each with layers / signature / why-it-catches-a-missing-fault / difference from prior work / verdict |
| `method.html` | LATI: the algebra, the identifiability fix, the binned fast path, the controls, cross-fitting, the two bugs |
| `evidence.html` | Every number, with its source file |
| `irregularities.html` | IR-47-001 … IR-47-015 |
| `prior-results.csv` | 63 rows: every known submission and score across the family |
| `prior-output-manifest.csv` | Every file this repository publishes or removed, with SHA-256 |
| `downloads/` | The shipped GeoTIFFs |

`downloads/` is committed on purpose — the deliverable must be reachable from the
live site with one click, and nothing else in this repository may be committed
that exceeds the size cap. Large restored inputs stay in `.cache/`, which
`.gitignore` excludes; see `data/README.md`.
