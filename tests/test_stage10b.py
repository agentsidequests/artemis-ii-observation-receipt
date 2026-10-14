from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10b_representation_audit import verify_stage10b, verify_with_mutations  # noqa: E402


class Stage10BRepresentationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10b(ROOT)

    def test_isolated_scalar_ambiguity_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual(
            "VERIFIED_ISOLATED_SCALAR_AMBIGUITY", self.result["evidence_state"]
        )

    def test_complete_focus_facet_has_two_records(self) -> None:
        self.assertEqual(8423, self.result["source_records"])
        self.assertEqual(2, self.result["focus_record_count"])
        self.assertEqual([2948, 2954], [int(item["shutter_count"]) for item in self.result["focus_records"]])

    def test_both_focus_records_are_isolated_between_sunset_neighbors(self) -> None:
        contexts = self.result["neighbor_contexts"]
        self.assertEqual(2, len(contexts))
        for context in contexts:
            self.assertEqual("24_Sunset", context["previous"]["activity_id"])
            self.assertEqual("24_Sunset", context["following"]["activity_id"])
            self.assertEqual(1, context["previous_shutter_delta"])
            self.assertEqual(1, context["following_shutter_delta"])

    def test_focus_facet_recovers_zero_complete_camera_actions(self) -> None:
        self.assertEqual(2, self.result["physical_actions_touched"])
        self.assertEqual(0, self.result["focus_only_complete_actions"])
        self.assertEqual(8, self.result["companion_records_needed_for_complete_actions"])

    def test_schema_allows_one_activity_id(self) -> None:
        self.assertEqual("1", self.result["schema_activity_id_max_occurs"])

    def test_plan_is_context_not_execution_oracle(self) -> None:
        self.assertTrue(self.result["focus_within_nominal_plan_window"])
        check = next(
            item
            for item in self.result["checks"]
            if item["id"] == "plan_is_timing_context_not_execution_oracle"
        )
        self.assertTrue(check["pass"])

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_claim_ceiling_preserves_ambiguity(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in (
            "overlapping intent, curation, or error",
            "cannot decide which labels are correct",
            "prove forward look execution",
            "assign causality to the schema",
        ):
            self.assertIn(phrase, ceiling)

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
