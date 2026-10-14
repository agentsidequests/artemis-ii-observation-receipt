from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10f_mechanism_triangulation import verify_stage10f, verify_with_mutations  # noqa: E402


class Stage10FMechanismTriangulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10f(ROOT)

    def test_partial_per_frame_curation_signature_is_supported(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual(
            "SUPPORTED_PARTIAL_PER_FRAME_CURATION_SIGNATURE",
            self.result["evidence_state"],
        )

    def test_repeated_signature_couples_position_activity_and_target(self) -> None:
        self.assertEqual(13, self.result["repeated_actions"])
        self.assertEqual(39, self.result["repeated_frames"])
        self.assertEqual(26, self.result["discussion_frames_with_terminator_target"])
        self.assertEqual(13, self.result["crew_choice_frames_without_target"])

    def test_signature_lies_inside_archived_crew_choice_request_window(self) -> None:
        self.assertTrue(self.result["signature_inside_crew_choice_request"])

    def test_inference_is_ranked_not_declared_proven(self) -> None:
        inference = self.result["supported_inference"].lower()
        self.assertIn("strongest current explanation", inference)
        self.assertIn("not a recovered edit log", inference)
        self.assertEqual(3, len(self.result["alternative_explanations"]))

    def test_decision_use_treats_activity_as_mixed_provenance(self) -> None:
        self.assertIn("mixed provenance field", self.result["decision_use"].lower())
        self.assertIn("reconstruct actions", self.result["decision_use"].lower())

    def test_claim_ceiling_preserves_edit_history_and_correctness_limits(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in (
            "cannot prove which records were human-overridden",
            "identify correct labels",
            "infer image content",
            "missing target always means default labeling",
            "without edit logs",
        ):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
