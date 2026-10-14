#!/usr/bin/env python3
"""Verify Stage 10B's Forward Look activity-representation audit."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import (
    integer,
    load_hits,
    load_json,
    normalize_hit,
    parse_utc,
    verify_stage10a,
)


XSD_NS = {"xs": "http://www.w3.org/2001/XMLSchema"}


def add_check(
    checks: list[dict[str, Any]],
    errors: list[str],
    check_id: str,
    passed: bool,
    *,
    error: str,
    **details: Any,
) -> None:
    checks.append({"id": check_id, "pass": passed, **details})
    if not passed:
        errors.append(error)


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "boundary_claim": False,
        "labels_declared_wrong": False,
        "discussion_execution_inferred": False,
        "image_content_inferred": False,
        "schema_declared_causal": False,
        "concurrent_activity_declared_impossible": False,
        "scope": "flight_day_6_raw_crew_camera",
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "call_isolated_singletons_a_temporal_boundary":
        state["boundary_claim"] = True
    elif mutation == "declare_the_forward_look_labels_wrong":
        state["labels_declared_wrong"] = True
    elif mutation == "treat_activity_id_as_discussion_execution_evidence":
        state["discussion_execution_inferred"] = True
    elif mutation == "infer_image_content_from_nearby_transcript":
        state["image_content_inferred"] = True
    elif mutation == "claim_scalar_cardinality_caused_the_observed_assignments":
        state["schema_declared_causal"] = True
    elif mutation == "claim_the_schema_forbids_real_world_concurrent_activity":
        state["concurrent_activity_declared_impossible"] = True
    elif mutation == "generalize_two_records_to_all_artemis_metadata":
        state["scope"] = "all_artemis_metadata"
    elif mutation == "open_pixels_to_choose_the_correct_activity":
        mutated["source_contract"]["pixel_payload_bytes"] = 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_receipt(root: Path, receipt: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for record in receipt.get("sources", []):
        path = root / record["path"]
        if not path.is_file():
            failures.append(f"missing:{record['path']}")
            continue
        if path.stat().st_size != record["bytes"]:
            failures.append(f"bytes:{record['path']}")
        if sha256_file(path) != record["sha256"]:
            failures.append(f"sha256:{record['path']}")
    return failures


def same_camera_neighbors(
    records: list[dict[str, Any]], focus_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_serial: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["serial"] and integer(record["shutter_count"]) is not None:
            by_serial[record["serial"]].append(record)
    for serial_records in by_serial.values():
        serial_records.sort(key=lambda item: integer(item["shutter_count"]) or -1)
    contexts: list[dict[str, Any]] = []
    for focus in focus_records:
        serial_records = by_serial[focus["serial"]]
        index = next(index for index, item in enumerate(serial_records) if item["id"] == focus["id"])
        previous = serial_records[index - 1] if index > 0 else None
        following = serial_records[index + 1] if index + 1 < len(serial_records) else None
        contexts.append(
            {
                "focus": focus,
                "previous": previous,
                "following": following,
                "previous_shutter_delta": (
                    integer(focus["shutter_count"]) - integer(previous["shutter_count"])
                    if previous
                    else None
                ),
                "following_shutter_delta": (
                    integer(following["shutter_count"]) - integer(focus["shutter_count"])
                    if following
                    else None
                ),
            }
        )
    return contexts


def find_plan_entry(root: Path, path: str, name: str) -> dict[str, Any] | None:
    with (root / path).open(encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        return None
    return next(
        (
            item.get("target_properties", {})
            for item in payload
            if item.get("target_properties", {}).get("ltp_name") == name
        ),
        None,
    )


def verify_stage10b(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10b.json"), mutation)
    contract = spec["source_contract"]
    observables = spec["frozen_observables"]
    receipt = load_json(root / contract["receipt_path"])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    receipt_failures = verify_receipt(root, receipt)
    add_check(
        checks,
        errors,
        "source_identity",
        not receipt_failures,
        error="A Stage 10B source byte or receipt identity changed.",
        failures=receipt_failures,
    )

    stage10a = verify_stage10a(root)
    add_check(
        checks,
        errors,
        "stage10a_replay",
        stage10a["pass"]
        and stage10a["source_records"] == 8423
        and stage10a["activity_fractured_brackets"] == 2,
        error="The complete Stage 10A denominator or fracture result did not replay.",
    )

    stage10a_receipt = load_json(root / "evidence" / "stage10a" / "acquisition-receipt.json")
    hits, page_errors = load_hits(root, stage10a_receipt)
    records = [normalize_hit(hit) for hit in hits]
    activity_counts = Counter(record["activity_id"] or "<missing>" for record in records)
    focus_records = [
        record for record in records if record["activity_id"] == spec["focus_activity_id"]
    ]
    focus_records.sort(key=lambda item: item["time"])
    focus_contract_ok = (
        not page_errors
        and len(focus_records) == observables["expected_focus_record_count"]
        and {item["serial"] for item in focus_records}
        == {observables["expected_focus_serial"]}
        and [integer(item["shutter_count"]) for item in focus_records]
        == observables["expected_focus_shutter_counts"]
        and [item["target_id"] for item in focus_records]
        == observables["expected_focus_target_ids"]
    )
    add_check(
        checks,
        errors,
        "complete_focus_facet_census",
        focus_contract_ok,
        error="The complete Forward Look raw-image facet did not reproduce as two records.",
        activity_count=activity_counts[spec["focus_activity_id"]],
        records=focus_records,
    )

    contexts = same_camera_neighbors(records, focus_records)
    comparison = spec["comparison_activity_id"]
    isolated_ok = len(contexts) == 2 and all(
        context["previous"] is not None
        and context["following"] is not None
        and context["previous_shutter_delta"] == 1
        and context["following_shutter_delta"] == 1
        and context["previous"]["activity_id"] == comparison
        and context["following"]["activity_id"] == comparison
        for context in contexts
    )
    add_check(
        checks,
        errors,
        "isolated_same_camera_singletons",
        isolated_ok,
        error="At least one Forward Look record is not an isolated singleton between Sunset records.",
        contexts=contexts,
    )

    result = load_json(root / contract["stage10a_result_path"])
    focus_brackets: list[dict[str, Any]] = []
    for focus in focus_records:
        matches = [
            bracket
            for bracket in result["activity_fractures"]
            if focus["file_name"] in bracket["file_names"]
        ]
        if len(matches) == 1:
            focus_brackets.append(matches[0])
    bracket_ok = len(focus_brackets) == 2 and all(
        bracket["activity_ids"].count(spec["focus_activity_id"]) == 1
        and bracket["activity_ids"].count(comparison) == 4
        for bracket in focus_brackets
    )
    action_count = len(focus_brackets)
    focus_only_complete_actions = sum(
        1 for bracket in focus_brackets if set(bracket["activity_ids"]) == {spec["focus_activity_id"]}
    )
    companion_records_needed = sum(
        len(bracket["file_names"])
        - bracket["activity_ids"].count(spec["focus_activity_id"])
        for bracket in focus_brackets
    )
    add_check(
        checks,
        errors,
        "physical_action_fragmentation",
        bracket_ok and action_count == 2 and focus_only_complete_actions == 0,
        error="The focus facet no longer maps one record from each of two five-frame brackets.",
        physical_actions=action_count,
        focus_only_complete_actions=focus_only_complete_actions,
        companion_records_needed=companion_records_needed,
    )

    schema_path = root / contract["schema_path"]
    schema = ET.parse(schema_path).getroot()
    observational_intent = schema.find(
        ".//xs:complexType[@name='Observational_Intent']", XSD_NS
    )
    activity_element = (
        observational_intent.find(".//xs:element[@name='activity_id']", XSD_NS)
        if observational_intent is not None
        else None
    )
    schema_max_occurs = (
        activity_element.get("maxOccurs") if activity_element is not None else None
    )
    schema_ok = schema_max_occurs == observables["schema_activity_id_max_occurs"] == "1"
    add_check(
        checks,
        errors,
        "scalar_activity_schema",
        schema_ok,
        error="The official Observational_Intent schema does not limit activity_id to one value.",
        max_occurs=schema_max_occurs,
    )

    plan = find_plan_entry(
        root, contract["outgoing_target_request_path"], "Discussion #6: Forward Look"
    )
    plan_ok = (
        plan is not None
        and plan.get("request_date_time") == "07 Apr 2026 00:44:00"
        and plan.get("request_duration") == observables["forward_look_request_duration_minutes"]
    )
    planned_start = parse_utc(observables["forward_look_request_time"])
    planned_end = planned_start + timedelta(
        minutes=observables["forward_look_request_duration_minutes"]
    )
    focus_within_nominal_window = all(
        planned_start <= parse_utc(item["time"]) <= planned_end for item in focus_records
    )
    add_check(
        checks,
        errors,
        "plan_is_timing_context_not_execution_oracle",
        plan_ok and focus_within_nominal_window,
        error="The plan timing context or focus-window relation changed.",
        planned_start=planned_start.isoformat(),
        planned_end=planned_end.isoformat(),
        focus_within_nominal_window=focus_within_nominal_window,
    )

    with (root / contract["transcript_path"]).open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        transcript_rows = list(csv.DictReader(handle))
    transcript_by_time = {row["utc"]: row["text"] for row in transcript_rows}
    missing_cues = [
        [utc, phrase]
        for utc, phrase in observables["transcript_cues"]
        if phrase.lower() not in transcript_by_time.get(utc, "").lower()
    ]
    add_check(
        checks,
        errors,
        "contemporaneous_operational_context",
        not missing_cues,
        error="One or more frozen transcript context cues is missing.",
        missing_cues=missing_cues,
    )

    state = spec["mutation_state"]
    boundary_ok = (
        not any(
            state[key]
            for key in (
                "boundary_claim",
                "labels_declared_wrong",
                "discussion_execution_inferred",
                "image_content_inferred",
                "schema_declared_causal",
                "concurrent_activity_declared_impossible",
            )
        )
        and state["scope"] == "flight_day_6_raw_crew_camera"
        and contract["pixel_payload_bytes"] == 0
        and receipt["pixel_payload_bytes"] == 0
    )
    add_check(
        checks,
        errors,
        "claim_and_access_boundaries",
        boundary_ok,
        error="A prohibited causal, execution, content, scope, or pixel claim was admitted.",
        mutation_state=state,
        pixel_payload_bytes=contract["pixel_payload_bytes"],
    )

    if isolated_ok and bracket_ok and schema_ok:
        evidence_state = "VERIFIED_ISOLATED_SCALAR_AMBIGUITY"
    elif not isolated_ok and focus_records:
        evidence_state = "VERIFIED_TEMPORAL_BOUNDARY"
    else:
        evidence_state = "MIXED_OR_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "source_records": len(records),
        "focus_activity_id": spec["focus_activity_id"],
        "focus_records": focus_records,
        "focus_record_count": len(focus_records),
        "physical_actions_touched": action_count,
        "focus_only_complete_actions": focus_only_complete_actions,
        "companion_records_needed_for_complete_actions": companion_records_needed,
        "focus_brackets": focus_brackets,
        "neighbor_contexts": contexts,
        "schema_activity_id_max_occurs": schema_max_occurs,
        "focus_within_nominal_plan_window": focus_within_nominal_window,
        "pixel_payload_bytes": receipt["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10b(root)
    mutation_names = load_json(root / "spec" / "stage10b.json")["hard_negatives"]
    mutations = {name: verify_stage10b(root, name) for name in mutation_names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 10B hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10B — Forward Look Representation Audit",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Complete Flight Day 6 raw crew-camera records: `{result['source_records']}`",
        f"- Forward Look facet records: `{result['focus_record_count']}`",
        f"- Physical five-frame actions touched: `{result['physical_actions_touched']}`",
        f"- Complete actions recoverable from the facet alone: `{result['focus_only_complete_actions']}`",
        f"- Sunset-tagged companion records needed: `{result['companion_records_needed_for_complete_actions']}`",
        f"- Official schema `activity_id` maximum occurrences: `{result['schema_activity_id_max_occurs']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "",
        "## Result",
        "",
        "The complete raw-image `Discussion #6: Forward Look` facet contains two isolated records. Each is one frame inside a different five-frame exposure bracket; its immediate same-camera neighbors and the other four bracket frames are tagged `24_Sunset`. The activity-only facet therefore recovers zero complete camera actions and needs eight records from another facet to reconstruct the two actions.",
        "",
        "The official schema permits one `activity_id` per `Observational_Intent`. That cardinality is a representation constraint, not proof of why these two assignments occurred. The records alone cannot distinguish overlapping intent, curation, or error, and the plan window is not execution evidence.",
        "",
        "## Claim ceiling",
        "",
        result["claim_ceiling"],
        "",
        "## Hard negatives",
        "",
    ]
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
        result = verify_stage10b(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(
            render_markdown(result)
            if args.command == "verify"
            else json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
