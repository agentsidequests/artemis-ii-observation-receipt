#!/usr/bin/env python3
"""Verify Stage 11H's protocol-context alignment canary."""

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

from stage10a_metadata_integrity import add_check, load_json
from stage11g_unit_sensitive_prominence import verify_stage11g


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "plan_memberships_are_partition": False,
        "fitted_regime_rule_is_held_out": False,
        "bracket_length_is_target_or_content_label": False,
        "actual_sampler": "unspecified",
        "observed_model_bias": False,
        "drop_bracket_exposures": False,
        "one_universal_correct_weighting": False,
        "scope": "verified_plan_associated_action_union",
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_plan_memberships_a_partition": ("plan_memberships_are_partition", True),
        "call_fitted_regime_rule_held_out": ("fitted_regime_rule_is_held_out", True),
        "call_bracket_length_a_target_or_content_label": ("bracket_length_is_target_or_content_label", True),
        "claim_actual_sampler_is_uniform_products": ("actual_sampler", "uniform_products"),
        "claim_observed_model_bias": ("observed_model_bias", True),
        "recommend_dropping_bracket_exposures": ("drop_bracket_exposures", True),
        "claim_one_universal_correct_weighting": ("one_universal_correct_weighting", True),
        "generalize_to_unadmitted_archive_records": ("scope", "entire_archive"),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels_during_alignment_test": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def derive(root: Path, spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    source = spec["source_contract"]
    associated_ids: set[str] = set()
    with (root / source["membership_ledger_path"]).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["plan_order"]:
                associated_ids.add(row["action_id"])
    actions: dict[str, dict[str, Any]] = {}
    with (root / source["relationship_manifest_path"]).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["collection_id"] != "data_source" or row["action_id"] not in associated_ids:
                continue
            action = actions.setdefault(row["action_id"], {
                "action_id": row["action_id"], "camera_serial": row["camera_serial"],
                "action_start_utc": row["action_start_utc"], "exposures_in_action": int(row["exposures_in_action"]),
            })
            if (action["camera_serial"], action["action_start_utc"], action["exposures_in_action"]) != (
                row["camera_serial"], row["action_start_utc"], int(row["exposures_in_action"])
            ):
                raise ValueError(f"Inconsistent action metadata: {row['action_id']}")
    if set(actions) != associated_ids:
        raise ValueError("At least one plan-associated action is absent from the relationship manifest.")
    counts = Counter(action["exposures_in_action"] for action in actions.values())
    flat_products = sum(3 * action["exposures_in_action"] for action in actions.values())
    five_products = counts[5] * 15
    camera_actions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for action in actions.values():
        camera_actions[action["camera_serial"]].append(action)
    runs: dict[str, list[dict[str, Any]]] = {}
    for camera, items in camera_actions.items():
        ordered = sorted(items, key=lambda item: (item["action_start_utc"], item["action_id"]))
        camera_runs: list[dict[str, Any]] = []
        for item in ordered:
            exposure_count = item["exposures_in_action"]
            if not camera_runs or camera_runs[-1]["exposures_in_action"] != exposure_count:
                camera_runs.append({
                    "exposures_in_action": exposure_count,
                    "start_utc": item["action_start_utc"],
                    "actions": 0,
                })
            camera_runs[-1]["actions"] += 1
        runs[camera] = camera_runs
    camera_counts = {camera: Counter(item["exposures_in_action"] for item in items) for camera, items in camera_actions.items()}
    metrics = {
        "plan_associated_unique_actions": len(actions),
        "three_exposure_actions": counts[3],
        "five_exposure_actions": counts[5],
        "five_exposure_action_share": counts[5] / len(actions),
        "flat_products": flat_products,
        "five_exposure_flat_products": five_products,
        "five_exposure_product_share": five_products / flat_products,
        "five_exposure_product_vs_action_share_amplification": (five_products / flat_products) / (counts[5] / len(actions)),
        "camera_3500015_actions": len(camera_actions["3500015"]),
        "camera_3500015_three_exposure_actions": camera_counts["3500015"][3],
        "camera_3500015_five_exposure_actions": camera_counts["3500015"][5],
        "camera_3500015_exposure_count_transitions": len(runs["3500015"]) - 1,
        "camera_3500015_five_run_start_utc": runs["3500015"][1]["start_utc"],
        "camera_3500015_following_three_run_start_utc": runs["3500015"][2]["start_utc"],
        "camera_3500017_actions": len(camera_actions["3500017"]),
        "camera_3500017_three_exposure_actions": camera_counts["3500017"][3],
        "camera_3500017_five_exposure_actions": camera_counts["3500017"][5],
        "camera_3500017_exposure_count_transitions": len(runs["3500017"]) - 1,
        "camera_3920019_actions": len(camera_actions["3920019"]),
        "camera_3920019_three_exposure_actions": camera_counts["3920019"][3],
        "camera_3920019_five_exposure_actions": camera_counts["3920019"][5],
        "camera_3920019_exposure_count_transitions": len(runs["3920019"]) - 1,
        "camera_3920019_action_share": len(camera_actions["3920019"]) / len(actions),
        "camera_3920019_flat_products": sum(3 * item["exposures_in_action"] for item in camera_actions["3920019"]),
        "camera_3920019_product_share": sum(3 * item["exposures_in_action"] for item in camera_actions["3920019"]) / flat_products,
        "camera_3920019_product_vs_action_share_amplification": (
            sum(3 * item["exposures_in_action"] for item in camera_actions["3920019"]) / flat_products
        ) / (len(camera_actions["3920019"]) / len(actions)),
    }
    return metrics, runs


def verify_stage11h(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11h.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    prior = verify_stage11g(root) if prior is None else prior
    add_check(checks, errors, "unit_sensitive_prominence_replays", prior["pass"], error="Stage 11G no longer verifies.")
    metrics, runs = derive(root, spec)
    metrics_ok = all(
        math.isclose(float(metrics[key]), float(expected), rel_tol=0.0, abs_tol=1e-12)
        if isinstance(expected, float) else metrics[key] == expected
        for key, expected in spec["frozen_observables"].items()
    )
    add_check(checks, errors, "protocol_context_alignment", metrics_ok,
              error="The frozen plan-associated protocol-context alignment changed.", metrics=metrics)
    run_shape_ok = (
        [item["exposures_in_action"] for item in runs["3500015"]] == [3, 5, 3]
        and [item["exposures_in_action"] for item in runs["3500017"]] == [3]
        and [item["exposures_in_action"] for item in runs["3920019"]] == [5]
    )
    add_check(checks, errors, "camera_time_run_shape", run_shape_ok,
              error="The frozen camera-specific exposure-count run shape changed.", camera_runs=runs)
    state = spec["mutation_state"]
    boundary_ok = (
        not any((state["plan_memberships_are_partition"], state["fitted_regime_rule_is_held_out"],
                 state["bracket_length_is_target_or_content_label"], state["observed_model_bias"],
                 state["drop_bracket_exposures"], state["one_universal_correct_weighting"],
                 state["novelty_or_priority"]))
        and state["actual_sampler"] == "unspecified"
        and state["scope"] == "verified_plan_associated_action_union"
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited partition, prediction, content, sampler, model, deletion, weighting, scope, novelty, or pixel claim was admitted.",
              mutation_state=state)
    evidence_state = "VERIFIED_PROTOCOL_CONTEXT_ALIGNMENT" if metrics_ok and run_shape_ok else "PROTOCOL_CONTEXT_ALIGNMENT_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "metrics": metrics,
        "camera_runs": runs, "disposition": spec["disposition"],
        "verified": "Within the deduplicated plan-associated action union, the five-exposure protocol is aligned with camera and contiguous time regimes. Five-exposure actions are 35.455% of actions but 47.794% of flat products; camera 3920019 rises from 10.130% of actions to 13.655% of products.",
        "decision_use": "A flat product table can inherit operational camera/time structure from the acquisition protocol before any pixel feature is measured. Preserve the intentional exposures, but make the sampling estimand and protocol strata explicit.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage11g(root)
    baseline = verify_stage11h(root, prior=prior)
    names = load_json(root / "spec/stage11h.json")["hard_negatives"]
    mutations = {name: verify_stage11h(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11H hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["metrics"]
    lines = ["# Stage 11H — Protocol–Context Alignment", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Plan-associated action union: `{item['plan_associated_unique_actions']}`",
        f"- Three- / five-exposure actions: `{item['three_exposure_actions']}` / `{item['five_exposure_actions']}`",
        f"- Five-exposure action / product shares: `{item['five_exposure_action_share']:.3%}` / `{item['five_exposure_product_share']:.3%}`",
        f"- Product-share amplification: `{item['five_exposure_product_vs_action_share_amplification']:.6f}×`",
        f"- Camera 3500015 run shape: `3 → 5 → 3` with `{item['camera_3500015_exposure_count_transitions']}` transitions",
        f"- Camera 3500017: `{item['camera_3500017_actions']}` / `{item['camera_3500017_actions']}` three-exposure actions",
        f"- Camera 3920019: `{item['camera_3920019_actions']}` / `{item['camera_3920019_actions']}` five-exposure actions",
        f"- Camera 3920019 action / product shares: `{item['camera_3920019_action_share']:.3%}` / `{item['camera_3920019_product_share']:.3%}`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11h(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
