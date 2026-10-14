#!/usr/bin/env python3
"""Verify Stage 10J's fractional-stop camera-action oracle expansion."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_hits, load_json, normalize_hit
from stage10c_camera_action_integrity import detect_complete_brackets, sequence_key
from stage10e_all_days_integrity import load_daily_hits, verify_stage10e


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "fd6_only": False, "exhaustive": False, "pao_correct": False, "other_correct": False,
        "all_errors": False, "mechanism_scope": "stage10f_repeated_signature",
        "partial_brackets": False,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    mapping = {
        "retain_flight_day_6_only_generalization": "fd6_only",
        "call_six_patterns_exhaustive": "exhaustive",
        "infer_pao_labels_correct": "pao_correct",
        "infer_other_labels_correct": "other_correct",
        "call_every_fracture_a_metadata_error": "all_errors",
        "admit_partial_brackets": "partial_brackets",
    }
    if mutation == "generalize_stage10f_mechanism_cross_day":
        state["mechanism_scope"] = "all_fractures"
    elif mutation == "open_pixels_to_resolve_cross_day_labels":
        mutated["source_contract"]["pixel_payload_bytes"] = 1
    elif mutation in mapping:
        state[mapping[mutation]] = True
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_receipt(root: Path, receipt: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for record in receipt.get("sources", []):
        path = root / record["path"]
        if not path.is_file(): failures.append(f"missing:{record['path']}"); continue
        if path.stat().st_size != record["bytes"]: failures.append(f"bytes:{record['path']}")
        if sha256_file(path) != record["sha256"]: failures.append(f"sha256:{record['path']}")
    return failures


def counts_by_day(items: list[dict[str, Any]], file_days: dict[str, str]) -> dict[str, int]:
    counter = Counter(file_days[item["file_names"][0]] for item in items)
    return {str(day): counter[str(day)] for day in range(1, 11)}


def verify_stage10j(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10j.json"), mutation)
    contract, expected = spec["source_contract"], spec["frozen_observables"]
    receipt = load_json(root / contract["receipt_path"])
    checks: list[dict[str, Any]] = []; errors: list[str] = []

    failures = verify_receipt(root, receipt)
    add_check(checks, errors, "source_identity", receipt.get("status") == "COMPLETED" and not failures,
              error="A Stage 10J source or dependency identity changed.", failures=failures)

    prior = verify_stage10e(root)
    prior_ok = prior.get("pass") is True and prior["complete_brackets"] == 2103 and prior["activity_fractured_brackets"] == 21
    add_check(checks, errors, "prior_four_pattern_replay", prior_ok,
              error="The bounded Stage 10E baseline did not replay.")

    receipt10a = load_json(root / contract["stage10a_receipt_path"])
    receipt10e = load_json(root / contract["stage10e_receipt_path"])
    fd6_hits, fd6_errors = load_hits(root, receipt10a)
    daily_hits, daily_errors = load_daily_hits(root, receipt10e)
    hits = daily_hits + fd6_hits
    records = [normalize_hit(hit) for hit in hits]
    source_ok = not fd6_errors and not daily_errors and len(records) == contract["expected_records"]
    add_check(checks, errors, "complete_source_replay", source_ok,
              error="The complete 10,329-record raw cohort did not replay.", records=len(records), page_errors=fd6_errors + daily_errors)

    base_contract = copy.deepcopy(load_json(root / contract["stage10c_spec_path"])["complete_bracket_contract"])
    base_contract["allowed_bracket_sequences"] = spec["expanded_patterns"]
    brackets = detect_complete_brackets(records, base_contract)
    patterns = Counter(sequence_key(item["bracket_values"]) for item in brackets)
    file_days = {item["file_name"]: item["flight_day"] for item in records}
    by_day = counts_by_day(brackets, file_days)
    used = {name for item in brackets for name in item["file_names"]}
    fractional = [item for item in brackets if any("/" in value for value in item["bracket_values"])]
    denominator_ok = (
        len(brackets) == expected["complete_brackets"] and len(used) == expected["exposures_in_complete_brackets"]
        and len(records) - len(used) == expected["unadmitted_records"]
        and dict(patterns) == expected["pattern_counts"] and by_day == expected["brackets_by_flight_day"]
        and len(fractional) == expected["fractional_pattern_actions"]
    )
    add_check(checks, errors, "expanded_complete_action_denominator", denominator_ok,
              error="The expanded complete-action denominator or pattern distribution changed.",
              complete_brackets=len(brackets), exposures=len(used), unadmitted=len(records)-len(used),
              patterns=dict(patterns), by_day=by_day, fractional_actions=len(fractional))

    fractures = [item for item in brackets if item["activity_facet_fracture"]]
    fractures_by_day = counts_by_day(fractures, file_days)
    fractional_fractures = [item for item in fractional if item["activity_facet_fracture"]]
    target_presence = sum(item["target_presence_fracture"] for item in fractures)
    target_value = sum(item["target_value_fracture"] for item in fractures)
    recurrence_ok = (
        len(fractures) == expected["activity_fractures"] and fractures_by_day == expected["fractures_by_flight_day"]
        and len(fractional_fractures) == expected["fractional_pattern_fractures"]
        and target_presence == expected["target_presence_fractures"] and target_value == expected["target_value_fractures"]
    )
    add_check(checks, errors, "cross_day_fracture_recurrence", recurrence_ok,
              error="The cross-day fracture counts or target relations changed.",
              fractures=len(fractures), by_day=fractures_by_day,
              fractional_fractures=len(fractional_fractures), target_presence=target_presence, target_value=target_value)

    falsification_ok = prior_ok and sum(value for day, value in fractures_by_day.items() if day != "6") == 4
    add_check(checks, errors, "stage10e_fd6_only_generalization_superseded", falsification_ok,
              error="The changed case did not decisively test the Flight-Day-6-only generalization.")

    state = spec["mutation_state"]
    boundary_ok = (
        not any(state[key] for key in ("fd6_only", "exhaustive", "pao_correct", "other_correct", "all_errors", "partial_brackets"))
        and state["mechanism_scope"] == "stage10f_repeated_signature"
        and contract["pixel_payload_bytes"] == 0 and receipt["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited concentration, completeness, correctness, mechanism, partial-sequence, or pixel claim was admitted.",
              mutation_state=state, pixel_payload_bytes=contract["pixel_payload_bytes"])

    evidence_state = "VERIFIED_FRACTIONAL_STOP_EXPANSION_AND_CROSS_DAY_RECURRENCE" if denominator_ok and recurrence_ok and falsification_ok else "EXPANSION_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "source_records": len(records), "complete_brackets": len(brackets), "exposures_in_complete_brackets": len(used),
        "unadmitted_records": len(records)-len(used), "pattern_counts": dict(patterns), "brackets_by_flight_day": by_day,
        "activity_fractures": len(fractures), "activity_fracture_rate": len(fractures)/len(brackets),
        "fractures_by_flight_day": fractures_by_day, "fractional_pattern_actions": len(fractional),
        "fractional_pattern_fractures": len(fractional_fractures), "target_presence_fractures": target_presence,
        "target_value_fractures": target_value, "stage10e_generalization_superseded": falsification_ok,
        "new_cross_day_fractures": fractional_fractures,
        "verified": spec["interpretation"]["verified"], "falsification": spec["interpretation"]["falsification"],
        "bounded_inference": spec["interpretation"]["bounded_inference"], "decision_use": spec["interpretation"]["decision_use"],
        "pixel_payload_bytes": receipt["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10j(root)
    names = load_json(root / "spec" / "stage10j.json")["hard_negatives"]
    mutations = {name: verify_stage10j(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10J hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10J — Fractional-Stop Bracket Expansion", "", f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`", f"- Complete six-pattern actions: `{result['complete_brackets']:,}`",
        f"- Activity-fractured actions: `{result['activity_fractures']}` (`{result['activity_fracture_rate']:.4%}`)",
        f"- Fractional-pattern actions / fractures: `{result['fractional_pattern_actions']}` / `{result['fractional_pattern_fractures']}`",
        f"- Stage 10E generalization superseded: `{result['stage10e_generalization_superseded']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`", "", "## Verified", "", result["verified"], "",
        "## Successful falsification", "", result["falsification"], "", "## Bounded inference", "", result["bounded_inference"], "",
        "## Decision use", "", result["decision_use"], "", "## Claim ceiling", "", result["claim_ceiling"], "", "## Flight-day action / fracture counts", "",
    ]
    for day in sorted(result["brackets_by_flight_day"], key=int):
        lines.append(f"- Flight Day {day}: `{result['brackets_by_flight_day'][day]}` / `{result['fractures_by_flight_day'][day]}`")
    lines += ["", "## Hard negatives", ""]
    for name, mutation_result in result.get("hard_negatives", {}).items():
        lines.append(f"- `{name}`: {'REJECTED' if not mutation_result['pass'] else 'UNEXPECTEDLY ACCEPTED'}")
    lines.append(""); return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1]); parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path); parser.add_argument("--mutation"); args = parser.parse_args(argv)
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10j(args.root.resolve(), args.mutation)
    if args.json_output: write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2)); return 0 if result["pass"] else 1


if __name__ == "__main__": sys.exit(main())
