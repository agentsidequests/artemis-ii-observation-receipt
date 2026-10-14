from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10x_task_readiness import verify_stage10x, verify_with_mutations  # noqa: E402


class Stage10XTaskReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10x(ROOT)

    def test_result_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_TASK_READINESS_SEPARATION", self.result["evidence_state"])

    def test_readiness_is_task_conditioned(self) -> None:
        states = {row["task"]: row["status"] for row in self.result["task_matrix"]}
        self.assertEqual("SUPPORTED_NOW", states["archive_retrieval_and_footprint_audit"])
        self.assertEqual("CONDITIONALLY_SUPPORTABLE", states["within_event_temporal_or_hdr_modeling"])
        self.assertEqual("NOT_INTERNALLY_IDENTIFIABLE", states["new_sunset_event_generalization"])

    def test_four_independent_boundary_families_remain_visible(self) -> None:
        self.assertEqual(
            {"unit_and_event", "label_population", "acquisition_context", "measurement_level"},
            set(self.result["blocker_families"]),
        )

    def test_no_pixels_were_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
