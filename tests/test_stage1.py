from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from artemis_testbed import run_testbed  # noqa: E402
from stage1_boundary_equivalence import verify_stage1, verify_with_mutations  # noqa: E402


class Stage1BoundaryEquivalenceTests(unittest.TestCase):
    def test_verified_result_stops_original_timing_lane(self) -> None:
        result = verify_stage1(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("STOPPED", result["stage_gate"])
        self.assertEqual({"PASS": 0, "FAIL": 2, "AMBIGUOUS": 5}, result["boundary_summary"])

    def test_earthrise_duration_is_decisive_hard_negative(self) -> None:
        result = verify_stage1(ROOT)
        earthrise = next(item for item in result["intervals"] if item["target"] == "Earthrise")
        self.assertTrue(earthrise["duration_hard_negative"])
        self.assertEqual("FAIL", earthrise["verdict"])
        self.assertAlmostEqual(4.147844, earthrise["plan_duration_seconds"], places=6)
        self.assertAlmostEqual(128.213, earthrise["observed_duration_seconds"], places=3)

    def test_duration_similarity_does_not_promote_sunset(self) -> None:
        result = verify_stage1(ROOT, "promote_sunset_from_duration_only")
        self.assertFalse(result["pass"])
        self.assertTrue(any("without an equivalence source" in error for error in result["errors"]))

    def test_all_semantic_mutations_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))

    def test_stage0_remains_replayable(self) -> None:
        result = run_testbed(ROOT)
        self.assertTrue(result["pass"], result["errors"])


if __name__ == "__main__":
    unittest.main()
