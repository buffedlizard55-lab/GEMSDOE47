from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
H60_BASE = "gems47-h60-lidarscarp-s2p0-20261007"
H60_NAN = f"downloads/{H60_BASE}-nanoutside.tif"
H60_ALLFINITE = f"downloads/{H60_BASE}-allfinite.tif"
H60_NAN_SHA256 = "d75ab9e282422d9592bc835c5cf719b22e6c564730de1f5fc42b57fc5bac2c01"
H60_ALLFINITE_SHA256 = "4ee074230a305fce6768012fc33380bf196c89170e70050a77cf4a44d74ef14c"
H60_ZIP = f"downloads/{H60_BASE}.zip"
H50_TIF = "downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif"
H50_SHA256 = "97e3c3816cd6b458d01e34d7022f871935bb57710e3982a11d9edaec13e91a17"
H49_TIF = "downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif"
H49_SHA256 = "a5abe022b8352971dc2f27a2733f289607d4a9ac44b60335bde7c822826c2a1b"
H49_BASE = "gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3"
H47QC_TIF = "downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.tif"
H47QC_SHA256 = "3866b60cf91b4f6bff2ef694153550aa97a744a3091a57ef9f83da41e16b91b2"
H50A_TIF = "downloads/gems47-h50a-corridor-s1p5-b3-20261007-4096e1f9d19b-template-nanoutside.tif"
H50A_SHA256 = "6dfe602d35b0f0755eae9a7a8bcc2e6f81efaf291f97341d588ee818b2e07cc5"


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.download_links: list[str] = []
        self.tiff_links: list[str] = []
        self.downloadable_tiff_links: list[str] = []
        self.assets: list[str] = []
        self.ids: set[str] = set()
        self.title_text = ""
        self.in_title = False
        self.language = None
        self.descriptions = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang")
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag in ("script", "img") and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("href"):
            self.assets.append(attrs["href"])
        if tag == "a" and attrs.get("href"):
            href = attrs["href"]
            self.links.append(href)
            if "download" in attrs:
                self.download_links.append(href)
            if urlparse(href).path.lower().endswith((".tif", ".tiff")):
                self.tiff_links.append(href)
                if "download" in attrs:
                    self.downloadable_tiff_links.append(href)
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.descriptions += 1
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data.strip()


class SiteTests(unittest.TestCase):
    def test_all_deployed_nested_links_and_assets_stay_inside_pages_artifact(self):
        for page in sorted((ROOT / "docs").rglob("*.html")):
            parser = _PageParser()
            parser.feed(page.read_text(encoding="utf-8"))
            for href in parser.links + parser.assets:
                url = urlparse(href)
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (page.parent / unquote(url.path)).resolve()
                self.assertTrue(target.is_relative_to((ROOT / "docs").resolve()), href)
                self.assertTrue(target.exists(), f"{page}: {href}")

    def test_all_local_html_links_and_fragments_resolve(self):
        pages = sorted([ROOT / "index.html", *ROOT.glob("docs/*.html")])
        self.assertGreaterEqual(len(pages), 4)
        for page in pages:
            parser = _PageParser()
            parser.feed(page.read_text(encoding="utf-8", errors="replace"))
            for href in parser.links:
                parsed = urlparse(href)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (page.parent / unquote(parsed.path)).resolve()
                self.assertTrue(target.exists(), f"{page.relative_to(ROOT)} has broken link {href}")
                if parsed.fragment and target.suffix.lower() == ".html":
                    target_page = _PageParser()
                    target_page.feed(target.read_text(encoding="utf-8", errors="replace"))
                    self.assertIn(parsed.fragment, target_page.ids, f"broken fragment {href} in {page}")

    def test_pages_have_accessible_metadata(self):
        pages = sorted([ROOT / "index.html", *ROOT.glob("docs/*.html")])
        for page in pages:
            parser = _PageParser()
            parser.feed(page.read_text(encoding="utf-8", errors="replace"))
            self.assertEqual(parser.language, "en", page.name)
            self.assertTrue(parser.title_text, page.name)
            self.assertEqual(parser.descriptions, 1, page.name)

    def test_current_user_guidance_keeps_no_upload_and_acceptance_boundary(self):
        names = (
            "index.html", "executive-summary.html", "current-status.html", "h60.html",
            "submit.html", "portal-checklist.html", "HOW_TO_SUBMIT.html", "COMPLIANCE.html",
            "RESULTS.html", "REMAINING_WORK.html", "all-downloads.html", "leaderboard.html",
            "sources.html",
        )
        for name in names:
            text = (ROOT / "docs" / name).read_text(encoding="utf-8").lower()
            self.assertTrue(
                "no upload" in text or "do not upload" in text or "no portal action" in text
                or "no competition upload" in text or "no portal upload" in text,
                f"{name}: missing no-upload boundary",
            )
            self.assertNotIn("ok to download and submit", text, name)
            self.assertNotIn("ok to submit.", text, name)

        for name in ("index.html", "executive-summary.html", "current-status.html", "h60.html"):
            text = (ROOT / "docs" / name).read_text(encoding="utf-8").lower()
            self.assertIn("organizer acceptance", text, name)
        c1 = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn("H47-C1", c1)
        self.assertIn("GATE CLOSED", c1)
        self.assertIn("not promoted", c1.lower())

    def test_current_downloads_point_to_nanoutside_for_inspection(self):
        current_pages = (
            "index.html", "executive-summary.html", "current-status.html", "h60.html",
            "submit.html", "portal-checklist.html", "HOW_TO_SUBMIT.html",
        )
        for name in current_pages:
            text = (ROOT / "docs" / name).read_text(encoding="utf-8").lower()
            self.assertIn(f"{H60_BASE}-nanoutside.tif".lower(), text, name)
            self.assertIn("inspection", text, name)
            self.assertTrue(
                "untested" in text or "not been tested" in text or "acceptance unknown" in text,
                name,
            )
            self.assertIn(H60_NAN_SHA256, text, name)

        home = _PageParser()
        home.feed((ROOT / "docs" / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(home.downloadable_tiff_links, [H60_NAN])
        self.assertNotIn(H60_ALLFINITE, home.downloadable_tiff_links)

        register = (ROOT / "docs" / "all-downloads.html").read_text(encoding="utf-8")
        row = register.split("<!--h60:row-->", 1)[1].split("</tr>", 1)[0]
        self.assertIn(H60_NAN.split("/")[-1], row)
        self.assertIn("download", row)
        self.assertIn("All-finite range diagnostic", row)
        self.assertIn("Audit ZIP (all-finite variant)", row)
        self.assertIn("no competition upload", row.lower())
        self.assertNotIn("OK TO SUBMIT", row)

    def test_h60_current_status_rules_leaderboard_and_c1_gate_receipt(self):
        current = json.loads((ROOT / "docs" / "data" / "current-artifact.json").read_text())
        self.assertEqual(current["status"], "H60_LOCALLY_PROMOTED_ORGANIZER_ACCEPTANCE_UNTESTED")
        self.assertTrue(current["scientific_promotion_gate_passed_locally"])
        self.assertFalse(current["organizer_acceptance_established"])
        self.assertFalse(current["upload_authorized_in_this_review"])
        self.assertFalse(current["slot_authorized_in_this_review"])
        self.assertFalse(current["upload_performed_in_this_review"])
        self.assertEqual(current["portal_submission_eligibility"], "not established")
        self.assertEqual(current["h47_c1_gate"]["status"], "CLOSED_NOT_PROMOTED")
        self.assertFalse(current["h47_c1_gate"]["c1_gate_reopened_by_h60"])

        nan_variant = current["preferred_local_format_review_variant"]
        self.assertEqual(nan_variant["sha256"], H60_NAN_SHA256)
        self.assertEqual(nan_variant["status"], "inspection_only")
        self.assertTrue(nan_variant["matches_published_null_or_nan_outside_wording_on_local_readback"])
        self.assertFalse(nan_variant["organizer_acceptance_established"])
        allfinite = current["range_check_diagnostic_variant"]
        self.assertEqual(allfinite["sha256"], H60_ALLFINITE_SHA256)
        self.assertFalse(allfinite["matches_published_null_or_nan_outside_wording_on_local_readback"])
        self.assertEqual(allfinite["status"], "diagnostic_only")

        rules = current["official_rules"]
        self.assertEqual(rules["published_feedback_allowance"], "up to three scoring/feedback submissions per week")
        self.assertIn("one final selected file", rules["final_selection"])
        self.assertFalse(rules["account_specific_eligibility_and_remaining_opportunities_known"])

        board = json.loads((ROOT / "docs" / "data" / "leaderboard-read-20261007.json").read_text())
        self.assertEqual(board["observed_date"], "2026-10-07")
        self.assertFalse(board["file_to_score_mapping_verified"])
        self.assertEqual([(r["rank"], r["score"]) for r in board["rows"]],
                         [(1, 0.3774), (7, 0.3195), (13, 0.2778)])
        self.assertIsNone(board["rows"][0]["participant"])
        self.assertIn("not preserved", board["rows"][0]["participant_name_status"])

        feed = json.loads((ROOT / "docs" / "data" / "source-feed.json").read_text())
        self.assertFalse(feed["drivendata_automated_monitoring_enabled"])
        self.assertEqual(feed["leaderboard"]["observed_date"], "2026-10-07")
        self.assertEqual(feed["leaderboard"]["status"], "STALE_LAST_OBSERVATION_RETAINED")
        self.assertEqual(feed["leaderboard"]["latest_observation_file"], "leaderboard-read-20261007.json")
        self.assertEqual(len(feed["leaderboard"]["rows"]), 3)

        historical = json.loads((ROOT / "docs" / "data" / "leaderboard-read-20261006.json").read_text())
        self.assertEqual(historical["historical_status"], "HISTORICAL_OBSERVATION_SUPERSEDED_BY_2026-10-07_PARTIAL_READ")
        self.assertEqual(historical["superseded_by"], "data/leaderboard-read-20261007.json")

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Do not upload or spend a competition slot in this review", readme)
        self.assertIn("up to **three scoring/feedback submissions per week**", readme)
        self.assertIn("0.3195 was rank 7", readme)

    def test_h60_exact_byte_variants_match_encoding_audit_and_zip_contents(self):
        nan_path = ROOT / "docs" / H60_NAN
        allfinite_path = ROOT / "docs" / H60_ALLFINITE
        self.assertTrue(nan_path.is_file())
        self.assertTrue(allfinite_path.is_file())
        self.assertEqual(hashlib.sha256(nan_path.read_bytes()).hexdigest(), H60_NAN_SHA256)
        self.assertEqual(hashlib.sha256(allfinite_path.read_bytes()).hexdigest(), H60_ALLFINITE_SHA256)

        audit = json.loads((ROOT / "docs" / "data" / "h60-encoding-audit.json").read_text())
        self.assertFalse(audit["official_acceptance_tested"])
        self.assertFalse(audit["historical_range_error_cause_known"])
        nan_record = audit["variants"]["nanoutside"]
        self.assertEqual(nan_record["sha256"], H60_NAN_SHA256)
        self.assertEqual(nan_record["bytes"], 351_392)
        self.assertEqual(nan_record["valid_mask_cells"], 5_167_373)
        self.assertEqual(nan_record["nan_cells"], 7_111_787)
        self.assertTrue(nan_record["outside_valid_mask_cells_are_nan"])
        self.assertFalse(nan_record["organizer_acceptance_established"])
        allfinite_record = audit["variants"]["allfinite"]
        self.assertEqual(allfinite_record["sha256"], H60_ALLFINITE_SHA256)
        self.assertTrue(allfinite_record["all_values_in_unit_interval"])
        self.assertTrue(allfinite_record["outside_cells_are_finite_zero"])
        self.assertFalse(allfinite_record["published_null_or_nan_outside_convention_matches_local_readback"])
        archive = audit["archive"]
        self.assertEqual(archive["status"], "audit_bundle_not_an_upload_bundle")
        self.assertFalse(archive["contains_nanoutside_tiff"])

        with rasterio.open(nan_path) as src:
            self.assertEqual(src.count, 1)
            self.assertEqual(src.dtypes[0], "float32")
            self.assertEqual(src.width, 3292)
            self.assertEqual(src.height, 3730)
            self.assertEqual(src.shape, (3730, 3292))
            self.assertEqual(src.crs.to_string(), "EPSG:32611")
            self.assertEqual(src.res, (100.0, 100.0))
            self.assertTrue(np.isnan(src.nodata))
            values = src.read(1)
            valid = src.read_masks(1) > 0
        self.assertEqual(int(valid.sum()), 5_167_373)
        self.assertTrue(np.isfinite(values[valid]).all())
        self.assertTrue(np.isnan(values[~valid]).all())
        self.assertTrue(np.isin(values[valid], np.array([0.0, 1.0], dtype=np.float32)).all())
        self.assertEqual(int((values[valid] > 0).sum()), 37_654)
        outside = ~valid
        del values, valid

        with rasterio.open(allfinite_path) as src:
            self.assertEqual(src.count, 1)
            self.assertEqual(src.dtypes[0], "float32")
            self.assertEqual(src.width, 3292)
            self.assertEqual(src.height, 3730)
            self.assertEqual(src.shape, (3730, 3292))
            self.assertEqual(src.crs.to_string(), "EPSG:32611")
            self.assertEqual(src.res, (100.0, 100.0))
            self.assertIsNone(src.nodata)
            all_values = src.read(1)
        self.assertTrue(np.isfinite(all_values).all())
        self.assertTrue(((all_values >= 0) & (all_values <= 1)).all())
        self.assertTrue((all_values[outside] == 0).all())
        self.assertEqual(int((all_values > 0).sum()), 37_654)

        with zipfile.ZipFile(ROOT / "docs" / H60_ZIP) as archive_zip:
            names = archive_zip.namelist()
            self.assertEqual(set(names), {
                f"{H60_BASE}-allfinite.tif",
                f"{H60_BASE}-note.txt",
                f"{H60_BASE}-receipt.json",
            })
            self.assertEqual(archive_zip.read(f"{H60_BASE}-allfinite.tif"), allfinite_path.read_bytes())
            note = archive_zip.read(f"{H60_BASE}-note.txt").decode()
            self.assertIn("DO NOT UPLOAD", note)
            self.assertIn("not a portal submission note", note.lower())
            self.assertNotIn(f"{H60_BASE}-nanoutside.tif", names)

    def test_h60_science_receipt_preserves_history_but_clearly_withdraws_portal_claim(self):
        data_receipt_path = ROOT / "docs" / "data" / "h60-artifact.json"
        receipt = json.loads(data_receipt_path.read_text())
        self.assertEqual(receipt["kind_at_generation"], "primary_submission_candidate")
        self.assertEqual(receipt["kind"], "historical_local_scientific_promotion_receipt")
        self.assertTrue(receipt["promoted"])
        self.assertEqual(receipt["promotion_scope"], "local_scientific_gate_only")
        self.assertFalse(receipt["organizer_acceptance_established"])
        self.assertEqual(receipt["portal_submission_eligibility"], "not established")
        self.assertFalse(receipt["upload_authorized_in_this_review"])
        self.assertFalse(receipt["upload_performed_in_this_review"])
        self.assertFalse(receipt["slot_authorized_in_this_review"])
        self.assertEqual(receipt["sha256_tif"], H60_ALLFINITE_SHA256)
        self.assertEqual(receipt["download_url"], H60_ALLFINITE)
        self.assertIn("does not satisfy the published null/NaN-outside wording",
                      receipt["current_review_2026_10_07"]["current_interpretation"])
        self.assertEqual(receipt["current_review_2026_10_07"]["current_primary_format_variant"]["sha256"],
                         H60_NAN_SHA256)
        self.assertEqual(receipt["current_review_2026_10_07"]["current_status_receipt"],
                         "current-artifact.json")

        archive_receipt = json.loads(
            (ROOT / "docs" / "downloads" / f"{H60_BASE}-receipt.json").read_text()
        )
        self.assertFalse(archive_receipt["organizer_acceptance_established"])
        self.assertFalse(archive_receipt["upload_authorized_in_this_review"])
        note = (ROOT / "docs" / "downloads" / f"{H60_BASE}-note.txt").read_text()
        self.assertIn("DO NOT UPLOAD", note)
        self.assertIn("Future-only optional Note", note)
        self.assertIn("organizer acceptance of either encoding is untested", note.lower())

    def test_h50_h51_and_h50a_pages_are_historical_not_upload_guidance(self):
        h50 = (ROOT / "docs" / "h50.html").read_text(encoding="utf-8")
        self.assertIn("prior local scientific candidate", h50.lower())
        self.assertIn("not portal-accepted", h50.lower())
        self.assertIn("does not meet the published null/NaN-outside wording", h50)
        self.assertIn("H60 is the current local candidate", h50)
        self.assertIn("diagnostic for inspection only", h50)
        self.assertNotIn("submit this", h50.lower())
        self.assertNotIn("OK TO DOWNLOAD AND SUBMIT", h50)

        h51 = (ROOT / "docs" / "h51.html").read_text(encoding="utf-8")
        self.assertIn("near-duplicate of H50", h51)
        self.assertIn("DO NOT UPLOAD", h51)
        self.assertIn("41 contiguous blocks", h51)
        self.assertIn("owner-derived", h51)
        self.assertNotIn("OK to Submit", h51)
        self.assertNotIn("61 contiguous blocks", h51)

        h50a = (ROOT / "docs" / "h50a.html").read_text(encoding="utf-8")
        self.assertIn("H50 is also not portal-accepted", h50a)
        self.assertIn("no upload or slot use is authorized", h50a.lower())
        self.assertIn("It is not OK to submit this file", h50a)

        register = (ROOT / "docs" / "all-downloads.html").read_text(encoding="utf-8")
        h50row = register.split("<!--h50:row-->", 1)[1].split("</tr>", 1)[0]
        self.assertIn("PRIOR LOCAL SCIENTIFIC CANDIDATE", h50row)
        self.assertNotIn("OK TO SUBMIT", h50row)
        self.assertIn("all cells finite", h50row)
        self.assertIn("fail the published", h50row.lower())
        self.assertIn("No TIFF in this register is authorized", register)

    def test_h50_artifact_receipt_remains_historical_and_bytes_are_pinned(self):
        receipt = json.loads((ROOT / "docs" / "data" / "h50-artifact.json").read_text())
        target = ROOT / "docs" / receipt["download_url"]
        self.assertTrue(target.is_file())
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), H50_SHA256)
        self.assertTrue(receipt["promoted"])  # historical local scientific promotion
        page = (ROOT / "docs" / "h50.html").read_text(encoding="utf-8")
        self.assertIn("not portal-accepted", page.lower())
        self.assertIn("does not match the published outside-null/NaN wording", page)

    def test_irregularity_registry_copies_are_synced_and_include_h60_correction(self):
        canonical = json.loads((ROOT / "registry" / "irregularities.json").read_text())
        deployed = json.loads((ROOT / "docs" / "data" / "irregularities.json").read_text())
        self.assertEqual(canonical, deployed)
        record = next(x for x in canonical["irregularities"] if x["id"] == "IR-H60-001")
        self.assertEqual(record["severity"], "HIGH / current limitation")
        self.assertIn("Neither was organizer-tested", record["what_was_done"])
        self.assertIn("no-upload/no-slot", record["what_was_done"])
        self.assertEqual(record["human_page"], "docs/irregularities.html#ir-h60-001")

    def test_h49_is_explicitly_research_only_in_site_register_and_receipts(self):
        register = (ROOT / "docs" / "all-downloads.html").read_text(encoding="utf-8")
        row = register.split("<!--h49:row-->", 1)[1].split("<!--/h49:row-->", 1)[0]
        for phrase in (
            "RESEARCH ONLY", "NOT SLOT-AUTHORIZED", "DO NOT UPLOAD",
            "FAILS published null/NaN-outside requirement", "owner-reported d2.8 reference",
            "not an authenticated leaderboard incumbent",
        ):
            self.assertIn(phrase.lower(), row.lower())
        self.assertNotIn("current artifact", row.lower())
        self.assertNotIn(">Portal note<", row)
        self.assertIn("H49_RESULTS.html", row)
        self.assertIn("h49-format-contract-audit.json", row)

        receipt = json.loads((ROOT / "docs" / "downloads" / f"{H49_BASE}.json").read_text())
        self.assertFalse(receipt["slot_authorized"])
        self.assertFalse(receipt["submission_eligible"])
        self.assertFalse(receipt["format_review"]["outside_null_or_nan"])
        self.assertNotIn("portal_note", receipt)
        self.assertIn("withdrawn_portal_note", receipt)

        canonical = json.loads((ROOT / "evidence" / "h49" / "format-contract-audit.json").read_text())
        deployed = json.loads((ROOT / "docs" / "data" / "h49-format-contract-audit.json").read_text())
        self.assertEqual(canonical, deployed)
        self.assertEqual(canonical["artifact"]["sha256"], H49_SHA256)
        self.assertFalse(canonical["assessment"]["submission_eligible"])
        self.assertFalse(canonical["assessment"]["outside_null_or_nan"])

    def test_h47qc_legacy_upload_recommendation_is_withdrawn(self):
        evidence = json.loads((ROOT / "evidence" / "h47qc-screen-20261006.json").read_text())
        deployed = json.loads((ROOT / "docs" / "h47qc-screen-20261006.json").read_text())
        self.assertEqual(evidence, deployed)
        audit = evidence["artifact"]["format_audit"]
        self.assertTrue(audit["historical_recommended_for_upload_at_generation"])
        self.assertFalse(audit["recommended_for_upload"])
        self.assertFalse(evidence["artifact"]["format_review"]["outside_null_or_nan"])
        self.assertFalse(evidence["review_interpretation"]["submission_eligible"])
        self.assertFalse(evidence["review_interpretation"]["slot_authorized"])
        self.assertFalse(evidence["promotion_gate"]["upload_authorized"])
        runner = (ROOT / "scripts" / "run_h47qc.py").read_text(encoding="utf-8")
        self.assertIn('artifact_audit["required_local_checks_passed"]', runner)
        self.assertNotIn('if not artifact_audit["recommended_for_upload"]', runner)

    def test_h49_exact_tiff_readback_fails_outside_null_requirement(self):
        path = ROOT / "docs" / H49_TIF
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), H49_SHA256)
        with rasterio.open(path) as src:
            values = src.read(1)
            mask = src.read_masks(1)
            self.assertEqual(src.count, 1)
            self.assertEqual(src.dtypes[0], "float32")
            self.assertEqual(src.shape, (3730, 3292))
            self.assertEqual(src.crs.to_string(), "EPSG:32611")
            self.assertIsNone(src.nodata)
        self.assertEqual(values.size, 12_279_160)
        self.assertTrue(np.isfinite(values).all())
        self.assertEqual(int(np.isnan(values).sum()), 0)
        self.assertTrue((mask > 0).all())
        self.assertTrue(np.array_equal(np.unique(values), np.array([0.0, 1.0], dtype=np.float32)))
        self.assertEqual(int((values > 0).sum()), 37_612)
        audit = json.loads((ROOT / "evidence" / "h49" / "format-contract-audit.json").read_text())
        self.assertEqual(audit["footprint_basis"]["outside_cells"], 7_111_787)
        self.assertFalse(audit["assessment"]["outside_null_or_nan"])

    def test_legacy_h50_h60_site_and_submission_generators_fail_closed(self):
        scripts = {
            "build_site.py": "historical generator would overwrite current Markdown status",
            "publish_research_site.py": "historical renderer would overwrite the current H60 status",
            "update_site_h50.py": "historical H50 updater would restore upload-ready language",
            "update_site_h60.py": "historical H60 updater would restore upload-ready language",
            "build_submission_h50.py": "historical H50 builder writes zero outside",
            "build_submission_h60.py": "historical H60 builder writes zero outside",
        }
        for script, message in scripts.items():
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / script)],
                    cwd=ROOT, text=True, capture_output=True, check=False,
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("DISABLED:", result.stdout)
                self.assertIn(message.lower(), result.stdout.lower())
                imported = subprocess.run(
                    [sys.executable, "-c",
                     "import runpy; runpy.run_path(" + repr(str(ROOT / "scripts" / script))
                     + ", run_name='retired_import_test')"],
                    cwd=ROOT, text=True, capture_output=True, check=False,
                )
                self.assertNotEqual(imported.returncode, 0)
                self.assertIn("DISABLED:", imported.stderr)

    def test_h49_unsafe_publisher_and_site_rewriters_fail_closed(self):
        scripts = {
            "build_submission_h49.py": "writes finite zeros outside",
            "publish_h49.py": "withdrawn portal note",
            "report_h49.py": "overwrite the corrected caveats",
            "update_site_h49.py": "overwrite current pages",
            "run_conformal_h49.py": "historical H49 v1 analysis is superseded",
        }
        for script, message in scripts.items():
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / script)],
                    cwd=ROOT, text=True, capture_output=True, check=False,
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("DISABLED:", result.stdout)
                self.assertIn(message.lower(), result.stdout.lower())

    def test_root_landing_page_is_a_fresh_mirror_of_docs_index(self):
        """Pages serves main:/ so the root index.html is what visitors land on.

        Regression test for IR-2026-10-08-A: the root page silently kept offering
        stale content after the site moved on. The mirror rule: every relative
        href/src repointed under docs/, data-base set to docs/.
        """
        import re

        source = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

        def prefix(match: re.Match) -> str:
            attr, target = match.group(1), match.group(2)
            if re.match(r"(?:[a-z][a-z0-9+.-]*:|#|/)", target):
                return match.group(0)
            return f'{attr}="docs/{target}"'

        expected = re.sub(r'(href|src)="([^"]+)"', prefix, source).replace(
            'data-base=""', 'data-base="docs/"'
        )
        actual = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
