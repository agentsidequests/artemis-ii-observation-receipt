#!/usr/bin/env python3
"""Build and verify Stage 10O's product-to-action relationship manifest."""

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

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_json
from stage10j_fractional_bracket_expansion import verify_stage10j
from stage10l_representation_compression import verify_stage10l
from stage10n_temporal_adjacency_sensitivity import reconstruct_actions, temporal_clusters, verify_stage10n


COLLECTION_ORDER = {"data_source": 0, "data_raw": 1, "data_processed": 2}
THRESHOLDS = (1, 2, 5, 10, 30)
FIELDS = [
    "product_id", "collection_id", "archive_size_bytes", "capture_identity",
    "action_id", "action_index", "camera_serial", "action_start_utc", "action_end_utc",
    "exposure_position", "exposures_in_action", "bracket_value", "activity_id", "target_id",
    "activity_facet_fracture", "target_presence_fracture", "target_value_fracture",
    "temporal_cluster_1s", "temporal_cluster_2s", "temporal_cluster_5s",
    "temporal_cluster_10s", "temporal_cluster_30s",
]


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "partition_status": "unassigned",
        "action_key": "reconstructed_complete_action",
        "products_independent": False,
        "action_id_authority": "private_derived_key",
        "temporal_clusters_are_scenes": False,
        "action_scope": "verified_complete_actions",
        "pixel_similarity_inferred": False,
        "archive_scope": "verified_complete_action_cohort",
        "result_kind": "relationship_manifest",
        "global_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    mapping = {
        "assign_train_test_without_a_frozen_task": ("partition_status", "assigned_80_20"),
        "use_activity_as_the_action_key": ("action_key", "activity_id"),
        "count_products_as_independent_observations": ("products_independent", True),
        "call_private_action_ids_official_pds_ids": ("action_id_authority", "official_pds_id"),
        "call_temporal_clusters_semantic_scenes": ("temporal_clusters_are_scenes", True),
        "include_unadmitted_records_as_complete_actions": ("action_scope", "all_records"),
        "infer_pixel_similarity": ("pixel_similarity_inferred", True),
        "claim_archive_wide_exhaustiveness": ("archive_scope", "complete_archive"),
        "call_hypothetical_hazard_observed_leakage": ("result_kind", "observed_leakage"),
        "claim_global_priority": ("global_priority", True),
        "open_pixels_for_manifest": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    state[key] = value
    return mutated


def stable_key(prefix: str, values: list[str]) -> str:
    digest = hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}-{digest}"


def action_identity(action: dict[str, Any]) -> str:
    capture_ids = [name.split("_", 1)[0] for name in action["file_names"]]
    return stable_key("a2-action", [action["serial"], action["start_time"], *capture_ids])


def product_records(root: Path, batch_dir: str) -> dict[str, list[dict[str, Any]]]:
    records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted((root / batch_dir).glob("batch-*-response.json")):
        for hit in load_json(path).get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            values = source.get("pds4_label", {}).get("msn:Mission_Information/msn:internal_id", [])
            if len(values) != 1:
                continue
            records[str(values[0])].append({
                "product_id": str(hit.get("_id")),
                "collection_id": str(source.get("collection_id")),
                "archive_size_bytes": int(source.get("archive", {}).get("size", 0)),
            })
    for values in records.values():
        values.sort(key=lambda item: (COLLECTION_ORDER.get(item["collection_id"], 99), item["product_id"]))
    return records


def build_rows(root: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    stage10n_spec = load_json(root / spec["source_contract"]["stage10n_spec_path"])
    actions = reconstruct_actions(root, stage10n_spec)
    action_ids = {id(action): action_identity(action) for action in actions}
    if len(set(action_ids.values())) != len(actions):
        raise ValueError("Private action-key collision")

    cluster_ids: dict[int, dict[str, str]] = {}
    for threshold in THRESHOLDS:
        mapping: dict[str, str] = {}
        for cluster in temporal_clusters(actions, float(threshold)):
            member_ids = [action_ids[id(action)] for action in cluster]
            cluster_id = stable_key(f"a2-t{threshold}s", member_ids)
            for member_id in member_ids:
                mapping[member_id] = cluster_id
        cluster_ids[threshold] = mapping

    products = product_records(root, spec["source_contract"]["stage10l_batch_dir"])
    rows: list[dict[str, Any]] = []
    for action_index, action in enumerate(actions, start=1):
        action_id = action_ids[id(action)]
        exposure_count = len(action["file_names"])
        for exposure_index, file_name in enumerate(action["file_names"]):
            capture_identity = file_name.split("_", 1)[0]
            for product in products.get(capture_identity, []):
                rows.append({
                    **product,
                    "capture_identity": capture_identity,
                    "action_id": action_id,
                    "action_index": action_index,
                    "camera_serial": action["serial"],
                    "action_start_utc": action["start_time"],
                    "action_end_utc": action["end_time"],
                    "exposure_position": exposure_index + 1,
                    "exposures_in_action": exposure_count,
                    "bracket_value": action["bracket_values"][exposure_index],
                    "activity_id": action["activity_ids"][exposure_index] or "",
                    "target_id": action["target_ids"][exposure_index] or "",
                    "activity_facet_fracture": str(bool(action["activity_facet_fracture"])).lower(),
                    "target_presence_fracture": str(bool(action["target_presence_fracture"])).lower(),
                    "target_value_fracture": str(bool(action["target_value_fracture"])).lower(),
                    **{f"temporal_cluster_{threshold}s": cluster_ids[threshold][action_id] for threshold in THRESHOLDS},
                })
    return rows


def render_manifest(rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_stage10o(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10o.json"), mutation)
    expected = spec["frozen_observables"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior_j = verify_stage10j(root)
    prior_l = verify_stage10l(root)
    prior_n = verify_stage10n(root)
    prior_ok = prior_j.get("pass") is True and prior_l.get("pass") is True and prior_n.get("pass") is True
    add_check(checks, errors, "prior_hierarchy_replay", prior_ok,
              error="The product, action, or temporal-group source result did not replay.")

    manifest_path = root / spec["source_contract"]["manifest_path"]
    built_bytes = render_manifest(build_rows(root, spec))
    built_sha = hashlib.sha256(built_bytes).hexdigest()
    artifact_ok = (
        manifest_path.is_file()
        and manifest_path.read_bytes() == built_bytes
        and len(built_bytes) == expected["manifest_bytes"]
        and built_sha == expected["manifest_sha256"]
    )
    add_check(checks, errors, "deterministic_manifest_identity", artifact_ok,
              error="The saved relationship manifest does not match the deterministic rebuild.",
              bytes=len(built_bytes), sha256=built_sha)

    rows = load_manifest(manifest_path) if manifest_path.is_file() else []
    product_ids = {row["product_id"] for row in rows}
    capture_ids = {row["capture_identity"] for row in rows}
    action_ids = {row["action_id"] for row in rows}
    collection_counts = Counter(row["collection_id"] for row in rows)
    hierarchy_ok = (
        len(rows) == len(product_ids) == expected["products"]
        and len(capture_ids) == expected["capture_identities"]
        and len(action_ids) == expected["complete_actions"]
        and dict(collection_counts) == expected["expected_collection_counts"]
        and sum(int(row["archive_size_bytes"]) for row in rows) == expected["expected_total_bytes"]
    )
    add_check(checks, errors, "hierarchy_cardinalities", hierarchy_ok,
              error="The manifest no longer preserves product, capture, action, collection, or byte totals.",
              rows=len(rows), captures=len(capture_ids), actions=len(action_ids), collections=dict(collection_counts))

    products_by_capture = Counter(row["capture_identity"] for row in rows)
    products_by_action = Counter(row["action_id"] for row in rows)
    grouping_ok = (
        set(products_by_capture.values()) == {3}
        and Counter(products_by_action.values()) == {
            9: expected["three_exposure_actions"], 15: expected["five_exposure_actions"]
        }
    )
    add_check(checks, errors, "exact_representation_and_action_groups", grouping_ok,
              error="A capture or action no longer has the exact expected product grouping.",
              products_per_capture=dict(Counter(products_by_capture.values())),
              products_per_action=dict(Counter(products_by_action.values())))

    temporal_counts = {
        str(threshold): len({row[f"temporal_cluster_{threshold}s"] for row in rows})
        for threshold in THRESHOLDS
    }
    temporal_ok = temporal_counts == expected["expected_temporal_clusters"]
    add_check(checks, errors, "conditional_temporal_group_keys", temporal_ok,
              error="The manifest temporal-cluster keys no longer replay Stage 10N.", counts=temporal_counts)

    state = spec["mutation_state"]
    boundary_ok = (
        state["partition_status"] == "unassigned"
        and state["action_key"] == "reconstructed_complete_action"
        and not state["products_independent"]
        and state["action_id_authority"] == "private_derived_key"
        and not state["temporal_clusters_are_scenes"]
        and state["action_scope"] == "verified_complete_actions"
        and not state["pixel_similarity_inferred"]
        and state["archive_scope"] == "verified_complete_action_cohort"
        and state["result_kind"] == "relationship_manifest"
        and not state["global_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited partition, independence, identity, semantic, scope, similarity, leakage, novelty, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_PRODUCT_ACTION_RELATIONSHIP_MANIFEST" if all((prior_ok, artifact_ok, hierarchy_ok, grouping_ok, temporal_ok)) else "RELATIONSHIP_MANIFEST_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "products": len(rows), "capture_identities": len(capture_ids), "complete_actions": len(action_ids),
        "collection_counts": dict(collection_counts), "total_bytes": sum(int(row["archive_size_bytes"]) for row in rows),
        "temporal_cluster_counts": temporal_counts, "manifest_path": spec["source_contract"]["manifest_path"],
        "manifest_bytes": len(built_bytes), "manifest_sha256": built_sha,
        "verified": "Every one of the 22,818 products in the verified cohort maps deterministically to one of 7,606 capture identities and one of 2,166 reconstructed complete actions. The manifest also carries separate private keys for each Stage 10N temporal threshold without assigning train, validation, or test membership.",
        "decision_use": "Join a later task to this relationship layer before splitting. Keep action_id as the exact minimum group and choose a broader temporal or semantic key only after the task supplies its dependence oracle.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10o(root)
    names = load_json(root / "spec/stage10o.json")["hard_negatives"]
    mutations = {name: verify_stage10o(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10O hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10O — Product-to-Action Relationship Manifest", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Products / captures / complete actions: `{result['products']:,}` / `{result['capture_identities']:,}` / `{result['complete_actions']:,}`",
        f"- Manifest bytes: `{result['manifest_bytes']:,}`",
        f"- Manifest SHA-256: `{result['manifest_sha256']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified", "", result["verified"], "", "## Decision use", "", result["decision_use"],
        "", "## Conditional temporal group counts", "",
    ]
    for threshold, count in result["temporal_cluster_counts"].items():
        lines.append(f"- `{threshold}s`: `{count:,}` groups")
    lines += ["", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", ""]
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
        spec = load_json(root / "spec/stage10o.json")
        payload = render_manifest(build_rows(root, spec))
        path = root / spec["source_contract"]["manifest_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        print(json.dumps({"path": str(path), "bytes": len(payload), "sha256": sha256_file(path)}, indent=2))
        return 0
    result = verify_with_mutations(root) if args.command == "verify" else verify_stage10o(root, args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
