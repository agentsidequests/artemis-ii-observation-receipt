from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage8a_reflectance_canary import (  # noqa: E402
    angular_difference_deg,
    initial_bearing_deg,
    verify_formation,
    verify_formation_with_mutations,
)


class Stage8AFormationTests(unittest.TestCase):
    def test_pixel_blind_formation_admits_only_bounded_wac_acquisition(self) -> None:
        result = verify_formation(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("FORMED_NO_VALUE_ACCESS", result["evidence_state"])
        self.assertEqual("ADMIT_BOUNDED_WAC_ACQUISITION", result["disposition"])
        self.assertEqual(0, result["wac_value_bytes_accessed"])

    def test_named_axis_bearings_are_derived_from_frozen_coordinates(self) -> None:
        result = verify_formation(ROOT)
        self.assertAlmostEqual(51.663512, result["named_axis_bearings_deg"]["glushko"], places=5)
        self.assertAlmostEqual(70.163725, result["named_axis_bearings_deg"]["ohm"], places=5)

    def test_bearing_and_wrap_helpers_have_known_geometry(self) -> None:
        self.assertAlmostEqual(0.0, initial_bearing_deg(0.0, 0.0, 10.0, 0.0))
        self.assertAlmostEqual(90.0, initial_bearing_deg(0.0, 0.0, 0.0, 10.0))
        self.assertAlmostEqual(-2.0, angular_difference_deg(359.0, 1.0))

    def test_claim_ceiling_and_exact_products_are_frozen(self) -> None:
        result = verify_formation(ROOT)
        by_id = {item["id"]: item for item in result["checks"]}
        self.assertTrue(by_id["exact_566nm_science_products"]["pass"])
        self.assertTrue(by_id["claim_ceiling"]["pass"])
        self.assertTrue(by_id["symmetric_pixel_blind_geometry"]["pass"])

    def test_every_formation_hard_negative_is_rejected(self) -> None:
        result = verify_formation_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))


if __name__ == "__main__":
    unittest.main()
