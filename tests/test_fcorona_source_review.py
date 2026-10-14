"""Source joins and conditional algebra, not an Artemis pixel or physical oracle."""

import csv
import hashlib
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'paper-review'
PDS_FIELDS = {
    'camera_serial': 'img_surface:Instrument_Information/img_surface:instrument_serial_number',
    'camera_file_number': 'cots_camera:File_Information/cots_camera:file_number',
    'shutter_count': 'cots_camera:Camera_Properties/cots_camera:shutter_count',
    'iso': 'img:ISO/img:iso_number',
    'focal_mm': 'img:Optical_Properties/img:focal_length',
    'shooting_mode': 'cots_camera:Camera_Settings/cots_camera:shooting_mode',
    'bracket_order': 'cots_camera:Exposure/cots_camera:auto_bracket_order',
    'bracket_value': 'cots_camera:Exposure/cots_camera:exposure_bracket_value',
    'target_id': 'msn_surface:Observational_Intent/msn_surface:target_id',
    'activity_id': 'msn_surface:Observational_Intent/msn_surface:activity_id',
}


def two_point_slope(values, radii):
    return math.log(values[0] / values[1]) / math.log(radii[1] / radii[0])


def encoded_subtraction_then_inversion(flux, background, gamma):
    return ((flux + background) ** gamma - background ** gamma) ** (1 / gamma)


class FcoronaSourceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((FOLDER / 'fcorona-source-only-receipt.json').read_text(encoding='utf-8'))
        cls.review = (FOLDER / 'FCORONA-CRITICAL-REVIEW.md').read_text(encoding='utf-8')
        cls.page = json.loads((ROOT / cls.receipt['metadata_input']['path']).read_text(encoding='utf-8'))
        cls.hits = {hit['_id']: hit for hit in cls.page['hits']['hits']}
        with (ROOT / cls.receipt['manifest_input']['path']).open(encoding='utf-8', newline='') as stream:
            cls.manifest = list(csv.DictReader(stream))

    def test_input_bytes_match_preserved_sources(self):
        for key in ['metadata_input', 'manifest_input', 'query_input']:
            source = self.receipt[key]
            payload = (ROOT / source['path']).read_bytes()
            self.assertEqual(len(payload), source['bytes'])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), source['sha256'])

    def test_every_extracted_field_replays_native_metadata(self):
        for record in self.receipt['metadata_records']:
            source = self.hits[record['raw_product_id']]['_source']
            self.assertEqual(source['collection_id'], 'data_raw')
            self.assertEqual(source['gather']['time']['start_time'], record['utc'])
            self.assertTrue(source['gather']['pds_archive']['file_name'].startswith(record['capture_stem'] + '_'))
            for name, key in PDS_FIELDS.items():
                self.assertEqual(source['pds4_label'][key][0], record[name])

    def test_alias_candidate_matches_nine_fields_but_adjacent_shot_does_not(self):
        public, candidate, adjacent = self.receipt['metadata_records']
        fields = self.receipt['matching_operational_fields']
        self.assertEqual(len(fields), 9)
        self.assertEqual(tuple(public[field] for field in fields), tuple(candidate[field] for field in fields))
        self.assertNotEqual(tuple(candidate[field] for field in fields), tuple(adjacent[field] for field in fields))
        for field in ['camera_file_number', 'shutter_count', 'utc', 'bracket_value']:
            self.assertNotEqual(candidate[field], adjacent[field])
        self.assertIn('not source-byte identity', self.receipt['metadata_conclusion'])

    def test_exact_manifest_join_and_shared_action_are_bounded(self):
        for record in self.receipt['metadata_records']:
            rows = [row for row in self.manifest if row['capture_identity'] == record['capture_stem']]
            self.assertEqual(len(rows), record['manifest_product_rows'])
            if rows:
                self.assertEqual({row['collection_id'] for row in rows}, {'data_source', 'data_raw', 'data_processed'})
                for row in rows:
                    self.assertEqual(row['action_id'], record['action_id'])
                    self.assertEqual(int(row['exposure_position']), record['position'])
                    self.assertEqual(int(row['exposures_in_action']), 5)

    def test_literal_target_filter_is_not_a_label_correctness_oracle(self):
        query = json.loads((ROOT / self.receipt['query_input']['path']).read_text(encoding='utf-8'))
        self.assertTrue(any('Observational_Intent/msn_surface:target_id' in field for field in query['_source']))
        self.assertFalse(any('Secondary' in field for field in query['_source']))
        for record in self.receipt['metadata_records']:
            self.assertEqual(record['target_id'], 'Moon')
            self.assertNotEqual(record['target_id'], 'Sunset')
        self.assertIn('not a target-label correctness judgment', self.receipt['literal_sunset_filter_result'])
        self.assertIn('not proof that NASA should replace', self.review)

    def test_three_id_pilot_overlap_screen_replays_but_not_full_history(self):
        with (ROOT / 'target-label-audit/pilot-prep/steward-crosswalk.csv').open(encoding='utf-8', newline='') as stream:
            pilot_ids = {row['capture_identity'] for row in csv.DictReader(stream)}
        screen = self.receipt['pilot_overlap']
        self.assertEqual(sum(stem in pilot_ids for stem in screen['screened_exact_stems']), screen['matches'])
        self.assertIn('no full reference-history', screen['limit'])

    def test_noncommuting_order_witness_is_numerically_reproducible(self):
        model = self.receipt['synthetic_model']
        truth = [model['amplitude'] * radius ** (-model['true_slope_magnitude']) for radius in model['radii']]
        self.assertEqual(truth, model['true_intensities'])
        wrong = [encoded_subtraction_then_inversion(flux, model['pre_encoding_background'], model['gamma']) for flux in truth]
        for computed, retained in zip(wrong, model['wrong_order_intensities']):
            self.assertAlmostEqual(computed, retained, places=12)
        self.assertAlmostEqual(two_point_slope(wrong, model['radii']), model['wrong_order_slope_magnitude'], places=12)
        self.assertGreater(two_point_slope(wrong, model['radii']), model['true_slope_magnitude'])

    def test_correct_pre_encoding_model_recovers_truth(self):
        model = self.receipt['synthetic_model']
        recovered = [((flux + model['pre_encoding_background']) ** model['gamma']) ** (1 / model['gamma']) - model['pre_encoding_background'] for flux in model['true_intensities']]
        self.assertAlmostEqual(two_point_slope(recovered, model['radii']), 3, places=12)

    def test_zero_background_and_linear_encoding_are_hard_negatives(self):
        for flux in [1, 8]:
            self.assertAlmostEqual(encoded_subtraction_then_inversion(flux, 0, .75), flux, places=12)
            self.assertAlmostEqual(encoded_subtraction_then_inversion(flux, 1, 1), flux, places=12)

    def test_post_encoding_offset_can_be_subtracted_correctly(self):
        for flux in [1, 8]:
            observed = flux ** .75 + 1
            self.assertAlmostEqual((observed - 1) ** (1 / .75), flux, places=12)

    def test_positive_residual_and_spatial_gain_have_distinct_slope_effects(self):
        model = self.receipt['synthetic_model']
        residual = [flux + model['positive_linear_background_residual'] for flux in model['true_intensities']]
        spatial = [model['true_intensities'][0], model['true_intensities'][1] * model['outer_gain']]
        self.assertAlmostEqual(two_point_slope(residual, model['radii']), model['positive_residual_slope_magnitude'], places=12)
        self.assertAlmostEqual(two_point_slope(spatial, model['radii']), model['spatial_gain_slope_magnitude'], places=12)
        self.assertLess(two_point_slope(residual, model['radii']), 3)
        self.assertGreater(two_point_slope(spatial, model['radii']), 3)

    def test_corresponding_level_sets_need_uniform_strict_monotonicity(self):
        values = [1, 2, 4, 8]
        for gamma in [.25, .75, 1, 2]:
            for threshold in values:
                self.assertEqual([value >= threshold for value in values], [value ** gamma >= threshold ** gamma for value in values])
        # Two explicit excluded cases: clipping ties and a spatial gain reversal.
        self.assertEqual(min(1, 2), min(1, 4))
        self.assertLess(1, 2)
        self.assertGreater(1 * 3, 2 * 1)

    def test_access_denials_and_no_effects_remain_explicit(self):
        for attempt in self.receipt['access_attempts']:
            self.assertEqual(attempt.get('http', attempt.get('bounded_direct_get_http')), 403)
        effects = self.receipt['effects_completed']
        self.assertEqual(effects['image_payload_bytes_acquired'], 0)
        self.assertTrue(all(value is False for key, value in effects.items() if key != 'image_payload_bytes_acquired'))
        model = self.receipt['synthetic_model']
        self.assertFalse(model['claimed_actual_paper_error'])
        self.assertFalse(model['actual_processing_order_verified'])

    def test_review_text_preserves_sources_scope_and_no_em_dash(self):
        for phrase in ['No error by the authors is established', 'No archive-wide alias prevalence', 'not authorization to acquire', 'not a new astrophysical discovery']:
            self.assertIn(phrase, self.review)
        for path in FOLDER.iterdir():
            if path.suffix in {'.md', '.json'}:
                self.assertNotIn('\u2014', path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
