import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_TIF = (
    "docs/downloads/gems47-h47b-single-scale-tmi-up150-400m-d5-"
    "n18524-research-only-not-for-submission-20261006-nanoutside.tif"
)
EXPECTED_SHA256 = "dc71c807fbca2cd398f394bcd91b10ecec6b46fe89c2d61f5b1c058fef672811"
EXPECTED_RESEARCH_NOTE = (
    "single-scale edge; d=5 px/500 m; catalogue-mask proxy conformal 6/7=85.7% nominal, "
    "lower floor 0.000 (exchangeability unverified); RESEARCH ONLY"
)


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

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang")
        if "id" in attrs:
            self.ids.add(attrs["id"])
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

    def test_irregularity_registry_human_pages_and_anchors_resolve(self):
        registry = json.loads((ROOT / "registry" / "irregularities.json").read_text(encoding="utf-8"))
        for record in registry["irregularities"]:
            parsed = urlparse(record["human_page"])
            target = (ROOT / unquote(parsed.path)).resolve()
            self.assertTrue(target.is_file(), record["id"])
            if parsed.fragment and target.suffix.lower() == ".html":
                parser = _PageParser()
                parser.feed(target.read_text(encoding="utf-8"))
                self.assertIn(parsed.fragment, parser.ids, record["id"])

    def test_pages_have_accessible_metadata(self):
        pages = sorted([ROOT / "index.html", *ROOT.glob("docs/*.html")])
        for page in pages:
            parser = _PageParser()
            parser.feed(page.read_text(encoding="utf-8"))
            self.assertEqual(parser.language, "en", page.name)
            self.assertTrue(parser.title_text, page.name)
            self.assertEqual(parser.descriptions, 1, page.name)

    def test_homepage_prominently_offers_only_the_research_artifact(self):
        text = (ROOT / "index.html").read_text(encoding="utf-8")
        parser = _PageParser()
        parser.feed(text)
        self.assertEqual(len(parser.tiff_links), 1, "exactly one TIFF download is offered")
        href = urlparse(parser.tiff_links[0]).path.lstrip("./")
        self.assertEqual(href, RESEARCH_TIF)
        target = ROOT / RESEARCH_TIF
        self.assertTrue(target.is_file(), f"offered TIFF does not exist: {target}")
        self.assertEqual(target.stat().st_size, 309_530)
        lower = text.lower()
        self.assertIn("research-only", lower)
        self.assertIn("not for submission", lower)
        self.assertIn("not promoted", lower)
        self.assertIn("no slot", lower)
        self.assertIn(EXPECTED_SHA256, text)
        self.assertIn(EXPECTED_RESEARCH_NOTE, text)
        self.assertIn("0.037159", text, "random-control loss is visible")

    def test_executive_summary_links_the_same_primary_artifact_and_discloses_mask_scope(self):
        path = ROOT / "docs" / "executive-summary.html"
        text = path.read_text(encoding="utf-8")
        parser = _PageParser()
        parser.feed(text)
        self.assertIn(
            "downloads/" + Path(RESEARCH_TIF).name,
            [urlparse(href).path for href in parser.tiff_links],
        )
        self.assertIn(EXPECTED_SHA256, text)
        self.assertIn(EXPECTED_RESEARCH_NOTE, text)
        self.assertIn("explicit mask derived from finite cells", text)
        self.assertIn("official evaluation", text.lower())
        self.assertIn("floor 0.000", text)

    def test_submission_and_summary_pages_keep_the_slot_gate_visible(self):
        for path in (ROOT / "docs" / "executive-summary.html", ROOT / "docs" / "submit.html", ROOT / "docs" / "portal-checklist.html"):
            text = path.read_text(encoding="utf-8").lower()
            self.assertTrue("do not upload" in text or "not for submission" in text, path.name)
            self.assertTrue("holdout" in text or "promotion gate" in text, path.name)


if __name__ == "__main__":
    unittest.main()
