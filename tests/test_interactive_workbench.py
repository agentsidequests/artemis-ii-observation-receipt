"""Interaction representation, receipt conservation and zero-dependency assets."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'observation-receipt'
sys.path.insert(0, str(APP / 'src'))
from observation_receipt.evaluator import evaluate_case
from observation_receipt.exporters import write_bundle
from observation_receipt import robustness


class InteractiveWorkbenchTests(unittest.TestCase):
    def test_pure_interactions_and_source_locators(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node needed only for build/interaction logic tests, not delivered viewers.')
        result = subprocess.run([node, str(ROOT/'presentation/test-workbench.cjs'), str(ROOT)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        checks = json.loads(result.stdout)
        self.assertEqual(checks['saved_scenarios'], 96)
        self.assertGreater(checks['view_roundtrips_and_source_pointers'], 40)

    def test_all_three_receipts_keep_findings_and_nonvisual_bytes(self):
        for name in ['artemis-ii-flashes', 'artemis-ii-identity', 'artemis-ii-identity-confirmed']:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as folder:
                case = json.loads((APP/'cases'/name/'case.json').read_bytes())
                receipt = evaluate_case(case, APP)
                before = json.dumps(receipt, sort_keys=True)
                files = write_bundle(case, receipt, Path(folder))
                page = files['index.html'].read_text(encoding='utf-8')
                self.assertEqual(json.dumps(receipt, sort_keys=True), before)
                self.assertEqual(json.loads(files['receipt.json'].read_bytes())['findings'], receipt['findings'])
                self.assertEqual(page.count('data-claim-card='), len(receipt['findings']))
                self.assertIn('claim-empty-reset', page)
                self.assertIn('No saved finding matches', page)
                self.assertIn('integrity state are unchanged', page)
                self.assertIn('<noscript>', page)
                self.assertIn("connect-src 'none'", page)
                self.assertNotIn('<script src=', page)
                for item in receipt['findings']:
                    if item['status'].startswith(('BLOCKED','REFUTED')) and item['rule_kind']!='identity_resolution_gate':
                        self.assertNotIn('<h3>'+item['proposition']+'</h3>',page)
                if name=='artemis-ii-flashes':
                    self.assertIn('Claim evaluated, not established:',page)

    def test_robustness_atlas_keeps_exact_analysis(self):
        with tempfile.TemporaryDirectory() as folder:
            receipt = robustness.evaluate(json.loads((APP/'cases/artemis-ii-robustness/case.json').read_bytes()), APP)
            before = json.dumps(receipt, sort_keys=True)
            files = robustness.write_bundle(receipt, Path(folder))
            self.assertEqual(json.dumps(receipt, sort_keys=True), before)
            self.assertEqual(json.loads(files['receipt.json'].read_bytes())['analysis'], receipt['analysis'])
            page = files['index.html'].read_text(encoding='utf-8')
            self.assertIn('assumption-atlas', page)
            self.assertIn('No numeric difference is computed', page)
            self.assertNotIn('__ATLAS_SCRIPT__', page)
            self.assertIn('There is no interpolation between cells', page)
            self.assertIn('<details id="assumption-atlas"',page)

    def test_assets_shipped_and_no_network_or_identity_expansion(self):
        project = (APP/'pyproject.toml').read_text(encoding='utf-8')
        for extension in ['*.html', '*.css', '*.js']:
            self.assertIn(extension, project)
        for name in ['presentation/workbench.js', 'observation-receipt/src/observation_receipt/assumption-atlas.js', 'observation-receipt/src/observation_receipt/claim-explorer.js']:
            text = (ROOT/name).read_text(encoding='utf-8')
            for banned in ['fetch(', 'localStorage', 'XMLHttpRequest', chr(0x2014)]:
                self.assertNotIn(banned, text)
        template = (ROOT/'presentation/index.template.html').read_text(encoding='utf-8')
        for label in ['saved-view-link', 'view-receipt', 'source-search', 'comparison-rows']:
            self.assertIn('id="'+label+'"', template)


if __name__ == '__main__':
    unittest.main()
