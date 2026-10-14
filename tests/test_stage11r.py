from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11r_hierarchical_test_isolation import (  # noqa: E402
    analyze_assignments,
    load_rows,
    verify_stage11r,
)


class Stage11RHierarchicalIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage11r(ROOT)
        cls.rows = load_rows(ROOT / "results/stage11l-split-assignments.csv")

    def test_stage_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["checks"])
        self.assertEqual(
            "VERIFIED_HIERARCHICAL_TEST_ISOLATION_AUDIT",
            self.result["evidence_state"],
        )
        self.assertTrue(all(self.result["checks"].values()))

    def test_test_partition_has_exact_three_bin_decomposition(self) -> None:
        metrics = self.result["structural_isolation"]
        self.assertEqual(4511, metrics["test_products"])
        self.assertEqual(4307, metrics["capture_linked_test_products"])
        self.assertEqual(204, metrics["action_only_linked_test_products"])
        self.assertEqual(0, metrics["action_isolated_test_products"])
        self.assertEqual(
            metrics["test_products"],
            metrics["capture_linked_test_products"]
            + metrics["action_only_linked_test_products"]
            + metrics["action_isolated_test_products"],
        )
        self.assertEqual(3679, metrics["test_visible_capture_groups"])
        self.assertEqual(3611, metrics["capture_linked_test_capture_groups"])
        self.assertEqual(68, metrics["capture_isolated_test_capture_groups"])
        self.assertEqual(1937, metrics["test_visible_action_groups"])
        self.assertEqual(0, metrics["action_isolated_test_action_groups"])

    def test_full_assignment_crossing_metrics_recompute(self) -> None:
        metrics = self.result["structural_isolation"]
        self.assertEqual(1937, metrics["crossing_action_groups"])
        self.assertEqual(20601, metrics["products_in_crossing_action_groups"])
        self.assertAlmostEqual(
            0.9028398632658428,
            metrics["share_all_products_in_crossing_actions"],
        )

    def test_relationship_mutations_change_the_decomposition(self) -> None:
        baseline = analyze_assignments(self.rows)
        mutated = copy.deepcopy(self.rows)
        target = next(
            row
            for row in mutated
            if row["product_key_partition"] == "test"
            and row["capture_identity"]
            in {
                train_row["capture_identity"]
                for train_row in mutated
                if train_row["product_key_partition"] == "train"
            }
        )
        target["capture_identity"] = "stage11r-mutated-capture"
        action_only = analyze_assignments(mutated)
        self.assertEqual(
            baseline["capture_linked_test_products"] - 1,
            action_only["capture_linked_test_products"],
        )
        self.assertEqual(
            baseline["action_only_linked_test_products"] + 1,
            action_only["action_only_linked_test_products"],
        )

        target["action_id"] = "stage11r-mutated-action"
        isolated = analyze_assignments(mutated)
        self.assertEqual(1, isolated["action_isolated_test_products"])

    def test_duplicate_product_identity_is_observable(self) -> None:
        mutated = self.rows + [dict(self.rows[0])]
        metrics = analyze_assignments(mutated)
        self.assertNotEqual(metrics["rows"], metrics["unique_product_ids"])

    def test_claim_ceiling_rejects_harm_and_validity_inference(self) -> None:
        ceiling = self.result["claim_ceiling"].casefold()
        for phrase in (
            "pixel similarity",
            "statistical dependence",
            "observed leakage",
            "performance inflation",
            "scientific-task invalidity",
            "nasa acceptance",
            "global novelty",
        ):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_and_no_em_dash(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes_opened"])
        for relative in (
            "spec/stage11r.json",
            "src/stage11r_hierarchical_test_isolation.py",
            "tests/test_stage11r.py",
        ):
            self.assertNotIn(chr(0x2014), (ROOT / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
