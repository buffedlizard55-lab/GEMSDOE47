import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.title_text = ""
        self.in_title = False
        self.language = None
        self.descriptions = 0
        self.disabled_tiff_button = False
        self.tiff_links = []
        self.button_disabled = False

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
        if tag == "button":
            self.button_disabled = "disabled" in attrs

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data.strip()
        if self.button_disabled and "TIFF download not available" in data:
            self.disabled_tiff_button = True


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
                    if parsed.path.lower().endswith(".md"):
                        self.assertEqual(parsed.netloc.lower(), "github.com")
                        self.assertIn("/blob/main/", parsed.path)
                    continue
                if not parsed.path:
                    continue
                target = (page.parent / unquote(parsed.path)).resolve()
                self.assertTrue(target.is_file(), f"{page.relative_to(ROOT)} has broken link {href}")
                if parsed.fragment:
                    target_page = _PageParser()
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

    def test_homepage_offers_the_audited_artifact_with_its_caveat(self):
        """The homepage gate was fail-closed while no artifact existed. One now does, and it is
        byte-audited, so the gate must offer it — with the caveat that the blocked-holdout
        requirement is NOT met, and the sha256 that makes the file auditable."""
        text = (ROOT / "index.html").read_text(encoding="utf-8")
        parser = _PageParser()
        parser.feed(text)
        self.assertFalse(parser.disabled_tiff_button, "the disabled placeholder button is gone")
        self.assertEqual(len(parser.tiff_links), 1, "exactly one TIFF download is offered")
        target = (ROOT / urlparse(parser.tiff_links[0]).path.lstrip("./")).resolve()
        self.assertTrue(target.is_file(), f"offered TIFF does not exist: {target}")
        self.assertGreater(target.stat().st_size, 1_000_000)
        lower = text.lower()
        self.assertIn("blocked-holdout", lower, "the unmet holdout requirement must remain visible")
        self.assertIn("not met", lower)
        self.assertIn("0d8ba64c", text, "the sha256 of the offered artifact must be on the page")
        self.assertIn("been uploaded", lower)
        self.assertIn("drivendata", lower)


if __name__ == "__main__":
    unittest.main()
