from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10a_metadata_integrity import load_json  # noqa: E402
from stage11l_split_receipt_canary import (  # noqa: E402
    build_assignment_rows,
    build_receipt,
    partition_for,
    render_assignments,
    verify_stage11l,
    verify_with_mutations,
)


class Stage11LSplitReceiptCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11l(ROOT)

    def test_receipt_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_DETERMINISTIC_SPLIT_RECEIPT_CANARY", self.result["evidence_state"])

    def test_hash_threshold_has_fixed_golden_cases(self) -> None:
        algorithm = {
            "seed": "golden",
            "train_numerator": 4,
            "train_denominator": 5,
        }
        expected = {}
        for key in ("alpha", "beta", "gamma", "delta"):
            digest = hashlib.sha256(f"golden\0{key}".encode("utf-8")).digest()
            value = int.from_bytes(digest[:8], "big")
            expected[key] = "train" if value < ((1 << 64) * 4) // 5 else "test"
        self.assertEqual(
            {"alpha": "train", "beta": "test", "gamma": "train", "delta": "train"},
            expected,
        )
        self.assertEqual(expected, {key: partition_for(key, algorithm) for key in expected})

    def test_policies_discriminate_relationship_boundaries(self) -> None:
        policies = self.result["policies"]
        self.assertEqual(1937, policies["product_key"]["crossing_action_groups"])
        self.assertEqual(0, policies["action_key"]["crossing_action_groups"])
        self.assertEqual(157, policies["action_key"]["crossing_temporal_5s_groups"])
        self.assertEqual(1216, policies["action_key"]["actions_in_crossing_temporal_5s_groups"])
        self.assertEqual(0, policies["temporal_5s_key"]["crossing_action_groups"])
        self.assertEqual(0, policies["temporal_5s_key"]["crossing_temporal_5s_groups"])

    def test_receipt_names_validator_completeness_and_assignment_identity(self) -> None:
        receipt = json.loads(
            (ROOT / "results" / "stage11l-split-receipt.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {"name": "stage11l_split_receipt_canary", "version": "1.0.0"},
            receipt["validator"],
        )
        self.assertEqual(0, receipt["unresolved_relationships"])
        self.assertEqual(0, receipt["unknown_assignment_rows"])
        self.assertEqual(self.result["assignment_sha256"], receipt["assignment_artifact"]["sha256"])

    def test_receipt_metrics_come_from_the_bound_assignment_bytes(self) -> None:
        spec = load_json(ROOT / "spec/stage11l.json")
        rows = build_assignment_rows(ROOT, spec)
        mutated = [dict(row) for row in rows]
        current = mutated[0]["action_key_partition"]
        mutated[0]["action_key_partition"] = "test" if current == "train" else "train"
        mutated_bytes = render_assignments(mutated)
        receipt = build_receipt(ROOT, spec, mutated_bytes)

        self.assertEqual(
            hashlib.sha256(mutated_bytes).hexdigest(),
            receipt["assignment_artifact"]["sha256"],
        )
        self.assertNotEqual(self.result["assignment_sha256"], receipt["assignment_artifact"]["sha256"])
        self.assertEqual(1, receipt["policies"]["action_key"]["crossing_action_groups"])

    def test_claim_ceiling_keeps_canary_narrow(self) -> None:
        ceiling = self.result["claim_ceiling"].casefold()
        for phrase in (
            "semantic scene",
            "valid split for a scientific task",
            "real pipeline leaked information",
            "guarantees independence",
            "model performance changes",
            "operationally sufficient for nasa or pds",
            "globally novel",
        ):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
