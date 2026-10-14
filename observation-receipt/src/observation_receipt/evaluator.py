"""Deterministic claim evaluation for Observation Receipt."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import validate_case
from .comparisons import NEW_RULES, build_views, evaluate_extension
from . import steward_links


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def indexed(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def _measurement_present(value: Any) -> bool:
    if isinstance(value, dict):
        return value.get("value") is not None
    return value is not None


def evaluate_claim(case: dict[str, Any], claim: dict[str, Any]) -> dict[str, Any]:
    rule = claim["rule"]
    kind = rule["kind"]
    candidates = case["candidates"]
    candidate_index = indexed(candidates)
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
        marks = [mark for item in selected for mark in item["witness_marks"]]
        observers = sorted({mark["observer"] for mark in marks})
        observed = {
            "event_count": len(selected),
            "witness_marks": len(marks),
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
        capabilities = window["capabilities"]
        missing = [
            name
            for name in rule["required_capabilities"]
            if capabilities.get(name, {}).get("state") != "demonstrated"
        ]
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
        finding.update(
            {
                "accepted_event_count": count,
                "sphere_area_km2": area,
                "duration_hours": duration,
                "value_km2_hour": value,
                "expected_value_km2_hour": expected,
                "relative_error": error,
            }
        )

    elif kind == "required_measurement_fields":
        measurement = case["measurement_function"]
        missing = [name for name in rule["fields"] if not _measurement_present(measurement.get(name))]
        finding["status"] = "BLOCKED_MISSING_MEASUREMENT_FUNCTION" if missing else "SUPPORTED_BY_DECLARED_FIELDS"
        finding["missing_fields"] = missing

    elif kind == "witness_independence_gate":
        candidate = candidate_index[rule["candidate_id"]]
        marks = candidate["witness_marks"]
        declared_model = candidate.get("witness_dependency_model")
        independent = [mark for mark in marks if mark["independence_state"] == "independent"]
        if not declared_model:
            status = "BLOCKED_DEPENDENCE_MODEL_MISSING"
        elif len(independent) < int(rule["required_independent_marks"]):
            status = "BLOCKED_INSUFFICIENT_INDEPENDENT_MARKS"
        else:
            status = "SUPPORTED_BY_DECLARED_DEPENDENCE_MODEL"
        finding.update(
            {
                "status": status,
                "candidate_id": candidate["id"],
                "witness_marks": len(marks),
                "independent_marks": len(independent),
                "dependency_model": declared_model,
            }
        )

    else:
        raise ValueError(f"Unsupported claim rule: {kind}")
    return finding


def verify_artifacts(case: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    resolved_root = root.resolve()
    for artifact in case["artifacts"]:
        if not artifact.get("path"):
            checks.append(
                {
                    "id": artifact["id"],
                    "url": artifact["url"],
                    "state": "REFERENCE_ONLY",
                    "match": True,
                }
            )
            continue
        path = (resolved_root / artifact["path"]).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError as error:
            raise ValueError(f"Artifact path escapes the declared root: {artifact['path']}") from error
        exists = path.is_file()
        observed_bytes = path.stat().st_size if exists else None
        observed_sha256 = sha256_file(path) if exists else None
        match = exists and observed_bytes == artifact["bytes"] and observed_sha256 == artifact["sha256"]
        checks.append(
            {
                "id": artifact["id"],
                "path": artifact["path"],
                "exists": exists,
                "bytes": observed_bytes,
                "sha256": observed_sha256,
                "expected_bytes": artifact["bytes"],
                "expected_sha256": artifact["sha256"],
                "state": "MATCH" if match else "MISMATCH",
                "match": match,
            }
        )
    return checks


def evaluate_case(case: dict[str, Any], root: Path) -> dict[str, Any]:
    """Validate and evaluate a case into a deterministic receipt."""

    validate_case(case)
    artifact_checks = verify_artifacts(case, root)
    identities, comparisons = build_views(case, root, artifact_checks)
    links = steward_links.build(case, root, artifact_checks, identities)
    findings = []
    for claim in case["claims"]:
        if claim["rule"]["kind"] in NEW_RULES:
            findings.append({"claim_id": claim["id"], "proposition": claim["proposition"],
                             "rule_kind": claim["rule"]["kind"], "claim_ceiling": claim["claim_ceiling"],
                             **evaluate_extension(claim["rule"], identities, comparisons)})
        else:
            findings.append(evaluate_claim(case, claim))
    statuses = {finding["claim_id"]: finding["status"] for finding in findings}
    expected_match = statuses == case["expected_findings"]
    checks = {
        "case_contract_valid": True,
        "artifacts_match": all(item["match"] for item in artifact_checks),
        "expected_findings_match": expected_match,
    }
    if identities or comparisons:
        checks["extension_sources_match"] = all(view["integrity_verified"] for view in identities + comparisons)
    if links:
        checks['steward_link_sources_match'] = all(link['integrity_verified'] for link in links)
    receipt = {
        "receipt_version": case["receipt_version"],
        "case_id": case["case_id"],
        "title": case["title"],
        "state": "VERIFIED" if all(checks.values()) else "FAILED",
        "pass": all(checks.values()),
        "checks": checks,
        "artifact_checks": artifact_checks,
        "findings": findings,
        "summary": {
            "supported": sum(status.startswith("SUPPORTED") for status in statuses.values()),
            "refuted": sum(status.startswith("REFUTED") for status in statuses.values()),
            "blocked": sum(status.startswith("BLOCKED") for status in statuses.values()),
            "other": sum(
                not status.startswith(("SUPPORTED", "REFUTED", "BLOCKED")) for status in statuses.values()
            ),
        },
        "claim_ceiling": case["claim_ceiling"],
        "next_steps": case.get("next_steps", []),
    }
    if case["receipt_version"] in {"0.3.0", "0.4.0"}:
        receipt.update({"identity_groups": identities, "conditional_comparisons": comparisons})
    if case['receipt_version'] == '0.4.0':
        receipt['steward_links'] = links
    return receipt
