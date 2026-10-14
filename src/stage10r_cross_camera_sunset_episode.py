#!/usr/bin/env python3
"""Verify Stage 10R's cross-camera, cross-facet Sunset episode canary."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json, parse_utc
from stage10p_capture_run_concentration import summarize_clusters, verify_stage10p
from stage10q_sunset_transcript_alignment import verify_stage10q


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "episode_kind": "time_bounded_cross_camera_observation_episode",
        "visual_redundancy_established": False,
        "activity_labels_incorrect": False,
        "speaker_camera_attribution": False,
        "result_kind": "structural_dependence_hazard",
        "scope": "one_verified_cohort_episode",
        "performance_effect_inferred": False,
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_episode_a_semantic_scene": ("episode_kind", "semantic_scene"),
        "call_images_duplicates_or_visually_redundant": ("visual_redundancy_established", True),
        "call_activity_labels_incorrect": ("activity_labels_incorrect", True),
        "attribute_cameras_to_named_speakers": ("speaker_camera_attribution", True),
        "call_cross_camera_relation_observed_leakage": ("result_kind", "observed_leakage"),
        "generalize_episode_to_archive": ("scope", "all_archive_products"),
        "infer_model_performance_effect": ("performance_effect_inferred", True),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_cross_camera_canary": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-9)


def verify_stage10r(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10r.json"), mutation)
    expected = spec["frozen_observables"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    stage10p = verify_stage10p(root)
    stage10q = verify_stage10q(root)
    prior_ok = stage10p["pass"] and stage10q["pass"]
    add_check(checks, errors, "prior_episode_receipts", prior_ok,
              error="The Stage 10P or 10Q episode receipt no longer verifies.")

    source = spec["source_contract"]
    all_clusters = summarize_clusters(root / source["manifest_path"])
    clusters = {item["cluster_id"]: item for item in all_clusters}
    primary = clusters.get(expected["primary_cluster_id"], {})
    primary_start = parse_utc(primary["start_utc"]) if primary else None
    primary_end = parse_utc(primary["end_utc"]) if primary else None
    overlapping = [
        item for item in all_clusters
        if primary_start is not None and primary_end is not None
        and parse_utc(item["start_utc"]) <= primary_end
        and parse_utc(item["end_utc"]) >= primary_start
    ]
    secondary = sorted(
        [item for item in overlapping if item["cluster_id"] != expected["primary_cluster_id"]],
        key=lambda item: item["start_utc"],
    )

    with (root / source["transcript_path"]).open(newline="", encoding="utf-8-sig") as handle:
        transcript = list(csv.DictReader(handle))
    secondary_utterances = sum(1 for row in transcript if any(
        parse_utc(item["start_utc"]) <= parse_utc(row["utc"]) <= parse_utc(item["end_utc"])
        for item in secondary
    ))
    secondary_products = sum(item["products"] for item in secondary)
    secondary_captures = sum(item["capture_identities"] for item in secondary)
    secondary_actions = sum(item["complete_actions"] for item in secondary)
    secondary_bytes = sum(item["archive_size_bytes"] for item in secondary)
    stage10o = load_json(root / source["stage10o_spec_path"])["frozen_observables"]
    derived = {
        "primary_cluster_id": primary.get("cluster_id"),
        "secondary_cluster_ids": [item["cluster_id"] for item in secondary],
        "secondary_cluster_count": len(secondary),
        "primary_camera": primary.get("camera_serials", [None])[0],
        "secondary_camera": sorted({camera for item in secondary for camera in item["camera_serials"]})[0] if secondary else None,
        "primary_activity": primary.get("activity_ids", [None])[0],
        "secondary_activity_ids": sorted({activity for item in secondary for activity in item["activity_ids"]}),
        "shared_target": primary.get("target_ids", [None])[0] if all(item.get("target_ids") == primary.get("target_ids") for item in secondary) else None,
        "secondary_products": secondary_products,
        "secondary_capture_identities": secondary_captures,
        "secondary_complete_actions": secondary_actions,
        "secondary_archive_size_bytes": secondary_bytes,
        "secondary_transcript_utterances": secondary_utterances,
        "combined_products": primary.get("products", 0) + secondary_products,
        "combined_capture_identities": primary.get("capture_identities", 0) + secondary_captures,
        "combined_complete_actions": primary.get("complete_actions", 0) + secondary_actions,
        "combined_archive_size_bytes": primary.get("archive_size_bytes", 0) + secondary_bytes,
        "cohort_product_share": (primary.get("products", 0) + secondary_products) / stage10o["products"],
        "cohort_capture_share": (primary.get("capture_identities", 0) + secondary_captures) / stage10o["capture_identities"],
        "cohort_action_share": (primary.get("complete_actions", 0) + secondary_actions) / stage10o["complete_actions"],
        "cohort_byte_share": (primary.get("archive_size_bytes", 0) + secondary_bytes) / stage10o["expected_total_bytes"],
        "distinct_cameras": len({camera for item in overlapping for camera in item["camera_serials"]}),
        "distinct_activity_ids": len({activity for item in overlapping for activity in item["activity_ids"]}),
    }
    nested_ok = bool(primary and secondary and all(
        primary_start <= parse_utc(item["start_utc"]) <= parse_utc(item["end_utc"]) <= primary_end
        for item in secondary
    ))
    exact_keys = [key for key, value in expected.items() if not isinstance(value, float)]
    float_keys = [key for key, value in expected.items() if isinstance(value, float)]
    episode_ok = nested_ok and all(derived[key] == expected[key] for key in exact_keys) and all(
        close(float(derived[key]), expected[key]) for key in float_keys
    )
    add_check(checks, errors, "cross_camera_cross_facet_episode", episode_ok,
              error="The nested cross-camera episode or combined observables changed.", derived=derived, nested=nested_ok)

    state = spec["mutation_state"]
    boundary_ok = (
        state["episode_kind"] == "time_bounded_cross_camera_observation_episode"
        and not state["visual_redundancy_established"]
        and not state["activity_labels_incorrect"]
        and not state["speaker_camera_attribution"]
        and state["result_kind"] == "structural_dependence_hazard"
        and state["scope"] == "one_verified_cohort_episode"
        and not state["performance_effect_inferred"]
        and not state["scientific_discovery_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited scene, visual, label, attribution, leakage, scope, performance, discovery, priority, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_CROSS_CAMERA_CROSS_FACET_OBSERVATION_EPISODE" if prior_ok and episode_ok else "CROSS_CAMERA_EPISODE_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "episode": derived,
        "verified": "The transcript-aligned Sunset episode contains four overlapping same-camera capture runs from two cameras and two activity facets. Together they produce 2,010 products representing 670 exposures and 134 actions, totaling 177.543697399 GB—8.809% of products and exposures, 6.187% of actions, and 10.924% of bytes in the verified complete-action cohort; 24 transcript utterances fall inside the three nested second-camera runs.",
        "decision_use": "Use this as the concrete reason that file, exposure, action, camera, activity facet, and observation episode are different possible evaluation units. The task's dependence oracle must choose among them.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10r(root)
    names = load_json(root / "spec/stage10r.json")["hard_negatives"]
    mutations = {name: verify_stage10r(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10R hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["episode"]
    lines = [
        "# Stage 10R — Cross-Camera Sunset Observation Episode", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Combined products / captures / actions: `{item['combined_products']:,}` / `{item['combined_capture_identities']:,}` / `{item['combined_complete_actions']:,}`",
        f"- Combined archive footprint: `{item['combined_archive_size_bytes'] / 1_000_000_000:.9f} GB`",
        f"- Cohort product / action / byte share: `{item['cohort_product_share']:.3%}` / `{item['cohort_action_share']:.3%}` / `{item['cohort_byte_share']:.3%}`",
        f"- Cameras / activity facets: `{item['distinct_cameras']}` / `{item['distinct_activity_ids']}`",
        f"- Transcript utterances inside second-camera interval: `{item['secondary_transcript_utterances']}`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10r(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
