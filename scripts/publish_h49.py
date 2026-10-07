#!/usr/bin/env python3
"""Publish the H49 artifact: ZIP + note + per-artifact receipt + the site's current-artifact pointer.

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


def main() -> int:
    bundle = json.loads((ROOT / "evidence" / "submission" / "bundle_h49.json").read_text())
    cert = json.loads((ROOT / "evidence" / "h49" / "conformal_certificate.json").read_text())
    audit_path = ROOT / "evidence" / "h49" / "pinned-public-inventory-uniqueness.json"
    public_audit = json.loads(audit_path.read_text()) if audit_path.exists() else None
    name = bundle["submission_name"]
    tif = DL / f"{name}.tif"
    assert tif.is_file(), tif
    digest = sha256(tif)
    assert digest == bundle["sha256"][1], "on-disk TIFF does not match the bundle hash"
    format_receipt = dict(bundle["format_receipt"])
    format_receipt["path"] = f"docs/downloads/{name}.tif"

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
        format_receipt=format_receipt,
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
    public_summary = None
    if public_audit is not None:
        public_summary = dict(
            report="data/pinned-public-inventory-uniqueness.json",
            generated_utc=public_audit["generated_utc"],
            inventory_sha256=public_audit["inventory_sha256"],
            public_repositories_in_inventory=public_audit["public_repositories_in_inventory"],
            comparisons=public_audit["comparisons"],
            exact_matches=public_audit["exact_matches"],
            bounded_unique=public_audit["bounded_unique"],
            global_unique_proven=public_audit["global_unique_proven"],
            max_jaccard=public_audit["max_jaccard"],
            unexamined_or_failed=public_audit["unexamined_or_failed"],
            failed_repository_inventories=public_audit["failed_repository_inventories"],
        )
    site = dict(
        schema_version=1,
        status="RESEARCH_ONLY_SLOT_GATE_CLOSED",
        slot_authorized=False,
        slot_gate=dict(
            authorized=False,
            reason=("The mean-maximizing shipped arm is an after-results amendment; the B "
                    "preregistration addendum and sweep evidence first appear together in Git, so "
                    "prospective timing is not independently auditable. The fixed-arm split-"
                    "conformal floor is therefore a nominal diagnostic, not a guarantee for the "
                    "complete adaptive rule. The paired 90% conformal lower bound on improvement "
                    "over the incumbent is below zero for both candidate arms."),
            next_step=("Use a new spatially independent or otherwise defensibly held-out dataset; "
                       "preregister the rule and the paired-improvement criterion before scoring; "
                       "do not spend a slot before that gate passes."),
            paired_vs_incumbent=cert["paired_vs_incumbent"],
            preregistration_provenance="NOT_INDEPENDENTLY_AUDITABLE_FROM_GIT_HISTORY",
        ),
        hypothesis_ids=["H49-B (signed polarity coherence)", "H49 round-2 emission control"],
        filename=f"{name}.tif",
        download_relative_to_docs=f"downloads/{name}.tif",
        submission_name=name,
        portal_note=note,
        portal_note_characters=len(note),
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        format_validation=format_receipt,
        zip=receipt["zip"],
        operating_point=bundle["operating_point"],
        chosen_spacing_px=bundle["operating_point"]["min_spacing_px"],
        chosen_spacing_m=bundle["operating_point"]["min_spacing_m"],
        conformal_confidence_pct=cert["confidence_pct"],
        conformal_result_status="NOMINAL_FIXED_ARM_DIAGNOSTIC_NOT_FULL_ADAPTIVE_PIPELINE_GUARANTEE",
        conformal_nominal_floor_primary_instrument=cb["certified_floor"],
        conformal_primary_instrument=cb["instrument"],
        conformal_n_calibration_blocks=cb["n_calibration_blocks"],
        conformal_order_statistic_k=cb["order_statistic_k"],
        conformal_floors_by_alpha=cb["floors_by_alpha"],
        conformal_corroborating_instrument=ca["instrument"],
        conformal_corroborating_floor=ca["certified_floor"],
        conformal_leave_one_out_worst_floor=cb["leave_one_out_worst_floor"],
        conformal_repeated_split=cert["repeated_split_robustness"],
        descriptive_operating_point_screens=cert["gates"],
        paired_vs_incumbent=cert["paired_vs_incumbent"],
        selection=dict(shipped=cert["shipped_selection"],
                       preregistered=cert["preregistered_selection"],
                       amendment=cert["amendment_justification"]),
        uniqueness=bundle["uniqueness"],
        public_uniqueness=public_summary,
        organizer_score=None,
        what_this_does_not_establish=[
            "no leaderboard score is measured, predicted or implied",
            "Instrument B is a public proxy built from SGMC, which also contains non-fault contacts",
            "geological-block exchangeability is an assumption, not an established fact",
            "the 400 re-splits reuse the same 39 blocks and are stability diagnostics, not new independent validation data",
            "Git history first records the B preregistration addendum in the same commit as the B sweep evidence",
            "the shipped mean-maximizing rule is an after-results amendment; the nominal fixed-arm floor does not certify the full adaptive procedure",
            "the 90% conformal lower bound on paired improvement over the incumbent is negative for both candidate arms",
            "the previous artifact in this repository (gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif) was never scored by the organiser either",
        ],
        data_authentication="SHA-256 pinned repository mirrors, not authenticated DrivenData downloads",
    )
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    if public_audit is not None:
        (SITE_DATA / "pinned-public-inventory-uniqueness.json").write_text(audit_path.read_text())
    (SITE_DATA / "current-artifact.json").write_text(json.dumps(site, indent=2) + "\n")
    print(f"wrote {zip_path.name} ({zip_path.stat().st_size} B), {name}.txt, {name}.json, "
          f"docs/data/current-artifact.json")
    print(f"tif sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
