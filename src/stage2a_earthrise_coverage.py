#!/usr/bin/env python3
"""Verify Stage 2A Earthrise image-transition coverage without network access."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file


UTC = timezone.utc
PDS_NS = {"pds": "http://pds.nasa.gov/pds4/pds/v1"}


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_utc(value: str) -> datetime:
    if value.endswith("Z"):
        return datetime.fromisoformat(value[:-1] + "+00:00")
    for pattern in ("%d %b %Y %H:%M:%S.%f", "%d %b %Y %H:%M:%S"):
        try:
            return datetime.strptime(value, pattern).replace(tzinfo=UTC)
        except ValueError:
            pass
    raise ValueError(f"Unsupported UTC timestamp: {value}")


def apply_mutation(
    spec: dict[str, Any], classification: dict[str, Any], mutation: str | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = copy.deepcopy(spec)
    classification = copy.deepcopy(classification)
    if mutation is None:
        return spec, classification
    if mutation == "shift_image_timestamps_plus_300_seconds":
        for frame in classification["frames"]:
            shifted = parse_utc(frame["time_utc"]) + timedelta(seconds=300)
            frame["time_utc"] = shifted.isoformat().replace("+00:00", "Z")
    elif mutation == "label_pre_event_frame_partial":
        classification["frames"][0]["state"] = "PARTIAL"
    elif mutation == "present_transcript_as_image_oracle":
        spec["oracle"]["kind"] = "crew_transcript"
    elif mutation == "widen_availability_window_to_event":
        spec["otr"]["start_utc"] = "2026-04-06T23:22:00Z"
        spec["otr"]["end_utc"] = "2026-04-06T23:24:00Z"
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec, classification


def xml_text(path: Path, query: str) -> str | None:
    node = ET.parse(path).getroot().find(query, PDS_NS)
    return node.text if node is not None else None


def find_earthrise_otr(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if not isinstance(payload, list):
        raise ValueError("OTR source is not a list")
    matches = [
        item["target_properties"]
        for item in payload
        if item.get("target_properties", {}).get("ltp_name") == "Earthrise"
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one Earthrise OTR target, found {len(matches)}")
    return matches[0]


def verify_stage2a(root: Path, mutation: str | None = None) -> dict[str, Any]:
    original_spec = load_json(root / "spec" / "stage2a.json")
    if not isinstance(original_spec, dict):
        raise ValueError("Stage 2A spec is not an object")
    oracle = original_spec["oracle"]
    classification_path = root / oracle["classification_path"]
    manifest_path = root / oracle["source_manifest_path"]
    contact_sheet_path = root / oracle["contact_sheet_path"]

    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    frozen_identities = [
        ("classification", classification_path, oracle["classification_sha256"]),
        ("source_manifest", manifest_path, oracle["source_manifest_sha256"]),
        ("contact_sheet", contact_sheet_path, oracle["contact_sheet_sha256"]),
    ]
    for identity, path, expected_hash in frozen_identities:
        observed_hash = sha256_file(path) if path.is_file() else None
        passed = observed_hash == expected_hash
        checks.append({"id": f"{identity}_identity", "pass": passed, "observed_sha256": observed_hash})
        if not passed:
            errors.append(f"{identity} identity mismatch")

    classification_original = load_json(classification_path)
    manifest = load_json(manifest_path)
    if not isinstance(classification_original, dict) or not isinstance(manifest, dict):
        raise ValueError("Stage 2A evidence objects are malformed")

    for item in manifest["files"]:
        path = root / item["path"]
        observed_hash = sha256_file(path) if path.is_file() else None
        observed_bytes = path.stat().st_size if path.is_file() else None
        passed = observed_hash == item["sha256"] and observed_bytes == item["bytes"]
        checks.append({"id": f"source_identity:{Path(item['path']).name}", "pass": passed})
        if not passed:
            errors.append(f"Source identity mismatch: {item['path']}")

    spec, classification = apply_mutation(original_spec, classification_original, mutation)
    if spec["oracle"]["kind"] != "fixed_camera_image_state_transitions":
        errors.append("Oracle is not the admitted fixed-camera image-state source")
    checks.append(
        {
            "id": "oracle_kind",
            "pass": spec["oracle"]["kind"] == "fixed_camera_image_state_transitions",
            "observed": spec["oracle"]["kind"],
        }
    )

    frames = classification["frames"]
    source_dir = root / "evidence" / "stage2a" / "source"
    observed_times: list[datetime] = []
    for frame in frames:
        image_path = source_dir / frame["image"]
        browse_label_path = image_path.with_suffix(".xml")
        raw_label_path = source_dir / frame["raw_label"]
        raw_time = xml_text(raw_label_path, ".//pds:Time_Coordinates/pds:start_date_time")
        browse_file = xml_text(browse_label_path, ".//pds:File/pds:file_name")
        browse_reference = xml_text(browse_label_path, ".//pds:Internal_Reference/pds:lid_reference")
        raw_lid = xml_text(raw_label_path, ".//pds:Identification_Area/pds:logical_identifier")
        label_binding = browse_file == frame["image"] and browse_reference == raw_lid
        timestamp_binding = raw_time == frame["time_utc"]
        checks.append({"id": f"label_binding:{frame['image']}", "pass": label_binding})
        checks.append({"id": f"timestamp_binding:{frame['image']}", "pass": timestamp_binding})
        if not label_binding:
            errors.append(f"Browse/raw label binding failed for {frame['image']}")
        if not timestamp_binding:
            errors.append(f"Timestamp binding failed for {frame['image']}")
        if raw_time is not None:
            observed_times.append(parse_utc(raw_time))

    expected_states = ["NOT_VISIBLE", "PARTIAL", "PARTIAL", "PARTIAL", "FULL_CLEAR", "FULL_CLEAR"]
    observed_states = [frame["state"] for frame in frames]
    sequence_pass = observed_states == expected_states
    checks.append({"id": "visual_state_sequence", "pass": sequence_pass, "observed": observed_states})
    if not sequence_pass:
        errors.append("Visual-state sequence does not match the frozen rise progression")

    cadence = [
        (observed_times[index] - observed_times[index - 1]).total_seconds()
        for index in range(1, len(observed_times))
    ]
    cadence_pass = len(observed_times) == len(frames) and cadence == [30.0] * (len(frames) - 1)
    checks.append({"id": "thirty_second_cadence", "pass": cadence_pass, "observed_seconds": cadence})
    if not cadence_pass:
        errors.append("Image timestamps are not a complete 30-second sequence")

    actual_brackets: dict[str, Any] | None = None
    if sequence_pass and cadence_pass:
        actual_brackets = {
            "first_visible_contact": {
                "lower_exclusive_utc": frames[0]["time_utc"],
                "upper_inclusive_utc": frames[1]["time_utc"],
            },
            "full_clearance": {
                "lower_exclusive_utc": frames[3]["time_utc"],
                "upper_inclusive_utc": frames[4]["time_utc"],
            },
            "stability_check_utc": frames[5]["time_utc"],
        }
    brackets_pass = actual_brackets == spec["expected_brackets"]
    checks.append({"id": "event_brackets", "pass": brackets_pass, "observed": actual_brackets})
    if not brackets_pass:
        errors.append("Derived event brackets differ from the frozen contract")

    otr_path = root / spec["otr"]["path"]
    otr_identity = sha256_file(otr_path) if otr_path.is_file() else None
    otr_identity_pass = otr_identity == spec["otr"]["sha256"]
    checks.append({"id": "otr_identity", "pass": otr_identity_pass, "observed_sha256": otr_identity})
    if not otr_identity_pass:
        errors.append("OTR identity mismatch")

    target = find_earthrise_otr(otr_path)
    source_start = parse_utc(target["start_date_time"])
    source_end = parse_utc(target["end_date_time"])
    expected_start = parse_utc(spec["otr"]["start_utc"])
    expected_end = parse_utc(spec["otr"]["end_utc"])
    otr_values_pass = source_start == expected_start and source_end == expected_end
    checks.append({"id": "otr_source_values", "pass": otr_values_pass})
    if not otr_values_pass:
        errors.append("OTR source values differ from the frozen availability window")

    relation = "UNESTABLISHED"
    minimum_separation_seconds: float | None = None
    availability_duration_seconds = (source_end - source_start).total_seconds()
    if actual_brackets is not None:
        event_latest_end = parse_utc(actual_brackets["full_clearance"]["upper_inclusive_utc"])
        event_earliest_start = parse_utc(actual_brackets["first_visible_contact"]["lower_exclusive_utc"])
        if source_start > event_latest_end:
            relation = "AFTER_EVENT_NO_OVERLAP"
            minimum_separation_seconds = (source_start - event_latest_end).total_seconds()
        elif source_end < event_earliest_start:
            relation = "BEFORE_EVENT_NO_OVERLAP"
            minimum_separation_seconds = (event_earliest_start - source_end).total_seconds()
        else:
            relation = "OVERLAP_OR_UNRESOLVED"

    expected = spec["expected_result"]
    result_pass = (
        relation == expected["coverage_relation"]
        and minimum_separation_seconds == expected["minimum_separation_seconds"]
        and abs(availability_duration_seconds - expected["availability_duration_seconds"]) <= 1e-6
    )
    checks.append(
        {
            "id": "coverage_relation",
            "pass": result_pass,
            "observed_relation": relation,
            "minimum_separation_seconds": minimum_separation_seconds,
        }
    )
    if not result_pass:
        errors.append("Coverage relation differs from the frozen expectation")

    passed = not errors and all(item["pass"] for item in checks)
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": expected["evidence_state"] if passed else "REJECTED",
        "disposition": expected["disposition"] if passed else None,
        "coverage_relation": relation,
        "minimum_separation_seconds": minimum_separation_seconds,
        "availability_window": {
            "start_utc": source_start.isoformat().replace("+00:00", "Z"),
            "end_utc": source_end.isoformat().replace("+00:00", "Z"),
            "duration_seconds": availability_duration_seconds,
        },
        "event_brackets": actual_brackets,
        "frames": frames,
        "checks": checks,
        "errors": errors,
        "claim_ceiling": spec["claim_ceiling"],
        "spice_branch": spec["spice_branch"],
        "next_step_logic": spec["next_step_logic"] if passed else None,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage2a(root)
    spec = load_json(root / "spec" / "stage2a.json")
    if not isinstance(spec, dict):
        raise ValueError("Stage 2A spec is not an object")
    mutations = {name: verify_stage2a(root, name) for name in spec["hard_negatives"]}
    hard_negatives_pass = all(not item["pass"] for item in mutations.values())
    passed = baseline["pass"] and hard_negatives_pass
    return {
        "baseline": baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": passed,
        "evidence_state": "VERIFIED_NO_OVERLAP" if passed else "FAILED",
    }


def render_markdown(verification: dict[str, Any]) -> str:
    baseline = verification["baseline"]
    brackets = baseline["event_brackets"]
    lines = [
        "# Artemis II Observation-Execution Testbed — Stage 2A Earthrise Result",
        "",
        f"- Verification: **{'PASS' if verification['pass'] else 'FAIL'}**",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Coverage relation: `{baseline['coverage_relation']}`",
        f"- Minimum separation: **{baseline['minimum_separation_seconds']:.0f} seconds**",
        f"- Disposition: `{baseline.get('disposition') or 'UNSET'}`",
        "",
        "The fixed SAW Cam 3 sequence places Earthrise completely before the official observation availability window. The result is interval-censored at 30 seconds; it is not an exact contact-time claim.",
        "",
        "## Independent image oracle",
        "",
        "| PDS timestamp | Frozen state | Bright-component corroboration |",
        "| --- | --- | ---: |",
    ]
    for frame in baseline["frames"]:
        lines.append(
            f"| {frame['time_utc']} | {frame['state']} | {frame['component_pixels']} pixels |"
        )
    lines.extend(
        [
            "",
            "## Derived brackets",
            "",
            f"- First visible contact: `({brackets['first_visible_contact']['lower_exclusive_utc']}, {brackets['first_visible_contact']['upper_inclusive_utc']}]`",
            f"- Full clearance: `({brackets['full_clearance']['lower_exclusive_utc']}, {brackets['full_clearance']['upper_inclusive_utc']}]`",
            f"- Stable full-clear check: `{brackets['stability_check_utc']}`",
            "",
            "## Coverage test",
            "",
            f"The OTR availability window is `{baseline['availability_window']['start_utc']}` to `{baseline['availability_window']['end_utc']}` ({baseline['availability_window']['duration_seconds']:.6f} seconds). Its start is 136 seconds after the latest possible full-clearance time, so overlap is impossible within the frozen image brackets.",
            "",
            "This does **not** mean the OTR endpoints were intended as contact times, and it does not establish why the window was placed later.",
            "",
            "## Independence and limits",
            "",
            "The oracle is partially independent: transcript review nominated the small time neighborhood, but the scored states and timestamps come only from a fixed Orion camera and PDS4 labels. The human visual classification is hash-pinned and corroborated by a stable image footprint; the 30-second sampling prevents exact contact times.",
            "",
            f"SPICE status: `{baseline['spice_branch']['status']}` — {baseline['spice_branch']['reason']}",
            "",
            "## Next-step logic",
            "",
            f"**Recommended:** {baseline['next_step_logic']['recommended']}",
            "",
            f"Why: {baseline['next_step_logic']['why']}",
            "",
            f"Alternative: {baseline['next_step_logic']['alternative']}",
            "",
            f"Fallback: {baseline['next_step_logic']['fallback']}",
            "",
            "## Hard negatives",
            "",
        ]
    )
    for name, result in verification["hard_negatives"].items():
        lines.append(f"- `{name}`: {'REJECTED' if not result['pass'] else 'UNEXPECTEDLY ACCEPTED'}")
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
    parser.add_argument(
        "--mutation",
        choices=(
            "shift_image_timestamps_plus_300_seconds",
            "label_pre_event_frame_partial",
            "present_transcript_as_image_oracle",
            "widen_availability_window_to_event",
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        payload = verify_with_mutations(args.root)
    else:
        payload = verify_stage2a(args.root, args.mutation)
    if args.json_output:
        write_json(args.json_output, payload)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        text = render_markdown(payload) if args.command == "verify" else json.dumps(payload, indent=2) + "\n"
        args.markdown_output.write_text(text, encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
