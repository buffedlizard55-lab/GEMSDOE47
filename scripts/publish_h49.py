#!/usr/bin/env python3
"""Historical H49 publisher retained for review; execution is disabled.

The original implementation writes a portal note and sets ``slot_authorized=True``. Those
claims were withdrawn after the exact TIFF failed the published outside-null/NaN requirement.
The CLI exits before reading evidence or writing files.

Historical implementation follows (not approved; do not run):



Everything is read out of ``evidence/submission/bundle_h49.json`` and
``evidence/h49/conformal_certificate.json`` -- no hash, byte count or floor is typed by hand.  The
ZIP is verified (exactly one member, whose sha256 equals the TIFF on disk) before the receipt that
claims it is written.

Run:  python3 scripts/publish_h49.py
Out:  docs/downloads/<name>.zip, <name>.txt, <name>.json, docs/data/current-artifact.json

The pointer uses its own filename on purpose: docs/data/current-submission.json stays the byte-identical
copy of evidence/current-submission.json (the H47-C1 screen receipt) that tests/test_current_artifact.py
checks, so an H49 upload cannot silently rewrite the record of an earlier screen.
"""
from __future__ import annotations

import hashlib
import json
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DL = ROOT / "docs" / "downloads"
SITE_DATA = ROOT / "docs" / "data"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _legacy_main() -> int:
    bundle = json.loads((ROOT / "evidence" / "submission" / "bundle_h49.json").read_text())
    cert = json.loads((ROOT / "evidence" / "h49" / "conformal_certificate.json").read_text())
    name = bundle["submission_name"]
    tif = DL / f"{name}.tif"
    assert tif.is_file(), tif
    digest = sha256(tif)
    assert digest == bundle["sha256"][1], "on-disk TIFF does not match the bundle hash"

    # ---- single-TIFF ZIP, verified
    zip_path = DL / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(tif, arcname=tif.name)
    with zipfile.ZipFile(zip_path) as zf:
        members = zf.namelist()
        assert members == [tif.name], members
        assert hashlib.sha256(zf.read(tif.name)).hexdigest() == digest

    # ---- portal note
    note = bundle["note_optional"]
    (DL / f"{name}.txt").write_text(note + "\n")

    # ---- per-artifact receipt
    receipt = dict(
        schema_version=1,
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        file=f"downloads/{name}.tif",
        bytes=bundle["operating_point"] and tif.stat().st_size,
        sha256=digest,
        submission_name=name,
        portal_note=note,
        portal_note_characters=len(note),
        zip=dict(file=f"downloads/{name}.zip", bytes=zip_path.stat().st_size,
                 sha256=sha256(zip_path), members=[tif.name], single_geotiff_verified=True),
        format_receipt=bundle["format_receipt"],
        operating_point=bundle["operating_point"],
        conformal=bundle["conformal"],
        uniqueness=bundle["uniqueness"],
        values_are_binary=bundle["values_are_binary"],
        recipe=bundle["recipe"],
        evidence=dict(bundle="evidence/submission/bundle_h49.json",
                      certificate=cert["sweeps"] and "evidence/h49/conformal_certificate.json",
                      sweep_a=cert["sweeps"]["a"]["path"], sweep_b=cert["sweeps"]["b"]["path"]),
    )
    (DL / f"{name}.json").write_text(json.dumps(receipt, indent=1) + "\n")

    # ---- the site's machine-readable pointer
    cb = cert["certificate"]["primary"]
    ca = cert["certificate"]["corroborating"]
    site = dict(
        schema_version=1,
        status="CERTIFIED_HOLDOUT_PASS_UNSCORED",
        slot_authorized=True,
        hypothesis_ids=["H49-B (signed polarity coherence)", "H49 round-2 emission control"],
        filename=f"{name}.tif",
        download_relative_to_docs=f"downloads/{name}.tif",
        submission_name=name,
        portal_note=note,
        portal_note_characters=len(note),
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        format_validation=bundle["format_receipt"],
        zip=receipt["zip"],
        operating_point=bundle["operating_point"],
        chosen_spacing_px=bundle["operating_point"]["min_spacing_px"],
        chosen_spacing_m=bundle["operating_point"]["min_spacing_m"],
        conformal_confidence_pct=cert["confidence_pct"],
        conformal_certified_floor_primary_instrument=cb["certified_floor"],
        conformal_primary_instrument=cb["instrument"],
        conformal_n_calibration_blocks=cb["n_calibration_blocks"],
        conformal_order_statistic_k=cb["order_statistic_k"],
        conformal_floors_by_alpha=cb["floors_by_alpha"],
        conformal_corroborating_instrument=ca["instrument"],
        conformal_corroborating_floor=ca["certified_floor"],
        conformal_leave_one_out_worst_floor=cb["leave_one_out_worst_floor"],
        conformal_repeated_split=cert["repeated_split_robustness"],
        gates=cert["gates"],
        selection=dict(shipped=cert["shipped_selection"],
                       preregistered=cert["preregistered_selection"],
                       amendment=cert["amendment_justification"]),
        uniqueness=bundle["uniqueness"],
        organizer_score=None,
        what_this_does_not_establish=[
            "no leaderboard score is measured, predicted or implied",
            "Instrument B is a public proxy built from SGMC, which also contains non-fault contacts",
            "the certificate is conditional on the shipped arm and assumes block exchangeability",
            "the previous artifact in this repository (gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif) "
            "was never scored by the organiser either",
        ],
        data_authentication="SHA-256 pinned repository mirrors, not authenticated DrivenData downloads",
    )
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    (SITE_DATA / "current-artifact.json").write_text(json.dumps(site, indent=2) + "\n")
    print(f"wrote {zip_path.name} ({zip_path.stat().st_size} B), {name}.txt, {name}.json, "
          f"docs/data/current-artifact.json")
    print(f"tif sha256 {digest}")
    return 0


def main() -> int:
    print("DISABLED: the historical H49 publisher would recreate a withdrawn portal note and slot-authorized pointer. No evidence read or file written.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
