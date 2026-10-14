#!/usr/bin/env python3
"""Verify Stage 11J's action-to-product rank-reversal attribution."""

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
from stage11i_weight_factorization import verify_stage11i


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "scientific_importance_ranking": False,
        "actual_sampler": "unspecified",
        "observed_model_bias": False,
        "causal_performance_effect": False,
        "formal_informative_cluster_size": False,
        "one_universal_correct_weighting": False,
        "discard_representations_or_brackets": False,
        "scope": "verified_active_plan_windows",
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "claim_scientific_importance_ranking": ("scientific_importance_ranking", True),
        "claim_actual_sampler_is_uniform_products": ("actual_sampler", "uniform_products"),
        "claim_observed_model_bias": ("observed_model_bias", True),
        "claim_causal_performance_effect": ("causal_performance_effect", True),
        "call_formal_informative_cluster_size": ("formal_informative_cluster_size", True),
        "claim_one_universal_correct_weighting": ("one_universal_correct_weighting", True),
        "recommend_discarding_representations_or_brackets": ("discard_representations_or_brackets", True),
        "generalize_to_unadmitted_archive_records": ("scope", "entire_archive"),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels_during_attribution": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def sign(value: int) -> int:
    return (value > 0) - (value < 0)


def derive(windows: list[dict[str, Any]], representations_per_capture: int) -> dict[str, Any]:
    equal_comparable = unequal_comparable = 0
    equal_reversals = unequal_reversals = 0
    reversal_directions: list[bool] = []
    product_rate_identities: list[bool] = []

    for window in windows:
        product_rate_identities.append(
            math.isclose(
                window["products_per_action"],
                representations_per_capture * window["exposures_per_action"],
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        )

    for left, right in itertools.combinations(windows, 2):
        action_sign = sign(left["actions"] - right["actions"])
        product_sign = sign(left["products"] - right["products"])
        if action_sign == 0 or product_sign == 0:
            continue
        equal_rate = left["products"] * right["actions"] == right["products"] * left["actions"]
        reversed_order = action_sign != product_sign
        if equal_rate:
            equal_comparable += 1
            equal_reversals += int(reversed_order)
        else:
            unequal_comparable += 1
            unequal_reversals += int(reversed_order)
        if reversed_order:
            higher_action, lower_action = (left, right) if action_sign > 0 else (right, left)
            reversal_directions.append(
                higher_action["products_per_action"] < lower_action["products_per_action"]
            )

    total_reversals = equal_reversals + unequal_reversals
    return {
        "active_plan_windows": len(windows),
        "strictly_comparable_action_product_pairs": equal_comparable + unequal_comparable,
        "equal_product_rate_comparable_pairs": equal_comparable,
        "unequal_product_rate_comparable_pairs": unequal_comparable,
        "equal_product_rate_reversals": equal_reversals,
        "unequal_product_rate_reversals": unequal_reversals,
        "all_reversals_cross_unequal_product_rates": total_reversals > 0 and equal_reversals == 0,
        "all_higher_action_windows_have_lower_product_rate": bool(reversal_directions) and all(reversal_directions),
        "all_window_product_rates_equal_three_times_exposure_rates": all(product_rate_identities),
        "constant_representations_per_capture": representations_per_capture,
    }


def verify_stage11j(
    root: Path,
    mutation: str | None = None,
    protocol_prior: dict[str, Any] | None = None,
    factor_prior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11j.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    protocol_prior = verify_stage11f(root) if protocol_prior is None else protocol_prior
    factor_prior = verify_stage11i(root) if factor_prior is None else factor_prior
    add_check(checks, errors, "protocol_weighting_canary_replays", protocol_prior["pass"],
              error="Stage 11F no longer verifies.")
    add_check(checks, errors, "weight_factorization_canary_replays", factor_prior["pass"],
              error="Stage 11I no longer verifies.")
    representations = factor_prior["metrics"]["representations_per_capture"]
    metrics = derive(protocol_prior["windows"], representations)
    metrics_ok = all(metrics[key] == expected for key, expected in spec["frozen_observables"].items())
    add_check(checks, errors, "rank_reversal_attribution", metrics_ok,
              error="The frozen rank-reversal attribution changed.", metrics=metrics)

    state = spec["mutation_state"]
    boundary_ok = (
        not any((state["scientific_importance_ranking"], state["observed_model_bias"],
                 state["causal_performance_effect"], state["formal_informative_cluster_size"],
                 state["one_universal_correct_weighting"], state["discard_representations_or_brackets"],
                 state["novelty_or_priority"]))
        and state["actual_sampler"] == "unspecified"
        and state["scope"] == "verified_active_plan_windows"
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited importance, sampler, model, causal, cluster-size, correction, deletion, scope, novelty, or pixel claim was admitted.",
              mutation_state=state)
    evidence_state = "VERIFIED_PROTOCOL_ATTRIBUTION_OF_PRODUCT_RANK_REVERSALS" if metrics_ok else "PRODUCT_RANK_REVERSAL_ATTRIBUTION_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "metrics": metrics,
        "disposition": spec["disposition"],
        "verified": "All 38 action-to-product plan-window rank reversals occur across unequal products-per-action rates, and in every case the window with more actions has the lower rate. With exactly three representations per capture throughout the admitted cohort, exposure-protocol composition is the varying multiplicity behind these product-rank reversals.",
        "decision_use": "The acquisition protocol becomes an implicit observation-weighting policy only when the hierarchy is flattened to products. This is an arithmetic property of the admitted archive structure, not evidence that an actual model used that sampler or suffered bias.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    protocol_prior = verify_stage11f(root)
    factor_prior = verify_stage11i(root)
    baseline = verify_stage11j(root, protocol_prior=protocol_prior, factor_prior=factor_prior)
    names = load_json(root / "spec/stage11j.json")["hard_negatives"]
    mutations = {
        name: verify_stage11j(root, name, protocol_prior=protocol_prior, factor_prior=factor_prior)
        for name in names
    }
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11J hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["metrics"]
    lines = ["# Stage 11J — Product-Rank Reversal Attribution", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Active windows / strictly comparable pairs: `{item['active_plan_windows']}` / `{item['strictly_comparable_action_product_pairs']}`",
        f"- Equal-rate comparable pairs / reversals: `{item['equal_product_rate_comparable_pairs']}` / `{item['equal_product_rate_reversals']}`",
        f"- Unequal-rate comparable pairs / reversals: `{item['unequal_product_rate_comparable_pairs']}` / `{item['unequal_product_rate_reversals']}`",
        f"- Constant representations per capture: `{item['constant_representations_per_capture']}`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11j(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
