from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10y_schedule_tag_non_equivalence import verify_stage10y, verify_with_mutations  # noqa: E402


class Stage10YScheduleTagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10y(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_SCHEDULE_TAG_NON_EQUIVALENCE", self.result["evidence_state"])

    def test_vocabularies_are_not_identical(self) -> None:
        item = self.result["correspondence"]
        self.assertEqual((19, 23, 14), (
            item["scheduled_target_names"], item["tag_values"], item["shared_exact_names"]
        ))
        self.assertEqual((9, 5), (item["tag_only_names"], item["plan_only_names"]))

    def test_most_tagged_exposures_are_outside_same_name_windows(self) -> None:
        item = self.result["correspondence"]
        self.assertEqual((1313, 2100), (
            item["exposures_inside_any_same_name_plan_window"],
            item["exposures_outside_all_same_name_plan_windows"],
        ))
        self.assertAlmostEqual(0.6152944623498389, item["outside_same_name_window_share"])

    def test_sunset_outside_rows_are_not_promoted_to_events(self) -> None:
        item = self.result["correspondence"]
        self.assertEqual((1553, 845, 708), (
            item["sunset_tagged_exposures"], item["sunset_inside_same_name_plan_window"],
            item["sunset_outside_same_name_plan_window"],
        ))

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
