# Next-session plan — continue without rework

## Hard gate before a submission TIFF

1. Obtain the official feature raster and `1m_DEM_links.csv` (names shown on the public problem page), an official raster-label file, and sample-submission GeoTIFF by an authorized, enrolled-competitor route. The exact label/template download basenames are not verified without login; pass their actual paths to the checker. The official page is login-gated; no credentials are present here and the project will not bypass it.
2. Place files under ignored `data/`, then run `python scripts/check_competition_data.py --labels LABEL_RASTER_BASENAME --template SAMPLE_TEMPLATE_BASENAME` for presence, SHA-256, and basic metadata. The check script does not download or authenticate; it fails closed when files are missing or grids disagree.
3. Verify raster shape, transform, CRS, band descriptions, nodata/mask and label counts from file bytes. Compare all template-aligned inputs before deriving a feature.
4. Freeze the existing spatial holdout baseline and verify it is genuinely out-of-fold with at least a 300 m buffer. If no valid incumbent exists, create and report the baseline first; do not claim an improvement against a guessed score.
5. Run only the existing initial H47-A screening implementation first. Retrieve official GeoDAWN overlap/flightline products if authorized; verify coverage, horizontal CRS, pixel size and independent overlap, then explicitly align the grids. Freeze candidate parameters and controls before looking at held-out results; any method change after this point requires a dated preregistration update before scoring.
6. Promote only if candidate improves on the local holdout best under the locked rule. Report per-fold values, pooled DTI, same-mass comparison, random/domain controls, and limitations. If not, record the negative result and keep the slot gate closed.
7. Generate a submission TIFF only from the promoted prediction, copied to the official template profile and audited after writing. Assign a unique name/comment from the build receipt and check for duplicate pixels/hashes against accessible prior artifacts.
8. Publish a download only after the artifact passes both the local format audit and the holdout gate. The exact competition portal requires the user/team's authorized submission action; this repository does not upload or spend slots.

## Research order after H47-A

- H47-B: clip the official USGS ASTER alteration polygons to the exact competition bounds; confirm class coverage/host geology before testing.
- H47-C: check ASF/OPERA Sentinel-1 scene coverage/coherence over the grid and determine whether an account is needed.
- H47-D: query USGS water site history for temperature/discharge parameters inside the footprint; deduplicate against INGENIOUS records and report actual station counts.

## Known limitations

- No competition inputs, GPU, or previous local pipeline were present in the initial checkout. Full train/inference/holdout has not run.
- The official data page is login-gated. Public-source listings and sibling-site output files do not substitute for the authorized training files.
- Current leaderboard values are a one-time public snapshot. DrivenData Terms of Use prevent project-side automated polling without written permission.
- Spatial holdout against public mapped faults is a proxy and cannot validate discovery of the private expert labels.
- No filename-to-score mapping for the reported 0.2778 is verified; the GEMSDOE32 page calls its H33-2-B2 candidate unscored.
- A public board score cannot guarantee private or final-round ranking. Competition rules state the same chosen submission is later rescored against an expert-expanded label set.
