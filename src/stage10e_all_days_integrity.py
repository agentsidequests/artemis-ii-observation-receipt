#!/usr/bin/env python3
"""Verify Stage 10E's all-flight-day camera-action integrity audit."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import (
    add_check,
    load_hits,
    load_json,
    normalize_hit,
    verify_source_identity,
)
from stage10c_camera_action_integrity import (
    detect_complete_brackets,
    longest_signature_run,
    sequence_key,
    verify_stage10c,
)


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "non_fd6_declared_error_free": False,
        "flyby_complexity_declared_causal": False,
        "scope": "all_flight_day_complete_raw_brackets",
        "correct_activity_inferred": False,
        "all_fd6_activity_declared_unreliable": False,
        "zero_fractures_declared_impossible": False,
        "incomplete_brackets_admitted": False,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "claim_non_fd6_images_are_error_free":
        state["non_fd6_declared_error_free"] = True
    elif mutation == "claim_lunar_flyby_complexity_caused_fractures":
        state["flyby_complexity_declared_causal"] = True
    elif mutation == "generalize_bracket_rate_to_nonbracket_products":
        state["scope"] = "all_raw_products"
    elif mutation == "infer_correct_activity_from_companion_frames":
        state["correct_activity_inferred"] = True
    elif mutation == "call_every_fd6_activity_assignment_unreliable":
        state["all_fd6_activity_declared_unreliable"] = True
    elif mutation == "treat_zero_observed_fractures_as_proof_of_impossibility":
        state["zero_fractures_declared_impossible"] = True
    elif mutation == "count_incomplete_brackets":
        state["incomplete_brackets_admitted"] = True
    elif mutation == "open_pixels_to_explain_flight_day_concentration":
        mutated["source_contract"]["pixel_payload_bytes"] = 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_daily_receipt(root: Path, receipt: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    records = list(receipt.get("sources", []))
    for page in receipt.get("atlas_pages", []):
        records.extend(
            [
                {
                    "path": page["request_path"],
                    "bytes": page["request_bytes"],
                    "sha256": page["request_sha256"],
                },
                {
                    "path": page["response_path"],
                    "bytes": page["response_bytes"],
                    "sha256": page["response_sha256"],
                },
            ]
        )
    from artemis_testbed import sha256_file

    for record in records:
        path = root / record["path"]
        if not path.is_file():
            failures.append(f"missing:{record['path']}")
            continue
        if path.stat().st_size != record["bytes"]:
            failures.append(f"bytes:{record['path']}")
        if sha256_file(path) != record["sha256"]:
            failures.append(f"sha256:{record['path']}")
    return failures


def load_daily_hits(root: Path, receipt: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    hits: list[dict[str, Any]] = []
    errors: list[str] = []
    for page in receipt.get("atlas_pages", []):
        payload = load_json(root / page["response_path"])
        page_hits = payload.get("hits", {}).get("hits", [])
        total = payload.get("hits", {}).get("total", {})
        if total.get("relation") != "eq" or total.get("value") != page["hits"]:
            errors.append(f"total:fd{page['flight_day']}:{total}")
        if len(page_hits) != page["hits"]:
            errors.append(f"hits:fd{page['flight_day']}:{len(page_hits)}")
        hits.extend(page_hits)
    return hits, errors


def zero_filled_counts(counter: Counter[str], days: range = range(1, 11)) -> dict[str, int]:
    return {str(day): counter[str(day)] for day in days}


def verify_stage10e(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10e.json"), mutation)
    contract = spec["source_contract"]
    expected = spec["frozen_observables"]
    receipt = load_json(root / contract["receipt_path"])
    receipt10a = load_json(root / contract["stage10a_receipt_path"])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    source_failures = verify_daily_receipt(root, receipt) + verify_source_identity(root, receipt10a)
    daily_hits, daily_errors = load_daily_hits(root, receipt)
    fd6_hits, fd6_errors = load_hits(root, receipt10a)
    hits = daily_hits + fd6_hits
    ids = [hit.get("_id") for hit in hits]
    records = [normalize_hit(hit) for hit in hits]
    flight_day_counts = zero_filled_counts(Counter(record["flight_day"] for record in records))
    source_ok = (
        not source_failures
        and not daily_errors
        and not fd6_errors
        and len(hits) == contract["expected_hits"]
        and len(set(ids)) == len(ids)
        and flight_day_counts == contract["expected_flight_day_counts"]
        and len(receipt.get("atlas_pages", [])) == contract["expected_daily_queries"]
    )
    add_check(
        checks,
        errors,
        "complete_all_flight_day_source",
        source_ok,
        error="The preserved 10,329-record all-flight-day source denominator did not replay.",
        source_failures=source_failures,
        page_errors=daily_errors + fd6_errors,
        records=len(records),
        unique_ids=len(set(ids)),
        flight_day_counts=flight_day_counts,
    )

    stage10c_spec = load_json(root / "spec" / "stage10c.json")
    bracket_contract = stage10c_spec["complete_bracket_contract"]
    contract_ok = (
        bracket_contract["allowed_bracket_sequences"]
        == spec["complete_bracket_contract"]["allowed_bracket_sequences"]
        and bracket_contract["maximum_span_seconds"] == 10.0
    )
    add_check(
        checks,
        errors,
        "stage10c_oracle_reuse",
        contract_ok,
        error="The Stage 10C complete-bracket oracle was not reused unchanged.",
    )

    brackets = detect_complete_brackets(records, bracket_contract) if contract_ok else []
    file_day = {record["file_name"]: record["flight_day"] for record in records}
    pattern_counts = Counter(sequence_key(item["bracket_values"]) for item in brackets)
    brackets_by_day = zero_filled_counts(
        Counter(file_day[item["file_names"][0]] for item in brackets)
    )
    denominator_ok = (
        len(brackets) == expected["expected_complete_brackets"]
        and dict(sorted(pattern_counts.items()))
        == dict(sorted(expected["expected_pattern_counts"].items()))
        and brackets_by_day == expected["expected_brackets_by_flight_day"]
    )
    add_check(
        checks,
        errors,
        "complete_action_denominator",
        denominator_ok,
        error="The all-flight-day bracket denominator, pattern census, or day distribution changed.",
        complete_brackets=len(brackets),
        pattern_counts=dict(pattern_counts),
        brackets_by_flight_day=brackets_by_day,
    )

    fractures = [item for item in brackets if item["activity_facet_fracture"]]
    fractures_by_day = zero_filled_counts(
        Counter(file_day[item["file_names"][0]] for item in fractures)
    )
    fracture_rate = len(fractures) / len(brackets) if brackets else None
    target_presence_count = sum(item["target_presence_fracture"] for item in fractures)
    target_value_count = sum(item["target_value_fracture"] for item in fractures)
    concentration_ok = (
        len(fractures) == expected["expected_activity_fractures"]
        and fracture_rate == expected["expected_activity_fracture_rate"]
        and fractures_by_day == expected["expected_fractures_by_flight_day"]
        and target_presence_count
        == expected["expected_target_presence_fractures_among_activity_fractures"]
        and target_value_count
        == expected["expected_target_value_fractures_among_activity_fractures"]
    )
    add_check(
        checks,
        errors,
        "flight_day_6_concentration",
        concentration_ok,
        error="The activity fractures no longer reproduce as twenty-one Flight Day 6-only actions.",
        activity_fractures=len(fractures),
        activity_fracture_rate=fracture_rate,
        fractures_by_flight_day=fractures_by_day,
        target_presence_fractures=target_presence_count,
        target_value_fractures=target_value_count,
    )

    signature = stage10c_spec["frozen_observables"]["repeated_signature"]
    signature_run = longest_signature_run(brackets, signature)
    stage10c = verify_stage10c(root)
    replay_ok = (
        stage10c["pass"]
        and stage10c["complete_brackets"] == brackets_by_day["6"] == 1721
        and stage10c["activity_fractured_brackets"] == fractures_by_day["6"] == 21
        and len(signature_run) == expected["expected_repeated_signature_actions"]
    )
    add_check(
        checks,
        errors,
        "stage10c_result_replay",
        replay_ok,
        error="The prior Flight Day 6 result or repeated signature did not replay inside the complete archive.",
        repeated_signature_actions=len(signature_run),
    )

    state = spec["mutation_state"]
    boundary_ok = (
        not any(
            state[key]
            for key in (
                "non_fd6_declared_error_free",
                "flyby_complexity_declared_causal",
                "correct_activity_inferred",
                "all_fd6_activity_declared_unreliable",
                "zero_fractures_declared_impossible",
                "incomplete_brackets_admitted",
            )
        )
        and state["scope"] == "all_flight_day_complete_raw_brackets"
        and contract["pixel_payload_bytes"] == 0
        and receipt["pixel_payload_bytes"] == 0
        and receipt10a["pixel_payload_bytes"] == 0
    )
    add_check(
        checks,
        errors,
        "claim_and_access_boundaries",
        boundary_ok,
        error="A prohibited correctness, causal, scope, reliability, completeness, or pixel claim was admitted.",
        mutation_state=state,
        pixel_payload_bytes=contract["pixel_payload_bytes"],
    )

    evidence_state = (
        "VERIFIED_ALL_DAYS_WITH_FLIGHT_DAY_6_ONLY_FRAGMENTATION"
        if denominator_ok and concentration_ok and replay_ok
        else "MIXED_OR_UNRESOLVED"
    )
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "source_records": len(records),
        "flight_day_record_counts": flight_day_counts,
        "complete_brackets": len(brackets),
        "pattern_counts": dict(pattern_counts),
        "brackets_by_flight_day": brackets_by_day,
        "activity_fractured_brackets": len(fractures),
        "activity_fracture_rate": fracture_rate,
        "fractures_by_flight_day": fractures_by_day,
        "target_presence_fractures_among_activity_fractures": target_presence_count,
        "target_value_fractures_among_activity_fractures": target_value_count,
        "repeated_signature_actions": len(signature_run),
        "activity_fractures": fractures,
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
    baseline = verify_stage10e(root)
    names = load_json(root / "spec" / "stage10e.json")["hard_negatives"]
    mutations = {name: verify_stage10e(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 10E hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10E — All-Flight-Day Camera-Action Integrity",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Complete raw crew-camera records: `{result['source_records']:,}`",
        f"- Complete bracket actions: `{result['complete_brackets']:,}`",
        f"- Activity-fractured actions: `{result['activity_fractured_brackets']}` (`{result['activity_fracture_rate']:.4%}`)",
        f"- Fractures outside Flight Day 6: `{sum(count for day, count in result['fractures_by_flight_day'].items() if day != '6')}`",
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
        "## Brackets / fractures by flight day",
        "",
    ]
    for day in sorted(result["brackets_by_flight_day"], key=int):
        lines.append(
            f"- Flight Day {day}: `{result['brackets_by_flight_day'][day]}` / `{result['fractures_by_flight_day'][day]}`"
        )
    lines.extend(["", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", ""])
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
        result = verify_stage10e(args.root.resolve(), args.mutation)
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
