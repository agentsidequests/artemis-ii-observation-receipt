from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11e_unit_choice_reweighting import verify_stage11e, verify_with_mutations  # noqa: E402


class Stage11EUnitChoiceReweightingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11e(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_UNIT_CHOICE_REWEIGHTING_CANARY", self.result["evidence_state"])

    def test_context_share_rises_with_flattened_units(self) -> None:
        item = self.result["measures"]
        self.assertAlmostEqual(0.13204062788550322, item["action_share"])
        self.assertAlmostEqual(0.18800946621088616, item["product_share"])
        self.assertAlmostEqual(0.2278532111354432, item["total_byte_share"])
        self.assertGreater(item["total_byte_share"], item["product_share"])
        self.assertGreater(item["product_share"], item["action_share"])

    def test_relative_weights_are_frozen(self) -> None:
        self.assertAlmostEqual(1.4238758874572708, self.result["measures"]["product_weight_vs_action_weight"])
        self.assertAlmostEqual(1.7256295640537413, self.result["measures"]["byte_weight_vs_action_weight"])
        self.assertEqual("ADMIT_UNIT_CHOICE_REWEIGHTING_CANARY", self.result["disposition"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
