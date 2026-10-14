from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10j_fractional_bracket_expansion import verify_stage10j, verify_with_mutations  # noqa: E402


class Stage10JFractionalBracketExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None: cls.result = verify_stage10j(ROOT)

    def test_expanded_oracle_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_FRACTIONAL_STOP_EXPANSION_AND_CROSS_DAY_RECURRENCE", self.result["evidence_state"])

    def test_expanded_denominator(self) -> None:
        self.assertEqual(2166, self.result["complete_brackets"])
        self.assertEqual(7606, self.result["exposures_in_complete_brackets"])
        self.assertEqual(2723, self.result["unadmitted_records"])

    def test_fractional_patterns_add_sixty_three_actions(self) -> None:
        self.assertEqual(61, self.result["pattern_counts"]["0,-2/3,+2/3"])
        self.assertEqual(2, self.result["pattern_counts"]["0,-4/3,-2/3,+2/3,+4/3"])
        self.assertEqual(63, self.result["fractional_pattern_actions"])

    def test_cross_day_fractures_supersede_fd6_only_claim(self) -> None:
        self.assertEqual(25, self.result["activity_fractures"])
        self.assertEqual(3, self.result["fractures_by_flight_day"]["3"])
        self.assertEqual(1, self.result["fractures_by_flight_day"]["4"])
        self.assertEqual(21, self.result["fractures_by_flight_day"]["6"])
        self.assertTrue(self.result["stage10e_generalization_superseded"])

    def test_new_fractures_preserve_target_state(self) -> None:
        self.assertEqual(23, self.result["target_presence_fractures"])
        self.assertEqual(1, self.result["target_value_fractures"])
        self.assertEqual(4, self.result["fractional_pattern_fractures"])

    def test_claim_ceiling_preserves_non_exhaustive_scope(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("pattern set exhaustive", "partial sequences", "correct activities", "stage 10f mechanism", "unadmitted actions"):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None: self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"]); self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__": unittest.main()
