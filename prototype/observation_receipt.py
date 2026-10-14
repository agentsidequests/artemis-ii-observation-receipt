#!/usr/bin/env python3
"""Evaluate a compact Observation Receipt case without external dependencies."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def indexed(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    values = {item["id"]: item for item in items}
    if len(values) != len(items):
        raise ValueError("Identifiers must be unique")
    return values


def evaluate_claim(case: dict[str, Any], claim: dict[str, Any]) -> dict[str, Any]:
    rule = claim["rule"]
    kind = rule["kind"]
    candidates = case["candidates"]
    windows = indexed(case["observation_windows"])
    facts = case["facts"]
    finding: dict[str, Any] = {
        "claim_id": claim["id"],
        "proposition": claim["proposition"],
        "rule_kind": kind,
        "claim_ceiling": claim["claim_ceiling"],
    }

    if kind == "ledger_summary":
        selected = [item for item in candidates if item["disposition"] == rule["disposition"]]
        marks = sum(len(item["witnesses"]) for item in selected)
        observers = sorted({name for item in selected for name in item["witnesses"]})
        observed = {
            "event_count": len(selected),
            "witness_marks": marks,
            "unique_observers": len(observers),
            "observers": observers,
        }
        expected = {
            "event_count": rule["expected_event_count"],
            "witness_marks": rule["expected_witness_marks"],
            "unique_observers": rule["expected_unique_observers"],
        }
        finding["status"] = "SUPPORTED" if all(observed[key] == expected[key] for key in expected) else "REFUTED_LEDGER_MISMATCH"
        finding["observed"] = observed
        finding["expected"] = expected

    elif kind == "window_after_boundary":
        window = windows[rule["window_id"]]
        start = parse_utc(window["start_utc"])
        boundary = parse_utc(facts[rule["boundary_fact"]])
        gap = (start - boundary).total_seconds()
        finding["status"] = "REFUTED_NONOVERLAP" if gap > 0 else "NOT_REFUTED_BY_BOUNDARY"
        finding["window_id"] = window["id"]
        finding["gap_seconds"] = gap

    elif kind == "window_capability_gate":
        window = windows[rule["window_id"]]
        start = parse_utc(window["start_utc"])
        stop = parse_utc(window["stop_utc"])
        event_time = parse_utc(facts[rule["event_time_fact"]])
        overlaps = start <= event_time <= stop
        missing = [name for name in rule["required_capabilities"] if not window["capabilities"].get(name, False)]
        if not overlaps:
            status = "REFUTED_NONOVERLAP"
        elif missing:
            status = "BLOCKED_INSUFFICIENT_CAPABILITY"
        else:
            status = "SUPPORTED_BY_DECLARED_GATE"
        finding.update({"status": status, "window_id": window["id"], "overlaps": overlaps, "missing_capabilities": missing})

    elif kind == "count_floor_sphere":
        count = sum(item["disposition"] == rule["disposition"] for item in candidates)
        radius = float(facts[rule["radius_fact"]])
        duration = float(facts[rule["duration_fact"]])
        area = 4.0 * math.pi * radius * radius
        value = count / (area * duration)
        expected = float(rule["expected_value_km2_hour"])
        error = abs(value - expected) / expected
        finding["status"] = "SUPPORTED_WITH_ASSUMPTIONS" if error <= float(rule["relative_tolerance"]) else "REFUTED_NUMERIC_MISMATCH"
        finding.update({
            "accepted_event_count": count,
            "sphere_area_km2": area,
            "duration_hours": duration,
            "value_km2_hour": value,
            "expected_value_km2_hour": expected,
            "relative_error": error,
        })

    elif kind == "required_measurement_fields":
        measurement = case["measurement_function"]
        missing = [name for name in rule["fields"] if measurement.get(name) is None]
        finding["status"] = "BLOCKED_MISSING_MEASUREMENT_FUNCTION" if missing else "SUPPORTED_BY_DECLARED_FIELDS"
        finding["missing_fields"] = missing

    else:
        raise ValueError(f"Unsupported claim rule: {kind}")
    return finding


def evaluate(case: dict[str, Any], root: Path) -> dict[str, Any]:
    if case.get("receipt_version") != "0.1.0":
        raise ValueError("Unsupported receipt version")
    artifact_checks = []
    for artifact in case["artifacts"]:
        path = root / artifact["path"]
        observed = {
            "id": artifact["id"],
            "path": artifact["path"],
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        observed["match"] = observed["bytes"] == artifact["bytes"] and observed["sha256"] == artifact["sha256"]
        artifact_checks.append(observed)
    findings = [evaluate_claim(case, claim) for claim in case["claims"]]
    statuses = {finding["claim_id"]: finding["status"] for finding in findings}
    checks = {
        "artifacts_match": all(item["match"] for item in artifact_checks),
        "candidate_ids_unique": len(indexed(case["candidates"])) == len(case["candidates"]),
        "window_ids_unique": len(indexed(case["observation_windows"])) == len(case["observation_windows"]),
        "claim_ids_unique": len(indexed(case["claims"])) == len(case["claims"]),
        "expected_case_findings": statuses == {
            "accepted-ledger": "SUPPORTED",
            "later-window-tested-ledger-events": "REFUTED_NONOVERLAP",
            "overlap-null-excludes-report": "BLOCKED_INSUFFICIENT_CAPABILITY",
            "all-lunar-count-floor": "SUPPORTED_WITH_ASSUMPTIONS",
            "calibrated-impact-flux": "BLOCKED_MISSING_MEASUREMENT_FUNCTION",
        },
    }
    return {
        "receipt_version": case["receipt_version"],
        "case_id": case["case_id"],
        "pass": all(checks.values()),
        "checks": checks,
        "artifact_checks": artifact_checks,
        "findings": findings,
        "summary": {
            "supported": sum(status.startswith("SUPPORTED") for status in statuses.values()),
            "refuted": sum(status.startswith("REFUTED") for status in statuses.values()),
            "blocked": sum(status.startswith("BLOCKED") for status in statuses.values()),
        },
    }


def to_markdown(receipt: dict[str, Any]) -> str:
    lines = [
        "# Observation Receipt: Artemis II flashes",
        "",
        f"State: `{'VERIFIED' if receipt['pass'] else 'FAILED'}`",
        "",
        "| Claim | Status |",
        "|---|---|",
    ]
    for finding in receipt["findings"]:
        lines.append(f"| {finding['proposition']} | `{finding['status']}` |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The receipt separates support, refutation, and blocked inference. The later window does not overlap the annotation's background-photo epoch. That epoch does not certify ledger creation or bound all five event times; coverage of every accepted event remains unestablished. Temporal overlap alone does not make the other camera null exclusionary because required capabilities are absent. Five accepted events support the conservative count floor, while the calibrated-flux claim remains blocked by the missing measurement function.",
        "",
        "This prototype does not accept a scientific or operational claim on NASA's behalf.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, nargs="?", default=Path("examples/artemis-ii-flashes.observation-receipt.json"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    case_path = args.case if args.case.is_absolute() else root / args.case
    case = json.loads(case_path.read_text(encoding="utf-8"))
    receipt = evaluate(copy.deepcopy(case), root)
    if args.write:
        (root / "results/observation-receipt-artemis-fixture.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
        (root / "results/observation-receipt-artemis-fixture.md").write_text(to_markdown(receipt), encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
