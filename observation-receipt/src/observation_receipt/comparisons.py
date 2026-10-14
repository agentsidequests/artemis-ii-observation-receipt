"""Source-bound unresolved identity and conditional numeric views."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


NEW_RULES = {"identity_resolution_gate", "conditional_comparison_gate"}
OPS = {"eq", "lt", "le", "gt", "ge"}
UNITS = {"count", "bytes", "percent", "index"}


def numeric(value: Any) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def valid_pointer(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("/") and len(value) > 1 and not re.search(r"~(?![01])", value)


def pointer(document: Any, path: str) -> Any:
    if not valid_pointer(path):
        raise ValueError(f"Invalid JSON pointer: {path}")
    value = document
    for part in path[1:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", key) and int(key) < len(value):
            value = value[int(key)]
        else:
            raise ValueError(f"JSON pointer does not resolve: {path}")
    return value


def validate_extensions(case: dict, artifact_ids: set[str], errors: list[str]) -> None:
    extended = case.get("receipt_version") in {"0.3.0", "0.4.0"}
    if not extended:
        if "identity_groups" in case or "conditional_comparisons" in case or any(
            isinstance(claim, dict) and isinstance(claim.get("rule"), dict) and claim["rule"].get("kind") in NEW_RULES
            for claim in case.get("claims", [])
        ):
            errors.append("Identity/comparison extensions require receipt_version 0.3.0")
        return
    collections = {}
    for name in ("identity_groups", "conditional_comparisons"):
        items = case.get(name, [])
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            errors.append(f"{name} must be an array of objects")
            collections[name] = []
            continue
        ids = [item.get("id") for item in items]
        if any(not isinstance(identifier, str) or not identifier for identifier in ids) or len(set(str(i) for i in ids)) != len(ids):
            errors.append(f"{name} must have unique non-empty string ids")
            collections[name] = []
            continue
        collections[name] = items
        for item in items:
            allowed = ({'id','label','state','basis','source_artifact_id','alternatives_pointer','source_locator','note'} if name == 'identity_groups' else
                       {'id','label','source_artifact_id','original_pointer','conditional_pointer','original_label','conditional_label','treatment','metrics','claim_ceiling'})
            if set(item) - allowed:
                errors.append(f"{name} contains unsupported fields")
            if not isinstance(item.get("label"), str) or not item["label"]:
                errors.append(f"{name}.label must be non-empty")
            if not isinstance(item.get("source_artifact_id"), str) or item.get("source_artifact_id") not in artifact_ids:
                errors.append(f"{name}.source_artifact_id does not resolve")
            artifact = next((a for a in case["artifacts"] if a.get("id") == item.get("source_artifact_id")), {})
            if not artifact.get("path"):
                errors.append(f"{name} requires a pinned local artifact, not a reference-only URL")
    for group in collections["identity_groups"]:
        if group.get("state") != "unresolved" or not isinstance(group.get("basis"), str) or group.get("basis") not in {"metadata_candidate", "unverified_link"}:
            errors.append("identity_groups preserve unresolved metadata candidates only; no resolved identity is accepted")
        if not valid_pointer(group.get("alternatives_pointer")):
            errors.append("identity_groups.alternatives_pointer must be a JSON pointer")
        if "selected_identity" in group:
            errors.append("identity_groups cannot select a representative")
    metric_ids = {}
    for comparison in collections["conditional_comparisons"]:
        for field in ("original_pointer", "conditional_pointer"):
            if not valid_pointer(comparison.get(field)):
                errors.append(f"conditional_comparisons.{field} must be a JSON pointer")
        if comparison.get("original_pointer") == comparison.get("conditional_pointer"):
            errors.append("Original and conditional roots must be distinct")
        for field in ("original_label", "conditional_label", "treatment", "claim_ceiling"):
            if not isinstance(comparison.get(field), str) or not comparison[field]:
                errors.append(f"conditional_comparisons.{field} must be non-empty")
        metrics = comparison.get("metrics")
        if not isinstance(metrics, list) or not metrics or any(not isinstance(m, dict) for m in metrics):
            errors.append("conditional_comparisons.metrics must be a non-empty object array")
            continue
        ids = [m.get("id") for m in metrics]
        if any(not isinstance(i, str) or not i for i in ids) or len(set(str(i) for i in ids)) != len(ids):
            errors.append("Comparison metric ids must be unique non-empty strings")
            continue
        metric_ids[comparison.get("id")] = set(str(i) for i in ids)
        for metric in metrics:
            if set(metric) - {'id','label','unit','pointer','scale','places'}:
                errors.append("Comparison metric contains unsupported fields")
            if not isinstance(metric.get("unit"), str) or metric.get("unit") not in UNITS or not valid_pointer(metric.get("pointer")):
                errors.append("Comparison metric requires a supported unit and JSON pointer")
            if any(field in metric for field in ("original", "conditional", "delta")):
                errors.append("Comparison metric numbers must come from the pinned source, not case literals")
            if not isinstance(metric.get("label"), str) or not metric["label"]:
                errors.append("Comparison metric label must be non-empty")
            if not numeric(metric.get("scale", 1)) or metric.get("scale", 1) <= 0:
                errors.append("Comparison metric scale must be positive and finite")
            if type(metric.get("places", 3)) is not int or not 0 <= metric.get("places", 3) <= 8:
                errors.append("Comparison metric places must be an integer from zero to eight")
    groups = {str(g.get("id")) for g in collections["identity_groups"]}
    for claim in case.get("claims", []):
        rule = claim.get("rule", {})
        if rule.get("kind") == "identity_resolution_gate" and rule.get("group_id") not in groups:
            errors.append("Identity gate group_id does not resolve")
        if rule.get("kind") != "conditional_comparison_gate":
            continue
        comparison_id = rule.get("comparison_id")
        conditions = rule.get("conditions")
        if not isinstance(comparison_id, str) or comparison_id not in metric_ids:
            errors.append("Conditional gate comparison_id does not resolve")
            continue
        if not isinstance(conditions, list) or not conditions or any(not isinstance(c, dict) for c in conditions):
            errors.append("Conditional gate conditions must be a non-empty object array")
            continue
        for condition in conditions:
            if set(condition) - {'metric_id','op','value','other_metric_id'}:
                errors.append("Conditional gate contains unsupported condition fields")
            literal = "value" in condition
            other = condition.get("other_metric_id")
            rhs_valid = numeric(condition.get("value")) if literal else isinstance(other, str) and other in metric_ids[comparison_id]
            if not isinstance(condition.get("metric_id"), str) or condition.get("metric_id") not in metric_ids.get(comparison_id, set()) or not isinstance(condition.get("op"), str) or condition.get("op") not in OPS or not rhs_valid or (literal and "other_metric_id" in condition):
                errors.append("Conditional gate requires a resolved metric, supported operator and finite numeric value")
            elif not literal:
                comparison = next(c for c in collections["conditional_comparisons"] if c["id"] == comparison_id)
                units = {m["id"]: m["unit"] for m in comparison["metrics"]}
                if units[condition["metric_id"]] != units[other]:
                    errors.append("Metric-to-metric conditions require matching units")


def read_source(artifact: dict, root: Path, checks: dict) -> Any | None:
    if not checks[artifact["id"]]["match"]:
        return None
    path = (root / artifact["path"]).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError("Comparison artifact escapes the declared root") from error
    payload = path.read_bytes()
    if len(payload) != artifact["bytes"] or hashlib.sha256(payload).hexdigest() != artifact["sha256"]:
        return None
    return json.loads(payload)


def build_views(case: dict, root: Path, artifact_checks: list[dict]) -> tuple[list[dict], list[dict]]:
    artifacts = {a["id"]: a for a in case["artifacts"]}
    checks = {c["id"]: c for c in artifact_checks}
    cache = {}
    def source(identifier):
        if identifier not in cache:
            cache[identifier] = read_source(artifacts[identifier], root, checks)
        return cache[identifier]
    identities = []
    for group in case.get("identity_groups", []):
        data = source(group["source_artifact_id"])
        alternatives = [] if data is None else pointer(data, group["alternatives_pointer"])
        if data is not None and (not isinstance(alternatives, list) or len(alternatives) < 2 or any(not isinstance(i, str) or not i for i in alternatives) or len(set(alternatives)) != len(alternatives)):
            raise ValueError("Identity alternatives must contain at least two distinct non-empty source identifiers")
        identities.append({**group, "alternatives": alternatives, "integrity_verified": data is not None,
                           "status": "UNRESOLVED_METADATA_IDENTITY" if data is not None else "BLOCKED_IDENTITY_INTEGRITY"})
    comparisons = []
    for item in case.get("conditional_comparisons", []):
        data = source(item["source_artifact_id"])
        rows = []
        if data is not None:
            original = pointer(data, item["original_pointer"])
            conditional = pointer(data, item["conditional_pointer"])
            for metric in item["metrics"]:
                old, new = pointer(original, metric["pointer"]), pointer(conditional, metric["pointer"])
                if not numeric(old) or not numeric(new):
                    raise ValueError(f"Comparison metric is not a finite number: {metric['id']}")
                scale = metric.get("scale", 1)
                if metric["unit"] in {"count", "bytes"} and (type(old) is not int or type(new) is not int or scale != 1):
                    raise ValueError("Count/byte metrics require integer source values and scale one")
                if metric["unit"] in {"count", "bytes"} and (old < 0 or new < 0):
                    raise ValueError("Count/byte source values cannot be negative")
                old, new = old * scale, new * scale
                if not numeric(old) or not numeric(new):
                    raise ValueError("Scaled comparison metric is not finite")
                rows.append({**metric, "original": old, "conditional": new, "delta": new-old,
                             "delta_unit": "percentage points" if metric["unit"] == "percent" else metric["unit"]})
        comparisons.append({**item, "metrics": rows, "integrity_verified": data is not None,
                            "status": "VERIFIED_CONDITIONAL_VIEW" if data is not None else "BLOCKED_COMPARISON_INTEGRITY",
                            "replaces_original": False})
    return identities, comparisons


def evaluate_extension(rule: dict, identities: list[dict], comparisons: list[dict]) -> dict:
    if rule["kind"] == "identity_resolution_gate":
        group = next(g for g in identities if g["id"] == rule["group_id"])
        return {"status": "BLOCKED_IDENTITY_UNRESOLVED" if group["integrity_verified"] else "BLOCKED_IDENTITY_INTEGRITY",
                "group_id": group["id"], "alternatives": group["alternatives"], "representative_selected": False}
    comparison = next(c for c in comparisons if c["id"] == rule["comparison_id"])
    if not comparison["integrity_verified"]:
        return {"status": "BLOCKED_COMPARISON_INTEGRITY", "comparison_id": comparison["id"]}
    metrics = {m["id"]: m for m in comparison["metrics"]}
    def holds(side):
        for condition in rule["conditions"]:
            a = metrics[condition["metric_id"]][side]
            b = condition["value"] if "value" in condition else metrics[condition["other_metric_id"]][side]
            result = {"eq": a == b, "lt": a < b, "le": a <= b, "gt": a > b, "ge": a >= b}[condition["op"]]
            if not result:
                return False
        return True
    original, conditional = holds("original"), holds("conditional")
    status = "SUPPORTED_CONDITIONAL_STABILITY" if original and conditional else "REFUTED_CONDITIONAL_STABILITY" if original and not conditional else "CHANGED_CONDITIONAL_DISPOSITION" if conditional else "UNSUPPORTED_IN_BOTH_VIEWS"
    return {"status": status, "comparison_id": comparison["id"], "original_holds": original,
            "conditional_holds": conditional, "same_disposition": original == conditional, "replaces_original": False}
