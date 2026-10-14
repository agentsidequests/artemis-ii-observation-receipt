from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage6b_specialist_pressure_test import verify_stage6b, verify_with_mutations  # noqa: E402


class Stage6BSpecialistPressureTestTests(unittest.TestCase):
    def test_pressure_test_retires_quantified_headline(self) -> None:
        result = verify_stage6b(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_SPECIALIST_PRESSURE_CORRECTION", result["evidence_state"])
        self.assertEqual(
            "STOP_QUANTIFIED_HEADLINE_CONTINUE_BOUNDED_TEST",
            result["disposition"],
        )
        self.assertEqual(
            "orientale_aggregate_texture_10_60x_below_object_resolution",
            result["retired_claim"],
        )
        self.assertEqual(0, result["network_bytes_in_verification"])

    def test_arithmetic_survives_but_explanation_does_not(self) -> None:
        adjudication = verify_stage6b(ROOT)["adjudication"]
        self.assertEqual("CORRECT", adjudication["stage6a_ratio_arithmetic"])
        self.assertEqual(
            "REJECTED_UNLIKE_QUANTITIES",
            adjudication["stage6a_ratio_commensurability"],
        )
        self.assertEqual("NON_DIAGNOSTIC", adjudication["stage6a_ratio_explanatory_status"])
        self.assertEqual("STOP_10_60X_HEADLINE", adjudication["public_lead_status"])

    def test_map_and_perception_quantities_remain_distinct(self) -> None:
        distinctions = verify_stage6b(ROOT)["distinctions"]
        self.assertEqual(
            {
                "roughness_measurement_baseline",
                "roughness_map_support",
                "visible_pattern_extent",
                "recognized_object_size",
                "claim",
            },
            set(distinctions),
        )
        self.assertIn("not interchangeable", distinctions["claim"])

    def test_replacement_is_blind_held_out_and_controlled(self) -> None:
        candidate = verify_stage6b(ROOT)["replacement_candidate"]
        self.assertEqual("held_out_semantic_cross_instrument_concordance", candidate["id"])
        self.assertEqual("BOUNDED_TEST_CANDIDATE", candidate["state"])
        self.assertIn("Blind-code", candidate["treatment"])
        self.assertIn("reserve Orientale as prior evidence", candidate["treatment"])
        self.assertIn("viewing geometry", candidate["oracle"])
        self.assertIn("NOVELTY_UNESTABLISHED", candidate["novelty_ceiling"])

    def test_every_stage6b_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
