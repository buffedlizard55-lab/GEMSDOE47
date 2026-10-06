# Knowledge base — index

Reusable across sessions. Read `README.md` §0 (the standing brief) first, then this index.
Every claim in these files is backed either by an official link or by a script in `scripts/`
whose output is committed under `evidence/`.

| file | what it settles |
|---|---|
| [01_metric_algebra_and_inversion.md](01_metric_algebra_and_inversion.md) | the metric's exact algebra, the credit bar, why binary is optimal, and the model-free bracket **5,764 ≤ \|G\| ≤ 15,179 px** inverted from the organiser's own eleven published scores |
| [02_the_two_instruments_measure_different_populations.md](02_the_two_instruments_measure_different_populations.md) | **why the obvious off-catalogue proxy is a trap.** SGMC off-catalogue traces are exposed mountain bedrock; the given catalogue is near background on elevation and sediment thickness. Selecting against SGMC builds a bedrock-contact detector. Includes the A1/A2 fix. |
| [03_geothermal_fault_discovery_research.md](03_geothermal_fault_discovery_research.md) | the verified literature: the competition, the origin of all 19 bands (INGENIOUS GDR DOI 10.15121/1881483), LiDAR fault-mapping results, structural settings that host geothermal systems, the geomorphometric transform citations, split conformal, and what is reachable from this sandbox |
| [04_free_public_data_sources.md](04_free_public_data_sources.md) | overlooked free/official sources with an explicit two-level obtainability verdict; **the measurement that kills the "add an external fault catalogue" research direction**; the NBMG 1:250,000 positional-error admission |
| [05_why_02778_and_can_we_beat_it.md](05_why_02778_and_can_we_beat_it.md) | the PhD-level answer the brief asks for, and the design document the submission was built from |
| [06_hypotheses_H47.md](06_hypotheses_H47.md) | the five surviving hypotheses ranked by ΔDTI ÷ cost, the validation gate, and **five refuted candidates with their numbers** |

## Irregularity register

Flagged where found, per the standing brief. Each is reproducible.

| id | irregularity | where |
|---|---|---|
| `IR-47-01` | `tc` is described in the raster metadata as "Tilt angle **or** total curvature", while the competition data page describes a top-of-crustal magnetic source depth estimate. Different quantities, different units, different signs. Measured AUC against the catalogue is **0.4476 — inverted**. Excluded from every recipe. | `knowledge/03` §2, `evidence/band_scale_diagnostics.json` |
| `IR-47-02` | The feature-valid domain and the submission footprint are **not nested**: 3,073 footprint pixels carry the float32 sentinel in ≥1 band, and 1,540 all-band-valid pixels lie *outside* the footprint. Writing NaN at those 3,073 is one route to the portal's range rejection. | `evidence/footprint_vs_feature_valid.json` |
| `IR-47-03` | `h27-4-d2.8` in its all-finite variant holds **40,199** positive px, not the 44,090 earlier family ledgers list. | `data/reference/README.md` |
| `IR-47-04` | Two SGMC copies differ (82,151 vs 83,593 positive px). All numbers here use the GEMSDOE30 copy in `data/reference/`. | `data/reference/README.md` |
| `IR-47-05` | The brief names **0.3195** as "the current highest". On 2026-10-06 that was rank 5; the leader was **0.3345**. Both are carried. | `README.md` §1 |
| `IR-47-PROXY-01` | A catalogue-derived holdout cannot reward a genuinely new fault. Proxy DTI is an **ordering** instrument, never a score forecast. | `src/gems47s3/holdout.py` |
| `IR-47-PROXY-02` | A catalogue-derived holdout is **structurally invalid** for any arm that prunes near the catalogue: the shipped 0.2778 artifact scores 0.0038 on it, below random, while the organiser scored it 0.2778. Fixed by the A1/A2 split. | `knowledge/02`, `src/gems47s3/holdout.py` |
| `IR-47-CODE-01` | `conformal.conformal_quantile` originally used `k = ceil((n+1)α)` and the `k`-th **smallest** value for the lower side, which **over-states the guarantee**. Caught by Monte-Carlo test, fixed to `k = ceil((n+1)(1-α))` and the `k`-th **largest**. | `src/gems47s3/conformal.py`, `tests/test_conformal.py` |
| `IR-47-CODE-02` | `geomorph.rank_scale` originally mapped ties to one value; combined with NMS that collapsed whole plateaus to a single emitted pixel (283 px per block where ~2,000 were expected). Fixed to a stable total order. | `src/gems47s3/geomorph.py`, `scripts/run_sweep_a.py` |
| `IR-47-CODE-03` | `emission.nms_disk` originally broke ties by 8-connected labelling, which let tied pixels at 1 < d ≤ min_dist both survive and violate the spacing constraint. Fixed to a radius-aware minimum-index filter. | `src/gems47s3/emission.py`, `tests/test_emission_raster.py` |
| `IR-47-CODE-04` | `transform_search.t_scarp` originally sampled **along** the strike instead of **across** it, and `t_openness` computed a mid-slope measure rather than openness, and `t_detrend` carried dead code. All three found in code review and fixed before the results were used. | `scripts/transform_search.py` |

## Environment limits, measured

No GPU. ~3 GB RAM. 2 CPUs. `curl`/`wget` blocked for everything except `pypi.org` and
`github.com`. Working transports: `fetch_page`, `web_search`, `git clone`, `gh api` (metadata **and**
raw blobs — this is how the three official rasters were restored), `pip --break-system-packages`.
Full matrix in `knowledge/03` §5.

Consequences that are decisions, not excuses: no deep U-Net or FaultSEG training; no 1 m or 10 m
DEM; every surface is built from the official 19-band 100 m stack plus the six external rasters
already present in `data/reference/`.
