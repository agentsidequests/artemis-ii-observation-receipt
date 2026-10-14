"""Current correspondence scope, proof gaps, drift and historical-case controls."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP/'src'))
from observation_receipt.evaluator import evaluate_case
from observation_receipt.exporters import write_bundle, render_html
from observation_receipt.model import validate_case, CaseValidationError


class StewardLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case=json.loads((APP/'cases/artemis-ii-identity-confirmed/case.json').read_bytes())
        cls.old=json.loads((APP/'cases/artemis-ii-identity/case.json').read_bytes())

    def mutate(self, change):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root=Path(temporary.name)
        case=copy.deepcopy(self.case)
        for artifact in case['artifacts']:
            target=root/artifact['path']
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((APP/artifact['path']).read_bytes())
        artifact=next(a for a in case['artifacts'] if a['id']=='steward-statement')
        target=root/artifact['path']
        data=json.loads(target.read_bytes())
        change(data['statement'])
        payload=(json.dumps(data)+'\n').encode('utf-8')
        target.write_bytes(payload)
        artifact.update(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
        return case,root

    def test_exact_pair_is_steward_confirmed_not_byte_verified(self):
        result=evaluate_case(self.case,APP)
        self.assertTrue(result['pass'])
        link=result['steward_links'][0]
        self.assertEqual('STEWARD_CONFIRMED_IDENTICAL_IMAGES',link['status'])
        self.assertEqual(['art002e009301','art002e015991'],link['statement']['native_identifiers'])
        self.assertEqual('019A0860.NEF',link['statement']['reported_original_filename'])
        self.assertFalse(link['statement']['local_byte_identity_verified'])
        self.assertFalse(link['representative_selected'])
        self.assertFalse(link['counts_recomputed'])
        self.assertFalse(link['email_authentication_performed_by_app'])

    def test_historical_comparison_and_findings_keep_exact_values(self):
        before=evaluate_case(self.old,APP)
        after=evaluate_case(self.case,APP)
        self.assertEqual(before['conditional_comparisons'],after['conditional_comparisons'])
        self.assertEqual(before['findings'][1:],after['findings'][1:])
        self.assertEqual('BLOCKED_IDENTITY_UNRESOLVED',after['findings'][0]['status'])
        self.assertIn('metadata alone',after['findings'][0]['proposition'].lower())

    def test_adjacent_id_is_a_discriminating_negative(self):
        case,root=self.mutate(lambda s:s['native_identifiers'].__setitem__(1,'art002e015990'))
        with self.assertRaisesRegex(ValueError,'exactly the two'):evaluate_case(case,root)

    def test_subset_duplicate_or_extra_member_is_rejected(self):
        for ids in [['art002e009301'],['art002e009301','art002e009301'],['art002e009301','art002e015991','art002e015990']]:
            with self.subTest(ids=ids):
                case,root=self.mutate(lambda s:s.update(native_identifiers=ids))
                with self.assertRaises(ValueError):evaluate_case(case,root)

    def test_byte_other_pair_count_and_publication_promotions_fail(self):
        for name in ['local_byte_identity_verified','checksums_supplied','other_pairs_confirmed','denominators_changed','publication_permission_established']:
            for value in [True,0,None]:
                with self.subTest(name=name,value=value):
                    case,root=self.mutate(lambda s:s.update({name:value}))
                    with self.assertRaisesRegex(ValueError,'cannot promote'):evaluate_case(case,root)

    def test_extra_source_payload_or_literal_representative_fails(self):
        case,root=self.mutate(lambda s:s.update(raw_email='not bundled'))
        with self.assertRaisesRegex(ValueError,'shape'):evaluate_case(case,root)
        case=copy.deepcopy(self.case)
        case['steward_links'][0]['selected_identity']='art002e015991'
        with self.assertRaises(CaseValidationError):validate_case(case)

    def test_wrong_source_class_or_relation_fails(self):
        for name,value in [('evidence_class','independent_pixel_verification'),('relationship','byte_identical_nefs')]:
            case,root=self.mutate(lambda s:s.update({name:value}))
            with self.assertRaisesRegex(ValueError,'evidence class'):evaluate_case(case,root)

    def test_reference_only_source_and_wrong_group_fail(self):
        case=copy.deepcopy(self.case)
        case['artifacts'][-1].pop('path')
        case['artifacts'][-1]['url']='https://example.org/claim'
        with self.assertRaises(CaseValidationError):validate_case(case)
        case=copy.deepcopy(self.case)
        case['steward_links'][0]['group_id']='another-group'
        with self.assertRaises(CaseValidationError):validate_case(case)

    def test_old_version_cannot_silently_activate_new_links(self):
        case=copy.deepcopy(self.case)
        case['receipt_version']='0.3.0'
        with self.assertRaisesRegex(CaseValidationError,'0.4.0'):validate_case(case)

    def test_integrity_failure_hides_confirmation_values_and_headline(self):
        case,root=self.mutate(lambda s:s.update(reported_original_filename='changed.NEF'))
        case['artifacts'][-1]['sha256']=self.case['artifacts'][-1]['sha256']
        result=evaluate_case(case,root)
        self.assertFalse(result['pass'])
        self.assertIsNone(result['steward_links'][0]['statement'])
        rendered=render_html(case,result)
        self.assertIn('Steward evidence could not be verified',rendered)
        self.assertNotIn('Steward confirmation received',rendered)
        self.assertNotIn('<h1>One confirmed pair.',rendered)
        self.assertNotIn('019A0860.NEF',rendered)
        self.assertNotIn('changed.NEF',rendered)

    def test_missing_alternative_source_also_blocks_confirmation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for artifact in self.case['artifacts']:
                if artifact['id']=='identity-excerpt':continue
                target=root/artifact['path']
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((APP/artifact['path']).read_bytes())
            result=evaluate_case(self.case,root)
            self.assertFalse(result['pass'])
            self.assertIsNone(result['steward_links'][0]['statement'])

    def test_export_shows_the_positive_statement_and_its_limits(self):
        result=evaluate_case(self.case,APP)
        with tempfile.TemporaryDirectory() as folder:
            files=write_bundle(self.case,result,Path(folder))
            text=files['index.html'].read_text(encoding='utf-8')
            for phrase in ['Two catalogue IDs. One steward-confirmed image.','019A0860.NEF','Not verified; no checksums supplied','Metadata-only proof remains insufficient','Both native IDs and original counts are retained']:
                self.assertIn(phrase,text)
            self.assertIn('<h1>One confirmed pair. Original counts preserved.</h1>',text)
            self.assertNotIn('Physical identity remains unresolved',text)
            self.assertNotIn('gmail_message_id',text)
            self.assertNotIn('internet_message_id',text)
            self.assertEqual(result,json.loads(files['receipt.json'].read_bytes()))


if __name__=='__main__':unittest.main()
