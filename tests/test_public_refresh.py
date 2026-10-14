"""Current public entry, rights and scoped statement checks, not scientific acceptance."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicRefreshTests(unittest.TestCase):
    def test_raw_correspondence_and_private_preparer_are_not_bundled(self):
        for name in [
            'paper-review/identity-census/nasa-response-2026-10-13.json',
            'paper-review/identity-census/NASA-RESPONSE-2026-10-13.md',
            'paper-review/steward-integration/JPL-FOLLOW-UP-DRAFT-2026-10-13.md',
            'src/prepare_steward_identity_demo.py',
            'tools/package_presentation.py',
        ]:
            self.assertFalse((ROOT/name).exists(), name)

    def test_exact_pair_summary_does_not_promote_byte_or_publication_evidence(self):
        source = json.loads((ROOT/'observation-receipt/cases/artemis-ii-identity-confirmed/sources/steward-confirmation.json').read_bytes())
        statement = source['statement']
        self.assertEqual(['art002e009301','art002e015991'], statement['native_identifiers'])
        self.assertEqual('019A0860.NEF', statement['reported_original_filename'])
        self.assertEqual("JPL reply reporting the science/archive teams' confirmation", statement['source_owner'])
        for key in ['local_byte_identity_verified','checksums_supplied','other_pairs_confirmed','denominators_changed','publication_permission_established']:
            self.assertIs(False, statement[key], key)

    def test_current_app_next_steps_do_not_request_a_repeat_email(self):
        case = json.loads((ROOT/'observation-receipt/cases/artemis-ii-identity-confirmed/case.json').read_bytes())
        self.assertIn('does not require another email request', case['next_steps'][1])
        self.assertEqual('0.4.0', case['receipt_version'])

    def test_prior_public_clock_qualification_is_retained(self):
        case = json.loads((ROOT/'observation-receipt/cases/artemis-ii-flashes/case.json').read_bytes())
        self.assertIn('not a verified ledger-creation time or an upper bound on all five events', case['viewer_context']['key_distinction'])
        self.assertEqual('event times unresolved; background-photo context is separate', case['artifacts'][0]['clock_domain'])

    def test_public_rights_match_the_approved_credit(self):
        license_bytes = (ROOT/'LICENSE').read_bytes()
        self.assertEqual(license_bytes, (ROOT/'observation-receipt/LICENSE').read_bytes())
        self.assertIn(b'MIT License', license_bytes)
        self.assertIn(b'Copyright (c) 2026 agentsidequests', license_bytes)
        self.assertIn('not relicensed', (ROOT/'README.md').read_text(encoding='utf-8').lower())

    def test_public_front_door_carries_all_cases_and_the_interactive_presentation(self):
        readme = (ROOT/'README.md').read_text(encoding='utf-8')
        for target in ['Artemis-II-Interactive-Presentation-2026-10-13.html', 'preview/identity-confirmed/index.html', 'preview/robustness/index.html', 'preview/flashes/index.html', 'preview/identity/index.html']:
            self.assertIn(target, readme)
            self.assertTrue((ROOT/target).is_file(), target)

    def test_summary_preserves_tentative_cause_and_zero_direct_cohort_reduction(self):
        text = (ROOT/'PUBLIC-REFRESH-NOTES-2026-10-13.md').read_text(encoding='utf-8')
        for phrase in ['likely explanation is not a demonstrated cause', 'Only `art002e015991` belongs', 'does not remove a double count', 'other 23', 'not a reproduction of the email']:
            self.assertIn(phrase, text)


if __name__ == '__main__':
    unittest.main()
