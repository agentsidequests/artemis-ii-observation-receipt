"""Run portable robustness checks in the owning Testbed regression."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src import prepare_observation_robustness_demo as P

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('portable_robustness_tests', ROOT / 'observation-receipt/tests/test_robustness.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PreparationTests(unittest.TestCase):
    def test_prepared_files_match_exact_scientific_parents(self):
        for name, payload in P.prepare().items():
            self.assertEqual(payload, (P.OWNER / name).read_bytes())

    def test_owner_edit_prevents_partial_fixture_write(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(P, 'OWNER', Path(folder)):
            (Path(folder) / 'case.json').write_bytes(b'owner edit')
            with self.assertRaises(ValueError): P.run('--write')
            self.assertFalse((Path(folder) / 'sources').exists())

    def test_historical_packager_cannot_ship_an_incomplete_extended_cli(self):
        self.skipTest('Private historical packager is not exported or exposed as a public command.')


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([tests, loader.loadTestsFromModule(MODULE)])
