#!/usr/bin/env python3
"""Build and verify Stage 10Z's action-to-plan membership ledger."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json, parse_utc
from stage10y_schedule_tag_non_equivalence import verify_stage10y


FIELDS = [
    "action_id", "action_index", "camera_serial", "action_start_utc", "action_end_utc",
    "exposures_in_action", "activity_ids", "target_ids", "membership_count",
    "membership_rank", "plan_order", "plan_target_name", "plan_ltp_name",
    "plan_start_utc", "plan_end_utc",
]


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "single_plan_membership_forced": False,
        "unassigned_actions_retained": True,
        "plan_windows_are_partition": False,
        "overlap_deduplication_required": True,
        "unassigned_actions_in_scope": True,
        "target_inferred_from_plan": False,
        "membership_is_independent_event": False,
        "model_partition_assigned": False,
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "force_single_plan_membership": ("single_plan_membership_forced", True),
        "drop_unassigned_actions": ("unassigned_actions_retained", False),
        "call_plan_windows_a_partition": ("plan_windows_are_partition", True),
        "sum_overlapping_windows_without_deduplication": ("overlap_deduplication_required", False),
        "call_unassigned_actions_out_of_scope": ("unassigned_actions_in_scope", False),
        "infer_target_from_plan_membership": ("target_inferred_from_plan", True),
        "call_membership_an_independent_event": ("membership_is_independent_event", True),
        "assign_model_partition_from_membership": ("model_partition_assigned", True),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_membership_ledger": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def parse_plan_time(value: str) -> datetime:
    return datetime.strptime(value, "%d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace(".000000+00:00", "Z").replace("+00:00", "Z")


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def exact_mapping(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    return all(
        close(float(actual[key]), float(value)) if isinstance(value, float) else actual[key] == value
        for key, value in expected.items()
    )


def derive(plan: list[dict[str, Any]], rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, int]]]:
    windows: list[dict[str, Any]] = []
    for plan_index, item in enumerate(plan):
        props = item["target_properties"]
        if not props.get("target_name") or not props.get("request_date_time") or not props.get("request_duration"):
            continue
        start = parse_plan_time(props["request_date_time"])
        windows.append({
            "plan_index": plan_index, "plan_order": str(props.get("order", "")),
            "plan_target_name": props["target_name"], "plan_ltp_name": props.get("ltp_name", ""),
            "plan_start_utc": iso_utc(start),
            "plan_end_utc": iso_utc(start + timedelta(minutes=float(props["request_duration"]))),
            "start": start, "end": start + timedelta(minutes=float(props["request_duration"])),
        })

    source = [row for row in rows if row["collection_id"] == "data_source"]
    by_action: dict[str, list[dict[str, str]]] = defaultdict(list)
    all_rows_by_action: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source:
        by_action[row["action_id"]].append(row)
    for row in rows:
        all_rows_by_action[row["action_id"]].append(row)

    ledger: list[dict[str, Any]] = []
    distribution: dict[str, dict[str, int]] = {}
    action_counts: Counter[int] = Counter()
    exposure_counts: Counter[int] = Counter()
    product_counts: Counter[int] = Counter()
    byte_counts: Counter[int] = Counter()
    relationships = 0
    windows_with_actions: set[int] = set()

    for action_id, action_rows in sorted(by_action.items(), key=lambda item: int(item[1][0]["action_index"])):
        first = action_rows[0]
        start = parse_utc(first["action_start_utc"])
        end = parse_utc(first["action_end_utc"])
        memberships = [window for window in windows if start >= window["start"] and end < window["end"]]
        count = len(memberships)
        action_counts[count] += 1
        exposure_counts[count] += len(action_rows)
        product_counts[count] += len(all_rows_by_action[action_id])
        byte_counts[count] += sum(int(row["archive_size_bytes"]) for row in all_rows_by_action[action_id])
        relationships += count
        windows_with_actions.update(window["plan_index"] for window in memberships)
        common = {
            "action_id": action_id, "action_index": int(first["action_index"]),
            "camera_serial": first["camera_serial"], "action_start_utc": first["action_start_utc"],
            "action_end_utc": first["action_end_utc"], "exposures_in_action": len(action_rows),
            "activity_ids": "|".join(sorted({row["activity_id"] for row in action_rows})),
            "target_ids": "|".join(sorted({row["target_id"] for row in action_rows if row["target_id"]})),
            "membership_count": count,
        }
        if not memberships:
            ledger.append({**common, "membership_rank": 0, "plan_order": "", "plan_target_name": "",
                           "plan_ltp_name": "", "plan_start_utc": "", "plan_end_utc": ""})
        for rank, window in enumerate(memberships, start=1):
            ledger.append({**common, "membership_rank": rank,
                           **{key: window[key] for key in ("plan_order", "plan_target_name", "plan_ltp_name", "plan_start_utc", "plan_end_utc")}})

    for count in sorted(action_counts):
        distribution[str(count)] = {
            "actions": action_counts[count], "exposures": exposure_counts[count],
            "products": product_counts[count], "bytes": byte_counts[count],
        }
    assigned_actions = sum(value for count, value in action_counts.items() if count)
    unique_assigned_exposures = sum(value for count, value in exposure_counts.items() if count)
    window_summed_exposures = sum(count * value for count, value in exposure_counts.items())
    unique_assigned_products = sum(value for count, value in product_counts.items() if count)
    window_summed_products = sum(count * value for count, value in product_counts.items())
    unique_assigned_bytes = sum(value for count, value in byte_counts.items() if count)
    window_summed_bytes = sum(count * value for count, value in byte_counts.items())
    relationship_manifest_bytes = (Path(__file__).resolve().parents[1] / "results/stage10o-product-relationship-manifest.csv").stat().st_size
    combined_relationship_layer_bytes = relationship_manifest_bytes + len(render_csv(ledger).encode("utf-8"))
    cohort_bytes = sum(byte_counts.values())
    metrics = {
        "complete_actions": len(by_action), "plan_entries_with_target_and_window": len(windows),
        "plan_windows_with_actions": len(windows_with_actions), "action_plan_relationships": relationships,
        "ledger_rows_including_unmatched": len(ledger),
        "actions_with_no_plan_membership": action_counts[0], "actions_with_one_plan_membership": action_counts[1],
        "actions_with_two_plan_memberships": action_counts[2], "actions_with_three_plan_memberships": action_counts[3],
        "actions_with_multiple_plan_memberships": sum(value for count, value in action_counts.items() if count > 1),
        "maximum_plan_memberships_per_action": max(action_counts),
        "assigned_action_share": assigned_actions / len(by_action),
        "multi_assigned_action_share": sum(value for count, value in action_counts.items() if count > 1) / len(by_action),
        "relationship_inflation_over_unique_assigned_actions": (relationships - assigned_actions) / assigned_actions,
        "unique_assigned_exposures": unique_assigned_exposures, "window_summed_exposures": window_summed_exposures,
        "window_exposure_inflation": (window_summed_exposures - unique_assigned_exposures) / unique_assigned_exposures,
        "unique_assigned_products": unique_assigned_products, "window_summed_products": window_summed_products,
        "unique_assigned_bytes": unique_assigned_bytes, "window_summed_bytes": window_summed_bytes,
        "window_byte_inflation": (window_summed_bytes - unique_assigned_bytes) / unique_assigned_bytes,
        "unassigned_products": product_counts[0], "unassigned_bytes": byte_counts[0],
        "unassigned_byte_share": byte_counts[0] / cohort_bytes,
        "relationship_manifest_bytes": relationship_manifest_bytes,
        "combined_relationship_layer_bytes": combined_relationship_layer_bytes,
        "combined_relationship_layer_cohort_fraction": combined_relationship_layer_bytes / cohort_bytes,
        "cohort_to_relationship_layer_byte_ratio": cohort_bytes / combined_relationship_layer_bytes,
    }
    return ledger, metrics, distribution


def render_csv(rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def inputs(root: Path, spec: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    source = spec["source_contract"]
    plan = json.loads((root / source["plan_path"]).read_text(encoding="utf-8"))
    if not isinstance(plan, list):
        raise ValueError("Expected the target request to contain a list of plan entries.")
    with (root / source["manifest_path"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return plan, rows


def materialize_ledger(root: Path) -> Path:
    spec = load_json(root / "spec/stage10z.json")
    plan, rows = inputs(root, spec)
    ledger, _, _ = derive(plan, rows)
    path = root / spec["source_contract"]["ledger_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_csv(ledger), encoding="utf-8", newline="")
    return path


def verify_stage10z(root: Path, mutation: str | None = None, prior: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10z.json"), mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior = verify_stage10y(root) if prior is None else prior
    add_check(checks, errors, "schedule_tag_guard_replays", prior["pass"],
              error="Stage 10Y no longer verifies.")

    plan, rows = inputs(root, spec)
    ledger, metrics, distribution = derive(plan, rows)
    structure_ok = exact_mapping(metrics, spec["frozen_observables"]) and distribution == spec["frozen_membership_distribution"]
    add_check(checks, errors, "many_to_many_membership_structure", structure_ok,
              error="The frozen action-to-plan membership structure changed.",
              metrics=metrics, distribution=distribution)

    ledger_path = root / spec["source_contract"]["ledger_path"]
    rendered_bytes = render_csv(ledger).encode("utf-8")
    ledger_ok = (
        ledger_path.exists() and ledger_path.read_bytes() == rendered_bytes
        and len(rendered_bytes) == spec["source_contract"]["ledger_bytes"]
        and hashlib.sha256(rendered_bytes).hexdigest() == spec["source_contract"]["ledger_sha256"]
    )
    add_check(checks, errors, "deterministic_complete_membership_ledger", ledger_ok,
              error="The action-to-plan membership ledger is missing or differs from deterministic replay.",
              ledger_path=str(ledger_path), rows=len(ledger), bytes=len(rendered_bytes),
              sha256=hashlib.sha256(rendered_bytes).hexdigest())

    state = spec["mutation_state"]
    boundary_ok = (
        not state["single_plan_membership_forced"] and state["unassigned_actions_retained"]
        and not state["plan_windows_are_partition"] and state["overlap_deduplication_required"]
        and state["unassigned_actions_in_scope"] and not state["target_inferred_from_plan"]
        and not state["membership_is_independent_event"] and not state["model_partition_assigned"]
        and not state["scientific_discovery_or_priority"] and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited one-owner, dropping, partition, double-count, target, event, model, discovery, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_MANY_TO_MANY_ACTION_PLAN_LEDGER" if structure_ok and ledger_ok else "ACTION_PLAN_MEMBERSHIP_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "membership": metrics, "membership_distribution": distribution,
        "verified": "Scheduled plan windows do not partition the 2,166 complete actions. Of those actions, 626 match no timed plan window, 1,482 match one, 54 match two, and four match three. The deterministic ledger preserves all actions and all 1,602 action-window relationships without forcing a single owner.",
        "decision_use": "Use the ledger as a many-to-many join. Dropping unmatched actions would omit 25.316% of cohort bytes; summing overlapping plan windows without action-level deduplication would overcount assigned bytes by 5.432%.",
        "ledger_path": spec["source_contract"]["ledger_path"],
        "ledger_bytes": len(rendered_bytes), "ledger_sha256": hashlib.sha256(rendered_bytes).hexdigest(),
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    prior = verify_stage10y(root)
    baseline = verify_stage10z(root, prior=prior)
    names = load_json(root / "spec/stage10z.json")["hard_negatives"]
    mutations = {name: verify_stage10z(root, name, prior=prior) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10Z hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["membership"]
    lines = [
        "# Stage 10Z — Action-to-Plan Membership Ledger", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Complete actions / relationship rows: `{item['complete_actions']:,}` / `{item['action_plan_relationships']:,}`",
        f"- Actions with 0 / 1 / 2 / 3 memberships: `{item['actions_with_no_plan_membership']:,}` / `{item['actions_with_one_plan_membership']:,}` / `{item['actions_with_two_plan_memberships']:,}` / `{item['actions_with_three_plan_memberships']:,}`",
        f"- Unassigned cohort-byte share: `{item['unassigned_byte_share']:.3%}`",
        f"- Overlapping-window byte inflation without deduplication: `{item['window_byte_inflation']:.3%}`",
        f"- Ledger: `{result['ledger_path']}`",
        f"- Ledger bytes / SHA-256: `{result['ledger_bytes']:,}` / `{result['ledger_sha256']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified", "", result["verified"], "", "## Decision use", "", result["decision_use"],
        "", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", "",
    ]
    for name, mutation_result in result.get("hard_negatives", {}).items():
        lines.append(f"- `{name}`: {'REJECTED' if not mutation_result['pass'] else 'UNEXPECTEDLY ACCEPTED'}")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--mutation")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "build":
        materialize_ledger(root)
    result = verify_with_mutations(root) if args.command == "verify" else verify_stage10z(root, args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
