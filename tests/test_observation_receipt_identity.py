"""Include the portable extension checks in the Testbed's regression gate."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src import prepare_observation_identity_demo as preparation

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'observation-receipt/tests/test_identity_comparisons.py'
SPEC = importlib.util.spec_from_file_location('observation_receipt_identity_tests', PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IdentityFixturePreparationTests(unittest.TestCase):
    def test_all_three_prepared_files_replay_the_exact_parent_receipts(self):
        files=preparation.prepare()
        self.assertEqual(3,len(files))
        for name,data in files.items():self.assertEqual(data,(preparation.OWNER/name).read_bytes())
        self.assertEqual((ROOT/'paper-review/downstream-sensitivity/result.json').read_bytes(),files['sources/downstream-sensitivity.json'])
        excerpt=json.loads(files['sources/metadata-family-excerpt.json'])
        self.assertEqual('IDENTITY_ALTERNATIVES_ABSTAIN',excerpt['family']['status'])
        self.assertEqual(['art002e009301','art002e015991'],excerpt['alternatives'])

    def test_owner_edit_blocks_all_new_fixture_writes(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(preparation,'OWNER',Path(folder)):
            path=Path(folder)/'case.json'
            path.write_bytes(b'owner edit')
            with self.assertRaises(ValueError):preparation.run('--write')
            self.assertEqual(b'owner edit',path.read_bytes())
            self.assertFalse((Path(folder)/'sources').exists())


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([tests,loader.loadTestsFromModule(MODULE)])
