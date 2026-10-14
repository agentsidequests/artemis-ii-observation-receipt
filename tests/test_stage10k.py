from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10k_four_unit_contract import verify_stage10k, verify_with_mutations  # noqa: E402


class Stage10KFourUnitContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10k(ROOT)

    def test_contract_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_FOUR_UNIT_ANALYSIS_CONTRACT", self.result["evidence_state"])

    def test_four_units_remain_distinct(self) -> None:
        units = self.result["units"]
        self.assertEqual((11591, 814.51), (units["source_files"], units["source_volume_gb"]))
        self.assertEqual((32133, 2.52679007551), (units["archive_products"], units["archive_decimal_tb"]))
        self.assertEqual(10329, units["nikon_capture_identities"])
        self.assertEqual((2166, 7606), (units["complete_six_pattern_actions"], units["exposures_in_complete_actions"]))

    def test_residuals_stay_unresolved(self) -> None:
        self.assertEqual({"documented_pending_iphone": 68, "unexplained_nikon_residuals": 10, "unexplained_cab_cam_2_residuals": 28}, self.result["provenance"])

    def test_retrieval_consequence_replays(self) -> None:
        retrieval = self.result["retrieval"]
        self.assertEqual((69, 207), (retrieval["fractured_capture_identities"], retrieval["fractured_products"]))
        self.assertEqual((14, 84, 0, 14), (retrieval["stress_case_actions"], retrieval["stress_case_filtered_products"], retrieval["stress_case_complete_actions"], retrieval["stress_case_companion_exposures_needed"]))

    def test_supersessions_and_scope_replay(self) -> None:
        self.assertTrue(self.result["stage10d_hypothesis_superseded"])
        self.assertTrue(self.result["stage10e_generalization_superseded"])
        self.assertEqual((25, 4, 13), (self.result["activity_fractures"], self.result["cross_day_fractures"], self.result["local_repeated_signature_actions"]))

    def test_claim_ceiling_is_explicit(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("snapshot date", "exhaustive", "missing or defective", "local stage 10f mechanism", "global novelty or priority"):
            self.assertIn(phrase, ceiling)

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
