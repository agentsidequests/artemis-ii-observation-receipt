from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage6a_impact_reframe import verify_stage6a, verify_with_mutations  # noqa: E402


class Stage6AImpactReframeTests(unittest.TestCase):
    def test_reframe_selects_one_bounded_high_impact_lead(self) -> None:
        result = verify_stage6a(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_IMPACT_REFRAME", result["evidence_state"])
        self.assertEqual("CONTINUE_BOUNDED", result["disposition"])
        self.assertEqual(
            "orientale_aggregate_texture_below_object_resolution",
            result["selected_candidate_id"],
        )
        self.assertEqual(1, result["admitted_candidate_count"])
        self.assertEqual(0, result["network_bytes_in_verification"])

    def test_scale_relation_is_ten_to_sixty_times(self) -> None:
        result = verify_stage6a(ROOT)
        self.assertEqual([1.0, 6.0], result["scale_relation"]["object_resolution_km"])
        self.assertEqual(0.1, result["scale_relation"]["nominal_roughness_scale_km"])
        self.assertEqual([10.0, 60.0], result["scale_relation"]["contributing_scale_ratio"])
        self.assertIn("not direct resolution", result["scale_relation"]["interpretation"].lower())

    def test_two_exact_orientale_transcript_anchors_recur(self) -> None:
        result = verify_stage6a(ROOT)
        self.assertEqual(2, len(result["transcript_anchors"]))
        self.assertTrue(all(item["pass"] for item in result["transcript_anchors"]))
        self.assertTrue(all(item["match_count"] == 1 for item in result["transcript_anchors"]))

    def test_selected_lead_remains_direct_derivation(self) -> None:
        result = verify_stage6a(ROOT)
        selected = result["candidate_ranking"][0]
        self.assertEqual("DIRECT_DERIVATION", selected["novelty_classification"])
        self.assertEqual("CONTINUE_BOUNDED", selected["disposition"])
        self.assertEqual(
            "PLAUSIBLE_NOT_MISSION_VALIDATED",
            result["scale_relation"]["mechanism_state"],
        )

    def test_timing_and_metadata_do_not_displace_lead(self) -> None:
        result = verify_stage6a(ROOT)
        candidates = {item["id"]: item for item in result["candidate_ranking"]}
        self.assertEqual(
            "DEMOTE_TO_SUPPORTING_CLUE",
            candidates["event_specific_timing_anomaly"]["disposition"],
        )
        self.assertEqual(
            "STOP_NO_DELTA",
            candidates["archive_activity_and_target_metadata_friction"]["disposition"],
        )

    def test_every_stage6a_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
