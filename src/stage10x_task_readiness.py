#!/usr/bin/env python3
"""Verify Stage 10X's task-conditioned readiness synthesis."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json
from stage10t_task_conditioned_unit_ladder import verify_stage10t
from stage10u_camera_target_shortcut import verify_stage10u
from stage10v_task_representation_fitness import verify_stage10v
from stage10w_target_tag_selection import verify_stage10w


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "archive_globally_benchmark_ready": False,
        "archive_globally_unusable": False,
        "retrieval_called_scientific_model": False,
        "within_event_called_new_event_generalization": False,
        "blank_tags_used_as_negative_labels": False,
        "camera_only_baseline_required": True,
        "processed_tier_called_calibrated": False,
        "one_split_repairs_all_boundaries": False,
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_archive_globally_benchmark_ready": ("archive_globally_benchmark_ready", True),
        "call_archive_globally_unusable": ("archive_globally_unusable", True),
        "call_retrieval_a_scientific_model": ("retrieval_called_scientific_model", True),
        "call_within_event_new_event_generalization": ("within_event_called_new_event_generalization", True),
        "use_blank_tags_as_negative_labels": ("blank_tags_used_as_negative_labels", True),
        "omit_camera_only_baseline": ("camera_only_baseline_required", False),
        "call_processed_tier_calibrated": ("processed_tier_called_calibrated", True),
        "claim_one_split_repairs_all_boundaries": ("one_split_repairs_all_boundaries", True),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_readiness_synthesis": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def collect_prior(root: Path) -> dict[str, dict[str, Any]]:
    return {
        "stage10t": verify_stage10t(root),
        "stage10u": verify_stage10u(root),
        "stage10v": verify_stage10v(root),
        "stage10w": verify_stage10w(root),
    }


def verify_stage10x(
    root: Path, mutation: str | None = None,
    prior: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10x.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior = collect_prior(root) if prior is None else prior
    required = spec["source_contract"]["required_prior_states"]
    prior_ok = all(prior[name]["pass"] and prior[name]["evidence_state"] == state
                   for name, state in required.items())
    add_check(checks, errors, "prior_boundaries_replay", prior_ok,
              error="At least one required Stage 10T–10W boundary no longer verifies.",
              states={name: result["evidence_state"] for name, result in prior.items()})

    matrix = spec["task_matrix"]
    status_counts = Counter(row["status"] for row in matrix)
    expected_counts = {
        "tasks": len(matrix),
        "supported_now": status_counts["SUPPORTED_NOW"],
        "supported_now_with_claim_limit": status_counts["SUPPORTED_NOW_WITH_CLAIM_LIMIT"],
        "conditionally_supportable": status_counts["CONDITIONALLY_SUPPORTABLE"],
        "not_yet_supportable": status_counts["NOT_YET_SUPPORTABLE"],
        "not_internally_identifiable": status_counts["NOT_INTERNALLY_IDENTIFIABLE"],
        "not_supported_by_archived_tiers_alone": status_counts["NOT_SUPPORTED_BY_ARCHIVED_TIERS_ALONE"],
        "independent_blocker_families": len(spec["blocker_families"]),
    }
    matrix_ok = expected_counts == spec["frozen_summary"] and all(
        set(row) == {"task", "status", "estimand", "admissible_unit", "limiting_boundary", "status_changer"}
        and all(row.values()) for row in matrix
    )
    add_check(checks, errors, "task_readiness_matrix", matrix_ok,
              error="The task-readiness matrix is incomplete or no longer matches its frozen summary.",
              status_counts=dict(status_counts), blocker_families=list(spec["blocker_families"]))

    exact_tasks = {row["task"]: row["status"] for row in matrix}
    route_ok = exact_tasks == {
        "archive_retrieval_and_footprint_audit": "SUPPORTED_NOW",
        "within_identity_representation_transformation": "SUPPORTED_NOW_WITH_CLAIM_LIMIT",
        "within_event_temporal_or_hdr_modeling": "CONDITIONALLY_SUPPORTABLE",
        "supervised_archive_target_classification": "NOT_YET_SUPPORTABLE",
        "new_sunset_event_generalization": "NOT_INTERNALLY_IDENTIFIABLE",
        "calibrated_color_or_photometry": "NOT_SUPPORTED_BY_ARCHIVED_TIERS_ALONE",
    }
    add_check(checks, errors, "task_specific_routes", route_ok,
              error="A task was globally promoted, globally rejected, or assigned the wrong evidence status.")

    state = spec["mutation_state"]
    boundary_ok = (
        not state["archive_globally_benchmark_ready"]
        and not state["archive_globally_unusable"]
        and not state["retrieval_called_scientific_model"]
        and not state["within_event_called_new_event_generalization"]
        and not state["blank_tags_used_as_negative_labels"]
        and state["camera_only_baseline_required"]
        and not state["processed_tier_called_calibrated"]
        and not state["one_split_repairs_all_boundaries"]
        and not state["scientific_discovery_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited global-readiness, task-substitution, label, camera, calibration, universal-fix, discovery, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_TASK_READINESS_SEPARATION" if prior_ok and matrix_ok and route_ok else "TASK_READINESS_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "task_matrix": matrix, "blocker_families": spec["blocker_families"],
        "summary": expected_counts,
        "verified": "The current archive is ready for some bounded tasks, conditional for others, and insufficient for still others. Retrieval accounting is supported now; representation work is supportable with a claim limit; within-event modeling needs a frozen protocol; supervised target classification needs a label-population audit and camera/event controls; new-Sunset-event generalization needs another event; calibrated color or photometry needs an external calibration chain.",
        "decision_use": "Replace the binary question 'is this dataset benchmark-ready?' with six task-specific readiness decisions. The four blocker families are independent: a better split cannot create labels, another event, camera balance, or calibration.",
        "pixel_payload_bytes": state["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"], "next_step_logic": spec["next_step_logic"],
        "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = collect_prior(root)
    baseline = verify_stage10x(root, prior=prior)
    names = load_json(root / "spec/stage10x.json")["hard_negatives"]
    mutations = {name: verify_stage10x(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10X hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10X — Task-Conditioned Readiness Map", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Candidate tasks: `{result['summary']['tasks']}`",
        f"- Independent blocker families: `{result['summary']['independent_blocker_families']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified", "", result["verified"], "", "## Task map", "",
        "| Task | Status | Admissible unit | Limiting boundary |",
        "| --- | --- | --- | --- |",
    ]
    for row in result["task_matrix"]:
        lines.append(f"| {row['task']} | `{row['status']}` | {row['admissible_unit']} | {row['limiting_boundary']} |")
    lines.extend(["", "## Decision use", "", result["decision_use"],
                  "", "## Claim ceiling", "", result["claim_ceiling"],
                  "", "## Hard negatives", ""])
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10x(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
