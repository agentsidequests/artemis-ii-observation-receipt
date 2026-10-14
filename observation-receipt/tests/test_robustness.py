"""Portable consumer parity, hostile inputs, exports and the real CLI."""
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'src'))
from observation_receipt import robustness as R


class RobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = json.loads((APP / 'cases/artemis-ii-robustness/case.json').read_bytes())
        cls.receipt = R.evaluate(cls.case, APP)

    def scenario(self, unit='all_representation_bytes', population='frozen_nonblank_subset', budget=0):
        return next(b for b in self.receipt['analysis']['reassignment_sensitivity'] if
                    (b['unit'], b['population'], b['reassignment_budget']) == (unit, population, budget))

    def test_saved_controls_have_exactly_96_distinct_scenarios(self):
        self.assertEqual(96, len(self.receipt['analysis']['reassignment_sensitivity']))
        self.assertEqual(7606, len(self.receipt['fields']))
        self.assertEqual(3413, self.receipt['analysis']['partition']['recorded_fields'])

    def test_47_48_crossing_uses_exact_fixed_denominator(self):
        before, after = self.scenario(budget=47), self.scenario(budget=48)
        self.assertEqual(781104206358, after['total_weight'])
        self.assertEqual(before['total_weight'], after['total_weight'])
        self.assertEqual(390397190239, after['lower']['numerator'])
        self.assertGreater(2 * before['lower']['numerator'], before['total_weight'])
        self.assertLessEqual(2 * after['lower']['numerator'], after['total_weight'])
        self.assertEqual(48, len(after['lower_reassigned_ids']))

    def test_full_cohort_and_nonblank_are_not_substituted(self):
        full, selected = self.scenario(population='full_cohort'), self.scenario()
        self.assertGreater(full['blank_weight'], 0)
        self.assertEqual(0, selected['blank_weight'])
        self.assertGreater(full['total_weight'], selected['total_weight'])
        self.assertLess(full['lower']['percentage'], 50)
        self.assertGreater(full['upper']['percentage'], 50)

    def test_minimal_witness_and_equal_cost_completion_remain_separate(self):
        unit = self.receipt['analysis']['units'][-1]
        self.assertEqual(48, unit['majority_sensitivity']['minimum_fields_to_lose_strict_majority'])
        self.assertEqual(3747, unit['completion_budgets']['5pp']['minimum_fields_resolved_equal_field_cost'])
        self.assertFalse(unit['completion_budgets']['5pp']['real_resolution_or_cost_optimality'])

    def test_products_are_three_representations_not_independent_captures(self):
        a = self.scenario(unit='exposure_fields', population='full_cohort')
        b = self.scenario(unit='products', population='full_cohort')
        self.assertEqual(3 * a['total_weight'], b['total_weight'])
        self.assertEqual(a['lower']['share'], b['lower']['share'])

    def test_source_locators_resolve_exact_original_csv_rows(self):
        source = (APP / self.case['sources']['manifest']['path']).read_text(encoding='utf-8')
        rows = list(csv.DictReader(io.StringIO(source)))
        for identifier in self.scenario(budget=48)['lower_reassigned_ids']:
            field = self.receipt['fields'][identifier]
            for collection, product in field['products'].items():
                row = rows[product['row'] - 2]
                self.assertEqual(identifier, row['capture_identity'])
                self.assertEqual(collection, row['collection_id'])
                self.assertEqual(product['id'], row['product_id'])
                self.assertEqual(product['bytes'], int(row['archive_size_bytes']))

    def test_source_integrity_and_root_escape_fail_closed(self):
        for name in ['contract', 'result', 'manifest']:
            case = copy.deepcopy(self.case)
            case['sources'][name]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
                R.evaluate(case, APP)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            R.read_artifact({'path': '../outside', 'bytes': 1, 'sha256': '0' * 64}, APP)

    def test_unknown_or_boolean_controls_rejected(self):
        for key, values in {'budget': [True, -1, 49, 48.0], 'unit': ['physical_flux'], 'population': ['corrected_cohort']}.items():
            for value in values:
                case = copy.deepcopy(self.case)
                case['defaults'][key] = value
                with self.assertRaises(ValueError):
                    R.evaluate(case, APP)

    def test_saved_scenario_mutations_cannot_launder_a_receipt(self):
        fields = self.receipt['fields']
        for mutation in [lambda b: b['lower'].update(numerator=True),
                         lambda b: b.update(total_weight=b['total_weight'] + 1),
                         lambda b: b.update(extrema_are_separate_witnesses=False),
                         lambda b: b['lower_reassigned_ids'].append('not-a-source-key')]:
            result = copy.deepcopy(self.receipt['analysis'])
            mutation(result['reassignment_sensitivity'][0])
            with self.assertRaises(ValueError):
                R.validate_accounting(result, fields)

    def test_duplicate_missing_or_boolean_scenario_rejected(self):
        for mode in ['duplicate', 'missing', 'bool']:
            result = copy.deepcopy(self.receipt['analysis'])
            panel = result['reassignment_sensitivity']
            if mode == 'duplicate': panel[-1] = panel[0]
            elif mode == 'missing': panel.pop()
            else: panel[0]['reassignment_budget'] = False
            with self.assertRaises(ValueError): R.validate_accounting(result, self.receipt['fields'])

    def test_predecessor_and_completion_witness_drift_rejected(self):
        for mode in ['majority', 'completion', 'cost']:
            result = copy.deepcopy(self.receipt['analysis'])
            summary = result['units'][-1]
            if mode == 'majority': summary['majority_sensitivity']['predecessor']['numerator'] -= 1
            elif mode == 'completion': summary['completion_budgets']['5pp']['resolved_ids'].pop()
            else: summary['completion_budgets']['5pp']['real_resolution_or_cost_optimality'] = True
            with self.assertRaises(ValueError): R.validate_accounting(result, self.receipt['fields'])

    def test_manifest_duplicate_incomplete_and_conflicting_rows_rejected(self):
        header = 'product_id,capture_identity,collection_id,archive_size_bytes,action_id,activity_id,target_id\n'
        rows = ['a,k,data_source,1,act,activity,Sunset\n', 'b,k,data_raw,2,act,activity,Sunset\n', 'c,k,data_processed,3,act,activity,Sunset\n']
        self.assertEqual(6, R.fields_from_manifest((header + ''.join(rows)).encode())['k']['weights']['all_representation_bytes'])
        for bad in [rows[:2], rows + [rows[0]], [rows[0], rows[1].replace('Sunset','Earth'), rows[2]], [rows[0].replace(',1,',',0,'), *rows[1:]]]:
            with self.assertRaises(ValueError): R.fields_from_manifest((header + ''.join(bad)).encode())

    def test_source_descriptors_are_strict(self):
        descriptor = self.case['sources']['result']
        for change in [{'bytes': True}, {'sha256': 'a' * 63}, {'path': ''}, {'extra': 'literal-data'}]:
            with self.assertRaises(ValueError): R.read_artifact({**descriptor, **change}, APP)

    def test_case_repin_alone_cannot_qualify_a_changed_snapshot(self):
        case = copy.deepcopy(self.case)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, artifact in case['sources'].items():
                data = (APP / artifact['path']).read_bytes()
                if name == 'contract': data += b'\n'
                path = root / (name + '.data')
                path.write_bytes(data)
                artifact.update(path=path.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            with self.assertRaisesRegex(ValueError, 'case hash alone is insufficient'):
                R.evaluate(case, root)

    def test_exports_are_deterministic_and_source_bound(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            R.write_bundle(self.receipt, output)
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            R.write_bundle(self.receipt, output)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
            manifest = json.loads(before['manifest.json'])
            for record in manifest['files']:
                self.assertEqual(record['sha256'], hashlib.sha256(before[record['path']]).hexdigest())
            endpoints = list(csv.DictReader(io.StringIO(before['bound-endpoints.csv'].decode())))
            self.assertEqual(192, len(endpoints))
            self.assertEqual(22818, len(list(csv.DictReader(io.StringIO(before['source-fields.csv'].decode())))))

    def test_viewer_distinctions_keyboard_structure_and_no_external_resources(self):
        page = Path(R.__file__).with_name('robustness-viewer.html').read_text(encoding='utf-8')
        for phrase in ['not an error finding', 'separate realizable witnesses', 'statistical sample sizes', 'at build time', '47', '48', 'at most r', 'r = 0', 'first 100', 'without the search filter']:
            self.assertIn(phrase, page.lower())
        for identifier in ['unit', 'population', 'budget', 'try-crossing', 'reset', 'witness', 'completion', 'search', 'source-record']:
            self.assertIn('id="' + identifier + '"', page)
        self.assertIn('tabindex="0" role="region"', page)
        self.assertIn(':focus-visible', page)
        self.assertNotIn('\u2014', page)
        self.assertNotIn('<script src=', page)
        self.assertNotIn('<link ', page)

    def test_cli_builds_separate_case_and_invalid_sources_write_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'bundle'
            command = [sys.executable, '-B', str(APP / 'run.py'), 'demo', '--case', 'robustness', '--output', str(output)]
            completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue((output / 'index.html').is_file())
            bad = copy.deepcopy(self.case)
            bad['sources']['result']['sha256'] = '0' * 64
            path = Path(folder) / 'bad.json'
            path.write_bytes(R.serialize(bad))
            failed = Path(folder) / 'failed'
            completed = subprocess.run([sys.executable, '-B', str(APP / 'run.py'), 'build', str(path), '--root', str(APP), '--output', str(failed)], capture_output=True)
            self.assertEqual(2, completed.returncode)
            self.assertIn(b'Source integrity mismatch', completed.stderr)
            self.assertFalse(failed.exists())

    def test_schema_inventory_matches_runtime_without_external_validator_claim(self):
        schema = json.loads((APP / 'schemas/tag-weight-case-v1.schema.json').read_bytes())
        self.assertEqual(set(self.case), set(schema['required']))
        self.assertFalse(schema['additionalProperties'])
        self.assertEqual(list(R.UNITS), schema['properties']['defaults']['properties']['unit']['enum'])
        self.assertEqual(list(R.BUDGETS), schema['properties']['defaults']['properties']['budget']['enum'])


if __name__ == '__main__': unittest.main()
