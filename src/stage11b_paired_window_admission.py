#!/usr/bin/env python3
"""Verify Stage 11B's paired-window task admission."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json
from stage11a_planned_target_replication import verify_stage11a


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "plan_membership_is_image_content": False, "same_name_is_scene_equivalence": False,
        "same_camera_is_calibrated_photometry": False, "windows_are_independent_events": False,
        "sparse_tags_are_negative_evidence": False, "model_partition_assigned": False,
        "performance_effect_inferred": False, "scientific_result_claimed": False,
        "novelty_or_priority": False, "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_plan_membership_image_content": ("plan_membership_is_image_content", True),
        "call_same_name_scene_equivalence": ("same_name_is_scene_equivalence", True),
        "call_same_camera_calibrated_photometry": ("same_camera_is_calibrated_photometry", True),
        "call_windows_independent_events": ("windows_are_independent_events", True),
        "call_sparse_tags_negative_evidence": ("sparse_tags_are_negative_evidence", True),
        "assign_model_partition_before_registration": ("model_partition_assigned", True),
        "claim_model_performance_effect": ("performance_effect_inferred", True),
        "call_candidate_scientific_result": ("scientific_result_claimed", True),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels_during_admission": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def exact_mapping(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    return all(
        close(float(actual[key]), float(value)) if isinstance(value, float) else actual[key] == value
        for key, value in expected.items()
    )


def derive(plan: list[dict[str, Any]], ledger: list[dict[str, str]], manifest: list[dict[str, str]]) -> tuple[dict[str, Any], dict[str, dict[str, Any]], bool]:
    active_orders = {row["plan_order"] for row in ledger if row["plan_order"]}
    plan_by_order = {str(item["target_properties"].get("order")): item["target_properties"] for item in plan}
    active_by_target: dict[str, list[str]] = defaultdict(list)
    for order in sorted(active_orders):
        active_by_target[plan_by_order[order]["target_name"]].append(order)
    candidates = {
        target: orders for target, orders in active_by_target.items()
        if len(orders) == 2
        and all(float(plan_by_order[order].get("diameter", 0)) > 0 for order in orders)
        and all(float(plan_by_order[order].get("latitude", 0)) != 0 for order in orders)
        and all(float(plan_by_order[order].get("longitude", 0)) != 0 for order in orders)
    }
    ledger_by_order: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ledger:
        if row["plan_order"]:
            ledger_by_order[row["plan_order"]].append(row)
    manifest_by_action: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in manifest:
        manifest_by_action[row["action_id"]].append(row)

    details: dict[str, dict[str, Any]] = {}
    total_actions: set[str] = set()
    total_exposures = total_products = total_bytes = total_tags = 0
    all_disjoint = all_same_camera = True
    explicit_repeats = 0
    for target, orders in sorted(candidates.items()):
        orders = sorted(orders, key=lambda order: ledger_by_order[order][0]["plan_start_utc"])
        window_items = []
        for order in orders:
            members = ledger_by_order[order]
            action_ids = {row["action_id"] for row in members}
            rows = [row for action_id in action_ids for row in manifest_by_action[action_id]]
            source_rows = [row for row in rows if row["collection_id"] == "data_source"]
            window_items.append({
                "actions": len(action_ids), "exposures": len(source_rows), "products": len(rows),
                "archive_size_bytes": sum(int(row["archive_size_bytes"]) for row in rows),
                "exact_same_name_tags": sum(row["target_id"] == target for row in source_rows),
                "camera_serials": sorted({row["camera_serial"] for row in source_rows}),
                "start": parse_utc(members[0]["plan_start_utc"]), "end": parse_utc(members[0]["plan_end_utc"]),
                "action_ids": action_ids,
            })
            total_actions.update(action_ids)
            total_exposures += len(source_rows); total_products += len(rows)
            total_bytes += sum(int(row["archive_size_bytes"]) for row in rows)
            total_tags += sum(row["target_id"] == target for row in source_rows)
        disjoint = window_items[0]["end"] <= window_items[1]["start"]
        cameras = sorted(set(window_items[0]["camera_serials"]) | set(window_items[1]["camera_serials"]))
        same_camera = len(cameras) == 1 and all(item["camera_serials"] == cameras for item in window_items)
        all_disjoint &= disjoint; all_same_camera &= same_camera
        first, second = (plan_by_order[order] for order in orders)
        explicit = (
            "first of two photometric observations" in first.get("target_description", "").casefold()
            and "second of two photometric observations" in second.get("target_description", "").casefold()
            and "repeat observations" in first.get("impact_statement", "").casefold()
        )
        explicit_repeats += explicit
        intent = "explicit_photometric_viewing_condition_repeat" if explicit else (
            "same_name_two_part_plan" if target == "Orientale Basin" else "same_name_revisit_no_explicit_photometric_repeat"
        )
        details[target] = {
            "orders": orders, "window_gap_seconds": (window_items[1]["start"] - window_items[0]["end"]).total_seconds(),
            "actions": [item["actions"] for item in window_items],
            "exposures": [item["exposures"] for item in window_items],
            "products": [item["products"] for item in window_items],
            "archive_size_bytes": [item["archive_size_bytes"] for item in window_items],
            "exact_same_name_tags": [item["exact_same_name_tags"] for item in window_items],
            "camera_serials": cameras, "repeat_intent": intent,
        }
    metrics = {
        "paired_geolocated_targets": len(details), "paired_windows": 2 * len(details),
        "complete_actions": len(total_actions), "exposures": total_exposures, "products": total_products,
        "archive_size_bytes": total_bytes, "shared_camera_serials": sorted({serial for item in details.values() for serial in item["camera_serials"]}),
        "exact_same_name_tagged_exposures": total_tags, "exact_same_name_tag_share": total_tags / total_exposures,
        "all_pairs_disjoint": all_disjoint, "all_pairs_same_camera": all_same_camera,
        "explicit_repeat_observation_targets": explicit_repeats,
    }
    selected_ok = details.get("Glushko Crater", {}).get("repeat_intent") == "explicit_photometric_viewing_condition_repeat"
    return metrics, details, selected_ok


def verify_stage11b(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11b.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    prior = verify_stage11a(root) if prior is None else prior
    add_check(checks, errors, "replication_census_replays", prior["pass"], error="Stage 11A no longer verifies.")
    source = spec["source_contract"]
    plan = json.loads((root / source["plan_path"]).read_text(encoding="utf-8"))
    with (root / source["membership_ledger_path"]).open(newline="", encoding="utf-8") as handle:
        ledger = list(csv.DictReader(handle))
    with (root / source["relationship_manifest_path"]).open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))
    metrics, pairs, selected_ok = derive(plan, ledger, manifest)
    pair_ok = exact_mapping(metrics, spec["frozen_observables"]) and pairs == spec["frozen_pairs"] and selected_ok
    add_check(checks, errors, "paired_window_task_admission", pair_ok,
              error="The frozen paired-window candidate structure or explicit Glushko repeat intent changed.",
              metrics=metrics, pairs=pairs)
    state = spec["mutation_state"]
    boundary_ok = not any((state["plan_membership_is_image_content"], state["same_name_is_scene_equivalence"],
        state["same_camera_is_calibrated_photometry"], state["windows_are_independent_events"],
        state["sparse_tags_are_negative_evidence"], state["model_partition_assigned"],
        state["performance_effect_inferred"], state["scientific_result_claimed"], state["novelty_or_priority"])) and state["pixel_payload_bytes"] == 0
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited content, equivalence, calibration, independence, tag, model, science, novelty, or pixel claim was admitted.", mutation_state=state)
    evidence_state = "VERIFIED_PAIRED_WINDOW_TASK_CANDIDATE" if pair_ok else "PAIRED_WINDOW_ADMISSION_UNRESOLVED"
    return {"testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
            "evidence_state": evidence_state if not errors else "REJECTED", "cohort": metrics, "pairs": pairs,
            "selected_candidate": spec["selected_candidate"],
            "verified": "Three geolocated lunar targets have two disjoint active plan windows on the same camera serial. Glushko is the strongest positive task candidate because the plan explicitly defines first and second photometric observations intended to inform how changing viewing conditions affect perceived brightness, color, and texture.",
            "decision_use": "Admit a pixel-blind registration and protocol gate for Glushko, not a model run. Plan membership and same camera make the comparison plausible; sparse exact tags and absent pixel registration prevent an image-content or evaluation claim.",
            "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
            "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors}


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage11a(root)
    baseline = verify_stage11b(root, prior=prior)
    names = load_json(root / "spec/stage11b.json")["hard_negatives"]
    mutations = {name: verify_stage11b(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11B hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["cohort"]
    lines = ["# Stage 11B — Paired-Window Task Admission", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`", f"- Evidence state: `{result['evidence_state']}`",
        f"- Targets / windows / actions / exposures: `{item['paired_geolocated_targets']}` / `{item['paired_windows']}` / `{item['complete_actions']}` / `{item['exposures']}`",
        f"- Products / footprint: `{item['products']:,}` / `{item['archive_size_bytes'] / 1_000_000_000:.9f} GB`",
        f"- Exact same-name tag coverage: `{item['exact_same_name_tagged_exposures']}` / `{item['exposures']}` (`{item['exact_same_name_tag_share']:.3%}`)",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`", "", "## Verified", "", result["verified"],
        "", "## Decision use", "", result["decision_use"], "", "## Pair details", ""]
    for name, pair in result["pairs"].items():
        lines.append(f"- `{name}`: orders `{pair['orders'][0]}` / `{pair['orders'][1]}`, gap `{pair['window_gap_seconds'] / 60:.1f}` min, actions `{pair['actions'][0]}` / `{pair['actions'][1]}`, intent `{pair['repeat_intent']}`")
    lines.extend(["", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", ""])
    for name, mutation_result in result.get("hard_negatives", {}).items():
        lines.append(f"- `{name}`: {'REJECTED' if not mutation_result['pass'] else 'UNEXPECTEDLY ACCEPTED'}")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1]); parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path); parser.add_argument("--mutation"); args = parser.parse_args(argv)
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11b(args.root.resolve(), args.mutation)
    if args.json_output: write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True); args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2)); return 0 if result["pass"] else 1


if __name__ == "__main__": sys.exit(main())
