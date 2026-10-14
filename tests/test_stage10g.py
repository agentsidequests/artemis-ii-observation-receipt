from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10g_retrieval_distortion import verify_stage10g, verify_with_mutations  # noqa: E402


class Stage10GRetrievalDistortionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10g(ROOT)

    def test_retrieval_distortion_amplification_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual(
            "VERIFIED_RETRIEVAL_DISTORTION_AMPLIFICATION",
            self.result["evidence_state"],
        )

    def test_action_exposure_product_units_are_distinct(self) -> None:
        self.assertEqual(21, self.result["fractured_actions"])
        self.assertEqual(69, self.result["exposure_ids"])
        self.assertEqual(207, self.result["product_records"])

    def test_every_exposure_has_three_representations(self) -> None:
        self.assertEqual(
            {"data_source": 69, "data_raw": 69, "data_processed": 69},
            self.result["collection_counts"],
        )
        self.assertEqual(15833953276, self.result["total_bytes"])

    def test_activity_target_partitions_are_coupled_in_twenty_actions(self) -> None:
        self.assertEqual(20, self.result["activity_target_partition_coupled_actions"])

    def test_discussion_facet_overcounts_products_and_under_recovers_actions(self) -> None:
        self.assertEqual(14, self.result["discussion_crew_choice_actions"])
        self.assertEqual(28, self.result["discussion_exposure_ids"])
        self.assertEqual(84, self.result["discussion_product_records"])
        self.assertEqual(0, self.result["discussion_complete_actions_recoverable"])
        self.assertEqual(14, self.result["discussion_companion_exposure_ids_needed"])
        self.assertEqual(42, self.result["discussion_companion_product_records_needed"])

    def test_decision_use_names_three_explicit_keys(self) -> None:
        decision = self.result["decision_use"].lower()
        for phrase in ("collection identity", "nasa internal id", "camera-native grouping"):
            self.assertIn(phrase, decision)

    def test_claim_ceiling_preserves_independence_and_scope_limits(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in (
            "independent observations",
            "useful representations waste",
            "correct activities or targets",
            "non-bracket products",
            "every archive product class",
        ):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
