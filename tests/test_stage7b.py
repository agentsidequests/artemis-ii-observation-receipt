from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage7b_multi_target_admission import (  # noqa: E402
    verify_stage7b,
    verify_with_mutations,
)


class Stage7BMultiTargetAdmissionTests(unittest.TestCase):
    def test_transcript_only_gate_verifies_the_stop(self) -> None:
        result = verify_stage7b(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertFalse(result["panel_admitted"])
        self.assertEqual("VERIFIED_ADMISSION_STOP", result["evidence_state"])
        self.assertEqual("STOP_NO_NEW_INSTRUMENT_ACCESS", result["disposition"])

    def test_no_new_same_endpoint_comparison_qualifies(self) -> None:
        result = verify_stage7b(ROOT)
        self.assertEqual([], result["qualifying_same_endpoint_ids"])
        self.assertEqual(0, result["observed_counts"]["new_directional_comparisons"])
        self.assertEqual(0, result["observed_counts"]["unique_named_non_orientale_targets"])
        self.assertEqual(0, result["observed_counts"]["morphology_matched_pairs"])

    def test_stage7a_and_orientale_are_not_recycled(self) -> None:
        result = verify_stage7b(ROOT)
        classification = next(
            check
            for check in result["checks"]
            if check["id"] == "candidate_classification_and_counts"
        )
        self.assertTrue(classification["pass"])
        self.assertNotIn("vavilov_vs_hertzsprung_roughness", classification["qualifying_ids"])
        self.assertNotIn("orientale_vs_hertzsprung_texture", classification["qualifying_ids"])

    def test_cross_axis_candidates_remain_separate(self) -> None:
        result = verify_stage7b(ROOT)
        self.assertEqual(
            ["glushko_vs_ohm_ray_brightness", "reiner_gamma_albedo_uniformity"],
            result["cross_axis_candidates"],
        )

    def test_gate_spends_zero_new_instrument_value_bytes(self) -> None:
        result = verify_stage7b(ROOT)
        self.assertEqual(0, result["new_instrument_value_bytes"])
        check = next(
            check for check in result["checks"] if check["id"] == "no_post_gate_value_access"
        )
        self.assertTrue(check["pass"])

    def test_stop_does_not_refute_stage7a_or_future_observations(self) -> None:
        ceiling = verify_stage7b(ROOT)["claim_ceiling"].lower()
        self.assertIn("does not refute stage 7a", ceiling)
        self.assertIn("broader value of astronaut language", ceiling)
        self.assertIn("cross-axis candidates", ceiling)
        self.assertIn("new independently coded observations", ceiling)

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
