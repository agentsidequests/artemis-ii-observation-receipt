from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11i_weight_factorization import verify_stage11i, verify_with_mutations  # noqa: E402


class Stage11IWeightFactorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11i(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_IMPLICIT_WEIGHT_FACTORIZATION", self.result["evidence_state"])

    def test_factorization_closes_exactly(self) -> None:
        item = self.result["metrics"]
        self.assertEqual((2166, 7606, 22818, 3), (
            item["complete_actions"], item["capture_identities"],
            item["archive_products"], item["representations_per_capture"],
        ))
        self.assertEqual(22818, item["capture_identities"] * item["representations_per_capture"])
        self.assertEqual(22818, item["three_exposure_actions"] * 9 + item["five_exposure_actions"] * 15)

    def test_representation_multiplier_preserves_relative_protocol_weight(self) -> None:
        item = self.result["metrics"]
        self.assertAlmostEqual(5 / 3, item["source_row_weight_ratio_five_vs_three"])
        self.assertAlmostEqual(5 / 3, item["product_weight_ratio_five_vs_three"])
        self.assertFalse(item["representation_multiplier_changes_relative_protocol_ratio"])

    def test_five_exposure_share_amplification_is_exact(self) -> None:
        item = self.result["metrics"]
        self.assertAlmostEqual(0.25577100646352724, item["five_exposure_action_share"])
        self.assertAlmostEqual(0.36418616881409416, item["five_exposure_capture_and_product_share"])
        self.assertAlmostEqual(1.4238758874572706, item["five_exposure_share_amplification"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
