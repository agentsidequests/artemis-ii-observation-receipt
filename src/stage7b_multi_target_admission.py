#!/usr/bin/env python3
"""Verify the transcript-only Stage 7B multi-target admission gate."""

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


def transcript_candidate_is_present(root: Path, candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    transcript_path = root / candidate["transcript_path"]
    if not transcript_path.is_file():
        return [f"Missing transcript for {candidate['id']}: {candidate['transcript_path']}"]
    if sha256_file(transcript_path) != candidate["transcript_sha256"]:
        return [f"Transcript identity changed for {candidate['id']}"]

    with transcript_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected_text: list[str] = []
    for row_number in candidate["rows"]:
        index = row_number - 2
        if index < 0 or index >= len(rows):
            errors.append(f"Transcript row {row_number} is absent for {candidate['id']}")
            continue
        selected_text.append(rows[index]["text"])
    joined = " ".join(selected_text).lower()
    for anchor in candidate["anchors"]:
        if anchor.lower() not in joined:
            errors.append(f"Missing anchor for {candidate['id']}: {anchor}")

    supporting_path = candidate.get("supporting_transcript_path")
    if supporting_path:
        path = root / supporting_path
        if not path.is_file() or sha256_file(path) != candidate["supporting_transcript_sha256"]:
            errors.append(f"Supporting transcript identity changed for {candidate['id']}")
    return errors


def qualifies_same_endpoint(
    candidate: dict[str, Any], shared_endpoint: str
) -> bool:
    targets = {target.lower() for target in candidate["targets"]}
    return all(
        (
            candidate["endpoint"] == shared_endpoint,
            bool(candidate["direction"]),
            candidate["direct_comparison"] is True,
            candidate["named_localization"] is True,
            candidate["morphology_matched"] is True,
            candidate["new_held_out"] is True,
            candidate["control_pair_frozen"] is True,
            "orientale" not in targets,
            candidate["id"] != "vavilov_vs_hertzsprung_roughness",
        )
    )


def apply_mutation(
    spec: dict[str, Any], coding: dict[str, Any], source_screen: dict[str, Any], mutation: str | None
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    spec = copy.deepcopy(spec)
    coding = copy.deepcopy(coding)
    source_screen = copy.deepcopy(source_screen)
    if mutation is None:
        return spec, coding, source_screen
    candidates = {item["id"]: item for item in coding["candidates"]}
    if mutation == "reuse_stage7a_pair_as_new":
        item = candidates["vavilov_vs_hertzsprung_roughness"]
        item["new_held_out"] = True
        item["morphology_matched"] = True
        item["control_pair_frozen"] = True
    elif mutation == "readmit_orientale_as_held_out":
        item = candidates["orientale_vs_hertzsprung_texture"]
        item["new_held_out"] = True
        item["control_pair_frozen"] = True
    elif mutation == "promote_vague_region_to_exact_localization":
        item = candidates["north_vavilov_pumice_patch"]
        item["named_localization"] = True
        item["morphology_matched"] = True
        item["new_held_out"] = True
        item["control_pair_frozen"] = True
    elif mutation == "mix_reflectance_and_geology_into_lola_endpoint":
        candidates["reiner_gamma_albedo_uniformity"]["endpoint"] = spec["shared_endpoint"]
        candidates["glushko_vs_ohm_ray_brightness"]["endpoint"] = spec["shared_endpoint"]
    elif mutation == "count_interrogative_as_confirmed_observation":
        item = candidates["glushko_primary_rays_jagged"]
        item["direction"] = "Glushko rays rougher than a control"
        item["targets"] = ["Glushko rays", "fabricated control rays"]
        item["endpoint"] = spec["shared_endpoint"]
        item["direct_comparison"] = True
        item["named_localization"] = True
        item["morphology_matched"] = True
        item["new_held_out"] = True
        item["control_pair_frozen"] = True
    elif mutation == "waive_observer_breadth":
        spec["admission_oracle"]["minimum_qualifying_observers"] = 1
    elif mutation == "access_instrument_values_before_admission":
        source_screen["access_boundary"]["new_instrument_value_bytes"] = 1
    elif mutation == "claim_admission_stop_refutes_semantic_signal":
        spec["claim_ceiling"] = "The admission stop disproves astronaut semantic sensing."
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec, coding, source_screen


def verify_stage7b(root: Path, mutation: str | None = None) -> dict[str, Any]:
    raw_spec = load_json(root / "spec" / "stage7b.json")
    raw_coding = load_json(root / raw_spec["candidate_evidence"]["path"])
    raw_screen = load_json(root / raw_spec["source_screen"]["path"])
    spec, coding, source_screen = apply_mutation(raw_spec, raw_coding, raw_screen, mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    identity_ok = (
        sha256_file(root / raw_spec["candidate_evidence"]["path"])
        == raw_spec["candidate_evidence"]["sha256"]
        and sha256_file(root / raw_spec["source_screen"]["path"])
        == raw_spec["source_screen"]["sha256"]
    )
    add_check(
        checks,
        errors,
        "frozen_evidence_identity",
        identity_ok,
        error="The Stage 7B candidate coding or source screen changed.",
    )

    transcript_errors: list[str] = []
    for candidate in coding["candidates"]:
        transcript_errors.extend(transcript_candidate_is_present(root, candidate))
    add_check(
        checks,
        errors,
        "transcript_identities_and_anchors",
        not transcript_errors,
        error="; ".join(transcript_errors) or "Transcript evidence is incomplete.",
        candidates_checked=len(coding["candidates"]),
    )

    expected_oracle = {
        "minimum_new_directional_comparisons": 3,
        "minimum_unique_named_non_orientale_targets": 4,
        "minimum_qualifying_observers": 2,
        "minimum_morphology_matched_pairs": 2,
        "minimum_frozen_negative_control_pairs": 1,
        "require_same_endpoint": True,
        "require_direct_comparison": True,
        "require_named_localization": True,
        "require_new_held_out": True,
        "require_control_pair_frozen": True,
        "exclude_orientale": True,
        "exclude_stage7a_pair": True,
        "maximum_new_instrument_value_bytes_before_admission": 0,
    }
    add_check(
        checks,
        errors,
        "frozen_admission_oracle",
        spec["admission_oracle"] == expected_oracle,
        error="The Stage 7B admission thresholds or exclusions changed.",
        observed=spec["admission_oracle"],
    )

    same_endpoint_candidates = [
        candidate
        for candidate in coding["candidates"]
        if qualifies_same_endpoint(candidate, spec["shared_endpoint"])
    ]
    unique_targets = sorted(
        {
            target
            for candidate in same_endpoint_candidates
            for target in candidate["targets"]
            if "orientale" not in target.lower()
        }
    )
    qualifying_observers = sorted(
        {
            speaker
            for candidate in same_endpoint_candidates
            for speaker in candidate["speakers"]
        }
    )
    matched_pairs = sum(
        1 for candidate in same_endpoint_candidates if candidate["morphology_matched"] is True
    )
    control_pairs = sum(
        1 for candidate in same_endpoint_candidates if candidate["control_pair_frozen"] is True
    )
    cross_axis = sorted(
        candidate["id"]
        for candidate in coding["candidates"]
        if candidate["new_held_out"] is True
        and candidate["endpoint"] != spec["shared_endpoint"]
    )
    observed_counts = {
        "candidate_episodes": len(coding["candidates"]),
        "new_directional_comparisons": len(same_endpoint_candidates),
        "unique_named_non_orientale_targets": len(unique_targets),
        "qualifying_observers": len(qualifying_observers),
        "morphology_matched_pairs": matched_pairs,
        "frozen_negative_control_pairs": control_pairs,
        "cross_axis_candidates": len(cross_axis),
    }
    summary = coding["candidate_summary"]
    summary_ok = (
        summary["candidate_episodes"] == observed_counts["candidate_episodes"]
        and summary["new_held_out_same_endpoint_directional_comparisons"]
        == observed_counts["new_directional_comparisons"]
        and summary["new_held_out_same_endpoint_unique_named_targets"]
        == observed_counts["unique_named_non_orientale_targets"]
        and summary["new_held_out_same_endpoint_observers"]
        == observed_counts["qualifying_observers"]
        and summary["new_held_out_same_endpoint_morphology_matched_pairs"]
        == observed_counts["morphology_matched_pairs"]
        and summary["frozen_negative_control_pairs"]
        == observed_counts["frozen_negative_control_pairs"]
        and sorted(summary["cross_axis_candidates_requiring_separate_tests"])
        == cross_axis
        and observed_counts == spec["expected_counts"]
    )
    add_check(
        checks,
        errors,
        "candidate_classification_and_counts",
        summary_ok,
        error="Candidate classification no longer matches the frozen Stage 7B counts.",
        observed_counts=observed_counts,
        qualifying_ids=[candidate["id"] for candidate in same_endpoint_candidates],
        cross_axis_ids=cross_axis,
    )

    boundary = source_screen["access_boundary"]
    no_value_access = (
        boundary["new_instrument_value_bytes"] == 0
        and boundary["new_control_target_value_bytes"] == 0
        and boundary["new_geologic_map_bytes"] == 0
        and boundary["stage7a_values_reused_for_scoring"] is False
        and source_screen["source_disposition"] == "NO_ACTION_FOR_STAGE7B_VALUE_ACCESS"
    )
    add_check(
        checks,
        errors,
        "no_post_gate_value_access",
        no_value_access,
        error="Stage 7B accessed or reused decision-bearing source values before admission.",
        access_boundary=boundary,
    )

    claim_ceiling = spec["claim_ceiling"].lower()
    ceiling_ok = all(
        phrase in claim_ceiling
        for phrase in (
            "does not refute stage 7a",
            "broader value of astronaut language",
            "cross-axis candidates",
            "new independently coded observations",
        )
    )
    add_check(
        checks,
        errors,
        "claim_ceiling",
        ceiling_ok,
        error="The admission stop was promoted into a substantive refutation.",
        claim_ceiling=spec["claim_ceiling"],
    )

    oracle = spec["admission_oracle"]
    panel_admitted = (
        observed_counts["new_directional_comparisons"]
        >= oracle["minimum_new_directional_comparisons"]
        and observed_counts["unique_named_non_orientale_targets"]
        >= oracle["minimum_unique_named_non_orientale_targets"]
        and observed_counts["qualifying_observers"]
        >= oracle["minimum_qualifying_observers"]
        and observed_counts["morphology_matched_pairs"]
        >= oracle["minimum_morphology_matched_pairs"]
        and observed_counts["frozen_negative_control_pairs"]
        >= oracle["minimum_frozen_negative_control_pairs"]
        and no_value_access
    )
    evidence_state = (
        "MULTI_TARGET_PANEL_ADMITTED" if panel_admitted else "VERIFIED_ADMISSION_STOP"
    )
    disposition = (
        "FREEZE_AND_RUN_CONTROLLED_PANEL"
        if panel_admitted
        else "STOP_NO_NEW_INSTRUMENT_ACCESS"
    )
    state_ok = (
        evidence_state == spec["expected_state"]
        and disposition == spec["expected_disposition"]
    )
    add_check(
        checks,
        errors,
        "frozen_terminal_state",
        state_ok,
        error="The Stage 7B terminal state differs from the frozen admission result.",
        evidence_state=evidence_state,
        disposition=disposition,
    )

    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "panel_admitted": panel_admitted,
        "evidence_state": evidence_state,
        "disposition": disposition,
        "observed_counts": observed_counts,
        "qualifying_same_endpoint_ids": [
            candidate["id"] for candidate in same_endpoint_candidates
        ],
        "cross_axis_candidates": cross_axis,
        "new_instrument_value_bytes": boundary["new_instrument_value_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage7b(root)
    mutation_names = load_json(root / "spec" / "stage7b.json")["hard_negatives"]
    mutations = {name: verify_stage7b(root, name) for name in mutation_names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 7B hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    counts = result["observed_counts"]
    lines = [
        "# Stage 7B — Controlled Multi-Target Admission",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Panel admitted: `{'YES' if result['panel_admitted'] else 'NO'}`",
        f"- New instrument-value bytes: `{result['new_instrument_value_bytes']}`",
        "",
        "## Result",
        "",
        "The transcript-only admission gate stops the same-endpoint LOLA continuation. Ten plausible episodes were inspected, but none is simultaneously new, held out, directly comparative, target-localized, morphology-matched, control-frozen, non-Orientale, and on the same roughness endpoint.",
        "",
        "| Admission dimension | Required | Observed |",
        "| --- | ---: | ---: |",
        f"| New directional comparisons | 3 | {counts['new_directional_comparisons']} |",
        f"| Unique named non-Orientale targets | 4 | {counts['unique_named_non_orientale_targets']} |",
        f"| Qualifying observers | 2 | {counts['qualifying_observers']} |",
        f"| Morphology-matched pairs | 2 | {counts['morphology_matched_pairs']} |",
        f"| Frozen negative-control pairs | 1 | {counts['frozen_negative_control_pairs']} |",
        "",
        "The apparent scarcity is not evidence that the Stage 7A signal is false. It is evidence that the current transcript cannot supply the larger controlled panel without post hoc region construction, exposed-outcome reuse, or mixed physical endpoints.",
        "",
        "## What survived",
        "",
        "Two new claims remain worth considering, but only as separately preregistered cross-axis tests:",
        "",
        "- Reiner Gamma: visually uniform albedo with a darker center — a normalized-reflectance question.",
        "- Glushko versus Ohm: similar ray brightness, with Glushko slightly brighter — a ray-sector reflectance question.",
        "",
        "Neither was quietly relabeled as LOLA roughness. No WAC raster or geologic-map values were accessed.",
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
    lines.extend(
        [
            "",
            "## Next-step logic",
            "",
            f"- If admitted: {result['next_step_logic']['if_admitted']}",
            f"- If stopped: {result['next_step_logic']['if_stopped']}",
            f"- If indeterminate: {result['next_step_logic']['if_indeterminate']}",
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
        result = verify_stage7b(args.root.resolve(), args.mutation)
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
