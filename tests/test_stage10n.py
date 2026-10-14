from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10n_temporal_adjacency_sensitivity import verify_stage10n, verify_with_mutations  # noqa: E402


class Stage10NTemporalAdjacencySensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10n(ROOT)

    def test_sensitivity_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_TEMPORAL_ADJACENCY_SPLIT_SENSITIVITY", self.result["evidence_state"])

    def test_five_second_conditional_result(self) -> None:
        scenario = self.result["scenarios"]["5"]
        self.assertEqual((816, 306, 1656, 82), (
            scenario["clusters"], scenario["multi_action_clusters"],
            scenario["actions_in_multi_action_clusters"], scenario["maximum_cluster_actions"],
        ))
        self.assertAlmostEqual(1239.003659450896, scenario["expected_actions_in_crossing_clusters"])
        self.assertAlmostEqual(0.5720238501620019, scenario["expected_action_exposure_rate"])

    def test_full_sensitivity_is_monotonic(self) -> None:
        rates = [self.result["scenarios"][str(threshold)]["expected_action_exposure_rate"] for threshold in (1, 2, 5, 10, 30)]
        self.assertEqual(rates, sorted(rates))

    def test_five_second_clusters_have_non_independent_facet_concordance(self) -> None:
        diagnostic = self.result["five_second_facet_diagnostic"]
        self.assertEqual((290, 16, 0), (
            diagnostic["single_activity_clusters"], diagnostic["mixed_activity_clusters"], diagnostic["no_activity_clusters"],
        ))
        self.assertAlmostEqual(0.9477124183006536, diagnostic["single_activity_rate"])
        self.assertEqual((139, 132, 7, 167), (
            diagnostic["target_bearing_clusters"], diagnostic["single_target_clusters"],
            diagnostic["mixed_target_clusters"], diagnostic["no_target_clusters"],
        ))
        self.assertAlmostEqual(0.9496402877697842, diagnostic["single_target_rate_among_target_bearing"])

    def test_claim_ceiling_keeps_time_nonsemantic(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("semantic scenes", "observed leakage", "universal time threshold", "independent validation", "image similarity", "performance effect", "global novelty or priority"):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
