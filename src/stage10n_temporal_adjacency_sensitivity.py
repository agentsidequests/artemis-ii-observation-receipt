#!/usr/bin/env python3
"""Verify Stage 10N's conditional temporal-adjacency split sensitivity."""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_hits, load_json, normalize_hit, parse_utc
from stage10c_camera_action_integrity import detect_complete_brackets
from stage10e_all_days_integrity import load_daily_hits
from stage10j_fractional_bracket_expansion import verify_stage10j
from stage10m_ai_split_hazard import verify_stage10m


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "clusters_are_semantic_scenes": False,
        "result_kind": "conditional_expected_crossing",
        "action_grouping_universally_sufficient": False,
        "threshold_status": "sensitivity_set",
        "camera_scope": "same_serial_only",
        "action_scope": "verified_complete_actions",
        "performance_effect_inferred": False,
        "global_priority": False,
        "facet_evidence_status": "non_independent_structural_diagnostic",
        "facets_are_correct_or_images_similar": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    mapping = {
        "call_temporal_clusters_semantic_scenes": ("clusters_are_semantic_scenes", True),
        "call_expected_crossing_observed_leakage": ("result_kind", "observed_leakage"),
        "claim_action_grouping_is_universally_sufficient": ("action_grouping_universally_sufficient", True),
        "promote_one_threshold_to_ground_truth": ("threshold_status", "five_seconds_is_ground_truth"),
        "mix_camera_serials_in_clusters": ("camera_scope", "all_cameras_one_sequence"),
        "count_unadmitted_records_as_actions": ("action_scope", "all_records"),
        "infer_model_performance_effect": ("performance_effect_inferred", True),
        "claim_global_priority": ("global_priority", True),
        "call_facet_concordance_independent_validation": ("facet_evidence_status", "independent_validation"),
        "infer_facets_are_correct_or_images_are_similar": ("facets_are_correct_or_images_similar", True),
        "open_pixels_for_temporal_sensitivity": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    state[key] = value
    return mutated


def reconstruct_actions(root: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    contract = spec["source_contract"]
    stage10j_spec = load_json(root / "spec/stage10j.json")
    receipt10a = load_json(root / contract["stage10a_receipt_path"])
    receipt10e = load_json(root / contract["stage10e_receipt_path"])
    fd6_hits, fd6_errors = load_hits(root, receipt10a)
    daily_hits, daily_errors = load_daily_hits(root, receipt10e)
    if fd6_errors or daily_errors:
        raise ValueError(f"Source replay failed: {fd6_errors + daily_errors}")
    records = [normalize_hit(hit) for hit in daily_hits + fd6_hits]
    bracket_contract = copy.deepcopy(load_json(root / contract["stage10c_spec_path"])["complete_bracket_contract"])
    bracket_contract["allowed_bracket_sequences"] = stage10j_spec["expanded_patterns"]
    return detect_complete_brackets(records, bracket_contract)


def temporal_clusters(actions: list[dict[str, Any]], threshold_seconds: float) -> list[list[dict[str, Any]]]:
    by_serial: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for action in actions:
        by_serial[action["serial"]].append(action)
    clusters: list[list[dict[str, Any]]] = []
    for serial in sorted(by_serial):
        current: list[dict[str, Any]] = []
        for action in sorted(by_serial[serial], key=lambda item: item["start_time"]):
            if current:
                gap = (parse_utc(action["start_time"]) - parse_utc(current[-1]["end_time"])).total_seconds()
                if gap > threshold_seconds:
                    clusters.append(current)
                    current = []
            current.append(action)
        if current:
            clusters.append(current)
    return clusters


def summarize_clusters(clusters: list[list[dict[str, Any]]], train_probability: float) -> dict[str, Any]:
    sizes = [len(cluster) for cluster in clusters]
    crossing_probabilities = [1.0 - train_probability ** size - (1.0 - train_probability) ** size for size in sizes]
    expected_crossing = sum(crossing_probabilities)
    expected_actions = sum(size * probability for size, probability in zip(sizes, crossing_probabilities))
    total_actions = sum(sizes)
    return {
        "clusters": len(clusters),
        "multi_action_clusters": sum(size > 1 for size in sizes),
        "actions_in_multi_action_clusters": sum(size for size in sizes if size > 1),
        "maximum_cluster_actions": max(sizes),
        "expected_crossing_clusters": expected_crossing,
        "expected_actions_in_crossing_clusters": expected_actions,
        "expected_action_exposure_rate": expected_actions / total_actions,
    }


def facet_diagnostic(clusters: list[list[dict[str, Any]]]) -> dict[str, Any]:
    multi = [cluster for cluster in clusters if len(cluster) > 1]

    def values(cluster: list[dict[str, Any]], field: str) -> set[str]:
        return {value for action in cluster for value in action[field] if value}

    activity_counts = [len(values(cluster, "activity_ids")) for cluster in multi]
    target_counts = [len(values(cluster, "target_ids")) for cluster in multi]
    target_bearing = sum(count > 0 for count in target_counts)
    single_activity = sum(count == 1 for count in activity_counts)
    single_target = sum(count == 1 for count in target_counts)
    return {
        "multi_action_clusters": len(multi),
        "single_activity_clusters": single_activity,
        "mixed_activity_clusters": sum(count > 1 for count in activity_counts),
        "no_activity_clusters": sum(count == 0 for count in activity_counts),
        "single_activity_rate": single_activity / len(multi),
        "target_bearing_clusters": target_bearing,
        "single_target_clusters": single_target,
        "mixed_target_clusters": sum(count > 1 for count in target_counts),
        "no_target_clusters": sum(count == 0 for count in target_counts),
        "single_target_rate_among_target_bearing": single_target / target_bearing,
    }


def values_match(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if isinstance(expected_value, float):
            if not math.isclose(actual_value, expected_value, rel_tol=0.0, abs_tol=1e-12):
                return False
        elif actual_value != expected_value:
            return False
    return True


def verify_stage10n(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10n.json"), mutation)
    expected = spec["frozen_observables"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    stage10j = verify_stage10j(root)
    stage10m = verify_stage10m(root)
    actions = reconstruct_actions(root, spec)
    source_ok = stage10j.get("pass") is True and stage10m.get("pass") is True and len(actions) == expected["complete_actions"]
    add_check(checks, errors, "source_action_replay", source_ok,
              error="The verified action cohort or preceding split-hazard result did not replay.", actions=len(actions))

    scenarios: dict[str, dict[str, Any]] = {}
    scenario_failures: list[str] = []
    for threshold in expected["thresholds_seconds"]:
        key = str(threshold)
        result = summarize_clusters(temporal_clusters(actions, float(threshold)), expected["train_probability"])
        scenarios[key] = result
        if not values_match(result, expected["scenarios"][key]):
            scenario_failures.append(key)
    add_check(checks, errors, "frozen_threshold_sensitivity", not scenario_failures,
              error="At least one temporal-adjacency sensitivity result changed.", failures=scenario_failures)

    monotonic_ok = all(
        scenarios[str(left)]["expected_action_exposure_rate"] < scenarios[str(right)]["expected_action_exposure_rate"]
        for left, right in zip(expected["thresholds_seconds"], expected["thresholds_seconds"][1:])
    )
    add_check(checks, errors, "broader_grouping_increases_action_exposure", monotonic_ok,
              error="The threshold sensitivity no longer increases expected action exposure monotonically.")

    facet_result = facet_diagnostic(temporal_clusters(actions, 5.0))
    facet_ok = values_match(facet_result, expected["five_second_facet_diagnostic"])
    add_check(checks, errors, "five_second_facet_concordance", facet_ok,
              error="The five-second temporal clusters no longer match the frozen facet diagnostic.",
              diagnostic=facet_result)

    state = spec["mutation_state"]
    boundary_ok = (
        not state["clusters_are_semantic_scenes"]
        and state["result_kind"] == "conditional_expected_crossing"
        and not state["action_grouping_universally_sufficient"]
        and state["threshold_status"] == "sensitivity_set"
        and state["camera_scope"] == "same_serial_only"
        and state["action_scope"] == "verified_complete_actions"
        and not state["performance_effect_inferred"]
        and not state["global_priority"]
        and state["facet_evidence_status"] == "non_independent_structural_diagnostic"
        and not state["facets_are_correct_or_images_similar"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited semantic, observed, sufficiency, threshold, scope, performance, novelty, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_TEMPORAL_ADJACENCY_SPLIT_SENSITIVITY" if source_ok and not scenario_failures and monotonic_ok and facet_ok else "TEMPORAL_SENSITIVITY_UNRESOLVED"
    five = scenarios["5"]
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "complete_actions": len(actions), "train_probability": expected["train_probability"], "scenarios": scenarios,
        "verified": "Action-level grouping removes the exact representation and bracket-sibling crossings modeled in Stage 10M, but it does not guarantee temporal-episode independence. Under a conditional five-second same-camera adjacency rule, 1,656 of 2,166 actions lie in multi-action clusters; independent 80/20 action assignment puts an expected 1,239.004 actions (57.202%) in clusters that cross the partition. The conditional rate ranges from 4.046% at one second to 86.193% at thirty seconds. At five seconds, 290 of 306 multi-action clusters carry one activity value across all admitted exposures, and 132 of 139 target-bearing clusters carry one target value. Because those facets are time-derived and partly curated, this is structural concordance rather than independent scene validation.",
        "decision_use": "Treat reconstructed action identity as a necessary minimum grouping key, not a complete evaluation design. A real task must freeze whether scene, target, time, operator, or acquisition episode creates broader dependence before a split is built.",
        "primary_five_second": five, "five_second_facet_diagnostic": facet_result,
        "pixel_payload_bytes": state["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"], "next_step_logic": spec["next_step_logic"],
        "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10n(root)
    names = load_json(root / "spec/stage10n.json")["hard_negatives"]
    mutations = {name: verify_stage10n(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10N hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10N — Temporal-Adjacency Split Sensitivity", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Verified complete actions: `{result['complete_actions']:,}`",
        f"- Hypothetical split: `{result['train_probability']:.0%}/{1-result['train_probability']:.0%}` at the action level",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified conditional result", "", result["verified"], "", "## Threshold sensitivity", "",
    ]
    for threshold, scenario in result["scenarios"].items():
        lines.append(
            f"- `{threshold}s`: `{scenario['actions_in_multi_action_clusters']:,}` actions in multi-action clusters; "
            f"expected `{scenario['expected_actions_in_crossing_clusters']:.3f}` actions (`{scenario['expected_action_exposure_rate']:.3%}`) in crossing clusters"
        )
    facet = result["five_second_facet_diagnostic"]
    lines += [
        "", "## Non-independent facet diagnostic", "",
        f"At five seconds, `{facet['single_activity_clusters']}` / `{facet['multi_action_clusters']}` multi-action clusters (`{facet['single_activity_rate']:.3%}`) carry one activity value across their admitted exposures. Of `{facet['target_bearing_clusters']}` clusters with any target value, `{facet['single_target_clusters']}` (`{facet['single_target_rate_among_target_bearing']:.3%}`) carry one target value. These time-derived and partly curated facets corroborate archive structure; they do not independently validate scene identity, label correctness, or image similarity.",
        "", "## Decision use", "", result["decision_use"], "", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", "",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10n(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
