from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10w_target_tag_selection import verify_stage10w, verify_with_mutations  # noqa: E402


class Stage10WTargetTagSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10w(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_NONUNIFORM_TARGET_TAG_COVERAGE", self.result["evidence_state"])

    def test_only_a_minority_of_exposures_are_tagged(self) -> None:
        item = self.result["coverage"]
        self.assertEqual((3413, 4193, 7606), (item["target_tag_present"], item["target_tag_blank"], item["source_exposures"]))
        self.assertAlmostEqual(0.4487246910333947, item["target_tag_coverage"])

    def test_activity_coverage_spans_zero_complete_and_partial(self) -> None:
        item = self.result["coverage"]
        self.assertEqual((17, 8, 20), (item["zero_coverage_activities"], item["full_coverage_activities"], item["partial_coverage_activities"]))
        self.assertEqual({"exposures": 1294, "tagged": 1294}, self.result["activity_examples"]["24_Sunset"])
        self.assertEqual({"exposures": 399, "tagged": 0}, self.result["activity_examples"]["12_Orientale Basin (2/2)"])

    def test_activity_lookup_is_descriptive_not_held_out(self) -> None:
        item = self.result["coverage"]
        self.assertAlmostEqual(0.8204646313259204, item["activity_tag_presence_cramers_v"])
        self.assertAlmostEqual(0.8748356560610044, item["activity_majority_lookup_accuracy"])
        self.assertIn("in-sample", self.result["verified"].lower())

    def test_stage10u_mechanism_is_qualified(self) -> None:
        self.assertIn("acquisition-only", self.result["decision_use"])
        self.assertIn("both acquisition and curation", self.result["claim_ceiling"])

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
