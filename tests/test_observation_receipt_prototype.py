from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "prototype/observation_receipt.py"
SPEC = importlib.util.spec_from_file_location("observation_receipt", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CASE_PATH = ROOT / "examples/artemis-ii-flashes.observation-receipt.json"
SCHEMA_PATH = ROOT / "schemas/observation-receipt-v0.1.schema.json"


class ObservationReceiptPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.case = json.loads(CASE_PATH.read_text(encoding="utf-8"))

    def test_fixture_produces_five_distinct_findings(self) -> None:
        receipt = MODULE.evaluate(copy.deepcopy(self.case), ROOT)
        self.assertTrue(receipt["pass"], receipt["checks"])
        statuses = {item["claim_id"]: item["status"] for item in receipt["findings"]}
        self.assertEqual("SUPPORTED", statuses["accepted-ledger"])
        self.assertEqual("REFUTED_NONOVERLAP", statuses["later-window-tested-ledger-events"])
        self.assertEqual("BLOCKED_INSUFFICIENT_CAPABILITY", statuses["overlap-null-excludes-report"])
        self.assertEqual("SUPPORTED_WITH_ASSUMPTIONS", statuses["all-lunar-count-floor"])
        self.assertEqual("BLOCKED_MISSING_MEASUREMENT_FUNCTION", statuses["calibrated-impact-flux"])
        self.assertEqual({"supported": 2, "refuted": 1, "blocked": 2}, receipt["summary"])

    def test_schema_names_the_five_reusable_rule_types(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        values = schema["properties"]["claims"]["items"]["properties"]["rule"]["properties"]["kind"]["enum"]
        self.assertEqual(
            [
                "ledger_summary",
                "window_after_boundary",
                "window_capability_gate",
                "count_floor_sphere",
                "required_measurement_fields",
            ],
            values,
        )

    def test_later_window_gap_and_count_floor_are_exact(self) -> None:
        receipt = MODULE.evaluate(copy.deepcopy(self.case), ROOT)
        findings = {item["claim_id"]: item for item in receipt["findings"]}
        self.assertEqual(913.0, findings["later-window-tested-ledger-events"]["gap_seconds"])
        self.assertAlmostEqual(1.314200547396414e-7, findings["all-lunar-count-floor"]["value_km2_hour"], places=16)

    def test_photo_epoch_is_not_promoted_to_all_event_coverage(self) -> None:
        receipt = MODULE.evaluate(copy.deepcopy(self.case), ROOT)
        finding = receipt['findings'][1]
        self.assertEqual('annotation_base_image_utc', self.case['claims'][1]['rule']['boundary_fact'])
        self.assertNotIn('annotation_ledger_utc', self.case['facts'])
        self.assertIn('background-photo epoch', finding['proposition'])
        self.assertIn('event-level video coverage remains unestablished', finding['claim_ceiling'])
        text = MODULE.to_markdown(receipt)
        self.assertIn('does not certify ledger creation or bound all five event times', text)
        self.assertNotIn('Non-overlap refutes the claim that the later camera window tested a ledger event', text)

    def test_changed_window_removes_nonoverlap_refutation(self) -> None:
        changed = copy.deepcopy(self.case)
        changed["observation_windows"][0]["start_utc"] = "2026-04-07T01:03:30Z"
        finding = MODULE.evaluate_claim(changed, changed["claims"][1])
        self.assertEqual("NOT_REFUTED_BY_BOUNDARY", finding["status"])

    def test_capability_mutation_changes_only_the_gate(self) -> None:
        changed = copy.deepcopy(self.case)
        changed["observation_windows"][1]["capabilities"] = {
            name: True for name in changed["claims"][2]["rule"]["required_capabilities"]
        }
        finding = MODULE.evaluate_claim(changed, changed["claims"][2])
        self.assertEqual("SUPPORTED_BY_DECLARED_GATE", finding["status"])
        self.assertEqual([], finding["missing_capabilities"])

    def test_measurement_gate_names_every_missing_field(self) -> None:
        finding = MODULE.evaluate_claim(copy.deepcopy(self.case), self.case["claims"][4])
        self.assertEqual(
            ["monitored_area_km2", "live_time_hours", "limiting_magnitude", "detection_probability_surface", "calibrated_brightness"],
            finding["missing_fields"],
        )

    def test_saved_outputs_match_when_present(self) -> None:
        json_path = ROOT / "results/observation-receipt-artemis-fixture.json"
        if not json_path.exists():
            self.skipTest("Prototype output has not been generated yet.")
        self.assertEqual(MODULE.evaluate(copy.deepcopy(self.case), ROOT), json.loads(json_path.read_text(encoding="utf-8")))

    def test_public_prototype_uses_no_em_dash_or_private_vocabulary(self) -> None:
        text = MODULE_PATH.read_text(encoding="utf-8") + CASE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("—", text)
        folded = text.casefold()
        for phrase in ("private-system-name",):
            self.assertNotIn(phrase, folded)


if __name__ == "__main__":
    unittest.main()
