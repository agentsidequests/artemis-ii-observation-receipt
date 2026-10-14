from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10l_representation_compression import verify_stage10l, verify_with_mutations  # noqa: E402


class Stage10LRepresentationCompressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10l(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_COMPLETE_ACTION_REPRESENTATION_COMPRESSION", self.result["evidence_state"])

    def test_every_identity_has_three_products(self) -> None:
        self.assertEqual((22818, 7606, 2166), (self.result["products"], self.result["capture_identities"], self.result["complete_actions"]))
        self.assertEqual({"data_source": 7606, "data_raw": 7606, "data_processed": 7606}, self.result["collection_counts"])

    def test_exact_product_action_ratio(self) -> None:
        self.assertAlmostEqual(3.5115420129270545, self.result["exposures_per_action"])
        self.assertAlmostEqual(10.534626038781163, self.result["products_per_action"])

    def test_exact_cohort_footprint(self) -> None:
        self.assertEqual(1625281365343, self.result["total_bytes"])
        self.assertEqual({"data_source": 150708337459, "data_raw": 370489806656, "data_processed": 1104083221228}, self.result["collection_bytes"])

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_claim_ceiling_preserves_scope(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("verified complete six-pattern nikon cohort", "independent scientific observations", "unadmitted records", "archive quality", "global novelty or priority"):
            self.assertIn(phrase, ceiling)

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
