#!/usr/bin/env python3
"""Verify Stage 11C's plan-versus-realization boundary canary."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_json
from stage11b_paired_window_admission import verify_stage11b


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "plan_window_is_realized_event": False,
        "activity_id_is_image_content_truth": False,
        "transcript_envelope_is_single_target_ground_truth": False,
        "post_transition_actions_are_orientale_pixels": False,
        "preplan_actions_are_glushko_pixels": False,
        "model_partition_assigned": False,
        "performance_effect_inferred": False,
        "scientific_discovery_claimed": False,
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_plan_window_realized_event": ("plan_window_is_realized_event", True),
        "call_activity_id_image_content_truth": ("activity_id_is_image_content_truth", True),
        "call_transcript_envelope_single_target_ground_truth": ("transcript_envelope_is_single_target_ground_truth", True),
        "call_post_transition_actions_orientale_pixels": ("post_transition_actions_are_orientale_pixels", True),
        "call_preplan_actions_glushko_pixels": ("preplan_actions_are_glushko_pixels", True),
        "assign_model_partition_before_registration": ("model_partition_assigned", True),
        "claim_model_performance_effect": ("performance_effect_inferred", True),
        "call_boundary_result_scientific_discovery": ("scientific_discovery_claimed", True),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels_during_boundary_test": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def load_actions(path: Path, camera_serial: str) -> dict[str, list[dict[str, str]]]:
    actions: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["camera_serial"] == camera_serial:
                actions[row["action_id"]].append(row)
    return actions


def summarize(actions: dict[str, list[dict[str, str]]], start: datetime, end: datetime) -> dict[str, Any]:
    selected = {
        action_id: rows for action_id, rows in actions.items()
        if start <= parse_utc(rows[0]["action_start_utc"]) < end
    }
    source_rows = [row for rows in selected.values() for row in rows if row["collection_id"] == "data_source"]
    activities = Counter()
    for rows in selected.values():
        action_source = [row for row in rows if row["collection_id"] == "data_source"]
        values = {row["activity_id"] for row in action_source}
        if len(values) != 1:
            activities["<mixed>"] += 1
        else:
            activities[next(iter(values))] += 1
    return {
        "actions": len(selected),
        "exposures": len(source_rows),
        "products": sum(len(rows) for rows in selected.values()),
        "archive_size_bytes": sum(int(row["archive_size_bytes"]) for rows in selected.values() for row in rows),
        "activity_ids": dict(sorted(activities.items())),
    }


def exact_mapping(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    return actual == expected


def verify_stage11c(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11c.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    prior = verify_stage11b(root) if prior is None else prior
    add_check(checks, errors, "paired_window_admission_replays", prior["pass"], error="Stage 11B no longer verifies.")

    source = spec["source_contract"]
    transcript_path = root / source["transcript_path"]
    identity_ok = (
        transcript_path.stat().st_size == source["transcript_bytes"]
        and sha256_file(transcript_path) == source["transcript_sha256"]
    )
    add_check(checks, errors, "transcript_identity", identity_ok, error="The frozen transcript bytes changed.")

    with transcript_path.open(newline="", encoding="utf-8-sig") as handle:
        transcript = list(csv.DictReader(handle))
    anchors_ok = True
    for anchor in spec["anchors"].values():
        anchor_time = anchor["utc"].replace("T", " ").removesuffix("Z")
        anchors_ok &= any(row["utc"] == anchor_time and row["text"] == anchor["text"] for row in transcript)
    add_check(checks, errors, "content_led_transcript_anchors", anchors_ok,
              error="At least one frozen Glushko/diversion/Orientale transcript anchor changed.")

    actions = load_actions(root / source["relationship_manifest_path"], source["camera_serial"])
    anchor = {key: parse_utc(value["utc"]) for key, value in spec["anchors"].items()}
    schedule_start = parse_utc(spec["scheduled_window"]["start_utc"])
    schedule_end = parse_utc(spec["scheduled_window"]["end_utc"])
    segments = {
        "transcript_envelope": summarize(actions, anchor["realized_envelope_start"], anchor["realized_envelope_end"]),
        "scheduled_window": summarize(actions, schedule_start, schedule_end),
        "transcript_envelope_before_schedule": summarize(actions, anchor["realized_envelope_start"], schedule_start),
        "schedule_transcript_overlap": summarize(actions, schedule_start, anchor["realized_envelope_end"]),
        "scheduled_window_after_orientale_transition": summarize(actions, anchor["realized_envelope_end"], schedule_end),
        "explicit_internal_diversion": summarize(actions, anchor["explicit_diversion_start"], anchor["explicit_diversion_end"]),
    }
    segments_ok = exact_mapping(segments, spec["frozen_segments"])
    add_check(checks, errors, "plan_realization_segment_counts", segments_ok,
              error="The frozen plan/transcript segment counts changed.", segments=segments)

    overlap = segments["schedule_transcript_overlap"]["actions"]
    plan_actions = segments["scheduled_window"]["actions"]
    envelope_actions = segments["transcript_envelope"]["actions"]
    union_actions = (
        segments["transcript_envelope_before_schedule"]["actions"]
        + overlap
        + segments["scheduled_window_after_orientale_transition"]["actions"]
    )
    measures = {
        "scheduled_actions_before_transition_share": overlap / plan_actions,
        "scheduled_actions_after_transition_share": segments["scheduled_window_after_orientale_transition"]["actions"] / plan_actions,
        "transcript_envelope_actions_before_schedule_share": segments["transcript_envelope_before_schedule"]["actions"] / envelope_actions,
        "transcript_envelope_actions_inside_schedule_share": overlap / envelope_actions,
        "action_interval_jaccard": overlap / union_actions,
    }
    measures_ok = all(math.isclose(measures[key], expected, rel_tol=0.0, abs_tol=1e-15)
                      for key, expected in spec["frozen_overlap_measures"].items())
    add_check(checks, errors, "overlap_measures", measures_ok,
              error="The frozen plan/transcript action-overlap measures changed.", measures=measures)

    state = spec["mutation_state"]
    boundary_ok = not any(value for key, value in state.items() if key != "pixel_payload_bytes") and state["pixel_payload_bytes"] == 0
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited event, content, ground-truth, model, science, novelty, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_PLAN_REALIZATION_BOUNDARY_DIVERGENCE" if segments_ok and measures_ok else "PLAN_REALIZATION_BOUNDARY_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "segments": segments,
        "overlap_measures": measures, "disposition": spec["disposition"],
        "verified": "The second Glushko scheduled interval and the content-led transcript envelope select materially different complete-action cohorts. The activity_id changes at the scheduled boundary, while the spoken transition to Orientale occurs earlier than the scheduled end.",
        "decision_use": "Downgrade plan windows and activity_id values from content cohorts to navigation priors. Preserve Glushko as a promising paired-observation candidate, but require realized-segment and image-content registration before task construction.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage11b(root)
    baseline = verify_stage11c(root, prior=prior)
    names = load_json(root / "spec/stage11c.json")["hard_negatives"]
    mutations = {name: verify_stage11c(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11C hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    segments = result["segments"]
    measures = result["overlap_measures"]
    lines = ["# Stage 11C — Plan / Realization Boundary Canary", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Scheduled window: `{segments['scheduled_window']['actions']}` actions",
        f"- Transcript envelope: `{segments['transcript_envelope']['actions']}` actions",
        f"- Shared interval: `{segments['schedule_transcript_overlap']['actions']}` actions",
        f"- Transcript-envelope actions before schedule: `{segments['transcript_envelope_before_schedule']['actions']}` (`{measures['transcript_envelope_actions_before_schedule_share']:.3%}`)",
        f"- Scheduled actions after spoken Orientale transition: `{segments['scheduled_window_after_orientale_transition']['actions']}` (`{measures['scheduled_actions_after_transition_share']:.3%}`)",
        f"- Action-set interval Jaccard: `{measures['action_interval_jaccard']:.3%}`",
        f"- Explicit internal diversion: `{segments['explicit_internal_diversion']['actions']}` actions",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`", "", "## Verified", "", result["verified"],
        "", "## Decision use", "", result["decision_use"], "", "## Claim ceiling", "", result["claim_ceiling"],
        "", "## Hard negatives", ""]
    for name, mutation_result in result.get("hard_negatives", {}).items():
        lines.append(f"- `{name}`: {'REJECTED' if not mutation_result['pass'] else 'UNEXPECTEDLY ACCEPTED'}")
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11c(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
