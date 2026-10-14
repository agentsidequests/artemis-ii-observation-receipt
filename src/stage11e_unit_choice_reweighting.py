#!/usr/bin/env python3
"""Verify Stage 11E's unit-choice reweighting canary."""

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
from stage10l_representation_compression import verify_stage10l
from stage11c_plan_realization_boundary import parse_utc
from stage11d_sunset_context_extension import verify_stage11d


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "context_is_complete_event": False,
        "scope": "verified_complete_action_cohort",
        "actual_sampler": "unspecified",
        "observed_model_bias": False,
        "causal_performance_effect": False,
        "products_are_wasteful_duplicates": False,
        "scientific_discovery_claimed": False,
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    if mutation == "call_context_complete_event":
        mutated["mutation_state"]["context_is_complete_event"] = True
    elif mutation == "generalize_to_entire_archive":
        mutated["mutation_state"]["scope"] = "entire_archive"
    elif mutation == "claim_actual_pipeline_samples_products_uniformly":
        mutated["mutation_state"]["actual_sampler"] = "uniform_products"
    elif mutation == "claim_actual_pipeline_samples_bytes_proportionally":
        mutated["mutation_state"]["actual_sampler"] = "byte_proportional"
    elif mutation == "claim_observed_model_bias":
        mutated["mutation_state"]["observed_model_bias"] = True
    elif mutation == "claim_reweighting_causal_performance_effect":
        mutated["mutation_state"]["causal_performance_effect"] = True
    elif mutation == "call_products_wasteful_duplicates":
        mutated["mutation_state"]["products_are_wasteful_duplicates"] = True
    elif mutation == "call_boundary_result_scientific_discovery":
        mutated["mutation_state"]["scientific_discovery_claimed"] = True
    elif mutation == "claim_novelty_or_priority":
        mutated["mutation_state"]["novelty_or_priority"] = True
    elif mutation == "open_pixels_during_reweighting_test":
        mutated["mutation_state"]["pixel_payload_bytes"] = 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def derive_context(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    stage11d = load_json(root / spec["source_contract"]["stage11d_spec_path"])
    start = parse_utc(stage11d["anchors"]["context_start"]["utc"])
    end = parse_utc(stage11d["anchors"]["context_continuation"]["utc"])
    actions: set[str] = set()
    captures: set[str] = set()
    products = 0
    collection_bytes: Counter[str] = Counter()
    with (root / spec["source_contract"]["relationship_manifest_path"]).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if start <= parse_utc(row["action_start_utc"]) < end:
                actions.add(row["action_id"])
                if row["collection_id"] == "data_source":
                    captures.add(row["capture_identity"])
                products += 1
                collection_bytes[row["collection_id"]] += int(row["archive_size_bytes"])
    return {
        "duration_seconds": (end - start).total_seconds(),
        "actions": len(actions), "exposures": len(captures), "products": products,
        "collection_bytes": dict(sorted(collection_bytes.items())),
        "total_bytes": sum(collection_bytes.values()),
    }


def derive_measures(context: dict[str, Any], cohort: dict[str, Any]) -> dict[str, float]:
    action_share = context["actions"] / cohort["actions"]
    product_share = context["products"] / cohort["products"]
    total_byte_share = context["total_bytes"] / cohort["total_bytes"]
    return {
        "action_share": action_share,
        "exposure_share": context["exposures"] / cohort["exposures"],
        "product_share": product_share,
        "source_byte_share": context["collection_bytes"]["data_source"] / cohort["collection_bytes"]["data_source"],
        "raw_byte_share": context["collection_bytes"]["data_raw"] / cohort["collection_bytes"]["data_raw"],
        "processed_byte_share": context["collection_bytes"]["data_processed"] / cohort["collection_bytes"]["data_processed"],
        "total_byte_share": total_byte_share,
        "product_weight_vs_action_weight": product_share / action_share,
        "byte_weight_vs_action_weight": total_byte_share / action_share,
        "product_minus_action_percentage_points": (product_share - action_share) * 100,
        "byte_minus_action_percentage_points": (total_byte_share - action_share) * 100,
    }


def verify_stage11e(root: Path, mutation: str | None = None, priors: tuple[dict[str, Any], dict[str, Any]] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11e.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    stage10l, stage11d = (verify_stage10l(root), verify_stage11d(root)) if priors is None else priors
    add_check(checks, errors, "complete_cohort_and_context_replay", stage10l["pass"] and stage11d["pass"],
              error="Stage 10L or Stage 11D no longer verifies.")
    context = derive_context(root, spec)
    cohort = {
        "actions": stage10l["complete_actions"], "exposures": stage10l["capture_identities"],
        "products": stage10l["products"], "collection_bytes": stage10l["collection_bytes"],
        "total_bytes": stage10l["total_bytes"],
    }
    context_ok = context == spec["frozen_context"]
    cohort_ok = cohort == spec["frozen_cohort"]
    add_check(checks, errors, "context_and_cohort_denominators", context_ok and cohort_ok,
              error="The frozen context or complete-cohort denominator changed.", context=context, cohort=cohort)
    measures = derive_measures(context, cohort)
    measures_ok = all(math.isclose(measures[key], expected, rel_tol=0.0, abs_tol=1e-15)
                      for key, expected in spec["frozen_measures"].items())
    add_check(checks, errors, "unit_choice_reweighting", measures_ok,
              error="The frozen unit-choice weighting measures changed.", measures=measures)
    state = spec["mutation_state"]
    boundary_ok = (
        not state["context_is_complete_event"]
        and state["scope"] == "verified_complete_action_cohort"
        and state["actual_sampler"] == "unspecified"
        and not any((state["observed_model_bias"], state["causal_performance_effect"],
                     state["products_are_wasteful_duplicates"], state["scientific_discovery_claimed"],
                     state["novelty_or_priority"]))
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited completeness, scope, sampler, model, value, science, novelty, or pixel claim was admitted.",
              mutation_state=state)
    evidence_state = "VERIFIED_UNIT_CHOICE_REWEIGHTING_CANARY" if measures_ok else "UNIT_CHOICE_REWEIGHTING_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "context": context,
        "cohort": cohort, "measures": measures, "disposition": spec["disposition"],
        "verified": "The conservative Sunset context is 13.204% of verified complete camera actions but 18.801% of products and 22.785% of bytes. Product and byte denominators therefore assign it more weight than an action denominator even before any pixel analysis.",
        "decision_use": "Treat sampling unit as an explicit model-design choice. A flat product table changes event weight as well as dependency structure; action or event balancing answers a different question.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    priors = (verify_stage10l(root), verify_stage11d(root))
    baseline = verify_stage11e(root, priors=priors)
    names = load_json(root / "spec/stage11e.json")["hard_negatives"]
    mutations = {name: verify_stage11e(root, name, priors=priors) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11E hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["measures"]
    lines = ["# Stage 11E — Unit-Choice Reweighting Canary", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Context share by actions: `{item['action_share']:.3%}`",
        f"- Context share by products: `{item['product_share']:.3%}`",
        f"- Context share by total bytes: `{item['total_byte_share']:.3%}`",
        f"- Product weight / action weight: `{item['product_weight_vs_action_weight']:.6f}×`",
        f"- Byte weight / action weight: `{item['byte_weight_vs_action_weight']:.6f}×`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`", "", "## Verified", "", result["verified"],
        "", "## Decision use", "", result["decision_use"], "", "## Claim ceiling", "", result["claim_ceiling"],
        "", "## Hard negatives", ""]
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11e(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
