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
H50_TIF = "downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif"
H50_SHA256 = "97e3c3816cd6b458d01e34d7022f871935bb57710e3982a11d9edaec13e91a17"
H60_TIF = "downloads/gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif"
H60_SHA256 = "4ee074230a305fce6768012fc33380bf196c89170e70050a77cf4a44d74ef14c"
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

    def test_home_and_summary_lead_with_h50_and_offer_it_for_submission(self):
        """The two pages the user reads must make the submittable file obvious."""
        for name in ("index.html", "executive-summary.html"):
            text = (ROOT / "docs" / name).read_text(encoding="utf-8")
            # a one-click download above the fold, before the page's <h1>
            self.assertLess(text.index("↓ Download GeoTIFF (submit this)"), text.index("<h1>"), name)
            self.assertIn(H50_TIF.split("/")[-1], text)
            self.assertIn("OK TO DOWNLOAD AND SUBMIT", text)
            self.assertIn("H50a template-format checkpoint", text)
            self.assertIn("It is not OK to submit this file", text)
            self.assertIn("2.0 px / 200 m", text)  # H60, the current primary
            self.assertIn("VALID FALLBACK", text)   # H50, the labelled fallback
            self.assertIn("h60 lidar-scarp d2p0 conformal90", text)
            self.assertIn("split-conformal", text)
            self.assertIn("conditional on block exchangeability", text)
            # the older research artifacts must still be labelled as not submittable
            self.assertIn("RESEARCH-ONLY", text)
            self.assertIn("DO NOT UPLOAD", text)
            self.assertIn("H49 historical", text)
            self.assertIn("H47-QC geothermometer screen", text)
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn(H60_SHA256, home)
        # the H50 fallback bytes remain pinned on the register and H50 evidence pages
        register = (ROOT / "docs" / "all-downloads.html").read_text(encoding="utf-8")
        self.assertIn(H50_SHA256, register)
        self.assertIn(H60_SHA256, register)
        self.assertNotIn(H49_TIF, home, "H49 must not be offered as a download")

    def test_homepage_offers_h50_plus_labelled_research_downloads(self):
        text = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        parser = _PageParser()
        parser.feed(text)
        offered = {urlparse(link).path.lstrip("./") for link in parser.tiff_links}
        self.assertEqual(offered, {H60_TIF, H50_TIF, H47QC_TIF})
        for path, sha in ((H60_TIF, H60_SHA256), (H50_TIF, H50_SHA256),
                          (H47QC_TIF, H47QC_SHA256)):
            target = ROOT / "docs" / path
            self.assertTrue(target.is_file(), f"offered TIFF does not exist: {target}")
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), sha)
        lower = text.lower()
        # the H50 artifact is NOT described as unscored/not promoted
        self.assertNotIn("unscored", lower)
        self.assertIn("not promoted", lower)          # about the older research artifacts
        self.assertIn("do not upload", lower)
        self.assertIn("0.165881", text)               # H50 blocked-holdout pooled DTI
        self.assertIn("0.287891", text)               # H60 blocked-holdout pooled DTI
        self.assertIn("0.1938", text)                 # H60 independent SGMC corroboration
        self.assertIn("0.049421", text)               # owner-reported d2.8 reference
        self.assertIn("H47-QC geothermometer screen", text)
        self.assertIn("It is not OK to submit this file", text)
        self.assertIn("strict local template-mask check passes", text)

    def test_h50_artifact_receipt_is_published_and_matches_the_bytes(self):
        receipt_path = ROOT / "docs" / "data" / "h50-artifact.json"
        self.assertTrue(receipt_path.is_file())
        receipt = json.loads(receipt_path.read_text())
        target = ROOT / "docs" / receipt["download_url"]
        self.assertTrue(target.is_file(), f"published TIFF missing: {target}")
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), receipt["sha256_tif"])
        self.assertEqual(receipt["sha256_tif"], H50_SHA256)
        self.assertTrue(receipt["promoted"])
        self.assertTrue(receipt["readback_checks"]["all_in_unit_interval"])
        self.assertTrue(receipt["readback_checks"]["nan_intolerant_range_check"])
        self.assertIsNone(receipt["format"]["nodata"])
        self.assertEqual(receipt["budget"], 37654)
        self.assertEqual(receipt["screen_selected_spacing_px"], 2.8)
        self.assertAlmostEqual(receipt["conformal"]["certified_floor_dti"], 0.0957, places=4)

    def test_h60_artifact_receipt_is_published_and_matches_the_bytes(self):
        receipt_path = ROOT / "docs" / "data" / "h60-artifact.json"
        self.assertTrue(receipt_path.is_file())
        receipt = json.loads(receipt_path.read_text())
        target = ROOT / "docs" / receipt["download_url"]
        self.assertTrue(target.is_file(), f"published TIFF missing: {target}")
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), receipt["sha256_tif"])
        self.assertEqual(receipt["sha256_tif"], H60_SHA256)
        self.assertTrue(receipt["promoted"])
        self.assertTrue(receipt["readback_checks"]["all_in_unit_interval"])
        self.assertTrue(receipt["readback_checks"]["nan_intolerant_range_check"])
        self.assertIsNone(receipt["format"]["nodata"])
        self.assertEqual(receipt["budget"], 37654)
        self.assertEqual(receipt["screen_selected_spacing_px"], 2.0)
        self.assertAlmostEqual(receipt["conformal"]["certified_floor_dti"], 0.0989, places=4)
        self.assertGreater(receipt["holdout"]["candidate_pooled_dti"],
                           receipt["holdout"]["h50_anchor_pooled_dti"])
        self.assertGreater(receipt["holdout"]["candidate_sgmc_pooled_dti"],
                           receipt["holdout"]["random_sgmc_pooled_dti"])
        # the landing page offers exactly this artifact as the primary download
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn(H60_SHA256, home)
        self.assertIn("h60 lidar-scarp d2p0 conformal90", home)
        h60_page = (ROOT / "docs" / "h60.html").read_text(encoding="utf-8")
        self.assertIn(H60_SHA256, h60_page)
        self.assertIn("preregistered", h60_page.lower())
        self.assertGreaterEqual(receipt["conformal"]["coverage_at_least"], 0.90)
        self.assertEqual(receipt["uniqueness"]["exact_matches"], 0)
        self.assertLess(receipt["uniqueness"]["max_jaccard"], 0.5)
        self.assertIn("h60 lidar-scarp d2p0 conformal90", receipt["submission_note_field"])
        self.assertIn("owner-derived", h60_page)   # provenance wording corrected

    def test_h50_artifact_receipt_note_field(self):
        receipt = json.loads((ROOT / "docs" / "data" / "h50-artifact.json").read_text())
        self.assertIn("h50 slope-anomaly d2p8 conformal90", receipt["submission_note_field"])

    def test_h50_evidence_page_links_only_inside_the_pages_artifact(self):
        page = (ROOT / "docs" / "h50.html").read_text(encoding="utf-8")
        self.assertIn("OK TO SUBMIT", page)
        self.assertIn("h50.html", page)
        self.assertNotIn("../", page)
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
        self.assertIn("It is not OK to submit this file", page)
        self.assertIn("h50.html", page)
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn(H50_TIF.split("/")[-1], home)
        self.assertNotIn(H50A_TIF.split("/")[-1], home,
                         "H50a must not be offered as a download on the home page")

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

        current = json.loads((ROOT / "docs" / "data" / "current-artifact.json").read_text())
        self.assertEqual(current["status"], "RESEARCH_ONLY_FORMAT_REQUIREMENT_FAIL")
        self.assertFalse(current["slot_authorized"])
        self.assertFalse(current["submission_eligible"])
        self.assertFalse(current["current_primary_artifact"])
        self.assertFalse(current["format_review"]["outside_null_or_nan"])
        self.assertIn("historical_builder_format_receipt", current)
        self.assertNotIn("portal_note", current)

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
            self.assertIn("no slot", text, name)
            self.assertIn(H49_BASE, text, name)
            self.assertIn("null-or-nan-outside", text, name)
            self.assertIn("owner-reported d2.8 reference", text, name)

    def test_root_landing_page_mirrors_the_docs_homepage(self):
        """Pages serves main:/ so the root index.html is what visitors land on.

        Regression test for IR-2026-10-08-A: the root page silently kept offering
        the research-only H47-C1 TIFF after the site moved to H60.
        """
        root = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(H60_TIF.split("/")[-1], root)
        self.assertIn("OK TO DOWNLOAD AND SUBMIT", root)
        self.assertIn("h60 lidar-scarp d2p0 conformal90", root)
        self.assertIn(H60_SHA256, root)
        self.assertNotIn("H47-C1 inference", root)
        self.assertNotIn("31 prior rasters", root)
        parser = _PageParser()
        parser.feed(root)
        for href in parser.links + parser.assets:
            url = urlparse(href)
            if url.scheme or url.netloc or not url.path:
                continue
            self.assertTrue(url.path.startswith("docs/"), href)
            target = (ROOT / unquote(url.path)).resolve()
            self.assertTrue(target.is_file(), f"root index: {href}")


if __name__ == "__main__":
    unittest.main()
