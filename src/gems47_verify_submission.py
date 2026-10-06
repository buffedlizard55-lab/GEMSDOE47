#!/usr/bin/env python3
"""Retired verifier entry point — it assumed a now-withdrawn submission ledger.

Use ``scripts/validate_submission.py`` with current authorized template/feature
paths for byte-level checks. That local format check cannot promote a candidate.
H47-B is research-only and must not be uploaded; see docs/analysis.md.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "RETIRED: no submission exists in notes/results.json. This verifier "
        "assumed a withdrawn candidate and score ledger. No submission check "
        "was run. See docs/validation-h47b-20261006.md and use "
        "scripts/validate_submission.py only for local format checks.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
