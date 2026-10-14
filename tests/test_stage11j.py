from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11j_rank_reversal_attribution import verify_stage11j, verify_with_mutations  # noqa: E402


class Stage11JRankReversalAttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11j(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_PROTOCOL_ATTRIBUTION_OF_PRODUCT_RANK_REVERSALS", self.result["evidence_state"])

    def test_all_reversals_cross_unequal_rates(self) -> None:
        item = self.result["metrics"]
        self.assertEqual((222, 0), (item["equal_product_rate_comparable_pairs"], item["equal_product_rate_reversals"]))
        self.assertEqual((399, 38), (item["unequal_product_rate_comparable_pairs"], item["unequal_product_rate_reversals"]))
        self.assertTrue(item["all_reversals_cross_unequal_product_rates"])

    def test_reversal_direction_and_factorization_are_exact(self) -> None:
        item = self.result["metrics"]
        self.assertTrue(item["all_higher_action_windows_have_lower_product_rate"])
        self.assertTrue(item["all_window_product_rates_equal_three_times_exposure_rates"])
        self.assertEqual(3, item["constant_representations_per_capture"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
