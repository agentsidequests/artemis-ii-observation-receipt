"""Small-model exhaustive oracles and frozen-source replay for the follow-on."""
from __future__ import annotations

import copy
import csv
import io
import itertools
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from src import tag_weight_robustness as m


def field(identity, target, weight):
    return m.Field(identity, target, "action-" + identity, "activity", weight, weight, weight)


def enumerate_memberships(fields, budget, include_blanks=True):
    selected = [f for f in fields if include_blanks or f.target]
    total = sum(f.source_bytes for f in selected)
    values = []
    for bits in itertools.product((0, 1), repeat=len(selected)):
        changed = sum(bit != (f.target == "Sunset") for bit, f in zip(bits, selected) if f.target)
        if changed <= budget:
            values.append(Fraction(sum(bit * f.source_bytes for bit, f in zip(bits, selected)), total))
    return min(values), max(values)


def manifest_bytes():
    columns = ["product_id", "collection_id", "capture_identity", "archive_size_bytes", "target_id",
               "action_id", "activity_id", "camera_serial", "exposure_position", "exposures_in_action"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for i, collection in enumerate(m.COLLECTIONS):
        writer.writerow(dict(zip(columns, (f"product-{i}", collection, "capture-1", 10 + i, "Sunset",
                                           "action", "activity", "camera", 1, 1))))
    return stream.getvalue().encode()


class MathematicalOracleTests(unittest.TestCase):
    def test_hand_computed_completion_and_reassignment(self):
        fields = [field("a", "Sunset", 4), field("b", "Moon", 2), field("c", "", 3), field("d", "", 1)]
        b = m.bounds(fields, "data_source_bytes", "Sunset")
        self.assertEqual((b["lower"]["numerator"], b["upper"]["numerator"], b["total_weight"]), (4, 8, 10))
        b = m.bounds(fields, "data_source_bytes", "Sunset", 1)
        self.assertEqual((b["lower"]["numerator"], b["upper"]["numerator"]), (0, 10))
        self.assertEqual(b["lower_reassigned_ids"], ["a"])
        self.assertEqual(b["upper_reassigned_ids"], ["b"])

    def test_exhaustive_membership_extrema(self):
        for states in itertools.product(("Sunset", "Moon", ""), repeat=4):
            for weights in ((1, 1, 1, 1), (1, 2, 7, 3), (11, 1, 2, 5)):
                fields = [field(str(i), t, w) for i, (t, w) in enumerate(zip(states, weights))]
                for budget in range(5):
                    for include in (True, False):
                        if not include and not any(states):
                            continue
                        oracle = enumerate_memberships(fields, budget, include)
                        b = m.bounds(fields, "data_source_bytes", "Sunset", budget, include)
                        actual = (Fraction(b["lower"]["numerator"], b["total_weight"]),
                                  Fraction(b["upper"]["numerator"], b["total_weight"]))
                        self.assertEqual(actual, oracle, (states, weights, budget, include))

    def test_exhaustive_minimum_majority_subsets(self):
        for weights in itertools.product((1, 2, 5), repeat=4):
            fields = [field(str(i), "Sunset", w) for i, w in enumerate(weights)] + [field("other", "Moon", 3)]
            witness = m.majority_witness(fields, "data_source_bytes", "Sunset")
            total = sum(weights) + 3
            feasible = [len(subset) for k in range(5) for subset in itertools.combinations(weights, k)
                        if 2 * (sum(weights) - sum(subset)) <= total]
            self.assertEqual(witness["minimum_fields_to_lose_strict_majority"], min(feasible))

    def test_exhaustive_minimum_completion_subsets(self):
        for weights in itertools.product((1, 2, 5), repeat=4):
            fields = [field(str(i), "", w) for i, w in enumerate(weights)] + [field("known", "Moon", 7)]
            for n, d in ((0, 1), (1, 10), (1, 4), (1, 2), (1, 1)):
                budget = m.completion_budget(fields, "data_source_bytes", n, d)
                total = sum(weights) + 7
                feasible = [len(subset) for k in range(5) for subset in itertools.combinations(weights, k)
                            if (sum(weights) - sum(subset)) * d <= total * n]
                self.assertEqual(budget["minimum_fields_resolved_equal_field_cost"], min(feasible))

    def test_exact_equality_loses_strict_majority(self):
        fields = [field("a", "Sunset", 4), field("b", "Sunset", 1), field("c", "Moon", 3)]
        witness = m.majority_witness(fields, "data_source_bytes", "Sunset")
        self.assertEqual(witness["minimum_fields_to_lose_strict_majority"], 1)
        self.assertLessEqual(2 * witness["after"]["numerator"], witness["denominator"])
        fields = [field("a", "Sunset", 4), field("b", "Moon", 4)]
        self.assertEqual(m.majority_witness(fields, "data_source_bytes", "Sunset")["minimum_fields_to_lose_strict_majority"], 0)

    def test_equal_weights_reproduce_field_budget(self):
        fields = [field(str(i), "" if i < 4193 else "Moon", 1) for i in range(7606)]
        for n, d, expected in ((1, 10, 3433), (1, 20, 3813), (1, 100, 4117)):
            self.assertEqual(m.completion_budget(fields, "exposure_fields", n, d)["minimum_fields_resolved_equal_field_cost"], expected)

    def test_order_invariance_and_deterministic_ties(self):
        fields = [field("b", "Sunset", 3), field("a", "Sunset", 3), field("z", "", 2), field("m", "Moon", 1)]
        baseline = m.bounds(fields, "data_source_bytes", "Sunset", 1)
        for permutation in itertools.permutations(fields):
            self.assertEqual(m.bounds(list(permutation), "data_source_bytes", "Sunset", 1), baseline)
        self.assertEqual(baseline["lower_reassigned_ids"], ["a"])

    def test_invalid_values_and_duplicate_identity_rejected(self):
        fields = [field("a", "Sunset", 1)]
        for invalid in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                m.bounds(fields, "data_source_bytes", "Sunset", invalid)
        for value in (0, -1, True, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                m.bounds([field("a", "Sunset", value)], "data_source_bytes", "Sunset")
        with self.assertRaises(ValueError):
            m.bounds(fields + fields, "data_source_bytes", "Sunset")
        with self.assertRaises(ValueError):
            m.completion_budget(fields, "data_source_bytes", 1, 0)
        with self.assertRaises(ValueError):
            m.bounds(fields, "unknown", "Sunset")
        with self.assertRaises(ValueError):
            m.bounds([field("a", "", 1)], "data_source_bytes", "Sunset", include_blanks=False)

    def test_heterogeneous_cost_hard_negative(self):
        # Remove at least 6 of 13 unknown weight: weight 6/cost 100 versus two weight 4+3/cost 1+1.
        # Largest weight is cardinality-optimal but not total-cost-optimal.
        fields = [field("heavy", "", 6), field("small-a", "", 4), field("small-b", "", 3), field("known", "Moon", 7)]
        b = m.completion_budget(fields, "data_source_bytes", 7, 20)
        self.assertEqual(b["resolved_ids"], ["heavy"])
        self.assertLess(2, 100)
        self.assertFalse(b["real_resolution_or_cost_optimality"])


class SourceAndReplayTests(unittest.TestCase):
    def test_manifest_source_and_parity(self):
        fields = m.parse_manifest(manifest_bytes())
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0].weight("all_representation_bytes"), 33)
        self.assertEqual(fields[0].weight("products"), 3)

    def test_representation_and_field_corruptions_rejected(self):
        payload = manifest_bytes()
        lines = payload.splitlines(keepends=True)
        bad = [b"".join(lines[:-1]), payload + lines[-1], payload.replace(b"data_processed", b"data_unknown"),
               payload.replace(b",12,Sunset,", b",12,Moon,"), payload.replace(b",10,Sunset,", b",0,Sunset,"),
               payload.replace(b"product-2", b"product-0")]
        for mutated in bad:
            with self.subTest(payload=mutated):
                with self.assertRaises(ValueError):
                    m.parse_manifest(mutated)

    def test_contract_claim_laundering_rejected(self):
        contract = json.loads((m.ROOT / m.OUT / "contract.json").read_text())
        for key in contract["forbidden_claims"]:
            changed = copy.deepcopy(contract)
            changed["forbidden_claims"][key] = True
            with self.assertRaises(ValueError):
                m.validate_contract(changed)
        changed = copy.deepcopy(contract)
        changed["forbidden_claims"] = {}
        with self.assertRaises(ValueError):
            m.validate_contract(changed)
        changed = copy.deepcopy(contract)
        changed["assumptions"]["resolution_cost"] = "actual cheapest review"
        with self.assertRaises(ValueError):
            m.validate_contract(changed)

    def test_source_hash_drift_stops_before_parser(self):
        contract = json.loads((m.ROOT / m.OUT / "contract.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / m.OUT).mkdir(parents=True)
            (root / m.OUT / "contract.json").write_text(json.dumps(contract))
            (root / contract["source"]["path"]).parent.mkdir(parents=True)
            (root / contract["source"]["path"]).write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "source identity"):
                m.run(root)

    def test_frozen_result_and_all_witnesses_replay(self):
        result, witnesses, priorities, report = m.run()
        self.assertEqual(result["partition"]["exposure_fields"], 7606)
        combined = next(s for s in result["units"] if s["unit"] == "all_representation_bytes")
        witness = combined["majority_sensitivity"]
        self.assertEqual(witness["minimum_fields_to_lose_strict_majority"], 48)
        self.assertGreater(2 * witness["predecessor"]["numerator"], witness["denominator"])
        self.assertLessEqual(2 * witness["after"]["numerator"], witness["denominator"])
        self.assertEqual(combined["completion_budgets"]["5pp"]["minimum_fields_resolved_equal_field_cost"], 3747)
        fields = m.parse_manifest((m.ROOT / result["source_identity"]["path"]).read_bytes())
        by_id = {f.identity: f for f in fields}
        for summary in result["units"]:
            unit = summary["unit"]
            w = summary["majority_sensitivity"]
            picked = [f for f in witnesses if f["unit"] == unit]
            self.assertEqual(sum(row["weight"] for row in picked), w["removed_weight"])
            self.assertEqual([row["capture_identity"] for row in picked], w["reassigned_ids"])
            for row in picked:
                self.assertEqual(by_id[row["capture_identity"]].target, "Sunset")
                self.assertEqual(by_id[row["capture_identity"]].weight(unit), row["weight"])
            schedule = [row for row in priorities if row["unit"] == unit]
            remaining = summary["completion"]["blank_weight"]
            for row in schedule:
                f = by_id[row["capture_identity"]]
                self.assertEqual(f.target, "")
                remaining -= f.weight(unit)
                self.assertEqual(row["remaining_unknown_weight"], remaining)
            self.assertEqual(remaining, 0)
        self.assertNotIn("\u2014", report)

    def test_saved_artifacts_exact_replay(self):
        for name, payload in m.artifacts().items():
            self.assertEqual((m.ROOT / m.OUT / name).read_bytes(), payload, name)

    def test_native_crosscheck_receipt_binding(self):
        native = json.loads((m.ROOT / m.OUT / "native-crosscheck.json").read_text())
        contract = json.loads((m.ROOT / m.OUT / "contract.json").read_text())
        self.assertTrue(native["pass"])
        self.assertEqual(native["source_sha256"], contract["source"]["sha256"])
        self.assertEqual(native["unit_count"], 6)
        self.assertEqual(native["sensitivity_interval_checks"], 96)
        combined = next(s for s in native["units"] if s["unit"] == "all_representation_bytes")
        self.assertEqual(combined["minimum_fields_to_lose_strict_majority"], 48)


if __name__ == "__main__":
    unittest.main()
