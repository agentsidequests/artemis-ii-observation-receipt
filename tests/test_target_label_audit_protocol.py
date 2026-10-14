"""Design-artifact checks only. No sampler, annotations or scientific oracle."""

import csv
import hashlib
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TargetLabelAuditProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / 'target-label-audit/contract.json').read_text(encoding='utf-8'))
        cls.protocol = (ROOT / 'ARTEMIS-II-TARGET-LABEL-AUDIT-PROTOCOL.md').read_text(encoding='utf-8')

    def test_design_is_not_reported_as_execution(self):
        self.assertEqual(self.contract['status'], 'DESIGN_ONLY_NOT_EXECUTED')
        self.assertTrue(all(value is False for value in self.contract['effects_completed'].values()))
        self.assertFalse(self.contract['planning_example_only']['approved_allocation'])

    def test_exact_frame_and_partition(self):
        path = ROOT / self.contract['manifest']
        payload = path.read_bytes()
        self.assertEqual(len(payload), self.contract['manifest_bytes'])
        self.assertEqual(hashlib.sha256(payload).hexdigest(), self.contract['manifest_sha256'])
        with path.open(newline='', encoding='utf-8') as stream:
            rows = [r for r in csv.DictReader(stream) if r['collection_id'] == self.contract['collection_filter']]
        counts = self.contract['frame_counts']
        self.assertEqual(len(rows), counts['total'])
        self.assertEqual(len({r['capture_identity'] for r in rows}), len(rows))
        self.assertEqual(len({r['action_id'] for r in rows}), counts['actions'])
        self.assertEqual(sum(bool(r['target_id'].strip()) for r in rows), counts['tagged'])
        self.assertEqual(sum(not r['target_id'].strip() for r in rows), counts['blank'])
        self.assertEqual(counts['tagged'] + counts['blank'], counts['total'])

    def test_empty_forms_match_contract_and_preserve_blinding(self):
        for name, key in [('reviewer-form.csv', 'reviewer_fields'), ('adjudication-form.csv', 'adjudication_fields')]:
            with (ROOT / 'target-label-audit' / name).open(newline='', encoding='utf-8') as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(rows, [self.contract[key]])
        self.assertNotIn('original_target', self.contract['reviewer_fields'])
        self.assertNotIn('camera_serial', self.contract['reviewer_fields'])
        self.assertNotIn('activity_id', self.contract['reviewer_fields'])
        self.assertIn('reference_locked_utc', self.contract['adjudication_fields'])
        self.assertIn('archive_unblinded_utc', self.contract['adjudication_fields'])

    def test_unknown_is_not_removed_from_response_inventory(self):
        self.assertEqual(set(self.contract['judgments']), {'PRESENT', 'ABSENT', 'UNRESOLVED', 'OUT_OF_SCOPE'})
        self.assertIn('UNRESOLVED', self.contract['tag_comparisons'])
        self.assertIn('OUT_OF_SCOPE', self.contract['tag_comparisons'])

    def test_planning_example_is_approximate_not_approved(self):
        plan = self.contract['planning_example_only']
        for population_key, sample_key in [('tagged', 'tagged_n'), ('blank', 'blank_n')]:
            N = self.contract['frame_counts'][population_key]
            a = plan['z'] ** 2 * plan['p'] * (1 - plan['p'])
            self.assertEqual(math.ceil(N * a / (plan['half_width'] ** 2 * (N - 1) + a)), plan[sample_key])
        self.assertEqual(plan['tagged_n'] + plan['blank_n'], plan['total'])
        self.assertEqual(2 * plan['total'], plan['initial_reviews_one_concept'])
        self.assertFalse(plan['guaranteed_precision'])
        self.assertIn('not a guaranteed interval width', self.protocol)

    def test_purposeful_pilot_cannot_supply_probability_estimate(self):
        self.assertFalse(self.contract['pilot']['probability_estimation_allowed'])
        self.assertIn('cannot estimate population rates', self.protocol)

    def test_material_claim_boundaries_are_explicit(self):
        for text in [
            'not deterministic bounds on all unreviewed images',
            'primary-target choice',
            'cannot create a second Sunset event',
            'without acquiring or labeling images or contacting anyone',
            'Zero observed contradictions is not proof of zero errors',
            'A one-concept pilot cannot evaluate tags naming other concepts',
        ]:
            self.assertIn(text, self.protocol)

    def test_synthetic_weight_counterexample_is_not_unweighted(self):
        population = [1, 9]
        means = [1, 0]
        weighted = sum(N * y for N, y in zip(population, means)) / sum(population)
        self.assertAlmostEqual(weighted, .1)
        self.assertNotEqual(weighted, sum(means) / len(means))

    def test_new_artifact_text_has_no_em_dash(self):
        self.assertNotIn('\u2014', self.protocol)


if __name__ == '__main__':
    unittest.main()
