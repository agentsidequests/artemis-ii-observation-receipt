from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10u_camera_target_shortcut import verify_with_mutations  # noqa: E402


class Stage10UCameraTargetShortcutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_with_mutations(ROOT)

    def test_baseline_and_hard_negatives_pass(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertTrue(self.result["hard_negatives_pass"])

    def test_camera_target_contingency_is_exact(self) -> None:
        item = self.result["association"]
        self.assertEqual((3413, 23, 3), (item["labeled_exposures"], item["target_classes"], item["camera_serials"]))
        self.assertEqual((19, 807), (item["camera_exclusive_target_classes"], item["camera_exclusive_labeled_exposures"]))
        self.assertAlmostEqual(0.23644887196015235, item["camera_exclusive_exposure_share"])

    def test_document_nominated_z9_rule_has_signal(self) -> None:
        item = self.result["association"]
        self.assertEqual((593, 734), (item["z9_sunset_exposures"], item["z9_labeled_exposures"]))
        self.assertAlmostEqual(0.6774099033108703, item["rule_accuracy"])
        self.assertAlmostEqual(0.544975095224143, item["majority_accuracy"])
        self.assertGreater(item["rule_accuracy_lift"], 0.13)

    def test_camera_is_not_necessary_or_sufficient(self) -> None:
        item = self.result["association"]
        self.assertEqual((593, 1719, 141, 960), (
            item["rule_true_positive"], item["rule_true_negative"],
            item["rule_false_positive"], item["rule_false_negative"],
        ))
        self.assertLess(item["rule_sensitivity"], 0.4)
        self.assertIn("does not prove that pixels reveal camera identity", self.result["decision_use"])


if __name__ == "__main__":
    unittest.main()
