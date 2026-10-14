from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10d_archive_units import verify_stage10d, verify_with_mutations  # noqa: E402


class Stage10DArchiveUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10d(ROOT)

    def test_multi_unit_archive_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual(
            "VERIFIED_MULTI_UNIT_ARCHIVE_WITH_HEADLINE_CONSISTENT_SUBTOTAL",
            self.result["evidence_state"],
        )

    def test_exact_mission_footprint(self) -> None:
        self.assertEqual(32133, self.result["mission_products"])
        self.assertEqual(2526790075510, self.result["mission_bytes"])
        self.assertEqual(
            {
                "artemis2_crew_camera": 30987,
                "artemis2_orion_camera": 1034,
                "artemis2_mission_audio": 112,
            },
            self.result["bundle_counts"],
        )

    def test_crew_collections_have_equal_product_counts_but_different_bytes(self) -> None:
        self.assertEqual(
            {"data_source": 10329, "data_raw": 10329, "data_processed": 10329},
            self.result["crew_collection_counts"],
        )
        self.assertEqual(1692902139098, self.result["crew_collection_bytes"]["data_processed"])

    def test_nonprocessed_subtotal_is_consistent_with_more_than_800gb(self) -> None:
        self.assertEqual(
            833887936412,
            self.result["mission_bytes_excluding_processed_crew_collection"],
        )
        self.assertGreater(self.result["nonprocessed_decimal_gigabytes"], 800)
        self.assertLess(self.result["nonprocessed_decimal_gigabytes"], 900)

    def test_forward_look_facet_multiplies_two_ids_into_six_products(self) -> None:
        self.assertEqual(6, self.result["forward_look_product_records"])
        self.assertEqual(
            ["art002e015902", "art002e015908"],
            self.result["forward_look_internal_ids"],
        )

    def test_complete_actions_multiply_ten_ids_into_thirty_products(self) -> None:
        self.assertEqual(30, self.result["forward_look_action_product_records"])
        self.assertEqual(10, self.result["forward_look_action_internal_ids"])
        self.assertEqual(
            {"data_source": 10, "data_raw": 10, "data_processed": 10},
            self.result["forward_look_action_collection_counts"],
        )
        self.assertEqual(
            {"24_Sunset": 24, "25_Discussion #6: Forward Look": 6},
            self.result["forward_look_action_activity_counts"],
        )

    def test_claim_ceiling_keeps_accounting_hypothesis_bounded(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in (
            "consistent with nasa's 'more than 800 gigabytes'",
            "call nasa's statement false",
            "claim nasa documented",
            "prove perfect representation parity",
            "live atlas snapshot indefinitely",
        ):
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
