from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10q_sunset_transcript_alignment import verify_stage10q, verify_with_mutations  # noqa: E402


class Stage10QSunsetTranscriptAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10q(ROOT)

    def test_canary_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_TRANSCRIPT_ALIGNED_OBSERVATION_EPISODE", self.result["evidence_state"])

    def test_exact_alignment_is_frozen(self) -> None:
        item = self.result["alignment"]
        self.assertEqual(35, item["inside_utterances"])
        self.assertEqual({"Hansen": 34, "Wiseman": 1}, item["inside_speaker_counts"])
        self.assertAlmostEqual(2.084, item["nearest_prior_lead_seconds"])
        self.assertAlmostEqual(0.013, item["nearest_after_offset_seconds"])

    def test_observation_vocabulary_is_present(self) -> None:
        self.assertEqual(["streamer", "plume", "glow", "moon", "sun"], self.result["alignment"]["required_inside_terms"])

    def test_claim_ceiling_preserves_visual_and_pipeline_unknowns(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("semantic scene", "visual similarity", "operator identity", "observed leakage", "model-performance effect", "scientific discovery"):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
