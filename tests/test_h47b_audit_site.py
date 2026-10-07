import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = "gems47-h47b-single-scale-tmi-up150-400m-d5-n18524-research-only-not-for-submission-20261006-nanoutside.tif"
ARTIFACT_SHA256 = "dc71c807fbca2cd398f394bcd91b10ecec6b46fe89c2d61f5b1c058fef672811"


class H47BAuditSiteTests(unittest.TestCase):
    def test_h47b_artifact_is_secondary_and_exact_bytes_are_registered(self):
        data_path = ROOT / "docs" / "downloads" / ARTIFACT
        self.assertTrue(data_path.is_file())
        self.assertEqual(hashlib.sha256(data_path.read_bytes()).hexdigest(), ARTIFACT_SHA256)

        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        summary = (ROOT / "docs" / "executive-summary.html").read_text(encoding="utf-8")
        audit = (ROOT / "docs" / "h47b-mask-audit-20261006.html").read_text(encoding="utf-8")
        downloads = (ROOT / "docs" / "all-downloads.html").read_text(encoding="utf-8")
        # H47-B remains archived as a secondary research artifact in the register and its
        # dedicated audit. Current landing pages now represent H50 accurately: locally
        # promoted, but not organizer-accepted or slot-authorized.
        for current_page in (home, summary):
            self.assertIn("h50.html", current_page)
            self.assertIn("locally promoted", current_page.lower())
            self.assertIn("not organizer-accepted", current_page.lower())
            self.assertNotIn("OK TO DOWNLOAD AND SUBMIT", current_page)
        self.assertIn("h47b-mask-audit-20261006.html", downloads)
        self.assertIn(ARTIFACT, audit)
        self.assertIn(ARTIFACT_SHA256, audit)
        self.assertIn(ARTIFACT, downloads)
        self.assertIn(ARTIFACT_SHA256, downloads)
        self.assertIn("NOT PROMOTED", audit)
        self.assertIn("portal error's cause remains unknown", audit)
        self.assertIn("0.02563947", audit)
        self.assertIn("0.03715911", audit)

    def test_footprint_issue_is_synchronized_in_both_machine_registries(self):
        registry = json.loads((ROOT / "registry" / "irregularities.json").read_text())
        deployed = json.loads((ROOT / "docs" / "data" / "irregularities.json").read_text())
        self.assertEqual(registry, deployed)
        record = next(row for row in registry["irregularities"] if row["id"] == "IR-47-021")
        self.assertIn("5,167,373", record["why_it_matters"])
        self.assertIn("5,165,852", record["why_it_matters"])
        self.assertEqual(record["human_page"], "docs/irregularities.html#ir-47-021")
        irregularities_page = (ROOT / "docs" / "irregularities.html").read_text(encoding="utf-8")
        self.assertIn('id="ir-47-021"', irregularities_page)
        self.assertIn("h47b-mask-audit-20261006.html", irregularities_page)


if __name__ == "__main__":
    unittest.main()
