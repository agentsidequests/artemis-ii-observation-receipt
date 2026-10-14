#!/usr/bin/env python3
"""Verify the Stage 2C source-only explanation gate without network access."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage2a_earthrise_coverage import verify_stage2a
from stage2b_fixed_camera_replication import verify_stage2b


UTC = timezone.utc


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def parse_utc(value: str) -> datetime:
    if value.endswith("Z"):
        return datetime.fromisoformat(value[:-1] + "+00:00")
    for pattern in ("%d %b %Y %H:%M:%S.%f", "%d %b %Y %H:%M:%S"):
        try:
            return datetime.strptime(value, pattern).replace(tzinfo=UTC)
        except ValueError:
            pass
    raise ValueError(f"Unsupported UTC timestamp: {value!r}")


def close(actual: float, expected: float, tolerance: float = 1e-6) -> bool:
    return abs(actual - expected) <= tolerance


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


def find_target(payload: list[Any], ltp_name: str) -> dict[str, Any]:
    matches = [
        item["target_properties"]
        for item in payload
        if item.get("target_properties", {}).get("ltp_name") == ltp_name
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one {ltp_name} target, found {len(matches)}")
    return matches[0]


def apply_mutation(
    spec: dict[str, Any], extracts: dict[str, Any], mutation: str | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = copy.deepcopy(spec)
    extracts = copy.deepcopy(extracts)
    if mutation is None:
        return spec, extracts
    if mutation == "remove_trajectory_source":
        extracts["sources"] = [
            item for item in extracts["sources"] if item["id"] != "operations_report_leg_and_shift"
        ]
    elif mutation == "move_reported_delta_outside_earthrise_lag":
        spec["planning_lineage"]["reported_example_delta_seconds"] = 15.4
    elif mutation == "promote_sitrep_without_timing_mapping":
        spec["field_comparison"]["differing_fields"]["sci_sit_rep"][
            "timing_explanation_status"
        ] = "SOURCE_NOMINATED_TESTABLE_HYPOTHESIS"
    elif mutation == "equate_request_duration_with_availability":
        spec["field_comparison"]["differing_fields"]["request_duration_minutes"][
            "documented_semantics"
        ] = "observation_availability_window"
    elif mutation == "promote_hypothesis_to_confirmed_cause":
        spec["candidate_evaluations"][0]["status"] = "CONFIRMED_CAUSE"
        spec["expected_result"]["evidence_state"] = "VERIFIED_CONFIRMED_CAUSE"
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec, extracts


def verified_field_comparison(
    earthset: dict[str, Any], earthrise: dict[str, Any]
) -> dict[str, Any]:
    def true_stms(target: dict[str, Any]) -> list[str]:
        return [f"stm{index}" for index in range(1, 11) if target[f"stm{index}"]]

    def schedule(target: dict[str, Any]) -> dict[str, float | str]:
        request = parse_utc(target["request_date_time"])
        start = parse_utc(target["start_date_time"])
        end = parse_utc(target["end_date_time"])
        slot = float(target["request_duration"] * 60)
        start_offset = (start - request).total_seconds()
        end_offset = (end - request).total_seconds()
        return {
            "request_utc": request.isoformat().replace("+00:00", "Z"),
            "request_slot_seconds": slot,
            "availability_start_offset_seconds": start_offset,
            "availability_end_offset_seconds": end_offset,
            "availability_duration_seconds": (end - start).total_seconds(),
            "post_window_slot_seconds": slot - end_offset,
        }

    earthset_schedule = schedule(earthset)
    earthrise_schedule = schedule(earthrise)
    return {
        "shared": {
            "time_sensitive": earthset["time_sensitive"] == earthrise["time_sensitive"] is True,
            "stm_true": true_stms(earthset),
            "stm_equal": true_stms(earthset) == true_stms(earthrise),
            "camera_actions_equal": earthset["camera_actions"].strip()
            == earthrise["camera_actions"].strip(),
            "impact_statement_equal_after_trim": earthset["impact_statement"].strip()
            == earthrise["impact_statement"].strip(),
            "middle_date_time_equal": earthset["middle_date_time"]
            == earthrise["middle_date_time"],
            "location_equal": all(
                earthset[field] == earthrise[field]
                for field in ("longitude", "latitude", "diameter")
            ),
        },
        "differing": {
            "request_duration_minutes": {
                "earthset": earthset["request_duration"],
                "earthrise": earthrise["request_duration"],
            },
            "sci_sit_rep": {
                "earthset": earthset["sci_sit_rep"],
                "earthrise": earthrise["sci_sit_rep"],
            },
            "unaided_eye_prompt_differs": earthset["unaided_eye_actions"].strip()
            != earthrise["unaided_eye_actions"].strip(),
        },
        "schedule": {"earthset": earthset_schedule, "earthrise": earthrise_schedule},
        "availability_width_ratio_earthset_to_earthrise": earthset_schedule[
            "availability_duration_seconds"
        ]
        / earthrise_schedule["availability_duration_seconds"],
    }


def verify_stage2c(root: Path, mutation: str | None = None) -> dict[str, Any]:
    original_spec = load_json(root / "spec" / "stage2c.json")
    if not isinstance(original_spec, dict):
        raise ValueError("Stage 2C spec is not an object")
    original_extracts = load_json(root / original_spec["source_evidence"]["source_extracts_path"])
    if not isinstance(original_extracts, dict):
        raise ValueError("Stage 2C source extracts are not an object")
    spec, extracts = apply_mutation(original_spec, original_extracts, mutation)

    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    evidence = original_spec["source_evidence"]

    for identity, path_key, hash_key in (
        ("otr", "otr_path", "otr_sha256"),
        ("source_extracts", "source_extracts_path", "source_extracts_sha256"),
    ):
        path = root / evidence[path_key]
        observed_hash = sha256_file(path) if path.is_file() else None
        add_check(
            checks,
            errors,
            f"{identity}_identity",
            observed_hash == evidence[hash_key],
            observed_sha256=observed_hash,
            error=f"{identity} identity mismatch",
        )

    sources = {item["id"]: item for item in extracts["sources"]}
    required_sources = set(spec["source_evidence"]["required_source_ids"])
    source_set_pass = required_sources.issubset(sources)
    add_check(
        checks,
        errors,
        "required_source_set",
        source_set_pass,
        observed=sorted(sources),
        error="The frozen primary-source set is incomplete",
    )

    expected_parent_hashes = {
        "data_user_guide": "c4f5ab25363ca3f8fc17bb776e9fc90c19707c8a18c9255648aef34d6a7b0bd2",
        "operations_report": "64339869c8a1c41dde273cf1b507a0827e93a881390e4af4c16a5f2f44b00cf5",
        "targeting_package": "177cda54d5770134b49cdcc35855171ed0c1ba5f354b0df0e521e06e16516273",
    }
    parent_hashes_pass = bool(source_set_pass)
    if source_set_pass:
        parent_hashes_pass = (
            sources["data_user_guide"]["sha256"] == expected_parent_hashes["data_user_guide"]
            and sources["targeting_package_timeline"]["sha256"]
            == expected_parent_hashes["targeting_package"]
            and all(
                sources[source_id]["sha256"] == expected_parent_hashes["operations_report"]
                for source_id in required_sources
                if source_id.startswith("operations_report_")
            )
        )
    add_check(
        checks,
        errors,
        "parent_document_identities",
        parent_hashes_pass,
        error="A source extract is not bound to the frozen NASA/PDS document identity",
    )

    stage2a = verify_stage2a(root)
    stage2b = verify_stage2b(root)
    prior = spec["source_evidence"]["prior_stage_requirements"]
    prior_pass = (
        stage2a["pass"]
        and stage2a["evidence_state"] == prior["stage2a_evidence_state"]
        and stage2a["coverage_relation"] == prior["stage2a_coverage_relation"]
        and stage2b["pass"]
        and stage2b["evidence_state"] == prior["stage2b_evidence_state"]
        and stage2b["events"]["earthset"]["coverage_relation"]
        == prior["stage2b_earthset_relation"]
    )
    add_check(
        checks,
        errors,
        "prior_stage_replay",
        prior_pass,
        stage2a=stage2a["evidence_state"],
        stage2b=stage2b["evidence_state"],
        error="Stage 2A or Stage 2B no longer supports the frozen contrast",
    )

    otr_payload = load_json(root / evidence["otr_path"])
    if not isinstance(otr_payload, list):
        raise ValueError("OTR payload is not a list")
    earthset = find_target(otr_payload, "Earthset")
    earthrise = find_target(otr_payload, "Earthrise")
    observed_fields = verified_field_comparison(earthset, earthrise)
    frozen_fields = spec["field_comparison"]

    shared_expected = frozen_fields["shared_fields"]
    shared_observed = observed_fields["shared"]
    shared_pass = (
        shared_observed["time_sensitive"] == shared_expected["time_sensitive"]
        and shared_observed["stm_equal"]
        and shared_observed["stm_true"] == shared_expected["stm_true"]
        and shared_observed["camera_actions_equal"] == shared_expected["camera_actions_equal"]
        and shared_observed["impact_statement_equal_after_trim"]
        == shared_expected["impact_statement_equal_after_trim"]
        and shared_observed["middle_date_time_equal"]
        and shared_observed["location_equal"]
    )
    add_check(
        checks,
        errors,
        "shared_fields_hard_negative",
        shared_pass,
        observed=shared_observed,
        error="The shared-field hard negative changed",
    )

    differing_expected = frozen_fields["differing_fields"]
    differing_observed = observed_fields["differing"]
    differing_pass = (
        differing_observed["request_duration_minutes"]
        == {
            "earthset": differing_expected["request_duration_minutes"]["earthset"],
            "earthrise": differing_expected["request_duration_minutes"]["earthrise"],
        }
        and differing_observed["sci_sit_rep"]
        == {
            "earthset": differing_expected["sci_sit_rep"]["earthset"],
            "earthrise": differing_expected["sci_sit_rep"]["earthrise"],
        }
        and differing_observed["unaided_eye_prompt_differs"]
        and differing_expected["request_duration_minutes"]["documented_semantics"]
        == "requested activity duration"
        and differing_expected["request_duration_minutes"]["timing_explanation_status"]
        == "NOT_NOMINATED_ACTIVITY_SLOT_ONLY"
        and differing_expected["sci_sit_rep"]["documented_semantics"]
        == "science situation report required"
        and differing_expected["sci_sit_rep"]["timing_explanation_status"]
        == "NOT_NOMINATED_NO_AVAILABILITY_MAPPING"
    )
    add_check(
        checks,
        errors,
        "documented_field_differences",
        differing_pass,
        observed=differing_observed,
        error="A field difference was changed or promoted without a timing mapping",
    )

    schedule_pass = True
    for event in ("earthset", "earthrise"):
        observed = observed_fields["schedule"][event]
        expected = frozen_fields["outcome_and_schedule_values"][event]
        schedule_pass = schedule_pass and observed["request_utc"] == expected["request_utc"]
        schedule_pass = schedule_pass and all(
            close(float(observed[key]), float(expected[key]))
            for key in (
                "request_slot_seconds",
                "availability_start_offset_seconds",
                "availability_end_offset_seconds",
                "availability_duration_seconds",
                "post_window_slot_seconds",
            )
        )
    ratio = observed_fields["availability_width_ratio_earthset_to_earthrise"]
    schedule_pass = schedule_pass and close(
        ratio,
        frozen_fields["outcome_and_schedule_values"][
            "availability_width_ratio_earthset_to_earthrise"
        ],
        1e-9,
    )
    add_check(
        checks,
        errors,
        "schedule_values",
        schedule_pass,
        observed=observed_fields["schedule"],
        availability_width_ratio=ratio,
        error="The frozen OTR schedule comparison changed",
    )

    trajectory_source = sources.get("operations_report_leg_and_shift", {})
    source_actual = parse_utc(trajectory_source["figure_actual_utc"]) if trajectory_source else None
    source_visual = (
        parse_utc(trajectory_source["figure_visualization_utc"]) if trajectory_source else None
    )
    source_delta = (
        (source_visual - source_actual).total_seconds()
        if source_actual is not None and source_visual is not None
        else None
    )
    lineage = spec["planning_lineage"]
    lineage_pass = (
        source_delta == trajectory_source.get("figure_delta_seconds")
        == lineage["reported_example_delta_seconds"]
        and lineage["reported_direction"] == "actual_earlier_than_post_tli_visualization"
        and lineage["matched_view_actual_utc"] == trajectory_source.get("figure_actual_utc")
        and lineage["matched_view_visualization_utc"]
        == trajectory_source.get("figure_visualization_utc")
    )
    add_check(
        checks,
        errors,
        "documented_planning_lineage",
        lineage_pass,
        observed_delta_seconds=source_delta,
        error="The documented post-TLI planning lineage or matched-view delta changed",
    )

    clearance = stage2a["event_brackets"]["full_clearance"]
    earthrise_window_start = parse_utc(stage2a["availability_window"]["start_utc"])
    clearance_lower = parse_utc(clearance["lower_exclusive_utc"])
    clearance_upper = parse_utc(clearance["upper_inclusive_utc"])
    lag_minimum = (earthrise_window_start - clearance_upper).total_seconds()
    lag_maximum = (earthrise_window_start - clearance_lower).total_seconds()
    expected_result = spec["expected_result"]
    lag_pass = close(
        lag_minimum,
        expected_result["earthrise_clearance_lag_minimum_inclusive_seconds"],
    ) and close(
        lag_maximum,
        expected_result["earthrise_clearance_lag_maximum_exclusive_seconds"],
    )
    add_check(
        checks,
        errors,
        "earthrise_clearance_lag_bracket",
        lag_pass,
        minimum_inclusive_seconds=lag_minimum,
        maximum_exclusive_seconds=lag_maximum,
        error="The Earthrise clearance-to-window-start lag bracket changed",
    )

    reported_delta = float(lineage["reported_example_delta_seconds"])
    earthset_window = float(
        observed_fields["schedule"]["earthset"]["availability_duration_seconds"]
    )
    earthrise_window = float(
        observed_fields["schedule"]["earthrise"]["availability_duration_seconds"]
    )
    candidate_relations = {
        "reported_example_delta_inside_earthrise_clearance_lag_bracket": lineage_pass
        and lag_minimum <= reported_delta < lag_maximum,
        "earthset_window_wider_than_reported_example_delta": earthset_window
        > reported_delta,
        "earthrise_window_narrower_than_reported_example_delta": earthrise_window
        < reported_delta,
        "stage2a_no_overlap_and_stage2b_earthset_overlap_remain_verified": prior_pass,
    }
    candidates = {item["id"]: item for item in spec["candidate_evaluations"]}
    trajectory_candidate = candidates["post_tli_trajectory_offset_x_window_width"]
    candidate_pass = (
        all(candidate_relations.values())
        and trajectory_candidate["status"] == "SOURCE_NOMINATED_TESTABLE_HYPOTHESIS"
        and set(trajectory_candidate["required_relations"]) == set(candidate_relations)
        and candidates["request_duration"]["status"]
        == "NOT_NOMINATED_ACTIVITY_SLOT_ONLY"
        and candidates["science_situation_report"]["status"]
        == "NOT_NOMINATED_NO_AVAILABILITY_MAPPING"
        and candidates["shared_science_and_camera_fields"]["status"]
        == "HARD_NEGATIVE_SAME_VALUES"
    )
    admitted_candidate_count = 1 if candidate_pass else 0
    add_check(
        checks,
        errors,
        "candidate_nomination_oracle",
        candidate_pass
        and admitted_candidate_count == expected_result["admitted_candidate_count"],
        relations=candidate_relations,
        admitted_candidate_count=admitted_candidate_count,
        error="The trajectory-offset/window-width candidate did not meet the frozen nomination oracle",
    )

    ceiling_pass = (
        expected_result["evidence_state"] == "VERIFIED_SOURCE_NOMINATED_HYPOTHESIS"
        and expected_result["disposition"] == "HYPOTHESIS_NOMINATED_STOP_SOURCE_ONLY"
        and "No causal confirmation" in spec["claim_ceiling"]
    )
    add_check(
        checks,
        errors,
        "claim_ceiling",
        ceiling_pass,
        error="The bounded hypothesis was promoted beyond the frozen claim ceiling",
    )

    passed = not errors and all(item["pass"] for item in checks)
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": expected_result["evidence_state"] if passed else "REJECTED",
        "disposition": expected_result["disposition"] if passed else None,
        "field_comparison": observed_fields,
        "planning_alignment": {
            "documented_matched_view_delta_seconds": source_delta,
            "reported_direction": lineage["reported_direction"],
            "earthrise_clearance_lag_minimum_inclusive_seconds": lag_minimum,
            "earthrise_clearance_lag_maximum_exclusive_seconds": lag_maximum,
            "earthset_availability_duration_seconds": earthset_window,
            "earthrise_availability_duration_seconds": earthrise_window,
            "relations": candidate_relations,
        },
        "admitted_candidate_count": admitted_candidate_count,
        "candidate_evaluations": spec["candidate_evaluations"],
        "network_bytes_in_verification": 0,
        "checks": checks,
        "errors": errors,
        "claim_ceiling": spec["claim_ceiling"],
        "stop_rule": spec["stop_rule"],
        "next_step_logic": spec["next_step_logic"] if passed else None,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage2c(root)
    spec = load_json(root / "spec" / "stage2c.json")
    if not isinstance(spec, dict):
        raise ValueError("Stage 2C spec is not an object")
    mutations = {name: verify_stage2c(root, name) for name in spec["hard_negatives"]}
    hard_negatives_pass = all(not item["pass"] for item in mutations.values())
    passed = baseline["pass"] and hard_negatives_pass
    return {
        "baseline": baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": passed,
        "evidence_state": (
            "VERIFIED_SOURCE_NOMINATED_HYPOTHESIS" if passed else "FAILED"
        ),
    }


def render_markdown(verification: dict[str, Any]) -> str:
    baseline = verification["baseline"]
    alignment = baseline["planning_alignment"]
    fields = baseline["field_comparison"]
    lines = [
        "# Artemis II Observation-Execution Testbed — Stage 2C Result",
        "",
        f"- Verification: **{'PASS' if verification['pass'] else 'FAIL'}**",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Disposition: `{baseline.get('disposition') or 'UNSET'}`",
        f"- Admitted explanatory candidates: **{baseline['admitted_candidate_count']}**",
        "",
        "## Bounded result",
        "",
        "NASA documents one matched-view example in which the realized flyby was 154 seconds earlier than the post-TLI visualization used in the planning lineage. That 154-second example falls inside Earthrise's independently measured 136-to-166-second full-clearance-to-availability-start lag.",
        "",
        "Earthset's availability window is 196.650033 seconds wide, while Earthrise's is only 4.147844 seconds. The width difference can therefore make the two events respond differently to an offset of the documented scale: Earthset can remain overlapping while Earthrise misses completely.",
        "",
        "This is a source-nominated, quantitatively consistent hypothesis—not a confirmed cause or a uniform timing correction.",
        "The matched-view comparison comes from an earlier scene, not either limb crossing; event-specific transfer remains the unresolved test.",
        "",
        "## Quantitative oracle",
        "",
        "| Quantity | Value | Frozen relation |",
        "| --- | ---: | --- |",
        f"| NASA matched-view actual-vs-visualization delta | {alignment['documented_matched_view_delta_seconds']:.0f}s earlier | Inside Earthrise lag bracket |",
        f"| Earthrise full-clearance-to-window-start lag | [{alignment['earthrise_clearance_lag_minimum_inclusive_seconds']:.0f}s, {alignment['earthrise_clearance_lag_maximum_exclusive_seconds']:.0f}s) | Contains 154s |",
        f"| Earthset availability width | {alignment['earthset_availability_duration_seconds']:.6f}s | Wider than 154s |",
        f"| Earthrise availability width | {alignment['earthrise_availability_duration_seconds']:.6f}s | Narrower than 154s |",
        "",
        "## Fields that do not explain the placement",
        "",
        f"- Requested activity duration differs ({fields['differing']['request_duration_minutes']['earthset']} vs. {fields['differing']['request_duration_minutes']['earthrise']} minutes), but NASA documents it as the LTP observation slot rather than an availability boundary.",
        "- Earthrise requires a Science Situation Report and Earthset does not, but the source supplies no mapping from that reporting flag to visibility-window placement.",
        "- Time-sensitive status, STM links, camera actions, science impact, and location placeholders are shared and cannot discriminate the opposite results.",
        "",
        "## Falsifier and stop",
        "",
        "When NASA publishes the actual Artemis II SPICE bundle, derive the Earthrise event-specific geometry. Reject the hypothesis if the actual-vs-planned shift falls outside the frozen 136-to-166-second lag bracket or if the OTR timing did not inherit the documented post-TLI planning basis.",
        "",
        baseline["stop_rule"],
        "",
        "## Next-step logic",
        "",
        f"**Recommended:** {baseline['next_step_logic']['recommended']}",
        "",
        f"Why: {baseline['next_step_logic']['why']}",
        "",
        f"Blocked: {baseline['next_step_logic']['blocked']}",
        "",
        "## Hard negatives",
        "",
    ]
    for name, result in verification["hard_negatives"].items():
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
            "remove_trajectory_source",
            "move_reported_delta_outside_earthrise_lag",
            "promote_sitrep_without_timing_mapping",
            "equate_request_duration_with_availability",
            "promote_hypothesis_to_confirmed_cause",
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        payload = verify_with_mutations(args.root)
    else:
        payload = verify_stage2c(args.root, args.mutation)
    if args.json_output:
        write_json(args.json_output, payload)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        text = render_markdown(payload) if args.command == "verify" else json.dumps(payload, indent=2) + "\n"
        args.markdown_output.write_text(text, encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
