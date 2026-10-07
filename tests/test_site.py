from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
C1_TIF = "downloads/gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif"
C1_SHA256 = "e6eea1956b8f76ffef2f4867a6e2ac0bef078c0c61c3711e44eb07e93cb089d0"
H47QC_TIF = "downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.tif"
H47QC_SHA256 = "3866b60cf91b4f6bff2ef694153550aa97a744a3091a57ef9f83da41e16b91b2"
H49_TIF = "downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif"
H49_SHA256 = "a5abe022b8352971dc2f27a2733f289607d4a9ac44b60335bde7c822826c2a1b"
H49_BASE = "gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3"
H50_TIF = "downloads/gems47-h50-slopeanom-s2p8-20261007-nanoutside.tif"
H50_ALLFINITE_TIF = "downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif"
H51_TIF = "downloads/gems47-h51-multiscale-s2p8-20261007-nanoutside.tif"
H50_SHA256 = "2e32d8ed384692bc44ff768ca5d3814ed48d7b627ba3c818743ee13ab3538d5b"
H50_ALLFINITE_SHA256 = "97e3c3816cd6b458d01e34d7022f871935bb57710e3982a11d9edaec13e91a17"
H51_SHA256 = "e6eb13f671e2663b4f69e94307dfcac840bf9039cb411ab7b815cf029301fa43"
H50A_TIF = "downloads/gems47-h50a-corridor-s1p5-b3-20261007-4096e1f9d19b-template-nanoutside.tif"
H50A_SHA256 = "6dfe602d35b0f0755eae9a7a8bcc2e6f81efaf291f97341d588ee818b2e07cc5"


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.title_text = ""
        self.in_title = False
        self.language = None
        self.descriptions = 0
        self.tiff_links: list[str] = []
        self.assets: list[str] = []

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
            self.links.append(attrs["href"])
            if urlparse(attrs["href"]).path.lower().endswith((".tif", ".tiff")):
                self.tiff_links.append(attrs["href"])
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
                self.assertTrue(target.is_file(), f"{page}: {href}")

    def test_home_and_summary_lead_with_h50_review_file_and_limits(self):
        """The homepage and executive summary make the exact H50 review bytes prominent."""
        for name in ("index.html", "executive-summary.html"):
            text = (ROOT / "docs" / name).read_text(encoding="utf-8")
            self.assertIn(H50_TIF.split("/")[-1], text, name)
            self.assertIn("Download H50 NaN-outside GeoTIFF", text, name)
            self.assertIn("not organizer-accepted", text.lower(), name)
            self.assertIn("2.8 px / 280 m", text, name)
            self.assertIn("0.095701", text, name)
            self.assertIn("90%", text, name)
            self.assertIn("block-score exchangeability", text.lower(), name)
            self.assertIn("H51", text, name)
            self.assertIn("H49", text, name)
            self.assertIn("h50 slope-anomaly d2p8 conformal90", text, name)
            self.assertNotIn("OK TO SUBMIT", text, name)
            self.assertNotIn("submit this", text.lower(), name)
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertLess(home.index(H50_TIF.split("/")[-1]), home.index("Documented spatially blocked"))
        summary = (ROOT / "docs" / "executive-summary.html").read_text(encoding="utf-8")
        self.assertLess(summary.index(H50_TIF.split("/")[-1]), summary.index("H50 spacing and conditional"))

    def test_homepage_offers_h50_plus_labelled_research_downloads(self):
        text = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        parser = _PageParser()
        parser.feed(text)
        offered = {urlparse(link).path.lstrip("./") for link in parser.tiff_links}
        self.assertEqual(offered, {H50_TIF})
        target = ROOT / "docs" / H50_TIF
        self.assertTrue(target.is_file())
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), H50_SHA256)
        lower = text.lower()
        self.assertIn("locally promoted", lower)
        self.assertIn("not organizer-accepted", lower)
        self.assertIn("no upload", lower)
        self.assertIn("no fresh h51-specific", lower)
        self.assertIn("0.165881", text)
        self.assertIn("0.049421", text)
        self.assertIn("h49", lower)
        self.assertIn("0.040976", text)
        self.assertIn("0.038014", text)
        self.assertIn("does not literally satisfy", lower)
        self.assertNotIn("OK TO SUBMIT", text)

    def test_h50_artifact_receipt_is_published_and_matches_the_bytes(self):
        receipt_path = ROOT / "docs" / "data" / "h50-artifact.json"
        self.assertTrue(receipt_path.is_file())
        receipt = json.loads(receipt_path.read_text())
        target = ROOT / "docs" / receipt["download_url"]
        self.assertTrue(target.is_file(), f"published TIFF missing: {target}")
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), receipt["sha256_tif"])
        self.assertEqual(receipt["sha256_tif"], H50_SHA256)
        self.assertTrue(receipt["promoted"])
        self.assertTrue(receipt["local_promotion_gate_passed"])
        self.assertFalse(receipt["submission_eligible"])
        self.assertFalse(receipt["slot_authorized"])
        self.assertFalse(receipt["organizer_acceptance_established"])
        self.assertTrue(receipt["readback_checks"]["all_in_unit_interval_inside"])
        self.assertTrue(receipt["readback_checks"]["nan_outside_footprint"])
        self.assertEqual(receipt["format"]["nodata"], "NaN")
        self.assertEqual(receipt["format"]["outside_footprint"], "NaN")
        self.assertEqual(receipt["budget"], 37654)
        self.assertEqual(receipt["screen_selected_spacing_px"], 2.8)
        self.assertAlmostEqual(receipt["conformal"]["conditional_lower_floor_dti"], 0.095701, places=5)
        self.assertGreaterEqual(receipt["conformal"]["coverage_at_least_if_exchangeable"], 0.90)
        self.assertFalse(receipt["conformal"]["exchangeability_verified"])
        self.assertEqual(receipt["uniqueness"]["exact_matches"], 0)
        self.assertLess(receipt["uniqueness"]["max_jaccard"], 0.5)
        self.assertIn("h50 slope-anomaly d2p8 conformal90", receipt["submission_note_field"])
        self.assertEqual(receipt["allfinite_diagnostic_variant"]["sha256"], H50_ALLFINITE_SHA256)
        self.assertFalse(receipt["allfinite_diagnostic_variant"]["satisfies_published_null_or_nan_outside_wording"])
        with rasterio.open(target) as src:
            values = src.read(1)
            mask = src.read_masks(1) > 0
            self.assertEqual(src.count, 1)
            self.assertEqual(src.dtypes[0], "float32")
            self.assertEqual(src.shape, (3730, 3292))
            self.assertEqual(src.crs.to_string(), "EPSG:32611")
            self.assertTrue(np.isnan(src.nodata))
            self.assertEqual(int(mask.sum()), 5_167_373)
            self.assertEqual(int(np.isnan(values).sum()), 7_111_787)
            self.assertTrue(np.isfinite(values[mask]).all())
            self.assertTrue(np.isnan(values[~mask]).all())
            self.assertTrue(np.isin(values[mask], [0.0, 1.0]).all())
            self.assertEqual(int((values[mask] > 0).sum()), 37_654)
        zip_path = ROOT / "docs" / receipt["zip_url"]
        with __import__("zipfile").ZipFile(zip_path) as archive:
            self.assertEqual(archive.namelist(), [target.name])
            self.assertEqual(archive.read(target.name), target.read_bytes())

    def test_h50_evidence_page_links_only_inside_the_pages_artifact(self):
        page = (ROOT / "docs" / "h50.html").read_text(encoding="utf-8")
        self.assertIn("LOCALLY PROMOTED PUBLIC-PROXY CANDIDATE", page)
        self.assertNotIn("OK TO SUBMIT", page)
        self.assertIn(H50_TIF.split("/")[-1], page)
        self.assertIn("h50.html", page)
        self.assertNotIn("../", page)
        self.assertIn("0.0957 DTI", page)
        self.assertIn("conditional lower floor", page)
        for name in ("h50-instrument-ranking.json", "h50-screen.json",
                     "h50-field-scan.json", "h50-budget-profile.json"):
            self.assertTrue((ROOT / "docs" / "data" / name).is_file(), name)
            self.assertIn(name, page)

    def test_h50a_sibling_artifact_is_registered_as_research_only(self):
        """The H50a export merged in from main stays labelled research-only."""
        register = (ROOT / "docs" / "all-downloads.html").read_text(encoding="utf-8")
        self.assertIn(H50A_TIF.split("/")[-1], register)
        self.assertIn(H50A_SHA256, register)
        self.assertIn("DO NOT UPLOAD", register)
        page = (ROOT / "docs" / "h50a.html").read_text(encoding="utf-8")
        self.assertIn("research only", page.lower())
        self.assertIn("do not submit this file", page.lower())
        self.assertIn("h50.html", page)
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn(H50_TIF.split("/")[-1], home)
        self.assertNotIn(H50A_TIF.split("/")[-1], home,
                         "H50a must not be offered as a download on the home page")

    def test_h51_is_research_only_and_inherited_h50_conformal_result_is_not_applied(self):
        receipt = json.loads((ROOT / "docs" / "data" / "h51-artifact.json").read_text())
        self.assertEqual(receipt["kind"], "research_only_candidate")
        self.assertFalse(receipt["promoted"])
        self.assertFalse(receipt["local_promotion_gate_passed"])
        self.assertFalse(receipt["submission_eligible"])
        self.assertFalse(receipt["slot_authorized"])
        self.assertFalse(receipt["organizer_acceptance_established"])
        conformal = receipt["conformal"]
        self.assertFalse(conformal["applies_to_h51"])
        self.assertIsNone(conformal["coverage_at_least"])
        self.assertIsNone(conformal["certified_floor_dti"])
        self.assertTrue(conformal["inherited_h50_context"]["not_transferable_to_h51"])
        target = ROOT / "docs" / H51_TIF
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), H51_SHA256)
        with rasterio.open(target) as src:
            values = src.read(1)
            mask = src.read_masks(1) > 0
            self.assertEqual(src.count, 1)
            self.assertEqual(src.dtypes[0], "float32")
            self.assertEqual(src.shape, (3730, 3292))
            self.assertEqual(src.crs.to_string(), "EPSG:32611")
            self.assertTrue(np.isnan(src.nodata))
            self.assertEqual(int(mask.sum()), 5_167_373)
            self.assertEqual(int(np.isnan(values).sum()), 7_111_787)
            self.assertTrue(np.isfinite(values[mask]).all())
            self.assertTrue(np.isnan(values[~mask]).all())
            self.assertEqual(int((values[mask] > 0).sum()), 37_654)
        page = (ROOT / "docs" / "h51.html").read_text(encoding="utf-8")
        self.assertIn("RESEARCH ONLY", page)
        self.assertIn("no H51-specific certificate", page)
        self.assertIn("Do not transfer the H50 result to H51", page)
        self.assertNotIn("OK to Submit", page)

    def test_h49_is_explicitly_research_only_in_site_register_and_receipts(self):
        register = (ROOT / "docs" / "all-downloads.html").read_text(encoding="utf-8")
        row = register.split("<!--h49:row-->", 1)[1].split("<!--/h49:row-->", 1)[0]
        for phrase in (
            "RESEARCH ONLY", "NOT SLOT-AUTHORIZED", "DO NOT UPLOAD",
            "FAILS published null/NaN-outside requirement", "owner-reported d2.8 reference",
            "not an authenticated leaderboard incumbent",
        ):
            self.assertIn(phrase.lower(), row.lower())
        h49row = row.split(f"{H49_BASE}.tif", 1)[1]
        self.assertIn("Archived H49 receipt", h49row)
        self.assertNotIn("current artifact", h49row.lower())
        self.assertNotIn(">Portal note<", h49row)
        self.assertIn("H49_RESULTS.html", h49row)
        self.assertIn("h49-format-contract-audit.json", h49row)

        current = json.loads((ROOT / "docs" / "data" / "current-artifact.json").read_text())
        self.assertEqual(current["hypothesis_id"], "H50")
        self.assertEqual(current["status"], "LOCALLY_PROMOTED_PUBLIC_PROXY_CANDIDATE_NOT_ORGANIZER_ACCEPTED")
        self.assertTrue(current["current_primary_artifact"])
        self.assertTrue(current["local_promotion_gate_passed"])
        self.assertFalse(current["slot_authorized"])
        self.assertFalse(current["submission_eligible"])
        self.assertFalse(current["organizer_acceptance_established"])
        self.assertTrue(current["format_review"]["outside_null_or_nan"])

        archived = json.loads((ROOT / "docs" / "data" / "h49-artifact.json").read_text())
        self.assertEqual(archived["status"], "RESEARCH_ONLY_FORMAT_REQUIREMENT_FAIL")
        self.assertFalse(archived["slot_authorized"])
        self.assertFalse(archived["submission_eligible"])
        self.assertFalse(archived["current_primary_artifact"])
        self.assertFalse(archived["format_review"]["outside_null_or_nan"])
        self.assertIn("historical_builder_format_receipt", archived)
        self.assertNotIn("portal_note", archived)

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

    def test_all_local_html_links_resolve(self):
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
                self.assertTrue(target.is_file(), f"{page.relative_to(ROOT)} has broken link {href}")
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

    def test_submission_guide_keeps_gates_and_h49_failure_visible(self):
        for name in ("executive-summary.html", "submit.html", "portal-checklist.html"):
            text = (ROOT / "docs" / name).read_text(encoding="utf-8").lower()
            self.assertIn("do not upload", text, name)
            self.assertIn("slot", text, name)
            self.assertIn("h49", text, name)
            self.assertIn("null-or-nan-outside", text, name)
            self.assertIn("owner-reported d2.8 reference", text, name)
            self.assertIn("not organizer-accepted", text, name)
        text = (ROOT / "docs" / "submit.html").read_text(encoding="utf-8")
        self.assertIn(H50_TIF.split("/")[-1], text)
        self.assertIn(H50_SHA256, text)
        self.assertIn("GEMSDOE47-H50-slope-anomaly-s2p8-20261007", text)
        self.assertIn("h50 slope-anomaly d2p8 conformal90", text)

if __name__ == "__main__":
    unittest.main()
