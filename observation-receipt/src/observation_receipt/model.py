"""Case validation for Observation Receipt."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .comparisons import NEW_RULES, validate_extensions
from .steward_links import validate as validate_steward_links


RECEIPT_VERSION = "0.4.0"
SUPPORTED_VERSIONS = {"0.2.0", "0.3.0", RECEIPT_VERSION}
DISPOSITIONS = {"accepted", "ambiguous", "rejected", "retracted"}
TIME_STATES = {"exact", "interval", "unknown"}
ELICITATION_STATES = {"unprompted", "prompted", "socially_cued", "unknown"}
INDEPENDENCE_STATES = {"independent", "dependent", "not_established"}
CAPABILITY_STATES = {"demonstrated", "not_demonstrated", "not_applicable"}
RULE_KINDS = NEW_RULES | {
    "ledger_summary",
    "window_after_boundary",
    "window_capability_gate",
    "count_floor_sphere",
    "required_measurement_fields",
    "witness_independence_gate",
}


class CaseValidationError(ValueError):
    """Raised when a case cannot be evaluated safely."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Case validation failed:\n- " + "\n- ".join(errors))


def _parse_utc(value: str, location: str, errors: list[str]) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            errors.append(f"{location} must include a timezone")
    except (TypeError, ValueError, AttributeError):
        errors.append(f"{location} must be an ISO 8601 date-time")


def _unique_ids(items: Any, location: str, errors: list[str]) -> set[str]:
    if not isinstance(items, list):
        errors.append(f"{location} must be an array")
        return set()
    values: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            errors.append(f"{location}[{index}].id must be a non-empty string")
            continue
        values.append(item["id"])
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        errors.append(f"{location} contains duplicate ids: {', '.join(duplicates)}")
    return set(values)


def validate_case(case: dict[str, Any]) -> None:
    """Validate the portable case contract and fail closed on ambiguity."""

    errors: list[str] = []
    required = {
        "receipt_version",
        "case_id",
        "title",
        "artifacts",
        "facts",
        "candidates",
        "observation_windows",
        "measurement_function",
        "claims",
        "expected_findings",
        "claim_ceiling",
    }
    missing = sorted(required - set(case))
    if missing:
        errors.append(f"case is missing required fields: {', '.join(missing)}")
    if not isinstance(case.get("receipt_version"), str) or case.get("receipt_version") not in SUPPORTED_VERSIONS:
        errors.append("receipt_version must be 0.2.0, 0.3.0 or 0.4.0")
    if not isinstance(case.get("case_id"), str) or not case.get("case_id"):
        errors.append("case_id must be a non-empty string")
    if not isinstance(case.get("title"), str) or not case.get("title"):
        errors.append("title must be a non-empty string")

    artifact_ids = _unique_ids(case.get("artifacts"), "artifacts", errors)
    candidate_ids = _unique_ids(case.get("candidates"), "candidates", errors)
    window_ids = _unique_ids(case.get("observation_windows"), "observation_windows", errors)
    claim_ids = _unique_ids(case.get("claims"), "claims", errors)

    for index, artifact in enumerate(case.get("artifacts", [])):
        if not isinstance(artifact, dict):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        if not artifact.get("path") and not artifact.get("url"):
            errors.append(f"artifacts[{index}] must declare path or url")
        if artifact.get("path"):
            if type(artifact.get("bytes")) is not int or artifact["bytes"] < 0:
                errors.append(f"artifacts[{index}].bytes must be a non-negative integer")
            digest = artifact.get("sha256")
            if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                errors.append(f"artifacts[{index}].sha256 must be 64 lowercase hexadecimal characters")

    mark_ids: list[str] = []
    for index, candidate in enumerate(case.get("candidates", [])):
        if not isinstance(candidate, dict):
            errors.append(f"candidates[{index}] must be an object")
            continue
        if candidate.get("disposition") not in DISPOSITIONS:
            errors.append(f"candidates[{index}].disposition is unsupported")
        marks = candidate.get("witness_marks")
        if not isinstance(marks, list):
            errors.append(f"candidates[{index}].witness_marks must be an array")
            continue
        for mark_index, mark in enumerate(marks):
            location = f"candidates[{index}].witness_marks[{mark_index}]"
            if not isinstance(mark, dict):
                errors.append(f"{location} must be an object")
                continue
            mark_id = mark.get("id")
            if not isinstance(mark_id, str) or not mark_id:
                errors.append(f"{location}.id must be a non-empty string")
            else:
                mark_ids.append(mark_id)
            if not isinstance(mark.get("observer"), str) or not mark.get("observer"):
                errors.append(f"{location}.observer must be a non-empty string")
            time_state = mark.get("time_state")
            if time_state not in TIME_STATES:
                errors.append(f"{location}.time_state is unsupported")
            marked_at = mark.get("marked_at_utc")
            if time_state == "exact" and not marked_at:
                errors.append(f"{location}.marked_at_utc is required for an exact mark")
            if marked_at:
                _parse_utc(marked_at, f"{location}.marked_at_utc", errors)
            if mark.get("elicitation_state") not in ELICITATION_STATES:
                errors.append(f"{location}.elicitation_state is unsupported")
            if mark.get("independence_state") not in INDEPENDENCE_STATES:
                errors.append(f"{location}.independence_state is unsupported")
            source_id = mark.get("source_artifact_id")
            if source_id not in artifact_ids:
                errors.append(f"{location}.source_artifact_id does not resolve")
    duplicate_marks = sorted({value for value in mark_ids if mark_ids.count(value) > 1})
    if duplicate_marks:
        errors.append(f"witness marks contain duplicate ids: {', '.join(duplicate_marks)}")

    for index, window in enumerate(case.get("observation_windows", [])):
        if not isinstance(window, dict):
            errors.append(f"observation_windows[{index}] must be an object")
            continue
        for field in ("start_utc", "stop_utc"):
            if field not in window:
                errors.append(f"observation_windows[{index}].{field} is required")
            else:
                _parse_utc(window[field], f"observation_windows[{index}].{field}", errors)
        capabilities = window.get("capabilities")
        if not isinstance(capabilities, dict):
            errors.append(f"observation_windows[{index}].capabilities must be an object")
        else:
            for name, capability in capabilities.items():
                if not isinstance(capability, dict) or capability.get("state") not in CAPABILITY_STATES:
                    errors.append(
                        f"observation_windows[{index}].capabilities.{name}.state must be demonstrated, not_demonstrated, or not_applicable"
                    )

    facts = case.get("facts")
    if not isinstance(facts, dict):
        errors.append("facts must be an object")

    for index, claim in enumerate(case.get("claims", [])):
        if not isinstance(claim, dict):
            errors.append(f"claims[{index}] must be an object")
            continue
        rule = claim.get("rule")
        if not isinstance(rule, dict) or rule.get("kind") not in RULE_KINDS:
            errors.append(f"claims[{index}].rule.kind is unsupported")
            continue
        if rule["kind"] in {"window_after_boundary", "window_capability_gate"} and rule.get("window_id") not in window_ids:
            errors.append(f"claims[{index}].rule.window_id does not resolve")
        if rule["kind"] == "witness_independence_gate" and rule.get("candidate_id") not in candidate_ids:
            errors.append(f"claims[{index}].rule.candidate_id does not resolve")

    expected = case.get("expected_findings")
    if not isinstance(expected, dict):
        errors.append("expected_findings must be an object")
    elif set(expected) != claim_ids:
        errors.append("expected_findings keys must match claim ids exactly")

    if not errors:
        validate_extensions(case, artifact_ids, errors)
    if not errors:
        validate_steward_links(case, artifact_ids, errors)
    if errors:
        raise CaseValidationError(errors)
