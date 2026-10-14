from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11b_paired_window_admission import verify_stage11b, verify_with_mutations  # noqa: E402


class Stage11BPairedWindowAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11b(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_PAIRED_WINDOW_TASK_CANDIDATE", self.result["evidence_state"])

    def test_three_same_camera_disjoint_pairs_exist(self) -> None:
        item = self.result["cohort"]
        self.assertEqual((3, 6, 262, 786, 2358), (
            item["paired_geolocated_targets"], item["paired_windows"], item["complete_actions"],
            item["exposures"], item["products"],
        ))
        self.assertTrue(item["all_pairs_disjoint"] and item["all_pairs_same_camera"])

    def test_glushko_has_explicit_repeat_intent(self) -> None:
        pair = self.result["pairs"]["Glushko Crater"]
        self.assertEqual("explicit_photometric_viewing_condition_repeat", pair["repeat_intent"])
        self.assertEqual(6420.0, pair["window_gap_seconds"])
        self.assertEqual("ADMIT_PIXEL_BLIND_REGISTRATION_AND_PROTOCOL_GATE", self.result["selected_candidate"]["admission_state"])

    def test_sparse_tags_do_not_block_or_validate_content(self) -> None:
        self.assertEqual(18, self.result["cohort"]["exact_same_name_tagged_exposures"])
        self.assertAlmostEqual(0.022900763358778626, self.result["cohort"]["exact_same_name_tag_share"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"]); self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__": unittest.main()
