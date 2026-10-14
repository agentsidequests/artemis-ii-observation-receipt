from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10s_planned_sunset_window import verify_stage10s, verify_with_mutations  # noqa: E402


class Stage10SPlanBoundedSunsetWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_with_mutations(ROOT)

    def test_baseline_and_hard_negatives_pass(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertTrue(self.result["hard_negatives_pass"])

    def test_plan_bounded_window_is_exact(self) -> None:
        item = self.result["window"]
        self.assertEqual("2026-04-07T00:36:00Z", item["planned_start_utc"])
        self.assertEqual("2026-04-07T00:44:00Z", item["planned_end_utc"])
        self.assertEqual(2535, item["products"])
        self.assertEqual(845, item["capture_identities"])
        self.assertEqual(169, item["complete_actions"])
        self.assertEqual(200901668231, item["archive_size_bytes"])

    def test_representation_ledger_is_not_collapsed(self) -> None:
        item = self.result["window"]
        self.assertEqual(17257373901, item["source_bytes"])
        self.assertEqual(46133066720, item["raw_bytes"])
        self.assertEqual(137511227610, item["processed_bytes"])
        self.assertEqual(item["archive_size_bytes"], item["source_bytes"] + item["raw_bytes"] + item["processed_bytes"])
        self.assertAlmostEqual(11.641497100515306, item["archive_to_source_byte_ratio"])
        self.assertAlmostEqual(0.6844703123713605, item["processed_byte_share"])

    def test_sunset_leads_comparable_plan_windows(self) -> None:
        item = self.result["window"]
        self.assertEqual(36, item["plan_windows_with_actions"])
        self.assertEqual((1, 1, 1), (item["product_rank"], item["action_rank"], item["byte_rank"]))
        self.assertGreater(item["product_lead_ratio"], 1.36)
        self.assertGreater(item["action_lead_ratio"], 1.12)
        self.assertGreater(item["byte_lead_ratio"], 1.13)
        self.assertEqual(12, item["target_matched_plan_windows"])
        self.assertGreater(item["target_matched_byte_lead_ratio"], 4.8)

    def test_fixed_time_window_does_not_depend_on_target_filter(self) -> None:
        item = self.result["window"]
        self.assertEqual(["Sunset"], item["target_ids"])
        self.assertEqual(1.0, item["target_label_concordance"])

    def test_event_level_replication_limit_is_explicit(self) -> None:
        item = self.result["window"]
        self.assertEqual(1, item["scheduled_sunset_entries"])
        self.assertEqual(1.0, item["event_cross_probability_80_20"])
        self.assertIn("effective event-level sample count here as one", self.result["decision_use"])


if __name__ == "__main__":
    unittest.main()
