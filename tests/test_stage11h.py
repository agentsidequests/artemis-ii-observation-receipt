from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11h_protocol_context_alignment import verify_stage11h, verify_with_mutations  # noqa: E402


class Stage11HProtocolContextAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11h(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_PROTOCOL_CONTEXT_ALIGNMENT", self.result["evidence_state"])

    def test_action_union_and_weight_shift_are_exact(self) -> None:
        item = self.result["metrics"]
        self.assertEqual((1540, 994, 546, 17136, 8190), (
            item["plan_associated_unique_actions"], item["three_exposure_actions"],
            item["five_exposure_actions"], item["flat_products"], item["five_exposure_flat_products"],
        ))
        self.assertAlmostEqual(0.35454545454545455, item["five_exposure_action_share"])
        self.assertAlmostEqual(0.47794117647058826, item["five_exposure_product_share"])

    def test_camera_time_run_shape_is_exact(self) -> None:
        runs = self.result["camera_runs"]
        self.assertEqual([3, 5, 3], [item["exposures_in_action"] for item in runs["3500015"]])
        self.assertEqual([3], [item["exposures_in_action"] for item in runs["3500017"]])
        self.assertEqual([5], [item["exposures_in_action"] for item in runs["3920019"]])

    def test_camera_counts_are_exact(self) -> None:
        item = self.result["metrics"]
        self.assertEqual((1377, 987, 390, 2), (
            item["camera_3500015_actions"], item["camera_3500015_three_exposure_actions"],
            item["camera_3500015_five_exposure_actions"], item["camera_3500015_exposure_count_transitions"],
        ))
        self.assertEqual((7, 7, 0), (
            item["camera_3500017_actions"], item["camera_3500017_three_exposure_actions"],
            item["camera_3500017_five_exposure_actions"],
        ))
        self.assertEqual((156, 0, 156), (
            item["camera_3920019_actions"], item["camera_3920019_three_exposure_actions"],
            item["camera_3920019_five_exposure_actions"],
        ))
        self.assertAlmostEqual(0.1012987012987013, item["camera_3920019_action_share"])
        self.assertEqual(2340, item["camera_3920019_flat_products"])
        self.assertAlmostEqual(0.13655462184873948, item["camera_3920019_product_share"])
        self.assertAlmostEqual(1.3480392156862744, item["camera_3920019_product_vs_action_share_amplification"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
