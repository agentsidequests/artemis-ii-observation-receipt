#!/usr/bin/env python3
"""Verify Stage 10A's complete-denominator activity-facet integrity test."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file


PDS_KEYS = {
    "flight_day": "msn:Mission_Information/msn:flight_day_number",
    "activity_id": "msn_surface:Observational_Intent/msn_surface:activity_id",
    "target_id": "msn_surface:Observational_Intent/msn_surface:target_id",
    "serial": "img_surface:Instrument_Information/img_surface:instrument_serial_number",
    "shutter_count": "cots_camera:Camera_Properties/cots_camera:shutter_count",
    "file_number": "cots_camera:File_Information/cots_camera:file_number",
    "shooting_mode": "cots_camera:Camera_Settings/cots_camera:shooting_mode",
    "auto_bracket_order": "cots_camera:Exposure/cots_camera:auto_bracket_order",
    "bracket_value": "cots_camera:Exposure/cots_camera:exposure_bracket_value",
    "focal_length": "img:Optical_Properties/img:focal_length",
    "iso": "img:ISO/img:iso_number",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


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


def pds_value(source: dict[str, Any], field: str) -> str | None:
    value = source.get("pds4_label", {}).get(PDS_KEYS[field])
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value) if value is not None else None


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "correct_activity_inferred": False,
        "image_content_inferred_from_missing_target": False,
        "oracle": "camera-native complete five-exposure bracket",
        "scope": "flight_day_6_complete_brackets",
        "pixel_data_declared_invalid": False,
        "pds_validation_declared_semantic": False,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "infer_correct_activity_from_bracket_majority":
        state["correct_activity_inferred"] = True
    elif mutation == "treat_target_id_absence_as_wrong_image_content":
        state["image_content_inferred_from_missing_target"] = True
    elif mutation == "use_otr_windows_as_execution_truth":
        state["oracle"] = "operational timeline report window"
    elif mutation == "count_incomplete_or_nonconsecutive_brackets":
        mutated["complete_bracket_contract"]["frame_count"] = 4
    elif mutation == "generalize_fd6_bracket_rate_to_all_archive_products":
        state["scope"] = "all_archive_products"
    elif mutation == "claim_metadata_fragmentation_invalidates_pixel_data":
        state["pixel_data_declared_invalid"] = True
    elif mutation == "claim_pds_validation_guarantees_semantic_label_correctness":
        state["pds_validation_declared_semantic"] = True
    elif mutation == "open_pixels_to_resolve_activity_identity":
        mutated["source_contract"]["pixel_payload_bytes"] = 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_source_identity(root: Path, receipt: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    records = list(receipt.get("sources", []))
    for page in receipt.get("atlas_pages", []):
        records.extend(
            [
                {
                    "path": page["request_path"],
                    "bytes": page["request_bytes"],
                    "sha256": page["request_sha256"],
                },
                {
                    "path": page["response_path"],
                    "bytes": page["response_bytes"],
                    "sha256": page["response_sha256"],
                },
            ]
        )
    for record in records:
        path = root / record["path"]
        if not path.is_file():
            failures.append(f"missing:{record['path']}")
            continue
        if path.stat().st_size != record["bytes"]:
            failures.append(f"bytes:{record['path']}")
        if sha256_file(path) != record["sha256"]:
            failures.append(f"sha256:{record['path']}")
    return failures


def load_hits(root: Path, receipt: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    hits: list[dict[str, Any]] = []
    errors: list[str] = []
    for page in receipt.get("atlas_pages", []):
        payload = load_json(root / page["response_path"])
        page_hits = payload.get("hits", {}).get("hits", [])
        total = payload.get("hits", {}).get("total", {}).get("value")
        if total != 8423:
            errors.append(f"total:{page['page_index']}:{total}")
        if len(page_hits) != page["hits"]:
            errors.append(f"page_hits:{page['page_index']}:{len(page_hits)}")
        hits.extend(page_hits)
    return hits, errors


def normalize_hit(hit: dict[str, Any]) -> dict[str, Any]:
    source = hit.get("_source", {})
    record = {
        "id": hit.get("_id"),
        "file_name": source.get("gather", {}).get("pds_archive", {}).get("file_name"),
        "time": source.get("gather", {}).get("time", {}).get("start_time"),
        "bundle_id": source.get("bundle_id"),
        "collection_id": source.get("collection_id"),
        **{field: pds_value(source, field) for field in PDS_KEYS},
    }
    record["instrument_serial_number"] = record["serial"]
    record["iso_number"] = record["iso"]
    return record


def integer(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def bracket_from_window(
    window: list[dict[str, Any]], contract: dict[str, Any]
) -> dict[str, Any] | None:
    if len(window) != contract["frame_count"]:
        return None
    if [item["bracket_value"] for item in window] != contract["required_bracket_values"]:
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
        assert all(value is not None for value in values)
        if values != list(range(values[0], values[0] + contract["frame_count"])):
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
    nonempty_activities = {value for value in activities if value}
    nonempty_targets = {value for value in targets if value}
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
        "activity_facet_fracture": len(nonempty_activities) > 1,
        "target_presence_fracture": 0 < len([value for value in targets if value]) < len(window),
        "target_value_fracture": len(nonempty_targets) > 1,
    }


def detect_complete_brackets(
    records: list[dict[str, Any]], contract: dict[str, Any]
) -> list[dict[str, Any]]:
    by_serial: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["serial"] is not None and integer(record["shutter_count"]) is not None:
            by_serial[record["serial"]].append(record)
    brackets: list[dict[str, Any]] = []
    for serial_records in by_serial.values():
        serial_records.sort(key=lambda item: integer(item["shutter_count"]) or -1)
        index = 0
        while index <= len(serial_records) - contract["frame_count"]:
            window = serial_records[index : index + contract["frame_count"]]
            bracket = bracket_from_window(window, contract)
            if bracket is None:
                index += 1
            else:
                brackets.append(bracket)
                index += contract["frame_count"]
    return sorted(brackets, key=lambda item: (item["start_time"], item["serial"]))


def verify_stage10a(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10a.json"), mutation)
    receipt = load_json(root / "evidence" / "stage10a" / "acquisition-receipt.json")
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    source_failures = verify_source_identity(root, receipt)
    add_check(
        checks,
        errors,
        "source_identity",
        not source_failures,
        error="A Stage 10A source byte or receipt identity changed.",
        failures=source_failures,
    )

    hits, page_errors = load_hits(root, receipt)
    ids = [hit.get("_id") for hit in hits]
    denominator_ok = (
        not page_errors
        and len(hits) == spec["source_contract"]["expected_hits"] == 8423
        and len(set(ids)) == len(ids)
        and len(receipt.get("atlas_pages", [])) == spec["source_contract"]["expected_pages"]
    )
    add_check(
        checks,
        errors,
        "complete_unique_denominator",
        denominator_ok,
        error="The complete 8,423-record denominator was not reproduced.",
        records=len(hits),
        unique_ids=len(set(ids)),
        page_errors=page_errors,
    )

    records = [normalize_hit(hit) for hit in hits]
    cohort_errors = [
        record["id"]
        for record in records
        if record["bundle_id"] != "artemis2_crew_camera"
        or record["collection_id"] != "data_raw"
        or record["flight_day"] != "6"
    ]
    add_check(
        checks,
        errors,
        "cohort_contract",
        not cohort_errors,
        error="One or more records fell outside the frozen Flight Day 6 raw crew-camera cohort.",
        failures=cohort_errors[:20],
    )

    query = load_json(root / spec["source_contract"]["atlas_query_path"])
    query_ok = (
        query.get("size") == spec["source_contract"]["page_size"] == 1000
        and query.get("track_total_hits") is True
        and query.get("sort") == [{"gather.time.start_time": {"order": "asc"}}]
    )
    add_check(
        checks,
        errors,
        "frozen_query_contract",
        query_ok,
        error="The Atlas query no longer matches the complete-denominator contract.",
    )

    official_text = (
        root / spec["source_contract"]["label_definitions_path"]
    ).read_text(encoding="utf-8", errors="replace").lower()
    official_semantics_ok = all(
        phrase in official_text
        for phrase in (
            "identifier specifying the activity this observation is a part of",
            "visual inspection and manual tagging",
            "not thoroughly verified post-mission and may contain errors",
        )
    )
    add_check(
        checks,
        errors,
        "official_field_semantics_and_limit",
        official_semantics_ok,
        error="The official activity meaning or target-tag limitation was not preserved.",
    )

    contract = spec["complete_bracket_contract"]
    contract_ok = (
        contract.get("frame_count") == 5
        and contract.get("required_bracket_values") == ["0", "-2", "-1", "+1", "+2"]
        and contract.get("required_auto_bracket_order") == "0,-,+"
        and contract.get("consecutive_integer_fields") == ["shutter_count", "file_number"]
        and contract.get("maximum_span_seconds") == 10.0
    )
    add_check(
        checks,
        errors,
        "camera_native_complete_bracket_oracle",
        contract_ok,
        error="The camera-native complete-bracket oracle was weakened or changed.",
    )

    brackets = detect_complete_brackets(records, contract) if contract_ok else []
    activity_fractures = [item for item in brackets if item["activity_facet_fracture"]]
    target_presence_fractures = [item for item in brackets if item["target_presence_fracture"]]
    target_value_fractures = [item for item in brackets if item["target_value_fracture"]]
    known_files = set(spec["baseline"]["known_case"])
    known_matches = [item for item in brackets if set(item["file_names"]) == known_files]
    known_case_ok = (
        len(known_matches) == 1
        and known_matches[0]["activity_ids"]
        == [
            "24_Sunset",
            "25_Discussion #6: Forward Look",
            "24_Sunset",
            "24_Sunset",
            "24_Sunset",
        ]
        and known_matches[0]["activity_facet_fracture"]
    )
    add_check(
        checks,
        errors,
        "known_case_reproduction",
        known_case_ok,
        error="The predeclared known fractured bracket was not reproduced exactly once.",
    )

    state = spec["mutation_state"]
    boundary_ok = (
        state["correct_activity_inferred"] is False
        and state["image_content_inferred_from_missing_target"] is False
        and state["oracle"] == "camera-native complete five-exposure bracket"
        and state["scope"] == "flight_day_6_complete_brackets"
        and state["pixel_data_declared_invalid"] is False
        and state["pds_validation_declared_semantic"] is False
        and spec["source_contract"]["pixel_payload_bytes"] == 0
        and receipt["pixel_payload_bytes"] == 0
    )
    add_check(
        checks,
        errors,
        "claim_and_access_boundaries",
        boundary_ok,
        error="A hard-negative inference, scope expansion, or pixel access was admitted.",
        pixel_payload_bytes=spec["source_contract"]["pixel_payload_bytes"],
        mutation_state=state,
    )

    evidence_state = (
        "VERIFIED_ACTIVITY_FACET_FRAGMENTATION"
        if activity_fractures
        else "VERIFIED_NO_ACTIVITY_FRACTURE_IN_COMPLETE_BRACKETS"
    )
    rate = len(activity_fractures) / len(brackets) if brackets else None
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "source_records": len(records),
        "complete_brackets": len(brackets),
        "activity_fractured_brackets": len(activity_fractures),
        "activity_fracture_rate": rate,
        "target_presence_fractured_brackets": len(target_presence_fractures),
        "target_value_fractured_brackets": len(target_value_fractures),
        "pixel_payload_bytes": receipt["pixel_payload_bytes"],
        "activity_fractures": activity_fractures,
        "target_presence_fractures": target_presence_fractures,
        "target_value_fractures": target_value_fractures,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10a(root)
    mutation_names = load_json(root / "spec" / "stage10a.json")["hard_negatives"]
    mutations = {name: verify_stage10a(root, name) for name in mutation_names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 10A hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    rate = result["activity_fracture_rate"]
    rate_text = "n/a" if rate is None else f"{rate:.4%}"
    lines = [
        "# Stage 10A — Exposure-Bracket Metadata Integrity",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Complete Flight Day 6 raw crew-camera records: `{result['source_records']}`",
        f"- Qualifying complete five-frame brackets: `{result['complete_brackets']}`",
        f"- Activity-fractured brackets: `{result['activity_fractured_brackets']}` (`{rate_text}`)",
        f"- Target-presence-fractured brackets: `{result['target_presence_fractured_brackets']}`",
        f"- Target-value-fractured brackets: `{result['target_value_fractured_brackets']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "",
        "## Result",
        "",
    ]
    if result["activity_fractured_brackets"]:
        lines.append(
            "At least one camera-native five-exposure bracket is divided across multiple `activity_id` values. The archive therefore preserves the files while fragmenting one physical camera action across search facets in this qualified cohort."
        )
    else:
        lines.append(
            "No activity-facet fracture was found in the qualified complete-bracket cohort."
        )
    lines.extend(["", "## Activity-fractured brackets", ""])
    for bracket in result["activity_fractures"]:
        lines.extend(
            [
                f"- `{bracket['start_time']}` — `{bracket['serial']}`",
                f"  - Files: `{', '.join(bracket['file_names'])}`",
                f"  - Activity IDs: `{bracket['activity_ids']}`",
                f"  - Target IDs: `{bracket['target_ids']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Claim ceiling",
            "",
            result["claim_ceiling"],
            "",
            "## Hard negatives",
            "",
        ]
    )
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
        result = verify_stage10a(args.root.resolve(), args.mutation)
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
