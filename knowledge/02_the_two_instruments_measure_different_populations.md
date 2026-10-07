# The two candidate holdout instruments measure DIFFERENT fault populations

Measured 2026-10-06 from the official rasters only. Reproduce with
`python3 scripts/measure_instruments.py` -> `evidence/instrument_populations.json`.

## The measurement

Median band value, and mean empirical rank within the footprint, for three pixel populations:

| band | background p50 | given-catalogue p50 | SGMC off-catalogue p50 | cat rank | offcat rank |
|---|---|---|---|---|---|
| `det_elev` (detrended elevation) | -76.28 | **-68.76** | **+115.42** | 0.492 | **0.690** |
| `det_elev_slope` | 3.58 | **5.10** | **12.99** | 0.548 | **0.743** |
| `depth_to_base_surf` | 315.79 | **320.99** | **104.88** | 0.511 | **0.350** |
| `ieq_n100a15` | 738.63 | **906.00** | 726.90 | **0.561** | 0.483 |
| `geod_2ndinv` | 19.40 | **25.00** | 18.68 | **0.558** | 0.480 |
| `geod_shearrate` | 9.36 | **12.59** | 8.70 | **0.541** | 0.453 |
| `deq_n100a15` | 607.70 | **766.10** | 577.86 | **0.543** | 0.481 |
| `tc` | 18.59 | 17.42 | 15.82 | **0.448** | 0.385 |
| `iso_grav_anom` | -7.15 | -8.42 | -2.96 | 0.469 | **0.607** |

`cat` = within 3 px (300 m, the metric's kernel support) of the given training labels
(444,794 px). `offcat` = within 3 px of USGS SGMC traces lying > 3 px from the given
catalogue (428,326 px). Overlap between the two: 22,841 px (5.1 % of cat, 5.3 % of offcat).

## What it means

* The **given catalogue** is expert-mapped *Quaternary* fault. Its terrain signature is close
  to background on elevation (-68.8 vs -76.3) and on sediment thickness (321 m vs 316 m), and
  mildly elevated on slope (5.10 vs 3.58). These are largely **buried or basin-margin** traces.
  Its strongest raw-band affinities are the smooth regional fields: earthquake intensity
  (0.561), geodetic second invariant (0.558), shear rate (0.541), distance-to-earthquake
  (0.543).
* **SGMC off-catalogue** is high (det_elev +115.4), steep (slope 13.0, 2.5x background) and
  shallow-basement (105 m). That is **exposed mountain bedrock**. SGMC is a *geologic map
  compilation*, so its off-catalogue traces are dominated by lithologic contacts and older
  structures in the ranges, not by Quaternary faults in basins.

The two populations are close to disjoint in terrain space. `height_only` (local mean
`det_elev`, 19 px window) reaches precision-at-40k of **0.3325** against SGMC off-catalogue -
better than any fault-specific transform tried - which is decisive evidence that Instrument B
largely measures *"is this a mountain"*.

## Consequence for the submission

**Instrument B (off-catalogue SGMC) is REJECTED as the selection instrument.** Optimising
against it would build a bedrock-contact detector, which is precisely the documented failure
mode of fault-mapping models in this province: Hermant, Kiersnowski & Bellanger (2025, 50th
Stanford Geothermal Workshop) report that their siUNET/FaultSEG models "falsely fire on
coastline, canyon and stream morphology".

The hidden truth is expert-identified *new* faults for geothermal systems, mapped from 1 m
LiDAR and imagery by NLR and USGS experts (DrivenData forum 11527; INGENIOUS GDR
DOI 10.15121/1881483 for the training labels). That population is far closer to the given
catalogue than to SGMC bedrock contacts. **Instrument A (held-out catalogue components) is
therefore the correct selection instrument**, with its own defect handled explicitly:

*Defect (IR-47-PROXY-02).* Holding out catalogue components and then pruning predictions near
the visible catalogue destroys the fold truth by construction. The owner-supplied H33-2-B2 raster
returns DTI 0.0038 on this local Instrument A proxy, below random. This is not mapped to the
participant-level 0.2778 leaderboard row, and it neither authenticates the file nor explains a
participant score. That is a property of this instrument, not evidence about the official score.

*Fix.* Split the held-out components by whether they lie within 300 m of the *rest* of the
catalogue:

* **A1 "isolated"** - held-out components alone in their 300 m dilation. The flank prune does
  not touch them. Measures genuine off-catalogue discovery.
* **A2 "flanking"** - held-out components that share a 300 m dilation with another component.
  This is the population S13 describes ("newly mapped geometry of an existing fault system"),
  and it is the population the flank prune destroys.

The operating point is then chosen to be robust across A1 and A2 (max-min), which resolves the
flank-buffer question that the live anchor left ambiguous, instead of pretending one proxy
answers it.

## Corollary that changes the field design

Against Instrument A the best transform found so far is `scarp_step(det_elev_slope, r=1.5)` at
precision-at-40k **0.2467** (2.9x the 0.0861 random baseline), *not* `lrm(det_elev_slope, 9)`
which wins on Instrument B (0.2603) but only reaches 0.1059 on Instrument A. Every
`det_elev` (as opposed to `det_elev_slope`) transform is near the random baseline on
Instrument A (best 0.0956). The ranking of transforms **reverses between instruments**, which
is why the instrument choice had to be settled before the field was built.
