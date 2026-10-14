"""Portable source binding, abstention, predicates, exports and first entry."""

import copy
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from observation_receipt.comparisons import evaluate_extension, pointer, read_source
from observation_receipt.evaluator import evaluate_case
from observation_receipt.exporters import write_bundle, render_html, _csv_text
from observation_receipt.model import CaseValidationError, RULE_KINDS, validate_case

CASE = ROOT / 'cases/artemis-ii-identity/case.json'


def temp_sources(case, directory, changed=None):
    modified = copy.deepcopy(case)
    for artifact in modified['artifacts']:
        data = (ROOT / artifact['path']).read_bytes()
        if artifact['id'] == 'sensitivity' and changed is not None:
            parsed = json.loads(data)
            changed(parsed)
            data = (json.dumps(parsed, allow_nan=True) + '\n').encode('utf-8')
        name = artifact['id'] + '.json'
        (directory / name).write_bytes(data)
        artifact.update(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    return modified


class IdentityComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = json.loads(CASE.read_text(encoding='utf-8'))
        cls.receipt = evaluate_case(cls.case, ROOT)

    def test_real_source_bound_fixture_has_eight_predicates_and_one_identity_block(self):
        self.assertTrue(self.receipt['pass'])
        self.assertEqual({'supported':8,'refuted':0,'blocked':1,'other':0},self.receipt['summary'])
        self.assertEqual(self.case['expected_findings'],{f['claim_id']:f['status'] for f in self.receipt['findings']})
        self.assertEqual(['art002e009301','art002e015991'],self.receipt['identity_groups'][0]['alternatives'])
        self.assertFalse(self.receipt['conditional_comparisons'][0]['replaces_original'])

    def test_every_metric_matches_independent_source_walk_and_declared_scale(self):
        source = json.loads((ROOT / self.case['artifacts'][0]['path']).read_text(encoding='utf-8'))
        def walk(block,path):
            for part in path[1:].split('/'):
                block=block[part]
            return block
        metrics = self.receipt['conditional_comparisons'][0]['metrics']
        self.assertEqual(23,len(metrics))
        for metric in metrics:
            a=walk(source['baseline'],metric['pointer'])*metric['scale']
            b=walk(source['conditional_withheld'],metric['pointer'])*metric['scale']
            self.assertEqual((a,b,b-a),(metric['original'],metric['conditional'],metric['delta']))
        by_id={m['id']:m for m in metrics}
        self.assertEqual((4511,4509),(by_id['test']['original'],by_id['test']['conditional']))
        self.assertAlmostEqual(.1326271894041109,by_id['sunset_byte']['delta'],places=10)

    def test_source_mismatch_blocks_values_and_support(self):
        changed=copy.deepcopy(self.case)
        changed['artifacts'][0]['sha256']='0'*64
        receipt=evaluate_case(changed,ROOT)
        self.assertFalse(receipt['pass'])
        self.assertEqual([],receipt['conditional_comparisons'][0]['metrics'])
        self.assertEqual('BLOCKED_COMPARISON_INTEGRITY',receipt['conditional_comparisons'][0]['status'])
        self.assertEqual(0,receipt['summary']['supported'])

    def test_identity_source_mismatch_never_shows_verified_alternatives(self):
        changed=copy.deepcopy(self.case)
        changed['artifacts'][1]['sha256']='0'*64
        receipt=evaluate_case(changed,ROOT)
        self.assertFalse(receipt['pass'])
        self.assertEqual([],receipt['identity_groups'][0]['alternatives'])
        self.assertEqual('BLOCKED_IDENTITY_INTEGRITY',receipt['findings'][0]['status'])

    def test_source_recheck_closes_verification_to_use_race(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            case=temp_sources(self.case,root)
            artifact=case['artifacts'][0]
            (root/artifact['path']).write_bytes(b'changed after verification')
            self.assertIsNone(read_source(artifact,root,{artifact['id']:{'match':True}}))

    def test_repinned_changed_byte_share_loses_support_not_hardcoded(self):
        def change(data):
            data['conditional_withheld']['selection_weighting']['strict_tagged_weighting_panel']['sunset_share_of_tagged_bytes']=.49
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            receipt=evaluate_case(temp_sources(self.case,root,change),root)
            finding=next(f for f in receipt['findings'] if f['claim_id']=='selected_sunset_action_minority_byte_majority')
            self.assertTrue(finding['original_holds'])
            self.assertFalse(finding['conditional_holds'])
            self.assertEqual('REFUTED_CONDITIONAL_STABILITY',finding['status'])
            self.assertFalse(receipt['pass'])

    def test_metric_to_metric_ordering_is_dynamic(self):
        def change(data):
            data['conditional_withheld']['opportunity_weighting']['raw_concentration_equivalent_windows']['actions']=1
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            receipt=evaluate_case(temp_sources(self.case,root,change),root)
            finding=next(f for f in receipt['findings'] if f['claim_id']=='raw_window_concentration_action_above_product_above_byte')
            self.assertEqual('REFUTED_CONDITIONAL_STABILITY',finding['status'])

    def test_resolved_state_and_representative_choice_are_rejected(self):
        for field,value in [('state','resolved'),('selected_identity','art002e015991'),('selected_identity',None)]:
            changed=copy.deepcopy(self.case)
            changed['identity_groups'][0][field]=value
            with self.assertRaises(CaseValidationError):validate_case(changed)

    def test_same_roots_and_literal_values_are_rejected(self):
        changed=copy.deepcopy(self.case)
        changed['conditional_comparisons'][0]['conditional_pointer']='/baseline'
        with self.assertRaises(CaseValidationError):validate_case(changed)
        changed=copy.deepcopy(self.case)
        changed['conditional_comparisons'][0]['metrics'][0]['original']=999
        with self.assertRaises(CaseValidationError):validate_case(changed)

    def test_missing_and_reference_only_sources_are_rejected(self):
        for source in ['unknown',None,[]]:
            changed=copy.deepcopy(self.case)
            changed['conditional_comparisons'][0]['source_artifact_id']=source
            with self.assertRaises(CaseValidationError):validate_case(changed)
        changed=copy.deepcopy(self.case)
        changed['artifacts'][0].pop('path')
        changed['artifacts'][0]['url']='https://example.invalid/reference-only'
        with self.assertRaises(CaseValidationError):validate_case(changed)

    def test_duplicate_and_malformed_extension_ids_are_rejected(self):
        for collection in ['identity_groups','conditional_comparisons']:
            changed=copy.deepcopy(self.case)
            changed[collection].append(copy.deepcopy(changed[collection][0]))
            with self.assertRaises(CaseValidationError):validate_case(changed)
            changed=copy.deepcopy(self.case)
            changed[collection][0]['id']=[]
            with self.assertRaises(CaseValidationError):validate_case(changed)
        changed=copy.deepcopy(self.case)
        changed['conditional_comparisons'][0]['metrics'].append(copy.deepcopy(changed['conditional_comparisons'][0]['metrics'][0]))
        with self.assertRaises(CaseValidationError):validate_case(changed)

    def test_invalid_scale_places_units_and_conditions_are_rejected(self):
        for field,value in [('scale',False),('scale',0),('scale',float('inf')),('places',True),('places',9),('unit',[]),('unit','physical_flux')]:
            changed=copy.deepcopy(self.case)
            changed['conditional_comparisons'][0]['metrics'][0][field]=value
            with self.assertRaises(CaseValidationError):validate_case(changed)
        for condition in [{'metric_id':'missing','op':'eq','value':0},{'metric_id':'isolated','op':'exec','value':0},{'metric_id':'isolated','op':'eq','value':True},{'metric_id':'isolated','op':'eq','value':0,'other_metric_id':'test'},{'metric_id':'test','op':'gt','other_metric_id':'sunset_byte'}]:
            changed=copy.deepcopy(self.case)
            changed['claims'][1]['rule']['conditions']=[condition]
            with self.assertRaises(CaseValidationError):validate_case(changed)

    def test_boolean_nonfinite_and_noninteger_counts_in_source_are_rejected(self):
        for value in [True,float('nan'),float('inf'),-1,22803.5]:
            def change(data):data['conditional_withheld']['selection_weighting']['all_cohort']['products']=value
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder)
                with self.assertRaises(ValueError):evaluate_case(temp_sources(self.case,root,change),root)

    def test_missing_pointer_and_escaped_source_path_are_rejected(self):
        changed=copy.deepcopy(self.case)
        changed['conditional_comparisons'][0]['metrics'][0]['pointer']='/missing'
        with self.assertRaisesRegex(ValueError,'does not resolve'):evaluate_case(changed,ROOT)
        changed=copy.deepcopy(self.case)
        changed['artifacts'][0]['path']='../outside.json'
        with self.assertRaisesRegex(ValueError,'escapes'):evaluate_case(changed,ROOT)

    def test_json_pointer_escapes_array_bounds_and_bad_tilde(self):
        self.assertEqual(3,pointer({'a/b':{'~key':[3]}},'/a~1b/~0key/0'))
        for path in ['/a~2b','/a~1b/~0key/-1','/a~1b/~0key/01','/a~1b/~0key/2']:
            with self.assertRaises(ValueError):pointer({'a/b':{'~key':[3]}},path)

    def test_legacy_version_cannot_silently_take_new_fields(self):
        changed=copy.deepcopy(self.case)
        changed['receipt_version']='0.2.0'
        with self.assertRaises(CaseValidationError):validate_case(changed)
        for name in ['artemis-ii-flashes','synthetic-field-test']:
            legacy=json.loads((ROOT/'cases'/name/'case.json').read_text(encoding='utf-8'))
            receipt=evaluate_case(legacy,ROOT)
            self.assertTrue(receipt['pass'])
            self.assertEqual('0.2.0',receipt['receipt_version'])
            self.assertNotIn('conditional_comparisons',receipt)

    def test_changed_and_unsupported_both_dispositions_are_not_favorable(self):
        rule={'kind':'conditional_comparison_gate','comparison_id':'c','conditions':[{'metric_id':'m','op':'gt','value':0}]}
        for old,new,expected in [(-1,1,'CHANGED_CONDITIONAL_DISPOSITION'),(-1,-2,'UNSUPPORTED_IN_BOTH_VIEWS')]:
            view={'id':'c','integrity_verified':True,'metrics':[{'id':'m','original':old,'conditional':new}]}
            self.assertEqual(expected,evaluate_extension(rule,[],[view])['status'])

    def test_bundle_determinism_all_csv_rows_and_embedded_download(self):
        with tempfile.TemporaryDirectory() as first,tempfile.TemporaryDirectory() as second:
            a=write_bundle(self.case,self.receipt,Path(first))
            b=write_bundle(self.case,self.receipt,Path(second))
            self.assertEqual(10,len(a))
            for name in a:self.assertEqual(a[name].read_bytes(),b[name].read_bytes())
            with a['comparison.csv'].open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
            self.assertEqual(23,len(rows))
            self.assertTrue(all(r['replaces_original']=='False' for r in rows))
            with a['identity-groups.csv'].open(encoding='utf-8',newline='') as stream:self.assertEqual(2,len(list(csv.DictReader(stream))))
            html=a['index.html'].read_text(encoding='utf-8')
            for text in ['No representative selected','Frozen original cohort','Conditional: one action withheld','download="comparison.csv"','data:text/csv;charset=utf-8;base64,','tabindex="0"','Inspect comparison source paths','Replay integrity, not scientific acceptance']:
                self.assertIn(text,html)
            self.assertNotIn('<script src=',html.lower())
            self.assertEqual(html.count('<script>'),1)
            self.assertIn((ROOT/'src/observation_receipt/claim-explorer.js').read_text(encoding='utf-8'),html)
            self.assertIn("connect-src 'none'",html)
            self.assertNotIn('id="timeline"',html)
            md=a['receipt.md'].read_text(encoding='utf-8')
            self.assertEqual(1,md.count('## Findings'))
            self.assertIn('Original preserved; conditional view compared',md)
            self.assertIn('percentage points',md)

    def test_html_escapes_case_labels_and_csv_blocks_formula_text(self):
        changed=copy.deepcopy(self.case)
        changed['identity_groups'][0]['label']='<script>alert(1)</script>'
        receipt=evaluate_case(changed,ROOT)
        with tempfile.TemporaryDirectory() as output:
            page=write_bundle(changed,receipt,Path(output))['index.html'].read_text(encoding='utf-8')
            self.assertIn('&lt;script&gt;',page)
            self.assertNotIn('<script>alert(1)</script>',page)
            self.assertEqual(page.count('<script>'),1)
        text=_csv_text(['label','delta'],[{'label':'=SUM(A1:A9)','delta':-15}])
        self.assertIn("'=SUM",text)
        self.assertIn(',-15',text)

    def test_real_identity_launcher_builds_the_new_view(self):
        with tempfile.TemporaryDirectory() as output:
            command=[sys.executable,'-B',str(ROOT/'run.py'),'demo','--case','identity','--output',output]
            done=subprocess.run(command,cwd=ROOT,capture_output=True,encoding='utf-8')
            self.assertEqual(0,done.returncode,done.stderr)
            self.assertTrue((Path(output)/'index.html').exists())
            self.assertEqual('0.3.0',json.loads((Path(output)/'receipt.json').read_text())['receipt_version'])

    def test_warning_grid_has_no_extra_cell_before_its_paragraph(self):
        with tempfile.TemporaryDirectory() as output:
            page=write_bundle(self.case,self.receipt,Path(output))['index.html'].read_text(encoding='utf-8')
            self.assertIn('<aside class="principle"><p>',page)
            self.assertNotIn('<aside class="principle"><div>',page)

    def test_unresolved_identity_card_titles_outcome_and_labels_evaluated_claim(self):
        before=copy.deepcopy(self.receipt)
        page=render_html(self.case,self.receipt)
        card=page.split('<article class="finding blocked"',1)[1].split('>',1)[1].split('</article>',1)[0]
        proposition=self.receipt['findings'][0]['proposition']
        self.assertIn('<h3>Physical identity remains unresolved</h3>',card)
        self.assertIn('<strong>Claim evaluated:</strong> '+proposition,card)
        self.assertNotIn('<h3>'+proposition+'</h3>',card)
        self.assertEqual(before,self.receipt)

    def test_failed_identity_integrity_is_not_titled_as_a_verified_assessment(self):
        changed=copy.deepcopy(self.case)
        changed['artifacts'][1]['sha256']='0'*64
        receipt=evaluate_case(changed,ROOT)
        page=render_html(changed,receipt)
        card=page.split('<article class="finding blocked"',1)[1].split('>',1)[1].split('</article>',1)[0]
        self.assertIn('BLOCKED_IDENTITY_INTEGRITY',card)
        self.assertIn('<h3>Identity evidence could not be verified</h3>',card)
        self.assertNotIn('<h3>Physical identity remains unresolved</h3>',card)
        self.assertIn('<strong>Claim evaluated:</strong>',card)

    def test_reference_only_urls_are_not_counted_as_verified_files(self):
        case=json.loads((ROOT/'cases/artemis-ii-flashes/case.json').read_text())
        receipt=evaluate_case(case,ROOT)
        with tempfile.TemporaryDirectory() as output:
            files=write_bundle(case,receipt,Path(output))
            html=files['index.html'].read_text(encoding='utf-8')
            md=files['receipt.md'].read_text(encoding='utf-8')
            self.assertIn('3 of 3 local artifact identities verified',html)
            self.assertIn('2 reference-only URLs, not byte verified',html)
            self.assertNotIn('5 of 5',html)
            self.assertIn('Local artifacts verified: **3 / 3**',md)
            self.assertTrue(receipt['pass'])

    def test_real_invalid_build_writes_no_bundle(self):
        changed=copy.deepcopy(self.case)
        changed['conditional_comparisons'][0]['metrics'][0]['pointer']='/missing'
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'case.json'
            source.write_text(json.dumps(changed),encoding='utf-8')
            output=root/'output'
            done=subprocess.run([sys.executable,'-B',str(ROOT/'run.py'),'build',str(source),'--root',str(ROOT),'--output',str(output)],capture_output=True,encoding='utf-8')
            self.assertEqual(2,done.returncode)
            self.assertIn('does not resolve',done.stderr)
            self.assertFalse(output.exists())

    def test_owned_cli_uses_utf8_under_hostile_output_encoding(self):
        changed=copy.deepcopy(self.case)
        changed['title']='Caf\u00e9 comparison'
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'case.json'
            source.write_text(json.dumps(changed),encoding='utf-8')
            done=subprocess.run([sys.executable,'-B',str(ROOT/'run.py'),'build',str(source),'--root',str(ROOT),'--output',str(root/'output')],env={**os.environ,'PYTHONIOENCODING':'ascii'},capture_output=True,encoding='utf-8')
            self.assertEqual(0,done.returncode,done.stderr)
            self.assertIn('Caf\u00e9',done.stdout)

    def test_schema_rule_set_and_local_references_are_structurally_complete(self):
        schema=json.loads((ROOT/'schemas/observation-receipt-v0.3.schema.json').read_text())
        self.assertEqual(RULE_KINDS,set(schema['$defs']['claim']['properties']['rule']['properties']['kind']['enum']))
        def visit(value):
            if isinstance(value,dict):
                if '$ref' in value:
                    self.assertTrue(value['$ref'].startswith('#/'))
                    pointer(schema,value['$ref'][1:])
                for child in value.values():visit(child)
            elif isinstance(value,list):
                for child in value:visit(child)
        visit(schema)


if __name__=='__main__':unittest.main()
