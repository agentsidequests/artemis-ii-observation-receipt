#!/usr/bin/env python3
"""Verify Stage 10L's complete-action representation compression result."""

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
from stage10j_fractional_bracket_expansion import verify_stage10j


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "products_are_scientific_observations": False,
        "scope": "verified_complete_six_pattern_cohort",
        "actions_exhaustive": False,
        "representations_wasteful": False,
        "archive_quality_inferred": False,
        "snapshot_date_required": True,
        "global_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "count_products_as_independent_scientific_observations":
        state["products_are_scientific_observations"] = True
    elif mutation == "generalize_ratio_to_all_archive_products":
        state["scope"] = "all_archive_products"
    elif mutation == "call_six_pattern_action_cohort_exhaustive":
        state["actions_exhaustive"] = True
    elif mutation == "infer_representations_are_wasteful_duplicates":
        state["representations_wasteful"] = True
    elif mutation == "infer_archive_quality_from_ratio":
        state["archive_quality_inferred"] = True
    elif mutation == "omit_snapshot_date":
        state["snapshot_date_required"] = False
    elif mutation == "claim_global_priority":
        state["global_priority"] = True
    elif mutation == "open_pixels_for_count_reconciliation":
        state["pixel_payload_bytes"] = 1
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


def verify_stage10l(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10l.json"), mutation)
    contract, expected = spec["source_contract"], spec["frozen_observables"]
    receipt = load_json(root / contract["receipt_path"])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    failures = verify_receipt(root, receipt)
    source_ok = receipt.get("status") == "COMPLETED" and not failures and receipt.get("pixel_payload_bytes") == 0
    add_check(checks, errors, "source_identity", source_ok,
              error="A Stage 10L source, query, response, or dependency identity changed.", failures=failures)

    stage10j = verify_stage10j(root)
    cohort_ok = (
        stage10j.get("pass") is True
        and stage10j["complete_brackets"] == expected["complete_actions"]
        and stage10j["exposures_in_complete_brackets"] == expected["capture_identities"]
        and receipt.get("cohort", {}).get("complete_actions") == expected["complete_actions"]
        and receipt.get("cohort", {}).get("capture_identities") == expected["capture_identities"]
    )
    add_check(checks, errors, "complete_action_cohort_replay", cohort_ok,
              error="The Stage 10J complete-action cohort no longer matches Stage 10L.")

    collection_counts: Counter[str] = Counter()
    collection_bytes: Counter[str] = Counter()
    identity_collections: dict[str, list[str]] = defaultdict(list)
    responses = sorted((root / contract["atlas_batch_dir"]).glob("batch-*-response.json"))
    for path in responses:
        payload = load_json(path)
        for hit in payload.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            internal_ids = source.get("pds4_label", {}).get("msn:Mission_Information/msn:internal_id", [])
            if len(internal_ids) != 1:
                continue
            identity = str(internal_ids[0])
            collection = str(source.get("collection_id"))
            size = int(source.get("archive", {}).get("size", 0))
            identity_collections[identity].append(collection)
            collection_counts[collection] += 1
            collection_bytes[collection] += size
    expected_collections = set(expected["expected_collections"])
    parity_failures = {
        identity: values
        for identity, values in identity_collections.items()
        if len(values) != expected["expected_products_per_identity"] or set(values) != expected_collections
    }
    parity_ok = (
        len(responses) == receipt.get("cohort", {}).get("batches") == 77
        and len(identity_collections) == expected["capture_identities"]
        and not parity_failures
        and dict(collection_counts) == expected["expected_collections"]
        and sum(collection_counts.values()) == expected["expected_products"]
    )
    add_check(checks, errors, "per_identity_three_way_parity", parity_ok,
              error="The complete-action cohort no longer has exact source/raw/processed parity.",
              batches=len(responses), identities=len(identity_collections), products=sum(collection_counts.values()),
              collections=dict(collection_counts), parity_failures=len(parity_failures))

    bytes_ok = dict(collection_bytes) == expected["expected_collection_bytes"] and sum(collection_bytes.values()) == expected["expected_total_bytes"]
    add_check(checks, errors, "cohort_product_footprint", bytes_ok,
              error="The complete-action cohort's product footprint changed.",
              collection_bytes=dict(collection_bytes), total_bytes=sum(collection_bytes.values()))

    products_per_action = expected["expected_products"] / expected["complete_actions"]
    exposures_per_action = expected["capture_identities"] / expected["complete_actions"]
    ratio_ok = products_per_action == expected["products_per_action"] and exposures_per_action == expected["exposures_per_action"]
    add_check(checks, errors, "exact_denominator_ratios", ratio_ok,
              error="The frozen exposure/action or product/action ratio changed.",
              exposures_per_action=exposures_per_action, products_per_action=products_per_action)

    route = receipt.get("route_recovery", {})
    route_ok = route == {"initial_failure": "HTTP_403_LARGE_REQUEST", "failure_class": "SURFACE_PREREQUISITE_MISSING", "fallback": "same_endpoint_bounded_batches"}
    add_check(checks, errors, "bounded_route_recovery", route_ok,
              error="The Stage 10L transport failure or bounded fallback was not preserved.", route_recovery=route)

    state = spec["mutation_state"]
    boundary_ok = (
        not state["products_are_scientific_observations"]
        and state["scope"] == "verified_complete_six_pattern_cohort"
        and not state["actions_exhaustive"]
        and not state["representations_wasteful"]
        and not state["archive_quality_inferred"]
        and state["snapshot_date_required"]
        and not state["global_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited independence, scope, completeness, value, quality, novelty, date, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_COMPLETE_ACTION_REPRESENTATION_COMPRESSION" if all((cohort_ok, parity_ok, bytes_ok, ratio_ok)) else "REPRESENTATION_COMPRESSION_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "complete_actions": expected["complete_actions"], "capture_identities": len(identity_collections),
        "products": sum(collection_counts.values()), "collection_counts": dict(collection_counts),
        "collection_bytes": dict(collection_bytes), "total_bytes": sum(collection_bytes.values()),
        "exposures_per_action": exposures_per_action, "products_per_action": products_per_action,
        "verified": "Every one of the 7,606 exposure identities in the verified complete six-pattern cohort has exactly one source, one raw, and one processed Atlas product. The cohort therefore contains 22,818 products representing 2,166 complete actions: 3.511542 exposures and 10.534626 products per action.",
        "decision_use": "This is the strongest exact denominator-collision demonstration: in the dated complete-action cohort, a product count is 10.53 times the reconstructed physical-action count. It is a unit conversion, not an archive-wide inflation, quality, duplication-value, or scientific-evidence claim.",
        "pixel_payload_bytes": receipt["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10l(root)
    names = load_json(root / "spec/stage10l.json")["hard_negatives"]
    mutations = {name: verify_stage10l(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10L hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10L — Complete-Action Representation Compression", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Products / exposure identities / complete actions: `{result['products']:,}` / `{result['capture_identities']:,}` / `{result['complete_actions']:,}`",
        f"- Products per complete action: `{result['products_per_action']:.6f}`",
        f"- Cohort product footprint: `{result['total_bytes'] / 1_000_000_000:.9f} GB`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10l(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
