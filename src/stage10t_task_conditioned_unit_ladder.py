#!/usr/bin/env python3
"""Verify Stage 10T's task-conditioned unit ladder and split-feasibility result."""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json
from stage10s_planned_sunset_window import verify_stage10s


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "candidate_units_are_independent": False,
        "universal_unit_selected": False,
        "event_level_modeling_impossible": False,
        "within_event_evaluation_invalid": False,
        "scheduled_sunset_events": 1,
        "result_kind": "hypothetical_split_feasibility",
        "performance_effect_inferred": False,
        "scope": "one_plan_bounded_event_in_verified_cohort",
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_every_unit_independent": ("candidate_units_are_independent", True),
        "choose_one_universal_unit": ("universal_unit_selected", True),
        "claim_event_level_modeling_impossible": ("event_level_modeling_impossible", True),
        "call_within_event_evaluation_invalid": ("within_event_evaluation_invalid", True),
        "invent_second_sunset_event": ("scheduled_sunset_events", 2),
        "call_hypothetical_split_observed_leakage": ("result_kind", "observed_leakage"),
        "infer_model_performance_effect": ("performance_effect_inferred", True),
        "claim_cross_mission_representativeness": ("scope", "cross_mission"),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_unit_ladder": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def event_allocations(event_count: int) -> tuple[int, int]:
    allocations = list(itertools.product(("train", "test"), repeat=event_count))
    valid = [allocation for allocation in allocations if "train" in allocation and "test" in allocation]
    return len(allocations), len(valid)


def verify_stage10t(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10t.json"), mutation)
    expected = spec["frozen_observables"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior = verify_stage10s(root)
    prior_ok = prior["pass"]
    add_check(checks, errors, "plan_bounded_window_receipt", prior_ok,
              error="Stage 10S no longer verifies.")
    window = prior["window"]
    event_count = window["scheduled_sunset_entries"]
    allocations, valid_allocations = event_allocations(event_count)
    counts = {
        "archive_products": window["products"],
        "exposure_identities": window["capture_identities"],
        "complete_actions": window["complete_actions"],
        "conditional_five_second_clusters": window["five_second_clusters"],
        "scheduled_sunset_events": event_count,
    }
    derived = {
        **counts,
        "product_to_event_ratio": counts["archive_products"] / event_count,
        "exposure_to_event_ratio": counts["exposure_identities"] / event_count,
        "action_to_event_ratio": counts["complete_actions"] / event_count,
        "cluster_to_event_ratio": counts["conditional_five_second_clusters"] / event_count,
        "possible_binary_event_allocations": allocations,
        "valid_two_sided_event_allocations": valid_allocations,
        "invalid_within_event_substitutions": len(counts) - 1,
    }
    exact_keys = [key for key, value in expected.items() if not isinstance(value, float)]
    float_keys = [key for key, value in expected.items() if isinstance(value, float)]
    observables_ok = (
        all(derived[key] == expected[key] for key in exact_keys)
        and all(close(float(derived[key]), expected[key]) for key in float_keys)
    )
    add_check(checks, errors, "task_conditioned_unit_ladder", observables_ok,
              error="The candidate-unit ladder or event-allocation result changed.", derived=derived)

    ladder_ok = (
        [item["unit"] for item in spec["unit_ladder"]] == [
            "archive_product", "exposure_identity", "complete_camera_action",
            "conditional_five_second_same_camera_cluster", "scheduled_sunset_event"
        ]
        and [item["count"] for item in spec["unit_ladder"]] == list(counts.values())
        and all(item["not_established"] for item in spec["unit_ladder"])
        and set(spec["task_routes"]) == {
            "new_sunset_event_generalization", "within_event_temporal_generalization",
            "representation_or_hdr_task", "retrieval_or_storage_task"
        }
    )
    add_check(checks, errors, "task_routes_and_limits", ladder_ok,
              error="A unit count, task route, or non-independence limit changed.")

    state = spec["mutation_state"]
    boundary_ok = (
        not state["candidate_units_are_independent"]
        and not state["universal_unit_selected"]
        and not state["event_level_modeling_impossible"]
        and not state["within_event_evaluation_invalid"]
        and state["scheduled_sunset_events"] == 1
        and state["result_kind"] == "hypothetical_split_feasibility"
        and not state["performance_effect_inferred"]
        and state["scope"] == "one_plan_bounded_event_in_verified_cohort"
        and not state["scientific_discovery_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited independence, universality, feasibility, leakage, performance, scope, discovery, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_TASK_CONDITIONED_UNIT_LADDER" if prior_ok and observables_ok and ladder_ok else "TASK_CONDITIONED_UNIT_LADDER_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "unit_ladder": derived,
        "verified": "One plan-bounded Sunset event can be counted as 2,535 archive products, 845 exposure identities, 169 complete bracket actions, 24 conditional same-camera bursts, or one scheduled event. These are task-conditioned candidate units, not five interchangeable or independently validated sample counts. With one event there are two whole-event binary allocations and zero that place distinct Sunset events in both train and test.",
        "decision_use": "For new-Sunset-event generalization, a two-sided internal Artemis II event split is infeasible: the single event must be entirely in train or test, or the claim must narrow. Within-event temporal, HDR, representation, and retrieval tasks remain possible, but require their own grouping and evaluation contracts.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10t(root)
    names = load_json(root / "spec/stage10t.json")["hard_negatives"]
    mutations = {name: verify_stage10t(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10T hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["unit_ladder"]
    lines = [
        "# Stage 10T — Task-Conditioned Unit Ladder", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Products → exposures → actions → conditional bursts → event: `{item['archive_products']:,}` → `{item['exposure_identities']:,}` → `{item['complete_actions']:,}` → `{item['conditional_five_second_clusters']:,}` → `{item['scheduled_sunset_events']}`",
        f"- Whole-event binary allocations / valid two-sided allocations: `{item['possible_binary_event_allocations']}` / `{item['valid_two_sided_event_allocations']}`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10t(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
