#!/usr/bin/env python3
"""Verify Stage 11K's byte-rank factorization."""

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
from stage11j_rank_reversal_attribution import verify_stage11j


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "byte_rank_is_scientific_importance": False,
        "mean_bytes_per_product_is_quality": False,
        "actual_sampler": "unspecified",
        "observed_model_bias": False,
        "causal_performance_effect": False,
        "one_universal_correct_weighting": False,
        "discard_large_products": False,
        "scope": "verified_active_plan_windows",
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "claim_byte_rank_is_scientific_importance": ("byte_rank_is_scientific_importance", True),
        "claim_mean_bytes_per_product_is_quality": ("mean_bytes_per_product_is_quality", True),
        "claim_actual_sampler_is_uniform_bytes": ("actual_sampler", "uniform_bytes"),
        "claim_observed_model_bias": ("observed_model_bias", True),
        "claim_causal_performance_effect": ("causal_performance_effect", True),
        "claim_one_universal_correct_weighting": ("one_universal_correct_weighting", True),
        "recommend_discarding_large_products": ("discard_large_products", True),
        "generalize_to_unadmitted_archive_records": ("scope", "entire_archive"),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels_during_byte_factorization": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def sign(value: int) -> int:
    return (value > 0) - (value < 0)


def ordered_example(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    higher, lower = (left, right) if left["actions"] > right["actions"] else (right, left)
    return {
        "higher_action_order": higher["plan_order"], "higher_action_name": higher["plan_target_name"],
        "higher_action_actions": higher["actions"], "higher_action_products": higher["products"],
        "higher_action_bytes": higher["archive_size_bytes"],
        "lower_action_order": lower["plan_order"], "lower_action_name": lower["plan_target_name"],
        "lower_action_actions": lower["actions"], "lower_action_products": lower["products"],
        "lower_action_bytes": lower["archive_size_bytes"],
    }


def derive(windows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    counts = {"product_and_byte_reversals": 0, "product_only_reversals": 0,
              "byte_only_reversals": 0, "neither_reverses": 0}
    examples: dict[str, Any] = {}
    factor_checks = []
    strict = 0
    for window in windows:
        factor_checks.append(math.isclose(
            window["bytes_per_action"],
            window["products_per_action"] * window["archive_size_bytes"] / window["products"],
            rel_tol=0.0, abs_tol=1e-6,
        ))
    for left, right in itertools.combinations(windows, 2):
        action_sign = sign(left["actions"] - right["actions"])
        product_sign = sign(left["products"] - right["products"])
        byte_sign = sign(left["archive_size_bytes"] - right["archive_size_bytes"])
        if action_sign == 0 or product_sign == 0 or byte_sign == 0:
            continue
        strict += 1
        product_reverses = action_sign != product_sign
        byte_reverses = action_sign != byte_sign
        if product_reverses and byte_reverses:
            counts["product_and_byte_reversals"] += 1
        elif product_reverses:
            counts["product_only_reversals"] += 1
            examples.setdefault("product_only", ordered_example(left, right))
        elif byte_reverses:
            counts["byte_only_reversals"] += 1
            examples.setdefault("byte_only", ordered_example(left, right))
        else:
            counts["neither_reverses"] += 1
    product_total = counts["product_and_byte_reversals"] + counts["product_only_reversals"]
    byte_total = counts["product_and_byte_reversals"] + counts["byte_only_reversals"]
    metrics = {
        "strictly_comparable_action_product_byte_pairs": strict, **counts,
        "total_product_reversals": product_total, "total_byte_reversals": byte_total,
        "byte_reversal_overlap_with_product_reversal_share": counts["product_and_byte_reversals"] / byte_total,
        "byte_only_share_of_byte_reversals": counts["byte_only_reversals"] / byte_total,
        "all_window_byte_rates_factor_exactly": all(factor_checks),
    }
    return metrics, examples


def verify_stage11k(root: Path, mutation: str | None = None,
                    protocol_prior: dict[str, Any] | None = None,
                    attribution_prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11k.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    protocol_prior = verify_stage11f(root) if protocol_prior is None else protocol_prior
    attribution_prior = verify_stage11j(root) if attribution_prior is None else attribution_prior
    add_check(checks, errors, "protocol_weighting_canary_replays", protocol_prior["pass"], error="Stage 11F no longer verifies.")
    add_check(checks, errors, "product_reversal_attribution_replays", attribution_prior["pass"], error="Stage 11J no longer verifies.")
    metrics, examples = derive(protocol_prior["windows"])
    metrics_ok = all(
        math.isclose(float(metrics[key]), float(expected), rel_tol=0.0, abs_tol=1e-12)
        if isinstance(expected, float) else metrics[key] == expected
        for key, expected in spec["frozen_observables"].items()
    )
    examples_ok = examples == spec["frozen_examples"]
    add_check(checks, errors, "byte_rank_cross_classification", metrics_ok,
              error="The frozen product/byte rank cross-classification changed.", metrics=metrics)
    add_check(checks, errors, "frozen_counterexamples", examples_ok,
              error="A frozen product-only or byte-only reversal example changed.", examples=examples)
    state = spec["mutation_state"]
    boundary_ok = (
        not any((state["byte_rank_is_scientific_importance"], state["mean_bytes_per_product_is_quality"],
                 state["observed_model_bias"], state["causal_performance_effect"],
                 state["one_universal_correct_weighting"], state["discard_large_products"],
                 state["novelty_or_priority"]))
        and state["actual_sampler"] == "unspecified"
        and state["scope"] == "verified_active_plan_windows"
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited importance, quality, sampler, model, causal, correction, deletion, scope, novelty, or pixel claim was admitted.",
              mutation_state=state)
    evidence_state = "VERIFIED_BYTE_WEIGHT_AS_DISTINCT_ARCHIVE_LAYER" if metrics_ok and examples_ok else "BYTE_WEIGHT_FACTOR_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "metrics": metrics,
        "examples": examples, "disposition": spec["disposition"],
        "verified": "Of 38 action-to-product rank reversals, 35 persist under byte totals and three are undone; byte weighting creates 24 additional reversals, yielding 59. Byte prominence therefore combines protocol-derived products/action with a distinct mean-bytes/product layer.",
        "decision_use": "Use products to reason about protocol-derived sample weight and bytes to reason about retrieval or systems burden. Neither is a neutral proxy for observations, and byte size is not a quality score.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    protocol_prior = verify_stage11f(root)
    attribution_prior = verify_stage11j(root)
    baseline = verify_stage11k(root, protocol_prior=protocol_prior, attribution_prior=attribution_prior)
    names = load_json(root / "spec/stage11k.json")["hard_negatives"]
    mutation_results = {
        name: verify_stage11k(root, name, protocol_prior=protocol_prior, attribution_prior=attribution_prior)
        for name in names
    }
    hard_negatives_pass = all(not result["pass"] for result in mutation_results.values())
    return {**baseline, "hard_negatives": {name: "REJECTED" if not item["pass"] else "ACCEPTED" for name, item in mutation_results.items()},
            "hard_negatives_pass": hard_negatives_pass, "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11K hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["metrics"]
    lines = ["# Stage 11K — Byte-Rank Factorization", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Strictly comparable action/product/byte pairs: `{item['strictly_comparable_action_product_byte_pairs']}`",
        f"- Both reverse / product only / byte only / neither: `{item['product_and_byte_reversals']}` / `{item['product_only_reversals']}` / `{item['byte_only_reversals']}` / `{item['neither_reverses']}`",
        f"- Total product / byte reversals: `{item['total_product_reversals']}` / `{item['total_byte_reversals']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`", "", "## Verified", "", result["verified"],
        "", "## Decision use", "", result["decision_use"], "", "## Claim ceiling", "", result["claim_ceiling"],
        "", "## Hard negatives", ""]
    for name, outcome in result.get("hard_negatives", {}).items():
        lines.append(f"- `{name}`: {outcome}")
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11k(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
