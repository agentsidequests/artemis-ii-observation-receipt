from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11t_opportunity_concentration import (  # noqa: E402
    concentration_equivalent,
    replication_debt,
    verify_with_mutations,
)


class Stage11TOpportunityConcentrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_with_mutations(ROOT)

    def test_stage_verifies_and_hard_negatives_fail(self) -> None:
        self.assertTrue(self.result["pass"], self.result["checks"])
        self.assertEqual(
            "VERIFIED_SCHEDULED_OPPORTUNITY_CONCENTRATION",
            self.result["evidence_state"],
        )
        self.assertTrue(self.result["hard_negatives_pass"])

    def test_concentration_identity(self) -> None:
        self.assertAlmostEqual(3.0, concentration_equivalent([1.0, 1.0, 1.0]))
        self.assertLess(concentration_equivalent([8.0, 1.0, 1.0]), 2.0)

    def test_replication_debt_identity(self) -> None:
        self.assertEqual(3, replication_debt({"a": 1, "b": 2, "c": 4}, 3))

    def test_unit_weighting_increases_concentration(self) -> None:
        raw = self.result["metrics"]["raw_concentration_equivalent_windows"]
        self.assertGreater(raw["actions"], raw["products"])
        self.assertGreater(raw["products"], raw["archive_size_bytes"])

    def test_fractional_allocations_conserve_unique_action_totals(self) -> None:
        conservation = self.result["metrics"]["fractional_conservation"]
        for unit, item in conservation.items():
            self.assertTrue(item["window_match"], unit)
            self.assertTrue(item["collapsed_match"], unit)

    def test_claim_ceiling_rejects_independence_and_semantic_equivalence(self) -> None:
        ceiling = self.result["claim_ceiling"].casefold()
        for phrase in (
            "effective sample size",
            "independent realized event",
            "scientific comparability",
            "mission reflight",
            "archive quality",
            "model performance",
        ):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_and_no_em_dash(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes_opened"])
        for relative in (
            "spec/stage11t.json",
            "src/stage11t_opportunity_concentration.py",
            "tests/test_stage11t.py",
        ):
            self.assertNotIn(chr(0x2014), (ROOT / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
