from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from artemis_testbed import run_testbed  # noqa: E402
from stage1_boundary_equivalence import verify_stage1  # noqa: E402
from stage2a_earthrise_coverage import verify_stage2a, verify_with_mutations  # noqa: E402


class Stage2AEarthriseCoverageTests(unittest.TestCase):
    def test_fixed_camera_oracle_verifies_no_overlap(self) -> None:
        result = verify_stage2a(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_NO_OVERLAP", result["evidence_state"])
        self.assertEqual("AFTER_EVENT_NO_OVERLAP", result["coverage_relation"])
        self.assertEqual(136.0, result["minimum_separation_seconds"])

    def test_contact_and_clearance_are_interval_censored(self) -> None:
        result = verify_stage2a(ROOT)
        self.assertEqual(
            {
                "lower_exclusive_utc": "2026-04-06T23:21:14Z",
                "upper_inclusive_utc": "2026-04-06T23:21:44Z",
            },
            result["event_brackets"]["first_visible_contact"],
        )
        self.assertEqual(
            {
                "lower_exclusive_utc": "2026-04-06T23:22:44Z",
                "upper_inclusive_utc": "2026-04-06T23:23:14Z",
            },
            result["event_brackets"]["full_clearance"],
        )

    def test_pds_labels_supply_complete_thirty_second_cadence(self) -> None:
        result = verify_stage2a(ROOT)
        cadence = next(item for item in result["checks"] if item["id"] == "thirty_second_cadence")
        self.assertTrue(cadence["pass"])
        self.assertEqual([30.0, 30.0, 30.0, 30.0, 30.0], cadence["observed_seconds"])

    def test_all_stage2a_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))

    def test_earlier_stages_remain_replayable(self) -> None:
        self.assertTrue(run_testbed(ROOT)["pass"])
        self.assertTrue(verify_stage1(ROOT)["pass"])


if __name__ == "__main__":
    unittest.main()
