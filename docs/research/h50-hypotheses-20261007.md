# H50 — ranked candidate hypotheses, written before the field was chosen

Recorded 2026-10-07. Each candidate names the layer(s) it reads, the physical signature it
targets, why it should catch a fault that is **missing from the USGS/INGENIOUS catalogue**, how
it differs from anything already implemented in this repository, and the measured result on the
off-catalogue lidar scarp-peak instrument. The ranking metric and the decision rule were fixed
before the field was built: *maximise the mean DTI over the five off-catalogue lidar scarp-peak
instruments whose DTI is positively rank-correlated with the owner-reported public scores*
(`lappos_max` t200 d3, `lapneg_max` t200 d3, `step_max` t150 d3, `cross_max` t200 d3,
`upface_max` t200 d3). The SGMC off-catalogue instrument is reported but is **negatively**
rank-correlated with the reported scores, so it is a diagnostic, not a selection criterion.

Background that forced a new instrument
---------------------------------------
Every prior arm in this repository selected its field against either the given catalogue or the
SGMC compilation. `evidence/h50/instrument-ranking.json` shows why that is wrong: over the
13 owner-reported score artifacts restored in this checkout, DTI against the catalogue is
Spearman **−0.477** against the reported score, against SGMC off-catalogue **−0.025**, against
the union of both **−0.554**. Those pixels are masked out of evaluation, so mass placed on them
is pure waste, and any field optimised against them learns to spend mass where it cannot score.
The only positive correlations come from the **off-catalogue local maxima of the
organiser-supplied 1 m lidar scarp stack** — real, independently measured scarps that the
catalogue does not contain.

---

## Rank 1 — H50-A: the slope-anomaly field (SELECTED)

* **Layers.** Official band 19 `det_elev_slope` (the only band with substantial structure above
  the metric's 3 px kernel support: high-frequency variance fraction 0.181), plus its own
  25 px (2.5 km) Gaussian regional level. Optional variant: the same rank normalised within each
  GeoDAWN acquisition block (`external/audit_sources/acquisition_block_id_100m.tif`).
* **Physical signature.** A *locally* steep step on an otherwise gentle surface. A fault scarp is
  a narrow break; a mountain front is a broad ramp. Subtracting the regional slope removes the
  ramp and keeps the break.
* **Why it catches a catalogue-missing fault.** The catalogue is a compilation of *mapped*
  traces. An unmapped scarp is still a steep step in the detrended elevation — nothing about
  being unmapped changes its geometry, only its absence from the compilation.
* **How it differs.** No prior arm ranked a band above its own regional level, and no prior arm
  used the 1 m lidar scarp peaks as a truth population at all.
* **Measured.** 0.2067 (lappos), 0.2276 (lapneg), 0.2130 (step), 0.1682 (cross) — mean 0.1774.
  Against the plain global slope rank (0.1971 / 0.2110 / 0.1877 / 0.1773, mean 0.1693) that is
  **+4.8 %**, and against `scarp_step(det_elev, hw 9)` (0.1172 / 0.1124 / 0.0919 / 0.1067) it is
  **+51 %**.
* **Implementation cost.** Low: one Gaussian filter and one rank.

## Rank 2 — H50-F: acquisition-block-normalised rank (retained variant)

* Same layers, plus the acquisition-block raster; the rank is normalised *within* each block.
* Rationale: slope statistics differ between flight blocks, so a global rank lets one rugged
  block monopolise the emission budget.
* Measured: 0.2005 / 0.2149 / 0.1903 / 0.1790 (mean 0.1719) — a hair below H50-A on the lidar
  instruments but the **best of all fields on SGMC** (0.1495). Kept as the documented robustness
  variant; H50-A was chosen because the decision rule weights the lidar instruments, and because
  σ = 25 px matches this repository's established "regional" convention.

## Rank 3 — H50-B: cross-instrument edge coincidence (REJECTED)

* **Layers.** RTP analytic signal, isostatic-gravity gradient, `det_elev` scarp, lidar
  `step_max` — each thresholded at its 99.5th percentile and dilated by the 300 m kernel.
* **Signature.** A fault offsets topography *and* basement *and* magnetics along the same line.
* **Why it should have worked.** Four independent instruments agreeing on the same 300 m support
  is a strong prior for a through-going structure the compilations missed.
* **Measured — failed.** DTI_B 0.0267–0.0326, *below* the h33 reference (0.0954) and far below
  the local-ruggedness field (0.1310). Cause: a 4-level count field carries almost no ranking
  information, so greedy spaced selection degenerates to raster order. A rank-weighted variant
  (sum of four maximum-filtered edge-rank maps) reached only 0.0853.
* **Verdict.** Do not retry a hard-vote coincidence transform. The *idea* survives only as a
  soft multiplicative corroboration, which is H50-E.

## Rank 4 — H50-E: multi-physics corroboration of the slope field (REJECTED)

* **Layers.** `det_elev_slope` rank × rank of each of: `scarp_step(det_elev, hw 5/9)`,
  `curvature`, `lrm`, `tpi`, `tc`, `tmi_hg`, `iso_grav_anom_hg`, `geod_2ndinv`, `cond_surf`,
  `depth_to_base_surf`, `|line_response(rtp)|`, the elevation gradient magnitude.
* **Measured — every product degraded the field.** The best product (slope × tpi) reached
  0.1635 / 0.1946 / 0.1689 / 0.1464 against H50-A's 0.2067 / 0.2276 / 0.2130 / 0.1682. The
  magnetic products were worst: slope × `tmi_hg` 0.1236, slope × `|line_response(rtp)|` 0.1331.
* **Reading.** This is the round's contrarian result. For the off-catalogue scarp population the
  family's multi-physics AND-gate throws away exactly the steep scarps the 1 m lidar finds. The
  magnetic and gravity layers are informative about *basement structure*, not about *surficial
  scarp expression*, and the hidden new-fault population behaves like the latter.

## Rank 5 — H50-C: the step contrast ratio (REJECTED)

* **Layers.** `scarp_step(det_elev, hw)` divided by the regional mean slope.
* **Signature.** A step *relative to* its surroundings — explicitly separating a scarp from a
  uniformly steep hillside.
* **Measured — failed.** 0.1013–0.1324 across half-widths and background radii, against 0.2917
  for the plain slope rank on the union instrument. The ratio destroys the amplitude information
  the lidar scarp channels carry.

## Rank 6 — H50-D: strike-aligned anisotropic emission (REJECTED)

* **Layers.** Any field; this changes the *emission geometry*, not the field. The exclusion zone
  becomes an ellipse aligned to the local structure-tensor strike, tight across strike and loose
  along it, on the argument that one truth pixel needs only one best-covering dot and cross-strike
  duplicates are wasted mass.
* **Measured — failed.** 0.2504–0.2792 against 0.2917 isotropic on the union instrument. The
  along-strike density gain is smaller than the cross-strike coverage loss.
* **Verdict.** The untested variant is a per-trace budget reallocation rather than a per-pixel
  exclusion rule.

## Also tested and rejected

| Variant | Measured (union instrument, 2.8 px, 37,654 dots) |
|---|---:|
| Pre-smoothing the slope before ranking, σ = 0.5–3.0 px | 0.2892 → 0.2235 (monotone loss) |
| Soft continuous values instead of unit dots | 0.2621 |
| Catalogue flank buffer of 1/2/3 px | 0.2908 / 0.2889 / 0.2848 (0 px is best) |
| Slope minus its regional level, acquisition-block ranked | 0.2922 (tie within noise) |
| Slope / regional slope ratio | 0.1614 |
| Rank difference (global rank minus regional rank) | 0.0757 |
| Local rank in a 21–61 px moving window | 0.1828 → 0.1473 |
| Ensembles of two or three fields | 0.2297–0.2636 |
| Elevation gradient magnitude instead of band 19 | 0.2017 |
| Raw `tc` band | 0.0619 |
| `|line_response(rtp, σ 2)|` | 0.0688 |

## Budget decision

The budget is *not* taken from the instrument. On the off-catalogue lidar peaks the marginal dot
keeps paying the credit bar (`α · DTI`) all the way to 120,000 dots, because that instrument is
finite and recall-saturating. 37,654 is therefore justified by (a) the credit bar — the marginal
dot's mean realised kernel weight is 0.2343 against a bar of 0.0584, a 4× margin — and (b) the
mass regime of the owner-reported score history. See `evidence/h50/budget-profile.json`.
