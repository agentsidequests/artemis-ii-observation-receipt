from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10e_all_days_integrity import verify_stage10e, verify_with_mutations  # noqa: E402


class Stage10EAllDaysIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10e(ROOT)

    def test_all_days_fd6_concentration_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual(
            "VERIFIED_ALL_DAYS_WITH_FLIGHT_DAY_6_ONLY_FRAGMENTATION",
            self.result["evidence_state"],
        )

    def test_complete_source_denominator(self) -> None:
        self.assertEqual(10329, self.result["source_records"])
        self.assertEqual(
            {"1": 273, "2": 616, "3": 253, "4": 276, "5": 311, "6": 8423, "7": 98, "8": 79, "9": 0, "10": 0},
            self.result["flight_day_record_counts"],
        )

    def test_complete_action_denominator(self) -> None:
        self.assertEqual(2103, self.result["complete_brackets"])
        self.assertEqual(
            {"0,-1,+1": 290, "0,-2,+2": 1261, "0,-2,-1,+1,+2": 226, "0,-6,-3,+3,+6": 326},
            self.result["pattern_counts"],
        )

    def test_every_observed_fracture_is_on_flight_day_6(self) -> None:
        self.assertEqual(21, self.result["activity_fractured_brackets"])
        self.assertEqual(21, self.result["fractures_by_flight_day"]["6"])
        self.assertEqual(
            0,
            sum(count for day, count in self.result["fractures_by_flight_day"].items() if day != "6"),
        )

    def test_other_days_supply_real_negative_denominator(self) -> None:
        other_brackets = sum(
            count for day, count in self.result["brackets_by_flight_day"].items() if day != "6"
        )
        self.assertEqual(382, other_brackets)

    def test_stage10c_signature_survives_archive_expansion(self) -> None:
        self.assertEqual(13, self.result["repeated_signature_actions"])

    def test_claim_ceiling_preserves_concentration_not_causation(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in (
            "non-flight-day-6 images error-free",
            "lunar-flyby complexity caused",
            "non-bracket products",
            "correct activity labels",
            "wholesale",
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
