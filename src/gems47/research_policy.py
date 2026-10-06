"""Keep retired, unvalidated builders out of the scientific release path."""
from __future__ import annotations

import sys
from pathlib import Path


def require_research_only() -> None:
    """An explicit opt-in is for education only, never a competition-slot gate."""
    if "--research-only" not in sys.argv:
        print("RETIRED submission builder: no eligible candidate, no slot. Use the current "
              "preregistered pipeline. --research-only permits historical educational reproduction "
              "in ignored cache only; it never authorizes uploading.", file=sys.stderr)
        raise SystemExit(2)
    sys.argv.remove("--research-only")


def reject_pages_output(path: Path, root: Path) -> None:
    if path.resolve().is_relative_to((root / "docs").resolve()):
        raise ValueError("retired educational builders cannot overwrite the Pages release or downloads")
