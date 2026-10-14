from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage2a_earthrise_coverage import verify_stage2a  # noqa: E402
from stage2b_fixed_camera_replication import verify_stage2b, verify_with_mutations  # noqa: E402


class Stage2BFixedCameraReplicationTests(unittest.TestCase):
    def test_earthset_is_one_verified_overlap_replication(self) -> None:
        result = verify_stage2b(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_SINGLE_ADMISSIBLE_REPLICATION", result["evidence_state"])
        self.assertEqual("SINGLE_ADMISSIBLE_REPLICATION", result["pattern"])
        self.assertEqual(1, result["admissible_replications"])
        self.assertEqual("OVERLAPS_EVENT", result["events"]["earthset"]["coverage_relation"])
        self.assertEqual(
            54.269803,
            result["events"]["earthset"]["minimum_guaranteed_overlap_seconds"],
        )

    def test_earthset_transition_is_interval_censored(self) -> None:
        result = verify_stage2b(ROOT)
        brackets = result["events"]["earthset"]["transition_brackets"]
        self.assertEqual(
            {
                "lower_exclusive_utc": "2026-04-06T22:41:44Z",
                "upper_inclusive_utc": "2026-04-06T22:42:14Z",
            },
            brackets["occultation_onset"],
        )
        self.assertEqual(
            {
                "lower_exclusive_utc": "2026-04-06T22:43:14Z",
                "upper_inclusive_utc": "2026-04-06T22:43:44Z",
            },
            brackets["complete_disappearance"],
        )

    def test_sunset_and_sunrise_stop_without_rescue(self) -> None:
        result = verify_stage2b(ROOT)
        self.assertEqual("NOT_ADMISSIBLE_CAMERA_VIEW", result["events"]["sunset"]["status"])
        self.assertEqual(
            ["SUN_VISIBLE", "SUN_VISIBLE", "PARTIAL", "PARTIAL"],
            result["events"]["sunset"]["states"],
        )
        self.assertEqual("NOT_ADMISSIBLE_CAMERA_VIEW", result["events"]["sunrise"]["status"])
        self.assertEqual([], result["events"]["sunrise"]["frames"])

    def test_acquisition_is_hash_pinned_and_under_budget(self) -> None:
        result = verify_stage2b(ROOT)
        self.assertEqual(24, result["acquisition"]["accepted_files"])
        self.assertEqual(29181381, result["acquisition"]["accepted_bytes"])
        self.assertLess(
            result["acquisition"]["accepted_bytes"],
            result["acquisition"]["aggregate_max_bytes"],
        )
        self.assertEqual(0, result["acquisition"]["network_bytes_in_verification"])

    def test_all_stage2b_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))

    def test_stage2a_earthrise_remains_replayable(self) -> None:
        result = verify_stage2a(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("AFTER_EVENT_NO_OVERLAP", result["coverage_relation"])


if __name__ == "__main__":
    unittest.main()
