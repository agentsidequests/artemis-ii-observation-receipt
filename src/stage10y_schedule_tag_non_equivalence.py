#!/usr/bin/env python3
"""Verify Stage 10Y's schedule/tag non-equivalence canary."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json, parse_utc
from stage10x_task_readiness import verify_stage10x


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "target_tags_are_event_ids": False,
        "plan_names_are_exhaustive_labels": False,
        "outside_window_tags_are_wrong": False,
        "zero_match_means_planned_observation_missed": False,
        "exact_name_match_is_independent_event": False,
        "ontologies_merged": False,
        "model_grouped_by_target_tag_as_event": False,
        "outside_sunset_rows_are_new_events": False,
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_target_tags_event_ids": ("target_tags_are_event_ids", True),
        "call_plan_names_exhaustive_labels": ("plan_names_are_exhaustive_labels", True),
        "call_outside_window_tags_wrong": ("outside_window_tags_are_wrong", True),
        "call_zero_match_planned_observation_missed": ("zero_match_means_planned_observation_missed", True),
        "call_exact_name_match_independent_event": ("exact_name_match_is_independent_event", True),
        "merge_plan_and_tag_ontologies": ("ontologies_merged", True),
        "group_model_by_target_tag_as_event": ("model_grouped_by_target_tag_as_event", True),
        "call_sunset_outside_rows_new_events": ("outside_sunset_rows_are_new_events", True),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_schedule_tag_canary": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def parse_plan_time(value: str) -> datetime:
    return datetime.strptime(value, "%d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc)


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def derive(plan: list[dict[str, Any]], rows: list[dict[str, str]]) -> tuple[dict[str, Any], dict[str, list[str]], dict[str, dict[str, int]]]:
    windows: list[tuple[str, datetime, datetime]] = []
    for item in plan:
        props = item["target_properties"]
        name = props.get("target_name")
        request = props.get("request_date_time")
        duration = props.get("request_duration")
        if not name or not request or not duration:
            continue
        start = parse_plan_time(request)
        windows.append((name, start, start + timedelta(minutes=float(duration))))

    source = [row for row in rows if row["collection_id"] == "data_source"]
    tagged = [row for row in source if row["target_id"]]
    plan_names = {name for name, _, _ in windows}
    tag_names = {row["target_id"] for row in tagged}
    totals = Counter(row["target_id"] for row in tagged)
    matched = Counter()
    for row in tagged:
        action_start = parse_utc(row["action_start_utc"])
        action_end = parse_utc(row["action_end_utc"])
        if any(row["target_id"] == name and action_start >= start and action_end < end
               for name, start, end in windows):
            matched[row["target_id"]] += 1

    inside = sum(matched.values())
    metrics = {
        "scheduled_entries_with_target_and_window": len(windows),
        "scheduled_target_names": len(plan_names),
        "tagged_source_exposures": len(tagged),
        "tag_values": len(tag_names),
        "shared_exact_names": len(plan_names & tag_names),
        "tag_only_names": len(tag_names - plan_names),
        "plan_only_names": len(plan_names - tag_names),
        "tag_values_with_any_same_name_window_membership": sum(matched[name] > 0 for name in tag_names),
        "tag_values_with_zero_same_name_window_membership": sum(matched[name] == 0 for name in tag_names),
        "exposures_inside_any_same_name_plan_window": inside,
        "exposures_outside_all_same_name_plan_windows": len(tagged) - inside,
        "same_name_window_membership_share": inside / len(tagged),
        "outside_same_name_window_share": (len(tagged) - inside) / len(tagged),
        "sunset_tagged_exposures": totals["Sunset"],
        "sunset_inside_same_name_plan_window": matched["Sunset"],
        "sunset_outside_same_name_plan_window": totals["Sunset"] - matched["Sunset"],
    }
    names = {"tag_only": sorted(tag_names - plan_names), "plan_only": sorted(plan_names - tag_names)}
    examples = {name: {"tagged": totals[name], "inside_same_name_window": matched[name]}
                for name in ("Earth", "Orientale Basin", "Reiner Gamma", "Sunset", "Vavilov Crater")}
    return metrics, names, examples


def exact_mapping(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    return all(
        close(float(actual[key]), float(value)) if isinstance(value, float) else actual[key] == value
        for key, value in expected.items()
    )


def verify_stage10y(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10y.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior = verify_stage10x(root) if prior is None else prior
    add_check(checks, errors, "task_readiness_replays", prior["pass"],
              error="Stage 10X no longer verifies.")

    source = spec["source_contract"]
    plan = json.loads((root / source["plan_path"]).read_text(encoding="utf-8"))
    if not isinstance(plan, list):
        raise ValueError("Expected the target request to contain a list of plan entries.")
    with (root / source["manifest_path"]).open(newline="", encoding="utf-8") as handle:
        metrics, names, examples = derive(plan, list(csv.DictReader(handle)))
    correspondence_ok = (
        exact_mapping(metrics, spec["frozen_observables"])
        and names == spec["frozen_name_sets"]
        and examples == spec["frozen_examples"]
    )
    add_check(checks, errors, "schedule_tag_correspondence", correspondence_ok,
              error="The frozen schedule/tag correspondence changed.",
              metrics=metrics, name_sets=names, examples=examples)

    state = spec["mutation_state"]
    boundary_ok = (
        not state["target_tags_are_event_ids"]
        and not state["plan_names_are_exhaustive_labels"]
        and not state["outside_window_tags_are_wrong"]
        and not state["zero_match_means_planned_observation_missed"]
        and not state["exact_name_match_is_independent_event"]
        and not state["ontologies_merged"]
        and not state["model_grouped_by_target_tag_as_event"]
        and not state["outside_sunset_rows_are_new_events"]
        and not state["scientific_discovery_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited event, label, correctness, ontology, grouping, discovery, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_SCHEDULE_TAG_NON_EQUIVALENCE" if correspondence_ok else "SCHEDULE_TAG_CORRESPONDENCE_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "correspondence": metrics, "name_sets": names, "examples": examples,
        "verified": "The mission plan and target-tag layer are not interchangeable ontologies or grouping systems. They share 14 exact names, while nine tag values are absent from the plan vocabulary and five plan names are absent from the tag vocabulary. Only 1,313 of 3,413 tagged source exposures have complete actions inside an exact-same-name scheduled window.",
        "decision_use": "Use an independent schedule or task-native episode oracle for event grouping, and treat target tags as curated navigation metadata unless their population is separately audited. The fixed Sunset plan window remains primary; its tag concordance is corroborative.",
        "pixel_payload_bytes": state["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"], "next_step_logic": spec["next_step_logic"],
        "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage10x(root)
    baseline = verify_stage10y(root, prior=prior)
    names = load_json(root / "spec/stage10y.json")["hard_negatives"]
    mutations = {name: verify_stage10y(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10Y hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["correspondence"]
    lines = [
        "# Stage 10Y — Schedule/Tag Non-Equivalence Canary", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Plan target names / tag values / exact-name overlap: `{item['scheduled_target_names']}` / `{item['tag_values']}` / `{item['shared_exact_names']}`",
        f"- Tagged exposures inside / outside exact-same-name plan windows: `{item['exposures_inside_any_same_name_plan_window']:,}` / `{item['exposures_outside_all_same_name_plan_windows']:,}`",
        f"- Exact-same-name membership share: `{item['same_name_window_membership_share']:.3%}`",
        f"- Sunset tagged inside / outside scheduled Sunset window: `{item['sunset_inside_same_name_plan_window']:,}` / `{item['sunset_outside_same_name_plan_window']:,}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified", "", result["verified"], "", "## Decision use", "", result["decision_use"],
        "", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", "",
    ]
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10y(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
