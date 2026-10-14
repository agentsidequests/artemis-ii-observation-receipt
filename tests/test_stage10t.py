from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10t_task_conditioned_unit_ladder import verify_with_mutations  # noqa: E402


class Stage10TTaskConditionedUnitLadderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_with_mutations(ROOT)

    def test_baseline_and_hard_negatives_pass(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertTrue(self.result["hard_negatives_pass"])

    def test_unit_ladder_is_exact(self) -> None:
        item = self.result["unit_ladder"]
        self.assertEqual(
            (2535, 845, 169, 24, 1),
            (
                item["archive_products"], item["exposure_identities"],
                item["complete_actions"], item["conditional_five_second_clusters"],
                item["scheduled_sunset_events"],
            ),
        )

    def test_two_sided_new_event_split_is_infeasible(self) -> None:
        item = self.result["unit_ladder"]
        self.assertEqual(2, item["possible_binary_event_allocations"])
        self.assertEqual(0, item["valid_two_sided_event_allocations"])
        self.assertIn("two-sided internal Artemis II event split is infeasible", self.result["decision_use"])

    def test_result_preserves_narrower_task_routes(self) -> None:
        self.assertIn("Within-event temporal, HDR, representation, and retrieval tasks remain possible", self.result["decision_use"])
        self.assertIn("not five interchangeable", self.result["verified"])


if __name__ == "__main__":
    unittest.main()
