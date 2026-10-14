#!/usr/bin/env python3
"""Verify Stage 10G's representation/action retrieval-distortion audit."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_json


INTERNAL_ID = "msn:Mission_Information/msn:internal_id"
ACTIVITY_ID = "msn_surface:Observational_Intent/msn_surface:activity_id"
TARGET_ID = "msn_surface:Observational_Intent/msn_surface:target_id"
DISCUSSION = "15_Discussion #4: Terminator"
CREW_CHOICE = "14_Crew Choice #2"


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "products_declared_independent_observations": False,
        "representations_declared_evidence_multiplier": False,
        "exposures_declared_all_archive_anomalies": False,
        "target_correctness_inferred": False,
        "discussion_facet_declared_action_complete": False,
        "representations_declared_waste": False,
        "scope": "verified_fractured_raw_brackets",
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "count_207_products_as_independent_observations":
        state["products_declared_independent_observations"] = True
    elif mutation == "claim_three_representations_triple_scientific_evidence":
        state["representations_declared_evidence_multiplier"] = True
    elif mutation == "claim_69_exposures_are_all_archive_anomalies":
        state["exposures_declared_all_archive_anomalies"] = True
    elif mutation == "infer_target_correctness_from_partition_coupling":
        state["target_correctness_inferred"] = True
    elif mutation == "declare_discussion_facet_action_complete":
        state["discussion_facet_declared_action_complete"] = True
    elif mutation == "call_representations_wasteful_duplicates":
        state["representations_declared_waste"] = True
    elif mutation == "generalize_bracket_result_to_every_product_class":
        state["scope"] = "every_archive_product_class"
    elif mutation == "open_pixels_to_normalize_archive_units":
        mutated["source_contract"]["pixel_payload_bytes"] = 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def scalar(source: dict[str, Any], key: str) -> str | None:
    value = source.get("pds4_label", {}).get(key)
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value) if value is not None else None


def verify_receipt(root: Path, receipt: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for record in receipt.get("sources", []):
        path = root / record["path"]
        if not path.is_file():
            failures.append(f"missing:{record['path']}")
            continue
        if path.stat().st_size != record["bytes"]:
            failures.append(f"bytes:{record['path']}")
        if sha256_file(path) != record["sha256"]:
            failures.append(f"sha256:{record['path']}")
    return failures


def partitions_equivalent(activities: list[str | None], targets: list[str | None]) -> bool:
    return all(
        (activities[left] == activities[right]) == (targets[left] == targets[right])
        for left in range(len(activities))
        for right in range(len(activities))
    )


def verify_stage10g(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10g.json"), mutation)
    contract = spec["source_contract"]
    expected = spec["frozen_observables"]
    receipt = load_json(root / contract["receipt_path"])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    receipt_failures = verify_receipt(root, receipt)
    add_check(
        checks,
        errors,
        "source_identity",
        receipt.get("status") == "COMPLETED" and not receipt_failures,
        error="A Stage 10G source byte or receipt identity changed.",
        failures=receipt_failures,
    )

    stage10e = load_json(root / contract["stage10e_result_path"])
    stage10f = load_json(root / contract["stage10f_result_path"])
    actions = stage10e["activity_fractures"]
    exposure_ids = {
        file_name.split("_")[0]
        for action in actions
        for file_name in action["file_names"]
    }
    denominator_ok = (
        stage10e.get("pass") is True
        and stage10f.get("pass") is True
        and len(actions) == expected["fractured_actions"]
        and len(exposure_ids) == expected["exposure_ids"]
    )
    add_check(
        checks,
        errors,
        "verified_action_denominator",
        denominator_ok,
        error="The verified fractured-action or exposure-identity denominator changed.",
        actions=len(actions),
        exposure_ids=len(exposure_ids),
    )

    response = load_json(root / contract["atlas_response_path"])
    hits = response.get("hits", {}).get("hits", [])
    total = response.get("hits", {}).get("total", {})
    by_id: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    collection_counts: Counter[str | None] = Counter()
    collection_bytes: Counter[str | None] = Counter()
    activity_counts: Counter[str | None] = Counter()
    for hit in hits:
        source = hit.get("_source", {})
        internal_id = scalar(source, INTERNAL_ID)
        collection = source.get("collection_id")
        by_id[internal_id].append(source)
        collection_counts[collection] += 1
        collection_bytes[collection] += int(source.get("archive", {}).get("size", 0))
        activity_counts[scalar(source, ACTIVITY_ID)] += 1
    expected_collections = {"data_source", "data_raw", "data_processed"}
    representation_invariant = all(
        len(records) == 3
        and {record.get("collection_id") for record in records} == expected_collections
        and len({scalar(record, ACTIVITY_ID) for record in records}) == 1
        and len({scalar(record, TARGET_ID) for record in records}) == 1
        for records in by_id.values()
    )
    representation_ok = (
        total.get("relation") == "eq"
        and total.get("value") == len(hits) == expected["product_records"]
        and {value for value in by_id if value} == exposure_ids
        and len(by_id) == expected["exposure_ids"]
        and representation_invariant
        and dict(collection_counts) == expected["collection_counts"]
        and dict(collection_bytes) == expected["collection_bytes"]
        and sum(collection_bytes.values()) == expected["total_bytes"]
    )
    add_check(
        checks,
        errors,
        "three_representation_product_multiplication",
        representation_ok,
        error="The 69 exposure IDs no longer reproduce as 207 invariant products across three collections.",
        product_records=len(hits),
        exposure_ids=len(by_id),
        collection_counts=dict(collection_counts),
        collection_bytes=dict(collection_bytes),
        total_bytes=sum(collection_bytes.values()),
        metadata_invariant_across_representations=representation_invariant,
    )

    coupled_actions = sum(
        partitions_equivalent(action["activity_ids"], action["target_ids"])
        for action in actions
    )
    coupling_ok = coupled_actions == expected["activity_target_partition_coupled_actions"]
    add_check(
        checks,
        errors,
        "activity_target_partition_coupling",
        coupling_ok,
        error="The activity/target partition coupling count changed.",
        coupled_actions=coupled_actions,
        fractured_actions=len(actions),
    )

    discussion_actions = [
        action
        for action in actions
        if {value for value in action["activity_ids"] if value} == {DISCUSSION, CREW_CHOICE}
    ]
    discussion_exposures = {
        file_name.split("_")[0]
        for action in discussion_actions
        for file_name, activity in zip(action["file_names"], action["activity_ids"])
        if activity == DISCUSSION
    }
    discussion_products = activity_counts[DISCUSSION]
    complete_actions = sum(
        all(activity == DISCUSSION for activity in action["activity_ids"])
        for action in discussion_actions
    )
    companion_exposures = sum(
        activity != DISCUSSION
        for action in discussion_actions
        for activity in action["activity_ids"]
    )
    stress_ok = (
        len(discussion_actions) == expected["discussion_crew_choice_actions"]
        and len(discussion_exposures) == expected["discussion_exposure_ids"]
        and discussion_products == expected["discussion_product_records"]
        and complete_actions == expected["discussion_complete_actions_recoverable"]
        and companion_exposures == expected["discussion_companion_exposure_ids_needed"]
        and companion_exposures * 3 == expected["discussion_companion_product_records_needed"]
    )
    add_check(
        checks,
        errors,
        "discussion_facet_overcount_and_under_recovery",
        stress_ok,
        error="The Discussion #4 stress-case product, exposure, or action reconstruction counts changed.",
        actions_touched=len(discussion_actions),
        product_records=discussion_products,
        exposure_ids=len(discussion_exposures),
        complete_actions=complete_actions,
        companion_exposure_ids_needed=companion_exposures,
        companion_product_records_needed=companion_exposures * 3,
    )

    state = spec["mutation_state"]
    boundary_ok = (
        not any(
            state[key]
            for key in (
                "products_declared_independent_observations",
                "representations_declared_evidence_multiplier",
                "exposures_declared_all_archive_anomalies",
                "target_correctness_inferred",
                "discussion_facet_declared_action_complete",
                "representations_declared_waste",
            )
        )
        and state["scope"] == "verified_fractured_raw_brackets"
        and contract["pixel_payload_bytes"] == 0
        and receipt["pixel_payload_bytes"] == 0
    )
    add_check(
        checks,
        errors,
        "claim_and_access_boundaries",
        boundary_ok,
        error="A prohibited independence, evidence, anomaly, correctness, waste, scope, or pixel claim was admitted.",
        mutation_state=state,
        pixel_payload_bytes=contract["pixel_payload_bytes"],
    )

    evidence_state = (
        "VERIFIED_RETRIEVAL_DISTORTION_AMPLIFICATION"
        if representation_ok and coupling_ok and stress_ok
        else "MIXED_OR_UNRESOLVED"
    )
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "fractured_actions": len(actions),
        "exposure_ids": len(exposure_ids),
        "product_records": len(hits),
        "collection_counts": dict(collection_counts),
        "collection_bytes": dict(collection_bytes),
        "total_bytes": sum(collection_bytes.values()),
        "activity_target_partition_coupled_actions": coupled_actions,
        "discussion_crew_choice_actions": len(discussion_actions),
        "discussion_exposure_ids": len(discussion_exposures),
        "discussion_product_records": discussion_products,
        "discussion_complete_actions_recoverable": complete_actions,
        "discussion_companion_exposure_ids_needed": companion_exposures,
        "discussion_companion_product_records_needed": companion_exposures * 3,
        "verified": spec["interpretation"]["verified"],
        "stress_case": spec["interpretation"]["stress_case"],
        "decision_use": spec["interpretation"]["decision_use"],
        "pixel_payload_bytes": receipt["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10g(root)
    names = load_json(root / "spec" / "stage10g.json")["hard_negatives"]
    mutations = {name: verify_stage10g(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 10G hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10G — Retrieval Distortion Amplification",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Fractured actions / exposure IDs / products: `{result['fractured_actions']}` / `{result['exposure_ids']}` / `{result['product_records']}`",
        f"- Total footprint of those products: `{result['total_bytes'] / 1_000_000_000:.6f} GB`",
        f"- Activity/target partition coupled actions: `{result['activity_target_partition_coupled_actions']}` / `{result['fractured_actions']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "",
        "## Verified",
        "",
        result["verified"],
        "",
        "## Discussion #4 stress case",
        "",
        result["stress_case"],
        "",
        "## Decision use",
        "",
        result["decision_use"],
        "",
        "## Claim ceiling",
        "",
        result["claim_ceiling"],
        "",
        "## Hard negatives",
        "",
    ]
    for name, mutation_result in result.get("hard_negatives", {}).items():
        verdict = "REJECTED" if not mutation_result["pass"] else "UNEXPECTEDLY ACCEPTED"
        lines.append(f"- `{name}`: {verdict}")
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
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        result = verify_with_mutations(args.root.resolve())
    else:
        result = verify_stage10g(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(
            render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
