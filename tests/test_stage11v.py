from __future__ import annotations

import sys
import csv
import hashlib
import io
import itertools
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11v_target_completion_bounds import (  # noqa: E402
    completion_bounds, completion_budget, main, sunset_completion_witness, verify_with_mutations,
)


class Stage11VTargetCompletionBoundsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_with_mutations(ROOT)

    def test_stage_verifies_and_hard_negatives_fail(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_TARGET_FIELD_COMPLETION_BOUNDS", self.result["evidence_state"])
        self.assertTrue(self.result["hard_negatives_pass"])

    def test_cohort_partition_is_exact(self) -> None:
        metrics = self.result["metrics"]
        self.assertEqual((7606, 3413, 4193, 23), (
            metrics["source_exposures"],
            metrics["nonblank_target_fields"],
            metrics["blank_target_fields"],
            metrics["observed_target_field_values"],
        ))

    def test_sunset_completion_bound_is_exact(self) -> None:
        sunset = self.result["metrics"]["sunset"]
        self.assertEqual((1553, 1553, 5746), (
            sunset["observed_count"], sunset["lower_count"], sunset["upper_count"],
        ))
        self.assertAlmostEqual(0.455024904775857, sunset["observed_share_among_nonblank"])
        self.assertAlmostEqual(0.2041809098080463, sunset["lower_share_full_cohort"])
        self.assertAlmostEqual(0.7554562187746516, sunset["upper_share_full_cohort"])

    def test_every_marginal_width_equals_blank_share(self) -> None:
        metrics = self.result["metrics"]
        for item in metrics["bounds_by_target_field_value"].values():
            self.assertAlmostEqual(metrics["blank_share"], item["bound_width"])

    def test_extreme_assignments_attain_the_bounds(self) -> None:
        metrics = self.result["metrics"]
        extremes = metrics["extreme_assignments"]
        self.assertEqual(1553, extremes["no_blank_fields_assigned_to_sunset"]["sunset_count"])
        self.assertEqual(5746, extremes["all_blank_fields_assigned_to_sunset"]["sunset_count"])

    def test_binary_completion_bounds_match_exhaustive_small_worlds(self) -> None:
        for total in range(1, 8):
            for observed in range(total + 1):
                for blank in range(total - observed + 1):
                    worlds = [(observed + sum(bits)) / total for bits in itertools.product((0, 1), repeat=blank)]
                    self.assertEqual((min(worlds), max(worlds)), completion_bounds(total, observed, blank))

    def test_invalid_partitions_are_rejected(self) -> None:
        for counts in ((0, 0, 0), (2, -1, 1), (2, 1, -1), (2, 1, 2), (2.0, 1, 1), (True, 0, 0)):
            with self.assertRaises(ValueError):
                completion_bounds(*counts)

    def test_actual_row_level_witness_preserves_recorded_fields(self) -> None:
        with (ROOT / 'results/stage10o-product-relationship-manifest.csv').open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        text, summary = sunset_completion_witness(rows)
        output = list(csv.DictReader(io.StringIO(text)))
        source = {row['capture_identity']: row for row in rows if row['collection_id'] == 'data_source'}
        self.assertEqual(7606, len(output))
        self.assertEqual(set(source), {row['source_capture_id'] for row in output})
        for row in output:
            value = source[row['source_capture_id']]['target_id']
            self.assertEqual(value, row['observed_target_field'])
            self.assertEqual(str(int(not value)), row['field_is_blank'])
            self.assertEqual(str(int(value == 'Sunset')), row['lower_possible_sunset_membership'])
            self.assertEqual(str(int(not value or value == 'Sunset')), row['upper_possible_sunset_membership'])
        self.assertEqual(1553, sum(int(row['lower_possible_sunset_membership']) for row in output))
        self.assertEqual(5746, sum(int(row['upper_possible_sunset_membership']) for row in output))
        self.assertEqual(hashlib.sha256(text.encode('utf-8')).hexdigest(), summary['csv_sha256'])
        self.assertEqual(summary, self.result['metrics']['completion_witness'])

    def test_duplicate_capture_witness_is_rejected(self) -> None:
        row = {'collection_id': 'data_source', 'capture_identity': 'same', 'target_id': 'Sunset'}
        with self.assertRaisesRegex(ValueError, 'unique source capture'):
            sunset_completion_witness([row, row.copy()])

    def test_strict_majority_tipping_is_exact(self) -> None:
        majority = self.result['metrics']['sunset_majority']
        self.assertEqual(2251, majority['additional_blank_memberships_needed'])
        self.assertEqual(7606 / 2, 1553 + 2250)
        self.assertGreater(1553 + 2251, 7606 / 2)

    def test_completion_budgets_are_sharp_guarantees_not_sample_sizes(self) -> None:
        for denominator, audit_count in ((10, 3433), (20, 3813), (100, 4117)):
            budget = completion_budget(7606, 4193, denominator)
            self.assertEqual(audit_count, budget['minimum_blank_fields_resolved'])
            self.assertLessEqual((4193 - audit_count) / 7606, 1 / denominator)
            self.assertGreater((4193 - (audit_count - 1)) / 7606, 1 / denominator)
        for denominator in (0, -1, 2.0):
            with self.assertRaises(ValueError):
                completion_budget(7606, 4193, denominator)

    def test_native_recount_agrees_without_importing_python_runner(self) -> None:
        native = json.loads((ROOT / 'evidence/stage11v/native-count-oracle.json').read_text(encoding='utf-8'))
        script = ROOT / 'evidence/stage11v/native-count-oracle.ps1'
        self.assertEqual(hashlib.sha256(script.read_bytes()).hexdigest().upper(), native['script_sha256'])
        self.assertEqual(self.result['source_identity']['sha256'].upper(), native['source_sha256'])
        self.assertEqual(7606, native['source_exposures'])
        self.assertEqual(4193, native['blank_target_fields'])
        self.assertEqual(2251, native['sunset_strict_majority_additional_count'])
        for name, item in self.result['metrics']['bounds_by_target_field_value'].items():
            self.assertEqual(item['observed_count'], native['bounds_by_field_value'][name]['observed'])
            self.assertEqual(item['upper_count'], native['bounds_by_field_value'][name]['upper_count'])
        for denominator, label in ((10, '10_percentage_points'), (20, '5_percentage_points'), (100, '1_percentage_point')):
            self.assertEqual(self.result['metrics']['deterministic_completion_budgets'][label]['minimum_blank_fields_resolved'], native['deterministic_completion_budgets'][f'1/{denominator}']['resolved'])

    def test_failed_verification_withholds_witness_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'withheld.csv'
            with patch('stage11v_target_completion_bounds.verify_stage11v', return_value={'pass': False}):
                with self.assertRaisesRegex(ValueError, 'withheld'):
                    main(['run', '--extremes-output', str(output)])
            self.assertFalse(output.exists())

    def test_changed_source_withholds_witness_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'withheld.csv'
            with patch('stage11v_target_completion_bounds.verify_stage11v', return_value={'pass': True}), patch('stage11v_target_completion_bounds.source_identity', return_value={'match': False}):
                with self.assertRaisesRegex(ValueError, 'identity changed'):
                    main(['run', '--extremes-output', str(output)])
            self.assertFalse(output.exists())

    def test_output_alias_is_rejected_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'same.csv'
            with self.assertRaisesRegex(ValueError, 'distinct'):
                main(['run', '--json-output', str(output), '--extremes-output', str(output)])
            self.assertFalse(output.exists())

    def test_output_cannot_overwrite_frozen_source_or_evidence(self) -> None:
        for relative in ('results/stage10o-product-relationship-manifest.csv', 'evidence/stage11v/native-count-oracle.json', 'spec/stage11v.json', 'src/stage11v_target_completion_bounds.py'):
            path = ROOT / relative
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, 'cannot overwrite'):
                main(['run', '--extremes-output', str(path)])
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_marginal_bounds_are_not_a_joint_distribution(self) -> None:
        ceiling = self.result["claim_ceiling"].casefold()
        self.assertIn("not a joint multiclass distribution", ceiling)
        self.assertIn("physical target prevalence", ceiling)
        self.assertIn("metadata field", ceiling)

    def test_all_intervals_hold_together_but_upper_endpoints_do_not(self) -> None:
        intervals = self.result['metrics']['bounds_by_target_field_value'].values()
        self.assertGreater(sum(item['upper_count'] for item in intervals), 7606)
        # Each completed single-valued field satisfies all component intervals.
        # Their cartesian upper corner is not a valid categorical distribution.
        observed = (1, 1, 0)
        total, blank = 5, 3
        bounds = [completion_bounds(total, count, blank) for count in observed]
        upper_vector = tuple(upper for _, upper in bounds)
        worlds = []
        for assignments in itertools.product(range(3), repeat=blank):
            shares = tuple((observed[index] + assignments.count(index)) / total for index in range(3))
            worlds.append(shares)
            self.assertAlmostEqual(1.0, sum(shares))
            for share, (lower, upper) in zip(shares, bounds):
                self.assertLessEqual(lower, share)
                self.assertLessEqual(share, upper)
        self.assertNotIn(upper_vector, worlds)

    def test_no_pixels_and_no_em_dash(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes_opened"])
        for relative in ("spec/stage11v.json", "src/stage11v_target_completion_bounds.py", "tests/test_stage11v.py"):
            self.assertNotIn(chr(0x2014), (ROOT / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
