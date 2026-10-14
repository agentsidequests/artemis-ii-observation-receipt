#!/usr/bin/env python3
"""Verify the Stage 6A impact reframe without network access."""

from __future__ import annotations

import argparse
import copy
import csv
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
    spec: dict[str, Any], extracts: dict[str, Any], mutation: str | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = copy.deepcopy(spec)
    extracts = copy.deepcopy(extracts)
    if mutation is None:
        return spec, extracts
    if mutation == "promote_to_direct_100m_resolution":
        spec["derived_relation"]["interpretation"] = (
            "The crew directly resolved individual 100 m terrain features."
        )
    elif mutation == "treat_psychophysics_as_mission_validation":
        spec["derived_relation"]["mechanism_state"] = "MISSION_VALIDATED"
    elif mutation == "claim_public_priority":
        spec["candidates"][0]["novelty_classification"] = "NEW_DISCOVERY"
    elif mutation == "promote_single_case_to_general_human_superiority":
        spec["candidates"][0]["strongest_limit"] = (
            "This proves humans outperform instruments for lunar observation."
        )
    elif mutation == "restore_timing_as_public_lead":
        spec["expected_result"]["selected_candidate_id"] = (
            "event_specific_timing_anomaly"
        )
        spec["candidates"][0]["rank"] = 5
        spec["candidates"][4]["rank"] = 1
        spec["candidates"][4]["disposition"] = "CONTINUE_BOUNDED"
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec, extracts


def transcript_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_stage6a(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage6a.json")
    extracts_path = root / spec["source_evidence"]["source_extracts_path"]
    extracts = load_json(extracts_path)
    spec, extracts = apply_mutation(spec, extracts, mutation)

    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    extracts_hash = sha256_file(extracts_path)
    add_check(
        checks,
        errors,
        "source_extract_identity",
        extracts_hash == spec["source_evidence"]["source_extracts_sha256"],
        error="Source-extract identity does not match the frozen contract.",
        actual_sha256=extracts_hash,
        expected_sha256=spec["source_evidence"]["source_extracts_sha256"],
    )

    sources = {item["id"]: item for item in extracts["sources"]}
    required_ids = set(spec["source_evidence"]["required_source_ids"])
    add_check(
        checks,
        errors,
        "required_source_set",
        required_ids == set(sources),
        error="Required Stage 6A source set is incomplete or contains an unplanned source.",
        required=sorted(required_ids),
        actual=sorted(sources),
    )

    report_ids = {
        "preliminary_report_orientale_texture",
        "preliminary_report_human_resolution",
        "preliminary_report_multiscale_human_vision",
        "preliminary_report_color_limit",
    }
    report_hash_ok = all(
        sources[item_id].get("parent_sha256")
        == spec["source_evidence"]["expected_preliminary_report_sha256"]
        for item_id in report_ids
    )
    guide_hash_ok = (
        sources["data_user_guide_target_metadata_limit"].get("parent_sha256")
        == spec["source_evidence"]["expected_data_user_guide_sha256"]
    )
    add_check(
        checks,
        errors,
        "parent_document_identities",
        report_hash_ok and guide_hash_ok,
        error="A NASA parent-document identity differs from the frozen source identity.",
        preliminary_report=report_hash_ok,
        data_user_guide=guide_hash_ok,
    )

    transcript_path = root / spec["transcript_evidence"]["path"]
    actual_transcript_hash = sha256_file(transcript_path)
    add_check(
        checks,
        errors,
        "transcript_identity",
        actual_transcript_hash == spec["transcript_evidence"]["sha256"],
        error="The Orientale transcript does not match the frozen source identity.",
        actual_sha256=actual_transcript_hash,
        expected_sha256=spec["transcript_evidence"]["sha256"],
    )
    rows = transcript_rows(transcript_path)
    anchor_results: list[dict[str, Any]] = []
    for anchor in spec["transcript_evidence"]["anchors"]:
        matches = [
            row
            for row in rows
            if row["utc"] == anchor["utc"]
            and row["speaker"] == anchor["speaker"]
            and anchor["contains"] in row["text"]
        ]
        anchor_results.append({**anchor, "match_count": len(matches), "pass": len(matches) == 1})
    add_check(
        checks,
        errors,
        "exact_transcript_anchors",
        all(item["pass"] for item in anchor_results),
        error="One or more Orientale transcript anchors is absent or non-unique.",
        anchors=anchor_results,
    )

    relation = spec["derived_relation"]
    computed_minimum_ratio = (
        relation["nasa_unaided_object_resolution_minimum_km"]
        / relation["nominal_hectometer_scale_km"]
    )
    computed_maximum_ratio = (
        relation["nasa_unaided_object_resolution_maximum_km"]
        / relation["nominal_hectometer_scale_km"]
    )
    ratios_ok = (
        computed_minimum_ratio == relation["minimum_scale_ratio"] == 10.0
        and computed_maximum_ratio == relation["maximum_scale_ratio"] == 60.0
    )
    add_check(
        checks,
        errors,
        "aggregate_texture_scale_relation",
        ratios_ok,
        error="The frozen object-resolution-to-roughness-scale relation is not 10-to-60 times.",
        minimum_ratio=computed_minimum_ratio,
        maximum_ratio=computed_maximum_ratio,
    )
    interpretation_ok = (
        "aggregate regional texture" in relation["interpretation"]
        and "not direct resolution" in relation["interpretation"].lower()
        and "directly resolved" not in relation["interpretation"].lower()
    )
    add_check(
        checks,
        errors,
        "no_direct_subresolution_object_claim",
        interpretation_ok,
        error="The interpretation promotes aggregate texture into direct 100 m object vision.",
        interpretation=relation["interpretation"],
    )
    add_check(
        checks,
        errors,
        "mechanism_ceiling",
        relation["mechanism_state"] == "PLAUSIBLE_NOT_MISSION_VALIDATED",
        error="Primary psychophysics was promoted beyond mechanism plausibility.",
        mechanism_state=relation["mechanism_state"],
    )

    ranked = sorted(spec["candidates"], key=lambda item: item["rank"])
    unique_ranks = [item["rank"] for item in ranked] == list(
        range(1, len(ranked) + 1)
    )
    selected_id = spec["expected_result"]["selected_candidate_id"]
    selected = next((item for item in ranked if item["id"] == selected_id), None)
    selected_ok = bool(
        selected
        and selected["rank"] == 1
        and selected["id"] == "orientale_aggregate_texture_below_object_resolution"
        and selected["novelty_classification"] == "DIRECT_DERIVATION"
        and selected["disposition"] == "CONTINUE_BOUNDED"
    )
    add_check(
        checks,
        errors,
        "selected_candidate",
        unique_ranks and selected_ok,
        error="The candidate ranking does not preserve the bounded Orientale lead.",
        selected_candidate=selected,
        ranks=[{"rank": item["rank"], "id": item["id"]} for item in ranked],
    )

    timing = next(item for item in spec["candidates"] if item["id"] == "event_specific_timing_anomaly")
    metadata = next(
        item
        for item in spec["candidates"]
        if item["id"] == "archive_activity_and_target_metadata_friction"
    )
    alternatives_ok = (
        timing["rank"] == 5
        and timing["disposition"] == "DEMOTE_TO_SUPPORTING_CLUE"
        and metadata["disposition"] == "STOP_NO_DELTA"
    )
    add_check(
        checks,
        errors,
        "weaker_leads_bounded",
        alternatives_ok,
        error="A low-impact or already-published lead displaced the stronger bounded result.",
        timing_disposition=timing["disposition"],
        metadata_disposition=metadata["disposition"],
    )

    strongest_limit = selected["strongest_limit"] if selected else ""
    claim_ceiling = " ".join(spec["claim_ceiling"]).lower()
    boundary_ok = (
        "single mission case" in strongest_limit.lower()
        and "not a claimed scientific discovery" in claim_ceiling
        and "cannot establish general human superiority" in claim_ceiling
    )
    add_check(
        checks,
        errors,
        "claim_boundary",
        boundary_ok,
        error="The single-case, no-priority, or no-superiority boundary was lost.",
        strongest_limit=strongest_limit,
    )

    passed = not errors
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": passed,
        "evidence_state": spec["expected_result"]["evidence_state"] if passed else "REJECTED",
        "disposition": spec["expected_result"]["disposition"] if passed else "STOP_REJECTED",
        "selected_candidate_id": selected_id,
        "admitted_candidate_count": spec["expected_result"]["admitted_candidate_count"] if passed else 0,
        "network_bytes_in_verification": 0,
        "scale_relation": {
            "object_resolution_km": [
                relation["nasa_unaided_object_resolution_minimum_km"],
                relation["nasa_unaided_object_resolution_maximum_km"],
            ],
            "nominal_roughness_scale_km": relation["nominal_hectometer_scale_km"],
            "contributing_scale_ratio": [computed_minimum_ratio, computed_maximum_ratio],
            "interpretation": relation["interpretation"],
            "mechanism_state": relation["mechanism_state"],
        },
        "transcript_anchors": anchor_results,
        "candidate_ranking": ranked,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage6a(root)
    hard_negatives: dict[str, dict[str, Any]] = {}
    for mutation in load_json(root / "spec" / "stage6a.json")["hard_negatives"]:
        hard_negatives[mutation] = verify_stage6a(root, mutation)
    hard_negatives_pass = all(not result["pass"] for result in hard_negatives.values())
    return {
        **baseline,
        "hard_negatives": hard_negatives,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 6A hard negative was accepted."]),
    }


def render_markdown(verification: dict[str, Any]) -> str:
    ranking = verification["candidate_ranking"]
    ratio = verification["scale_relation"]
    lines = [
        "# Stage 6A — Impact Reframe Verification",
        "",
        f"- Result: `{'PASS' if verification['pass'] else 'FAIL'}`",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Disposition: `{verification['disposition']}`",
        f"- Selected lead: `{verification['selected_candidate_id']}`",
        f"- Scored network bytes: `{verification['network_bytes_in_verification']}`",
        "",
        "## Decision-changing result",
        "",
        "NASA's Orientale comparison says the crew-described regional texture appears in a LOLA-derived hectometer-scale roughness map but not in a Diviner-derived 1–2 m rock-abundance map. Joined to NASA's separate 1–6 km unaided object-resolution bound, the nominal contributing scale is 10–60 times smaller than the direct object-resolution floor.",
        "",
        "This supports an aggregate-texture interpretation, not direct vision of 100 m objects. It is a direct derivation from NASA's published components, not a claimed scientific discovery.",
        "",
        "## Scale relation",
        "",
        "| Quantity | Frozen value |",
        "| --- | ---: |",
        f"| NASA unaided object-resolution bound | {ratio['object_resolution_km'][0]:g}–{ratio['object_resolution_km'][1]:g} km |",
        f"| Nominal hectometer roughness scale | {ratio['nominal_roughness_scale_km']:g} km |",
        f"| Direct-resolution floor / contributing scale | {ratio['contributing_scale_ratio'][0]:g}–{ratio['contributing_scale_ratio'][1]:g}× |",
        "",
        f"Mechanism state: `{ratio['mechanism_state']}`.",
        "",
        "## Candidate ranking",
        "",
        "| Rank | Candidate | Impact | Novelty | Disposition |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for item in ranking:
        lines.append(
            f"| {item['rank']} | `{item['id']}` | {item['impact']} | `{item['novelty_classification']}` | `{item['disposition']}` |"
        )
    lines.extend(
        [
            "",
            "## Claim ceiling",
            "",
            *[f"- {item}" for item in verification["claim_ceiling"]],
            "",
            "## Next-step logic",
            "",
            f"**Recommended:** {verification['next_step_logic']['recommended']}",
            "",
            f"Why: {verification['next_step_logic']['why']}",
            "",
            f"Fallback: {verification['next_step_logic']['fallback']}",
            "",
            f"Stop: {verification['next_step_logic']['stop']}",
            "",
            "## Hard negatives",
            "",
        ]
    )
    for name, result in verification.get("hard_negatives", {}).items():
        lines.append(f"- `{name}`: {'REJECTED' if not result['pass'] else 'UNEXPECTEDLY ACCEPTED'}")
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
            "promote_to_direct_100m_resolution",
            "treat_psychophysics_as_mission_validation",
            "claim_public_priority",
            "promote_single_case_to_general_human_superiority",
            "restore_timing_as_public_lead",
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        payload = verify_with_mutations(args.root)
    else:
        payload = verify_stage6a(args.root, args.mutation)
    if args.json_output:
        write_json(args.json_output, payload)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_markdown(payload) if args.command == "verify" else json.dumps(payload, indent=2) + "\n"
        args.markdown_output.write_text(rendered, encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
