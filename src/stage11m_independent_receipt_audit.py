#!/usr/bin/env python3
"""Replay the serialized Stage 11L split receipt through a separate implementation."""

from __future__ import annotations

import argparse
import ast
import copy
import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ASSIGNMENT_FIELDS = [
    "product_id",
    "capture_identity",
    "action_id",
    "temporal_cluster_5s",
    "product_key_partition",
    "action_key_partition",
    "temporal_5s_key_partition",
]
RELATIONSHIP_FIELDS = (
    "product_id",
    "capture_identity",
    "action_id",
    "temporal_cluster_5s",
)
POLICIES = {
    "product_key": ("product_id", "product_key_partition"),
    "action_key": ("action_id", "action_key_partition"),
    "temporal_5s_key": ("temporal_cluster_5s", "temporal_5s_key_partition"),
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def parse_csv(payload: bytes, required_fields: list[str] | tuple[str, ...]) -> tuple[list[str], list[dict[str, str]]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV payload is not valid UTF-8.") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    fields = reader.fieldnames or []
    if not set(required_fields).issubset(fields):
        raise ValueError("CSV payload is missing required fields.")
    rows = list(reader)
    if any(None in row or any(row.get(field) is None for field in required_fields) for row in rows):
        raise ValueError("CSV payload contains a malformed row.")
    return fields, rows


def render_assignments(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=ASSIGNMENT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def render_receipt(receipt: dict[str, Any]) -> bytes:
    return (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")


def partition_for(key: str, algorithm: dict[str, Any]) -> str:
    digest = hashlib.sha256(f"{algorithm['seed']}\0{key}".encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], byteorder="big", signed=False)
    numerator = int(algorithm["train_numerator"])
    denominator = int(algorithm["train_denominator"])
    cutoff = ((1 << 64) * numerator) // denominator
    return "train" if value < cutoff else "test"


def policy_metrics(rows: list[dict[str, str]], partition_field: str) -> dict[str, Any]:
    products = Counter(row[partition_field] for row in rows)
    actions_visible: dict[str, set[str]] = defaultdict(set)
    temporal_visible: dict[str, set[str]] = defaultdict(set)
    action_partitions: dict[str, set[str]] = defaultdict(set)
    temporal_partitions: dict[str, set[str]] = defaultdict(set)
    temporal_actions: dict[str, set[str]] = defaultdict(set)
    temporal_products: Counter[str] = Counter()
    for row in rows:
        partition = row[partition_field]
        action = row["action_id"]
        temporal = row["temporal_cluster_5s"]
        actions_visible[partition].add(action)
        temporal_visible[partition].add(temporal)
        action_partitions[action].add(partition)
        temporal_partitions[temporal].add(partition)
        temporal_actions[temporal].add(action)
        temporal_products[temporal] += 1

    crossing_actions = {key for key, values in action_partitions.items() if len(values) > 1}
    crossing_temporal = {key for key, values in temporal_partitions.items() if len(values) > 1}
    actions_in_crossing_temporal: set[str] = set()
    for key in crossing_temporal:
        actions_in_crossing_temporal.update(temporal_actions[key])
    return {
        "products_by_partition": dict(sorted(products.items())),
        "test_product_share": products.get("test", 0) / len(rows) if rows else 0.0,
        "actions_visible_by_partition": {
            key: len(values) for key, values in sorted(actions_visible.items())
        },
        "temporal_5s_groups_visible_by_partition": {
            key: len(values) for key, values in sorted(temporal_visible.items())
        },
        "crossing_action_groups": len(crossing_actions),
        "products_in_crossing_action_groups": sum(
            row["action_id"] in crossing_actions for row in rows
        ),
        "crossing_temporal_5s_groups": len(crossing_temporal),
        "actions_in_crossing_temporal_5s_groups": len(actions_in_crossing_temporal),
        "products_in_crossing_temporal_5s_groups": sum(
            temporal_products[key] for key in crossing_temporal
        ),
    }


def has_stage11l_import(verifier_path: Path) -> bool:
    tree = ast.parse(verifier_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.startswith("stage11l") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").startswith("stage11l"):
                return True
    return False


def add_check(
    checks: list[dict[str, Any]],
    errors: list[str],
    name: str,
    passed: bool,
    error: str,
    **details: Any,
) -> None:
    checks.append({"name": name, "pass": bool(passed), **details})
    if not passed:
        errors.append(error)


def mutate_candidate(
    receipt: dict[str, Any],
    assignments: list[dict[str, str]],
    mutation: str | None,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    receipt = copy.deepcopy(receipt)
    assignments = [dict(row) for row in assignments]
    if mutation is None:
        return receipt, assignments
    if mutation == "tamper_source_hash_in_receipt":
        receipt["source"]["sha256"] = "0" * 64
    elif mutation == "tamper_assignment_hash_in_receipt":
        receipt["assignment_artifact"]["sha256"] = "0" * 64
    elif mutation == "tamper_algorithm_seed_in_receipt":
        receipt["algorithm"]["seed"] = "tampered-seed"
    elif mutation == "duplicate_assignment_row":
        assignments.append(dict(assignments[0]))
    elif mutation == "drop_assignment_row":
        assignments.pop()
    elif mutation == "change_relationship_key":
        assignments[0]["action_id"] += "-tampered"
    elif mutation == "tamper_partition_assignment":
        field = "product_key_partition"
        assignments[0][field] = "test" if assignments[0][field] == "train" else "train"
    elif mutation == "tamper_reported_metric":
        receipt["policies"]["action_key"]["crossing_action_groups"] = 99
    elif mutation == "call_temporal_groups_semantic_scenes":
        receipt["claim_boundary"]["temporal_groups_not_semantic_scenes"] = False
    elif mutation == "call_crossing_observed_model_leakage":
        receipt["claim_boundary"]["no_observed_leakage_claim"] = False
    elif mutation == "open_pixels_for_receipt_audit":
        receipt["claim_boundary"]["pixel_payload_bytes"] = 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return receipt, assignments


def audit_stage11m(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = load_json(root / "spec/stage11m.json")
    contract = spec["source_contract"]
    verifier_path = root / contract["verifier_source_path"]
    source_path = root / contract["relationship_manifest_path"]
    assignment_path = root / contract["assignment_artifact_path"]
    receipt_path = root / contract["receipt_path"]

    verifier_bytes = verifier_path.read_bytes()
    source_bytes = source_path.read_bytes()
    original_assignment_bytes = assignment_path.read_bytes()
    original_receipt_bytes = receipt_path.read_bytes()
    source_fields, source_rows = parse_csv(source_bytes, RELATIONSHIP_FIELDS)
    assignment_fields, original_assignments = parse_csv(original_assignment_bytes, ASSIGNMENT_FIELDS)
    original_receipt = json.loads(original_receipt_bytes.decode("utf-8"))
    receipt, assignments = mutate_candidate(original_receipt, original_assignments, mutation)
    assignment_bytes = original_assignment_bytes if mutation is None else render_assignments(assignments)
    receipt_bytes = original_receipt_bytes if mutation is None else render_receipt(receipt)

    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    add_check(
        checks,
        errors,
        "verifier_source_identity",
        sha256(verifier_bytes) == contract["verifier_source_sha256"],
        "The standalone verifier source does not match its frozen identity.",
        sha256=sha256(verifier_bytes),
    )
    add_check(
        checks,
        errors,
        "implementation_separation",
        not has_stage11l_import(verifier_path),
        "The consumer verifier imports Stage 11L implementation code.",
    )
    add_check(
        checks,
        errors,
        "source_artifact_identity",
        len(source_bytes) == contract["relationship_manifest_bytes"]
        and sha256(source_bytes) == contract["relationship_manifest_sha256"],
        "The relationship manifest does not match its frozen identity.",
    )
    add_check(
        checks,
        errors,
        "assignment_artifact_identity",
        len(assignment_bytes) == contract["assignment_artifact_bytes"]
        and sha256(assignment_bytes) == contract["assignment_artifact_sha256"],
        "The assignment artifact does not match its frozen identity.",
    )
    add_check(
        checks,
        errors,
        "receipt_artifact_identity",
        len(receipt_bytes) == contract["receipt_bytes"]
        and sha256(receipt_bytes) == contract["receipt_sha256"],
        "The receipt does not match its frozen identity.",
    )
    add_check(
        checks,
        errors,
        "assignment_schema",
        assignment_fields == ASSIGNMENT_FIELDS,
        "The assignment field order or schema differs from the consumer contract.",
    )

    receipt_source = receipt.get("source", {})
    add_check(
        checks,
        errors,
        "receipt_source_binding",
        receipt_source.get("path") == contract["relationship_manifest_path"]
        and receipt_source.get("bytes") == len(source_bytes)
        and receipt_source.get("sha256") == sha256(source_bytes)
        and receipt_source.get("rows") == len(source_rows),
        "The receipt does not bind the exact source manifest.",
    )
    receipt_assignment = receipt.get("assignment_artifact", {})
    add_check(
        checks,
        errors,
        "receipt_assignment_binding",
        receipt_assignment.get("path") == contract["assignment_artifact_path"]
        and receipt_assignment.get("bytes") == len(assignment_bytes)
        and receipt_assignment.get("sha256") == sha256(assignment_bytes)
        and receipt_assignment.get("fields") == ASSIGNMENT_FIELDS,
        "The receipt does not bind the exact assignment artifact.",
    )

    source_ids = [row["product_id"] for row in source_rows]
    assignment_ids = [row["product_id"] for row in assignments]
    complete = (
        len(assignments) == spec["frozen_observables"]["products"]
        and len(assignment_ids) == len(set(assignment_ids))
        and assignment_ids == source_ids
    )
    add_check(
        checks,
        errors,
        "complete_one_to_one_assignments",
        complete,
        "The assignment artifact is not a complete one-to-one rendering of source products.",
    )
    source_by_id = {row["product_id"]: row for row in source_rows}
    relationships_match = len(source_by_id) == len(source_rows)
    for row in assignments:
        source_row = source_by_id.get(row["product_id"])
        if source_row is None or any(row[field] != source_row[field] for field in RELATIONSHIP_FIELDS[1:]):
            relationships_match = False
            break
    add_check(
        checks,
        errors,
        "relationship_binding",
        relationships_match,
        "An assignment row changes or invents a declared source relationship.",
    )

    algorithm = receipt.get("algorithm", {})
    add_check(
        checks,
        errors,
        "algorithm_contract",
        algorithm == spec["algorithm"],
        "The receipt algorithm differs from the frozen consumer contract.",
    )
    replay_ok = True
    try:
        for row in assignments:
            for key_field, partition_field in POLICIES.values():
                if row[partition_field] != partition_for(row[key_field], algorithm):
                    replay_ok = False
                    break
            if not replay_ok:
                break
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        replay_ok = False
    add_check(
        checks,
        errors,
        "assignment_replay",
        replay_ok,
        "At least one assignment does not replay under the receipt algorithm.",
    )

    computed_policies = {
        name: {"grouping_key": key_field, **policy_metrics(assignments, partition_field)}
        for name, (key_field, partition_field) in POLICIES.items()
    }
    key_metrics = spec["frozen_observables"]["key_metrics"]
    frozen_metrics_match = (
        computed_policies["product_key"]["crossing_action_groups"]
        == key_metrics["product_key_crossing_actions"]
        and computed_policies["action_key"]["crossing_action_groups"]
        == key_metrics["action_key_crossing_actions"]
        and computed_policies["action_key"]["crossing_temporal_5s_groups"]
        == key_metrics["action_key_crossing_temporal_5s_groups"]
        and computed_policies["action_key"]["actions_in_crossing_temporal_5s_groups"]
        == key_metrics["action_key_actions_in_crossing_temporal_5s_groups"]
        and computed_policies["temporal_5s_key"]["crossing_action_groups"]
        == key_metrics["temporal_5s_key_crossing_actions"]
        and computed_policies["temporal_5s_key"]["crossing_temporal_5s_groups"]
        == key_metrics["temporal_5s_key_crossing_temporal_5s_groups"]
    )
    add_check(
        checks,
        errors,
        "receipt_metric_replay",
        receipt.get("policies") == computed_policies and frozen_metrics_match,
        "The receipt metrics do not match the standalone recomputation or frozen key metrics.",
        policies=computed_policies,
    )

    boundary = receipt.get("claim_boundary", {})
    boundaries_ok = (
        boundary.get("canary_not_scientific_task_split") is True
        and boundary.get("temporal_groups_not_semantic_scenes") is True
        and boundary.get("no_observed_leakage_claim") is True
        and boundary.get("no_performance_effect_claim") is True
        and boundary.get("five_seconds_not_universal") is True
        and boundary.get("pixel_payload_bytes") == 0
        and receipt.get("unresolved_relationships") == 0
        and receipt.get("unknown_assignment_rows") == 0
    )
    add_check(
        checks,
        errors,
        "claim_and_access_boundaries",
        boundaries_ok,
        "The receipt widens a prohibited claim, opens pixels, or leaves relationships unresolved.",
    )

    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": (
            "VERIFIED_IMPLEMENTATION_DIVERSE_SPLIT_RECEIPT_AUDIT"
            if not errors
            else "REJECTED"
        ),
        "oracle_independence": spec["engineering_contract"]["independence"]["classification"],
        "independence_details": spec["engineering_contract"]["independence"],
        "verifier_source_sha256": sha256(verifier_bytes),
        "source_sha256": sha256(source_bytes),
        "assignment_sha256": sha256(assignment_bytes),
        "receipt_sha256": sha256(receipt_bytes),
        "source_fields": source_fields,
        "policies": computed_policies,
        "pixel_payload_bytes": boundary.get("pixel_payload_bytes"),
        "verified": "A standalone consumer implementation reproduced the serialized source and assignment bindings, every assignment, and every policy metric without importing Stage 11L code.",
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec/stage11m.json")
    baseline = audit_stage11m(root)
    mutation_results: dict[str, Any] = {}
    hard_negatives_pass = True
    for name, required_failed_checks in spec["hard_negatives"].items():
        result = audit_stage11m(root, name)
        failed_checks = [check["name"] for check in result["checks"] if not check["pass"]]
        required_detected = all(check in failed_checks for check in required_failed_checks)
        rejected = not result["pass"] and required_detected
        hard_negatives_pass = hard_negatives_pass and rejected
        mutation_results[name] = {
            "rejected": rejected,
            "failed_checks": failed_checks,
            "required_failed_checks": required_failed_checks,
        }
    return {
        **baseline,
        "hard_negatives": mutation_results,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"] + (
            [] if hard_negatives_pass else ["At least one required Stage 11M mutation check passed."]
        ),
    }


def render_markdown(result: dict[str, Any]) -> str:
    policies = result["policies"]
    lines = [
        "# Stage 11M: Implementation-Diverse Split-Receipt Audit",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Oracle independence: `{result['oracle_independence']}`",
        f"- Verifier source SHA-256: `{result['verifier_source_sha256']}`",
        f"- Assignment SHA-256: `{result['assignment_sha256']}`",
        f"- Receipt SHA-256: `{result['receipt_sha256']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "",
        "## Verified",
        "",
        result["verified"],
        "",
        "## Separately recomputed key metrics",
        "",
        f"- Product-key crossing actions: `{policies['product_key']['crossing_action_groups']:,}`",
        f"- Action-key crossing actions: `{policies['action_key']['crossing_action_groups']:,}`",
        f"- Action-key crossing conditional five-second groups: `{policies['action_key']['crossing_temporal_5s_groups']:,}`",
        f"- Actions inside those crossed outer groups: `{policies['action_key']['actions_in_crossing_temporal_5s_groups']:,}`",
        f"- Five-second-key crossing actions / groups: `{policies['temporal_5s_key']['crossing_action_groups']:,}` / `{policies['temporal_5s_key']['crossing_temporal_5s_groups']:,}`",
        "",
        "## Mutation results",
        "",
    ]
    for name, mutation in result.get("hard_negatives", {}).items():
        status = "REJECTED AT REQUIRED CHECKS" if mutation["rejected"] else "NOT ADEQUATELY REJECTED"
        lines.append(f"- `{name}`: {status}")
    lines += ["", "## Claim ceiling", "", result["claim_ceiling"], ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--mutation")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    result = verify_with_mutations(root) if args.command == "verify" else audit_stage11m(root, args.mutation)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
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
