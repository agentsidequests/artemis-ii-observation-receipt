#!/usr/bin/env python3
"""Verify the Stage 6B specialist pressure-test correction offline."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def add_check(
    checks: list[dict[str, Any]],
    errors: list[str],
    check_id: str,
    passed: bool,
    *,
    error: str,
    **details: Any,
) -> None:
    checks.append({"id": check_id, "pass": passed, **details})
    if not passed:
        errors.append(error)


def apply_mutation(
    spec: dict[str, Any], mutation: str | None
) -> dict[str, Any]:
    spec = copy.deepcopy(spec)
    if mutation is None:
        return spec
    if mutation == "equate_baseline_with_visible_object_size":
        spec["distinctions"]["claim"] = (
            "The roughness measurement baseline is the size of the object the crew saw."
        )
    elif mutation == "promote_rimae_case_to_global_acuity_floor":
        spec["adjudication"]["rimae_resolution_status"] = "GLOBAL_ACUITY_FLOOR"
    elif mutation == "transfer_hair_texture_mechanism_to_lunar_terrain":
        spec["adjudication"]["psychophysics_transfer_status"] = (
            "VALIDATED_ARTEMIS_MECHANISM"
        )
    elif mutation == "claim_nasa_orientale_component_as_new":
        spec["adjudication"]["nasa_orientale_component_status"] = (
            "NEW_TESTBED_DISCOVERY"
        )
    elif mutation == "retain_10_60x_as_public_headline":
        spec["adjudication"]["public_lead_status"] = "PUBLISH_10_60X_HEADLINE"
    elif mutation == "use_orientale_as_both_prior_and_held_out_test":
        spec["replacement_candidate"]["treatment"] = (
            "Train on Orientale and evaluate the same Orientale correspondence."
        )
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec


def verify_stage6b(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage6b.json"), mutation)
    extracts_path = root / spec["source_evidence"]["path"]
    extracts = load_json(extracts_path)

    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    actual_extract_hash = sha256_file(extracts_path)
    add_check(
        checks,
        errors,
        "source_extract_identity",
        actual_extract_hash == spec["source_evidence"]["sha256"],
        error="Specialist source-extract identity does not match the frozen contract.",
        actual_sha256=actual_extract_hash,
        expected_sha256=spec["source_evidence"]["sha256"],
    )

    sources = {item["id"]: item for item in extracts["sources"]}
    required = set(spec["source_evidence"]["required_source_ids"])
    add_check(
        checks,
        errors,
        "required_source_set",
        set(sources) == required,
        error="The specialist source set is incomplete or contains an unplanned source.",
        required=sorted(required),
        actual=sorted(sources),
    )

    report_hash = spec["source_evidence"]["expected_preliminary_report_sha256"]
    report_sources = ("nasa_orientale_comparison", "nasa_resolution_case_scope")
    report_identity_ok = all(
        sources[source_id].get("parent_sha256") == report_hash
        for source_id in report_sources
    )
    add_check(
        checks,
        errors,
        "nasa_report_identity",
        report_identity_ok,
        error="A decision-bearing NASA report extract has the wrong parent identity.",
        expected_sha256=report_hash,
    )

    distinctions = spec["distinctions"]
    distinctions_ok = (
        "horizontal separation" in distinctions["roughness_measurement_baseline"]
        and "regional window" in distinctions["roughness_map_support"]
        and "not established by the roughness baseline"
        in distinctions["visible_pattern_extent"]
        and "particular range" in distinctions["recognized_object_size"]
        and "not interchangeable" in distinctions["claim"]
    )
    add_check(
        checks,
        errors,
        "non_commensurate_quantities",
        distinctions_ok,
        error="Measurement baseline, map support, visible pattern, and recognized object size were conflated.",
        distinctions=distinctions,
    )

    adjudication = spec["adjudication"]
    expected_adjudication = {
        "stage6a_ratio_arithmetic": "CORRECT",
        "stage6a_ratio_commensurability": "REJECTED_UNLIKE_QUANTITIES",
        "stage6a_ratio_explanatory_status": "NON_DIAGNOSTIC",
        "nasa_orientale_component_status": "ALREADY_PUBLISHED_QUALITATIVE_CONCORDANCE",
        "rimae_resolution_status": "TASK_SPECIFIC_BOUND_NOT_GLOBAL_FLOOR",
        "psychophysics_transfer_status": "PLAUSIBILITY_ONLY_NO_ARTEMIS_VALIDATION",
        "public_lead_status": "STOP_10_60X_HEADLINE",
    }
    adjudication_ok = adjudication == expected_adjudication
    add_check(
        checks,
        errors,
        "specialist_adjudication",
        adjudication_ok,
        error="The pressure-test correction or one of its transfer limits was lost.",
        adjudication=adjudication,
    )

    replacement = spec["replacement_candidate"]
    treatment = replacement["treatment"].lower()
    oracle = replacement["oracle"].lower()
    replacement_ok = (
        replacement["id"] == "held_out_semantic_cross_instrument_concordance"
        and replacement["state"] == "BOUNDED_TEST_CANDIDATE"
        and "blind-code" in treatment
        and "reserve orientale as prior evidence rather than evaluation data" in treatment
        and all(
            layer in treatment
            for layer in ("lola roughness", "diviner rock abundance", "topography", "albedo")
        )
        and "viewing geometry" in oracle
        and "optical tool" in oracle
        and "novelty_unestablished" in replacement["novelty_ceiling"].lower()
    )
    add_check(
        checks,
        errors,
        "held_out_replacement_test",
        replacement_ok,
        error="The replacement test is not blind, held out, controlled, or novelty-bounded.",
        replacement_candidate=replacement,
    )

    claim_text = " ".join(spec["claim_ceiling"]).lower()
    ceiling_ok = (
        "numerically correct" in claim_text
        and "not a validated measure of perceptual reach" in claim_text
        and "does not show" in claim_text
        and "does not validate" in claim_text
        and "no such result exists yet" in claim_text
    )
    add_check(
        checks,
        errors,
        "claim_ceiling",
        ceiling_ok,
        error="The corrected claim ceiling is incomplete.",
        claim_ceiling=spec["claim_ceiling"],
    )

    expected = spec["expected_result"]
    decision_ok = (
        expected["evidence_state"] == "VERIFIED_SPECIALIST_PRESSURE_CORRECTION"
        and expected["disposition"]
        == "STOP_QUANTIFIED_HEADLINE_CONTINUE_BOUNDED_TEST"
        and expected["retired_claim"]
        == "orientale_aggregate_texture_10_60x_below_object_resolution"
        and expected["selected_candidate_id"]
        == "held_out_semantic_cross_instrument_concordance"
    )
    add_check(
        checks,
        errors,
        "decision",
        decision_ok,
        error="The corrected stop or replacement candidate changed.",
        expected_result=expected,
    )

    passed = not errors
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": passed,
        "evidence_state": expected["evidence_state"] if passed else "REJECTED",
        "disposition": expected["disposition"] if passed else "STOP_REJECTED",
        "retired_claim": expected["retired_claim"],
        "selected_candidate_id": expected["selected_candidate_id"],
        "network_bytes_in_verification": 0,
        "adjudication": adjudication,
        "distinctions": distinctions,
        "replacement_candidate": replacement,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage6b(root)
    mutations = load_json(root / "spec" / "stage6b.json")["hard_negatives"]
    hard_negatives = {name: verify_stage6b(root, name) for name in mutations}
    hard_negatives_pass = all(not result["pass"] for result in hard_negatives.values())
    return {
        **baseline,
        "hard_negatives": hard_negatives,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 6B hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 6B — Specialist Literature Pressure Test",
        "",
        f"- Result: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Retired claim: `{result['retired_claim']}`",
        f"- Replacement candidate: `{result['selected_candidate_id']}`",
        f"- Scored network bytes: `{result['network_bytes_in_verification']}`",
        "",
        "## Decision-changing correction",
        "",
        "The Stage 6A 10–60× arithmetic is numerically correct but scientifically non-diagnostic. It divides a nominal LOLA roughness measurement baseline by a task-specific object-recognition bound. Specialist sources show that those quantities have different meanings and cannot measure the crew's perceptual reach.",
        "",
        "LOLA computes roughness over short horizontal baselines and aggregates many measurements into regional windows. The crew could see a large regional pattern correlated with short-baseline roughness without detecting individual features at the roughness baseline. NASA's 1–6 km range comes from one rille-recognition case whose visibility also depended on range, angle, illumination, contrast, and competing visual stimuli.",
        "",
        "The subresolution texture paper remains mechanism plausibility for controlled hair-like line textures only. It does not validate lunar-terrain perception.",
        "",
        "## Adjudication",
        "",
    ]
    for key, value in result["adjudication"].items():
        lines.append(f"- `{key}`: `{value}`")
    replacement = result["replacement_candidate"]
    lines.extend(
        [
            "",
            "## Replacement bounded test",
            "",
            f"**Question:** {replacement['question']}",
            "",
            f"**Treatment:** {replacement['treatment']}",
            "",
            f"**Oracle:** {replacement['oracle']}",
            "",
            f"**Hard negative:** {replacement['hard_negative']}",
            "",
            f"**Novelty ceiling:** `{replacement['novelty_ceiling']}`",
            "",
            "## Claim ceiling",
            "",
            *[f"- {item}" for item in result["claim_ceiling"]],
            "",
            "## Next-step logic",
            "",
            f"**Recommended:** {result['next_step_logic']['recommended']}",
            "",
            f"Why: {result['next_step_logic']['why']}",
            "",
            f"Fallback: {result['next_step_logic']['fallback']}",
            "",
            f"Stop: {result['next_step_logic']['stop']}",
            "",
            "## Hard negatives",
            "",
        ]
    )
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
    parser.add_argument(
        "--mutation",
        choices=(
            "equate_baseline_with_visible_object_size",
            "promote_rimae_case_to_global_acuity_floor",
            "transfer_hair_texture_mechanism_to_lunar_terrain",
            "claim_nasa_orientale_component_as_new",
            "retain_10_60x_as_public_headline",
            "use_orientale_as_both_prior_and_held_out_test",
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        result = verify_with_mutations(args.root)
    else:
        result = verify_stage6b(args.root, args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n"
        args.markdown_output.write_text(rendered, encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
