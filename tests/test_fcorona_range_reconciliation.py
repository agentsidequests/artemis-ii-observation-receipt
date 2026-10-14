"""Source identity, geometry replay and hard negatives, not scientific acceptance."""

import copy
import hashlib
import json
import unittest

from src.fcorona_range_reconciliation import OWNER, ROOT, observer, reconcile_texts, replay, table, vectors


class FcoronaRangeReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((OWNER / 'horizons-requests.json').read_text(encoding='utf-8'))
        cls.texts = {path.name: path.read_text(encoding='utf-8') for path in (OWNER / 'source').glob('*.txt')}
        cls.result = json.loads((OWNER / 'result.json').read_text(encoding='utf-8'))

    def test_result_replays_all_preserved_source_bytes(self):
        self.assertEqual(self.result, replay())

    def test_anchors_replay_the_old_contract_without_event_mapping(self):
        contract = json.loads((ROOT / 'spec/stage11n.json').read_text(encoding='utf-8'))
        for name, position in [('first_clear_candidate_utc',1),('shared_candidate_utc',2),('ambiguous_candidate_utc',3),('later_clear_candidate_utc',4),('last_clear_candidate_utc',5),('annotation_ledger_utc',6)]:
            self.assertEqual(contract['transcript_anchors'][name], self.result['rows'][position]['utc'])
        self.assertEqual(4, self.result['clear_report_anchor_count'])
        self.assertFalse(self.result['limits']['all_five_events_mapped'])

    def test_source_bytes_have_exact_sizes_and_hashes(self):
        acquisition = json.loads((OWNER / 'acquisition-receipt.json').read_text(encoding='utf-8'))
        for source in acquisition['files']:
            payload = (OWNER / 'source' / source['file']).read_bytes()
            self.assertEqual(len(payload), source['bytes'])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), source['sha256'])

    def test_wrong_center_is_rejected(self):
        changed = self.texts['vectors.txt'].replace('Center body name: Moon (301)', 'Center body name: Earth (399)')
        with self.assertRaises(ValueError):
            vectors(changed)

    def test_wrong_units_are_rejected(self):
        changed = self.texts['vectors.txt'].replace('Output units    : KM-S', 'Output units    : AU-D')
        with self.assertRaises(ValueError):
            vectors(changed)

    def test_tdb_is_not_silently_treated_as_utc(self):
        changed = self.texts['vectors.txt'].replace('JDUT', 'JDTDB').replace('Calendar Date (UT )', 'Calendar Date (TDB)')
        with self.assertRaises(ValueError):
            vectors(changed)

    def test_changed_epoch_cannot_replay(self):
        config = copy.deepcopy(self.config)
        config['times'][2]['utc'] = '2026-04-07T01:51:15.947Z'
        with self.assertRaises(ValueError):
            reconcile_texts(self.texts, config)

    def test_missing_row_cannot_be_hidden_by_zip(self):
        texts = dict(self.texts)
        lines = texts['vectors.txt'].splitlines()
        texts['vectors.txt'] = '\n'.join(line for line in lines if not line.startswith('2461137.535601238,'))
        with self.assertRaises(ValueError):
            reconcile_texts(texts, self.config)

    def test_incomplete_source_table_is_rejected(self):
        with self.assertRaises(ValueError):
            table(self.texts['vectors.txt'].replace('$$EOE', ''))

    def test_nonfinite_values_are_rejected(self):
        changed = self.texts['vectors.txt'].replace('-2.546898341717839E+03', 'NaN')
        with self.assertRaises(ValueError):
            vectors(changed)

    def test_cartesian_range_inconsistency_is_rejected(self):
        changed = self.texts['vectors.txt'].replace('8.282107749677036E+03', '9.282107749677036E+03')
        with self.assertRaises(ValueError):
            vectors(changed)

    def test_reciprocal_queries_share_ranges_and_negate_states(self):
        forward = vectors(self.texts['vectors.txt'])
        reverse = vectors(self.texts['reverse-vectors.txt'], reverse=True)
        for a, b in zip(forward, reverse):
            self.assertAlmostEqual(a['distance_km'], b['distance_km'], places=7)
            for x, y in zip(a['position'] + a['velocity'], b['position'] + b['velocity']):
                self.assertAlmostEqual(x, -y, places=7)
        self.assertFalse(self.result['limits']['independent_navigation_solution'])

    def test_observer_unit_mutation_is_rejected(self):
        changed = self.texts['observer.txt'].replace('Units: ARCSECONDS', 'Units: ARCMINUTES')
        with self.assertRaises(ValueError):
            observer(changed)

    def test_center_surface_convention_cannot_reproduce_the_feature_range(self):
        self.assertLess(self.result['largest_all_surface_range_at_clear_anchors_km'], 13500)
        self.assertGreater(self.result['nasa_feature_conditional_center_range_km'], 74000)
        self.assertFalse(self.result['limits']['source_typo_mechanism_proved'])

    def test_photograph_and_near_pericynthion_are_not_the_same_geometry(self):
        near, photograph = self.result['rows'][0], self.result['rows'][-1]
        self.assertAlmostEqual(near['spherical_altitude_km'], 6545, delta=1)
        self.assertAlmostEqual(photograph['spherical_altitude_km'], 10134, delta=1)
        self.assertAlmostEqual(photograph['native_angular_diameter_degrees'], 16.831, places=3)

    def test_no_replacement_photometry_or_external_effect_is_inferred(self):
        self.assertTrue(all(value is False for value in self.result['limits'].values()))
        self.assertIn('retire as an established', self.result['prior_26_96_and_3_58_disposition'])
        effects = json.loads((OWNER / 'acquisition-receipt.json').read_text(encoding='utf-8'))['effects']
        self.assertEqual(effects['image_payloads_acquired'], 0)
        self.assertEqual(effects['installations'], 0)
        self.assertFalse(effects['outreach'])
        self.assertFalse(effects['publication'])
        self.assertFalse(effects['remote_push'])


if __name__ == '__main__':
    unittest.main()
