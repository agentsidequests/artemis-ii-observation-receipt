#!/usr/bin/env python3
"""Verify Stage 11F's mission-wide protocol weighting canary."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json
from stage11e_unit_choice_reweighting import verify_stage11e


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "plan_windows_are_partition": False,
        "product_weight_is_image_content_weight": False,
        "five_exposure_windows_more_valuable": False,
        "actual_sampler": "unspecified",
        "observed_model_bias": False,
        "causal_performance_effect": False,
        "scope": "verified_complete_action_cohort",
        "scientific_discovery_claimed": False,
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_plan_windows_a_partition": ("plan_windows_are_partition", True),
        "call_product_weight_image_content_weight": ("product_weight_is_image_content_weight", True),
        "call_five_exposure_windows_more_valuable": ("five_exposure_windows_more_valuable", True),
        "claim_actual_sampler_is_uniform_products": ("actual_sampler", "uniform_products"),
        "claim_observed_model_bias": ("observed_model_bias", True),
        "claim_protocol_weighting_causal_performance_effect": ("causal_performance_effect", True),
        "generalize_to_unadmitted_archive_records": ("scope", "entire_archive"),
        "call_boundary_result_scientific_discovery": ("scientific_discovery_claimed", True),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels_during_protocol_test": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def derive(root: Path, spec: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = spec["source_contract"]
    manifest_by_action: dict[str, list[dict[str, str]]] = defaultdict(list)
    with (root / source["relationship_manifest_path"]).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            manifest_by_action[row["action_id"]].append(row)
    actions_by_order: dict[str, set[str]] = defaultdict(set)
    names: dict[str, str] = {}
    with (root / source["membership_ledger_path"]).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["plan_order"]:
                actions_by_order[row["plan_order"]].add(row["action_id"])
                names[row["plan_order"]] = row["plan_target_name"]
    windows: list[dict[str, Any]] = []
    for order, action_ids in actions_by_order.items():
        exposure_counts = [sum(row["collection_id"] == "data_source" for row in manifest_by_action[action_id]) for action_id in action_ids]
        products = sum(len(manifest_by_action[action_id]) for action_id in action_ids)
        total_bytes = sum(int(row["archive_size_bytes"]) for action_id in action_ids for row in manifest_by_action[action_id])
        regime = "pure_three" if set(exposure_counts) == {3} else "pure_five" if set(exposure_counts) == {5} else "mixed"
        windows.append({
            "plan_order": order, "plan_target_name": names[order], "regime": regime,
            "actions": len(action_ids), "exposures": sum(exposure_counts), "products": products,
            "archive_size_bytes": total_bytes, "exposures_per_action": sum(exposure_counts) / len(action_ids),
            "products_per_action": products / len(action_ids), "bytes_per_action": total_bytes / len(action_ids),
        })
    counts = Counter(window["regime"] for window in windows)
    product_weights = [window["products_per_action"] for window in windows]
    byte_weights = [window["bytes_per_action"] for window in windows]
    sunset = next(window for window in windows if window["plan_target_name"] == "Sunset")
    byte_rank = 1 + sum(value > sunset["bytes_per_action"] for value in byte_weights)
    metrics = {
        "active_plan_windows": len(windows),
        "pure_three_exposure_windows": counts["pure_three"],
        "pure_five_exposure_windows": counts["pure_five"],
        "mixed_exposure_windows": counts["mixed"],
        "minimum_products_per_action": min(product_weights),
        "maximum_products_per_action": max(product_weights),
        "median_products_per_action": statistics.median(product_weights),
        "pure_five_vs_pure_three_product_weight": 15 / 9,
        "minimum_bytes_per_action": min(byte_weights),
        "maximum_bytes_per_action": max(byte_weights),
        "maximum_vs_minimum_byte_weight": max(byte_weights) / min(byte_weights),
        "sunset_actions": sunset["actions"],
        "sunset_exposures_per_action": sunset["exposures_per_action"],
        "sunset_products_per_action": sunset["products_per_action"],
        "sunset_bytes_per_action": sunset["bytes_per_action"],
        "sunset_byte_weight_rank_descending": byte_rank,
    }
    return metrics, sorted(windows, key=lambda item: item["plan_order"])


def verify_stage11f(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11f.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    prior = verify_stage11e(root) if prior is None else prior
    add_check(checks, errors, "unit_choice_canary_replays", prior["pass"], error="Stage 11E no longer verifies.")
    metrics, windows = derive(root, spec)
    metrics_ok = all(
        math.isclose(float(metrics[key]), float(expected), rel_tol=0.0, abs_tol=1e-12)
        if isinstance(expected, float) else metrics[key] == expected
        for key, expected in spec["frozen_observables"].items()
    )
    add_check(checks, errors, "plan_window_protocol_weighting", metrics_ok,
              error="The frozen plan-window protocol-weighting census changed.", metrics=metrics)
    parity_ok = all(math.isclose(window["products_per_action"], 3 * window["exposures_per_action"], rel_tol=0.0, abs_tol=1e-12)
                    for window in windows)
    add_check(checks, errors, "three_representation_parity_per_window", parity_ok,
              error="At least one active window lost three-representation parity.")
    state = spec["mutation_state"]
    boundary_ok = (
        not any((state["plan_windows_are_partition"], state["product_weight_is_image_content_weight"],
                 state["five_exposure_windows_more_valuable"], state["observed_model_bias"],
                 state["causal_performance_effect"], state["scientific_discovery_claimed"],
                 state["novelty_or_priority"]))
        and state["actual_sampler"] == "unspecified"
        and state["scope"] == "verified_complete_action_cohort"
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited partition, content, value, sampler, model, scope, science, novelty, or pixel claim was admitted.",
              mutation_state=state)
    evidence_state = "VERIFIED_PLAN_WINDOW_PROTOCOL_WEIGHTING" if metrics_ok and parity_ok else "PLAN_WINDOW_PROTOCOL_WEIGHTING_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "metrics": metrics,
        "windows": windows, "disposition": spec["disposition"],
        "verified": "Acquisition-protocol weighting recurs across active plan windows: 19 contain only three-exposure actions, 11 contain only five-exposure actions, and six are mixed. With three archive representations per exposure, pure-five windows carry 15 products per action versus nine for pure-three windows.",
        "decision_use": "A flat product table embeds protocol weights across the mission, not only in Sunset. Sampling and evaluation should declare whether actions, events, or products receive equal weight.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage11e(root)
    baseline = verify_stage11f(root, prior=prior)
    names = load_json(root / "spec/stage11f.json")["hard_negatives"]
    mutations = {name: verify_stage11f(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11F hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["metrics"]
    lines = ["# Stage 11F — Plan-Window Protocol Weighting", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Active windows: `{item['active_plan_windows']}`",
        f"- Pure 3-exposure / pure 5-exposure / mixed: `{item['pure_three_exposure_windows']}` / `{item['pure_five_exposure_windows']}` / `{item['mixed_exposure_windows']}`",
        f"- Product range per action: `{item['minimum_products_per_action']:.0f}` to `{item['maximum_products_per_action']:.0f}`",
        f"- Pure-5 / pure-3 product weight: `{item['pure_five_vs_pure_three_product_weight']:.6f}×`",
        f"- Byte/action range: `{item['minimum_bytes_per_action'] / 1_000_000:.3f} MB` to `{item['maximum_bytes_per_action'] / 1_000_000_000:.3f} GB`",
        f"- Sunset: `{item['sunset_products_per_action']:.0f}` products/action; byte-weight rank `{item['sunset_byte_weight_rank_descending']}` of `{item['active_plan_windows']}`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11f(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
