#!/usr/bin/env python3
"""Retired legacy conformal/mass-ceiling experiment.

Its historical score/raster mappings and assumed coverage are not authenticated
or promotion evidence. Do not run this script or use its old ceiling to claim
DTI 0.3195 is unreachable. See README.md, docs/COMPLIANCE.md, and docs/RESULTS.md.
"""

import sys


def main() -> int:
    print(
        "RETIRED: scripts/run_conformal.py used calibration outcomes to select candidates and "
        "then reused those outcomes for the reported floor. Its historical results are not "
        "promotion evidence; no analysis or file write was performed.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
