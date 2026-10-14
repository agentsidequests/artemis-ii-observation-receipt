from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11u_selection_weighting_cascade import (  # noqa: E402
    concentration_equivalent,
    ratio,
    verify_with_mutations,
)


class Stage11USelectionWeightingCascadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_with_mutations(ROOT)

    def test_stage_verifies_and_hard_negatives_fail(self) -> None:
        self.assertTrue(self.result["pass"], self.result["checks"])
        self.assertEqual(
            "VERIFIED_SELECTION_WEIGHTING_CASCADE",
            self.result["evidence_state"],
        )
        self.assertTrue(self.result["hard_negatives_pass"])

    def test_direct_manifest_golden_counts(self) -> None:
        path = ROOT / "results/stage10o-product-relationship-manifest.csv"
        with path.open("r", encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        source = [row for row in rows if row["collection_id"] == "data_source"]
        tagged = [row for row in source if row["target_id"]]
        sunset = [row for row in source if row["target_id"] == "Sunset"]
        self.assertEqual((7606, 3413, 1553), (len(source), len(tagged), len(sunset)))

    def test_selection_conditioning_identity(self) -> None:
        panel = self.result["metrics"]["selection_panel"]
        expected = ratio(
            panel["sunset_share_of_tagged_source_exposures"],
            panel["sunset_tag_occupancy_all_source_exposures"],
        )
        self.assertAlmostEqual(expected, panel["nonblank_conditioning_amplification"])
        self.assertGreater(panel["nonblank_conditioning_amplification"], 2.0)

    def test_exposure_product_identity_is_not_independence(self) -> None:
        panel = self.result["metrics"]["strict_tagged_weighting_panel"]
        self.assertEqual(3.0, panel["representations_per_exposure"])
        self.assertAlmostEqual(
            panel["sunset_share_of_tagged_exposures"],
            panel["sunset_share_of_tagged_products"],
        )
        self.assertIn("independent", self.result["claim_ceiling"].casefold())

    def test_byte_majority_survives_action_carried_sensitivity(self) -> None:
        strict = self.result["metrics"]["strict_tagged_weighting_panel"]
        sensitivity = self.result["metrics"]["action_carried_sensitivity"]
        self.assertGreater(strict["sunset_share_of_tagged_bytes"], 0.5)
        self.assertGreater(sensitivity["sunset_share_of_selected_action_bytes"], 0.5)

    def test_byte_majority_is_representation_sensitive(self) -> None:
        item = self.result["metrics"]["collection_byte_sensitivity"]
        self.assertLess(item["data_source"]["sunset_share"], 0.5)
        self.assertGreater(item["data_raw"]["sunset_share"], 0.5)
        self.assertGreater(item["data_processed"]["sunset_share"], 0.5)
        self.assertAlmostEqual(0.4918751992382373, item["data_source"]["sunset_share"])
        self.assertAlmostEqual(0.52719734536919, item["data_raw"]["sunset_share"])
        self.assertAlmostEqual(0.5273412245809236, item["data_processed"]["sunset_share"])

    def test_activity_structure_attribution(self) -> None:
        item = self.result["metrics"]["activity_structure_attribution"]
        outside = item["outside_activity"]
        self.assertEqual("24_Sunset", item["activity_id"])
        self.assertEqual((1294, 1553), (
            item["sunset_tagged_exposures_in_activity"],
            item["sunset_tagged_exposures_all"],
        ))
        self.assertAlmostEqual(0.83322601416613, item["share_of_sunset_tagged_exposures_from_activity"])
        self.assertAlmostEqual(0.12222746578574799, outside["sunset_share_of_tagged_exposures"])
        self.assertAlmostEqual(0.21553587192522253, outside["sunset_share_of_tagged_bytes"])

    def test_all_tag_countercheck_is_not_sunset_only(self) -> None:
        item = self.result["metrics"]["all_tag_countercheck"]
        concentration = item["concentration_equivalent_target_tag_values"]
        self.assertEqual(23, item["target_tag_values"])
        self.assertEqual(3, item["multi_target_actions"])
        self.assertAlmostEqual(915.0, item["fractional_action_weight_total"])
        self.assertGreater(concentration["fractional_actions"], concentration["exposures"])
        self.assertGreater(concentration["exposures"], concentration["archive_size_bytes"])
        self.assertEqual({1}, set(item["sunset_rank"].values()))

    def test_concentration_equivalent_identity(self) -> None:
        self.assertAlmostEqual(3.0, concentration_equivalent([1.0, 1.0, 1.0]))
        self.assertLess(concentration_equivalent([8.0, 1.0, 1.0]), 2.0)

    def test_population_and_unit_are_explicit(self) -> None:
        self.assertTrue(self.result["checks"]["population_and_unit_labels"])
        finding = self.result["finding"].casefold()
        for phrase in ("frozen cohort", "source-exposure rows", "tagged subset", "actions", "bytes"):
            self.assertIn(phrase, finding)

    def test_receipt_marks_partial_independence(self) -> None:
        receipt = self.result["verification_receipt"]
        self.assertEqual("partial", receipt["independence"])
        self.assertIn("no pixel", receipt["coverage_boundary"].casefold())

    def test_no_pixels_and_no_em_dash(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes_opened"])
        for relative in (
            "spec/stage11u.json",
            "src/stage11u_selection_weighting_cascade.py",
            "tests/test_stage11u.py",
        ):
            self.assertNotIn(chr(0x2014), (ROOT / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
