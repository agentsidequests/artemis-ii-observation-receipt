from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage8c_camera_native_canary import (  # noqa: E402
    verify_formation,
    verify_formation_with_mutations,
)


class Stage8CCameraNativeFormationTests(unittest.TestCase):
    def test_formation_admits_offline_scoring_only_after_zero_score_freeze(self) -> None:
        result = verify_formation(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("FORMED_NO_CAMERA_VALUE_SCORING", result["evidence_state"])
        self.assertEqual("ADMIT_FROZEN_OFFLINE_CAMERA_SCORING", result["disposition"])
        self.assertEqual(0, result["image_code_values_scored"])
        self.assertEqual(0, result["png_idat_streams_decompressed"])

    def test_joint_frame_is_primary_and_pair_is_not_independent_replication(self) -> None:
        result = verify_formation(ROOT)
        by_id = {item["id"]: item for item in result["checks"]}
        self.assertTrue(by_id["stage8b_admission_and_stage8a_non_reopening"]["pass"])
        self.assertTrue(by_id["joint_primary_pair_secondary"]["pass"])
        self.assertTrue(by_id["exact_source_identity"]["pass"])

    def test_coordinate_regions_pass_held_out_geometry_preflight(self) -> None:
        result = verify_formation(ROOT)
        check = {item["id"]: item for item in result["checks"]}[
            "coordinate_derived_regions_and_geometry_preflight"
        ]
        self.assertTrue(check["pass"])
        self.assertEqual(
            {"matched_glushko", "matched_ohm", "joint_glushko", "joint_ohm"},
            set(check["fits"]),
        )
        self.assertTrue(all(item["complete_region"] for item in check["fits"].values()))

    def test_rank_endpoint_keeps_photometry_and_perception_outside_claim(self) -> None:
        result = verify_formation(ROOT)
        by_id = {item["id"]: item for item in result["checks"]}
        self.assertTrue(by_id["png_and_uncalibrated_representation_boundary"]["pass"])
        self.assertTrue(by_id["rank_endpoint_and_frozen_oracle"]["pass"])
        self.assertTrue(by_id["claim_ceiling_and_branch_complete_next_steps"]["pass"])

    def test_every_formation_hard_negative_is_rejected(self) -> None:
        result = verify_formation_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
