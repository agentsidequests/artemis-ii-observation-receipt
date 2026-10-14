"""Metadata proposal checks, not an image-label validity or human-use oracle."""

import copy
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import prepare_target_label_pilot as prep


class TargetLabelPilotPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts, cls.receipt = prep.build()
        cls.policy, cls.groups, cls.source_rows, cls.excluded = prep.load_inputs(prep.ROOT)
        cls.crosswalk = list(csv.DictReader(io.StringIO(cls.artifacts['steward-crosswalk.csv'].decode('utf-8'))))
        cls.queue = list(csv.DictReader(io.StringIO(cls.artifacts['reviewer-queue.csv'].decode('utf-8'))))

    def test_counts_unique_units_and_actions(self):
        self.assertEqual(len(self.crosswalk), 48)
        self.assertEqual(len({r['capture_identity'] for r in self.crosswalk}), 48)
        self.assertEqual(len({r['action_id'] for r in self.crosswalk}), 48)
        self.assertEqual(len({r['audit_id'] for r in self.crosswalk}), 48)
        self.assertEqual(len(self.queue), 24)

    def test_phase_quotas_and_separate_actions(self):
        for phase, counts in self.receipt['phase_bucket_counts'].items():
            self.assertEqual(counts, self.policy['phase_quotas'])
            self.assertEqual(set(self.receipt['phase_camera_counts'][phase]), {'3500015', '3500017', '3920019'})
            self.assertEqual(set(self.receipt['phase_coverage_regimes'][phase]), {'zero', 'partial', 'complete'})
        first = {r['action_id'] for r in self.crosswalk if r['phase'] == 'CALIBRATION_PROPOSED'}
        reserve = {r['action_id'] for r in self.crosswalk if r['phase'] == 'CONFIRMATION_RESERVED'}
        self.assertFalse(first & reserve)

    def test_review_queue_is_calibration_only_and_masked(self):
        self.assertTrue(all(set(r) == set(prep.QUEUE_FIELDS) for r in self.queue))
        self.assertTrue(all(r['phase'] == 'CALIBRATION_PROPOSED' for r in self.queue))
        payload = self.artifacts['reviewer-queue.csv'].decode('utf-8')
        for token in ['art002e', '3500015', '3920019', 'https://', 'snapshot_target_field', 'activity_id', 'bracket_value']:
            self.assertNotIn(token, payload)
        for row in self.queue:
            self.assertEqual(row['render_status'], 'NO_IMAGE_BUNDLE')
            self.assertEqual(row['decision_status'], 'NOT_REVIEWED')

    def test_native_lineage_bytes_and_urls_are_recomputed(self):
        for row in self.crosswalk:
            products = self.groups[row['capture_identity']]
            self.assertEqual(row['snapshot_target_field'], products['data_source']['target_id'])
            for collection, prefix in zip(prep.COLLECTIONS, ('source', 'raw', 'processed')):
                product = products[collection]
                self.assertEqual(row[prefix + '_product_id'], product['product_id'])
                self.assertEqual(int(row[prefix + '_archive_size_bytes']), int(product['archive_size_bytes']))
                self.assertEqual(row[prefix + '_url'], prep.product_url(product, self.policy))
                self.assertEqual(row[prefix + '_label_url'], row[prefix + '_url'].rsplit('.', 1)[0] + '.xml')
            self.assertEqual(row['url_status'], 'DERIVED_NATIVE_PATH_NOT_LIVE_CHECKED')
            self.assertEqual(row['image_hash_status'], 'UNACQUIRED_UNKNOWN')

    def test_exact_costs_agree_with_crosswalk(self):
        for phase in self.policy['phases']:
            rows = [r for r in self.crosswalk if r['phase'] == phase]
            for collection, prefix in zip(prep.COLLECTIONS, ('source', 'raw', 'processed')):
                value = sum(int(r[prefix + '_archive_size_bytes']) for r in rows)
                self.assertEqual(value, self.receipt['native_representation_bytes'][phase][collection])
        total_processed = sum(v['data_processed'] for v in self.receipt['native_representation_bytes'].values())
        self.assertEqual(total_processed, 8480681056)

    def test_known_browse_exclusions_are_scoped(self):
        self.assertFalse({r['capture_identity'] for r in self.crosswalk} & self.excluded)
        self.assertIn('not a whole-history independence certificate', self.receipt['exclusion_history_scope'])

    def test_selection_is_input_order_invariant(self):
        forward = prep.choose_panel(self.source_rows, self.policy, self.excluded)
        reverse = prep.choose_panel(list(reversed(self.source_rows)), self.policy, self.excluded)
        self.assertEqual(forward, reverse)

    def test_deterministic_replay_and_artifact_identity(self):
        artifacts, receipt = prep.build()
        self.assertEqual(artifacts, self.artifacts)
        self.assertEqual(receipt, self.receipt)
        for name, info in receipt['artifacts'].items():
            self.assertEqual(info['bytes'], len(artifacts[name]))
            self.assertEqual(info['sha256'], prep.sha(artifacts[name]))
        self.assertTrue(all('\\' not in name for name in receipt['source_hashes']))

    def test_source_hash_mutation_fails_closed(self):
        read = Path.read_bytes
        def mutated(path):
            payload = read(path)
            return payload + b' ' if path.name == 'stage10o-product-relationship-manifest.csv' else payload
        with mock.patch.object(Path, 'read_bytes', mutated):
            with self.assertRaisesRegex(ValueError, 'Pinned source changed'):
                prep.build()

    def test_authority_flags_cannot_promote_proposal(self):
        read = Path.read_text
        for field, value in [('current_pixel_budget_bytes', 1), ('future_preview_ceiling_is_authorized', True),
                             ('images_labeled', True), ('qualified_rubric_accepted', True), ('probability_sample_drawn', True)]:
            policy = copy.deepcopy(self.policy)
            policy[field] = value
            def altered(path, *args, **kwargs):
                return json.dumps(policy) if path.name == 'policy.json' else read(path, *args, **kwargs)
            with self.subTest(field=field), mock.patch.object(Path, 'read_text', altered):
                with self.assertRaisesRegex(ValueError, 'cannot declare execution'):
                    prep.load_inputs(prep.ROOT)

    def test_infeasible_panel_refuses_padding(self):
        policy = copy.deepcopy(self.policy)
        with self.assertRaisesRegex(ValueError, 'infeasible'):
            prep.choose_panel(self.source_rows[:1], policy, set())

    def test_inconsistent_quota_refused(self):
        policy = copy.deepcopy(self.policy)
        policy['phase_quotas']['blank_recorded_tag'] = 11
        with self.assertRaisesRegex(ValueError, 'frozen phase quotas'):
            prep.choose_panel(self.source_rows, policy, self.excluded)

    def test_product_path_traversal_refused(self):
        row = copy.deepcopy(self.source_rows[0])
        row['product_id'] = self.policy['product_id_prefix'] + '/artemis2_crew_camera/data_source/../secret'
        with self.assertRaisesRegex(ValueError, 'not within'):
            prep.product_url(row, self.policy)

    def test_existing_different_artifact_blocks_all_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            folder = root / prep.PREP
            folder.mkdir(parents=True)
            (folder / 'reviewer-packet.md').write_bytes(b'owned edit')
            artifacts = {'reviewer-queue.csv': b'new', 'reviewer-packet.md': b'replacement'}
            with mock.patch.object(prep, 'ROOT', root), mock.patch.object(prep, 'build', return_value=(artifacts, {})), \
                    mock.patch('sys.argv', ['prepare', '--write']):
                with self.assertRaisesRegex(ValueError, 'Existing artifact differs'):
                    prep.main()
            self.assertFalse((folder / 'reviewer-queue.csv').exists())
            self.assertEqual((folder / 'reviewer-packet.md').read_bytes(), b'owned edit')

    def test_claim_limits_and_no_em_dash(self):
        packet = self.artifacts['reviewer-packet.md'].decode('utf-8')
        for phrase in ['not an independently validated label', 'no ready-to-score blinded image bundle',
                       'not observed transfer totals', 'current authorized pixel budget is **zero**',
                       'not access-control enforcement', 'More labels cannot create a second Sunset event']:
            self.assertIn(phrase, packet)
        self.assertNotIn('\u2014', packet)
        for key, value in self.receipt['effects'].items():
            self.assertEqual(value, 0 if key == 'pixel_bytes_acquired' else False)


if __name__ == '__main__':
    unittest.main()
