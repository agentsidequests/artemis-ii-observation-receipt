"""Deletion scope, independent recounts and non-favorable sensitivity predicates."""

import copy
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from src.camera_sequence_downstream_sensitivity import ROOT, OWNER, artifacts, close_tree, conclusion_flags, exclude_action, load_csv, load_json, metrics, replay, run, verify_pin


def fixture():
    manifest, assignments, memberships = [], [], []
    for action, keys in [('drop', ['a','b']), ('keep',['c','d'])]:
        for key in keys:
            for layer in ['data_source','data_raw','data_processed']:
                row = {'product_id':key+':'+layer, 'capture_identity':key, 'action_id':action,
                       'temporal_cluster_5s':'cluster-'+action, 'collection_id':layer, 'archive_size_bytes':'7',
                       'target_id':'Moon', 'activity_id':'synthetic'}
                manifest.append(row)
                assignments.append({field:row[field] for field in ['product_id','capture_identity','action_id','temporal_cluster_5s']} | {'product_key_partition':'test' if layer=='data_processed' else 'train'})
        memberships.append({'action_id':action,'plan_order':'1' if action=='drop' else '2'})
    return manifest,assignments,memberships


class DownstreamSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(OWNER / 'result.json')
        cls.contract = load_json(OWNER / 'contract.json')
        cls.manifest = load_csv(ROOT / 'results/stage10o-product-relationship-manifest.csv')
        cls.assignments = load_csv(ROOT / 'results/stage11l-split-assignments.csv')
        cls.memberships = load_csv(ROOT / 'results/stage10z-action-plan-membership.csv')
        cls.filtered = exclude_action(cls.manifest, cls.assignments, cls.memberships, cls.contract['action_id'], cls.contract['capture_keys'])

    def test_full_receipt_and_all_input_pins_replay(self):
        self.assertEqual(self.result, replay())
        for pin in self.contract['input_pins']:
            verify_pin(pin)

    def test_hash_mutation_is_rejected_without_source_change(self):
        pin = dict(self.contract['input_pins'][0])
        pin['sha256'] = '0'*64
        with self.assertRaises(ValueError):
            verify_pin(pin)

    def test_exact_full_action_withholding_and_unchanged_fields(self):
        retained, assignments, memberships, removed = self.filtered
        removed_ids = {row['product_id'] for row in removed}
        self.assertEqual((22818,22803,15),(len(self.manifest),len(retained),len(removed)))
        self.assertEqual(set(self.contract['capture_keys']),{row['capture_identity'] for row in removed})
        self.assertEqual({'data_source':5,'data_raw':5,'data_processed':5},dict(Counter(row['collection_id'] for row in removed)))
        self.assertEqual([row for row in self.manifest if row['product_id'] not in removed_ids],retained)
        self.assertEqual([row for row in self.assignments if row['product_id'] not in removed_ids],assignments)
        self.assertEqual([row for row in self.memberships if row['action_id'] != self.contract['action_id']],memberships)
        self.assertFalse(any('art002e009301' in row['product_id'] for row in retained))

    def test_filter_does_not_modify_original_tables(self):
        originals = fixture()
        before = copy.deepcopy(originals)
        exclude_action(*originals, 'drop',['a','b'])
        self.assertEqual(before, originals)

    def test_partial_or_repeated_representation_is_rejected(self):
        manifest, assignments, memberships = fixture()
        missing = manifest[0]['product_id']
        with self.assertRaises(ValueError):
            exclude_action([row for row in manifest if row['product_id']!=missing], [row for row in assignments if row['product_id']!=missing], memberships,'drop',['a','b'])
        repeated = dict(manifest[0],product_id='new-id')
        assigned = {field:repeated[field] for field in ['product_id','capture_identity','action_id','temporal_cluster_5s']} | {'product_key_partition':'train'}
        with self.assertRaises(ValueError):
            exclude_action(manifest+[repeated],assignments+[assigned],memberships,'drop',['a','b'])

    def test_wrong_action_or_capture_scope_is_rejected(self):
        data = fixture()
        for action,keys in [('wrong',['a','b']),('drop',['a']),('keep',['a','b'])]:
            with self.assertRaises(ValueError):
                exclude_action(*data,action,keys)

    def test_assignment_addition_duplicate_or_relationship_drift_is_rejected(self):
        manifest, assignments, memberships = fixture()
        for changed in [assignments+[assignments[0]],assignments[:-1],
                        [dict(row,action_id='other') if i==0 else row for i,row in enumerate(assignments)],
                        [dict(row,temporal_cluster_5s='other') if i==0 else row for i,row in enumerate(assignments)]]:
            with self.assertRaises(ValueError):
                exclude_action(manifest,changed,memberships,'drop',['a','b'])

    def test_independent_native_counts_and_byte_recount(self):
        retained, _, _, removed = self.filtered
        self.assertEqual(2165,len({row['action_id'] for row in retained}))
        self.assertEqual(7601,len({row['capture_identity'] for row in retained}))
        self.assertEqual(1971542570,sum(int(row['archive_size_bytes']) for row in removed))
        self.assertEqual({'data_source':151040000,'data_raw':457062880,'data_processed':1363439690},self.result['removal']['bytes_by_collection'])
        self.assertEqual(sum(int(row['archive_size_bytes']) for row in retained),self.result['conditional_withheld']['selection_weighting']['all_cohort']['archive_size_bytes'])

    def test_independent_train_test_and_relationship_bins(self):
        rows = self.filtered[1]
        train = [row for row in rows if row['product_key_partition']=='train']
        test = [row for row in rows if row['product_key_partition']=='test']
        captures,actions = {row['capture_identity'] for row in train},{row['action_id'] for row in train}
        bins = Counter('capture' if row['capture_identity'] in captures else 'action' if row['action_id'] in actions else 'isolated' for row in test)
        self.assertEqual(4509,len(test))
        self.assertEqual({'capture':4305,'action':204},dict(bins))
        self.assertEqual({'test':2,'train':13},self.result['removal']['product_key_partitions'])
        self.assertEqual(0,self.result['conditional_withheld']['relationship']['action_isolated_test_products'])

    def test_independent_field_selection_and_completion_counts(self):
        rows = [row for row in self.filtered[0] if row['collection_id']=='data_source']
        nonblank = sum(bool(row['target_id']) for row in rows)
        blank = len(rows)-nonblank
        sunset = sum(row['target_id']=='Sunset' for row in rows)
        self.assertEqual((7601,3408,4193,1553),(len(rows),nonblank,blank,sunset))
        observed = self.result['conditional_withheld']['field_completion']
        self.assertEqual(sunset/len(rows),observed['sunset']['lower_share_full_cohort'])
        self.assertEqual((sunset+blank)/len(rows),observed['sunset']['upper_share_full_cohort'])
        self.assertEqual(2248,len(rows)//2+1-sunset)
        self.assertEqual(2248,observed['sunset_majority']['additional_blank_memberships_needed'])

    def test_independent_sunset_action_and_byte_shares(self):
        rows = self.filtered[0]
        source = [row for row in rows if row['collection_id']=='data_source']
        tagged = {row['capture_identity'] for row in source if row['target_id']}
        sunset = {row['capture_identity'] for row in source if row['target_id']=='Sunset'}
        selected_actions = {row['action_id'] for row in source if row['target_id']}
        sunset_actions = {row['action_id'] for row in source if row['target_id']=='Sunset'}
        selected_bytes = sum(int(row['archive_size_bytes']) for row in rows if row['capture_identity'] in tagged)
        sunset_bytes = sum(int(row['archive_size_bytes']) for row in rows if row['capture_identity'] in sunset)
        panel = self.result['conditional_withheld']['selection_weighting']['strict_tagged_weighting_panel']
        self.assertEqual(len(sunset_actions)/len(selected_actions),panel['sunset_share_of_selected_actions'])
        self.assertEqual(sunset_bytes/selected_bytes,panel['sunset_share_of_tagged_bytes'])
        self.assertLess(panel['sunset_share_of_selected_actions'],.5)
        self.assertGreater(panel['sunset_share_of_tagged_bytes'],.5)

    def test_overlap_membership_and_fractional_byte_conservation(self):
        memberships = self.filtered[2]
        self.assertEqual({'28','29'},set(self.result['removal']['original_plan_orders']))
        self.assertEqual(36,len({row['plan_order'] for row in memberships if row['plan_order']}))
        per_action = {}
        for row in memberships:
            if row['plan_order']:
                per_action.setdefault(row['action_id'],set()).add(row['plan_order'])
        active_bytes = sum(int(row['archive_size_bytes']) for row in self.filtered[0] if row['action_id'] in per_action)
        conservation = self.result['conditional_withheld']['opportunity_weighting']['fractional_conservation']['archive_size_bytes']
        self.assertEqual(active_bytes,conservation['expected_unique_total'])
        self.assertAlmostEqual(active_bytes,conservation['fractional_window_total'],places=5)
        self.assertAlmostEqual(active_bytes,conservation['collapsed_fractional_total'],places=5)

    def test_no_op_control_reproduces_the_original_five_receipt_blocks(self):
        self.assertEqual(self.result['baseline'],metrics(self.manifest,self.assignments,self.memberships))
        self.assertTrue(all(self.result['baseline_replay_checks'].values()))

    def test_predicates_can_report_lost_support_not_force_robustness(self):
        changed = copy.deepcopy(self.result['conditional_withheld'])
        changed['relationship']['action_isolated_test_products']=1
        changed['selection_weighting']['strict_tagged_weighting_panel']['sunset_share_of_tagged_bytes']=.49
        changed['selection_weighting']['collection_byte_sensitivity']['data_source']['sunset_share']=.51
        flags = conclusion_flags(changed)
        self.assertFalse(flags['zero_action_isolated_test_products'])
        self.assertFalse(flags['selected_sunset_action_minority_byte_majority'])
        self.assertFalse(flags['source_tier_sunset_minority_raw_processed_majorities'])

    def test_all_actual_named_dispositions_hold_only_for_this_condition(self):
        self.assertEqual(8,len(self.result['conclusions']))
        self.assertTrue(all(row['same_boolean_disposition'] and row['withheld'] for row in self.result['conclusions'].values()))
        self.assertTrue(all(value is False for value in self.result['limits'].values()))
        self.assertEqual({'network_requests':0,'new_image_bytes':0,'outreach':False,'publication':False,'remote_push':False},self.result['effects'])

    def test_protected_detection_receipts_are_unchanged_not_reinterpreted(self):
        pins = {pin['path']:pin for pin in self.contract['input_pins']}
        for path in ['results/stage11n-result.json','results/stage11q-injection-recovery.json']:
            verify_pin(pins[path])
        self.assertIn('not recomputed',self.result['detection_disposition'])

    def test_actual_cli_and_every_csv_row_replay(self):
        completed = subprocess.run([sys.executable,'-B','-m','src.camera_sequence_downstream_sensitivity','--check'],cwd=ROOT,check=True,capture_output=True,text=True)
        self.assertEqual(15,json.loads(completed.stdout)['removed_products'])
        for name,data in artifacts(self.result).items():
            self.assertEqual(data,(OWNER/name).read_bytes())
        self.assertEqual(15,len(load_csv(OWNER/'withheld-products.csv')))
        self.assertEqual(len(self.result['comparison']),len(load_csv(OWNER/'comparison.csv')))

    def test_changed_existing_artifact_blocks_all_writes(self):
        with tempfile.TemporaryDirectory() as directory,patch('src.camera_sequence_downstream_sensitivity.OWNER',Path(directory)),patch('src.camera_sequence_downstream_sensitivity.replay',return_value=self.result):
            root=Path(directory)
            (root/'result.json').write_bytes(b'owner edit')
            with self.assertRaises(ValueError):
                run('--write')
            self.assertEqual(b'owner edit',(root/'result.json').read_bytes())
            self.assertFalse((root/'comparison.csv').exists())

    def test_acceptance_or_effect_mutation_stops_before_source_or_output_access(self):
        for field in ['physical_identity','canonical_counts_replaced','candidate_adopted']:
            changed=copy.deepcopy(self.contract)
            changed['limits'][field]=True
            with patch('src.camera_sequence_downstream_sensitivity.load_json',return_value=changed),self.assertRaises(ValueError):
                replay()

    def test_numeric_compare_does_not_confuse_boolean_and_integer(self):
        self.assertFalse(close_tree(True,1))
        self.assertFalse(close_tree(0,False))
        self.assertTrue(close_tree({'value':1.0},{'value':1.0}))
        self.assertFalse(close_tree({'value':1.0},{'value':1.1}))


if __name__=='__main__':
    unittest.main()
