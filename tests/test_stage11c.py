from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11c_plan_realization_boundary import verify_stage11c, verify_with_mutations  # noqa: E402


class Stage11CPlanRealizationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11c(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_PLAN_REALIZATION_BOUNDARY_DIVERGENCE", self.result["evidence_state"])

    def test_schedule_misses_early_transcript_envelope_actions(self) -> None:
        self.assertEqual(17, self.result["segments"]["transcript_envelope_before_schedule"]["actions"])
        self.assertAlmostEqual(0.6071428571428571, self.result["overlap_measures"]["transcript_envelope_actions_before_schedule_share"])

    def test_schedule_retains_post_transition_actions(self) -> None:
        segment = self.result["segments"]["scheduled_window_after_orientale_transition"]
        self.assertEqual((23, 69, 207), (segment["actions"], segment["exposures"], segment["products"]))
        self.assertEqual({"11_Glushko Crater (2/2)": 23}, segment["activity_ids"])

    def test_transcript_envelope_is_not_promoted_to_pure_content(self) -> None:
        self.assertEqual(4, self.result["segments"]["explicit_internal_diversion"]["actions"])
        self.assertEqual("REQUIRE_REALIZED_SEGMENT_REGISTRATION_BEFORE_PAIRED_WINDOW_TASK", self.result["disposition"])
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
