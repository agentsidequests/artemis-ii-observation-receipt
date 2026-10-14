#!/usr/bin/env python3
"""Verify Stage 11D's Sunset planned-block context extension canary."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_json
from stage11c_plan_realization_boundary import parse_utc, verify_stage11c


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "connected_context_is_complete_event": False,
        "all_context_actions_are_sunset_pixels": False,
        "plan_window_is_invalid": False,
        "outside_actions_are_new_sunset_events": False,
        "target_tag_is_image_truth": False,
        "model_partition_assigned": False,
        "observed_model_leakage_claimed": False,
        "scientific_discovery_claimed": False,
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_connected_context_complete_event": ("connected_context_is_complete_event", True),
        "call_all_context_actions_sunset_pixels": ("all_context_actions_are_sunset_pixels", True),
        "call_plan_window_invalid": ("plan_window_is_invalid", True),
        "call_outside_actions_new_sunset_events": ("outside_actions_are_new_sunset_events", True),
        "call_target_tag_image_truth": ("target_tag_is_image_truth", True),
        "assign_model_partition_from_context": ("model_partition_assigned", True),
        "claim_observed_model_leakage": ("observed_model_leakage_claimed", True),
        "call_boundary_result_scientific_discovery": ("scientific_discovery_claimed", True),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels_during_context_test": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def load_actions(path: Path) -> dict[str, list[dict[str, str]]]:
    actions: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            actions[row["action_id"]].append(row)
    return actions


def summarize(actions: dict[str, list[dict[str, str]]], start: Any, end: Any) -> dict[str, Any]:
    selected = {key: rows for key, rows in actions.items() if start <= parse_utc(rows[0]["action_start_utc"]) < end}
    def values(field: str) -> dict[str, int]:
        counts = Counter()
        for rows in selected.values():
            source_rows = [row for row in rows if row["collection_id"] == "data_source"]
            distinct = {row[field] or "<blank>" for row in source_rows}
            counts[next(iter(distinct)) if len(distinct) == 1 else "<mixed>"] += 1
        return dict(sorted(counts.items()))
    return {
        "actions": len(selected),
        "exposures": sum(sum(row["collection_id"] == "data_source" for row in rows) for rows in selected.values()),
        "products": sum(len(rows) for rows in selected.values()),
        "archive_size_bytes": sum(int(row["archive_size_bytes"]) for rows in selected.values() for row in rows),
        "camera_serials": values("camera_serial"),
        "activity_ids": values("activity_id"),
        "target_ids": values("target_id"),
    }


def verify_stage11d(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11d.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    prior = verify_stage11c(root) if prior is None else prior
    add_check(checks, errors, "plan_realization_boundary_replays", prior["pass"], error="Stage 11C no longer verifies.")

    source = spec["source_contract"]
    transcript_path = root / source["transcript_path"]
    identity_ok = transcript_path.stat().st_size == source["transcript_bytes"] and sha256_file(transcript_path) == source["transcript_sha256"]
    add_check(checks, errors, "transcript_identity", identity_ok, error="The frozen Sunset transcript bytes changed.")
    with transcript_path.open(newline="", encoding="utf-8-sig") as handle:
        transcript = list(csv.DictReader(handle))
    anchors_ok = all(any(row["utc"] == item["utc"].replace("T", " ").removesuffix("Z") and row["text"] == item["text"] for row in transcript)
                     for item in spec["anchors"].values())
    add_check(checks, errors, "sunset_context_anchors", anchors_ok,
              error="The frozen Sun-gone or spoken-continuation anchor changed.")

    actions = load_actions(root / source["relationship_manifest_path"])
    context_start = parse_utc(spec["anchors"]["context_start"]["utc"])
    context_end = parse_utc(spec["anchors"]["context_continuation"]["utc"])
    plan_start = parse_utc(spec["scheduled_window"]["start_utc"])
    plan_end = parse_utc(spec["scheduled_window"]["end_utc"])
    segments = {
        "sun_gone_to_plan_start": summarize(actions, context_start, plan_start),
        "scheduled_window": summarize(actions, plan_start, plan_end),
        "plan_end_to_spoken_continuation": summarize(actions, plan_end, context_end),
        "conservative_connected_context": summarize(actions, context_start, context_end),
    }
    segments_ok = segments == spec["frozen_segments"]
    add_check(checks, errors, "connected_context_counts", segments_ok,
              error="The frozen Sunset plan/context counts changed.", segments=segments)

    plan = segments["scheduled_window"]
    context = segments["conservative_connected_context"]
    measures = {
        "scheduled_action_share_of_connected_context": plan["actions"] / context["actions"],
        "outside_scheduled_action_share_of_connected_context": (context["actions"] - plan["actions"]) / context["actions"],
        "connected_context_to_scheduled_product_ratio": context["products"] / plan["products"],
        "scheduled_byte_share_of_connected_context": plan["archive_size_bytes"] / context["archive_size_bytes"],
        "connected_context_to_scheduled_byte_ratio": context["archive_size_bytes"] / plan["archive_size_bytes"],
    }
    measures_ok = all(math.isclose(measures[key], expected, rel_tol=0.0, abs_tol=1e-15)
                      for key, expected in spec["frozen_measures"].items())
    add_check(checks, errors, "context_extension_measures", measures_ok,
              error="The frozen Sunset context-extension measures changed.", measures=measures)

    state = spec["mutation_state"]
    boundary_ok = not any(value for key, value in state.items() if key != "pixel_payload_bytes") and state["pixel_payload_bytes"] == 0
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited completeness, content, event, model, science, novelty, or pixel claim was admitted.", mutation_state=state)
    evidence_state = "VERIFIED_SUNSET_PLAN_CONTEXT_EXTENSION" if segments_ok and measures_ok else "SUNSET_PLAN_CONTEXT_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "segments": segments,
        "measures": measures, "disposition": spec["disposition"],
        "verified": "The fixed Sunset plan block is a valid independent planned-event unit but not an exhaustive realized-observation boundary. A conservative transcript-bracketed connected context contains 4,290 products versus 2,535 inside the plan while the scheduled-event count remains one.",
        "decision_use": "Present the plan block and connected context as two different, explicitly bounded denominators. The larger context strengthens the file-count/effective-sample paradox but does not become a complete event or image-content cohort.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage11c(root)
    baseline = verify_stage11d(root, prior=prior)
    names = load_json(root / "spec/stage11d.json")["hard_negatives"]
    mutations = {name: verify_stage11d(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11D hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    plan = result["segments"]["scheduled_window"]
    context = result["segments"]["conservative_connected_context"]
    measures = result["measures"]
    lines = ["# Stage 11D — Sunset Planned Block / Connected Context", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Planned block: `{plan['products']:,}` products / `{plan['exposures']:,}` exposures / `{plan['actions']}` actions / `{plan['archive_size_bytes'] / 1_000_000_000:.9f} GB`",
        f"- Conservative connected context: `{context['products']:,}` products / `{context['exposures']:,}` exposures / `{context['actions']}` actions / `{context['archive_size_bytes'] / 1_000_000_000:.9f} GB`",
        f"- Plan share of context actions: `{measures['scheduled_action_share_of_connected_context']:.3%}`",
        f"- Context / plan product ratio: `{measures['connected_context_to_scheduled_product_ratio']:.6f}×`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11d(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
