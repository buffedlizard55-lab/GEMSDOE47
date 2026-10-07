"""Pinned specification of the DOE GEMS Prize grid — every value measured, not assumed.

Provenance of the numbers below
-------------------------------
Geometry / counts were re-measured in this repository on 2026-10-06 by
``scripts/verify_data.py`` from hash-pinned owner-supplied public-mirror bytes. The pins
were inherited from the team's earlier mirror restorations (``buffedlizard55-lab/GEMSDOE10``
``data/README.md`` and ``src/gems10/spec.py``) and rechecked here. These hashes establish
mirror-byte consistency only; they do not authenticate organizer provenance.

Official statements these values are checked against
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format):

  * same projected CRS as the training data — UTM zone 11N, EPSG:32611
  * same resolution as the training data — 100 m
  * same bounds as the training data; data outside the bounds is null or nan
  * a single layer, datatype 32-bit float, values between 0 and 1

Repository paths currently populated from the public mirror (not authenticated organizer bytes):

  data/training_features.tif
  data/labels.tif
  data/sample_submission.tif
"""

from __future__ import annotations

# --- geometry (measured here, 2026-10-06) ------------------------------------
EPSG = 32611
PIXEL_SIZE_M = 100.0
WIDTH = 3292            # columns
HEIGHT = 3730           # rows
ORIGIN_X = 243350.0     # transform c  (upper-left X)
ORIGIN_Y = 4508550.0    # transform f  (upper-left Y)
TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
BOUNDS = (243350.0, 4135550.0, 572550.0, 4508550.0)  # left, bottom, right, top
TOTAL_PIXELS = WIDTH * HEIGHT          # 12,279,160

# --- measured counts ---------------------------------------------------------
FOOTPRINT_PIXELS = 5_167_373   # finite pixels in the owner-supplied mirrored sample_submission.tif
NODATA_PIXELS = 7_111_787      # NaN pixels in the owner-supplied mirrored sample_submission.tif
LABEL_POSITIVE_PIXELS = 60_988  # labels.tif int8 == 1 (the USGS/INGENIOUS catalogue)
FEATURES_ALL_BAND_VALID_PIXELS = 5_165_840

COVERAGE_OF_FOOTPRINT = LABEL_POSITIVE_PIXELS / FOOTPRINT_PIXELS   # 0.011803
COVERAGE_OF_GRID = LABEL_POSITIVE_PIXELS / TOTAL_PIXELS             # 0.004967

# --- sentinels ---------------------------------------------------------------
FEATURE_SENTINEL = -3.4028234663852886e38   # float32 most-negative, used as nodata
FEATURE_INVALID_BELOW = -1e38               # sentinel observed in the mirrored feature raster; portal handling is unknown
LABEL_NODATA = -1
SUBMISSION_NODATA = float("nan")

# --- metric constants (official page 967) ------------------------------------
ALPHA = 0.2          # false-positive weight
BETA = 0.8           # false-negative weight
RADIUS_M = 300.0     # triangular kernel support
RADIUS_PX = 3.0      # 300 m at 100 m pixels
EPS_METRIC = 1e-12

# --- sha256 pins (independently re-verified in this repository) --------------
PINS: dict[str, dict] = {
    "training_features.tif": {
        "bytes": 418_912_844,
        "sha256": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
        "official_data_tab_name": "gems-geodawn-numerical-features.tif",
    },
    "labels.tif": {
        "bytes": 425_830,
        "sha256": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
        "official_data_tab_name": "existing_faults.tif",
    },
    "sample_submission.tif": {
        "bytes": 1_599_597,
        "sha256": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
        "official_data_tab_name": "example_submission.tif",
    },
}

# Transport fallback: the 419 MB feature stack cannot live in one GitHub blob
# (>100 MB limit), so it travels as five parts in a public team mirror.
# This is a *transport* mirror, not an official publisher; the sha256 pins above
# establish identity with the pinned mirror bytes only; organizer provenance is unverified.
BRIDGE_REPO = "buffedlizard55-lab/6GEMSDOE"
BRIDGE_COMMIT = "e2fe3f41c6f5dd2dcb2fc91958ee67698f114ada"
BRIDGE_PARTS = [
    ("part-000", 94_371_840,
     "0a330f8951af6c921029e25c84a579319d2db554d62d30d894d6ddc97f98cff7"),
    ("part-001", 94_371_840,
     "3c98037b2c997e3bbfcdfc2d9a982e8b820a77410dd7404b05cdb80594922c50"),
    ("part-002", 94_371_840,
     "c375c4dbc40c59bbaece572b5e348700b75935f9a30c879c82b6417e0836f31c"),
    ("part-003", 94_371_840,
     "b164159e6d0cb2595bc9f63a948af2646b124114a9c5921880c7516092137320"),
    ("part-004", 41_425_484,
     "fa0a6f9c936fac1d6f20ca37f5929b2d60bf7a80f3d477dcab886f941aee2696"),
]

# --- the 19 official feature bands (band index 1..19) ------------------------
# Names and descriptions read from the official raster's per-band TIFF tags.
FEATURE_BANDS: list[tuple[str, str]] = [
    ("mag_anom", "Magnetic anomaly - deviation from expected Earth's magnetic field"),
    ("rtp", "Reduced to pole magnetic data - magnetic anomaly corrected for latitude effects"),
    ("tmi_hg", "Total magnetic intensity horizontal gradient - rate of change in horizontal direction"),
    ("geod_2ndinv", "Geodetic second invariant - measure of strain rate tensor magnitude"),
    ("iso_grav_anom_slope", "Isostatic gravity anomaly slope - gradient of gravity after isostatic correction"),
    ("tc", "Tilt angle or total curvature - magnetic field derivative for edge detection"),
    ("geod_shearrate", "Geodetic shear rate - rate of angular deformation from GPS/InSAR"),
    ("geod_dilaterate", "Geodetic dilatation rate - rate of volumetric strain (expansion/contraction)"),
    ("tmi_vg", "Total magnetic intensity vertical gradient - rate of change in vertical direction"),
    ("deq_n100a15", "Distance to earthquake (n=100km radius, a=15deg azimuth parameters)"),
    ("iso_grav_anom_vg", "Isostatic gravity anomaly vertical gradient - vertical rate of change"),
    ("det_elev", "Detrended elevation - topography with regional trends removed"),
    ("iso_grav_anom", "Isostatic gravity anomaly - gravity after compensating for topographic mass"),
    ("tmi", "Total magnetic intensity - total strength of magnetic field"),
    ("depth_to_base_surf", "Depth to basement surface - thickness of sedimentary cover"),
    ("ieq_n100a15", "Earthquake intensity or density (n=100km radius, a=15deg parameters)"),
    ("cond_surf", "Conductivity surface - electrical conductivity of subsurface"),
    ("iso_grav_anom_hg", "Isostatic gravity anomaly horizontal gradient - horizontal rate of change"),
    ("det_elev_slope", "Detrended elevation slope - gradient of elevation after detrending"),
]

BAND_INDEX = {name: i for i, (name, _) in enumerate(FEATURE_BANDS)}


def band(name: str) -> int:
    """1-based rasterio band index for a feature name."""
    return BAND_INDEX[name] + 1
