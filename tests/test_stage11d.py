from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11d_sunset_context_extension import verify_stage11d, verify_with_mutations  # noqa: E402


class Stage11DSunsetContextExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11d(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_SUNSET_PLAN_CONTEXT_EXTENSION", self.result["evidence_state"])

    def test_planned_block_remains_exact(self) -> None:
        segment = self.result["segments"]["scheduled_window"]
        self.assertEqual((169, 845, 2535, 200901668231),
                         (segment["actions"], segment["exposures"], segment["products"], segment["archive_size_bytes"]))

    def test_connected_context_is_larger_without_becoming_an_event_oracle(self) -> None:
        segment = self.result["segments"]["conservative_connected_context"]
        self.assertEqual((286, 1430, 4290, 370325578092),
                         (segment["actions"], segment["exposures"], segment["products"], segment["archive_size_bytes"]))
        self.assertAlmostEqual(1.6923076923076923, self.result["measures"]["connected_context_to_scheduled_product_ratio"])
        self.assertEqual("KEEP_ONE_PLANNED_EVENT_REPLACE_EXACT_REALIZED_COHORT_WITH_CONTEXT_RANGE", self.result["disposition"])

    def test_context_extends_on_both_sides_of_plan(self) -> None:
        self.assertEqual(99, self.result["segments"]["sun_gone_to_plan_start"]["actions"])
        self.assertEqual(18, self.result["segments"]["plan_end_to_spoken_continuation"]["actions"])
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
