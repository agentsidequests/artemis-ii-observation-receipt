from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10v_task_representation_fitness import verify_stage10v, verify_with_mutations  # noqa: E402


class Stage10VTaskRepresentationFitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10v(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_STORAGE_WEIGHT_NOT_CALIBRATION_LEVEL", self.result["evidence_state"])

    def test_processed_layer_dominates_both_footprints(self) -> None:
        item = self.result["footprint"]
        self.assertAlmostEqual(0.6793182059249131, item["cohort_processed_byte_share"])
        self.assertAlmostEqual(0.6844703123713605, item["sunset_processed_byte_share"])
        self.assertGreater(item["cohort_processed_to_source_byte_ratio"], 7.3)

    def test_no_calibrated_tier_is_invented(self) -> None:
        self.assertEqual(0, self.result["footprint"]["calibrated_product_tiers"])
        gate = self.result["task_representation_gate"]
        self.assertEqual("none_available", gate["instrument_independent_physical_measurement"])
        self.assertEqual("none_available", gate["quantitatively_verified_color"])

    def test_each_available_representation_has_a_distinct_task(self) -> None:
        gate = self.result["task_representation_gate"]
        self.assertEqual("source", gate["preserve_original_native_pixels_and_metadata"])
        self.assertEqual("raw", gate["open_standardized_bayer_array_analysis"])
        self.assertEqual("processed", gate["human_viewable_vendor_interpretation"])

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
