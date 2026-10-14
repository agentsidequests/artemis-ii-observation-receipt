from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11g_unit_sensitive_prominence import verify_stage11g, verify_with_mutations  # noqa: E402


class Stage11GUnitSensitiveProminenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11g(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_UNIT_SENSITIVE_WINDOW_PROMINENCE", self.result["evidence_state"])

    def test_pairwise_reversal_counts_are_exact(self) -> None:
        item = self.result["metrics"]
        self.assertEqual((630, 621, 38, 583, 9), (
            item["unordered_window_pairs"], item["action_product_strictly_comparable_pairs"],
            item["action_product_reversed_pairs"], item["action_product_concordant_pairs"],
            item["action_product_tied_pairs"],
        ))
        self.assertEqual((621, 59, 562, 9), (
            item["action_byte_strictly_comparable_pairs"], item["action_byte_reversed_pairs"],
            item["action_byte_concordant_pairs"], item["action_byte_tied_pairs"],
        ))

    def test_examples_are_true_reversals(self) -> None:
        for example in self.result["product_reversal_examples"]:
            self.assertGreater(example["more_actions_actions"], example["more_products_actions"])
            self.assertLess(example["more_actions_products"], example["more_products_products"])

    def test_sunset_remains_first_under_all_three_totals(self) -> None:
        item = self.result["metrics"]
        self.assertEqual((1, 1, 1), (
            item["sunset_action_rank_descending"], item["sunset_product_rank_descending"],
            item["sunset_byte_rank_descending"],
        ))

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
