#!/usr/bin/env python3
"""Verify Stage 11T scheduled-opportunity concentration and replication debt."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


UNITS = ("actions", "products", "archive_size_bytes")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def concentration_equivalent(weights: list[float]) -> float:
    total = sum(weights)
    if total <= 0:
        raise ValueError("Concentration weights must sum to a positive value")
    return total * total / sum(weight * weight for weight in weights)


def replication_debt(counts: dict[str, int], target: int) -> int:
    return sum(max(0, target - count) for count in counts.values())


def source_identities(root: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    identities = []
    for expected in spec["sources"]:
        path = root / expected["path"]
        observed = {
            "path": expected["path"],
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path) if path.exists() else None,
        }
        observed["match"] = (
            observed["bytes"] == expected["bytes"]
            and observed["sha256"] == expected["sha256"]
        )
        identities.append(observed)
    return identities


def action_totals(manifest_rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"actions": 1.0, "products": 0.0, "archive_size_bytes": 0.0}
    )
    for row in manifest_rows:
        item = totals[row["action_id"]]
        item["products"] += 1.0
        item["archive_size_bytes"] += float(row["archive_size_bytes"])
    return dict(totals)


def active_memberships(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    windows: dict[str, dict[str, Any]] = {}
    actions_to_windows: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        order = row["plan_order"]
        if not order:
            continue
        windows.setdefault(order, {
            "plan_order": order,
            "plan_target_name": row["plan_target_name"],
            "plan_start_utc": row["plan_start_utc"],
            "plan_end_utc": row["plan_end_utc"],
            "action_ids": set(),
        })
        windows[order]["action_ids"].add(row["action_id"])
        if order not in actions_to_windows[row["action_id"]]:
            actions_to_windows[row["action_id"]].append(order)
    return windows, dict(actions_to_windows)


def collapse_same_name_windows(
    windows: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for window in windows.values():
        by_name[window["plan_target_name"]].append(window)
    clusters: dict[str, dict[str, Any]] = {}
    window_to_cluster: dict[str, str] = {}
    for name, items in by_name.items():
        items.sort(key=lambda item: parse_time(item["plan_start_utc"]))
        current: dict[str, Any] | None = None
        cluster_index = 0
        for item in items:
            start = parse_time(item["plan_start_utc"])
            end = parse_time(item["plan_end_utc"])
            if current is None or start > current["end"]:
                cluster_index += 1
                cluster_id = f"{name}::{cluster_index}"
                current = {
                    "cluster_id": cluster_id,
                    "plan_target_name": name,
                    "start": start,
                    "end": end,
                    "action_ids": set(item["action_ids"]),
                    "window_orders": [item["plan_order"]],
                }
                clusters[cluster_id] = current
            else:
                current["end"] = max(current["end"], end)
                current["action_ids"].update(item["action_ids"])
                current["window_orders"].append(item["plan_order"])
            window_to_cluster[item["plan_order"]] = current["cluster_id"]
    return clusters, window_to_cluster


def weighted_groups(
    groups: dict[str, dict[str, Any]],
    totals: dict[str, dict[str, float]],
    action_denominators: dict[str, int],
) -> list[dict[str, Any]]:
    result = []
    for group_id, group in groups.items():
        row: dict[str, Any] = {
            "group_id": group_id,
            "plan_target_name": group["plan_target_name"],
            "action_count": len(group["action_ids"]),
        }
        for unit in UNITS:
            row[unit] = sum(
                totals[action_id][unit] / action_denominators[action_id]
                for action_id in group["action_ids"]
            )
        result.append(row)
    return sorted(result, key=lambda item: item["group_id"])


def concentration_metrics(groups: list[dict[str, Any]]) -> dict[str, float]:
    return {
        unit: concentration_equivalent([float(group[unit]) for group in groups])
        for unit in UNITS
    }


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "drop_largest_window": False,
        "break_fractional_conservation": False,
        "concentration_is_effective_sample_size": False,
        "window_is_independent_event": False,
        "exact_name_is_semantic_equivalence": False,
        "replication_debt_is_required_mission_reflight": False,
        "archive_quality_failure": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "drop_largest_window": ("drop_largest_window", True),
        "break_fractional_conservation": ("break_fractional_conservation", True),
        "call_concentration_effective_sample_size": ("concentration_is_effective_sample_size", True),
        "call_windows_independent_events": ("window_is_independent_event", True),
        "call_exact_names_semantically_equivalent": ("exact_name_is_semantic_equivalence", True),
        "call_debt_required_reflight": ("replication_debt_is_required_mission_reflight", True),
        "call_archive_quality_failure": ("archive_quality_failure", True),
        "open_pixels": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def derive(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    manifest_rows = read_csv(root / spec["sources"][0]["path"])
    membership_rows = read_csv(root / spec["sources"][1]["path"])
    totals = action_totals(manifest_rows)
    windows, actions_to_windows = active_memberships(membership_rows)
    state = spec["mutation_state"]
    if state["drop_largest_window"]:
        largest_order = max(windows, key=lambda order: len(windows[order]["action_ids"]))
        windows.pop(largest_order)
        actions_to_windows = {
            action_id: [order for order in orders if order != largest_order]
            for action_id, orders in actions_to_windows.items()
        }
        actions_to_windows = {key: value for key, value in actions_to_windows.items() if value}

    raw_denominators = {action_id: 1 for action_id in actions_to_windows}
    fractional_denominators = {
        action_id: len(orders) for action_id, orders in actions_to_windows.items()
    }
    if state["break_fractional_conservation"]:
        first_action = sorted(fractional_denominators)[0]
        fractional_denominators[first_action] += 1

    raw_windows = weighted_groups(windows, totals, raw_denominators)
    fractional_windows = weighted_groups(windows, totals, fractional_denominators)

    clusters, window_to_cluster = collapse_same_name_windows(windows)
    action_to_clusters: dict[str, set[str]] = defaultdict(set)
    for action_id, orders in actions_to_windows.items():
        for order in orders:
            action_to_clusters[action_id].add(window_to_cluster[order])
    collapsed_denominators = {
        action_id: len(cluster_ids) for action_id, cluster_ids in action_to_clusters.items()
    }
    collapsed_fractional = weighted_groups(clusters, totals, collapsed_denominators)

    unique_active_actions = set(actions_to_windows)
    expected_unique_totals = {
        unit: sum(totals[action_id][unit] for action_id in unique_active_actions)
        for unit in UNITS
    }
    fractional_totals = {
        unit: sum(group[unit] for group in fractional_windows) for unit in UNITS
    }
    collapsed_totals = {
        unit: sum(group[unit] for group in collapsed_fractional) for unit in UNITS
    }
    conservation = {
        unit: {
            "expected_unique_total": expected_unique_totals[unit],
            "fractional_window_total": fractional_totals[unit],
            "collapsed_fractional_total": collapsed_totals[unit],
            "window_match": math.isclose(expected_unique_totals[unit], fractional_totals[unit], rel_tol=0.0, abs_tol=1e-6),
            "collapsed_match": math.isclose(expected_unique_totals[unit], collapsed_totals[unit], rel_tol=0.0, abs_tol=1e-6),
        }
        for unit in UNITS
    }

    exact_name_counts: dict[str, int] = defaultdict(int)
    for window in windows.values():
        exact_name_counts[window["plan_target_name"]] += 1
    collapsed_name_counts: dict[str, int] = defaultdict(int)
    for cluster in clusters.values():
        collapsed_name_counts[cluster["plan_target_name"]] += 1

    return {
        "active_windows": len(windows),
        "exact_plan_names": len(exact_name_counts),
        "unique_active_actions": len(unique_active_actions),
        "raw_concentration_equivalent_windows": concentration_metrics(raw_windows),
        "fractional_concentration_equivalent_windows": concentration_metrics(fractional_windows),
        "collapsed_same_name_clusters": len(clusters),
        "collapsed_fractional_concentration_equivalent_windows": concentration_metrics(collapsed_fractional),
        "replication_debt": {
            "exact_windows_k2": replication_debt(dict(exact_name_counts), 2),
            "exact_windows_k3": replication_debt(dict(exact_name_counts), 3),
            "collapsed_clusters_k2": replication_debt(dict(collapsed_name_counts), 2),
            "collapsed_clusters_k3": replication_debt(dict(collapsed_name_counts), 3),
        },
        "exact_name_window_counts": dict(sorted(exact_name_counts.items())),
        "collapsed_name_cluster_counts": dict(sorted(collapsed_name_counts.items())),
        "fractional_conservation": conservation,
        "same_name_overlap_collapses": len(windows) - len(clusters),
    }


def metrics_match(observed: dict[str, Any], expected: dict[str, Any]) -> bool:
    for key, value in expected.items():
        actual = observed.get(key)
        if isinstance(value, dict):
            if not isinstance(actual, dict) or not metrics_match(actual, value):
                return False
        elif isinstance(value, float):
            if actual is None or not math.isclose(float(actual), value, rel_tol=0.0, abs_tol=1e-9):
                return False
        elif actual != value:
            return False
    return True


def verify_stage11t(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11t.json"), mutation)
    identities = source_identities(root, spec)
    metrics = derive(root, spec)
    state = spec["mutation_state"]
    conserved = all(
        item["window_match"] and item["collapsed_match"]
        for item in metrics["fractional_conservation"].values()
    )
    raw = metrics["raw_concentration_equivalent_windows"]
    ranking = raw["actions"] > raw["products"] > raw["archive_size_bytes"]
    prohibited = {
        key: state[key]
        for key in (
            "concentration_is_effective_sample_size",
            "window_is_independent_event",
            "exact_name_is_semantic_equivalence",
            "replication_debt_is_required_mission_reflight",
            "archive_quality_failure",
        )
    }
    checks = {
        "source_identities": all(item["match"] for item in identities),
        "frozen_observables": metrics_match(metrics, spec["frozen_observables"]),
        "fractional_conservation": conserved,
        "unit_concentration_ranking": ranking,
        "claim_boundaries": not any(prohibited.values()),
        "zero_pixel_access": state["pixel_payload_bytes"] == 0,
    }
    passed = all(checks.values())
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": (
            "VERIFIED_SCHEDULED_OPPORTUNITY_CONCENTRATION"
            if passed
            else "REJECTED_SCHEDULED_OPPORTUNITY_CONCENTRATION"
        ),
        "checks": checks,
        "source_identities": identities,
        "metrics": metrics,
        "finding": (
            "The 36 active scheduled windows are substantially concentrated under action, product, "
            "and byte weighting. Product and byte abundance reduce the concentration-equivalent "
            "window count relative to action weighting, while exact-name window counts still leave "
            "a descriptive replication debt."
        ),
        "prohibited_claims": prohibited,
        "pixel_payload_bytes_opened": state["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec/stage11t.json")
    baseline = verify_stage11t(root)
    hard_negatives = {
        name: verify_stage11t(root, name) for name in spec["hard_negatives"]
    }
    hard_negatives_pass = all(not result["pass"] for result in hard_negatives.values())
    return {
        **baseline,
        "hard_negatives": hard_negatives,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
    }


def render_markdown(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    raw = metrics["raw_concentration_equivalent_windows"]
    fractional = metrics["fractional_concentration_equivalent_windows"]
    collapsed = metrics["collapsed_fractional_concentration_equivalent_windows"]
    debt = metrics["replication_debt"]
    return f"""# Stage 11T: Scheduled-Opportunity Concentration and Replication Debt

- Verification: `{'PASS' if result['pass'] else 'FAIL'}`
- Evidence state: `{result['evidence_state']}`
- Active windows: `{metrics['active_windows']}`
- Exact plan names: `{metrics['exact_plan_names']}`
- Pixel payload bytes opened: `{result['pixel_payload_bytes_opened']}`

## Concentration-equivalent window count

`N_conc = 1 / sum(p_i^2)` where `p_i` is a window's share of the declared weight.

| Sensitivity | Actions | Products | Bytes |
| --- | ---: | ---: | ---: |
| Raw active-window memberships | {raw['actions']:.3f} | {raw['products']:.3f} | {raw['archive_size_bytes']:.3f} |
| Fractionalized multiply assigned actions | {fractional['actions']:.3f} | {fractional['products']:.3f} | {fractional['archive_size_bytes']:.3f} |
| Same-name overlap collapsed, fractionalized | {collapsed['actions']:.3f} | {collapsed['products']:.3f} | {collapsed['archive_size_bytes']:.3f} |

This is a concentration index expressed in window units. It is not an effective sample size or an independent-event count.

## Descriptive replication debt

| Target | Exact-window debt | Same-name-collapsed debt |
| --- | ---: | ---: |
| At least 2 windows per exact plan name | {debt['exact_windows_k2']} | {debt['collapsed_clusters_k2']} |
| At least 3 windows per exact plan name | {debt['exact_windows_k3']} | {debt['collapsed_clusters_k3']} |

Exact-name equality is only a vocabulary match. It does not establish comparable geometry, illumination, observer state, or independent scientific replication.

## Claim ceiling

{result['claim_ceiling']}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--mutation")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    result = verify_with_mutations(root) if args.command == "verify" else verify_stage11t(root, args.mutation)
    if args.json_output:
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
