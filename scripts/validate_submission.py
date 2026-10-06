#!/usr/bin/env python3
"""Validate the exact persisted bytes of a prospective competition GeoTIFF."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gemsdoe47.validation import validate_submission, write_json_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", required=True, type=Path)
    parser.add_argument("--template", required=True, type=Path, help="official sample-submission GeoTIFF (use its actual authorized-download path)")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--features", type=Path, help="official training_features.tif; finite valid pixels define footprint")
    source.add_argument("--footprint-mask", type=Path, help="one-band binary mask; nonzero valid pixels define footprint")
    parser.add_argument("--report", type=Path, help="optional JSON report path")
    args = parser.parse_args()
    try:
        report = validate_submission(
            args.submission,
            args.template,
            features_path=args.features,
            footprint_mask_path=args.footprint_mask,
        )
    except (OSError, ValueError, RuntimeError) as error:
        print(f"VALIDATION FAILED\n{error}", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        write_json_report(report, args.report)
        print(f"\nReport saved: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
