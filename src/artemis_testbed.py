#!/usr/bin/env python3
"""Deterministic Stage 0 runner for the Artemis II observation-execution Testbed."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def corpus_inventory(
    root: Path, spec: dict[str, Any] | None = None
) -> tuple[list[str], str, int]:
    """Hash only the source set owned by Stage 0, not later-stage corpus evidence."""
    if spec is None:
        spec = load_spec(root)
    owned_paths = [root / spec["corpus"]["otr_path"]]
    owned_paths.extend(sorted(root.glob(spec["corpus"]["transcript_glob"])))
    rows: list[str] = []
    total_bytes = 0
    for path in sorted(set(owned_paths)):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        total_bytes += size
        rows.append(f"{relative}\t{size}\t{sha256_file(path)}")
    aggregate = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
    return rows, aggregate, total_bytes


def parse_utc(value: str) -> datetime:
    formats = (
        "%d %b %Y %H:%M:%S.%f",
        "%d %b %Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    raise ValueError(f"Unsupported UTC timestamp: {value!r}")


def iso_millis(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def load_spec(root: Path) -> dict[str, Any]:
    with (root / "spec" / "stage0.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def load_targets(root: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    with (root / spec["corpus"]["otr_path"]).open(encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    return [item["target_properties"] for item in payload]


def find_target(targets: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [target for target in targets if target.get("ltp_name") == name]
    if len(matches) != 1:
        raise ValueError(f"Target {name!r} resolved {len(matches)} times; expected exactly one")
    return matches[0]


def find_transcript_row(root: Path, event: dict[str, Any]) -> tuple[int, dict[str, str]]:
    path = root / event["transcript"]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    needle = event["cue_contains"].casefold()
    speaker = event["speaker"].casefold()
    matches = [
        (index, row)
        for index, row in enumerate(rows, start=2)
        if needle in row.get("text", "").casefold()
        and row.get("speaker", "").strip().casefold() == speaker
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Cue {event['cue_contains']!r} in {event['transcript']} resolved "
            f"{len(matches)} times; expected exactly one"
        )
    return matches[0]


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    if mutation is None:
        return mutated
    if mutation == "cue_not_found":
        next(item for item in mutated["events"] if item["id"] == "sunset_complete")[
            "cue_contains"
        ] = "THIS CUE MUST NOT EXIST"
    elif mutation == "swap_earthset_plan_field":
        next(item for item in mutated["events"] if item["id"] == "earthset_first_contact")[
            "plan_field"
        ] = "request_date_time"
    elif mutation == "shift_earthrise_plus_300":
        next(item for item in mutated["events"] if item["id"] == "earthrise_first_contact")[
            "observed_shift_seconds"
        ] = 300
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def run_testbed(root: Path, mutation: str | None = None) -> dict[str, Any]:
    original_spec = load_spec(root)
    spec = apply_mutation(original_spec, mutation)
    checks: list[dict[str, Any]] = []
    event_results: list[dict[str, Any]] = []
    errors: list[str] = []

    inventory, aggregate, byte_count = corpus_inventory(root, spec)
    corpus_ok = (
        len(inventory) == spec["corpus"]["file_count"]
        and byte_count == spec["corpus"]["byte_count"]
        and aggregate == spec["corpus"]["aggregate_sha256"]
    )
    checks.append(
        {
            "id": "corpus_identity",
            "pass": corpus_ok,
            "observed": {
                "file_count": len(inventory),
                "byte_count": byte_count,
                "aggregate_sha256": aggregate,
            },
        }
    )
    if not corpus_ok:
        errors.append("Corpus identity mismatch")
        return result_record(spec, mutation, checks, event_results, errors)

    try:
        targets = load_targets(root, spec)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"OTR load failure: {exc}")
        return result_record(spec, mutation, checks, event_results, errors)

    for event in spec["events"]:
        try:
            target = find_target(targets, event["target"])
            plan_value = target.get(event["plan_field"])
            if not plan_value:
                raise ValueError(
                    f"Target {event['target']!r} has no value for {event['plan_field']!r}"
                )
            plan_time = parse_utc(plan_value)
            row_number, row = find_transcript_row(root, event)
            observed_time = parse_utc(row["utc"])
            if event.get("observed_shift_seconds"):
                observed_time += timedelta(seconds=event["observed_shift_seconds"])
            delta = (observed_time - plan_time).total_seconds()
            delta_pass = abs(delta - event["expected_delta_seconds"]) <= event["tolerance_seconds"]
            event_results.append(
                {
                    "id": event["id"],
                    "label": event["label"],
                    "target": event["target"],
                    "plan_field": event["plan_field"],
                    "planned_utc": iso_millis(plan_time),
                    "observed_utc": iso_millis(observed_time),
                    "delta_seconds": round(delta, 3),
                    "direction": "early" if delta < 0 else "late" if delta > 0 else "on_time",
                    "transcript": event["transcript"],
                    "transcript_row": row_number,
                    "speaker": row["speaker"],
                    "cue_sha256": hashlib.sha256(row["text"].encode("utf-8")).hexdigest(),
                    "pass": delta_pass,
                }
            )
            if not delta_pass:
                errors.append(
                    f"{event['id']} delta {delta:.3f}s differs from expected "
                    f"{event['expected_delta_seconds']:.3f}s"
                )
        except (OSError, ValueError, KeyError, csv.Error) as exc:
            errors.append(f"{event['id']} failed: {exc}")

    all_events_pass = (
        len(event_results) == len(spec["events"])
        and all(item["pass"] for item in event_results)
    )
    all_early = all_events_pass and all(item["delta_seconds"] < 0 for item in event_results)
    checks.extend(
        [
            {"id": "all_event_oracles", "pass": all_events_pass},
            {"id": "all_frozen_boundaries_precede_plan_fields", "pass": all_early},
        ]
    )
    if not all_events_pass:
        errors.append("One or more event oracles failed")
    if all_events_pass and not all_early:
        errors.append("At least one frozen boundary did not precede its paired plan field")
    return result_record(spec, mutation, checks, event_results, errors)


def result_record(
    spec: dict[str, Any],
    mutation: str | None,
    checks: list[dict[str, Any]],
    events: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, Any]:
    passed = not errors and all(check.get("pass", False) for check in checks)
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": "VERIFIED" if passed and mutation is None else "REJECTED" if not passed else "MUTATION_UNEXPECTEDLY_ACCEPTED",
        "checks": checks,
        "events": events,
        "errors": errors,
        "claim_boundary": spec["acceptance"]["bounded_finding"] if passed and mutation is None else None,
        "unestablished": spec["acceptance"]["explicitly_unestablished"],
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = run_testbed(root)
    mutation_results = {}
    for mutation in (
        "shift_earthrise_plus_300",
        "cue_not_found",
        "swap_earthset_plan_field",
    ):
        mutation_results[mutation] = run_testbed(root, mutation)
    hard_negatives_pass = all(not result["pass"] for result in mutation_results.values())
    return {
        "baseline": baseline,
        "hard_negatives": mutation_results,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "evidence_state": "VERIFIED" if baseline["pass"] and hard_negatives_pass else "FAILED",
    }


def render_markdown(verification: dict[str, Any]) -> str:
    baseline = verification["baseline"]
    lines = [
        "# Artemis II Observation-Execution Testbed — Stage 0 Result",
        "",
        f"- Overall: **{'PASS' if verification['pass'] else 'FAIL'}**",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Baseline run: `{'PASS' if baseline['pass'] else 'FAIL'}`",
        f"- Hard negatives rejected: `{'YES' if verification['hard_negatives_pass'] else 'NO'}`",
        "",
        "## Recomputed event boundaries",
        "",
        "| Event | Planned UTC | Transcript cue UTC | Delta | Result |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for event in baseline["events"]:
        magnitude = abs(event["delta_seconds"])
        minutes = int(magnitude // 60)
        seconds = magnitude - minutes * 60
        delta = f"{minutes}m {seconds:04.1f}s {event['direction']}"
        lines.append(
            f"| {event['label']} | {event['planned_utc']} | {event['observed_utc']} | {delta} | "
            f"{'PASS' if event['pass'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Bounded finding",
            "",
            baseline.get("claim_boundary") or "No finding admitted.",
            "",
            "This verifies transcript-to-plan alignment mechanics only. It does not establish physical contact timing, cause, novelty, Artemis III generalization, or operational consequence.",
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
        choices=("shift_earthrise_plus_300", "cue_not_found", "swap_earthset_plan_field"),
    )
    args = parser.parse_args(argv)

    if args.command == "run":
        payload = run_testbed(args.root, args.mutation)
    else:
        if args.mutation:
            parser.error("--mutation is valid only with the run command")
        payload = verify_with_mutations(args.root)

    if args.json_output:
        write_json(args.json_output, payload)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        if args.command == "verify":
            args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
        else:
            args.markdown_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
