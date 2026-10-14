#!/usr/bin/env python3
"""Verify the Stage 9A archive-wide opportunity selection gate."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file


EXPECTED_GATES = [
    "question_not_already_answered",
    "current_archive_supports_minimum_test",
    "independent_discriminator_available",
    "does_not_reopen_closed_lane",
    "pass_or_fail_changes_decision",
    "bounded_complete_burden",
]
EXPECTED_COMPARATORS = {"truthful_operational_synthesis", "deliberate_stop"}
REQUIRED_EXCLUSIONS = {
    "Glushko-Ohm static reflectance",
    "Glushko-Ohm camera-native rescoring",
    "bulk archive analysis without an admitted question",
}
SELECTED_ID = "pre_earthrise_gray_feature_discrimination"
SELECTED_DISPOSITION = "ADMIT_NO_PIXEL_SOURCE_CONTROL_GATE"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


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
    spec: dict[str, Any],
    inventory: dict[str, Any],
    source_screen: str,
    mutation: str | None,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    spec = copy.deepcopy(spec)
    inventory = copy.deepcopy(inventory)
    if mutation is None:
        return spec, inventory, source_screen

    candidates = {item["id"]: item for item in inventory["candidates"]}
    if mutation == "promote_potential_gray_feature_to_confirmed_lunar_dust":
        spec["expected_result"]["claim_ceiling"] = (
            "The pre-Earthrise gray feature confirms lofted lunar dust."
        )
    elif mutation == "treat_search_absence_as_public_priority":
        source_screen = source_screen.replace(
            "that is `NOVELTY_UNESTABLISHED`, not proof of priority",
            "that proves this is an unpublished public scientific priority",
        )
    elif mutation == "select_already_published_corona_corroboration":
        inventory["selected_candidate"] = "solar_corona_pulsation_corroboration"
        inventory["selected_disposition"] = "ADMIT_NO_PIXEL_SOURCE_CONTROL_GATE"
    elif mutation == "reopen_closed_glushko_ohm_lane":
        spec["search_contract"]["excluded_lanes"].remove(
            "Glushko-Ohm camera-native rescoring"
        )
    elif mutation == "open_new_candidate_pixels_before_a_source_control_contract":
        spec["access_boundary"]["new_candidate_pixel_bytes"] = 1
        spec["next_step_logic"]["recommended"] = (
            "Open and score all candidate pixels before freezing sources or controls."
        )
    elif mutation == "omit_truthful_synthesis_and_deliberate_stop_comparators":
        inventory["comparators"] = []
    elif mutation == (
        "treat_external_camera_non_detection_as_a_refutation_without_sensitivity_equivalence"
    ):
        candidates[SELECTED_ID]["strongest_counterevidence"] = (
            "A blank external-camera frame refutes the crew observation."
        )
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec, inventory, source_screen


def verify_stage9a(root: Path, mutation: str | None = None) -> dict[str, Any]:
    raw_spec = load_json(root / "spec" / "stage9a.json")
    inventory_path = root / raw_spec["candidate_inventory_path"]
    source_path = root / raw_spec["source_screen_path"]
    raw_inventory = load_json(inventory_path)
    raw_source_screen = source_path.read_text(encoding="utf-8-sig")
    spec, inventory, source_screen = apply_mutation(
        raw_spec, raw_inventory, raw_source_screen, mutation
    )
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    identity_ok = (
        sha256_file(inventory_path) == raw_spec["candidate_inventory_sha256"]
        and sha256_file(source_path) == raw_spec["source_screen_sha256"]
    )
    add_check(
        checks,
        errors,
        "frozen_evidence_identity",
        identity_ok,
        error="The Stage 9A candidate inventory or source screen changed.",
    )

    candidates = inventory.get("candidates", [])
    candidate_ids = [item.get("id") for item in candidates]
    ranks = [item.get("rank") for item in candidates]
    gate_shape_ok = (
        spec.get("gate_fields") == EXPECTED_GATES
        and bool(candidates)
        and len(candidate_ids) == len(set(candidate_ids))
        and ranks == list(range(1, len(candidates) + 1))
        and all(list(item.get("gates", {})) == EXPECTED_GATES for item in candidates)
        and all(
            isinstance(value, bool)
            for item in candidates
            for value in item.get("gates", {}).values()
        )
    )
    add_check(
        checks,
        errors,
        "candidate_schema_and_rank_order",
        gate_shape_ok,
        error="Candidate ranks, identities, or gate fields are incomplete or changed.",
        candidate_count=len(candidates),
    )

    comparator_ids = {item.get("id") for item in inventory.get("comparators", [])}
    comparator_ok = comparator_ids == EXPECTED_COMPARATORS
    add_check(
        checks,
        errors,
        "direct_baseline_comparators",
        comparator_ok,
        error="Truthful synthesis and deliberate stop were not both compared.",
        comparator_ids=sorted(comparator_ids),
    )

    excluded = set(spec.get("search_contract", {}).get("excluded_lanes", []))
    exclusions_ok = REQUIRED_EXCLUSIONS.issubset(excluded)
    add_check(
        checks,
        errors,
        "closed_lanes_remain_closed",
        exclusions_ok,
        error="A closed or unbounded lane was reopened during opportunity selection.",
        required_exclusions=sorted(REQUIRED_EXCLUSIONS),
    )

    admitted = [
        item
        for item in candidates
        if item.get("gates")
        and all(item["gates"].get(field) is True for field in EXPECTED_GATES)
    ]
    admitted_ids = [item["id"] for item in admitted]
    ranked_admitted_ids = [
        item["id"] for item in sorted(admitted, key=lambda item: item["rank"])
    ]
    selected_id = inventory.get("selected_candidate")
    selected_disposition = inventory.get("selected_disposition")
    selection_ok = (
        ranked_admitted_ids[:1] == [SELECTED_ID]
        and selected_id == SELECTED_ID
        and selected_disposition == SELECTED_DISPOSITION
        and spec.get("expected_result", {}).get("selected_candidate") == SELECTED_ID
        and spec.get("expected_result", {}).get("disposition")
        == SELECTED_DISPOSITION
    )
    add_check(
        checks,
        errors,
        "admission_and_selection",
        selection_ok,
        error="The selected opportunity is not the frozen highest-ranked admitted candidate.",
        admitted_ids=ranked_admitted_ids,
        selected_candidate=selected_id,
    )

    source_lower = source_screen.lower()
    source_anchors = (
        "23:22:39 utc",
        "23:22:14",
        "23:22:44",
        "23:23:14 utc",
        "no lofted dust or exospheric glow was definitively detected",
        "novelty_unestablished",
        "not proof of priority",
        "not assumed to have equivalent sensitivity or viewpoint",
        "spice bundle is delayed",
    )
    source_ok = all(anchor in source_lower for anchor in source_anchors)
    add_check(
        checks,
        errors,
        "primary_source_and_project_anchors",
        source_ok,
        error="A decision-bearing source, time, novelty, or sensitivity boundary is missing.",
    )

    access_boundary = spec.get("access_boundary", {})
    no_pixel_access = access_boundary == {
        "new_candidate_pixel_bytes": 0,
        "new_candidate_label_bytes": 0,
        "existing_stage2a_pixels_reused_for_scoring": False,
        "retained_stage9a_evidence_types": [
            "primary-source screen",
            "candidate inventory",
        ],
    }
    add_check(
        checks,
        errors,
        "no_new_candidate_pixel_access",
        no_pixel_access,
        error="Stage 9A accessed candidate pixels or labels before its source/control gate.",
        access_boundary=access_boundary,
    )

    selected = next((item for item in candidates if item.get("id") == SELECTED_ID), {})
    counterevidence = selected.get("strongest_counterevidence", "").lower()
    sensitivity_ok = all(
        phrase in counterevidence
        for phrase in ("different viewpoint", "sensitivity", "non-identifying")
    )
    add_check(
        checks,
        errors,
        "external_camera_sensitivity_boundary",
        sensitivity_ok,
        error="External-camera non-detection was promoted without sensitivity equivalence.",
        strongest_counterevidence=selected.get("strongest_counterevidence"),
    )

    claim_ceiling = spec.get("expected_result", {}).get("claim_ceiling", "")
    ceiling_lower = claim_ceiling.lower()
    ceiling_ok = all(
        phrase in ceiling_lower
        for phrase in (
            "strongest untested archive candidate",
            "not a lunar-dust detection",
            "horizon-glow confirmation",
            "public scientific finding",
        )
    )
    add_check(
        checks,
        errors,
        "claim_ceiling",
        ceiling_ok,
        error="Question selection was promoted into a dust or public-science claim.",
        claim_ceiling=claim_ceiling,
    )

    next_logic = spec.get("next_step_logic", {})
    recommended = next_logic.get("recommended", "").lower()
    next_step_ok = all(
        phrase in recommended
        for phrase in (
            "no-new-pixel source-and-control gate",
            "exact crew and vehicle products",
            "minimum sensitivity comparison",
            "before opening any new pixels",
        )
    ) and "source_control_insufficient" in next_logic.get("fail", "").lower()
    add_check(
        checks,
        errors,
        "no_new_pixel_next_step",
        next_step_ok,
        error="The next step bypasses the frozen source/control gate or fail-closed state.",
    )

    evidence_state = (
        spec.get("expected_result", {}).get("evidence_state")
        if not errors
        else "REJECTED"
    )
    disposition = selected_disposition if not errors else "REJECTED"
    return {
        "testbed_id": spec.get("testbed_id"),
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": evidence_state,
        "disposition": disposition,
        "selected_candidate": selected_id,
        "admitted_candidate_ids": ranked_admitted_ids,
        "candidate_count": len(candidates),
        "comparator_ids": sorted(comparator_ids),
        "new_candidate_pixel_bytes": access_boundary.get("new_candidate_pixel_bytes"),
        "claim_ceiling": claim_ceiling,
        "next_step_logic": next_logic,
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage9a(root)
    mutation_names = load_json(root / "spec" / "stage9a.json")["hard_negatives"]
    mutations = {name: verify_stage9a(root, name) for name in mutation_names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 9A hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 9A — Archive-Wide Opportunity Selection",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Selected candidate: `{result['selected_candidate']}`",
        f"- New candidate-pixel bytes opened: `{result['new_candidate_pixel_bytes']}`",
        "",
        "## Result",
        "",
        "The strongest bounded, currently testable opportunity is the disputed gray feature reported at `23:22:39 UTC` immediately before/during Earthrise. NASA leaves the episode unresolved, while the repository already contains a fixed-camera sequence that brackets the utterance. The event therefore beats both a synthesis-only continuation and deliberate stop—but only as a question selected for a source-and-control gate.",
        "",
        "This is not a dust detection. Stage 9A opened no new candidate pixels and makes no claim that an external camera can reproduce or refute the crew view without viewpoint and sensitivity equivalence.",
        "",
        "## Admitted candidates",
        "",
    ]
    for candidate_id in result["admitted_candidate_ids"]:
        suffix = " — selected" if candidate_id == result["selected_candidate"] else " — held"
        lines.append(f"- `{candidate_id}`{suffix}")
    lines.extend(
        [
            "",
            "## Claim ceiling",
            "",
            result["claim_ceiling"],
            "",
            "## Hard negatives",
            "",
        ]
    )
    for name, mutation_result in result.get("hard_negatives", {}).items():
        verdict = "REJECTED" if not mutation_result["pass"] else "UNEXPECTEDLY ACCEPTED"
        lines.append(f"- `{name}`: {verdict}")
    lines.extend(
        [
            "",
            "## Next-step logic",
            "",
            f"- Recommended: {result['next_step_logic']['recommended']}",
            f"- Pass: {result['next_step_logic']['pass']}",
            f"- Fail: {result['next_step_logic']['fail']}",
            f"- Recheck trigger: {result['next_step_logic']['recheck_trigger']}",
            "",
        ]
    )
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
        result = verify_stage9a(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(
            render_markdown(result)
            if args.command == "verify"
            else json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
