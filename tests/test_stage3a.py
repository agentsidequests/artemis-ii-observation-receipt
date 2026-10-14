from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from artemis_testbed import run_testbed  # noqa: E402
from stage1_boundary_equivalence import verify_stage1  # noqa: E402
from stage2a_earthrise_coverage import verify_stage2a  # noqa: E402
from stage3_attention_allocation import verify_stage3a, verify_with_mutations  # noqa: E402


class Stage3AAttentionAllocationTests(unittest.TestCase):
    def test_partial_ledger_is_replayable(self) -> None:
        result = verify_stage3a(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_PARTIAL_LEDGER", result["evidence_state"])
        self.assertEqual(30, result["plan_inventory"]["numbered_targets"])
        self.assertEqual(21, result["plan_inventory"]["exact_entry_anchors"])
        self.assertEqual(9, len(result["plan_inventory"]["unresolved_entry_anchors"]))

    def test_request_to_cue_deltas_are_mixed_not_boundaries(self) -> None:
        summary = verify_stage3a(ROOT)["schedule_summary"]
        self.assertEqual(10, summary["early_anchor_count"])
        self.assertEqual(11, summary["late_anchor_count"])
        self.assertIn("not a physical-event time", summary["interpretation_limit"])

    def test_attention_classes_preserve_hard_negatives(self) -> None:
        result = verify_stage3a(ROOT)
        classes = {item["id"]: item["classification"] for item in result["attention_episodes"]}
        self.assertEqual("RESISTED_DIVERSION", classes["vavilov_refocus"])
        self.assertEqual("EXPECTED_CREW_CHOICE", classes["crew_choice_terminator"])
        self.assertEqual("ENTRY_INTERVAL_CENSORED", classes["impact_flash_recording_gap"])
        frozen = next(item for item in result["checks"] if item["id"] == "frozen_result")
        self.assertEqual(0, frozen["observed"]["proven_missed_targets"])
        self.assertEqual(0, frozen["observed"]["proven_diverted_targets"])

    def test_flash_remains_an_unvalidated_two_observer_candidate(self) -> None:
        result = verify_stage3a(ROOT)
        episode = next(
            item for item in result["attention_episodes"] if item["id"] == "forward_look_flash_candidate"
        )
        self.assertEqual("ATTENTION_SHIFT_CANDIDATE", episode["classification"])
        self.assertFalse(episode["independent_oracle"])
        self.assertEqual("UNVALIDATED_TWO_OBSERVER_CANDIDATE", result["flash_candidate_state"])
        self.assertEqual("2026-04-07T00:51:15.947Z", episode["cues"][1]["utc"])
        self.assertEqual("2026-04-07T00:51:57.628Z", episode["cues"][3]["utc"])

    def test_all_stage3a_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))

    def test_earlier_stages_remain_replayable(self) -> None:
        self.assertTrue(run_testbed(ROOT)["pass"])
        self.assertTrue(verify_stage1(ROOT)["pass"])
        self.assertTrue(verify_stage2a(ROOT)["pass"])


if __name__ == "__main__":
    unittest.main()
