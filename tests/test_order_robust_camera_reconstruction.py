"""Independent bounded enumeration and ambiguity/non-regression checks."""

import copy
import csv
import itertools
import json
import random
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from tests.test_camera_identity_alias_census import hit
from src.camera_identity_alias_census import ROOT, FIELDS
from src.order_robust_camera_reconstruction import OWNER, reconstruct, native_paths, assert_invariants, replay, artifacts, explicit_time
from stage10a_metadata_integrity import normalize_hit
from stage10c_camera_action_integrity import detect_complete_brackets

STRICT = ['serial', 'file_number', 'shutter_count', 'utc', 'iso', 'focal_length', 'shooting_mode', 'auto_bracket_order', 'bracket_value']
CONTRACT = json.loads((ROOT / 'spec/stage10c.json').read_text(encoding='utf-8'))['complete_bracket_contract']
CONTRACT['allowed_bracket_sequences'] = json.loads((ROOT / 'spec/stage10j.json').read_text(encoding='utf-8'))['expanded_patterns']


def trio():
    return [hit(999101), hit(999102, shutter='101', file_number='0101', utc='2026-04-07T00:00:00.100Z', bracket='-2'),
            hit(999103, shutter='102', file_number='0102', utc='2026-04-07T00:00:00.200Z', bracket='+2')]


def rename(item, old, new):
    changed = copy.deepcopy(item)
    changed['_id'] = changed['_id'].replace(old, new)
    changed['_source']['gather']['pds_archive']['file_name'] = changed['_source']['gather']['pds_archive']['file_name'].replace(old, new)
    return changed


def independent_exhaustive_paths(hits):
    """Small-case oracle reads raw fields and checks arithmetic, without production helpers."""
    paths = set()
    for pattern in CONTRACT['allowed_bracket_sequences']:
        for rows in itertools.permutations(hits, len(pattern)):
            labels = [row['_source']['pds4_label'] for row in rows]
            def values(field):
                return [label[FIELDS[field]][0] for label in labels]
            if values('bracket_value') != pattern:
                continue
            if any(value != '0,-,+' for value in values('auto_bracket_order')) or any('Exposure Bracketing' not in value for value in values('shooting_mode')):
                continue
            if any(len(set(values(field))) != 1 for field in ['serial', 'iso', 'focal_length']):
                continue
            if any([int(value) for value in values(field)] != list(range(int(values(field)[0]), int(values(field)[0]) + len(rows))) for field in ['file_number', 'shutter_count']):
                continue
            times = [datetime.fromisoformat(row['_source']['gather']['time']['start_time'].replace('Z', '+00:00')) for row in rows]
            if any(time.tzinfo is None for time in times) or any(a > b for a, b in zip(times, times[1:])) or not 0 <= (times[-1] - times[0]).total_seconds() <= 10:
                continue
            paths.add(tuple(row['_id'] for row in rows))
    return paths


class OrderRobustReconstructionTests(unittest.TestCase):
    def compute(self, hits, budget=None):
        return reconstruct(hits, STRICT, CONTRACT, budget)

    def test_simple_sequence_matches_independent_exhaustive_oracle(self):
        rows = trio()
        result = self.compute(rows)
        self.assertEqual(independent_exhaustive_paths(rows), native_paths(result))
        self.assertEqual({'UNAMBIGUOUS_METADATA_SEQUENCE': 1}, result['summary']['family_status_counts'])

    def test_tied_counter_distraction_never_changes_admission(self):
        rows = trio() + [hit(999104, file_number='0999', utc='2026-04-07T00:00:00.700Z', bracket='-1')]
        expected = self.compute(rows)
        self.assertEqual(1, expected['summary']['metadata_path_families'])
        for order in itertools.permutations(rows):
            self.assertEqual(expected, self.compute(list(order)))
        self.assertEqual(independent_exhaustive_paths(rows), native_paths(expected))

    def test_distinct_counter_negative_stays_stable(self):
        rows = trio() + [hit(999104, shutter='99', file_number='0999', bracket='-1')]
        self.assertEqual(self.compute(rows), self.compute(list(reversed(rows))))
        self.assertEqual(1, self.compute(rows)['summary']['native_complete_paths'])

    def test_matching_middle_is_retained_and_withheld_not_deduplicated(self):
        rows = trio()
        alias = rename(rows[1], '999102', '999104')
        alias['_source']['pds4_label'].pop(FIELDS['target_id'])
        rows.append(alias)
        result = self.compute(rows)
        self.assertEqual(independent_exhaustive_paths(rows), native_paths(result))
        self.assertEqual(2, result['summary']['native_complete_paths'])
        family = result['families'][0]
        self.assertEqual('IDENTITY_ALTERNATIVES_ABSTAIN', family['status'])
        self.assertEqual(2, len(family['slots'][1]['members']))
        self.assertEqual([['Moon'], None], [member['side_metadata']['target_id'] for member in family['slots'][1]['members']])
        for order in itertools.permutations(rows):
            self.assertEqual(result, self.compute(list(order)))

    def test_competing_middle_times_are_complete_but_not_admitted(self):
        rows = trio()
        alternative = rename(rows[1], '999102', '999104')
        alternative['_source']['gather']['time']['start_time'] = '2026-04-07T00:00:00.150Z'
        rows.append(alternative)
        result = self.compute(rows)
        self.assertEqual(independent_exhaustive_paths(rows), native_paths(result))
        self.assertEqual({'COMPETING_PATHS_ABSTAIN': 2}, result['summary']['family_status_counts'])
        self.assertEqual(1, len(result['competition_components']))
        self.assertEqual(2, len(result['competition_components'][0]['shared_native_ids']))
        self.assertEqual(result, self.compute(list(reversed(rows))))

    def test_omitted_competition_and_invented_admission_are_rejected(self):
        rows = trio()
        alternative = rename(rows[1], '999102', '999104')
        alternative['_source']['gather']['time']['start_time'] = '2026-04-07T00:00:00.150Z'
        result = self.compute(rows + [alternative])
        changed = copy.deepcopy(result)
        changed['competition_components'] = []
        with self.assertRaises(ValueError):
            assert_invariants(changed)
        changed = copy.deepcopy(result)
        changed['families'][0]['status'] = 'UNAMBIGUOUS_METADATA_SEQUENCE'
        with self.assertRaises(ValueError):
            assert_invariants(changed)

    def test_invented_component_is_rejected(self):
        result = self.compute(trio())
        changed = copy.deepcopy(result)
        changed['competition_components'] = [{'component_id':'fake', 'family_ids':[result['families'][0]['family_id']], 'shared_native_ids':[]}]
        with self.assertRaises(ValueError):
            assert_invariants(changed)

    def test_zero_counters_are_valid_without_the_legacy_sentinel(self):
        rows = [hit(999101, shutter='0', file_number='0000'),
                hit(999102, shutter='1', file_number='0001', utc='2026-04-07T00:00:00.100Z', bracket='-2'),
                hit(999103, shutter='2', file_number='0002', utc='2026-04-07T00:00:00.200Z', bracket='+2')]
        self.assertEqual(1, self.compute(rows)['summary']['native_complete_paths'])

    def test_settings_counter_bracket_and_order_mutations_stop_admission(self):
        for field, value in [('iso','800'), ('focal_length','50.0'), ('serial','3500015'), ('file_number','0201'),
                             ('shutter_count','201'), ('bracket_value','-1'), ('shooting_mode','Single'), ('auto_bracket_order','-,0,+')]:
            rows = trio()
            rows[1]['_source']['pds4_label'][FIELDS[field]] = [value]
            self.assertEqual(0, self.compute(rows)['summary']['native_complete_paths'], (field,value))

    def test_missing_multiple_values_are_not_equal_nulls(self):
        for value in [[],['400','800'],[None],[1600]]:
            rows = trio()
            rows[1]['_source']['pds4_label'][FIELDS['iso']] = value
            result = self.compute(rows)
            self.assertEqual(0, result['summary']['native_complete_paths'])
            self.assertEqual(1, result['summary']['unqualified_input_ids'])

    def test_naive_invalid_and_internally_reversed_times_are_rejected(self):
        for value in ['2026-04-07T00:00:00.100', 'not-time', '2026-04-06T23:59:59.999Z', '2026-04-07T00:00:11Z']:
            rows = trio()
            rows[1]['_source']['gather']['time']['start_time'] = value
            self.assertEqual(0, self.compute(rows)['summary']['native_complete_paths'])
        self.assertIsNone(explicit_time('2026-04-07T00:00:00'))

    def test_ten_second_span_boundary_and_outside_are_explicit(self):
        rows = trio()
        rows[2]['_source']['gather']['time']['start_time'] = '2026-04-07T00:00:10Z'
        self.assertEqual(1, self.compute(rows)['summary']['native_complete_paths'])
        rows[2]['_source']['gather']['time']['start_time'] = '2026-04-07T00:00:10.001Z'
        self.assertEqual(0, self.compute(rows)['summary']['native_complete_paths'])

    def test_duplicate_native_ids_are_rejected(self):
        rows = trio()
        with self.assertRaises(ValueError):
            self.compute(rows + [rows[1]])

    def test_complexity_limits_fail_closed_not_partial(self):
        rows = trio()
        rows.append(rename(rows[1], '999102', '999104'))
        with self.assertRaisesRegex(ValueError, 'Per-start'):
            self.compute(rows, {'maximum_native_paths':100, 'maximum_paths_per_start_pattern':1})
        with self.assertRaisesRegex(ValueError, 'Total'):
            self.compute(rows, {'maximum_native_paths':1, 'maximum_paths_per_start_pattern':100})
        with self.assertRaises(ValueError):
            self.compute(rows, {'maximum_native_paths':True, 'maximum_paths_per_start_pattern':100})
        with self.assertRaises(ValueError):
            self.compute(rows, {})

    def test_all_six_frozen_patterns_match_the_independent_oracle(self):
        for pattern in CONTRACT['allowed_bracket_sequences']:
            rows = [hit(999101+i, shutter=str(100+i), file_number=f'{100+i:04}',
                        utc=f'2026-04-07T00:00:00.{i:03}Z', bracket=value) for i,value in enumerate(pattern)]
            self.assertEqual(independent_exhaustive_paths(rows), native_paths(self.compute(rows)))
            self.assertEqual(1, self.compute(rows)['summary']['metadata_path_families'])

    def test_two_alternatives_in_every_slot_keep_all_eight_native_paths(self):
        rows = trio()
        rows += [rename(item, f'99910{i+1}', f'99910{i+4}') for i,item in enumerate(rows[:])]
        result = self.compute(rows)
        self.assertEqual(independent_exhaustive_paths(rows), native_paths(result))
        self.assertEqual(8, result['summary']['native_complete_paths'])
        self.assertEqual(1, result['summary']['metadata_path_families'])
        self.assertEqual('IDENTITY_ALTERNATIVES_ABSTAIN', result['families'][0]['status'])
        for order in itertools.permutations(rows):
            self.assertEqual(result, self.compute(list(order)))

    def test_transitive_competing_paths_have_one_complete_component(self):
        rows = [hit(999101, utc='2026-04-07T00:00:00.100Z'), hit(999104, utc='2026-04-07T00:00:00.250Z'),
                hit(999102, shutter='101',file_number='0101',utc='2026-04-07T00:00:00.150Z',bracket='-2'),
                hit(999105, shutter='101',file_number='0101',utc='2026-04-07T00:00:00.300Z',bracket='-2'),
                hit(999103, shutter='102',file_number='0102',utc='2026-04-07T00:00:00.200Z',bracket='+2'),
                hit(999106, shutter='102',file_number='0102',utc='2026-04-07T00:00:00.350Z',bracket='+2')]
        result = self.compute(rows)
        self.assertEqual(independent_exhaustive_paths(rows), native_paths(result))
        self.assertEqual({'COMPETING_PATHS_ABSTAIN':4}, result['summary']['family_status_counts'])
        self.assertEqual(1, len(result['competition_components']))
        self.assertEqual(4, len(result['competition_components'][0]['shared_native_ids']))
        changed = copy.deepcopy(result)
        changed['competition_components'][0]['family_ids'].pop()
        with self.assertRaises(ValueError):
            assert_invariants(changed)

    def test_nonmonotone_time_is_an_explicit_additional_gate_not_old_parity(self):
        rows = trio()
        rows[1]['_source']['gather']['time']['start_time'] = '2026-04-06T23:59:59.999Z'
        self.assertEqual(1, len(detect_complete_brackets([normalize_hit(row) for row in rows], CONTRACT)))
        self.assertEqual(0, self.compute(rows)['summary']['native_complete_paths'])

    def test_small_randomized_alternatives_match_independent_enumeration(self):
        for seed in range(32):
            chooser = random.Random(seed)
            rows = trio()
            extra = rename(rows[chooser.randrange(3)], '99910', '99920')
            if chooser.choice([True,False]):
                extra['_source']['gather']['time']['start_time'] = chooser.choice([
                    '2026-04-07T00:00:00.050Z','2026-04-07T00:00:00.150Z','2026-04-07T00:00:00.250Z'])
            if chooser.randrange(4) == 0:
                extra['_source']['pds4_label'][FIELDS['iso']] = ['800']
            rows.append(extra)
            chooser.shuffle(rows)
            self.assertEqual(independent_exhaustive_paths(rows), native_paths(self.compute(rows)), seed)

    def test_source_id_rename_does_not_choose_a_different_metadata_family(self):
        original = self.compute(trio())
        changed = self.compute([rename(row, '99910', '99920') for row in trio()])
        self.assertEqual(original['summary'], changed['summary'])
        self.assertEqual([family['family_id'] for family in original['families']], [family['family_id'] for family in changed['families']])

    def test_candidate_contract_cannot_promote_acceptance_or_external_effects(self):
        original = json.loads((OWNER / 'contract.json').read_text(encoding='utf-8'))
        for field in ['physical_identity','adopted_reconstruction','scientific_acceptance']:
            changed = copy.deepcopy(original)
            changed['limits'][field] = True
            with patch('src.order_robust_camera_reconstruction.checked_json', return_value=changed), self.assertRaises(ValueError):
                replay()
        changed = copy.deepcopy(original)
        changed['effects']['network_requests'] = 1
        with patch('src.order_robust_camera_reconstruction.checked_json', return_value=changed), self.assertRaises(ValueError):
            replay()

    def test_side_tag_changes_cannot_select_a_path(self):
        original = self.compute(trio())
        rows = trio()
        for row in rows:
            row['_source']['pds4_label'][FIELDS['target_id']] = ['Other']
            row['_source']['pds4_label'][FIELDS['activity_id']] = ['Different activity']
        changed = self.compute(rows)
        self.assertEqual(original['summary'], changed['summary'])
        self.assertEqual([family['family_id'] for family in original['families']], [family['family_id'] for family in changed['families']])

    def test_five_frame_path_matches_independent_oracle(self):
        rows = [hit(999101+i, shutter=str(100+i), file_number=f'{100+i:04}', utc=f'2026-04-07T00:00:00.{i:03}Z', bracket=value)
                for i,value in enumerate(['0','-6','-3','+3','+6'])]
        result = self.compute(rows)
        self.assertEqual(independent_exhaustive_paths(rows), native_paths(result))
        self.assertEqual(1, result['summary']['metadata_path_families'])

    def test_actual_result_replays_all_pinned_sources_and_orders(self):
        retained = json.loads((OWNER / 'result.json').read_text(encoding='utf-8'))
        self.assertEqual(retained, replay())
        self.assertEqual(8, len(retained['order_checks']))
        self.assertEqual({'IDENTITY_ALTERNATIVES_ABSTAIN':9,'UNAMBIGUOUS_METADATA_SEQUENCE':2165}, retained['summary']['family_status_counts'])
        self.assertEqual([], retained['baseline_comparison']['explicit_baseline_exclusions'])
        self.assertEqual(2166, sum(retained['baseline_comparison']['baseline_native_paths_by_candidate_status'].values()))

    def test_actual_cli_and_csv_membership_roundtrip(self):
        completed = subprocess.run([sys.executable,'-B','-m','src.order_robust_camera_reconstruction','--check'], cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertEqual(8, json.loads(completed.stdout)['order_checks'])
        result = json.loads((OWNER / 'result.json').read_text(encoding='utf-8'))
        with (OWNER / 'membership.csv').open(encoding='utf-8',newline='') as stream:
            rows = list(csv.DictReader(stream))
        expected = {(family['family_id'],str(position),member['product_id']) for family in result['families']
                    for position,slot in enumerate(family['slots']) for member in slot['members']}
        self.assertEqual(expected, {(row['family_id'],row['slot'],row['product_id']) for row in rows})
        self.assertEqual(7655, len(rows))

    def test_wrong_refresh_identity_or_changed_artifact_blocks_all_writes(self):
        with tempfile.TemporaryDirectory() as directory, patch('src.order_robust_camera_reconstruction.OWNER', Path(directory)), patch('src.order_robust_camera_reconstruction.replay', return_value={'families':[], 'summary':{}, 'baseline_comparison':{}, 'order_checks':[], 'status':'fixture'}):
            root = Path(directory)
            (root / 'result.json').write_bytes(b'owner edit')
            (root / 'membership.csv').write_bytes(b'owner csv')
            with self.assertRaises(ValueError):
                artifacts('--write')
            with self.assertRaises(ValueError):
                artifacts('--refresh', {'result.json':'0'*64, 'membership.csv':'0'*64})
            self.assertEqual(b'owner edit', (root / 'result.json').read_bytes())
            self.assertEqual(b'owner csv', (root / 'membership.csv').read_bytes())

    def test_claim_flags_do_not_attest_physical_adoption(self):
        result = json.loads((OWNER / 'result.json').read_text(encoding='utf-8'))
        self.assertTrue(all(value is False for value in result['claim_limits'].values()))
        self.assertEqual('ORDER_INVARIANT_METADATA_CANDIDATE_NOT_ADOPTED', result['status'])


if __name__ == '__main__':
    unittest.main()
