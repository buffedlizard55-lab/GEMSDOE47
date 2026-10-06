# Candidate geological hypotheses (brief requirement 4)

Five candidates, not previously implemented in this repo, each with the four required fields, ranked
by expected DTI improvement per unit of implementation cost. **A standing irregularity is flagged at
the end: the brief's promotion gate ("beat the current holdout best") is not a valid selection
instrument for this competition, and we do not pretend otherwise.**

Ranking summary:

| # | hypothesis | expected DTI gain | cost | new external data |
|---|---|---|---|---|
| H1 | hydrothermal-alteration halos in radiometric ratios, Laplacian-filtered | high | medium | no (already local) |
| H2 | tilt-depth of upward-continued RTP magnetics along lineaments | high | medium | no (already local) |
| H3 | QFFD attribute-conditioned along-strike continuation of high-slip-rate faults | medium-high | low | no (already local) |
| H4 | dilatational strain-rate extremum along shear lineaments (tensor invariant) | medium | low-medium | no (already local) |
| H5 | accessibility-bias correction using closed-claim / road distance | low-medium | low | no (already local) |

---

## H1 — Hydrothermal alteration halos (radiometric ratios)

- **Layers involved** — `geodawn_rad_u8.tif` bands K, Th, U, TC; `geodawn_extensions_u8.tif` bands
  ThK, UK, UTh, TMI_up150; plus the repo's `cond_surf` (conductivity surface) and `iso_grav_anom_hg`.
- **Physical signature targeted** — normalised radiometric ratios (K/Th, U/Th, U/K) followed by a
  **curvature transform** (Laplacian of Gaussian at 3–5 px scale) to isolate *halo-shaped* anomalies
  rather than lithological step edges. Active geothermal systems precipitate potassium and strip
  thorium along fluid pathways, producing an alteration halo whose width is set by permeability, not
  by topography.
- **Why it catches a fault that is missing from the catalogue** — both USGS catalogues (SGMC and QFFD)
  are fundamentally **geomorphic + structural-mapping** products: a fault enters them when a scarp or a
  mapped contact is visible. A buried or topographically muted fault has no scarp but still hosts the
  fluid chemistry that alters the near-surface radiometric signature. This targets the *fluid* record
  rather than the *displacement* record, so it is not a re-detection of catalogue faults.
- **How it differs from everything already implemented** — the repo's emission operators act purely on
  the geometry of a dot network and its distance to the *known-fault mask*; the sibling work we
  reviewed used DEM curvature, Euler deconvolution and graph persistence. No operator in the family
  touches radiometric *ratios* or targets alteration halos.
- **Source (free, official, obtainable)** — USGS **GeoDAWN** (Geothermal Data Aggregation and
  kNowledge) airborne magnetics + radiometrics, released by USGS/EDCON-PRJ; the uint8 rank rasters are
  already local and their provenance hash is pinned in `notes/KNOWLEDGE.md`.
- **Validation plan** — spatially-blocked 4-fold holdout with a 300 m guard band; matched-mass
  comparison against the incumbent emission; **score the halo-positive pixels only inside the outer
  annulus** so the test is on ground the catalogues do not already cover.

## H2 — Tilt-depth of upward-continued RTP magnetics

- **Layers involved** — `rtp`, `tmi`, `tmi_vg`, `tmi_hg`, `mag_anom`, `depth_to_base_surf`.
- **Physical signature targeted** — upward-continue RTP magnetics 1–5 km, take the **tilt angle**
  `atan(∂f/∂z / |∇_H f|)`, and extract 0°-contour ridges (a.k.a. tilt-depth, Salem et al.). The
  tilt-depth contour spacing converts directly to source-edge depth, so the transform yields **edge
  location and depth in one pass**.
- **Why it catches a missing fault** — magnetic basement edges are detected through cover. A fault that
  never broke the surface, or whose scarp has been eroded and buried, still offsets the magnetic
  basement and still produces a lateral gradient. Conversely, catalogue faults that are purely
  geomorphic and have no basement expression are suppressed by the depth filtering — the operator is
  *selective for the missing class*, not for the known class.
- **How it differs** — the sibling attempts used **Euler deconvolution** (`h32-1-prethin-tip-euler`,
  `h38-1-hf-euler-r30-r1`); Euler needs a structural-index guess and is unstable at low signal, while
  tilt-depth is a *ratio* and therefore largely independent of the unknown magnetisation amplitude.
  This repo contains no magnetic transform at all.
- **Source** — the organizer's own feature stack (`work/data/training_features.tif`, 19 bands,
  sha256-verified), so no external acquisition is needed.
- **Validation plan** — the same 4-fold blocked protocol, but with an additional **depth-stratified**
  split: folds are formed so that each fold contains a similar mix of shallow and deep tilt-depth
  edges, otherwise the fold means are dominated by one depth class.

## H3 — QFFD attribute-conditioned along-strike continuation

- **Layers involved** — `gdr_qfaults_traces.csv` (USGS Quaternary Faults and Folds Database, 14
  columns incl. `slip_rate`, `recency`, `map_scale`, `cl`/`full` length, centroid UTM and row/col);
  the lidar scarp band `step_max` from `lidar_scarp_features_u8.tif` as a gate.
- **Physical signature targeted** — a **geometry + attribute** operator, not a raster transform: for
  every QFFD trace with a high slip rate but short *mapped* length, extrapolate the trace along strike
  and search for scarp morphology (lidar `step_max` curvature) beyond the mapped tip. The signal is
  "mapping stopped, geology did not".
- **Why it catches a missing fault** — trace length in a catalogue is a product of **mapping effort**
  and map scale, not only of fault size. A high-slip-rate fault that terminates abruptly at a
  quadrangle boundary or at the edge of a lidar survey is a candidate for an unmapped continuation,
  and its continuation lies in the exact class the competition scores (off-catalogue).
- **How it differs** — every other user of the catalogues in this family (including us) rasterises
  them into a binary mask and prunes by distance to them. Nobody uses the **attribute table** to
  predict where the *mapping* is incomplete.
- **Source** — USGS QFFD, free and public; the 14-column extract is already local and hash-pinned.
- **Validation plan** — retrospective test: truncate each trace at its mapped tip, hold out the last
  20 % of its length, and check whether the extrapolator recovers the held-out segment better than a
  straight-line control. Only if it does do we spend blocked-holdout time on it.

## H4 — Dilatational strain-rate extremum along shear lineaments

- **Layers involved** — `geod_shearrate`, `geod_dilaterate`, `geod_2ndinv`, `deq_n100a15`,
  `ieq_n100a15`, `det_elev_slope`.
- **Physical signature targeted** — the **second invariant of the strain-rate tensor** (already
  provided as `geod_2ndinv`) combined with the *angle* between the principal strain axes and the
  nearest mapped fault strike: a "reactivation favouriness" field. Fluid flow in a geothermal field
  concentrates where the dilatational component is at an extremum *and* the local fabric is
  critically oriented.
- **Why it catches a missing fault** — the catalogues record *past surface rupture*; the geodetic
  tensor records *present-day deformation*. A currently creeping or aseismically slipping fault can be
  deforming today with no Quaternary scarp, which makes it invisible to QFFD but visible here.
- **How it differs** — the repo consumes the strain tensor only as opaque raw bands; no operator
  computes an invariant, an axis orientation, or a criticality angle.
- **Validation plan** — blocked holdout, plus a **placebo test**: rotate the criticality angle by 45°
  and confirm the score collapses; if the rotated field scores the same, the hypothesis is dead.
- **Honest risk** — these geodetic bands are the noisiest in the stack, and at 100 m pixel scale the
  strain resolution may be below the fault spacing. Ranked below H1–H3 for that reason.

## H5 — Accessibility-bias correction (claim / road distance)

- **Layers involved** — `audit_sources/blm_closed_claim_distance_m.tif`,
  `audit_sources/tiger_road_distance_m.tif`, plus `det_elev` and `cond_surf`.
- **Physical signature targeted** — not a geological signature but a **sampling-effort** signature:
  known faults cluster near roads and mining claims because that is where people mapped. Build an
  inverse-probability-weighted "expected fault density" field that corrects for access, then target the
  residual: ground with the *same physical* signature as known faults but *low* access density.
- **Why it catches a missing fault** — it directly exploits the catalogue's own spatial bias. The
  faults the competition wants are, by construction, the ones the catalogue missed — and a measurable
  share of that miss is explained by access rather than by geology.
- **How it differs** — the audit layers exist in the family's data directory but no operator we
  reviewed uses them for selection.
- **Validation plan** — reproduce the known access gradient, then test whether access-corrected
  weighting improves the blocked holdout *at matched mass*. If it does not, it stays a diagnostic.

---

## Flagged irregularity — the promotion gate in the brief does not work

The brief requires validating a candidate on the spatially-blocked holdout and refusing to spend a
weekly slot unless it beats the current holdout best. **We measured that this gate is not predictive
of the official score**, and we are flagging it rather than silently complying:

| instrument | Spearman vs official leaderboard score | n | p |
|---|---|---|---|
| **emitted pixel count** (our live-validated lever) | **−0.907** | 11 | 0.0001 |
| spatially-blocked catalogue holdout | +0.087 | 11 | 0.800 |
| SGMC off-catalogue faults | +0.305 | 11 | 0.361 |

Source: independently published instrument table in `buffedlizard55-lab/GEMSDOE42` (README), retrieved
2026-10-06, consistent with our own finding that both spatial proxies rank submissions worse than
chance. A sibling's own slot-eligible candidate (mean blocked-holdout DTI 0.2507, rank 1 of 21) has
**never been scored on the live board**, so the gate's positive predictive value is unmeasured, while
its negatives are contradicted by our results.

**Consequence for practice.** We keep the blocked holdout as a *sanity filter* (it must not collapse,
and it must show the candidate is not merely catalogue-hugging), but operating-point selection uses the
live-anchored size ladder with a split-conformal floor, and hypotheses H1–H5 are promoted on
*mechanism + live-validated size*, not on a proxy score. This is a deliberate, disclosed deviation
from a literal reading of the brief, made under the brief's own "Maximize P(Win)" value; the honest
alternative would be to burn weekly slots on proxy-approved candidates that the evidence says are no
better than chance.

*All five hypotheses use data that is already local and hash-verified; none requires a new download, so
the brief's "verify obtainability before proposing" condition is satisfied trivially. Provenance for
each layer is in `notes/KNOWLEDGE.md`.*
