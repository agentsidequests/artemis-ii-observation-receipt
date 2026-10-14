#!/usr/bin/env python3
"""Verify Stage 10U's camera-target shortcut canary."""

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
from stage10t_task_conditioned_unit_ladder import verify_stage10t


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "target_labels_ground_truth": False,
        "camera_causes_target": False,
        "camera_identity_sufficient": False,
        "diagnostic_rule_kind": "document_nominated_descriptive_rule",
        "pixels_encode_camera": False,
        "image_model_uses_shortcut": False,
        "result_kind": "metadata_association_canary",
        "performance_effect_inferred": False,
        "scope": "verified_complete_action_labeled_exposures",
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_target_labels_ground_truth": ("target_labels_ground_truth", True),
        "claim_camera_causes_target": ("camera_causes_target", True),
        "claim_camera_identity_sufficient": ("camera_identity_sufficient", True),
        "call_diagnostic_rule_held_out_model": ("diagnostic_rule_kind", "held_out_pixel_model"),
        "infer_pixels_encode_camera": ("pixels_encode_camera", True),
        "claim_image_model_uses_shortcut": ("image_model_uses_shortcut", True),
        "call_association_observed_leakage": ("result_kind", "observed_leakage"),
        "infer_model_performance_effect": ("performance_effect_inferred", True),
        "generalize_association_beyond_cohort": ("scope", "all_archive_and_future_missions"),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_camera_target_canary": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def association_metrics(rows: list[dict[str, str]], z9: str, sunset: str) -> dict[str, Any]:
    source_rows = [row for row in rows if row["collection_id"] == "data_source"]
    labeled = [row for row in source_rows if row["target_id"]]
    by_target: dict[str, Counter[str]] = defaultdict(Counter)
    for row in labeled:
        by_target[row["target_id"]][row["camera_serial"]] += 1
    exclusive = {target: counts for target, counts in by_target.items() if len(counts) == 1}

    tp = sum(row["camera_serial"] == z9 and row["target_id"] == sunset for row in labeled)
    tn = sum(row["camera_serial"] != z9 and row["target_id"] != sunset for row in labeled)
    fp = sum(row["camera_serial"] == z9 and row["target_id"] != sunset for row in labeled)
    fn = sum(row["camera_serial"] != z9 and row["target_id"] == sunset for row in labeled)
    total = len(labeled)
    positives = tp + fn
    negatives = tn + fp

    cameras = sorted({row["camera_serial"] for row in labeled})
    targets = sorted(by_target)
    cells = Counter((row["camera_serial"], row["target_id"]) for row in labeled)
    camera_counts = Counter(row["camera_serial"] for row in labeled)
    target_counts = Counter(row["target_id"] for row in labeled)
    chi_square = sum(
        (cells[camera, target] - camera_counts[camera] * target_counts[target] / total) ** 2
        / (camera_counts[camera] * target_counts[target] / total)
        for camera in cameras for target in targets
    )
    cramers_v = math.sqrt(chi_square / (total * min(len(cameras) - 1, len(targets) - 1)))
    mutual_information = sum(
        (count / total) * math.log2((count * total) / (camera_counts[camera] * target_counts[target]))
        for (camera, target), count in cells.items()
    )
    return {
        "source_exposures": len(source_rows),
        "labeled_exposures": total,
        "target_classes": len(targets),
        "camera_serials": len(cameras),
        "camera_exclusive_target_classes": len(exclusive),
        "camera_exclusive_labeled_exposures": sum(sum(counts.values()) for counts in exclusive.values()),
        "camera_exclusive_exposure_share": sum(sum(counts.values()) for counts in exclusive.values()) / total,
        "sunset_exposures": positives,
        "non_sunset_exposures": negatives,
        "z9_labeled_exposures": camera_counts[z9],
        "z9_sunset_exposures": tp,
        "rule_true_positive": tp,
        "rule_true_negative": tn,
        "rule_false_positive": fp,
        "rule_false_negative": fn,
        "rule_accuracy": (tp + tn) / total,
        "majority_accuracy": max(positives, negatives) / total,
        "rule_accuracy_lift": (tp + tn) / total - max(positives, negatives) / total,
        "rule_balanced_accuracy": (tp / positives + tn / negatives) / 2,
        "rule_precision": tp / (tp + fp),
        "rule_sensitivity": tp / positives,
        "rule_specificity": tn / negatives,
        "cramers_v": cramers_v,
        "mutual_information_bits": mutual_information,
    }


def verify_stage10u(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10u.json"), mutation)
    expected = spec["frozen_observables"]
    source = spec["source_contract"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior = verify_stage10t(root)
    add_check(checks, errors, "task_conditioned_unit_receipt", prior["pass"],
              error="Stage 10T no longer verifies.")

    guide = (root / source["data_user_guide_path"]).read_text(encoding="utf-8")
    document_nomination_ok = (
        "primary camera used during the eclipse observations" in guide
        and "multiple images over a single target area" in guide
        and "not thoroughly verified post-mission and may contain errors" in guide
    )
    add_check(checks, errors, "independent_document_nomination_and_label_limit", document_nomination_ok,
              error="The Z9 eclipse-role nomination or target-label limit changed in the Data User Guide.")

    with (root / source["manifest_path"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    derived = association_metrics(rows, source["z9_camera_serial"], source["sunset_label"])
    exact_keys = [key for key, value in expected.items() if not isinstance(value, float)]
    float_keys = [key for key, value in expected.items() if isinstance(value, float)]
    metrics_ok = (
        all(derived[key] == expected[key] for key in exact_keys)
        and all(close(float(derived[key]), expected[key]) for key in float_keys)
    )
    add_check(checks, errors, "camera_target_association", metrics_ok,
              error="The camera-target contingency or diagnostic rule metrics changed.", derived=derived)

    countercase_ok = (
        derived["z9_sunset_exposures"] < derived["sunset_exposures"]
        and derived["z9_labeled_exposures"] > derived["z9_sunset_exposures"]
        and derived["rule_sensitivity"] < 0.5
    )
    add_check(checks, errors, "camera_not_necessary_or_sufficient", countercase_ok,
              error="The countercase against camera sufficiency changed.")

    state = spec["mutation_state"]
    boundary_ok = (
        not state["target_labels_ground_truth"]
        and not state["camera_causes_target"]
        and not state["camera_identity_sufficient"]
        and state["diagnostic_rule_kind"] == "document_nominated_descriptive_rule"
        and not state["pixels_encode_camera"]
        and not state["image_model_uses_shortcut"]
        and state["result_kind"] == "metadata_association_canary"
        and not state["performance_effect_inferred"]
        and state["scope"] == "verified_complete_action_labeled_exposures"
        and not state["scientific_discovery_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited correctness, causal, sufficiency, model, leakage, performance, scope, discovery, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_CAMERA_TARGET_ASSOCIATION_CANARY" if document_nomination_ok and metrics_ok and countercase_ok else "CAMERA_TARGET_ASSOCIATION_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "association": derived,
        "verified": "Among 3,413 source exposures with nonblank target labels in the verified complete-action cohort, 19 of 23 target classes occur on one camera only and account for 807 exposures. The Data User Guide independently identifies the Z9 as the primary eclipse camera; 593 of its 734 labeled exposures carry Sunset. The descriptive rule 'predict Sunset iff Z9' scores 67.741% accuracy against a 54.498% majority baseline, but only 38.184% sensitivity.",
        "decision_use": "Treat camera identity as a prospective shortcut variable for any later target classifier. Require a camera-only baseline and camera/event-stratified evaluation before interpreting pixel performance. The metadata association does not prove that pixels reveal camera identity or that a model would exploit it.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10u(root)
    names = load_json(root / "spec/stage10u.json")["hard_negatives"]
    mutations = {name: verify_stage10u(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10U hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["association"]
    lines = [
        "# Stage 10U — Camera-Target Shortcut Canary", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Labeled source exposures / target classes / cameras: `{item['labeled_exposures']:,}` / `{item['target_classes']}` / `{item['camera_serials']}`",
        f"- Camera-exclusive target classes / exposures: `{item['camera_exclusive_target_classes']}` / `{item['camera_exclusive_labeled_exposures']:,}` (`{item['camera_exclusive_exposure_share']:.3%}`)",
        f"- Z9 labeled exposures carrying Sunset: `{item['z9_sunset_exposures']:,}` / `{item['z9_labeled_exposures']:,}` (`{item['rule_precision']:.3%}`)",
        f"- Camera-only rule accuracy / majority baseline / lift: `{item['rule_accuracy']:.3%}` / `{item['majority_accuracy']:.3%}` / `{item['rule_accuracy_lift']:.3%}`",
        f"- Rule balanced accuracy / sensitivity / specificity: `{item['rule_balanced_accuracy']:.3%}` / `{item['rule_sensitivity']:.3%}` / `{item['rule_specificity']:.3%}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified", "", result["verified"], "", "## Decision use", "", result["decision_use"],
        "", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", "",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10u(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
