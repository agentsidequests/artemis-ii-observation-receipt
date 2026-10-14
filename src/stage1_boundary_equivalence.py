#!/usr/bin/env python3
"""Verify the frozen Stage 1 boundary-equivalence stop decision."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artemis_testbed import find_target, find_transcript_row, load_targets, parse_utc, sha256_file


UTC = timezone.utc


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_specs(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return load_json(root / "spec" / "stage0.json"), load_json(root / "spec" / "stage1.json")


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    if mutation is None:
        return mutated
    boundaries = {item["id"]: item for item in mutated["boundary_map"]}
    intervals = {item["id"]: item for item in mutated["interval_checks"]}
    if mutation == "promote_earthrise_duration_mismatch":
        intervals["earthrise_progression"]["verdict"] = "PASS"
    elif mutation == "present_request_time_as_contact":
        item = boundaries["earthset_first_contact"]
        item["plan_field"] = "request_date_time"
        item["plan_semantics"] = "optical_first_contact"
        item["verdict"] = "PASS"
    elif mutation == "treat_beginning_as_completion":
        boundaries["earthset_first_contact"]["spoken_semantics"] = "optical_completion"
    elif mutation == "promote_sunset_from_duration_only":
        boundaries["sunset_first_contact"]["verdict"] = "PASS"
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def close(actual: float, expected: float, tolerance: float = 1e-6) -> bool:
    return abs(actual - expected) <= tolerance


def verify_stage1(root: Path, mutation: str | None = None) -> dict[str, Any]:
    stage0, original = load_specs(root)
    spec = apply_mutation(original, mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    evidence = spec["source_evidence"]
    identities = [
        ("source_extracts", root / evidence["extracts_path"], evidence["extracts_sha256"]),
        ("timeline_render", root / evidence["timeline_render_path"], evidence["timeline_render_sha256"]),
    ]
    otr_document = next(item for item in evidence["documents"] if item["id"] == "outgoing_target_request")
    identities.append(("otr", root / otr_document["local_path"], otr_document["sha256"]))
    for check_id, path, expected_hash in identities:
        observed_hash = sha256_file(path) if path.is_file() else None
        passed = observed_hash == expected_hash
        checks.append({"id": f"{check_id}_identity", "pass": passed, "observed_sha256": observed_hash})
        if not passed:
            errors.append(f"{check_id} identity mismatch")

    stage0_events = {item["id"]: item for item in stage0["events"]}
    expected_ids = set(stage0_events)
    boundary_ids = [item["id"] for item in spec["boundary_map"]]
    unique_complete = len(boundary_ids) == len(set(boundary_ids)) and set(boundary_ids) == expected_ids
    checks.append({"id": "boundary_map_complete", "pass": unique_complete})
    if not unique_complete:
        errors.append("Boundary map does not exactly cover the seven frozen Stage 0 events")

    field_semantics = spec["field_semantics"]
    role_semantics = {
        "earthset_first_contact": "optical_first_contact",
        "earthset_complete": "optical_completion",
        "earthrise_first_contact": "optical_first_contact",
        "earthrise_complete": "optical_completion",
        "sunset_first_contact": "optical_first_contact",
        "sunset_complete": "optical_completion",
        "sunrise_first_contact": "optical_first_contact",
    }
    for item in spec["boundary_map"]:
        event = stage0_events.get(item["id"])
        if event is None:
            continue
        if item["plan_field"] != event["plan_field"]:
            errors.append(f"{item['id']} changes the frozen plan field")
        expected_plan_semantics = field_semantics.get(item["plan_field"])
        if item["plan_semantics"] != expected_plan_semantics:
            errors.append(f"{item['id']} misstates {item['plan_field']} semantics")
        if item["spoken_semantics"] != role_semantics[item["id"]]:
            errors.append(f"{item['id']} misclassifies the spoken cue boundary")
        if item["verdict"] == "PASS":
            if item["plan_semantics"] != item["spoken_semantics"]:
                errors.append(f"{item['id']} passes mismatched boundary semantics")
            if not item.get("equivalence_source_locator"):
                errors.append(f"{item['id']} passes without an equivalence source")

    targets = load_targets(root, stage0)
    interval_results: list[dict[str, Any]] = []
    for interval in spec["interval_checks"]:
        target = find_target(targets, interval["target"])
        plan_duration = (
            parse_utc(target["end_date_time"]) - parse_utc(target["start_date_time"])
        ).total_seconds()
        start_event = stage0_events[interval["observed_start_event"]]
        end_event = stage0_events[interval["observed_end_event"]]
        _, start_row = find_transcript_row(root, start_event)
        _, end_row = find_transcript_row(root, end_event)
        observed_duration = (parse_utc(end_row["utc"]) - parse_utc(start_row["utc"])).total_seconds()
        ratio = plan_duration / observed_duration
        values_pass = (
            close(plan_duration, interval["expected_plan_duration_seconds"])
            and close(observed_duration, interval["expected_observed_duration_seconds"])
            and close(ratio, interval["expected_ratio"], 1e-9)
        )
        if not values_pass:
            errors.append(f"{interval['id']} duration evidence drifted")
        hard_negative = ratio < spec["duration_hard_negative"]["ratio_floor"]
        if hard_negative and interval["verdict"] != "FAIL":
            errors.append(f"{interval['id']} accepts the duration hard negative")
        interval_results.append(
            {
                "id": interval["id"],
                "target": interval["target"],
                "plan_duration_seconds": round(plan_duration, 6),
                "observed_duration_seconds": round(observed_duration, 6),
                "duration_difference_seconds": round(plan_duration - observed_duration, 6),
                "plan_to_observed_ratio": round(ratio, 9),
                "duration_hard_negative": hard_negative,
                "verdict": interval["verdict"],
                "pass": values_pass and (not hard_negative or interval["verdict"] == "FAIL"),
            }
        )

    summary = Counter(item["verdict"] for item in spec["boundary_map"])
    expected_summary = spec["expected_summary"]
    summary_pass = all(summary.get(key, 0) == expected_summary[key] for key in ("PASS", "FAIL", "AMBIGUOUS"))
    checks.append({"id": "expected_verdict_summary", "pass": summary_pass, "observed": dict(summary)})
    if not summary_pass:
        errors.append("Boundary verdict summary changed")

    stage_gate = "ADVANCE" if summary.get("FAIL", 0) == 0 and summary.get("AMBIGUOUS", 0) == 0 else "STOPPED"
    if stage_gate != expected_summary["stage_gate"]:
        errors.append(f"Stage gate is {stage_gate}, expected {expected_summary['stage_gate']}")
    checks.append({"id": "stage_gate", "pass": stage_gate == expected_summary["stage_gate"], "observed": stage_gate})

    passed = not errors and all(check["pass"] for check in checks) and all(item["pass"] for item in interval_results)
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": "VERIFIED_STOP" if passed and stage_gate == "STOPPED" else "REJECTED",
        "stage_gate": stage_gate,
        "disposition": expected_summary["disposition"] if passed else None,
        "checks": checks,
        "boundary_summary": {key: summary.get(key, 0) for key in ("PASS", "FAIL", "AMBIGUOUS")},
        "boundaries": spec["boundary_map"],
        "intervals": interval_results,
        "errors": errors,
        "next_step_logic": spec["next_step_logic"] if passed else None,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage1(root)
    _, spec = load_specs(root)
    mutations = {name: verify_stage1(root, name) for name in spec["hard_negatives"]}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    passed = baseline["pass"] and hard_negatives_pass
    return {
        "baseline": baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": passed,
        "evidence_state": "VERIFIED_STOP" if passed else "FAILED",
    }


def render_markdown(verification: dict[str, Any]) -> str:
    baseline = verification["baseline"]
    lines = [
        "# Artemis II Observation-Execution Testbed — Stage 1 Result",
        "",
        f"- Verification: **{'PASS' if verification['pass'] else 'FAIL'}**",
        f"- Stage 1 gate: **{baseline['stage_gate']}**",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Disposition: `{baseline.get('disposition') or 'UNSET'}`",
        f"- Boundary verdicts: {baseline['boundary_summary']['PASS']} PASS / {baseline['boundary_summary']['FAIL']} FAIL / {baseline['boundary_summary']['AMBIGUOUS']} AMBIGUOUS",
        "",
        "The verification passes because the Testbed correctly stops the original timing lane. It does not mean boundary equivalence passed.",
        "",
        "## Boundary map",
        "",
        "| Boundary | OTR meaning | Spoken meaning | Verdict |",
        "| --- | --- | --- | --- |",
    ]
    for item in baseline["boundaries"]:
        lines.append(
            f"| {item['id']} | {item['plan_semantics']} | {item['spoken_semantics']} | {item['verdict']} |"
        )
    lines.extend(
        [
            "",
            "## Interval hard negative",
            "",
            "| Event | OTR window | Crew progression | Ratio | Verdict |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for item in baseline["intervals"]:
        lines.append(
            f"| {item['target']} | {item['plan_duration_seconds']:.6f}s | "
            f"{item['observed_duration_seconds']:.3f}s | {item['plan_to_observed_ratio']:.3f} | {item['verdict']} |"
        )
    lines.extend(
        [
            "",
            "Earthrise is decisive: a 4.147844-second availability window cannot be treated as the endpoints of a 128.213-second first-corner-to-completely-risen progression.",
            "",
            "## Source-backed interpretation",
            "",
            "NASA documents the OTR timing as an observation availability window and separately presents target visibility and request timing. None of the reviewed source locators defines `start_date_time` or `end_date_time` as first or last optical contact.",
            "",
            "## Next-step logic",
            "",
            f"**Recommended:** {baseline['next_step_logic']['recommended']}",
            "",
            f"Why: {baseline['next_step_logic']['why']}",
            "",
            f"Blocked: {baseline['next_step_logic']['blocked_route']}",
            "",
            "## Hard negatives",
            "",
        ]
    )
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
            "promote_earthrise_duration_mismatch",
            "present_request_time_as_contact",
            "treat_beginning_as_completion",
            "promote_sunset_from_duration_only",
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        payload = verify_with_mutations(args.root)
    else:
        payload = verify_stage1(args.root, args.mutation)
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
