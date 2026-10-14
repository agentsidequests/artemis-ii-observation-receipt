from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10p_capture_run_concentration import verify_stage10p, verify_with_mutations  # noqa: E402


class Stage10PCaptureRunConcentrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10p(ROOT)

    def test_canary_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_FIVE_SECOND_CAPTURE_RUN_CONCENTRATION", self.result["evidence_state"])

    def test_largest_cluster_is_exact(self) -> None:
        item = self.result["largest_cluster"]
        self.assertEqual((1230, 410, 82, 75056509295), (
            item["products"], item["capture_identities"], item["complete_actions"], item["archive_size_bytes"],
        ))
        self.assertAlmostEqual(143.61, item["span_seconds"])
        self.assertEqual(["24_Sunset"], item["activity_ids"])
        self.assertEqual(["Sunset"], item["target_ids"])

    def test_concentration_is_cohort_scoped(self) -> None:
        item = self.result["largest_cluster"]
        self.assertAlmostEqual(0.05390481199053379, item["cohort_product_share"])
        self.assertAlmostEqual(0.0461806250262151, item["cohort_byte_share"])
        self.assertAlmostEqual(0.9999999886921788, item["expected_action_split_cross_probability_80_20"])

    def test_claim_ceiling_stays_nonsemantic_and_hypothetical(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("semantic scene", "activity or target correctness", "observed leakage", "performance effect", "global novelty or priority"):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
