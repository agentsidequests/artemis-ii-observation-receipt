from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11m_independent_receipt_audit import (  # noqa: E402
    audit_stage11m,
    partition_for,
    verify_with_mutations,
)


class Stage11MIndependentReceiptAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = audit_stage11m(ROOT)

    def test_standalone_audit_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual(
            "VERIFIED_IMPLEMENTATION_DIVERSE_SPLIT_RECEIPT_AUDIT",
            self.result["evidence_state"],
        )
        self.assertEqual("partial_implementation_diverse", self.result["oracle_independence"])

    def test_verifier_imports_no_stage11l_module(self) -> None:
        path = ROOT / "src/stage11m_independent_receipt_audit.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        self.assertFalse([name for name in imported if name.startswith("stage11l")])

    def test_independent_hash_threshold_golden_cases(self) -> None:
        algorithm = {
            "seed": "consumer-golden-v1",
            "train_numerator": 4,
            "train_denominator": 5,
        }
        self.assertEqual("train", partition_for("product-0001", algorithm))
        self.assertEqual("test", partition_for("product-0004", algorithm))
        self.assertEqual("train", partition_for("action-0007", algorithm))

    def test_recomputed_metrics_match_frozen_receipt(self) -> None:
        policies = self.result["policies"]
        self.assertEqual(1937, policies["product_key"]["crossing_action_groups"])
        self.assertEqual(0, policies["action_key"]["crossing_action_groups"])
        self.assertEqual(157, policies["action_key"]["crossing_temporal_5s_groups"])
        self.assertEqual(1216, policies["action_key"]["actions_in_crossing_temporal_5s_groups"])
        self.assertEqual(0, policies["temporal_5s_key"]["crossing_action_groups"])
        self.assertEqual(0, policies["temporal_5s_key"]["crossing_temporal_5s_groups"])

    def test_every_mutation_fails_at_its_required_checks(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertEqual(11, len(result["hard_negatives"]))
        for mutation in result["hard_negatives"].values():
            self.assertTrue(mutation["rejected"])
            for check in mutation["required_failed_checks"]:
                self.assertIn(check, mutation["failed_checks"])

    def test_claim_ceiling_preserves_partial_independence(self) -> None:
        ceiling = self.result["claim_ceiling"].casefold()
        for phrase in (
            "independence remains partial",
            "independent human replication",
            "scientific task validity",
            "observed leakage",
            "operational sufficiency for nasa or pds",
            "global novelty",
        ):
            self.assertIn(phrase, ceiling)

    def test_result_opens_no_pixels(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_saved_result_matches_live_audit_when_present(self) -> None:
        path = ROOT / "results/stage11m-result.json"
        if not path.exists():
            self.skipTest("Stage 11M result has not been rendered yet.")
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(saved["pass"])
        self.assertEqual(self.result["policies"], saved["policies"])
        self.assertEqual(self.result["verifier_source_sha256"], saved["verifier_source_sha256"])


if __name__ == "__main__":
    unittest.main()
