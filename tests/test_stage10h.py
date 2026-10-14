from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10h_source_volume_reconciliation import verify_stage10h, verify_with_mutations  # noqa: E402


class Stage10HSourceVolumeReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10h(ROOT)

    def test_source_and_archive_ledgers_reconcile(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_SOURCE_VOLUME_VS_ARCHIVE_PRODUCT_FOOTPRINT", self.result["evidence_state"])

    def test_official_source_data_denominator(self) -> None:
        self.assertEqual(11591, self.result["source_file_count"])
        self.assertEqual(814.51, self.result["source_volume_gb"])

    def test_atlas_product_footprint_is_distinct(self) -> None:
        self.assertEqual(32133, self.result["atlas_product_count"])
        self.assertEqual(2526790075510, self.result["atlas_archive_bytes"])

    def test_video_conversion_bridges_unequal_sizes(self) -> None:
        self.assertEqual(22, self.result["source_video_files"])
        self.assertEqual(598.20, self.result["source_video_volume_gb"])
        self.assertEqual(22, self.result["atlas_video_products"])
        self.assertEqual(26268401779, self.result["atlas_video_bytes"])

    def test_prior_subtotal_hypothesis_is_superseded(self) -> None:
        self.assertAlmostEqual(833.887936412, self.result["prior_subtotal_gb"])
        self.assertTrue(self.result["prior_hypothesis_superseded"])

    def test_decision_use_names_three_ledgers(self) -> None:
        decision = self.result["decision_use"].lower()
        for phrase in ("received source-data scale", "retrieval and compute burden", "evidentiary sampling"):
            self.assertIn(phrase, decision)

    def test_claim_ceiling_preserves_accounting_boundaries(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("source data", "download burden", "independent observations", "loss of scientific content", "release completeness"):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
