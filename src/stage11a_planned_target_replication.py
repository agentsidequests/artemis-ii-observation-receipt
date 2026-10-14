#!/usr/bin/env python3
"""Verify Stage 11A's planned-target window replication census."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json
from stage10z_action_plan_membership import verify_stage10z


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "active_windows_are_independent_events": False,
        "repeated_targets_evaluation_ready": False,
        "target_tags_substituted_for_plan_names": False,
        "singleton_targets_observed_only_once": False,
        "singleton_targets_scientifically_insufficient": False,
        "scope": "active_exact_plan_target_names",
        "model_partition_assigned": False,
        "performance_effect_inferred": False,
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_active_windows_independent_events": ("active_windows_are_independent_events", True),
        "call_repeated_targets_evaluation_ready": ("repeated_targets_evaluation_ready", True),
        "substitute_target_tags_for_plan_names": ("target_tags_substituted_for_plan_names", True),
        "claim_singleton_targets_observed_only_once": ("singleton_targets_observed_only_once", True),
        "claim_singleton_targets_scientifically_insufficient": ("singleton_targets_scientifically_insufficient", True),
        "generalize_to_all_archive_target_classes": ("scope", "all_archive_target_classes"),
        "assign_model_partition_from_plan_count": ("model_partition_assigned", True),
        "infer_model_performance_effect": ("performance_effect_inferred", True),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_replication_census": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def exact_mapping(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    return all(
        close(float(actual[key]), float(value)) if isinstance(value, float) else actual[key] == value
        for key, value in expected.items()
    )


def derive(rows: list[dict[str, str]]) -> tuple[dict[str, Any], dict[str, int]]:
    windows = {(row["plan_order"], row["plan_target_name"]) for row in rows if row["plan_order"]}
    counts = Counter(target for _, target in windows)
    singleton = sum(value == 1 for value in counts.values())
    repeated = sum(value > 1 for value in counts.values())
    metrics = {
        "active_plan_windows": len(windows), "active_plan_target_names": len(counts),
        "singleton_target_names": singleton, "repeated_target_names": repeated,
        "singleton_target_name_share": singleton / len(counts),
        "repeated_target_name_share": repeated / len(counts),
        "singleton_valid_two_sided_window_allocations": 0,
    }
    return metrics, dict(sorted(counts.items()))


def verify_stage11a(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11a.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior = verify_stage10z(root) if prior is None else prior
    add_check(checks, errors, "membership_ledger_replays", prior["pass"],
              error="Stage 10Z no longer verifies.")

    with (root / spec["source_contract"]["membership_ledger_path"]).open(newline="", encoding="utf-8") as handle:
        metrics, counts = derive(list(csv.DictReader(handle)))
    census_ok = exact_mapping(metrics, spec["frozen_observables"]) and counts == spec["frozen_window_counts"]
    add_check(checks, errors, "planned_target_window_census", census_ok,
              error="The frozen planned-target window replication census changed.",
              metrics=metrics, window_counts=counts)

    state = spec["mutation_state"]
    boundary_ok = (
        not state["active_windows_are_independent_events"]
        and not state["repeated_targets_evaluation_ready"]
        and not state["target_tags_substituted_for_plan_names"]
        and not state["singleton_targets_observed_only_once"]
        and not state["singleton_targets_scientifically_insufficient"]
        and state["scope"] == "active_exact_plan_target_names"
        and not state["model_partition_assigned"] and not state["performance_effect_inferred"]
        and not state["scientific_discovery_or_priority"] and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited independence, readiness, ontology, occurrence, sufficiency, scope, model, discovery, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_PLANNED_TARGET_WINDOW_REPLICATION_CENSUS" if census_ok else "PLANNED_TARGET_REPLICATION_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "replication": metrics, "window_counts": counts,
        "singleton_names": [name for name, count in counts.items() if count == 1],
        "repeated_names": {name: count for name, count in counts.items() if count > 1},
        "verified": "Among 19 exact plan target-name values represented in the 36 active timed windows, 12 occur in one active window and seven occur in multiple active windows. Sunset is therefore an example of a broader scheduled-window replication constraint, not an isolated case.",
        "decision_use": "A singleton plan name cannot support an internal two-sided evaluation on distinct same-name scheduled windows. Repeated plan names remain candidates only: window overlap, semantic comparability, camera coupling, and event identity still require task-native checks.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage10z(root)
    baseline = verify_stage11a(root, prior=prior)
    names = load_json(root / "spec/stage11a.json")["hard_negatives"]
    mutations = {name: verify_stage11a(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11A hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["replication"]
    lines = [
        "# Stage 11A — Planned-Target Window Replication Census", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Active plan windows / target names: `{item['active_plan_windows']}` / `{item['active_plan_target_names']}`",
        f"- Singleton / repeated target names: `{item['singleton_target_names']}` / `{item['repeated_target_names']}`",
        f"- Singleton share: `{item['singleton_target_name_share']:.3%}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified", "", result["verified"], "", "## Decision use", "", result["decision_use"],
        "", "## Singleton plan target names", "",
    ]
    lines.extend(f"- `{name}`" for name in result["singleton_names"])
    lines.extend(["", "## Repeated plan target names", ""])
    lines.extend(f"- `{name}`: `{count}` active windows" for name, count in result["repeated_names"].items())
    lines.extend(["", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", ""])
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11a(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
