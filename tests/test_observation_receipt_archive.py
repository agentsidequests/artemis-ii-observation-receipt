from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ObservationReceiptArchiveTests(unittest.TestCase):
    def test_git_archive_preserves_prototype_result_pins_and_current_proposition(self) -> None:
        names = [
            'prototype/observation_receipt.py',
            'examples/artemis-ii-flashes.observation-receipt.json',
            'results/stage11n-result.json',
            'results/stage11p-overlap-pixel-screen.json',
            'results/stage11q-injection-recovery.json',
            'results/observation-receipt-artemis-fixture.json',
        ]
        completed = subprocess.run(
            ['git', 'archive', '--format=tar', 'HEAD', '--', *names],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr.decode(errors='replace'))
        with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode='r:') as archive, tempfile.TemporaryDirectory() as folder:
            recovered = Path(folder)
            for name in names:
                member = archive.extractfile(name)
                self.assertIsNotNone(member, name)
                target = recovered / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(member.read())
            spec = importlib.util.spec_from_file_location('archived_prototype', recovered / names[0])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            case = json.loads((recovered / names[1]).read_bytes())
            receipt = module.evaluate(case, recovered)
            self.assertTrue(receipt['pass'], receipt['checks'])
            self.assertIn('background-photo epoch', receipt['findings'][1]['proposition'])
            self.assertEqual(json.loads((recovered / names[-1]).read_bytes()), receipt)

    def test_git_archive_preserves_fixture_identities(self) -> None:
        completed = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD:observation-receipt"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr.decode(errors="replace"))

        with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
            case_member = archive.extractfile("cases/artemis-ii-flashes/case.json")
            self.assertIsNotNone(case_member)
            case = json.loads(case_member.read().decode("utf-8"))
            for artifact in case["artifacts"]:
                if not artifact.get("path"):
                    continue
                member = archive.extractfile(artifact["path"])
                self.assertIsNotNone(member, artifact["path"])
                payload = member.read()
                self.assertEqual(artifact["bytes"], len(payload), artifact["path"])
                self.assertEqual(artifact["sha256"], hashlib.sha256(payload).hexdigest(), artifact["path"])


if __name__ == "__main__":
    unittest.main()
