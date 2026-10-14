from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10a_metadata_integrity import verify_stage10a, verify_with_mutations  # noqa: E402


class Stage10AMetadataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10a(ROOT)

    def test_complete_denominator_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual(8423, self.result["source_records"])

    def test_camera_native_brackets_are_detected(self) -> None:
        self.assertGreater(self.result["complete_brackets"], 0)
        check = next(
            item
            for item in self.result["checks"]
            if item["id"] == "camera_native_complete_bracket_oracle"
        )
        self.assertTrue(check["pass"])

    def test_known_fractured_bracket_is_reproduced(self) -> None:
        check = next(
            item for item in self.result["checks"] if item["id"] == "known_case_reproduction"
        )
        self.assertTrue(check["pass"])
        self.assertGreater(self.result["activity_fractured_brackets"], 0)

    def test_activity_facet_fragmentation_is_the_evidence_state(self) -> None:
        self.assertEqual(
            "VERIFIED_ACTIVITY_FACET_FRAGMENTATION", self.result["evidence_state"]
        )

    def test_no_pixel_payload_was_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_claim_ceiling_preserves_content_and_scope_limits(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in (
            "cannot identify the correct tag",
            "infer image content",
            "other flight days",
            "invalidate the pixel archive",
        ):
            self.assertIn(phrase, ceiling)

    def test_official_semantics_and_target_limit_are_preserved(self) -> None:
        check = next(
            item
            for item in self.result["checks"]
            if item["id"] == "official_field_semantics_and_limit"
        )
        self.assertTrue(check["pass"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
