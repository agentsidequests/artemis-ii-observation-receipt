from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage8a_reflectance_canary import verify_stage8a  # noqa: E402


class Stage8AReflectanceCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage8a(ROOT)

    def test_frozen_canary_is_a_verified_negative(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertFalse(self.result["signal_pass"])
        self.assertFalse(self.result["partial_pass"])
        self.assertEqual("NO_REFLECTANCE_CONCORDANCE", self.result["evidence_state"])
        self.assertEqual("STOP_GLUSHKO_OHM_REFLECTANCE_LANE", self.result["disposition"])

    def test_primary_sectors_do_not_clear_local_background(self) -> None:
        targets = self.result["primary"]["targets"]
        self.assertAlmostEqual(-0.020140798566795542, targets["glushko"]["local_contrast"], places=12)
        self.assertAlmostEqual(-0.0010588896662523692, targets["ohm"]["local_contrast"], places=12)
        self.assertIsNone(self.result["primary"]["similarity_ratio"])
        self.assertFalse(self.result["primary"]["glushko_greater_than_ohm"])

    def test_all_nine_robustness_cells_reject_the_full_claim(self) -> None:
        self.assertEqual(9, self.result["robustness_cells"])
        self.assertEqual(0, self.result["robustness_contrast_similarity_count"])
        self.assertEqual(0, self.result["robustness_direction_count"])

    def test_source_is_hash_pinned_bounded_and_replayed_offline(self) -> None:
        self.assertEqual(21847168, self.result["accepted_science_network_bytes"])
        self.assertEqual(66162790, self.result["complete_testbed_network_bytes"])
        self.assertEqual(0, self.result["network_bytes_in_verification"])
        by_id = {item["id"]: item for item in self.result["checks"]}
        self.assertTrue(by_id["source_manifest_identity"]["pass"])
        self.assertTrue(by_id["science_label_contract"]["pass"])

    def test_source_hash_leakage_mutation_is_rejected(self) -> None:
        mutated = verify_stage8a(ROOT, "tamper_source_manifest_hash")
        self.assertFalse(mutated["pass"])
        self.assertEqual("INDETERMINATE_SOURCE_OR_GEOMETRY", mutated["evidence_state"])

    def test_written_result_is_strict_json(self) -> None:
        path = ROOT / "results" / "stage8a-verification.json"
        parsed = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: self.fail(value))
        self.assertIsNone(parsed["primary"]["similarity_ratio"])

    def test_claim_ceiling_and_stop_logic_are_visible(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        self.assertIn("would not reconstruct", ceiling)
        self.assertIn("establish causal perception", ceiling)
        self.assertIn("scientific novelty", ceiling)
        self.assertIn("publishable scientific result", ceiling)
        self.assertIn("stop the glushko-ohm reflectance lane", self.result["next_step_logic"]["if_fail"].lower())


if __name__ == "__main__":
    unittest.main()
