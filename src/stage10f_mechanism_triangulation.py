#!/usr/bin/env python3
"""Verify Stage 10F's plan/execution/curation mechanism triangulation."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_json, parse_utc


UTC = timezone.utc


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "human_override_declared_proven": False,
        "crew_choice_declared_wrong": False,
        "discussion_declared_correct": False,
        "missing_target_declared_default": False,
        "image_content_inferred": False,
        "schema_declared_causal": False,
        "scope": "thirteen_action_repeated_signature",
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "declare_human_override_proven":
        state["human_override_declared_proven"] = True
    elif mutation == "declare_crew_choice_labels_wrong":
        state["crew_choice_declared_wrong"] = True
    elif mutation == "declare_discussion_labels_correct":
        state["discussion_declared_correct"] = True
    elif mutation == "treat_every_missing_target_as_an_unoverridden_default":
        state["missing_target_declared_default"] = True
    elif mutation == "infer_image_content_from_transcript":
        state["image_content_inferred"] = True
    elif mutation == "claim_scalar_schema_caused_partial_curation":
        state["schema_declared_causal"] = True
    elif mutation == "generalize_mechanism_to_every_archive_fracture":
        state["scope"] = "every_archive_fracture"
    elif mutation == "open_pixels_to_reconstruct_edit_history":
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


def parse_request_time(value: str) -> datetime:
    return datetime.strptime(value, "%d %b %Y %H:%M:%S").replace(tzinfo=UTC)


def find_request(root: Path, path: str, name: str) -> dict[str, Any] | None:
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


def verify_stage10f(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10f.json"), mutation)
    contract = spec["source_contract"]
    expected = spec["frozen_observables"]
    receipt = load_json(root / contract["receipt_path"])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    receipt_failures = verify_receipt(root, receipt)
    parent_sources = receipt.get("external_parent_sources", [])
    parent_ok = len(parent_sources) == 1 and (
        parent_sources[0].get("url") == contract["ntrs_download_url"]
        and parent_sources[0].get("bytes") == contract["parent_report_bytes"]
        and parent_sources[0].get("sha256") == contract["parent_report_sha256"]
    )
    add_check(
        checks,
        errors,
        "source_identity",
        receipt.get("status") == "COMPLETED" and not receipt_failures and parent_ok,
        error="A Stage 10F source byte, focused-report parent identity, or receipt changed.",
        failures=receipt_failures,
        parent_ok=parent_ok,
    )

    stage10c = load_json(root / contract["stage10c_result_path"])
    run = stage10c.get("repeated_signature_run", [])
    signature_ok = (
        stage10c.get("pass") is True
        and len(run) == expected["repeated_actions"]
        and sum(len(item["file_names"]) for item in run) == expected["repeated_frames"]
        and run[0]["start_time"] == expected["signature_start"]
        and run[-1]["end_time"] == expected["signature_end"]
        and all(item["activity_ids"] == expected["signature_activity_ids"] for item in run)
        and all(item["target_ids"] == expected["signature_target_ids"] for item in run)
        and all(item["bracket_values"] == expected["signature_bracket_values"] for item in run)
    )
    discussion_target_pairs = sum(
        activity == "15_Discussion #4: Terminator" and target == "Terminator"
        for item in run
        for activity, target in zip(item["activity_ids"], item["target_ids"])
    )
    crew_missing_pairs = sum(
        activity == "14_Crew Choice #2" and target is None
        for item in run
        for activity, target in zip(item["activity_ids"], item["target_ids"])
    )
    signature_ok = (
        signature_ok
        and discussion_target_pairs == expected["discussion_frames_with_terminator_target"]
        and crew_missing_pairs == expected["crew_choice_frames_without_target"]
    )
    add_check(
        checks,
        errors,
        "repeated_joint_metadata_signature",
        signature_ok,
        error="The thirteen-action exposure-position/activity/target signature did not reproduce.",
        actions=len(run),
        frames=sum(len(item["file_names"]) for item in run),
        discussion_terminator_pairs=discussion_target_pairs,
        crew_choice_missing_target_pairs=crew_missing_pairs,
    )

    guide = " ".join(
        (root / contract["user_guide_text_path"])
        .read_text(encoding="utf-8", errors="replace")
        .lower()
        .split()
    )
    procedure_ok = all(
        phrase in guide
        for phrase in (
            "by comparing the timeline in the ltp with the timestamp of each data item",
            "a human analyst noted a specific scheduled activity that differed from the ltp timeline activity",
            "the analyst designated activity overrides the ltp timeline activity",
            "through visual inspection and manual tagging using lunar targeting plan target names for only a subset of images",
            "not thoroughly verified post-mission and may contain errors",
        )
    )
    add_check(
        checks,
        errors,
        "official_two_path_generation_procedure",
        procedure_ok,
        error="The official timestamp, human-override, or manual target-tag procedure did not reproduce.",
    )

    crew_request = find_request(root, contract["outgoing_target_request_path"], "Crew Choice #2")
    discussion_request = find_request(
        root, contract["outgoing_target_request_path"], "Discussion #4: Terminator"
    )
    request_ok = (
        crew_request is not None
        and discussion_request is not None
        and crew_request.get("request_date_time") == expected["crew_choice_request_time"]
        and crew_request.get("request_duration") == expected["crew_choice_request_duration_minutes"]
        and discussion_request.get("request_date_time") == expected["discussion_request_time"]
        and discussion_request.get("request_duration") == expected["discussion_request_duration_minutes"]
    )
    crew_start = parse_request_time(expected["crew_choice_request_time"])
    crew_end = crew_start + timedelta(minutes=expected["crew_choice_request_duration_minutes"])
    signature_start = parse_utc(expected["signature_start"])
    signature_end = parse_utc(expected["signature_end"])
    signature_inside_request = crew_start <= signature_start <= signature_end < crew_end
    add_check(
        checks,
        errors,
        "request_timing_context",
        request_ok and signature_inside_request,
        error="The archived request timing or repeated-signature relation changed.",
        signature_inside_crew_choice_request=signature_inside_request,
        crew_choice_request_start=crew_start.isoformat(),
        crew_choice_request_end=crew_end.isoformat(),
    )

    with (root / contract["transcript_path"]).open(encoding="utf-8-sig", newline="") as handle:
        transcript = list(csv.DictReader(handle))
    by_time = {row["utc"]: row["text"] for row in transcript}
    missing_cues = [
        [utc, phrase]
        for utc, phrase in expected["transcript_cues"]
        if phrase.lower() not in by_time.get(utc, "").lower()
    ]
    first_cue = datetime.strptime(expected["transcript_cues"][0][0], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=UTC)
    cue_precedes_signature = first_cue < signature_start
    add_check(
        checks,
        errors,
        "contemporaneous_execution_context",
        not missing_cues and cue_precedes_signature,
        error="The contemporaneous terminator-discussion cues or their timing changed.",
        missing_cues=missing_cues,
        first_terminator_cue_precedes_signature=cue_precedes_signature,
    )

    report_text = " ".join(
        (root / contract["report_page_text_path"])
        .read_text(encoding="utf-8", errors="replace")
        .lower()
        .split()
    )
    report_ok = all(
        phrase in report_text
        for phrase in (
            "figure 4.1: as-executed timeline",
            "crew choice",
            "discussion #4: terminator",
            "the eye icon indicates the crew member making observations with the unaided eye",
            "the camera icon indicates the crew member making observations with a camera",
        )
    )
    add_check(
        checks,
        errors,
        "nasa_as_executed_timeline_context",
        report_ok,
        error="NASA's focused as-executed timeline page did not reproduce.",
    )

    state = spec["mutation_state"]
    boundary_ok = (
        not any(
            state[key]
            for key in (
                "human_override_declared_proven",
                "crew_choice_declared_wrong",
                "discussion_declared_correct",
                "missing_target_declared_default",
                "image_content_inferred",
                "schema_declared_causal",
            )
        )
        and state["scope"] == "thirteen_action_repeated_signature"
        and contract["pixel_payload_bytes"] == 0
        and receipt["pixel_payload_bytes"] == 0
    )
    add_check(
        checks,
        errors,
        "claim_and_access_boundaries",
        boundary_ok,
        error="A prohibited edit-history, correctness, content, causal, scope, or pixel claim was admitted.",
        mutation_state=state,
        pixel_payload_bytes=contract["pixel_payload_bytes"],
    )

    alignment_holds = all(
        check["pass"]
        for check in checks
        if check["id"]
        in {
            "repeated_joint_metadata_signature",
            "official_two_path_generation_procedure",
            "request_timing_context",
            "contemporaneous_execution_context",
            "nasa_as_executed_timeline_context",
        }
    )
    evidence_state = (
        "SUPPORTED_PARTIAL_PER_FRAME_CURATION_SIGNATURE"
        if alignment_holds
        else "MECHANISM_ALIGNMENT_NOT_SUPPORTED"
    )
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "repeated_actions": len(run),
        "repeated_frames": sum(len(item["file_names"]) for item in run),
        "signature_start": run[0]["start_time"] if run else None,
        "signature_end": run[-1]["end_time"] if run else None,
        "discussion_frames_with_terminator_target": discussion_target_pairs,
        "crew_choice_frames_without_target": crew_missing_pairs,
        "signature_inside_crew_choice_request": signature_inside_request,
        "verified": spec["mechanism_states"]["verified"],
        "supported_inference": spec["mechanism_states"]["supported_inference"],
        "alternative_explanations": spec["mechanism_states"]["alternative_explanations"],
        "decision_use": spec["mechanism_states"]["decision_use"],
        "pixel_payload_bytes": receipt["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10f(root)
    names = load_json(root / "spec" / "stage10f.json")["hard_negatives"]
    mutations = {name: verify_stage10f(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 10F hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10F — Plan / Execution / Curation Triangulation",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Repeated actions / frames: `{result['repeated_actions']}` / `{result['repeated_frames']}`",
        f"- Discussion + Terminator frames: `{result['discussion_frames_with_terminator_target']}`",
        f"- Crew Choice + missing-target frames: `{result['crew_choice_frames_without_target']}`",
        f"- Signature lies inside archived Crew Choice request window: `{result['signature_inside_crew_choice_request']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "",
        "## Verified",
        "",
        result["verified"],
        "",
        "## Strongest supported explanation",
        "",
        result["supported_inference"],
        "",
        "## Live alternatives",
        "",
    ]
    for alternative in result["alternative_explanations"]:
        lines.append(f"- {alternative}")
    lines.extend(
        [
            "",
            "## Decision use",
            "",
            result["decision_use"],
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
        result = verify_stage10f(args.root.resolve(), args.mutation)
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
