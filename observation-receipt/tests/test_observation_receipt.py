from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from observation_receipt.evaluator import evaluate_case, evaluate_claim  # noqa: E402
from observation_receipt.exporters import write_bundle  # noqa: E402
from observation_receipt.model import CaseValidationError, validate_case  # noqa: E402


ARTEMIS_PATH = ROOT / "cases" / "artemis-ii-flashes" / "case.json"
SYNTHETIC_PATH = ROOT / "cases" / "synthetic-field-test" / "case.json"


class ObservationReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artemis = json.loads(ARTEMIS_PATH.read_text(encoding="utf-8"))
        cls.synthetic = json.loads(SYNTHETIC_PATH.read_text(encoding="utf-8"))

    def test_artemis_case_produces_six_bounded_findings(self) -> None:
        receipt = evaluate_case(copy.deepcopy(self.artemis), ROOT)
        self.assertTrue(receipt["pass"], receipt["checks"])
        statuses = {item["claim_id"]: item["status"] for item in receipt["findings"]}
        self.assertEqual(self.artemis["expected_findings"], statuses)
        self.assertEqual({"supported": 2, "refuted": 1, "blocked": 3, "other": 0}, receipt["summary"])

    def test_artemis_exact_values_reproduce(self) -> None:
        receipt = evaluate_case(copy.deepcopy(self.artemis), ROOT)
        findings = {item["claim_id"]: item for item in receipt["findings"]}
        self.assertEqual(913.0, findings["later-window-tested-ledger-events"]["gap_seconds"])
        self.assertAlmostEqual(1.314200547396414e-7, findings["all-lunar-count-floor"]["value_km2_hour"], places=16)
        self.assertEqual(
            ["monitored_area_km2", "live_time_hours", "limiting_magnitude", "detection_probability_surface", "calibrated_brightness"],
            findings["calibrated-impact-flux"]["missing_fields"],
        )

    def test_photo_epoch_is_not_promoted_to_event_coverage(self) -> None:
        claim = next(item for item in self.artemis["claims"] if item["id"] == "later-window-tested-ledger-events")
        self.assertEqual("annotation_base_image_utc", claim["rule"]["boundary_fact"])
        self.assertNotIn("annotation_ledger_utc", self.artemis["facts"])
        self.assertIn("background-photo epoch", claim["proposition"])
        self.assertIn("not ledger creation or an upper bound", claim["claim_ceiling"])
        self.assertIn("event-level video coverage remains unestablished", claim["claim_ceiling"])
        with tempfile.TemporaryDirectory() as output:
            receipt = evaluate_case(copy.deepcopy(self.artemis), ROOT)
            write_bundle(self.artemis, receipt, Path(output))
            page = (Path(output) / "index.html").read_text(encoding="utf-8")
            self.assertIn("background-photo epoch", page)
            self.assertIn("event-level video coverage remains unestablished", page)
            self.assertNotIn("window tested one of the five events", page)

    def test_structured_marks_preserve_prompt_and_dependence(self) -> None:
        candidate = next(item for item in self.artemis["candidates"] if item["id"] == "shared-transcript-report")
        marks = {mark["observer"]: mark for mark in candidate["witness_marks"]}
        self.assertEqual("unprompted", marks["Reid Wiseman"]["elicitation_state"])
        self.assertEqual("socially_cued", marks["Jeremy Hansen"]["elicitation_state"])
        self.assertEqual("dependent", marks["Jeremy Hansen"]["independence_state"])
        finding = evaluate_claim(self.artemis, self.artemis["claims"][5])
        self.assertEqual("BLOCKED_DEPENDENCE_MODEL_MISSING", finding["status"])

    def test_flat_witness_shortcut_is_rejected(self) -> None:
        changed = copy.deepcopy(self.artemis)
        changed["candidates"][0].pop("witness_marks")
        changed["candidates"][0]["witnesses"] = ["Reid Wiseman"]
        with self.assertRaises(CaseValidationError) as raised:
            validate_case(changed)
        self.assertIn("witness_marks must be an array", str(raised.exception))

    def test_window_mutation_changes_nonoverlap_result(self) -> None:
        changed = copy.deepcopy(self.artemis)
        changed["observation_windows"][0]["start_utc"] = "2026-04-07T01:03:30Z"
        finding = evaluate_claim(changed, changed["claims"][1])
        self.assertEqual("NOT_REFUTED_BY_BOUNDARY", finding["status"])

    def test_capability_mutation_changes_only_the_gate(self) -> None:
        changed = copy.deepcopy(self.artemis)
        required = changed["claims"][2]["rule"]["required_capabilities"]
        changed["observation_windows"][1]["capabilities"] = {
            name: {"state": "demonstrated", "note": "test mutation"} for name in required
        }
        finding = evaluate_claim(changed, changed["claims"][2])
        self.assertEqual("SUPPORTED_BY_DECLARED_GATE", finding["status"])
        self.assertEqual([], finding["missing_capabilities"])

    def test_artifact_identity_mutation_fails_receipt_without_hiding_findings(self) -> None:
        changed = copy.deepcopy(self.artemis)
        changed["artifacts"][0]["sha256"] = "0" * 64
        receipt = evaluate_case(changed, ROOT)
        self.assertFalse(receipt["pass"])
        self.assertFalse(receipt["checks"]["artifacts_match"])
        self.assertEqual(6, len(receipt["findings"]))

    def test_artifact_path_cannot_escape_declared_root(self) -> None:
        changed = copy.deepcopy(self.artemis)
        changed["artifacts"][0]["path"] = "../outside.csv"
        with self.assertRaisesRegex(ValueError, "escapes the declared root"):
            evaluate_case(changed, ROOT)

    def test_synthetic_case_exercises_same_core_outside_lunar_domain(self) -> None:
        receipt = evaluate_case(copy.deepcopy(self.synthetic), ROOT)
        self.assertTrue(receipt["pass"], receipt["checks"])
        statuses = {item["claim_id"]: item["status"] for item in receipt["findings"]}
        self.assertEqual(self.synthetic["expected_findings"], statuses)
        self.assertIn("software behavior only", receipt["claim_ceiling"])

    def test_bundle_is_complete_deterministic_and_accessible_by_structure(self) -> None:
        receipt = evaluate_case(copy.deepcopy(self.artemis), ROOT)
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_paths = write_bundle(self.artemis, receipt, Path(first))
            second_paths = write_bundle(self.artemis, receipt, Path(second))
            expected = {
                "index.html",
                "receipt.json",
                "receipt.md",
                "candidates.csv",
                "witness-marks.csv",
                "observation-windows.csv",
                "findings.csv",
                "manifest.json",
            }
            self.assertEqual(expected, set(first_paths))
            for name in expected:
                self.assertEqual(first_paths[name].read_bytes(), second_paths[name].read_bytes(), name)
            viewer = first_paths["index.html"].read_text(encoding="utf-8")
            self.assertIn('href="#main"', viewer)
            self.assertIn('<main id="main">', viewer)
            self.assertIn("prefers-reduced-motion", viewer)
            self.assertIn("Marks remain distinct from independent confirmations", viewer)
            self.assertIn("data:application/json;charset=utf-8;base64,", viewer)
            self.assertIn('download="receipt.json"', viewer)
            self.assertNotIn("<script src=", viewer.casefold())
            self.assertEqual(viewer.count('<script>'),1)
            self.assertIn("connect-src 'none'",viewer)

    def test_one_command_demo_exercises_real_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as output:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "run.py"), "demo", "--output", output],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("Built Artemis II lunar flash evidence", completed.stdout)
            self.assertTrue((Path(output) / "index.html").is_file())

    def test_schema_and_runtime_expose_same_rule_kinds(self) -> None:
        schema = json.loads((ROOT / "schemas" / "observation-receipt-v0.2.schema.json").read_text(encoding="utf-8"))
        schema_kinds = set(schema["$defs"]["claim"]["properties"]["rule"]["properties"]["kind"]["enum"])
        case_kinds = {claim["rule"]["kind"] for claim in self.artemis["claims"] + self.synthetic["claims"]}
        self.assertTrue(case_kinds <= schema_kinds)
        self.assertIn("witness_independence_gate", schema_kinds)

    def test_public_package_avoids_private_vocabulary_and_em_dashes(self) -> None:
        text_extensions = {".py", ".md", ".json", ".toml", ".csv"}
        content = "\n".join(
            path.read_text(encoding="utf-8")
            for path in ROOT.rglob("*")
            if path.is_file()
            and path.suffix.casefold() in text_extensions
            and "build" not in path.parts
            and "tests" not in path.parts
        )
        self.assertNotIn(chr(0x2014), content)
        folded = content.casefold()
        for phrase in ("private-system-name",):
            self.assertNotIn(phrase, folded)


if __name__ == "__main__":
    unittest.main()
