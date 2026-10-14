from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage9a_opportunity_selection import verify_stage9a  # noqa: E402
from stage9b_source_control_gate import (  # noqa: E402
    EVENT_FRAME_IDS,
    verify_stage9b,
    verify_with_mutations,
)


class Stage9BSourceControlGateTests(unittest.TestCase):
    def test_gate_verifies_terminal_stop(self) -> None:
        result = verify_stage9b(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_SOURCE_CONTROL_STOP", result["evidence_state"])
        self.assertEqual("SOURCE_CONTROL_INSUFFICIENT", result["disposition"])
        self.assertEqual(
            "CLOSE_GRAY_FEATURE_IMAGE_LANE_AT_CURRENT_ARCHIVE_BOUNDARY",
            result["lane_state"],
        )

    def test_exact_event_source_is_pcd3_not_overlapping_pcd2(self) -> None:
        result = verify_stage9b(ROOT)
        check = next(
            item for item in result["checks"] if item["id"] == "exact_pcd3_event_transcript"
        )
        self.assertTrue(check["pass"])
        mutated = verify_stage9b(
            ROOT, "substitute_overlapping_pcd2_for_exact_pcd3_event_source"
        )
        self.assertFalse(mutated["pass"])

    def test_bounded_window_is_complete_and_contains_40_d5_frames(self) -> None:
        result = verify_stage9b(ROOT)
        self.assertEqual(41, result["atlas_hits"])
        self.assertEqual(40, result["crew_raw_frames"])
        self.assertEqual(EVENT_FRAME_IDS, result["event_bracket_frames"])

    def test_event_bracket_begins_20_milliseconds_after_report(self) -> None:
        result = verify_stage9b(ROOT)
        self.assertAlmostEqual(0.020, result["first_d5_offset_seconds"], places=9)
        self.assertAlmostEqual(4.990, result["external_saw_offset_seconds"], places=9)

    def test_five_event_labels_preserve_the_exposure_bracket(self) -> None:
        result = verify_stage9b(ROOT)
        check = next(
            item for item in result["checks"] if item["id"] == "event_label_contracts"
        )
        self.assertTrue(check["pass"])
        self.assertEqual(
            ["0.001", "5.0E-4", "6.25E-4", "0.00125", "0.002"],
            [item["exposure"] for item in check["labels"]],
        )

    def test_source_gate_opens_no_candidate_pixels(self) -> None:
        result = verify_stage9b(ROOT)
        self.assertEqual(0, result["new_candidate_pixel_bytes"])
        check = next(
            item for item in result["checks"] if item["id"] == "zero_candidate_pixel_access"
        )
        self.assertTrue(check["pass"])

    def test_partial_and_failed_controls_prevent_admission(self) -> None:
        statuses = verify_stage9b(ROOT)["dimension_statuses"]
        self.assertEqual("PARTIAL", statuses["D_rigid_terrain_control"])
        self.assertEqual("PARTIAL", statuses["E_observer_window_carrier_binding"])
        for dimension_id in (
            "F_cabin_window_optical_control",
            "G_external_comparable_carrier",
            "H_event_geometry",
            "I_calibrated_faint_source_response",
        ):
            self.assertEqual("FAIL", statuses[dimension_id])

    def test_claim_ceiling_preserves_dust_and_pixel_boundaries(self) -> None:
        ceiling = verify_stage9b(ROOT)["claim_ceiling"].lower()
        for phrase in (
            "does not inspect event pixels",
            "detect or exclude lunar dust",
            "refute koch",
            "public scientific finding",
        ):
            self.assertIn(phrase, ceiling)

    def test_stage9a_selection_remains_valid(self) -> None:
        result = verify_stage9a(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(
            "pre_earthrise_gray_feature_discrimination",
            result["selected_candidate"],
        )

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
