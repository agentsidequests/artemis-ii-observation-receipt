from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11a_planned_target_replication import verify_stage11a, verify_with_mutations  # noqa: E402


class Stage11APlannedTargetReplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11a(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_PLANNED_TARGET_WINDOW_REPLICATION_CENSUS", self.result["evidence_state"])

    def test_singleton_constraint_is_broader_than_sunset(self) -> None:
        item = self.result["replication"]
        self.assertEqual((36, 19, 12, 7), (
            item["active_plan_windows"], item["active_plan_target_names"],
            item["singleton_target_names"], item["repeated_target_names"],
        ))
        self.assertIn("Sunset", self.result["singleton_names"])
        self.assertIn("Earthrise", self.result["singleton_names"])

    def test_repeated_names_are_not_promoted_to_independent_events(self) -> None:
        self.assertEqual(2, self.result["repeated_names"]["Orientale Basin"])
        self.assertEqual(5, self.result["repeated_names"]["Guided Discussion"])
        self.assertIn("remain candidates only", self.result["decision_use"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
