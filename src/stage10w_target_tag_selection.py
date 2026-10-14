#!/usr/bin/env python3
"""Verify Stage 10W's target-tag selection canary."""

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
from stage10u_camera_target_shortcut import verify_stage10u


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "blank_tags_are_negative_examples": False,
        "target_tags_ground_truth": False,
        "missingness_kind": "observably_nonuniform_mechanism_unresolved",
        "labeler_intent_inferred": False,
        "targets_imputed_from_activity": False,
        "activity_lookup_kind": "in_sample_descriptive_diagnostic",
        "stage10u_mechanism": "acquisition_and_curation_not_separated",
        "scope": "verified_complete_action_cohort",
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_blank_tags_negative_examples": ("blank_tags_are_negative_examples", True),
        "call_target_tags_ground_truth": ("target_tags_ground_truth", True),
        "call_missingness_random": ("missingness_kind", "random"),
        "infer_labeler_intent": ("labeler_intent_inferred", True),
        "impute_targets_from_activity": ("targets_imputed_from_activity", True),
        "call_activity_lookup_held_out_model": ("activity_lookup_kind", "held_out_predictive_model"),
        "attribute_stage10u_association_only_to_acquisition": ("stage10u_mechanism", "acquisition_only"),
        "generalize_tagged_class_prevalence_to_archive": ("scope", "all_archive_and_blank_exposures"),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_tag_selection_canary": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def contingency(rows: list[dict[str, str]], key: str) -> tuple[float, float]:
    state = lambda row: bool(row["target_id"])
    cells = Counter((row[key], state(row)) for row in rows)
    groups = Counter(row[key] for row in rows)
    outcomes = Counter(state(row) for row in rows)
    total = len(rows)
    chi_square = sum(
        (cells[(group, outcome)] - groups[group] * outcomes[outcome] / total) ** 2
        / (groups[group] * outcomes[outcome] / total)
        for group in groups for outcome in outcomes
    )
    cramers_v = math.sqrt(chi_square / (total * min(len(groups) - 1, len(outcomes) - 1)))
    mutual_information = sum(
        (count / total) * math.log2((count * total) / (groups[group] * outcomes[outcome]))
        for (group, outcome), count in cells.items()
    )
    return cramers_v, mutual_information


def derive(rows: list[dict[str, str]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = [row for row in rows if row["collection_id"] == "data_source"]
    tagged = [row for row in source if row["target_id"]]
    activity = Counter(row["activity_id"] for row in source)
    activity_tagged = Counter(row["activity_id"] for row in tagged)
    camera = Counter(row["camera_serial"] for row in source)
    camera_tagged = Counter(row["camera_serial"] for row in tagged)
    zero = [name for name in activity if activity_tagged[name] == 0]
    full = [name for name in activity if activity_tagged[name] == activity[name]]
    partial = [name for name in activity if 0 < activity_tagged[name] < activity[name]]
    activity_v, activity_mi = contingency(source, "activity_id")
    camera_v, camera_mi = contingency(source, "camera_serial")
    lookup_correct = sum(max(activity_tagged[name], activity[name] - activity_tagged[name]) for name in activity)
    majority_accuracy = max(len(tagged), len(source) - len(tagged)) / len(source)
    metrics = {
        "source_exposures": len(source), "target_tag_present": len(tagged),
        "target_tag_blank": len(source) - len(tagged), "target_tag_coverage": len(tagged) / len(source),
        "activity_values": len(activity), "zero_coverage_activities": len(zero),
        "zero_coverage_exposures": sum(activity[name] for name in zero),
        "full_coverage_activities": len(full), "full_coverage_exposures": sum(activity[name] for name in full),
        "partial_coverage_activities": len(partial), "partial_coverage_exposures": sum(activity[name] for name in partial),
        "activity_tag_presence_cramers_v": activity_v,
        "activity_tag_presence_mutual_information_bits": activity_mi,
        "activity_majority_lookup_correct": lookup_correct,
        "activity_majority_lookup_accuracy": lookup_correct / len(source),
        "global_majority_state_accuracy": majority_accuracy,
        "activity_lookup_accuracy_lift": lookup_correct / len(source) - majority_accuracy,
        "camera_tag_presence_cramers_v": camera_v,
        "camera_tag_presence_mutual_information_bits": camera_mi,
        "sunset_tagged_exposures": sum(row["target_id"] == "Sunset" for row in tagged),
        "sunset_share_of_tagged_exposures": sum(row["target_id"] == "Sunset" for row in tagged) / len(tagged),
    }
    examples = {name: {"exposures": activity[name], "tagged": activity_tagged[name]}
                for name in ("24_Sunset", "12_Orientale Basin (2/2)", "07_Whole Moon", "h_Observation Break")}
    cameras = {name: {"exposures": camera[name], "tagged": camera_tagged[name],
                      "coverage": camera_tagged[name] / camera[name]} for name in sorted(camera)}
    return metrics, examples, cameras


def exact_mapping(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    return all(
        close(float(actual[key]), float(value)) if isinstance(value, float) else actual[key] == value
        for key, value in expected.items()
    )


def verify_stage10w(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10w.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior = verify_stage10u(root)
    add_check(checks, errors, "camera_target_canary_replays", prior["pass"],
              error="Stage 10U no longer verifies.")

    with (root / spec["source_contract"]["manifest_path"]).open(newline="", encoding="utf-8") as handle:
        metrics, examples, cameras = derive(list(csv.DictReader(handle)))
    coverage_ok = exact_mapping(metrics, spec["frozen_observables"])
    examples_ok = examples == spec["frozen_examples"]
    cameras_ok = all(exact_mapping(cameras[name], expected) for name, expected in spec["camera_coverage"].items())
    add_check(checks, errors, "nonuniform_target_tag_coverage", coverage_ok and examples_ok and cameras_ok,
              error="The frozen target-tag coverage structure changed.", metrics=metrics,
              examples=examples, cameras=cameras)

    guide = (root / spec["source_contract"]["data_user_guide_path"]).read_text(encoding="utf-8")
    compact = "".join(guide.casefold().split())
    guide_ok = (
        "targetsweredeterminedbythelunarscienceteamduringthemissionthroughvisualinspectionandmanualtagging" in compact
        and "usinglunartargetingplantargetnamesforonlyasubsetofimages" in compact
        and "notthoroughlyverifiedpost-missionandmaycontainerrors" in compact
    )
    add_check(checks, errors, "data_user_guide_manual_subset_limit", guide_ok,
              error="The Data User Guide's manual-subset or verification limit changed.")

    state = spec["mutation_state"]
    boundary_ok = (
        not state["blank_tags_are_negative_examples"]
        and not state["target_tags_ground_truth"]
        and state["missingness_kind"] == "observably_nonuniform_mechanism_unresolved"
        and not state["labeler_intent_inferred"]
        and not state["targets_imputed_from_activity"]
        and state["activity_lookup_kind"] == "in_sample_descriptive_diagnostic"
        and state["stage10u_mechanism"] == "acquisition_and_curation_not_separated"
        and state["scope"] == "verified_complete_action_cohort"
        and not state["scientific_discovery_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited blank-label, ground-truth, missingness, intent, imputation, model, mechanism, scope, discovery, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_NONUNIFORM_TARGET_TAG_COVERAGE" if coverage_ok and examples_ok and cameras_ok and guide_ok else "TARGET_TAG_SELECTION_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "coverage": metrics,
        "activity_examples": examples, "camera_coverage": cameras,
        "verified": "Target tags are present for 3,413 of 7,606 source exposures (44.872%). Across 45 activity values, 17 have zero tag coverage, eight have complete coverage, and 20 are partial; an in-sample activity-majority lookup classifies tag presence at 87.484% versus a 55.128% global-majority baseline.",
        "decision_use": "Treat target tags as curated navigation metadata unless a task-specific audit establishes a label population. Before supervised target modeling, measure and control label presence itself; do not convert blank tags into negative labels or interpret the Stage 10U association as acquisition-only.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10w(root)
    names = load_json(root / "spec/stage10w.json")["hard_negatives"]
    mutations = {name: verify_stage10w(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10W hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["coverage"]
    lines = [
        "# Stage 10W — Target-Tag Selection Canary", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Tagged / blank / total source exposures: `{item['target_tag_present']:,}` / `{item['target_tag_blank']:,}` / `{item['source_exposures']:,}`",
        f"- Target-tag coverage: `{item['target_tag_coverage']:.3%}`",
        f"- Zero / complete / partial activity values: `{item['zero_coverage_activities']}` / `{item['full_coverage_activities']}` / `{item['partial_coverage_activities']}`",
        f"- Activity association Cramér's V: `{item['activity_tag_presence_cramers_v']:.6f}`",
        f"- Activity-majority lookup / global majority: `{item['activity_majority_lookup_accuracy']:.3%}` / `{item['global_majority_state_accuracy']:.3%}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified", "", result["verified"], "", "## Decision use", "", result["decision_use"],
        "", "## Activity examples", "",
    ]
    for name, values in result["activity_examples"].items():
        lines.append(f"- `{name}`: `{values['tagged']:,}` / `{values['exposures']:,}` tagged")
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10w(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
