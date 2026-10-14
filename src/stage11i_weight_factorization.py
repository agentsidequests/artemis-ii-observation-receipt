#!/usr/bin/env python3
"""Verify Stage 11I's implicit-weight factorization."""

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
from stage11h_protocol_context_alignment import verify_stage11h


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "representation_multiplier_causes_relative_protocol_weight": False,
        "archive_representations_are_duplicates": False,
        "discard_representations_or_brackets": False,
        "representation_scientific_value_ranked": False,
        "actual_sampler": "unspecified",
        "observed_model_bias": False,
        "one_universal_correct_weighting": False,
        "scope": "verified_complete_action_cohort",
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "claim_representation_multiplier_causes_relative_protocol_weight": ("representation_multiplier_causes_relative_protocol_weight", True),
        "call_archive_representations_duplicates": ("archive_representations_are_duplicates", True),
        "recommend_discarding_representations_or_brackets": ("discard_representations_or_brackets", True),
        "rank_representation_scientific_value": ("representation_scientific_value_ranked", True),
        "claim_actual_sampler_is_uniform_products": ("actual_sampler", "uniform_products"),
        "claim_observed_model_bias": ("observed_model_bias", True),
        "claim_one_universal_correct_weighting": ("one_universal_correct_weighting", True),
        "generalize_to_unadmitted_archive_records": ("scope", "entire_archive"),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels_during_factorization": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def derive(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    by_action: dict[str, set[str]] = defaultdict(set)
    by_capture: dict[str, set[str]] = defaultdict(set)
    product_rows = 0
    with (root / spec["source_contract"]["relationship_manifest_path"]).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            product_rows += 1
            by_action[row["action_id"]].add(row["capture_identity"])
            by_capture[row["capture_identity"]].add(row["collection_id"])
    action_counts = Counter(len(captures) for captures in by_action.values())
    representation_counts = {len(collections) for collections in by_capture.values()}
    if representation_counts != {3}:
        raise ValueError(f"Representation parity changed: {representation_counts}")
    five_captures = action_counts[5] * 5
    action_total = len(by_action)
    capture_total = len(by_capture)
    representation_multiplier = next(iter(representation_counts))
    return {
        "complete_actions": action_total,
        "three_exposure_actions": action_counts[3],
        "five_exposure_actions": action_counts[5],
        "capture_identities": capture_total,
        "archive_products": product_rows,
        "representations_per_capture": representation_multiplier,
        "three_exposure_source_rows_per_action": 3,
        "five_exposure_source_rows_per_action": 5,
        "three_exposure_products_per_action": 3 * representation_multiplier,
        "five_exposure_products_per_action": 5 * representation_multiplier,
        "source_row_weight_ratio_five_vs_three": 5 / 3,
        "product_weight_ratio_five_vs_three": (5 * representation_multiplier) / (3 * representation_multiplier),
        "representation_multiplier_changes_relative_protocol_ratio": not math.isclose(
            5 / 3, (5 * representation_multiplier) / (3 * representation_multiplier), rel_tol=0.0, abs_tol=1e-12
        ),
        "five_exposure_action_share": action_counts[5] / action_total,
        "five_exposure_capture_and_product_share": five_captures / capture_total,
        "five_exposure_share_amplification": (five_captures / capture_total) / (action_counts[5] / action_total),
    }


def verify_stage11i(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11i.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    prior = verify_stage11h(root) if prior is None else prior
    add_check(checks, errors, "protocol_context_alignment_replays", prior["pass"], error="Stage 11H no longer verifies.")
    metrics = derive(root, spec)
    metrics_ok = all(
        math.isclose(float(metrics[key]), float(expected), rel_tol=0.0, abs_tol=1e-12)
        if isinstance(expected, float) else metrics[key] == expected
        for key, expected in spec["frozen_observables"].items()
    )
    add_check(checks, errors, "implicit_weight_factorization", metrics_ok,
              error="The frozen implicit-weight factorization changed.", metrics=metrics)
    arithmetic_ok = (
        metrics["capture_identities"] * metrics["representations_per_capture"] == metrics["archive_products"]
        and metrics["three_exposure_actions"] * 9 + metrics["five_exposure_actions"] * 15 == metrics["archive_products"]
    )
    add_check(checks, errors, "factorized_product_identity", arithmetic_ok,
              error="The product-count factorization no longer closes exactly.")
    state = spec["mutation_state"]
    boundary_ok = (
        not any((state["representation_multiplier_causes_relative_protocol_weight"],
                 state["archive_representations_are_duplicates"], state["discard_representations_or_brackets"],
                 state["representation_scientific_value_ranked"], state["observed_model_bias"],
                 state["one_universal_correct_weighting"], state["novelty_or_priority"]))
        and state["actual_sampler"] == "unspecified"
        and state["scope"] == "verified_complete_action_cohort"
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited representation, deletion, value, sampler, model, weighting, scope, novelty, or pixel claim was admitted.",
              mutation_state=state)
    evidence_state = "VERIFIED_IMPLICIT_WEIGHT_FACTORIZATION" if metrics_ok and arithmetic_ok else "IMPLICIT_WEIGHT_FACTORIZATION_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "metrics": metrics,
        "disposition": spec["disposition"],
        "verified": "The representation layer uniformly triples admitted capture rows without changing the five-versus-three action-weight ratio. Variable bracket length, not constant representation parity, creates relative action reweighting in product counts.",
        "decision_use": "Separate absolute row multiplication from relative sample weighting: preserve all representations and exposures, then choose the outer action, segment, or event estimand explicitly.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage11h(root)
    baseline = verify_stage11i(root, prior=prior)
    names = load_json(root / "spec/stage11i.json")["hard_negatives"]
    mutations = {name: verify_stage11i(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11I hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["metrics"]
    lines = ["# Stage 11I — Implicit-Weight Factorization", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Actions / captures / products: `{item['complete_actions']}` / `{item['capture_identities']}` / `{item['archive_products']}`",
        f"- Representation multiplier: `{item['representations_per_capture']}×` for every admitted capture",
        f"- Three- / five-exposure products per action: `{item['three_exposure_products_per_action']}` / `{item['five_exposure_products_per_action']}`",
        f"- Five / three relative weight before and after representation multiplication: `{item['source_row_weight_ratio_five_vs_three']:.6f}×` / `{item['product_weight_ratio_five_vs_three']:.6f}×`",
        f"- Five-exposure action / product shares: `{item['five_exposure_action_share']:.3%}` / `{item['five_exposure_capture_and_product_share']:.3%}`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage11i(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
