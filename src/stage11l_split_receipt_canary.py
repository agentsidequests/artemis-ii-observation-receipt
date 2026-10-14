#!/usr/bin/env python3
"""Build and verify Stage 11L's deterministic split-receipt canary."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json
from stage10o_relationship_manifest import verify_stage10o


FIELDS = [
    "product_id",
    "capture_identity",
    "action_id",
    "temporal_cluster_5s",
    "product_key_partition",
    "action_key_partition",
    "temporal_5s_key_partition",
]
POLICY_COLUMNS = {
    "product_key": "product_key_partition",
    "action_key": "action_key_partition",
    "temporal_5s_key": "temporal_5s_key_partition",
}
POLICY_KEYS = {
    "product_key": "product_id",
    "action_key": "action_id",
    "temporal_5s_key": "temporal_cluster_5s",
}


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "source_hash_override": None,
        "artifact_mutation": None,
        "action_policy_key": "action_id",
        "temporal_groups_are_scenes": False,
        "result_kind": "deterministic_canary",
        "performance_effect": False,
        "five_seconds_is_universal": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    mapping = {
        "mismatch_source_hash": ("source_hash_override", "0" * 64),
        "tamper_partition_assignment": ("artifact_mutation", "tamper_partition_assignment"),
        "drop_assignment_row": ("artifact_mutation", "drop_assignment_row"),
        "misdeclare_product_policy_as_action_safe": ("action_policy_key", "product_id"),
        "call_temporal_groups_semantic_scenes": ("temporal_groups_are_scenes", True),
        "call_crossing_observed_model_leakage": ("result_kind", "observed_model_leakage"),
        "infer_model_performance_effect": ("performance_effect", True),
        "claim_five_seconds_is_universal": ("five_seconds_is_universal", True),
        "open_pixels_for_split_canary": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    state[key] = value
    return mutated


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def partition_for(key: str, algorithm: dict[str, Any]) -> str:
    payload = f"{algorithm['seed']}\0{key}".encode("utf-8")
    value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    space = 1 << 64
    cutoff = (space * int(algorithm["train_numerator"])) // int(algorithm["train_denominator"])
    return "train" if value < cutoff else "test"


def load_relationship_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_assignment_rows(root: Path, spec: dict[str, Any]) -> list[dict[str, str]]:
    source = root / spec["source_contract"]["relationship_manifest_path"]
    algorithm = spec["algorithm"]
    rows = []
    for row in load_relationship_rows(source):
        rows.append({
            "product_id": row["product_id"],
            "capture_identity": row["capture_identity"],
            "action_id": row["action_id"],
            "temporal_cluster_5s": row["temporal_cluster_5s"],
            "product_key_partition": partition_for(row["product_id"], algorithm),
            "action_key_partition": partition_for(row["action_id"], algorithm),
            "temporal_5s_key_partition": partition_for(row["temporal_cluster_5s"], algorithm),
        })
    return rows


def render_assignments(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def parse_assignment_bytes(payload: bytes) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("The assignment artifact is not valid UTF-8.") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != FIELDS:
        raise ValueError("The assignment artifact fields do not match the frozen schema.")
    rows = list(reader)
    if any(None in row or any(row[field] is None for field in FIELDS) for row in rows):
        raise ValueError("The assignment artifact contains a malformed row.")
    return rows


def load_assignment_rows(path: Path) -> list[dict[str, str]]:
    return parse_assignment_bytes(path.read_bytes())


def policy_metrics(rows: list[dict[str, str]], partition_column: str) -> dict[str, Any]:
    products_by_partition = Counter(row[partition_column] for row in rows)
    actions_by_partition: dict[str, set[str]] = defaultdict(set)
    temporal_by_partition: dict[str, set[str]] = defaultdict(set)
    action_parts: dict[str, set[str]] = defaultdict(set)
    temporal_parts: dict[str, set[str]] = defaultdict(set)
    temporal_actions: dict[str, set[str]] = defaultdict(set)
    temporal_products: Counter[str] = Counter()
    for row in rows:
        partition = row[partition_column]
        action_id = row["action_id"]
        temporal_id = row["temporal_cluster_5s"]
        actions_by_partition[partition].add(action_id)
        temporal_by_partition[partition].add(temporal_id)
        action_parts[action_id].add(partition)
        temporal_parts[temporal_id].add(partition)
        temporal_actions[temporal_id].add(action_id)
        temporal_products[temporal_id] += 1

    crossing_actions = {key for key, parts in action_parts.items() if len(parts) > 1}
    crossing_temporal = {key for key, parts in temporal_parts.items() if len(parts) > 1}
    actions_in_crossing_temporal = set().union(
        *(temporal_actions[key] for key in crossing_temporal)
    ) if crossing_temporal else set()
    products_in_crossing_actions = sum(1 for row in rows if row["action_id"] in crossing_actions)
    products_in_crossing_temporal = sum(temporal_products[key] for key in crossing_temporal)
    return {
        "products_by_partition": dict(sorted(products_by_partition.items())),
        "test_product_share": products_by_partition.get("test", 0) / len(rows) if rows else 0.0,
        "actions_visible_by_partition": {
            key: len(value) for key, value in sorted(actions_by_partition.items())
        },
        "temporal_5s_groups_visible_by_partition": {
            key: len(value) for key, value in sorted(temporal_by_partition.items())
        },
        "crossing_action_groups": len(crossing_actions),
        "products_in_crossing_action_groups": products_in_crossing_actions,
        "crossing_temporal_5s_groups": len(crossing_temporal),
        "actions_in_crossing_temporal_5s_groups": len(actions_in_crossing_temporal),
        "products_in_crossing_temporal_5s_groups": products_in_crossing_temporal,
    }


def build_receipt(root: Path, spec: dict[str, Any], assignment_bytes: bytes) -> dict[str, Any]:
    source_path = root / spec["source_contract"]["relationship_manifest_path"]
    source_rows = load_relationship_rows(source_path)
    rows = parse_assignment_bytes(assignment_bytes)
    source_bytes = source_path.read_bytes()
    return {
        "testbed_id": spec["testbed_id"],
        "receipt_version": "1.0.0",
        "validator": {
            "name": "stage11l_split_receipt_canary",
            "version": "1.0.0",
        },
        "frozen_task": spec["engineering_contract"]["frozen_task"],
        "source": {
            "path": spec["source_contract"]["relationship_manifest_path"],
            "bytes": len(source_bytes),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "rows": len(source_rows),
        },
        "algorithm": spec["algorithm"],
        "assignment_artifact": {
            "path": spec["source_contract"]["assignment_artifact_path"],
            "bytes": len(assignment_bytes),
            "sha256": hashlib.sha256(assignment_bytes).hexdigest(),
            "fields": FIELDS,
        },
        "unresolved_relationships": 0,
        "unknown_assignment_rows": 0,
        "policies": {
            name: {
                "grouping_key": POLICY_KEYS[name],
                **policy_metrics(rows, column),
            }
            for name, column in POLICY_COLUMNS.items()
        },
        "oracle": {
            "action_preservation": "pass when crossing_action_groups equals zero",
            "temporal_5s_preservation": "pass when crossing_temporal_5s_groups equals zero",
            "source_identity": "pass when source bytes match the frozen SHA-256",
            "assignment_replay": "pass when every partition recomputes from the declared key, seed, and algorithm",
            "completeness": "pass when every source product appears exactly once",
            "independence": "partial; implementation and validator share the frozen algorithm, while mutation tests can contradict source, assignment, completeness, policy, and claim assertions",
        },
        "claim_boundary": {
            "canary_not_scientific_task_split": True,
            "temporal_groups_not_semantic_scenes": True,
            "no_observed_leakage_claim": True,
            "no_performance_effect_claim": True,
            "five_seconds_not_universal": True,
            "pixel_payload_bytes": 0,
        },
    }


def build_artifacts(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    rows = build_assignment_rows(root, spec)
    assignment_bytes = render_assignments(rows)
    receipt = build_receipt(root, spec, assignment_bytes)
    receipt_bytes = canonical_json_bytes(receipt)
    assignment_path = root / spec["source_contract"]["assignment_artifact_path"]
    receipt_path = root / spec["source_contract"]["receipt_path"]
    assignment_path.parent.mkdir(parents=True, exist_ok=True)
    assignment_path.write_bytes(assignment_bytes)
    receipt_path.write_bytes(receipt_bytes)
    return {
        "assignment_bytes": len(assignment_bytes),
        "assignment_sha256": hashlib.sha256(assignment_bytes).hexdigest(),
        "receipt_bytes": len(receipt_bytes),
        "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
        "policies": receipt["policies"],
    }


def verify_stage11l(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11l.json"), mutation)
    expected = spec["frozen_observables"]
    state = spec["mutation_state"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior = verify_stage10o(root)
    add_check(checks, errors, "relationship_manifest_replay", prior.get("pass") is True,
              error="The Stage 10O relationship manifest did not replay.")

    source_path = root / spec["source_contract"]["relationship_manifest_path"]
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    expected_source_sha = state["source_hash_override"] or spec["source_contract"]["relationship_manifest_sha256"]
    add_check(checks, errors, "frozen_source_identity", source_sha == expected_source_sha,
              error="The relationship manifest does not match the frozen source hash.", sha256=source_sha)

    built_rows = build_assignment_rows(root, spec)
    built_assignment_bytes = render_assignments(built_rows)
    built_receipt = build_receipt(root, spec, built_assignment_bytes)
    built_receipt_bytes = canonical_json_bytes(built_receipt)
    assignment_path = root / spec["source_contract"]["assignment_artifact_path"]
    receipt_path = root / spec["source_contract"]["receipt_path"]
    artifact_ok = (
        assignment_path.is_file()
        and receipt_path.is_file()
        and assignment_path.read_bytes() == built_assignment_bytes
        and receipt_path.read_bytes() == built_receipt_bytes
        and len(built_assignment_bytes) == expected["assignment_bytes"]
        and hashlib.sha256(built_assignment_bytes).hexdigest() == expected["assignment_sha256"]
        and len(built_receipt_bytes) == expected["receipt_bytes"]
        and hashlib.sha256(built_receipt_bytes).hexdigest() == expected["receipt_sha256"]
    )
    add_check(checks, errors, "deterministic_artifact_identity", artifact_ok,
              error="The saved assignment artifact or receipt does not match the deterministic rebuild.")

    rows = load_assignment_rows(assignment_path) if assignment_path.is_file() else []
    if state["artifact_mutation"] == "tamper_partition_assignment" and rows:
        rows[0]["action_key_partition"] = "test" if rows[0]["action_key_partition"] == "train" else "train"
    elif state["artifact_mutation"] == "drop_assignment_row" and rows:
        rows.pop()

    source_rows = load_relationship_rows(source_path)
    source_ids = [row["product_id"] for row in source_rows]
    artifact_ids = [row["product_id"] for row in rows]
    completeness_ok = (
        len(rows) == expected["products"]
        and len(artifact_ids) == len(set(artifact_ids))
        and artifact_ids == source_ids
    )
    add_check(checks, errors, "complete_one_to_one_assignments", completeness_ok,
              error="The assignment artifact does not contain every source product exactly once.")

    replay_ok = True
    for row in rows:
        for policy, column in POLICY_COLUMNS.items():
            if row[column] != partition_for(row[POLICY_KEYS[policy]], spec["algorithm"]):
                replay_ok = False
                break
        if not replay_ok:
            break
    add_check(checks, errors, "assignment_replay", replay_ok,
              error="At least one partition assignment does not replay from its declared key.")

    metrics = {
        name: {"grouping_key": POLICY_KEYS[name], **policy_metrics(rows, column)}
        for name, column in POLICY_COLUMNS.items()
    }
    metrics_ok = metrics == expected["policies"]
    add_check(checks, errors, "frozen_policy_metrics", metrics_ok,
              error="The canary policy metrics differ from the frozen result.", policies=metrics)

    oracle_ok = (
        metrics.get("product_key", {}).get("crossing_action_groups", 0) > 0
        and metrics.get("action_key", {}).get("crossing_action_groups") == 0
        and metrics.get("action_key", {}).get("crossing_temporal_5s_groups", 0) > 0
        and metrics.get("temporal_5s_key", {}).get("crossing_action_groups") == 0
        and metrics.get("temporal_5s_key", {}).get("crossing_temporal_5s_groups") == 0
    )
    add_check(checks, errors, "relationship_preservation_oracle", oracle_ok,
              error="The three policies no longer produce the required discriminating preservation pattern.")

    boundary_ok = (
        state["action_policy_key"] == "action_id"
        and not state["temporal_groups_are_scenes"]
        and state["result_kind"] == "deterministic_canary"
        and not state["performance_effect"]
        and not state["five_seconds_is_universal"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited policy, semantic, leakage, performance, universality, or pixel claim was admitted.")

    evidence_state = "VERIFIED_DETERMINISTIC_SPLIT_RECEIPT_CANARY" if not errors else "REJECTED"
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": evidence_state,
        "source_sha256": source_sha,
        "assignment_bytes": len(built_assignment_bytes),
        "assignment_sha256": hashlib.sha256(built_assignment_bytes).hexdigest(),
        "receipt_bytes": len(built_receipt_bytes),
        "receipt_sha256": hashlib.sha256(built_receipt_bytes).hexdigest(),
        "policies": metrics,
        "verified": "The deterministic canary distinguishes three policy boundaries: product hashing fractures declared action groups; action hashing preserves actions but still fractures conditional five-second groups; hashing the five-second key preserves both declared layers.",
        "decision_use": "Use the receipt as executable evidence that declared relationships can be checked and failed. Do not reuse the canary assignment as a scientific split; a real task must replace the conditional key with its own dependence oracle.",
        "pixel_payload_bytes": state["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage11l(root)
    names = load_json(root / "spec/stage11l.json")["hard_negatives"]
    mutations = {name: verify_stage11l(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11L hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    policies = result["policies"]
    lines = [
        "# Stage 11L: Deterministic Split-Receipt Canary", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Source manifest SHA-256: `{result['source_sha256']}`",
        f"- Assignment artifact bytes / SHA-256: `{result['assignment_bytes']:,}` / `{result['assignment_sha256']}`",
        f"- Receipt bytes / SHA-256: `{result['receipt_bytes']:,}` / `{result['receipt_sha256']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified", "", result["verified"], "", "## Policy comparison", "",
        "| Policy key | Test product share | Crossing action groups | Crossing 5-second groups | Actions inside crossing 5-second groups |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name in ("product_key", "action_key", "temporal_5s_key"):
        item = policies[name]
        lines.append(
            f"| `{item['grouping_key']}` | {item['test_product_share']:.3%} | "
            f"{item['crossing_action_groups']:,} | {item['crossing_temporal_5s_groups']:,} | "
            f"{item['actions_in_crossing_temporal_5s_groups']:,} |"
        )
    lines += [
        "", "## Decision use", "", result["decision_use"],
        "", "## Claim ceiling", "", result["claim_ceiling"],
        "", "## Hard negatives", "",
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
    parser.add_argument("command", choices=("build", "run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--mutation")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "build":
        summary = build_artifacts(root, load_json(root / "spec/stage11l.json"))
        print(json.dumps(summary, indent=2))
        return 0
    result = verify_with_mutations(root) if args.command == "verify" else verify_stage11l(root, args.mutation)
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
