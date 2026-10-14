"""Bounded linkage, oracle replay and adversarial ordering cases."""

import copy
import csv
import io
import json
import subprocess
import sys
import unittest

from src.camera_identity_alias_census import FIELDS, OWNER, ROOT, groups, key, normalize, normalize_hit, one, replay, sort_tie_profile, verify_bytes
from stage10c_camera_action_integrity import detect_complete_brackets


def hit(number, shutter='100', file_number='0100', utc='2026-04-07T00:00:00.000Z', bracket='0'):
    filename = f'art002e{number:06d}_nkz9019_raw_v01.tif'
    values = {'serial':'3920019','file_number':file_number,'shutter_count':shutter,'iso':'1600','focal_length':'35.0',
              'shooting_mode':'Continuous, Exposure Bracketing','auto_bracket_order':'0,-,+','bracket_value':bracket,
              'flight_day':'6','activity_id':'fixture','target_id':'Moon'}
    return {'_id':'atlas:pds4:artemis2:artemis2:/artemis2_crew_camera/data_raw/fd06/'+filename,
            '_source':{'bundle_id':'artemis2_crew_camera','collection_id':'data_raw',
                       'gather':{'pds_archive':{'file_name':filename},'time':{'start_time':utc}},
                       'pds4_label':{FIELDS[field]:[value] for field,value in values.items()}}}


class CameraIdentityAliasCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((OWNER / 'contract.json').read_text(encoding='utf-8'))
        cls.result = json.loads((OWNER / 'result.json').read_text(encoding='utf-8'))
        cls.strict = cls.contract['strict_fields']
        cls.core = cls.contract['core_fields']
        cls.action_contract = json.loads((ROOT / 'spec/stage10c.json').read_text(encoding='utf-8'))['complete_bracket_contract']

    def test_whole_result_replays_frozen_sources_and_existing_oracle(self):
        self.assertEqual(self.result, replay())

    def test_source_hash_mutation_is_rejected_without_modifying_source(self):
        source = dict(self.contract['inputs'][0])
        source['sha256'] = '0'*64
        with self.assertRaises(ValueError):
            verify_bytes(source)

    def test_complete_population_and_scope_are_preserved(self):
        self.assertEqual(10329, self.result['raw_records'])
        self.assertEqual(10329, self.result['unique_raw_product_ids'])
        self.assertEqual(10329, self.result['strict_key_eligible_records'])
        self.assertEqual({'products':22818,'capture_keys':7606,'actions':2166}, self.result['original_manifest'])

    def test_twenty_four_distinct_id_pairs_are_not_counted_twice(self):
        self.assertEqual(24, self.result['strict_candidate_groups'])
        self.assertEqual({'2':24}, self.result['strict_candidate_group_sizes'])
        self.assertEqual(48, self.result['strict_candidate_records'])
        self.assertEqual({'0':23,'1':1}, self.result['candidate_groups_by_number_of_counted_capture_keys'])

    def test_known_public_image_candidate_and_adjacent_negative_replay(self):
        public_pair = next(w for w in self.result['witnesses'] if any(r['capture_key']=='art002e009301' for r in w['records']))
        self.assertEqual({'art002e009301','art002e015991'}, {r['capture_key'] for r in public_pair['records']})
        self.assertNotIn('art002e015990', {r['capture_key'] for w in self.result['witnesses'] for r in w['records']})

    def test_side_metadata_conflicts_remain_visible(self):
        self.assertEqual(21, self.result['candidate_groups_with_side_metadata_conflicts'])
        for witness in self.result['witnesses'][:21]:
            self.assertEqual(['target_id'], witness['side_metadata_conflicts'])
            self.assertEqual([['Moon'],None], [r['side_metadata']['target_id'] for r in witness['records']])

    def test_null_empty_multiple_and_nonstring_fields_do_not_match(self):
        for invalid in [None,[],['','1'],[''],[None],[True],[1600]]:
            self.assertIsNone(one(invalid))
        a,b = normalize(hit(999101)),normalize(hit(999102))
        a['iso'] = b['iso'] = None
        self.assertEqual([], groups([a,b],self.strict))

    def test_core_match_is_not_promoted_when_optical_fields_disagree(self):
        a,b = normalize(hit(999101)),normalize(hit(999102))
        b['iso'] = '800'
        self.assertEqual(1,len(groups([a,b],self.core)))
        self.assertEqual([],groups([a,b],self.strict))

    def test_adjacent_shutter_and_file_numbers_are_a_negative(self):
        a = normalize(hit(999101))
        b = normalize(hit(999102,shutter='101',file_number='0101',utc='2026-04-07T00:00:00.100Z',bracket='-2'))
        self.assertNotEqual(key(a,self.core),key(b,self.core))

    def test_leading_zeros_are_not_silently_normalized(self):
        a,b = normalize(hit(999101)),normalize(hit(999102))
        b['file_number']='100'
        self.assertEqual([],groups([a,b],self.strict))

    def test_semantic_utc_is_separate_and_requires_offset(self):
        a,b = normalize(hit(999101)),normalize(hit(999102))
        b['utc']='2026-04-07T00:00:00Z'
        self.assertEqual([],groups([a,b],self.strict))
        self.assertEqual(1,len(groups([a,b],self.strict,semantic_utc=True)))
        b['utc']='2026-04-07T00:00:00'
        self.assertIsNone(key(b,self.strict,semantic_utc=True))

    def test_grouping_not_source_diagnostics_is_permutation_invariant(self):
        records=[normalize(hit(999102)),normalize(hit(999101)),normalize(hit(999103,shutter='101'))]
        self.assertEqual(groups(records,self.strict),groups(list(reversed(records)),self.strict))

    def test_wrong_product_collection_is_rejected(self):
        changed=hit(999101)
        changed['_source']['collection_id']='data_processed'
        with self.assertRaises(ValueError):
            normalize(changed)

    def test_filename_identifier_mismatch_is_rejected(self):
        changed=hit(999101)
        changed['_source']['gather']['pds_archive']['file_name']='art002e999999_nkz9019_raw_v01.tif'
        with self.assertRaises(ValueError):
            normalize(changed)

    def test_synthetic_duplicate_key_can_block_a_sequence_without_physical_claim(self):
        first=hit(999101)
        middle=hit(999102,shutter='101',file_number='0101',utc='2026-04-07T00:00:00.100Z',bracket='-2')
        last=hit(999103,shutter='102',file_number='0102',utc='2026-04-07T00:00:00.200Z',bracket='+2')
        middle_alias=copy.deepcopy(middle)
        middle_alias['_id']=middle_alias['_id'].replace('999102','999104')
        middle_alias['_source']['gather']['pds_archive']['file_name']=middle_alias['_source']['gather']['pds_archive']['file_name'].replace('999102','999104')
        baseline=[normalize_hit(item) for item in [first,middle,last]]
        repeated=[normalize_hit(item) for item in [first,middle,middle_alias,last]]
        self.assertEqual(1,len(detect_complete_brackets(baseline,self.action_contract)))
        self.assertEqual(0,len(detect_complete_brackets(repeated,self.action_contract)))

    def test_synthetic_sort_tie_order_changes_admission(self):
        first=hit(999101)
        middle=hit(999102,shutter='101',file_number='0101',utc='2026-04-07T00:00:00.100Z',bracket='-2')
        last=hit(999103,shutter='102',file_number='0102',utc='2026-04-07T00:00:00.200Z',bracket='+2')
        distraction=hit(999104,file_number='0999',utc='2026-04-07T00:00:00.700Z',bracket='-1')
        legacy=[normalize_hit(item) for item in [distraction,first,middle,last]]
        self.assertEqual(1,len(detect_complete_brackets(legacy,self.action_contract)))
        self.assertEqual(0,len(detect_complete_brackets(list(reversed(legacy)),self.action_contract)))
        distraction['_source']['pds4_label'][FIELDS['shutter_count']]=['99']
        negative=[normalize_hit(item) for item in [distraction,first,middle,last]]
        self.assertEqual(1,len(detect_complete_brackets(negative,self.action_contract)))
        self.assertEqual(1,len(detect_complete_brackets(list(reversed(negative)),self.action_contract)))

    def test_actual_unmodified_action_finder_is_not_order_invariant(self):
        diagnostic=self.result['conditional_algorithm_diagnostic']
        self.assertEqual((2166,7606),(diagnostic['baseline']['actions'],diagnostic['baseline']['admitted_raw_keys']))
        reverse=diagnostic['reversed_input_order']
        self.assertEqual((2134,7502),(reverse['summary']['actions'],reverse['summary']['admitted_raw_keys']))
        self.assertEqual(106,reverse['admitted_identifier_symmetric_difference'])

    def test_conditional_choices_are_not_corrected_action_counts(self):
        choices=self.result['conditional_algorithm_diagnostic']['conditional_representative_choices']
        for choice in choices.values():
            self.assertEqual((2174,7632),(choice['summary']['actions'],choice['summary']['admitted_raw_keys']))
            self.assertEqual(8,len(choice['added_camera_sequence_witnesses']))
        self.assertEqual(3439,choices['minimum_product_id']['admitted_target_fields']['nonblank_target_keys'])
        self.assertEqual(3418,choices['maximum_product_id']['admitted_target_fields']['nonblank_target_keys'])
        self.assertFalse(self.result['claim_limits']['counts_revised'])

    def test_sort_ties_are_not_all_strict_identity_candidates(self):
        profile=self.result['incumbent_sort_ties']
        self.assertEqual((101,222),(profile['tied_sort_keys'],profile['records_in_ties']))
        self.assertEqual(77,profile['ties_with_different_recorded_times'])
        self.assertEqual(77,profile['ties_with_different_file_numbers'])
        self.assertEqual(0,profile['ties_spanning_flight_days'])

    def test_crosswalk_has_every_candidate_and_preserves_status(self):
        with (OWNER / 'candidate-crosswalk.csv').open(encoding='utf-8',newline='') as stream:
            rows=list(csv.DictReader(stream))
        self.assertEqual(48,len(rows))
        self.assertEqual({r['product_id'] for w in self.result['witnesses'] for r in w['records']},{r['product_id'] for r in rows})
        self.assertTrue(all(r['status']=='METADATA_MATCH_CANDIDATE_NOT_PHYSICAL_IDENTITY' for r in rows))

    def test_actual_csv_entrypoint_replays_delivered_rows(self):
        completed=subprocess.run([sys.executable,'-B','-m','src.camera_identity_alias_census','--csv'],cwd=ROOT,check=True,text=True,capture_output=True)
        computed=list(csv.DictReader(io.StringIO(completed.stdout)))
        with (OWNER / 'candidate-crosswalk.csv').open(encoding='utf-8',newline='') as stream:
            self.assertEqual(computed,list(csv.DictReader(stream)))

    def test_claim_and_effect_limits_remain_false_or_zero(self):
        self.assertTrue(all(value is False for value in self.result['claim_limits'].values()))
        self.assertEqual({'network_requests':0,'image_payload_bytes':0,'outreach':False,'publication':False,'remote_push':False},self.result['effects'])


if __name__=='__main__':
    unittest.main()
