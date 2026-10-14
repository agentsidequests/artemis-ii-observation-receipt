#!/usr/bin/env python3
"""Verify Stage 10D's archive-unit normalization test."""

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


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "nasa_statement_declared_false": False,
        "formula_declared_documented": False,
        "representations_declared_independent_observations": False,
        "products_collapsed_to_one_file": False,
        "processed_omission_declared_intentional": False,
        "global_identity_parity_claimed": False,
        "snapshot_declared_permanent": False,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "call_nasa_800gb_statement_false":
        state["nasa_statement_declared_false"] = True
    elif mutation == "claim_nasa_documented_the_accounting_formula":
        state["formula_declared_documented"] = True
    elif mutation == "count_each_representation_as_an_independent_observation":
        state["representations_declared_independent_observations"] = True
    elif mutation == "collapse_three_products_into_one_downloadable_file":
        state["products_collapsed_to_one_file"] = True
    elif mutation == "claim_processed_products_were_intentionally_omitted":
        state["processed_omission_declared_intentional"] = True
    elif mutation == "generalize_two_action_identity_to_every_product":
        state["global_identity_parity_claimed"] = True
    elif mutation == "claim_atlas_snapshot_is_permanent":
        state["snapshot_declared_permanent"] = True
    elif mutation == "open_pixels_to_reconcile_archive_units":
        mutated["source_contract"]["pixel_payload_bytes"] = 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


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


def scalar(source: dict[str, Any], key: str) -> str | None:
    value = source.get("pds4_label", {}).get(key)
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value) if value is not None else None


def atlas_hits(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return payload.get("hits", {}).get("hits", [])


def atlas_total(payload: dict[str, Any]) -> int | None:
    return payload.get("hits", {}).get("total", {}).get("value")


def verify_stage10d(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10d.json"), mutation)
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
        error="A Stage 10D source byte or acquisition receipt identity changed.",
        failures=receipt_failures,
    )

    source_dir = root / "evidence" / "stage10d" / "source"
    footprint = load_json(source_dir / "atlas-mission-footprint-response.json")
    bundle_buckets = footprint.get("aggregations", {}).get("bundles", {}).get("buckets", [])
    bundle_counts = {item["key"]: item["doc_count"] for item in bundle_buckets}
    bundle_bytes = {item["key"]: int(item["bytes"]["value"]) for item in bundle_buckets}
    crew = next((item for item in bundle_buckets if item["key"] == "artemis2_crew_camera"), None)
    crew_collections = crew.get("collections", {}).get("buckets", []) if crew else []
    crew_collection_counts = {item["key"]: item["doc_count"] for item in crew_collections}
    crew_collection_bytes = {item["key"]: int(item["bytes"]["value"]) for item in crew_collections}
    mission_bytes = sum(bundle_bytes.values())
    footprint_ok = (
        atlas_total(footprint) == expected["mission_products"]
        and bundle_counts == expected["bundle_counts"]
        and bundle_bytes == expected["bundle_bytes"]
        and mission_bytes == expected["mission_bytes"]
        and crew_collection_counts == expected["crew_collection_counts"]
        and crew_collection_bytes == expected["crew_collection_bytes"]
    )
    add_check(
        checks,
        errors,
        "exact_atlas_product_footprint",
        footprint_ok,
        error="The preserved Atlas product counts or archive.size sums changed.",
        mission_products=atlas_total(footprint),
        mission_bytes=mission_bytes,
        bundle_counts=bundle_counts,
        bundle_bytes=bundle_bytes,
        crew_collection_counts=crew_collection_counts,
        crew_collection_bytes=crew_collection_bytes,
    )

    nonprocessed_bytes = mission_bytes - crew_collection_bytes.get("data_processed", 0)
    subtotal_ok = (
        nonprocessed_bytes
        == expected["mission_bytes_excluding_processed_crew_collection"]
        and nonprocessed_bytes > 800_000_000_000
        and nonprocessed_bytes < 900_000_000_000
    )
    add_check(
        checks,
        errors,
        "headline_consistent_subtotal",
        subtotal_ok,
        error="The preserved non-processed subtotal is no longer arithmetically consistent with more than 800 GB.",
        bytes=nonprocessed_bytes,
        decimal_gigabytes=nonprocessed_bytes / 1_000_000_000,
    )

    nasa_html = (root / contract["nasa_release_path"]).read_text(
        encoding="utf-8", errors="replace"
    ).lower()
    guide_text = " ".join(
        (root / contract["user_guide_text_path"])
        .read_text(encoding="utf-8", errors="replace")
        .lower()
        .split()
    )
    official_semantics_ok = (
        "more than 800 gigabytes" in nasa_html
        and "source nikon d5 and z9 camera images" in guide_text
        and "converted raw nikon d5 and z9 images" in guide_text
        and "processed nikon d5 and z9 images" in guide_text
        and "by comparing the timeline in the ltp with the timestamp of each data item" in guide_text
        and "the analyst designated activity overrides the ltp timeline activity" in guide_text
    )
    add_check(
        checks,
        errors,
        "official_statement_and_product_semantics",
        official_semantics_ok,
        error="The official headline, product-type definitions, or activity-generation rule changed.",
    )

    focus = load_json(source_dir / "atlas-forward-look-products-response.json")
    focus_hits = atlas_hits(focus)
    focus_ids = Counter(scalar(hit.get("_source", {}), INTERNAL_ID) for hit in focus_hits)
    focus_collections = Counter(hit.get("_source", {}).get("collection_id") for hit in focus_hits)
    focus_ok = (
        atlas_total(focus) == expected["forward_look_product_records"]
        and set(focus_ids) == set(expected["forward_look_internal_ids"])
        and all(count == 3 for count in focus_ids.values())
        and focus_collections
        == Counter({"data_source": 2, "data_raw": 2, "data_processed": 2})
    )
    add_check(
        checks,
        errors,
        "bounded_activity_representation_multiplication",
        focus_ok,
        error="The two Forward Look IDs no longer reproduce as six products across three representations.",
        product_records=atlas_total(focus),
        internal_id_counts=dict(focus_ids),
        collection_counts=dict(focus_collections),
    )

    action_payload = load_json(source_dir / "atlas-forward-look-actions-response.json")
    action_hits = atlas_hits(action_payload)
    action_ids: dict[str | None, set[str | None]] = defaultdict(set)
    action_collections = Counter()
    action_activities = Counter()
    for hit in action_hits:
        source = hit.get("_source", {})
        internal_id = scalar(source, INTERNAL_ID)
        collection = source.get("collection_id")
        action_ids[internal_id].add(collection)
        action_collections[collection] += 1
        action_activities[scalar(source, ACTIVITY_ID)] += 1
    expected_collection_set = {"data_source", "data_raw", "data_processed"}
    actions_ok = (
        atlas_total(action_payload) == expected["forward_look_action_product_records"]
        and len(action_ids) == expected["forward_look_action_internal_ids"]
        and all(collections == expected_collection_set for collections in action_ids.values())
        and action_collections == Counter(expected["forward_look_action_collection_counts"])
        and action_activities == Counter(expected["forward_look_action_activity_counts"])
    )
    add_check(
        checks,
        errors,
        "bounded_action_representation_multiplication",
        actions_ok,
        error="The ten bounded exposure IDs no longer reproduce as thirty products with preserved activity assignments.",
        product_records=atlas_total(action_payload),
        internal_ids=len(action_ids),
        collection_counts=dict(action_collections),
        activity_counts=dict(action_activities),
    )

    state = spec["mutation_state"]
    boundary_ok = (
        not any(state.values())
        and contract["pixel_payload_bytes"] == 0
        and receipt["pixel_payload_bytes"] == 0
    )
    add_check(
        checks,
        errors,
        "claim_and_access_boundaries",
        boundary_ok,
        error="A prohibited accusation, provenance, intent, identity, permanence, or pixel claim was admitted.",
        mutation_state=state,
        pixel_payload_bytes=contract["pixel_payload_bytes"],
    )

    evidence_state = (
        "VERIFIED_MULTI_UNIT_ARCHIVE_WITH_HEADLINE_CONSISTENT_SUBTOTAL"
        if footprint_ok and subtotal_ok and focus_ok and actions_ok
        else "MIXED_OR_UNRESOLVED"
    )
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "mission_products": atlas_total(footprint),
        "mission_bytes": mission_bytes,
        "mission_decimal_terabytes": mission_bytes / 1_000_000_000_000,
        "bundle_counts": bundle_counts,
        "bundle_bytes": bundle_bytes,
        "crew_collection_counts": crew_collection_counts,
        "crew_collection_bytes": crew_collection_bytes,
        "mission_bytes_excluding_processed_crew_collection": nonprocessed_bytes,
        "nonprocessed_decimal_gigabytes": nonprocessed_bytes / 1_000_000_000,
        "forward_look_product_records": atlas_total(focus),
        "forward_look_internal_ids": sorted(value for value in focus_ids if value),
        "forward_look_action_product_records": atlas_total(action_payload),
        "forward_look_action_internal_ids": len(action_ids),
        "forward_look_action_collection_counts": dict(action_collections),
        "forward_look_action_activity_counts": dict(action_activities),
        "verified_interpretation": spec["interpretation"]["verified"],
        "bounded_inference": spec["interpretation"]["inference"],
        "decision_use": spec["interpretation"]["decision_use"],
        "pixel_payload_bytes": receipt["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10d(root)
    names = load_json(root / "spec" / "stage10d.json")["hard_negatives"]
    mutations = {name: verify_stage10d(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 10D hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10D — Archive Unit Normalization",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Atlas mission data products: `{result['mission_products']:,}`",
        f"- Atlas mission product footprint: `{result['mission_decimal_terabytes']:.6f} TB`",
        f"- Footprint excluding processed crew-camera products: `{result['nonprocessed_decimal_gigabytes']:.6f} GB`",
        f"- Forward Look activity products / internal IDs: `{result['forward_look_product_records']}` / `{len(result['forward_look_internal_ids'])}`",
        f"- Two complete Forward Look actions products / internal IDs: `{result['forward_look_action_product_records']}` / `{result['forward_look_action_internal_ids']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "",
        "## Verified",
        "",
        result["verified_interpretation"],
        "",
        "## Bounded inference",
        "",
        result["bounded_inference"],
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
        result = verify_stage10d(args.root.resolve(), args.mutation)
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
