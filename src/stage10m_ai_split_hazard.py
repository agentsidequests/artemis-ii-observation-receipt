#!/usr/bin/env python3
"""Verify Stage 10M's related-group crossing model for hypothetical AI splits."""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json
from stage10j_fractional_bracket_expansion import verify_stage10j
from stage10l_representation_compression import verify_stage10l


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "result_kind": "expected_group_crossing_hazard",
        "existing_pipeline_contaminated": False,
        "representations_byte_identical": False,
        "bracket_siblings_identical": False,
        "scope": "verified_complete_action_cohort",
        "action_grouping_universal": False,
        "statistical_significance": False,
        "global_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "call_expected_crossing_observed_leakage":
        state["result_kind"] = "observed_leakage"
    elif mutation == "claim_an_existing_pipeline_is_contaminated":
        state["existing_pipeline_contaminated"] = True
    elif mutation == "treat_three_representations_as_byte_identical":
        state["representations_byte_identical"] = True
    elif mutation == "call_bracket_siblings_identical_images":
        state["bracket_siblings_identical"] = True
    elif mutation == "generalize_beyond_complete_action_cohort":
        state["scope"] = "all_archive_products"
    elif mutation == "claim_action_grouping_solves_every_evaluation_leak":
        state["action_grouping_universal"] = True
    elif mutation == "claim_statistical_significance":
        state["statistical_significance"] = True
    elif mutation == "claim_global_priority":
        state["global_priority"] = True
    elif mutation == "open_pixels_for_split_model":
        state["pixel_payload_bytes"] = 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def crossing_probability(train_probability: float, group_size: int) -> float:
    test_probability = 1.0 - train_probability
    return 1.0 - train_probability ** group_size - test_probability ** group_size


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def verify_stage10m(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10m.json"), mutation)
    expected = spec["frozen_observables"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    stage10j = verify_stage10j(root)
    stage10l = verify_stage10l(root)
    patterns = stage10j["pattern_counts"]
    three_actions = sum(count for pattern, count in patterns.items() if pattern.count(",") + 1 == 3)
    five_actions = sum(count for pattern, count in patterns.items() if pattern.count(",") + 1 == 5)
    source_ok = (
        stage10j.get("pass") is True and stage10l.get("pass") is True
        and three_actions == expected["three_exposure_actions"]
        and five_actions == expected["five_exposure_actions"]
        and three_actions + five_actions == expected["complete_actions"]
        and stage10l["capture_identities"] == expected["capture_identities"]
        and stage10l["products"] == expected["capture_identities"] * expected["products_per_identity"]
    )
    add_check(checks, errors, "source_cohort_replay", source_ok,
              error="The Stage 10J action-size distribution or Stage 10L representation parity changed.",
              three_exposure_actions=three_actions, five_exposure_actions=five_actions)

    scenarios: dict[str, dict[str, float]] = {}
    scenario_failures: list[str] = []
    for label, frozen in expected["scenarios"].items():
        train_probability = float(label)
        identity_cross = crossing_probability(train_probability, expected["products_per_identity"])
        product_three = crossing_probability(train_probability, 3 * expected["products_per_identity"])
        product_five = crossing_probability(train_probability, 5 * expected["products_per_identity"])
        exposure_three = crossing_probability(train_probability, 3)
        exposure_five = crossing_probability(train_probability, 5)
        product_actions = three_actions * product_three + five_actions * product_five
        exposure_actions = three_actions * exposure_three + five_actions * exposure_five
        result = {
            "identity_group_cross_probability": identity_cross,
            "expected_cross_identity_groups": expected["capture_identities"] * identity_cross,
            "expected_cross_action_groups_product_split": product_actions,
            "product_split_action_cross_rate": product_actions / expected["complete_actions"],
            "expected_cross_action_groups_exposure_split": exposure_actions,
            "exposure_split_action_cross_rate": exposure_actions / expected["complete_actions"],
            "action_group_split_cross_rate": 0.0,
        }
        scenarios[label] = result
        for key, value in frozen.items():
            if not close(result[key], value):
                scenario_failures.append(f"{label}:{key}")
    add_check(checks, errors, "frozen_split_scenarios", not scenario_failures,
              error="At least one frozen random-split group-crossing result changed.", failures=scenario_failures)

    ordering_ok = all(
        scenarios[label]["product_split_action_cross_rate"]
        > scenarios[label]["exposure_split_action_cross_rate"]
        > scenarios[label]["action_group_split_cross_rate"]
        for label in scenarios
    )
    add_check(checks, errors, "grouping_unit_ordering", ordering_ok,
              error="Product-, exposure-, and action-level grouping no longer preserve the expected risk ordering.")

    state = spec["mutation_state"]
    boundary_ok = (
        state["result_kind"] == "expected_group_crossing_hazard"
        and not state["existing_pipeline_contaminated"]
        and not state["representations_byte_identical"]
        and not state["bracket_siblings_identical"]
        and state["scope"] == "verified_complete_action_cohort"
        and not state["action_grouping_universal"]
        and not state["statistical_significance"]
        and not state["global_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited observation, contamination, identity, scope, sufficiency, significance, novelty, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_EXPECTED_RANDOM_SPLIT_GROUP_CROSSING_HAZARD" if source_ok and not scenario_failures and ordering_ok else "SPLIT_HAZARD_UNRESOLVED"
    primary = scenarios["0.8"]
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "three_exposure_actions": three_actions, "five_exposure_actions": five_actions,
        "complete_actions": expected["complete_actions"], "capture_identities": expected["capture_identities"],
        "scenarios": scenarios,
        "verified": "Under the frozen independent 80/20 product-level split model, an expected 1,930.148 of 2,166 complete actions (89.111%) place related products on both sides. Grouping the three representations by exposure but splitting exposure identities independently still crosses an expected 1,146.048 actions (52.911%). Splitting by complete action crosses zero by construction.",
        "decision_use": "For image-model evaluation on this verified cohort, use the reconstructed action identity as the minimum split key rather than product or exposure ID. This controls the exact representation and bracket-sibling dependence measured here; a real task may require broader grouping by scene, target, time, or source episode.",
        "pixel_payload_bytes": spec["source_contract"]["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10m(root)
    names = load_json(root / "spec/stage10m.json")["hard_negatives"]
    mutations = {name: verify_stage10m(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10M hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    primary = result["scenarios"]["0.8"]
    lines = [
        "# Stage 10M — AI Split Related-Group Crossing Hazard", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Complete three-/five-exposure actions: `{result['three_exposure_actions']:,}` / `{result['five_exposure_actions']:,}`",
        f"- 80/20 product-split expected action crossing: `{primary['expected_cross_action_groups_product_split']:.3f}` / `{result['complete_actions']:,}` (`{primary['product_split_action_cross_rate']:.3%}`)",
        f"- 80/20 exposure-split expected action crossing: `{primary['expected_cross_action_groups_exposure_split']:.3f}` / `{result['complete_actions']:,}` (`{primary['exposure_split_action_cross_rate']:.3%}`)",
        f"- Action-group split crossing: `{primary['action_group_split_cross_rate']:.0%}` by construction",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified model", "", result["verified"], "", "## Decision use", "", result["decision_use"],
        "", "## Claim ceiling", "", result["claim_ceiling"], "", "## Robustness scenarios", "",
    ]
    for label, scenario in result["scenarios"].items():
        lines.append(f"- `{float(label):.0%}/{1-float(label):.0%}`: product-level action crossing `{scenario['product_split_action_cross_rate']:.3%}`; exposure-level `{scenario['exposure_split_action_cross_rate']:.3%}`")
    lines += ["", "## Hard negatives", ""]
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10m(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
