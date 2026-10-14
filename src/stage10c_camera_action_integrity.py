#!/usr/bin/env python3
"""Verify Stage 10C's generalized camera-action facet-integrity audit."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import (
    add_check,
    integer,
    load_hits,
    load_json,
    normalize_hit,
    parse_utc,
    verify_source_identity,
)


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "partial_brackets_admitted": False,
        "correct_activity_inferred": False,
        "all_fractures_declared_errors": False,
        "image_content_inferred": False,
        "single_cause_claimed": False,
        "scope": "flight_day_6_complete_raw_brackets",
        "facets_declared_useless": False,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "count_partial_brackets":
        state["partial_brackets_admitted"] = True
    elif mutation == "infer_correct_activity_from_majority":
        state["correct_activity_inferred"] = True
    elif mutation == "call_every_fracture_a_metadata_error":
        state["all_fractures_declared_errors"] = True
    elif mutation == "treat_target_absence_as_image_content":
        state["image_content_inferred"] = True
    elif mutation == "claim_one_cause_for_all_fractures":
        state["single_cause_claimed"] = True
    elif mutation == "generalize_fd6_rate_to_other_days":
        state["scope"] = "all_flight_days"
    elif mutation == "claim_activity_facets_are_useless":
        state["facets_declared_useless"] = True
    elif mutation == "open_pixels_to_resolve_labels":
        mutated["source_contract"]["pixel_payload_bytes"] = 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def sequence_key(values: list[str]) -> str:
    return ",".join(values)


def bracket_from_sequence(
    window: list[dict[str, Any]], sequence: list[str], contract: dict[str, Any]
) -> dict[str, Any] | None:
    if len(window) != len(sequence):
        return None
    if [item["bracket_value"] for item in window] != sequence:
        return None
    if any(
        item["auto_bracket_order"] != contract["required_auto_bracket_order"]
        or contract["shooting_mode_contains"] not in (item["shooting_mode"] or "")
        for item in window
    ):
        return None
    for field in contract["same_fields"]:
        values = {item[field] for item in window}
        if None in values or len(values) != 1:
            return None
    for field in contract["consecutive_integer_fields"]:
        values = [integer(item[field]) for item in window]
        if any(value is None for value in values):
            return None
        assert values[0] is not None
        if values != list(range(values[0], values[0] + len(window))):
            return None
    try:
        times = [parse_utc(item["time"]) for item in window]
    except (TypeError, ValueError):
        return None
    span = (times[-1] - times[0]).total_seconds()
    if span < 0 or span > contract["maximum_span_seconds"]:
        return None
    activities = [item["activity_id"] for item in window]
    targets = [item["target_id"] for item in window]
    return {
        "serial": window[0]["serial"],
        "start_time": window[0]["time"],
        "end_time": window[-1]["time"],
        "span_seconds": span,
        "file_names": [item["file_name"] for item in window],
        "shutter_counts": [integer(item["shutter_count"]) for item in window],
        "file_numbers": [integer(item["file_number"]) for item in window],
        "bracket_values": [item["bracket_value"] for item in window],
        "activity_ids": activities,
        "target_ids": targets,
        "activity_facet_fracture": len({value for value in activities if value}) > 1,
        "target_presence_fracture": 0 < sum(value is not None for value in targets) < len(targets),
        "target_value_fracture": len({value for value in targets if value}) > 1,
    }


def detect_complete_brackets(
    records: list[dict[str, Any]], contract: dict[str, Any]
) -> list[dict[str, Any]]:
    sequences = sorted(contract["allowed_bracket_sequences"], key=len, reverse=True)
    by_serial: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["serial"] is not None and integer(record["shutter_count"]) is not None:
            by_serial[record["serial"]].append(record)
    brackets: list[dict[str, Any]] = []
    for serial_records in by_serial.values():
        serial_records.sort(key=lambda item: integer(item["shutter_count"]) or -1)
        index = 0
        while index < len(serial_records):
            if serial_records[index]["bracket_value"] != "0":
                index += 1
                continue
            match = None
            for sequence in sequences:
                match = bracket_from_sequence(
                    serial_records[index : index + len(sequence)], sequence, contract
                )
                if match is not None:
                    break
            if match is None:
                index += 1
            else:
                brackets.append(match)
                index += len(match["bracket_values"])
    return sorted(brackets, key=lambda item: (item["start_time"], item["serial"]))


def longest_signature_run(
    brackets: list[dict[str, Any]], signature: dict[str, Any]
) -> list[dict[str, Any]]:
    best: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for bracket in brackets:
        matches = (
            bracket["serial"] == signature["serial"]
            and bracket["activity_ids"] == signature["activity_ids"]
            and bracket["target_ids"] == signature["target_ids"]
            and bracket["bracket_values"] == signature["bracket_values"]
        )
        if matches:
            current.append(bracket)
            if len(current) > len(best):
                best = list(current)
        else:
            current = []
    return best


def verify_stage10c(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10c.json"), mutation)
    receipt = load_json(root / spec["source_contract"]["stage10a_receipt_path"])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    source_failures = verify_source_identity(root, receipt)
    hits, page_errors = load_hits(root, receipt)
    ids = [hit.get("_id") for hit in hits]
    source_ok = (
        not source_failures
        and not page_errors
        and len(hits) == spec["source_contract"]["expected_source_records"]
        and len(set(ids)) == len(ids)
    )
    add_check(
        checks,
        errors,
        "complete_source_replay",
        source_ok,
        error="The preserved complete Flight Day 6 source cohort did not replay.",
        source_failures=source_failures,
        page_errors=page_errors,
        records=len(hits),
    )

    records = [normalize_hit(hit) for hit in hits]
    contract = spec["complete_bracket_contract"]
    allowed = contract["allowed_bracket_sequences"]
    contract_ok = (
        allowed
        == [
            ["0", "-1", "+1"],
            ["0", "-2", "+2"],
            ["0", "-2", "-1", "+1", "+2"],
            ["0", "-6", "-3", "+3", "+6"],
        ]
        and all(sequence[0] == "0" for sequence in allowed)
        and contract["maximum_span_seconds"] == 10.0
        and contract["consecutive_integer_fields"] == ["shutter_count", "file_number"]
    )
    add_check(
        checks,
        errors,
        "camera_native_oracle",
        contract_ok,
        error="The predeclared complete-bracket oracle changed or admitted partial sequences.",
    )

    brackets = detect_complete_brackets(records, contract) if contract_ok else []
    pattern_counts = Counter(sequence_key(item["bracket_values"]) for item in brackets)
    expected = spec["frozen_observables"]
    denominator_ok = (
        len(brackets) == expected["expected_complete_brackets"]
        and dict(sorted(pattern_counts.items()))
        == dict(sorted(expected["expected_pattern_counts"].items()))
    )
    add_check(
        checks,
        errors,
        "complete_action_denominator",
        denominator_ok,
        error="The generalized complete-bracket denominator or pattern census changed.",
        complete_brackets=len(brackets),
        pattern_counts=dict(pattern_counts),
    )

    fractures = [item for item in brackets if item["activity_facet_fracture"]]
    fractured_pattern_counts = Counter(
        sequence_key(item["bracket_values"]) for item in fractures
    )
    target_presence_count = sum(item["target_presence_fracture"] for item in fractures)
    target_value_count = sum(item["target_value_fracture"] for item in fractures)
    fracture_rate = len(fractures) / len(brackets) if brackets else None
    recurrence_ok = (
        len(fractures) == expected["expected_activity_fractures"]
        and fracture_rate == expected["expected_activity_fracture_rate"]
        and dict(sorted(fractured_pattern_counts.items()))
        == dict(sorted(expected["expected_fractured_pattern_counts"].items()))
        and target_presence_count
        == expected["expected_target_presence_fractures_among_activity_fractures"]
        and target_value_count
        == expected["expected_target_value_fractures_among_activity_fractures"]
    )
    add_check(
        checks,
        errors,
        "recurrent_action_fragmentation",
        recurrence_ok,
        error="The predeclared fracture count, rate, pattern mix, or target relation changed.",
        activity_fractures=len(fractures),
        activity_fracture_rate=fracture_rate,
        fractured_pattern_counts=dict(fractured_pattern_counts),
        target_presence_fractures=target_presence_count,
        target_value_fractures=target_value_count,
    )

    signature = expected["repeated_signature"]
    signature_run = longest_signature_run(brackets, signature)
    signature_ok = (
        len(signature_run) == signature["expected_consecutive_actions"]
        and signature_run[0]["start_time"] == signature["expected_start"]
        and signature_run[-1]["end_time"] == signature["expected_end"]
    )
    add_check(
        checks,
        errors,
        "repeated_position_signature",
        signature_ok,
        error="The thirteen-action repeated position-specific signature did not reproduce.",
        actions=len(signature_run),
        start=signature_run[0]["start_time"] if signature_run else None,
        end=signature_run[-1]["end_time"] if signature_run else None,
    )

    state = spec["mutation_state"]
    boundary_ok = (
        not any(
            state[key]
            for key in (
                "partial_brackets_admitted",
                "correct_activity_inferred",
                "all_fractures_declared_errors",
                "image_content_inferred",
                "single_cause_claimed",
                "facets_declared_useless",
            )
        )
        and state["scope"] == "flight_day_6_complete_raw_brackets"
        and spec["source_contract"]["pixel_payload_bytes"] == 0
        and receipt["pixel_payload_bytes"] == 0
    )
    add_check(
        checks,
        errors,
        "claim_and_access_boundaries",
        boundary_ok,
        error="A prohibited causal, correctness, content, scope, facet-value, or pixel claim was admitted.",
        mutation_state=state,
        pixel_payload_bytes=spec["source_contract"]["pixel_payload_bytes"],
    )

    if signature_ok and recurrence_ok:
        evidence_state = "VERIFIED_RECURRENT_POSITION_STRUCTURED_FRAGMENTATION"
    elif recurrence_ok:
        evidence_state = "VERIFIED_RECURRENT_ACTION_FRAGMENTATION"
    else:
        evidence_state = "NO_VERIFIED_RECURRENCE"
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "source_records": len(records),
        "complete_brackets": len(brackets),
        "pattern_counts": dict(pattern_counts),
        "activity_fractured_brackets": len(fractures),
        "activity_fracture_rate": fracture_rate,
        "fractured_pattern_counts": dict(fractured_pattern_counts),
        "target_presence_fractures_among_activity_fractures": target_presence_count,
        "target_value_fractures_among_activity_fractures": target_value_count,
        "repeated_signature_run": signature_run,
        "pixel_payload_bytes": receipt["pixel_payload_bytes"],
        "activity_fractures": fractures,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10c(root)
    names = load_json(root / "spec" / "stage10c.json")["hard_negatives"]
    mutations = {name: verify_stage10c(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 10C hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    rate = result["activity_fracture_rate"]
    lines = [
        "# Stage 10C — Generalized Camera-Action Facet Integrity",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Complete Flight Day 6 raw records: `{result['source_records']}`",
        f"- Complete three- or five-frame bracket actions: `{result['complete_brackets']}`",
        f"- Activity-fractured actions: `{result['activity_fractured_brackets']}` (`{rate:.4%}`)",
        f"- Longest repeated position-specific fracture run: `{len(result['repeated_signature_run'])}` actions",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "",
        "## Result",
        "",
        "Activity-facet fragmentation recurs across 21 of 1,721 complete camera actions. Thirteen consecutive three-frame actions repeat the same split by exposure position: the middle exposure is tagged `14_Crew Choice #2` with no target, while the paired exposures are tagged `15_Discussion #4: Terminator` with target `Terminator`. This repeated within-action structure is not well explained as a single temporal activity boundary.",
        "",
        "The result establishes a retrieval-unit mismatch, not wrong labels. Activity facets retain coarse value, and the evidence does not identify the correct activity, image content, or authoring cause.",
        "",
        "## Pattern census",
        "",
    ]
    for pattern, count in sorted(result["pattern_counts"].items()):
        lines.append(f"- `{pattern}`: `{count}` complete actions")
    lines.extend(["", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", ""])
    for name, mutation_result in result.get("hard_negatives", {}).items():
        verdict = "REJECTED" if not mutation_result["pass"] else "UNEXPECTEDLY ACCEPTED"
        lines.append(f"- `{name}`: {verdict}")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--mutation")
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        result = verify_with_mutations(args.root.resolve())
    else:
        result = verify_stage10c(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(
            render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
