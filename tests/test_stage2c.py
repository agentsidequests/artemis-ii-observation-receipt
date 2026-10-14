from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage2a_earthrise_coverage import verify_stage2a  # noqa: E402
from stage2b_fixed_camera_replication import verify_stage2b  # noqa: E402
from stage2c_source_explanation_gate import verify_stage2c, verify_with_mutations  # noqa: E402


class Stage2CSourceExplanationGateTests(unittest.TestCase):
    def test_source_only_gate_nominates_one_bounded_hypothesis(self) -> None:
        result = verify_stage2c(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_SOURCE_NOMINATED_HYPOTHESIS", result["evidence_state"])
        self.assertEqual("HYPOTHESIS_NOMINATED_STOP_SOURCE_ONLY", result["disposition"])
        self.assertEqual(1, result["admitted_candidate_count"])
        self.assertEqual(0, result["network_bytes_in_verification"])

    def test_documented_delta_falls_inside_earthrise_lag(self) -> None:
        result = verify_stage2c(ROOT)
        alignment = result["planning_alignment"]
        self.assertEqual(154.0, alignment["documented_matched_view_delta_seconds"])
        self.assertEqual(136.0, alignment["earthrise_clearance_lag_minimum_inclusive_seconds"])
        self.assertEqual(166.0, alignment["earthrise_clearance_lag_maximum_exclusive_seconds"])
        self.assertTrue(
            alignment["relations"][
                "reported_example_delta_inside_earthrise_clearance_lag_bracket"
            ]
        )

    def test_window_widths_have_opposite_offset_tolerance(self) -> None:
        result = verify_stage2c(ROOT)
        alignment = result["planning_alignment"]
        self.assertEqual(196.650033, alignment["earthset_availability_duration_seconds"])
        self.assertEqual(4.147844, alignment["earthrise_availability_duration_seconds"])
        self.assertTrue(
            alignment["relations"]["earthset_window_wider_than_reported_example_delta"]
        )
        self.assertTrue(
            alignment["relations"]["earthrise_window_narrower_than_reported_example_delta"]
        )

    def test_non_explanatory_field_differences_remain_bounded(self) -> None:
        result = verify_stage2c(ROOT)
        candidates = {item["id"]: item for item in result["candidate_evaluations"]}
        self.assertEqual(
            "NOT_NOMINATED_ACTIVITY_SLOT_ONLY",
            candidates["request_duration"]["status"],
        )
        self.assertEqual(
            "NOT_NOMINATED_NO_AVAILABILITY_MAPPING",
            candidates["science_situation_report"]["status"],
        )
        self.assertEqual(
            "HARD_NEGATIVE_SAME_VALUES",
            candidates["shared_science_and_camera_fields"]["status"],
        )

    def test_every_stage2c_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))

    def test_prior_coverage_results_remain_replayable(self) -> None:
        stage2a = verify_stage2a(ROOT)
        stage2b = verify_stage2b(ROOT)
        self.assertTrue(stage2a["pass"], stage2a["errors"])
        self.assertEqual("AFTER_EVENT_NO_OVERLAP", stage2a["coverage_relation"])
        self.assertTrue(stage2b["pass"], stage2b["errors"])
        self.assertEqual("OVERLAPS_EVENT", stage2b["events"]["earthset"]["coverage_relation"])


if __name__ == "__main__":
    unittest.main()
