from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10i_provenance_crosswalk import verify_stage10i, verify_with_mutations  # noqa: E402


class Stage10IProvenanceCrosswalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10i(ROOT)

    def test_crosswalk_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_NON_BIJECTIVE_PROVENANCE_CROSSWALK_WITH_RESIDUALS", self.result["evidence_state"])

    def test_crew_crosswalk_preserves_known_and_unknown_differences(self) -> None:
        self.assertEqual(10407, self.result["source_crew_files"])
        self.assertEqual(10329, self.result["current_nikon_identities"])
        self.assertEqual(68, self.result["documented_pending_iphone"])
        self.assertEqual({"3500015": 4, "3500017": 1, "3920019": 5}, self.result["unexplained_nikon_residuals"])

    def test_orion_residual_is_in_cab_cam_two(self) -> None:
        self.assertEqual(1040, self.result["source_orion_stills"])
        self.assertEqual(1012, self.result["current_orion_stills"])
        self.assertEqual(28, self.result["unexplained_orion_residuals"]["cab2"])
        self.assertEqual(28, sum(self.result["unexplained_orion_residuals"].values()))

    def test_audio_source_and_product_counts_are_not_equated(self) -> None:
        self.assertEqual(115, self.result["source_audio_files"])
        self.assertEqual(112, sum(self.result["current_audio_products"].values()))
        self.assertEqual(56, self.result["current_audio_products"]["data_audio_pcd"] + self.result["current_audio_products"]["data_audio_loops"])

    def test_decision_use_names_four_units(self) -> None:
        decision = self.result["decision_use"].lower()
        for phrase in ("source files", "downloadable products", "capture identities", "multi-frame actions"):
            self.assertIn(phrase, decision)

    def test_claim_ceiling_preserves_residual_uncertainty(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("lost", "release completeness", "three products", "transcripts", "snapshot"):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
