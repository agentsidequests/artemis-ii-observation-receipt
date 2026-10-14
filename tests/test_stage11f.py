from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11f_protocol_weighting import verify_stage11f, verify_with_mutations  # noqa: E402


class Stage11FProtocolWeightingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11f(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_PLAN_WINDOW_PROTOCOL_WEIGHTING", self.result["evidence_state"])

    def test_protocol_regimes_cover_all_active_windows(self) -> None:
        item = self.result["metrics"]
        self.assertEqual((36, 19, 11, 6), (
            item["active_plan_windows"], item["pure_three_exposure_windows"],
            item["pure_five_exposure_windows"], item["mixed_exposure_windows"],
        ))

    def test_product_weight_range_follows_bracket_length(self) -> None:
        item = self.result["metrics"]
        self.assertEqual((9.0, 15.0), (item["minimum_products_per_action"], item["maximum_products_per_action"]))
        self.assertAlmostEqual(1.6666666666666667, item["pure_five_vs_pure_three_product_weight"])
        self.assertEqual(4, item["sunset_byte_weight_rank_descending"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
