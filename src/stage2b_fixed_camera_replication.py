#!/usr/bin/env python3
"""Verify Stage 2B fixed-camera replications without network access."""

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


def xml_text(path: Path, query: str) -> str | None:
    node = ET.parse(path).getroot().find(query, PDS_NS)
    return node.text if node is not None else None


def add_check(
    checks: list[dict[str, Any]], errors: list[str], check_id: str, passed: bool, **details: Any
) -> None:
    checks.append({"id": check_id, "pass": passed, **details})
    if not passed:
        errors.append(details.get("error", check_id))


def apply_mutation(
    spec: dict[str, Any], classification: dict[str, Any], mutation: str | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = copy.deepcopy(spec)
    classification = copy.deepcopy(classification)
    if mutation is None:
        return spec, classification
    if mutation == "shift_image_timestamps_plus_300_seconds":
        for event in classification["events"].values():
            for frame in event["frames"]:
                shifted = parse_utc(frame["time_utc"]) + timedelta(seconds=300)
                frame["time_utc"] = shifted.isoformat().replace("+00:00", "Z")
    elif mutation == "substitute_transcript_times_for_image_states":
        classification["oracle_source"] = "crew_transcript"
    elif mutation == "change_camera_inside_event":
        classification["camera"] = "Orion Solar Array Wing Camera 2"
    elif mutation == "invent_state_through_saturation_or_obstruction":
        classification["events"]["sunset"]["status"] = "ADMISSIBLE_PHYSICAL_TRANSITION"
        classification["events"]["sunset"]["frames"][-1]["state"] = "SUN_OCCULTED"
    elif mutation == "extend_frozen_sequence_after_pixel_inspection":
        frame = copy.deepcopy(classification["events"]["earthset"]["frames"][-1])
        frame["time_utc"] = "2026-04-06T22:44:14Z"
        classification["events"]["earthset"]["frames"].append(frame)
    elif mutation == "treat_availability_endpoint_as_physical_contact":
        spec["otr"]["field_semantics"] = "physical_contact"
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec, classification


def find_otr_targets(path: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(path)
    if not isinstance(payload, list):
        raise ValueError("OTR source is not a list")
    wanted = {"Earthset", "Sunset", "Sunrise"}
    matches: dict[str, dict[str, Any]] = {}
    for item in payload:
        target = item.get("target_properties", {})
        name = target.get("ltp_name")
        if name in wanted:
            if name in matches:
                raise ValueError(f"Duplicate OTR target: {name}")
            matches[name] = target
    if set(matches) != wanted:
        raise ValueError(f"Expected OTR targets {sorted(wanted)}, found {sorted(matches)}")
    return matches


def verify_frozen_identity(
    root: Path,
    identity: str,
    record: dict[str, Any],
    checks: list[dict[str, Any]],
    errors: list[str],
) -> Path:
    path = root / record["path"]
    observed = sha256_file(path) if path.is_file() else None
    add_check(
        checks,
        errors,
        f"{identity}_identity",
        observed == record["sha256"],
        observed_sha256=observed,
        error=f"{identity} identity mismatch",
    )
    return path


def derive_earthset(frames: list[dict[str, Any]]) -> dict[str, Any] | None:
    states = [frame["state"] for frame in frames]
    if states != [
        "FULL_VISIBLE",
        "FULL_VISIBLE",
        "FULL_VISIBLE",
        "FULL_VISIBLE",
        "PARTIAL",
        "PARTIAL",
        "PARTIAL",
        "NOT_VISIBLE",
    ]:
        return None
    return {
        "occultation_onset": {
            "lower_exclusive_utc": frames[3]["time_utc"],
            "upper_inclusive_utc": frames[4]["time_utc"],
        },
        "complete_disappearance": {
            "lower_exclusive_utc": frames[6]["time_utc"],
            "upper_inclusive_utc": frames[7]["time_utc"],
        },
        "terminal_state_check_utc": frames[7]["time_utc"],
    }


def verify_stage2b(root: Path, mutation: str | None = None) -> dict[str, Any]:
    original_spec = load_json(root / "spec" / "stage2b.json")
    if not isinstance(original_spec, dict):
        raise ValueError("Stage 2B spec is not an object")
    evidence = original_spec["evidence"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    acquisition_path = verify_frozen_identity(
        root, "acquisition_receipt", evidence["acquisition_receipt"], checks, errors
    )
    manifest_path = verify_frozen_identity(
        root, "source_manifest", evidence["source_manifest"], checks, errors
    )
    verify_frozen_identity(
        root, "label_scan_receipt", evidence["label_scan_receipt"], checks, errors
    )
    verify_frozen_identity(
        root, "label_scan_manifest", evidence["label_scan_manifest"], checks, errors
    )
    classification_path = verify_frozen_identity(
        root, "visual_classification", evidence["visual_classification"], checks, errors
    )

    acquisition = load_json(acquisition_path)
    manifest = load_json(manifest_path)
    classification_original = load_json(classification_path)
    if not all(isinstance(value, dict) for value in (acquisition, manifest, classification_original)):
        raise ValueError("Stage 2B evidence objects are malformed")

    acquisition_pass = (
        acquisition["status"] == "COMPLETED"
        and acquisition["spec_sha256"] == evidence["acquisition_contract_sha256"]
        and acquisition["aggregate_accepted_bytes"] == 29181381
        and acquisition["accepted_file_count"] == 24
        and acquisition["requested_file_count"] == 24
        and acquisition["per_event_accepted_bytes"]
        == {"earthset": 19569763, "sunset": 9611618, "sunrise": 0}
    )
    add_check(
        checks,
        errors,
        "bounded_acquisition_receipt",
        acquisition_pass,
        accepted_bytes=acquisition.get("aggregate_accepted_bytes"),
        accepted_files=acquisition.get("accepted_file_count"),
        error="Bounded acquisition receipt differs from the frozen result",
    )

    manifest_files = manifest.get("files", [])
    add_check(
        checks,
        errors,
        "source_manifest_cardinality",
        len(manifest_files) == 24,
        observed=len(manifest_files),
        error="Source manifest does not contain exactly 24 files",
    )
    for item in manifest_files:
        path = root / item["path"]
        present = path.is_file()
        observed_bytes = path.stat().st_size if present else None
        observed_hash = sha256_file(path) if present else None
        add_check(
            checks,
            errors,
            f"source_identity:{Path(item['path']).name}",
            present and observed_bytes == item["bytes"] and observed_hash == item["sha256"],
            error=f"Source identity mismatch: {item['path']}",
        )

    spec, classification = apply_mutation(original_spec, classification_original, mutation)
    oracle_pass = (
        classification.get("oracle_source") == "fixed_camera_image_state_transitions"
        and classification.get("camera") == spec["oracle"]["camera"]
        and spec["otr"]["field_semantics"] == "observation_availability_window"
    )
    add_check(
        checks,
        errors,
        "oracle_and_field_semantics",
        oracle_pass,
        error="The mutated evidence substitutes a disallowed oracle, camera, or endpoint meaning",
    )

    manifest_by_path = {item["path"]: item for item in manifest_files}
    event_specs = {event["event_id"]: event for event in spec["events"]}
    event_results: dict[str, dict[str, Any]] = {}
    for event_id in ("earthset", "sunset"):
        event_spec = event_specs[event_id]
        event_class = classification["events"][event_id]
        frames = event_class["frames"]
        selected = event_spec["selected_frames"]
        frame_count_pass = len(frames) == len(selected)
        add_check(
            checks,
            errors,
            f"{event_id}:frozen_frame_count",
            frame_count_pass,
            observed=len(frames),
            expected=len(selected),
            error=f"{event_id} frame sequence was widened or shortened",
        )
        times: list[datetime] = []
        for index, frame in enumerate(frames[: len(selected)]):
            selected_frame = selected[index]
            raw_path = root / selected_frame["raw_label_path"]
            raw_name = raw_path.name
            image_rel = f"evidence/stage2b/source/{event_id}/{frame['image']}"
            browse_label_rel = str(Path(image_rel).with_suffix(".xml")).replace("\\", "/")
            image_item = manifest_by_path.get(image_rel)
            browse_item = manifest_by_path.get(browse_label_rel)
            raw_lid = xml_text(raw_path, ".//pds:Identification_Area/pds:logical_identifier")
            raw_time = xml_text(raw_path, ".//pds:Time_Coordinates/pds:start_date_time")
            browse_path = root / browse_label_rel
            browse_file = xml_text(browse_path, ".//pds:File/pds:file_name") if browse_path.is_file() else None
            browse_reference = (
                xml_text(browse_path, ".//pds:Internal_Reference/pds:lid_reference")
                if browse_path.is_file()
                else None
            )
            raw_identity_pass = (
                raw_path.is_file()
                and raw_path.stat().st_size == selected_frame["bytes"]
                and sha256_file(raw_path) == selected_frame["sha256"]
                and raw_name == frame["raw_label"]
                and "_saw3_" in raw_name
            )
            label_binding_pass = (
                image_item is not None
                and browse_item is not None
                and browse_file == frame["image"]
                and browse_reference == raw_lid
                and raw_time == frame["time_utc"] == selected_frame["time_utc"]
            )
            add_check(
                checks,
                errors,
                f"{event_id}:raw_identity:{raw_name}",
                raw_identity_pass,
                error=f"Raw label identity mismatch: {raw_name}",
            )
            add_check(
                checks,
                errors,
                f"{event_id}:label_binding:{frame['image']}",
                label_binding_pass,
                error=f"Browse/raw/timestamp binding failed: {frame['image']}",
            )
            if raw_time is not None:
                times.append(parse_utc(raw_time))
        cadence = [
            (times[index] - times[index - 1]).total_seconds()
            for index in range(1, len(times))
        ]
        cadence_pass = len(times) == len(frames) and cadence == [30.0] * (len(frames) - 1)
        add_check(
            checks,
            errors,
            f"{event_id}:thirty_second_cadence",
            cadence_pass,
            observed_seconds=cadence,
            error=f"{event_id} is not a complete strict 30-second sequence",
        )
        event_results[event_id] = {
            "status": event_class["status"],
            "states": [frame["state"] for frame in frames],
            "frames": frames,
        }

    sunrise_class = classification["events"]["sunrise"]
    sunrise_pass = (
        event_specs["sunrise"]["source_disposition"] == "NOT_ADMISSIBLE_CAMERA_VIEW"
        and sunrise_class["status"] == "NOT_ADMISSIBLE_CAMERA_VIEW"
        and sunrise_class["frames"] == []
        and acquisition["per_event_accepted_bytes"]["sunrise"] == 0
    )
    add_check(
        checks,
        errors,
        "sunrise:pre_pixel_stop",
        sunrise_pass,
        error="Sunrise did not preserve its frozen pre-pixel stop",
    )
    event_results["sunrise"] = {
        "status": sunrise_class["status"],
        "states": [],
        "frames": [],
        "reason_code": "SOURCE_SEQUENCE_CANNOT_SUPPORT_STABILITY_CHECK",
    }

    earthset_frames = event_results["earthset"]["frames"]
    earthset_brackets = derive_earthset(earthset_frames)
    event_results["earthset"]["transition_brackets"] = earthset_brackets
    if earthset_brackets is not None:
        event_results["earthset"]["status"] = "VERIFIED_OVERLAP"

    sunset_states = event_results["sunset"]["states"]
    sunset_stop = (
        sunset_states == ["SUN_VISIBLE", "SUN_VISIBLE", "PARTIAL", "PARTIAL"]
        and event_results["sunset"]["status"] == "NOT_ADMISSIBLE_CAMERA_VIEW"
    )
    event_results["sunset"]["reason_code"] = "MISSING_TERMINAL_AND_STABILITY_STATE"
    add_check(
        checks,
        errors,
        "sunset:independent_stop",
        sunset_stop,
        observed_states=sunset_states,
        error="Sunset did not preserve the missing-terminal-state stop",
    )

    otr_path = root / spec["otr"]["path"]
    otr_identity = sha256_file(otr_path) if otr_path.is_file() else None
    add_check(
        checks,
        errors,
        "otr_identity",
        otr_identity == spec["otr"]["sha256"],
        observed_sha256=otr_identity,
        error="OTR identity mismatch",
    )
    otr_targets = find_otr_targets(otr_path)
    for event_id, target_name in (("earthset", "Earthset"), ("sunset", "Sunset"), ("sunrise", "Sunrise")):
        target = otr_targets[target_name]
        source_start = parse_utc(target["start_date_time"])
        source_end = parse_utc(target["end_date_time"])
        event_spec = event_specs[event_id]
        values_pass = (
            source_start == parse_utc(event_spec["otr_start_utc"])
            and source_end == parse_utc(event_spec["otr_end_utc"])
        )
        add_check(
            checks,
            errors,
            f"{event_id}:otr_source_values",
            values_pass,
            error=f"{event_id} OTR values differ from the frozen availability window",
        )
        event_results[event_id]["availability_window"] = {
            "start_utc": source_start.isoformat().replace("+00:00", "Z"),
            "end_utc": source_end.isoformat().replace("+00:00", "Z"),
            "duration_seconds": (source_end - source_start).total_seconds(),
        }

    earthset_relation = "UNESTABLISHED"
    guaranteed_overlap: float | None = None
    if earthset_brackets is not None:
        availability = event_results["earthset"]["availability_window"]
        availability_start = parse_utc(availability["start_utc"])
        availability_end = parse_utc(availability["end_utc"])
        observed_partial_times = [
            parse_utc(frame["time_utc"])
            for frame in earthset_frames
            if frame["state"] == "PARTIAL"
        ]
        partial_inside_window = [
            value for value in observed_partial_times if availability_start <= value <= availability_end
        ]
        if partial_inside_window:
            earthset_relation = "OVERLAPS_EVENT"
            guaranteed_overlap = (max(partial_inside_window) - availability_start).total_seconds()
    event_results["earthset"]["coverage_relation"] = earthset_relation
    event_results["earthset"]["minimum_guaranteed_overlap_seconds"] = guaranteed_overlap

    expected_events = spec["expected_result"]["events"]
    earthset_expected_pass = (
        event_results["earthset"]["status"] == expected_events["earthset"]["status"]
        and event_results["earthset"]["states"] == expected_events["earthset"]["states"]
        and earthset_brackets == expected_events["earthset"]["transition_brackets"]
        and earthset_relation == expected_events["earthset"]["coverage_relation"]
        and guaranteed_overlap == expected_events["earthset"]["minimum_guaranteed_overlap_seconds"]
        and abs(
            event_results["earthset"]["availability_window"]["duration_seconds"]
            - expected_events["earthset"]["availability_duration_seconds"]
        )
        <= 1e-6
    )
    add_check(
        checks,
        errors,
        "earthset:verified_overlap",
        earthset_expected_pass,
        observed_relation=earthset_relation,
        minimum_guaranteed_overlap_seconds=guaranteed_overlap,
        error="Earthset result differs from the frozen expected overlap",
    )
    stop_events_pass = (
        event_results["sunset"]["status"] == expected_events["sunset"]["status"]
        and event_results["sunset"]["states"] == expected_events["sunset"]["states"]
        and event_results["sunrise"]["status"] == expected_events["sunrise"]["status"]
        and event_results["sunrise"]["states"] == expected_events["sunrise"]["states"]
    )
    add_check(
        checks,
        errors,
        "independent_event_stops",
        stop_events_pass,
        error="Sunset or Sunrise stop differs from the frozen result",
    )

    admissible_count = sum(
        result["status"].startswith("VERIFIED_") for result in event_results.values()
    )
    pattern = "SINGLE_ADMISSIBLE_REPLICATION" if admissible_count == 1 else "UNESTABLISHED"
    pattern_pass = pattern == spec["expected_result"]["pattern"]
    add_check(
        checks,
        errors,
        "pattern_classification",
        pattern_pass,
        observed=pattern,
        admissible_replications=admissible_count,
        error="Pattern classification differs from the frozen expected result",
    )

    passed = not errors and all(item["pass"] for item in checks)
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": spec["expected_result"]["evidence_state"] if passed else "REJECTED",
        "disposition": spec["expected_result"]["disposition"] if passed else None,
        "pattern": pattern,
        "admissible_replications": admissible_count,
        "events": event_results,
        "acquisition": {
            "accepted_files": acquisition["accepted_file_count"],
            "accepted_bytes": acquisition["aggregate_accepted_bytes"],
            "aggregate_max_bytes": acquisition["aggregate_max_bytes"],
            "network_bytes_in_verification": 0,
        },
        "checks": checks,
        "errors": errors,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"]["if_single_admissible"] if passed else None,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage2b(root)
    spec = load_json(root / "spec" / "stage2b.json")
    if not isinstance(spec, dict):
        raise ValueError("Stage 2B spec is not an object")
    mutations = {name: verify_stage2b(root, name) for name in spec["hard_negatives"]}
    hard_negatives_pass = all(not item["pass"] for item in mutations.values())
    passed = baseline["pass"] and hard_negatives_pass
    return {
        "baseline": baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": passed,
        "evidence_state": "VERIFIED_SINGLE_ADMISSIBLE_REPLICATION" if passed else "FAILED",
    }


def render_markdown(verification: dict[str, Any]) -> str:
    baseline = verification["baseline"]
    earthset = baseline["events"]["earthset"]
    sunset = baseline["events"]["sunset"]
    brackets = earthset["transition_brackets"]
    lines = [
        "# Artemis II Observation-Execution Testbed — Stage 2B Result",
        "",
        f"- Verification: **{'PASS' if verification['pass'] else 'FAIL'}**",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Pattern classification: `{baseline['pattern']}`",
        f"- Admissible replications: **{baseline['admissible_replications']} of 3**",
        f"- Disposition: `{baseline.get('disposition') or 'UNSET'}`",
        "",
        "Only Earthset reaches the frozen physical-transition oracle. Its official observation availability window begins during the independently visible occultation, so Earthset is a bounded counterexample to the Earthrise non-overlap. Sunset and Sunrise stop independently; the result supports no repeated-pattern claim.",
        "",
        "## Earthset — verified overlap",
        "",
        "| PDS timestamp | Frozen state |",
        "| --- | --- |",
    ]
    for frame in earthset["frames"]:
        lines.append(f"| {frame['time_utc']} | {frame['state']} |")
    lines.extend(
        [
            "",
            f"- Occultation onset: `({brackets['occultation_onset']['lower_exclusive_utc']}, {brackets['occultation_onset']['upper_inclusive_utc']}]`",
            f"- Complete disappearance: `({brackets['complete_disappearance']['lower_exclusive_utc']}, {brackets['complete_disappearance']['upper_inclusive_utc']}]`",
            f"- Availability window: `[{earthset['availability_window']['start_utc']}, {earthset['availability_window']['end_utc']}]`",
            f"- Coverage relation: `{earthset['coverage_relation']}`",
            f"- Minimum guaranteed overlap: **{earthset['minimum_guaranteed_overlap_seconds']:.6f} seconds**",
            "",
            "The overlap is established because two observed PARTIAL frames occur after the availability window begins. The 30-second cadence still yields interval brackets rather than exact contact times.",
            "",
            "## Independent stops",
            "",
            f"- Sunset: `{sunset['status']}`. States: `{' -> '.join(sunset['states'])}`. The sequence ends before a fully occulted photosphere or following stability state.",
            "- Sunrise: `NOT_ADMISSIBLE_CAMERA_VIEW`. The complete label sequence cannot structurally supply the required post-clearance stability frame, so no pixels were acquired.",
            "",
            "## Burden",
            "",
            f"The bounded acquisition accepted {baseline['acquisition']['accepted_files']} files totaling {baseline['acquisition']['accepted_bytes']:,} bytes under a {baseline['acquisition']['aggregate_max_bytes']:,}-byte ceiling. Verification is local and uses zero network bytes.",
            "",
            "## Claim boundary",
            "",
            "Earthset disproves a uniform tested-event non-overlap, but one admissible replication cannot establish a recurrent placement pattern or explain why Earthrise and Earthset differ. OTR endpoints remain availability-window values, not physical contact times.",
            "",
            "## Next-step logic",
            "",
            f"{baseline['next_step_logic']}",
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
    parser.add_argument("--mutation", choices=(
        "shift_image_timestamps_plus_300_seconds",
        "substitute_transcript_times_for_image_states",
        "change_camera_inside_event",
        "invent_state_through_saturation_or_obstruction",
        "extend_frozen_sequence_after_pixel_inspection",
        "treat_availability_endpoint_as_physical_contact",
    ))
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        payload = verify_with_mutations(args.root)
    else:
        payload = verify_stage2b(args.root, args.mutation)
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
