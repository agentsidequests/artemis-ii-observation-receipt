from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11k_byte_rank_factorization import verify_stage11k, verify_with_mutations  # noqa: E402


class Stage11KByteRankFactorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11k(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_BYTE_WEIGHT_AS_DISTINCT_ARCHIVE_LAYER", self.result["evidence_state"])

    def test_product_and_byte_reversals_cross_classify(self) -> None:
        item = self.result["metrics"]
        self.assertEqual((35, 3, 24, 559), (
            item["product_and_byte_reversals"], item["product_only_reversals"],
            item["byte_only_reversals"], item["neither_reverses"],
        ))
        self.assertEqual(38, item["total_product_reversals"])
        self.assertEqual(59, item["total_byte_reversals"])

    def test_byte_rate_factorization_is_exact(self) -> None:
        self.assertTrue(self.result["metrics"]["all_window_byte_rates_factor_exactly"])
        self.assertAlmostEqual(35 / 59, self.result["metrics"]["byte_reversal_overlap_with_product_reversal_share"])
        self.assertAlmostEqual(24 / 59, self.result["metrics"]["byte_only_share_of_byte_reversals"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
