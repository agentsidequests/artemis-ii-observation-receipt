#!/usr/bin/env python3
"""Verify Stage 10P's largest conditional capture-run concentration canary."""

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

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_json, parse_utc


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "cluster_kind": "conditional_temporal_adjacency",
        "labels_correct": False,
        "cluster_independent_sample": False,
        "result_kind": "expected_crossing_hazard",
        "scope": "largest_five_second_cluster_in_verified_cohort",
        "performance_effect_inferred": False,
        "global_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    mapping = {
        "call_cluster_a_semantic_scene": ("cluster_kind", "semantic_scene"),
        "call_activity_or_target_labels_correct": ("labels_correct", True),
        "call_cluster_an_independent_sample": ("cluster_independent_sample", True),
        "call_expected_crossing_observed_leakage": ("result_kind", "observed_leakage"),
        "generalize_largest_cluster_to_archive": ("scope", "all_archive_products"),
        "infer_model_performance_effect": ("performance_effect_inferred", True),
        "claim_global_priority": ("global_priority", True),
        "open_pixels_for_concentration_canary": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    state[key] = value
    return mutated


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def summarize_clusters(manifest_path: Path) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[row["temporal_cluster_5s"]].append(row)
    summaries: list[dict[str, Any]] = []
    for cluster_id, rows in grouped.items():
        action_ids = {row["action_id"] for row in rows}
        capture_ids = {row["capture_identity"] for row in rows}
        start = min(row["action_start_utc"] for row in rows)
        end = max(row["action_end_utc"] for row in rows)
        actions = len(action_ids)
        summaries.append({
            "cluster_id": cluster_id,
            "products": len(rows),
            "capture_identities": len(capture_ids),
            "complete_actions": actions,
            "archive_size_bytes": sum(int(row["archive_size_bytes"]) for row in rows),
            "start_utc": start,
            "end_utc": end,
            "span_seconds": (parse_utc(end) - parse_utc(start)).total_seconds(),
            "camera_serials": sorted({row["camera_serial"] for row in rows}),
            "activity_ids": sorted({row["activity_id"] for row in rows if row["activity_id"]}),
            "target_ids": sorted({row["target_id"] for row in rows if row["target_id"]}),
            "products_per_action": len(rows) / actions,
            "action_product_rows": dict(Counter(row["exposures_in_action"] for row in rows)),
            "expected_action_split_cross_probability_80_20": 1.0 - 0.8 ** actions - 0.2 ** actions,
        })
    return sorted(summaries, key=lambda item: (-item["complete_actions"], -item["products"], item["cluster_id"]))


def verify_stage10p(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10p.json"), mutation)
    expected = spec["frozen_observables"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    stage10o_spec = load_json(root / spec["source_contract"]["stage10o_spec_path"])
    manifest_path = root / spec["source_contract"]["manifest_path"]
    identity_ok = (
        manifest_path.is_file()
        and manifest_path.stat().st_size == stage10o_spec["frozen_observables"]["manifest_bytes"]
        and sha256_file(manifest_path) == stage10o_spec["frozen_observables"]["manifest_sha256"]
    )
    add_check(checks, errors, "stage10o_manifest_identity", identity_ok,
              error="The Stage 10O manifest identity changed.")

    summaries = summarize_clusters(manifest_path) if identity_ok else []
    largest = summaries[0] if summaries else {}
    cohort_products = stage10o_spec["frozen_observables"]["products"]
    cohort_bytes = stage10o_spec["frozen_observables"]["expected_total_bytes"]
    cohort_actions = stage10o_spec["frozen_observables"]["complete_actions"]
    derived = {
        **largest,
        "largest_cluster_id": largest.get("cluster_id"),
        "cohort_product_share": largest.get("products", 0) / cohort_products,
        "cohort_byte_share": largest.get("archive_size_bytes", 0) / cohort_bytes,
        "top_five_actions": sum(item["complete_actions"] for item in summaries[:5]),
        "top_five_products": sum(item["products"] for item in summaries[:5]),
        "top_five_action_share": sum(item["complete_actions"] for item in summaries[:5]) / cohort_actions,
        "top_five_product_share": sum(item["products"] for item in summaries[:5]) / cohort_products,
    } if summaries else {}
    exact_keys = [key for key, value in expected.items() if not isinstance(value, float)]
    float_keys = [key for key, value in expected.items() if isinstance(value, float)]
    concentration_ok = (
        all(derived.get(key) == expected[key] for key in exact_keys)
        and all(close(float(derived.get(key, float("nan"))), expected[key]) for key in float_keys)
    )
    add_check(checks, errors, "largest_five_second_cluster", concentration_ok,
              error="The largest five-second cluster or its concentration metrics changed.", derived=derived)

    state = spec["mutation_state"]
    boundary_ok = (
        state["cluster_kind"] == "conditional_temporal_adjacency"
        and not state["labels_correct"]
        and not state["cluster_independent_sample"]
        and state["result_kind"] == "expected_crossing_hazard"
        and state["scope"] == "largest_five_second_cluster_in_verified_cohort"
        and not state["performance_effect_inferred"]
        and not state["global_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited scene, correctness, independence, observation, scope, performance, novelty, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_FIVE_SECOND_CAPTURE_RUN_CONCENTRATION" if identity_ok and concentration_ok else "CAPTURE_RUN_CONCENTRATION_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "largest_cluster": derived,
        "verified": "The largest conditional five-second same-camera cluster contains 1,230 downloadable products representing 410 exposures and 82 complete five-exposure actions over 143.61 seconds. Its products total 75.056509295 GB. Every admitted row carries camera serial 3500015, activity 24_Sunset, and target Sunset.",
        "decision_use": "Use this as the concrete microcase for why a flat file split can divide one structured capture run across evaluation partitions. The metadata establishes concentration and label concordance, not semantic scene identity or actual leakage.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10p(root)
    names = load_json(root / "spec/stage10p.json")["hard_negatives"]
    mutations = {name: verify_stage10p(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10P hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["largest_cluster"]
    lines = [
        "# Stage 10P — Five-Second Capture-Run Concentration", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Products / captures / actions: `{item['products']:,}` / `{item['capture_identities']:,}` / `{item['complete_actions']:,}`",
        f"- Time span: `{item['span_seconds']:.2f} seconds`",
        f"- Archive footprint: `{item['archive_size_bytes'] / 1_000_000_000:.9f} GB`",
        f"- Cohort product / byte share: `{item['cohort_product_share']:.3%}` / `{item['cohort_byte_share']:.3%}`",
        f"- Hypothetical independent 80/20 action-split crossing probability: `{item['expected_action_split_cross_probability_80_20']:.9%}`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10p(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
