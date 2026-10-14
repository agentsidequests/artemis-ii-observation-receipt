from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage3b_completion_ledger import verify_stage3b, verify_with_mutations  # noqa: E402


class Stage3BCompletionLedgerTests(unittest.TestCase):
    def test_complete_classification_ledger_is_replayable(self) -> None:
        result = verify_stage3b(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_COMPLETE_CLASSIFICATION_LEDGER", result["evidence_state"])
        self.assertEqual(30, result["ledger_summary"]["classified_targets"])
        self.assertEqual(21, result["ledger_summary"]["stage3a_exact_anchors"])
        self.assertEqual(9, result["ledger_summary"]["stage3b_resolutions"])

    def test_eight_execution_supported_and_one_unresolved(self) -> None:
        result = verify_stage3b(ROOT)
        self.assertEqual(8, result["ledger_summary"]["execution_supported_resolutions"])
        self.assertEqual(1, result["ledger_summary"]["unresolved_resolutions"])
        forward = next(
            item for item in result["resolutions"] if item["id"] == "discussion6_forward_look"
        )
        self.assertEqual("UNRESOLVED_NO_DISTINCT_ENTRY", forward["evidence_class"])
        self.assertEqual("UNRESOLVED", forward["terminal_state"])
        self.assertIsNone(forward["entry_cue_utc"])

    def test_parallel_plan_entries_retain_distinct_evidence(self) -> None:
        result = verify_stage3b(ROOT)
        self.assertTrue(all(item["pass"] for item in result["overlap_contracts"]))
        self.assertEqual(
            [2, 2],
            [item["distinct_entry_cues"] for item in result["overlap_contracts"]],
        )
        first_pair = [
            item
            for item in result["resolutions"]
            if item.get("overlap_group") == "eclipsed_deep_space_1"
        ]
        self.assertEqual({26, 27}, {item["order"] for item in first_pair})
        self.assertEqual(2, len({item["entry_cue_utc"] for item in first_pair}))

    def test_content_evidence_does_not_inflate_exact_anchor_count(self) -> None:
        result = verify_stage3b(ROOT)
        classes = result["ledger_summary"]["evidence_class_counts"]
        self.assertEqual(3, classes["CONTENT_LED_ENTRY"])
        self.assertEqual(21, result["ledger_summary"]["stage3a_exact_anchors"])
        discussion = next(
            item for item in result["resolutions"] if item["id"] == "discussion2_near_farside"
        )
        self.assertEqual("2026-04-06T18:50:05.905Z", discussion["entry_cue_utc"])

    def test_flash_remains_physically_unvalidated(self) -> None:
        result = verify_stage3b(ROOT)
        self.assertEqual("UNVALIDATED_CAPTURE_CANDIDATE", result["flash_candidate_state"])
        frozen = next(item for item in result["checks"] if item["id"] == "frozen_result")
        self.assertEqual(0, frozen["observed"]["proven_missed_targets"])
        self.assertEqual(0, frozen["observed"]["proven_diverted_targets"])

    def test_all_stage3b_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
