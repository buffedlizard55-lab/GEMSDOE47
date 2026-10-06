#!/usr/bin/env python3
"""Retired historical builder — fail closed.

The previous implementation emitted a delete-only subset of a published sibling
mask, rewrote the current result ledger, and attached an unsupported modeled
score/conformal-floor claim. That artifact is not eligible for submission. This
entry point is intentionally disabled; the source history records the old code.

Use the current research report only for review. No script in this repository
is authorized to create or submit a competition candidate without a new,
preregistered spatial-holdout promotion decision.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "RETIRED: this builder would recreate a delete-only historical artifact "
        "with withdrawn score/conformal claims. No output was written. See "
        "docs/analysis.md and docs/validation-h47b-20261006.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
