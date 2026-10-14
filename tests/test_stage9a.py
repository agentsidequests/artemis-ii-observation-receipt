from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage9a_opportunity_selection import (  # noqa: E402
    verify_stage9a,
    verify_with_mutations,
)


class Stage9AOpportunitySelectionTests(unittest.TestCase):
    def test_archive_wide_selection_verifies(self) -> None:
        result = verify_stage9a(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_OPPORTUNITY_SELECTED", result["evidence_state"])
        self.assertEqual(
            "pre_earthrise_gray_feature_discrimination",
            result["selected_candidate"],
        )
        self.assertEqual("ADMIT_NO_PIXEL_SOURCE_CONTROL_GATE", result["disposition"])

    def test_selected_candidate_beats_one_other_admitted_candidate(self) -> None:
        result = verify_stage9a(ROOT)
        self.assertEqual(
            [
                "pre_earthrise_gray_feature_discrimination",
                "systematic_activity_metadata_integrity",
            ],
            result["admitted_candidate_ids"],
        )

    def test_truthful_synthesis_and_stop_are_real_comparators(self) -> None:
        self.assertEqual(
            ["deliberate_stop", "truthful_operational_synthesis"],
            verify_stage9a(ROOT)["comparator_ids"],
        )

    def test_selection_opens_no_new_candidate_pixels(self) -> None:
        result = verify_stage9a(ROOT)
        self.assertEqual(0, result["new_candidate_pixel_bytes"])
        check = next(
            item for item in result["checks"] if item["id"] == "no_new_pixel_next_step"
        )
        self.assertTrue(check["pass"])

    def test_claim_ceiling_does_not_report_dust(self) -> None:
        ceiling = verify_stage9a(ROOT)["claim_ceiling"].lower()
        self.assertIn("not a lunar-dust detection", ceiling)
        self.assertIn("not", ceiling)
        self.assertIn("public scientific finding", ceiling)

    def test_primary_times_and_sensitivity_boundary_are_frozen(self) -> None:
        result = verify_stage9a(ROOT)
        for check_id in (
            "primary_source_and_project_anchors",
            "external_camera_sensitivity_boundary",
        ):
            check = next(item for item in result["checks"] if item["id"] == check_id)
            self.assertTrue(check["pass"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
