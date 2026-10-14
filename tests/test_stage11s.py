from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11s_attention_conditioned_detection import (  # noqa: E402
    verify_stage11s,
    verify_with_mutations,
)


class Stage11SAttentionConditionedDetectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_with_mutations(ROOT)

    def test_stage_verifies_and_all_hard_negatives_fail(self) -> None:
        self.assertTrue(self.result["pass"], self.result["checks"])
        self.assertEqual(
            "VERIFIED_ATTENTION_CONDITIONED_OBSERVATION_PROCESS",
            self.result["evidence_state"],
        )
        self.assertTrue(self.result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in self.result["hard_negatives"].values()))

    def test_exact_intervals_reproduce(self) -> None:
        deltas = self.result["deltas_seconds"]
        expected = {
            "first_report_to_search_intent_seconds": 138.865,
            "first_report_to_display_dimming_seconds": 180.764,
            "dedicated_watch_to_shared_report_seconds": 376.526,
            "dedicated_watch_to_timeline_return_seconds": 500.143,
            "shared_report_to_ambiguous_candidate_seconds": 96.464,
            "ground_prompt_end_to_candidate_seconds": 12.462,
            "first_to_last_clear_report_seconds": 1324.226,
        }
        for key, value in expected.items():
            self.assertAlmostEqual(value, deltas[key], places=6)

    def test_causal_and_physical_claims_are_withheld(self) -> None:
        self.assertTrue(all(not value for value in self.result["prohibited_claims"].values()))
        ceiling = self.result["claim_ceiling"].casefold()
        for phrase in (
            "detection probability",
            "witness independence",
            "physical impact rate",
            "physical clustering",
            "prompt causation",
            "event photometry",
        ):
            self.assertIn(phrase, ceiling)

    def test_missing_anchor_and_reordered_state_are_observable(self) -> None:
        self.assertFalse(verify_stage11s(ROOT, "drop_display_dimming_anchor")["pass"])
        reordered = verify_stage11s(ROOT, "move_search_intent_after_shared_report")
        self.assertFalse(reordered["checks"]["required_temporal_order"])

    def test_no_pixels_and_no_em_dash(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes_opened"])
        for relative in (
            "spec/stage11s.json",
            "src/stage11s_attention_conditioned_detection.py",
            "tests/test_stage11s.py",
        ):
            self.assertNotIn(chr(0x2014), (ROOT / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
