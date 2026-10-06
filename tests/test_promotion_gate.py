import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.package_submission import _promotion_gate


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PromotionGateTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.prediction = self.root / "prediction.tif"
        self.template = self.root / "template.tif"
        self.features = self.root / "features.tif"
        self.prediction.write_bytes(b"synthetic prediction bytes")
        self.template.write_bytes(b"synthetic template bytes")
        self.features.write_bytes(b"synthetic features bytes")
        self.report = {
            "schema_version": 2,
            "hypothesis_id": "H47-A",
            "status": "promoted",
            "official_inputs_authorized": True,
            "preregistered_before_scoring": True,
            "spatially_blocked": True,
            "guard_m": 300.0,
            "matched_mass": True,
            "controls_reported": True,
            "score_metric": "drivendata_distance_weighted_tversky",
            "report_id": "SYNTHETIC-UNIT-TEST-ONLY",
            "prediction_sha256": digest(self.prediction),
            "template_sha256": digest(self.template),
            "features_sha256": digest(self.features),
            "pooled_incumbent_dti": 0.196,
            "pooled_candidate_dti": 0.213,
            "evidence": {
                "domain_matched_random_control_reported": True,
                "ablations_reported": True,
                "metric_implementation": "local src/gems47_metric.py formula implementation; synthetic test only",
                "preregistration_sha256": "a" * 64,
                "fold_assignment_sha256": "b" * 64,
                "source_data_sha256": {"geodawn-area1": "c" * 64},
                "model_code_revision": "d" * 40,
            },
            "folds": [
                {"block_id": "north", "incumbent_dti": 0.20, "candidate_dti": 0.22, "incumbent_mass": 0.10, "candidate_mass": 0.10},
                {"block_id": "east", "incumbent_dti": 0.21, "candidate_dti": 0.23, "incumbent_mass": 0.10, "candidate_mass": 0.10},
                {"block_id": "south", "incumbent_dti": 0.18, "candidate_dti": 0.19, "incumbent_mass": 0.10, "candidate_mass": 0.10},
            ],
        }

    def tearDown(self):
        self.tempdir.cleanup()

    def _check(self, report=None):
        return _promotion_gate(
            report or self.report,
            self.prediction,
            self.template,
            self.features,
        )

    def test_allows_only_promoted_same_mass_multifold_gain(self):
        summary = self._check()
        self.assertEqual(summary["folds"], 3)
        self.assertEqual(summary["candidate_fold_wins"], 3)
        self.assertGreater(summary["candidate_mean_dti"], summary["incumbent_mean_dti"])

    def test_rejects_missing_local_metric_implementation(self):
        report = dict(self.report)
        report["evidence"] = dict(report["evidence"])
        report["evidence"].pop("metric_implementation")
        with self.assertRaisesRegex(ValueError, "pin the local DTI formula"):
            self._check(report)

    def test_rejects_unpromoted_report(self):
        report = dict(self.report, status="not_promoted")
        with self.assertRaisesRegex(ValueError, "status must be 'promoted'"):
            self._check(report)

    def test_rejects_missing_300_m_guard(self):
        report = dict(self.report, guard_m=299.0)
        with self.assertRaisesRegex(ValueError, "at least 300 m"):
            self._check(report)

    def test_rejects_wrong_candidate_hash(self):
        report = dict(self.report, prediction_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "prediction_sha256 does not match"):
            self._check(report)

    def test_rejects_candidate_that_does_not_beat_incumbent(self):
        report = dict(self.report)
        report["folds"] = [
            dict(fold, candidate_dti=fold["incumbent_dti"] - 0.01)
            for fold in self.report["folds"]
        ]
        with self.assertRaisesRegex(ValueError, "mean holdout score does not beat"):
            self._check(report)

    def test_rejects_fold_mean_gain_when_pooled_score_loses(self):
        report = dict(self.report, pooled_candidate_dti=0.195)
        with self.assertRaisesRegex(ValueError, "pooled holdout score does not beat"):
            self._check(report)


if __name__ == "__main__":
    unittest.main()
