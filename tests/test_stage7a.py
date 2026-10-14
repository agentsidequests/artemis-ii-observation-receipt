from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage7a_semantic_lola_canary import (  # noqa: E402
    great_circle_km,
    load_json,
    pixel_latitude,
    pixel_longitude,
    probability_superiority,
    verify_stage7a,
    verify_with_mutations,
)


class Stage7ASemanticLolaCanaryTests(unittest.TestCase):
    def test_frozen_semantic_prediction_passes_the_canary(self) -> None:
        result = verify_stage7a(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["signal_pass"])
        self.assertEqual("COARSE_SEMANTIC_LOLA_CONCORDANCE", result["evidence_state"])
        self.assertEqual("CONTINUE_CONTROLLED_MULTI_TARGET", result["disposition"])
        self.assertEqual(0, result["network_bytes_in_verification"])

    def test_primary_ratios_clear_the_frozen_threshold_at_all_scales(self) -> None:
        result = verify_stage7a(ROOT)
        expected = {57: 1.7939956065, 225: 2.3989228007, 560: 3.0548614883}
        for baseline, expected_ratio in expected.items():
            metric = result["metrics"][str(baseline)]["20"]
            self.assertAlmostEqual(expected_ratio, metric["median_ratio"], places=9)
            self.assertGreaterEqual(metric["median_ratio"], 1.2)
            self.assertGreaterEqual(
                metric["probability_superiority_descriptive_only"], 0.65
            )

    def test_all_radius_and_scale_comparisons_agree(self) -> None:
        result = verify_stage7a(ROOT)
        self.assertTrue(result["robustness_pass"])
        self.assertEqual(9, result["robustness_comparisons_passing"])
        self.assertEqual(9, result["robustness_comparisons_total"])

    def test_source_is_bounded_hash_pinned_and_replayed_offline(self) -> None:
        result = verify_stage7a(ROOT)
        receipt = load_json(ROOT / "evidence" / "stage7a" / "acquisition-receipt.json")
        self.assertEqual(2362387, receipt["network_bytes"])
        self.assertLessEqual(receipt["network_bytes"], receipt["network_budget_bytes"])
        self.assertEqual([1402, 1469], receipt["line_range_zero_based_inclusive"])
        self.assertEqual(0, result["network_bytes_in_verification"])
        self.assertTrue(
            next(check for check in result["checks"] if check["id"] == "source_manifest_identity")["pass"]
        )

    def test_coordinate_mapping_matches_pixel_registered_contract(self) -> None:
        contract = load_json(ROOT / "spec" / "stage7a.json")["raster_contract"]
        self.assertAlmostEqual(0.03125, pixel_latitude(1439, contract))
        self.assertAlmostEqual(-0.03125, pixel_latitude(1440, contract))
        self.assertAlmostEqual(0.03125, pixel_longitude(0, contract))
        self.assertAlmostEqual(359.96875, pixel_longitude(5759, contract))
        self.assertAlmostEqual(
            0.0,
            great_circle_km(-0.87, 221.23, -0.87, 221.23, contract["moon_radius_km"]),
        )

    def test_superiority_metric_is_descriptive_and_tie_aware(self) -> None:
        self.assertEqual(1.0, probability_superiority([3.0, 4.0], [1.0, 2.0]))
        self.assertEqual(0.5, probability_superiority([2.0], [2.0]))
        self.assertEqual(0.0, probability_superiority([1.0], [2.0]))

    def test_claim_ceiling_keeps_confounders_and_novelty_unestablished(self) -> None:
        ceiling = verify_stage7a(ROOT)["claim_ceiling"].lower()
        self.assertIn("does not establish causation", ceiling)
        self.assertIn("perception below resolution", ceiling)
        self.assertIn("independence from geology or morphology", ceiling)
        self.assertIn("statistical significance", ceiling)
        self.assertIn("publishable scientific result", ceiling)

    def test_every_stage7a_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
