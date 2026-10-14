from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from artemis_testbed import parse_utc, run_testbed, verify_with_mutations  # noqa: E402


class Stage0TestbedTests(unittest.TestCase):
    def test_corpus_identity_is_scoped_to_stage0_owned_sources(self) -> None:
        result = run_testbed(ROOT)
        identity = next(
            check for check in result["checks"] if check["id"] == "corpus_identity"
        )
        self.assertTrue(identity["pass"])
        self.assertEqual(27, identity["observed"]["file_count"])

    def test_baseline_recomputes_all_boundaries(self) -> None:
        result = run_testbed(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(7, len(result["events"]))
        self.assertTrue(all(event["delta_seconds"] < 0 for event in result["events"]))

    def test_all_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))

    def test_midnight_boundary_remains_utc(self) -> None:
        before_midnight = parse_utc("06 Apr 2026 23:59:59.000")
        after_midnight = parse_utc("07 Apr 2026 00:00:01.000")
        self.assertEqual(2.0, (after_midnight - before_midnight).total_seconds())
        self.assertEqual("UTC", before_midnight.tzname())

    def test_timestamp_shift_mutation_fails_expected_delta(self) -> None:
        result = run_testbed(ROOT, "shift_earthrise_plus_300")
        self.assertFalse(result["pass"])
        self.assertTrue(any("earthrise_first_contact delta" in error for error in result["errors"]))

    def test_missing_cue_stops_instead_of_guessing(self) -> None:
        result = run_testbed(ROOT, "cue_not_found")
        self.assertFalse(result["pass"])
        self.assertTrue(any("resolved 0 times" in error for error in result["errors"]))

    def test_wrong_plan_field_is_not_accepted(self) -> None:
        result = run_testbed(ROOT, "swap_earthset_plan_field")
        self.assertFalse(result["pass"])
        self.assertTrue(any("earthset_first_contact delta" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
