import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_TIF = "downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif"
ARTIFACT_SHA256 = "f2cec409ce3bec5a2805f1fab9a12ab7f72394f8be79cc365134ce43708c6060"
PRIOR_TIF = "downloads/gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif"
PRIOR_SHA256 = "e6eea1956b8f76ffef2f4867a6e2ac0bef078c0c61c3711e44eb07e93cb089d0"
H47QC_TIF = "downloads/gems47-h47qc-geothermometer-consensus-n5000-research-only-20261006.tif"
H47QC_SHA256 = "3866b60cf91b4f6bff2ef694153550aa97a744a3091a57ef9f83da41e16b91b2"


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.title_text = ""
        self.in_title = False
        self.language = None
        self.descriptions = 0
        self.tiff_links = []
        self.assets = []

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
    def test_all_deployed_nested_links_assets_stay_inside_pages_artifact(self):
        for page in sorted((ROOT / "docs").rglob("*.html")):
            parser = _PageParser(); parser.feed(page.read_text())
            for href in parser.links + parser.assets:
                url = urlparse(href)
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (page.parent / unquote(url.path)).resolve()
                self.assertTrue(target.is_relative_to((ROOT / "docs").resolve()), href)
                self.assertTrue(target.is_file(), f"{page}: {href}")

    def test_new_download_precedes_the_large_intro_on_home_and_summary(self):
        for name in ["index.html", "executive-summary.html"]:
            text = (ROOT / "docs" / name).read_text()
            self.assertLess(text.index("↓ Download GeoTIFF"), text.index("<h1>"), name)
            self.assertIn("2.8 px / 280 m", text)
            self.assertIn("split-conformal 90% floor 0.0318", text)

    def test_all_local_html_links_resolve(self):
        pages = sorted([ROOT / "index.html", *ROOT.glob("docs/*.html")])
        self.assertGreaterEqual(len(pages), 4)
        for page in pages:
            parser = _PageParser()
            parser.feed(page.read_text(encoding="utf-8"))
            for href in parser.links:
                parsed = urlparse(href)
                if parsed.scheme or parsed.netloc:
                    continue
                if not parsed.path:
                    continue
                target = (page.parent / unquote(parsed.path)).resolve()
                self.assertTrue(target.is_file(), f"{page.relative_to(ROOT)} has broken link {href}")
                if parsed.fragment:
                    target_page = _PageParser()
                    if target.suffix.lower() == ".html":
                        target_page.feed(target.read_text(encoding="utf-8", errors="replace"))
                        self.assertIn(parsed.fragment, target_page.ids, f"broken fragment {href} in {page}")

    def test_pages_have_accessible_metadata(self):
        pages = sorted([ROOT / "index.html", *ROOT.glob("docs/*.html")])
        for page in pages:
            parser = _PageParser()
            parser.feed(page.read_text(encoding="utf-8"))
            self.assertEqual(parser.language, "en", page.name)
            self.assertTrue(parser.title_text, page.name)
            self.assertEqual(parser.descriptions, 1, page.name)

    def test_homepage_offers_the_research_only_artifact_and_labels_prior_screens(self):
        text = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        parser = _PageParser()
        parser.feed(text)
        offered = {urlparse(link).path.lstrip("./") for link in parser.tiff_links}
        self.assertEqual(offered, {ARTIFACT_TIF, PRIOR_TIF, H47QC_TIF})
        target = ROOT / "docs" / ARTIFACT_TIF
        self.assertTrue(target.is_file(), f"offered TIFF does not exist: {target}")
        self.assertGreater(target.stat().st_size, 100_000)
        import hashlib
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), ARTIFACT_SHA256)
        # the current research artifact is offered before either historical screen
        self.assertLess(text.index(ARTIFACT_TIF), text.index(PRIOR_TIF))
        self.assertLess(text.index(ARTIFACT_TIF), text.index(H47QC_TIF))
        for path, sha in ((ROOT / "docs" / PRIOR_TIF, PRIOR_SHA256),
                          (ROOT / "docs" / H47QC_TIF, H47QC_SHA256)):
            self.assertTrue(path.is_file(), f"offered TIFF does not exist: {path}")
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)
        lower = text.lower()
        self.assertIn("unscored", lower)
        self.assertIn("not promoted", lower)
        self.assertIn("do not upload", lower)
        self.assertIn("no slot spent", lower)
        self.assertIn(ARTIFACT_SHA256, text)
        self.assertIn("data/pinned-public-inventory-uniqueness.json", text)
        self.assertIn("not globally unique", lower)
        self.assertIn("0.10329", text, "descriptive selection-half proxy mean is visible")
        self.assertIn("0.03184", text, "nominal fixed-arm floor is visible")
        self.assertIn("promotion gate closed", lower)
        self.assertIn("negative", lower, "the paired-improvement limitation is visible")
        self.assertIn("90%", text, "the conformal confidence level is visible")
        # the superseded screens keep their own, correctly-labelled numbers
        self.assertIn("0.177872", text, "prior screen pooled score is visible")
        self.assertIn("0.180216", text, "prior screen baseline loss is visible")
        self.assertIn("H47-QC geothermometer screen", text)
        self.assertIn("0.0131689425", text)
        self.assertIn("0.0141948068", text)

    def test_submission_and_summary_pages_keep_the_evidence_and_slot_warning_visible(self):
        for path in (ROOT / "docs" / "executive-summary.html", ROOT / "docs" / "submit.html",
                     ROOT / "docs" / "portal-checklist.html"):
            text = path.read_text(encoding="utf-8").lower()
            self.assertIn("split-conformal", text, path.name)
            self.assertIn("90%", text, path.name)
            self.assertIn("unscored", text, path.name)
            self.assertIn("three-scoring-submissions-per-week", text, path.name)
            self.assertIn("no score claimed", text, path.name)
            self.assertIn(ARTIFACT_TIF.split("/")[-1], text, path.name)


if __name__ == "__main__":
    unittest.main()
