from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage8b_stimulus_recoverability import (  # noqa: E402
    verify_formation,
    verify_formation_with_mutations,
)


class Stage8BFormationTests(unittest.TestCase):
    def test_formation_admits_only_three_scene_source_acquisition(self) -> None:
        result = verify_formation(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("FORMED_METADATA_ONLY_NO_PIXEL_ACCESS", result["evidence_state"])
        self.assertEqual("ADMIT_THREE_SCENE_SOURCE_ACQUISITION", result["disposition"])
        self.assertEqual(0, result["browse_pixel_bytes_accessed"])
        self.assertEqual(0, result["browse_images_inspected"])

    def test_pair_camera_state_and_source_identities_are_frozen(self) -> None:
        result = verify_formation(ROOT)
        by_id = {item["id"]: item for item in result["checks"]}
        self.assertTrue(by_id["three_predeclared_products"]["pass"])
        self.assertTrue(by_id["matched_pair_camera_state"]["pass"])
        self.assertTrue(by_id["transcript_identity_and_anchors"]["pass"])

    def test_geometry_and_human_mapping_are_independent_requirements(self) -> None:
        result = verify_formation(ROOT)
        by_id = {item["id"]: item for item in result["checks"]}
        self.assertTrue(by_id["six_dimension_recoverability_boundary"]["pass"])
        self.assertTrue(by_id["ordered_oracle"]["pass"])
        self.assertTrue(by_id["claim_ceiling"]["pass"])

    def test_every_formation_hard_negative_is_rejected(self) -> None:
        result = verify_formation_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
