"""Changed-byte and unsafe-path tests for the shipped inventory, not scientific acceptance."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.verify_public_package import validate_inventory


class PublicPackageBoundaryTests(unittest.TestCase):
    def fixture(self, root):
        payload = b'owned evidence\n'
        (root / 'evidence.txt').write_bytes(payload)
        return {'files': [{'path': 'evidence.txt', 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}]}

    def test_exact_inventory_accepts_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.fixture(root)
            errors, names = validate_inventory(root, manifest)
            self.assertEqual([], errors)
            self.assertEqual({'evidence.txt'}, names)

    def test_changed_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.fixture(root)
            (root / 'evidence.txt').write_bytes(b'changed evidence\n')
            errors, _ = validate_inventory(root, manifest)
            self.assertEqual(['Package byte identity mismatch: evidence.txt'], errors)

    def test_parent_traversal_duplicate_and_absolute_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.fixture(root)
            record = manifest['files'][0]
            manifest['files'].extend([dict(record), {**record, 'path': '../outside.txt'}, {**record, 'path': '/outside.txt'}, {**record, 'path': 'C:/outside.txt'}])
            errors, _ = validate_inventory(root, manifest)
            self.assertEqual(4, len(errors))
            self.assertTrue(all(error.startswith('Unsafe or duplicate package path: ') for error in errors))


if __name__ == '__main__':
    unittest.main()
