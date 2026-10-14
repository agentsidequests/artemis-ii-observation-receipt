"""Candidate-document consistency only, not an image scorer or scientific oracle."""

import copy
import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'target-label-audit/corona-rubric'


def interpret_declared_rules(rules, gates, premises):
    """Replay explicit synthetic premises; never infer any premise from pixels."""
    for rule in rules:
        if 'if_any_false' in rule:
            matches = any(gates.get(key) is not True for key in rule['if_any_false'])
        elif 'if_all' in rule:
            matches = all(premises.get(key) == value for key, value in rule['if_all'].items())
        elif 'if_any' in rule:
            matches = any(premises.get(key) == value for key, value in rule['if_any'].items())
        else:
            matches = True
        if matches:
            return rule['disposition']
    raise AssertionError('Candidate rules need a terminal abstention.')


class CoronaRubricCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((FOLDER / 'contract.json').read_text(encoding='utf-8'))
        cls.cases = json.loads((FOLDER / 'decision-cases.json').read_text(encoding='utf-8'))
        cls.document = (FOLDER / 'CANDIDATE-RUBRIC.md').read_text(encoding='utf-8')

    def evaluate(self, case, gates=None):
        scenario_gates = copy.deepcopy(gates if gates is not None else self.cases['hypothetical_accepted_gates'])
        scenario_gates.update(case.get('gate_overrides', {}))
        premises = self.cases['default_premises'] | case.get('premises', {})
        return interpret_declared_rules(self.contract['ordered_candidate_rules'], scenario_gates, premises)

    def test_current_candidate_is_unaccepted_without_effects(self):
        self.assertEqual(self.contract['status'], 'CANDIDATE_UNACCEPTED_NOT_READY_TO_SCORE')
        self.assertTrue(all(value is False for value in self.contract['gates'].values()))
        self.assertTrue(all(value is False for value in self.contract['effects_completed'].values()))
        self.assertFalse(self.contract['physical_classifier'])
        self.assertFalse(self.contract['numeric_detection_thresholds_accepted'])

    def test_release_gate_first_and_abstention_last(self):
        rules = self.contract['ordered_candidate_rules']
        self.assertEqual(rules[0]['rule'], 'RELEASE_GATE')
        self.assertEqual(set(rules[0]['if_any_false']), set(self.contract['gates']))
        self.assertEqual(rules[-1], {'rule': 'DEFAULT_ABSTENTION', 'disposition': 'UNRESOLVED'})

    def test_ten_hypothetical_cases_match_declared_rules(self):
        self.assertEqual(self.cases['status'], 'SYNTHETIC_PREMISE_CASES_ONLY')
        self.assertEqual(len(self.cases['cases']), 10)
        self.assertEqual(len({case['id'] for case in self.cases['cases']}), 10)
        for case in self.cases['cases']:
            with self.subTest(case=case['id']):
                self.assertEqual(self.evaluate(case), case['expected'])
                self.assertTrue(case['id'].startswith('SYN-'))
                self.assertNotIn('capture_identity', case)

    def test_no_hypothetical_case_is_ready_under_current_gates(self):
        for case in self.cases['cases']:
            self.assertEqual(self.evaluate(case, self.contract['gates']), 'NOT_READY_TO_SCORE')
        ready_gates = self.cases['hypothetical_accepted_gates']
        positive = self.cases['cases'][1]
        for gate in ready_gates:
            self.assertEqual(self.evaluate(positive, ready_gates | {gate: False}), 'NOT_READY_TO_SCORE')

    def test_each_absence_premise_is_required(self):
        negative = self.cases['cases'][6]
        self.assertEqual(self.evaluate(negative), 'ABSENT')
        for field, value in {
            'carrier_readable': False,
            'limb_region_locatable': False,
            'complete_region_coverage': False,
            'negative_profile_adequacy': False,
            'minimum_feature_recognition_demonstrated': False,
            'artifact_interference': 'UNRESOLVED',
            'unit_eligibility': 'UNKNOWN',
        }.items():
            changed = copy.deepcopy(negative)
            changed['premises'][field] = value
            with self.subTest(missing=field):
                self.assertEqual(self.evaluate(changed), 'UNRESOLVED')

    def test_positive_is_local_not_complete_coverage_but_not_artifact_blind(self):
        positive = copy.deepcopy(self.cases['cases'][2])
        self.assertEqual(self.evaluate(positive), 'PRESENT')
        for field, value in {'local_positive_adequacy': False, 'limb_region_locatable': False, 'artifact_interference': 'UNKNOWN'}.items():
            changed = copy.deepcopy(positive)
            changed['premises'][field] = value
            self.assertEqual(self.evaluate(changed), 'UNRESOLVED')

    def test_original_metadata_does_not_control_image_only_disposition(self):
        for case in self.cases['cases']:
            for target in ['', 'Sunset', 'Earth', 'Moon', 'Unknown']:
                changed = copy.deepcopy(case)
                changed['premises']['original_target'] = target
                changed['premises']['activity_id'] = '24_Sunset'
                changed['premises']['camera_serial'] = '3500015'
                self.assertEqual(self.evaluate(changed), case['expected'])

    def test_no_physical_origin_or_subtype_certification(self):
        self.assertEqual(self.contract['physical_subtypes_admitted'], [])
        self.assertNotIn('VERIFIED_CORONA', self.contract['interpretation_states'])
        for case in self.cases['cases']:
            self.assertIn(case['interpretation_state'], self.contract['interpretation_states'])
        same_capture = self.cases['cases'][-1]
        self.assertEqual(same_capture['reference_dependence'], 'SAME_CAPTURE')
        self.assertEqual(same_capture['interpretation_state'], 'UNRESOLVED')

    def test_empty_supplementary_form_has_no_hidden_metadata(self):
        with (FOLDER / 'review-form.csv').open(encoding='utf-8', newline='') as stream:
            self.assertEqual(list(csv.reader(stream)), [self.contract['supplementary_fields']])
        fields = self.contract['supplementary_fields']
        for forbidden in ['original_target', 'capture_identity', 'camera_serial', 'activity_id', 'source_url']:
            self.assertNotIn(forbidden, fields)
        self.assertIn('viewing_profile_sha256', fields)
        self.assertIn('reference_dependence', fields)

    def test_source_identities_and_local_bytes(self):
        self.assertEqual(len(self.contract['sources']), 6)
        for source in self.contract['sources']:
            self.assertTrue(source['url'].startswith('https://'))
            self.assertTrue(source['transfer_limit'])
            if 'local_path' in source:
                payload = (ROOT / source['local_path']).read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), source['sha256'])
        paper = next(source for source in self.contract['sources'] if source['id'] == 'TSUMURA_ARIMATSU')
        self.assertTrue(paper['url'].endswith('2604.13908v3'))
        self.assertTrue(paper['correction_retraction_status'].startswith('UNKNOWN'))
        self.assertEqual(paper['journal_byte_parity'], 'UNKNOWN')

    def test_existing_protocol_and_pilot_ownership_links_exist(self):
        for key in ['controlling_protocol', 'pilot_receipt', 'rubric_file']:
            self.assertTrue((ROOT / self.contract[key]).is_file())
        protocol = json.loads((ROOT / 'target-label-audit/contract.json').read_text(encoding='utf-8'))
        self.assertEqual(self.contract['judgments'], protocol['judgments'])
        self.assertTrue(all(value is False for value in protocol['effects_completed'].values()))

    def test_candidate_text_and_files_preserve_explicit_limits(self):
        for phrase in [
            'appearance diagnostic, not a solar-corona classifier',
            'Presence needs local adequacy; absence needs complete adequacy',
            'Appearance `ABSENT` does not prove a `Sunset` tag wrong',
            'same-image consensus is not independent physical truth',
            'counterexample to blanket image unusability',
            'Research text was reviewed',
        ]:
            self.assertIn(phrase.casefold(), self.document.casefold())
        for path in FOLDER.iterdir():
            if path.suffix in {'.md', '.json', '.csv'}:
                self.assertNotIn('\u2014', path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
