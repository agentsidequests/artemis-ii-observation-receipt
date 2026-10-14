from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10z_action_plan_membership import verify_stage10z, verify_with_mutations  # noqa: E402


class Stage10ZActionPlanMembershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10z(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_MANY_TO_MANY_ACTION_PLAN_LEDGER", self.result["evidence_state"])

    def test_every_action_is_preserved(self) -> None:
        item = self.result["membership"]
        self.assertEqual(2166, item["complete_actions"])
        self.assertEqual(2228, item["ledger_rows_including_unmatched"])
        self.assertEqual(2166, sum(value["actions"] for value in self.result["membership_distribution"].values()))

    def test_membership_is_many_to_many_and_incomplete(self) -> None:
        item = self.result["membership"]
        self.assertEqual((626, 1482, 54, 4), (
            item["actions_with_no_plan_membership"], item["actions_with_one_plan_membership"],
            item["actions_with_two_plan_memberships"], item["actions_with_three_plan_memberships"],
        ))
        self.assertEqual(1602, item["action_plan_relationships"])

    def test_drop_and_double_count_costs_are_visible(self) -> None:
        item = self.result["membership"]
        self.assertAlmostEqual(0.2531602369945133, item["unassigned_byte_share"])
        self.assertAlmostEqual(0.05432336257170055, item["window_byte_inflation"])

    def test_compact_relationship_layer_and_ledger_identity_are_frozen(self) -> None:
        item = self.result["membership"]
        self.assertEqual(10470310, item["combined_relationship_layer_bytes"])
        self.assertAlmostEqual(155227.62605338334, item["cohort_to_relationship_layer_byte_ratio"])
        self.assertEqual(398284, self.result["ledger_bytes"])
        self.assertEqual(
            "819e1da2f132488b99d403cdc9b9335fe5e55228fec4fd6277629ddbaf21ab38",
            self.result["ledger_sha256"],
        )

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
