from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10c_camera_action_integrity import verify_stage10c, verify_with_mutations  # noqa: E402


class Stage10CCameraActionIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10c(ROOT)

    def test_recurrent_position_structured_fragmentation_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual(
            "VERIFIED_RECURRENT_POSITION_STRUCTURED_FRAGMENTATION",
            self.result["evidence_state"],
        )

    def test_complete_action_denominator_and_pattern_counts(self) -> None:
        self.assertEqual(1721, self.result["complete_brackets"])
        self.assertEqual(
            {
                "0,-1,+1": 57,
                "0,-2,+2": 1117,
                "0,-2,-1,+1,+2": 221,
                "0,-6,-3,+3,+6": 326,
            },
            self.result["pattern_counts"],
        )

    def test_activity_fragmentation_repeats_across_patterns(self) -> None:
        self.assertEqual(21, self.result["activity_fractured_brackets"])
        self.assertAlmostEqual(21 / 1721, self.result["activity_fracture_rate"])
        self.assertEqual(
            {"0,-2,+2": 18, "0,-2,-1,+1,+2": 2, "0,-6,-3,+3,+6": 1},
            self.result["fractured_pattern_counts"],
        )

    def test_target_presence_is_associated_but_not_a_content_oracle(self) -> None:
        self.assertEqual(
            19, self.result["target_presence_fractures_among_activity_fractures"]
        )
        self.assertEqual(1, self.result["target_value_fractures_among_activity_fractures"])

    def test_thirteen_action_position_signature_repeats(self) -> None:
        run = self.result["repeated_signature_run"]
        self.assertEqual(13, len(run))
        self.assertEqual("2026-04-06T21:47:06.850Z", run[0]["start_time"])
        self.assertEqual("2026-04-06T21:47:56.420Z", run[-1]["end_time"])
        for bracket in run:
            self.assertEqual(["0", "-2", "+2"], bracket["bracket_values"])
            self.assertEqual(
                [
                    "15_Discussion #4: Terminator",
                    "14_Crew Choice #2",
                    "15_Discussion #4: Terminator",
                ],
                bracket["activity_ids"],
            )
            self.assertEqual(["Terminator", None, "Terminator"], bracket["target_ids"])

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_claim_ceiling_preserves_correctness_cause_and_scope_boundaries(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in (
            "which label is correct",
            "call every fracture an error",
            "assign one authoring cause",
            "other flight days",
            "coarse retrieval value",
        ):
            self.assertIn(phrase, ceiling)

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
