#!/usr/bin/env python3
"""Verify Stage 11G's unit-sensitive plan-window prominence canary."""

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
from stage11f_protocol_weighting import verify_stage11f


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "plan_windows_are_partition": False,
        "prominence_is_scientific_importance": False,
        "window_ordering_is_unit_invariant": False,
        "actual_sampler": "unspecified",
        "observed_model_bias": False,
        "causal_performance_effect": False,
        "one_universal_correct_weighting": False,
        "scope": "verified_active_plan_windows",
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_plan_windows_a_partition": ("plan_windows_are_partition", True),
        "call_prominence_scientific_importance": ("prominence_is_scientific_importance", True),
        "call_window_ordering_unit_invariant": ("window_ordering_is_unit_invariant", True),
        "claim_actual_sampler_is_uniform_products": ("actual_sampler", "uniform_products"),
        "claim_observed_model_bias": ("observed_model_bias", True),
        "claim_causal_performance_effect": ("causal_performance_effect", True),
        "claim_one_universal_correct_weighting": ("one_universal_correct_weighting", True),
        "generalize_to_unadmitted_archive_records": ("scope", "entire_archive"),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels_during_rank_test": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def sign(value: int) -> int:
    return (value > 0) - (value < 0)


def compare_pairs(windows: list[dict[str, Any]], second_key: str) -> dict[str, int | float]:
    reversed_pairs = 0
    concordant_pairs = 0
    tied_pairs = 0
    for left, right in itertools.combinations(windows, 2):
        action_sign = sign(left["actions"] - right["actions"])
        other_sign = sign(left[second_key] - right[second_key])
        if action_sign == 0 or other_sign == 0:
            tied_pairs += 1
        elif action_sign == other_sign:
            concordant_pairs += 1
        else:
            reversed_pairs += 1
    comparable_pairs = reversed_pairs + concordant_pairs
    return {
        "strictly_comparable_pairs": comparable_pairs,
        "reversed_pairs": reversed_pairs,
        "concordant_pairs": concordant_pairs,
        "tied_pairs": tied_pairs,
        "reversal_share_of_comparable_pairs": reversed_pairs / comparable_pairs,
    }


def descending_rank(windows: list[dict[str, Any]], selected: dict[str, Any], key: str) -> int:
    return 1 + sum(window[key] > selected[key] for window in windows)


def product_reversal_example(windows: list[dict[str, Any]], more_actions_order: str, more_products_order: str) -> dict[str, Any]:
    by_order = {window["plan_order"]: window for window in windows}
    more_actions = by_order[more_actions_order]
    more_products = by_order[more_products_order]
    return {
        "more_actions_order": more_actions_order,
        "more_actions_name": more_actions["plan_target_name"],
        "more_actions_actions": more_actions["actions"],
        "more_actions_products": more_actions["products"],
        "more_products_order": more_products_order,
        "more_products_name": more_products["plan_target_name"],
        "more_products_actions": more_products["actions"],
        "more_products_products": more_products["products"],
    }


def derive(windows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    product = compare_pairs(windows, "products")
    byte = compare_pairs(windows, "archive_size_bytes")
    sunset = next(window for window in windows if window["plan_target_name"] == "Sunset")
    metrics = {
        "active_plan_windows": len(windows),
        "unordered_window_pairs": len(windows) * (len(windows) - 1) // 2,
        "action_product_strictly_comparable_pairs": product["strictly_comparable_pairs"],
        "action_product_reversed_pairs": product["reversed_pairs"],
        "action_product_concordant_pairs": product["concordant_pairs"],
        "action_product_tied_pairs": product["tied_pairs"],
        "action_product_reversal_share_of_comparable_pairs": product["reversal_share_of_comparable_pairs"],
        "action_byte_strictly_comparable_pairs": byte["strictly_comparable_pairs"],
        "action_byte_reversed_pairs": byte["reversed_pairs"],
        "action_byte_concordant_pairs": byte["concordant_pairs"],
        "action_byte_tied_pairs": byte["tied_pairs"],
        "action_byte_reversal_share_of_comparable_pairs": byte["reversal_share_of_comparable_pairs"],
        "sunset_action_rank_descending": descending_rank(windows, sunset, "actions"),
        "sunset_product_rank_descending": descending_rank(windows, sunset, "products"),
        "sunset_byte_rank_descending": descending_rank(windows, sunset, "archive_size_bytes"),
    }
    examples = [
        product_reversal_example(windows, "2", "18"),
        product_reversal_example(windows, "7", "h"),
    ]
    return metrics, examples


def verify_stage11g(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11g.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    prior = verify_stage11f(root) if prior is None else prior
    add_check(checks, errors, "protocol_weighting_canary_replays", prior["pass"], error="Stage 11F no longer verifies.")
    metrics, examples = derive(prior["windows"])
    metrics_ok = all(
        math.isclose(float(metrics[key]), float(expected), rel_tol=0.0, abs_tol=1e-12)
        if isinstance(expected, float) else metrics[key] == expected
        for key, expected in spec["frozen_observables"].items()
    )
    add_check(checks, errors, "unit_sensitive_pairwise_ordering", metrics_ok,
              error="The frozen pairwise unit-sensitive ordering census changed.", metrics=metrics)
    examples_ok = examples == spec["frozen_product_reversal_examples"]
    add_check(checks, errors, "frozen_product_reversal_examples", examples_ok,
              error="At least one frozen product/action reversal example changed.", examples=examples)
    state = spec["mutation_state"]
    boundary_ok = (
        not any((state["plan_windows_are_partition"], state["prominence_is_scientific_importance"],
                 state["window_ordering_is_unit_invariant"], state["observed_model_bias"],
                 state["causal_performance_effect"], state["one_universal_correct_weighting"],
                 state["novelty_or_priority"]))
        and state["actual_sampler"] == "unspecified"
        and state["scope"] == "verified_active_plan_windows"
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited partition, importance, invariance, sampler, model, effect, weighting, scope, novelty, or pixel claim was admitted.",
              mutation_state=state)
    evidence_state = "VERIFIED_UNIT_SENSITIVE_WINDOW_PROMINENCE" if metrics_ok and examples_ok else "UNIT_SENSITIVE_WINDOW_PROMINENCE_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "metrics": metrics,
        "product_reversal_examples": examples, "disposition": spec["disposition"],
        "verified": "Changing the counting unit can reverse which active plan window appears larger: 38 strictly comparable action/product pairs and 59 action/byte pairs reverse order. Sunset remains first by all three totals.",
        "decision_use": "Any claim that an observation is 'largest' or 'dominant' must name the unit. Product and byte prominence are acquisition-and-representation-weighted views, not neutral substitutes for action prominence.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage11f(root)
    baseline = verify_stage11g(root, prior=prior)
    names = load_json(root / "spec/stage11g.json")["hard_negatives"]
    mutations = {name: verify_stage11g(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11G hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["metrics"]
    lines = ["# Stage 11G — Unit-Sensitive Plan-Window Prominence", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Active windows / unordered pairs: `{item['active_plan_windows']}` / `{item['unordered_window_pairs']}`",
        f"- Action→product reversals: `{item['action_product_reversed_pairs']} / {item['action_product_strictly_comparable_pairs']}` (`{item['action_product_reversal_share_of_comparable_pairs']:.3%}`)",
        f"- Action→byte reversals: `{item['action_byte_reversed_pairs']} / {item['action_byte_strictly_comparable_pairs']}` (`{item['action_byte_reversal_share_of_comparable_pairs']:.3%}`)",
        f"- Sunset action / product / byte ranks: `{item['sunset_action_rank_descending']}` / `{item['sunset_product_rank_descending']}` / `{item['sunset_byte_rank_descending']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`", "", "## Verified", "", result["verified"],
        "", "## Exact product/action reversals", ""]
    for example in result["product_reversal_examples"]:
        lines.append(
            f"- `{example['more_actions_order']} {example['more_actions_name']}`: {example['more_actions_actions']} actions / {example['more_actions_products']} products; "
            f"`{example['more_products_order']} {example['more_products_name']}`: {example['more_products_actions']} actions / {example['more_products_products']} products."
        )
    lines.extend(["", "## Decision use", "", result["decision_use"], "", "## Claim ceiling", "", result["claim_ceiling"],
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11g(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
