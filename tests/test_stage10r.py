from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10r_cross_camera_sunset_episode import verify_stage10r, verify_with_mutations  # noqa: E402


class Stage10RCrossCameraSunsetEpisodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10r(ROOT)

    def test_canary_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_CROSS_CAMERA_CROSS_FACET_OBSERVATION_EPISODE", self.result["evidence_state"])

    def test_combined_episode_is_exact(self) -> None:
        item = self.result["episode"]
        self.assertEqual((2010, 670, 134, 177543697399), (
            item["combined_products"], item["combined_capture_identities"],
            item["combined_complete_actions"], item["combined_archive_size_bytes"],
        ))
        self.assertEqual((2, 2, 24), (
            item["distinct_cameras"], item["distinct_activity_ids"], item["secondary_transcript_utterances"],
        ))
        self.assertAlmostEqual(0.088088351301604, item["cohort_product_share"])
        self.assertAlmostEqual(0.061865189289012, item["cohort_action_share"])
        self.assertAlmostEqual(0.10923874547809825, item["cohort_byte_share"])

    def test_cross_camera_and_cross_facet_values_are_preserved(self) -> None:
        item = self.result["episode"]
        self.assertEqual(("3500015", "3920019"), (item["primary_camera"], item["secondary_camera"]))
        self.assertEqual(("24_Sunset", ["24_Sunset", "h_Observation Break"], "Sunset"), (
            item["primary_activity"], item["secondary_activity_ids"], item["shared_target"],
        ))
        self.assertEqual(3, item["secondary_cluster_count"])

    def test_claim_ceiling_preserves_semantic_and_pipeline_unknowns(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("semantic scene", "visual redundancy", "activity-label error", "camera-operator identity", "observed leakage", "model-performance effect"):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
