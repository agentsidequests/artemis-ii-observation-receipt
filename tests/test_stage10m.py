from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10m_ai_split_hazard import verify_stage10m, verify_with_mutations  # noqa: E402


class Stage10MAISplitHazardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10m(ROOT)

    def test_model_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_EXPECTED_RANDOM_SPLIT_GROUP_CROSSING_HAZARD", self.result["evidence_state"])

    def test_action_size_distribution(self) -> None:
        self.assertEqual((1612, 554, 2166), (self.result["three_exposure_actions"], self.result["five_exposure_actions"], self.result["complete_actions"]))

    def test_eighty_twenty_hazard(self) -> None:
        scenario = self.result["scenarios"]["0.8"]
        self.assertAlmostEqual(1930.1480549646335, scenario["expected_cross_action_groups_product_split"])
        self.assertAlmostEqual(0.8911117520612343, scenario["product_split_action_cross_rate"])
        self.assertAlmostEqual(1146.0479999999998, scenario["expected_cross_action_groups_exposure_split"])
        self.assertAlmostEqual(0.5291080332409971, scenario["exposure_split_action_cross_rate"])
        self.assertEqual(0.0, scenario["action_group_split_cross_rate"])

    def test_ordering_holds_across_scenarios(self) -> None:
        for scenario in self.result["scenarios"].values():
            self.assertGreater(scenario["product_split_action_cross_rate"], scenario["exposure_split_action_cross_rate"])
            self.assertGreater(scenario["exposure_split_action_cross_rate"], scenario["action_group_split_cross_rate"])

    def test_claim_ceiling_preserves_hypothetical_scope(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("expected related-group crossing", "observed leakage", "any actual pipeline", "performance impact", "global novelty or priority"):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
