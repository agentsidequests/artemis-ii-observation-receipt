#!/usr/bin/env python3
"""Verify Stage 10S's plan-bounded Sunset execution-window canary."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json, parse_utc
from stage10r_cross_camera_sunset_episode import verify_stage10r


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "archive_footprint_is_source_volume": False,
        "plan_windows_are_disjoint_samples": False,
        "target_label_is_pixel_truth": False,
        "products_are_independent_samples": False,
        "serial_to_named_operator_attributed": False,
        "result_kind": "hypothetical_group_crossing_hazard",
        "performance_effect_inferred": False,
        "cross_event_generalization_estimated": False,
        "scope": "one_plan_bounded_window_in_verified_cohort",
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_archive_footprint_source_volume": ("archive_footprint_is_source_volume", True),
        "call_plan_windows_disjoint_samples": ("plan_windows_are_disjoint_samples", True),
        "call_target_label_pixel_truth": ("target_label_is_pixel_truth", True),
        "call_products_independent_samples": ("products_are_independent_samples", True),
        "attribute_serial_to_named_operator": ("serial_to_named_operator_attributed", True),
        "call_hypothetical_crossing_observed_leakage": ("result_kind", "observed_leakage"),
        "infer_model_performance_effect": ("performance_effect_inferred", True),
        "claim_cross_event_generalization_estimated": ("cross_event_generalization_estimated", True),
        "generalize_sunset_concentration_to_archive": ("scope", "all_archive_products"),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_plan_window_canary": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def parse_plan_time(value: str) -> datetime:
    return datetime.strptime(value, "%d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace(".000000+00:00", "Z").replace("+00:00", "Z")


def summarize_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    actions = {row["action_id"] for row in rows}
    captures = {row["capture_identity"] for row in rows}
    collections = {
        name: [row for row in rows if row["collection_id"] == name]
        for name in ("data_source", "data_raw", "data_processed")
    }
    return {
        "products": len(rows),
        "capture_identities": len(captures),
        "complete_actions": len(actions),
        "archive_size_bytes": sum(int(row["archive_size_bytes"]) for row in rows),
        "source_products": len(collections["data_source"]),
        "source_bytes": sum(int(row["archive_size_bytes"]) for row in collections["data_source"]),
        "raw_products": len(collections["data_raw"]),
        "raw_bytes": sum(int(row["archive_size_bytes"]) for row in collections["data_raw"]),
        "processed_products": len(collections["data_processed"]),
        "processed_bytes": sum(int(row["archive_size_bytes"]) for row in collections["data_processed"]),
        "archive_to_source_byte_ratio": sum(int(row["archive_size_bytes"]) for row in rows) / sum(int(row["archive_size_bytes"]) for row in collections["data_source"]),
        "processed_byte_share": sum(int(row["archive_size_bytes"]) for row in collections["data_processed"]) / sum(int(row["archive_size_bytes"]) for row in rows),
        "products_per_action": len(rows) / len(actions),
        "captures_per_action": len(captures) / len(actions),
        "distinct_cameras": len({row["camera_serial"] for row in rows}),
        "distinct_activity_ids": len({row["activity_id"] for row in rows}),
        "five_second_clusters": len({row["temporal_cluster_5s"] for row in rows}),
    }


def target_window_rows(
    rows: list[dict[str, str]], target: str, start: datetime, end: datetime
) -> list[dict[str, str]]:
    return [
        row for row in rows
        if row["target_id"] == target
        and parse_utc(row["action_start_utc"]) >= start
        and parse_utc(row["action_end_utc"]) < end
    ]


def plan_window_rows(
    rows: list[dict[str, str]], start: datetime, end: datetime
) -> list[dict[str, str]]:
    return [
        row for row in rows
        if parse_utc(row["action_start_utc"]) >= start
        and parse_utc(row["action_end_utc"]) < end
    ]


def plan_window_census(
    plan: list[dict[str, Any]], rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    census: list[dict[str, Any]] = []
    for index, item in enumerate(plan):
        props = item["target_properties"]
        request_time = props.get("request_date_time")
        duration = props.get("request_duration")
        target = props.get("target_name")
        if not request_time or not duration or not target:
            continue
        start = parse_plan_time(request_time)
        end = start + timedelta(minutes=float(duration))
        selected = plan_window_rows(rows, start, end)
        if not selected:
            continue
        summary = summarize_rows(selected)
        census.append({
            "index": index,
            "order": props.get("order"),
            "target_name": target,
            "ltp_name": props.get("ltp_name"),
            "planned_start_utc": iso_utc(start),
            "planned_duration_minutes": duration,
            **summary,
        })
    return census


def target_matched_plan_window_census(
    plan: list[dict[str, Any]], rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    census: list[dict[str, Any]] = []
    for index, item in enumerate(plan):
        props = item["target_properties"]
        request_time = props.get("request_date_time")
        duration = props.get("request_duration")
        target = props.get("target_name")
        if not request_time or not duration or not target:
            continue
        start = parse_plan_time(request_time)
        end = start + timedelta(minutes=float(duration))
        selected = target_window_rows(rows, target, start, end)
        if not selected:
            continue
        census.append({"index": index, **summarize_rows(selected)})
    return census


def rank_of(census: list[dict[str, Any]], selected_index: int, field: str) -> int:
    ranked = sorted(census, key=lambda item: (-item[field], item["index"]))
    return next(index for index, item in enumerate(ranked, start=1) if item["index"] == selected_index)


def next_value(census: list[dict[str, Any]], selected_index: int, field: str) -> int:
    return max(item[field] for item in census if item["index"] != selected_index)


def verify_stage10s(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10s.json"), mutation)
    expected = spec["frozen_observables"]
    source = spec["source_contract"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    prior = verify_stage10r(root)
    add_check(checks, errors, "prior_episode_receipt", prior["pass"],
              error="Stage 10R no longer verifies.")

    plan = json.loads((root / source["plan_path"]).read_text(encoding="utf-8"))
    if not isinstance(plan, list):
        raise ValueError("Expected the target request to contain a list of plan entries.")
    sunset_matches = [
        (index, item["target_properties"])
        for index, item in enumerate(plan)
        if item["target_properties"].get("order") == source["sunset_order"]
        and item["target_properties"].get("target_name") == "Sunset"
    ]
    next_matches = [
        item["target_properties"] for item in plan
        if item["target_properties"].get("order") == source["next_order"]
    ]
    plan_ok = len(sunset_matches) == 1 and len(next_matches) == 1
    add_check(checks, errors, "unique_plan_entries", plan_ok,
              error="The Sunset or next plan entry is no longer unique.")
    selected_index, sunset = sunset_matches[0]
    next_entry = next_matches[0]
    planned_start = parse_plan_time(sunset["request_date_time"])
    planned_end = planned_start + timedelta(minutes=float(sunset["request_duration"]))
    next_start = parse_plan_time(next_entry["request_date_time"])

    with (root / source["manifest_path"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    selected = plan_window_rows(rows, planned_start, planned_end)
    summary = summarize_rows(selected)
    cohort = {
        "products": len(rows),
        "capture_identities": len({row["capture_identity"] for row in rows}),
        "complete_actions": len({row["action_id"] for row in rows}),
        "archive_size_bytes": sum(int(row["archive_size_bytes"]) for row in rows),
    }

    with (root / source["transcript_path"]).open(newline="", encoding="utf-8-sig") as handle:
        transcript = list(csv.DictReader(handle))
    inside_transcript = [
        row for row in transcript if planned_start <= parse_utc(row["utc"]) < planned_end
    ]
    anchors_ok = all(any(
        parse_utc(row["utc"]) == parse_utc(anchor["utc"])
        and row["speaker"] == anchor["speaker"]
        and anchor["contains"].lower() in row["text"].lower()
        for row in transcript
    ) for anchor in spec["transcript_anchors"])
    add_check(checks, errors, "transcript_window_anchors", anchors_ok,
              error="A Sunset schedule or camera-configuration transcript anchor changed.")

    census = plan_window_census(plan, rows)
    target_matched_census = target_matched_plan_window_census(plan, rows)
    product_next = next_value(census, selected_index, "products")
    action_next = next_value(census, selected_index, "complete_actions")
    byte_next = next_value(census, selected_index, "archive_size_bytes")
    derived = {
        "target_name": sunset["target_name"],
        "ltp_name": sunset["ltp_name"],
        "planned_start_utc": iso_utc(planned_start),
        "planned_end_utc": iso_utc(planned_end),
        "planned_duration_minutes": sunset["request_duration"],
        "geometric_start_utc": iso_utc(parse_plan_time(sunset["start_date_time"].split(".")[0]) + timedelta(microseconds=int(sunset["start_date_time"].split(".")[1]))),
        "geometric_end_utc": iso_utc(parse_plan_time(sunset["end_date_time"].split(".")[0]) + timedelta(microseconds=int(sunset["end_date_time"].split(".")[1]))),
        "next_request_start_utc": iso_utc(next_start),
        **summary,
        "target_ids": sorted({row["target_id"] for row in selected}),
        "target_label_concordance": sum(row["target_id"] == sunset["target_name"] for row in selected) / len(selected),
        "transcript_utterances": len(inside_transcript),
        "transcript_speakers": len({row["speaker"] for row in inside_transcript}),
        "cohort_product_share": summary["products"] / cohort["products"],
        "cohort_capture_share": summary["capture_identities"] / cohort["capture_identities"],
        "cohort_action_share": summary["complete_actions"] / cohort["complete_actions"],
        "cohort_byte_share": summary["archive_size_bytes"] / cohort["archive_size_bytes"],
        "plan_windows_with_actions": len(census),
        "product_rank": rank_of(census, selected_index, "products"),
        "action_rank": rank_of(census, selected_index, "complete_actions"),
        "byte_rank": rank_of(census, selected_index, "archive_size_bytes"),
        "next_product_count": product_next,
        "next_action_count": action_next,
        "next_byte_count": byte_next,
        "product_lead_ratio": summary["products"] / product_next,
        "action_lead_ratio": summary["complete_actions"] / action_next,
        "byte_lead_ratio": summary["archive_size_bytes"] / byte_next,
        "target_matched_plan_windows": len(target_matched_census),
        "target_matched_product_lead_ratio": summary["products"] / next_value(target_matched_census, selected_index, "products"),
        "target_matched_action_lead_ratio": summary["complete_actions"] / next_value(target_matched_census, selected_index, "complete_actions"),
        "target_matched_byte_lead_ratio": summary["archive_size_bytes"] / next_value(target_matched_census, selected_index, "archive_size_bytes"),
        "scheduled_sunset_entries": sum(
            item["target_properties"].get("target_name") == "Sunset" for item in plan
        ),
        "event_cross_probability_80_20": 1.0 - 0.8 ** summary["complete_actions"] - 0.2 ** summary["complete_actions"],
    }
    intent_ok = (
        "Use D5 with long lens" in sunset["camera_actions"]
        and "continuous image captures" in sunset["impact_statement"]
        and planned_end == next_start
    )
    add_check(checks, errors, "plan_bounded_intent", intent_ok,
              error="The plan no longer fixes an eight-minute continuous-capture Sunset block ending at the next request.")

    exact_keys = [key for key, value in expected.items() if not isinstance(value, float)]
    float_keys = [key for key, value in expected.items() if isinstance(value, float)]
    observables_ok = (
        all(derived[key] == expected[key] for key in exact_keys)
        and all(close(float(derived[key]), expected[key]) for key in float_keys)
    )
    add_check(checks, errors, "plan_window_observables", observables_ok,
              error="The plan-bounded Sunset window, representation ledger, or comparative rank changed.",
              derived=derived)

    state = spec["mutation_state"]
    boundary_ok = (
        not state["archive_footprint_is_source_volume"]
        and not state["plan_windows_are_disjoint_samples"]
        and not state["target_label_is_pixel_truth"]
        and not state["products_are_independent_samples"]
        and not state["serial_to_named_operator_attributed"]
        and state["result_kind"] == "hypothetical_group_crossing_hazard"
        and not state["performance_effect_inferred"]
        and not state["cross_event_generalization_estimated"]
        and state["scope"] == "one_plan_bounded_window_in_verified_cohort"
        and not state["scientific_discovery_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited volume, independence, visual, attribution, leakage, performance, scope, discovery, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_PLAN_BOUNDED_SUNSET_CONCENTRATION" if plan_ok and anchors_ok and intent_ok and observables_ok else "PLAN_BOUNDED_SUNSET_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "window": derived,
        "verified": "The independently scheduled eight-minute Sunset block contains 2,535 current Atlas products representing 845 exposures and 169 complete five-exposure actions across two cameras, two activity facets, and 24 conditional temporal clusters. Its 200.901668231-GB retrieval footprint decomposes into 17.257373901 GB of source NEFs, 46.133066720 GB of raw TIFFs, and 137.511227610 GB of processed TIFFs: an 11.641497-fold retrieval-footprint-to-source-byte ratio. It ranks first by products, actions, and bytes among all 36 plan windows containing admitted actions; every admitted row in the fixed block carries the Sunset target label.",
        "decision_use": "For a model meant to generalize to a new Sunset event, treat the effective event-level sample count here as one, not 2,535 products, 845 exposures, or 169 actions. An episode-safe Artemis-II-only split cannot put different Sunset events in train and test because the plan contains only one Sunset entry. A within-event task needs a narrower, explicitly named estimand.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10s(root)
    names = load_json(root / "spec/stage10s.json")["hard_negatives"]
    mutations = {name: verify_stage10s(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10S hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["window"]
    lines = [
        "# Stage 10S — Plan-Bounded Sunset Window", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Planned block: `{item['planned_start_utc']}` to `{item['planned_end_utc']}` (`{item['planned_duration_minutes']}` minutes)",
        f"- Products / exposures / actions: `{item['products']:,}` / `{item['capture_identities']:,}` / `{item['complete_actions']:,}`",
        f"- Retrieval footprint: `{item['archive_size_bytes'] / 1_000_000_000:.9f} GB`",
        f"- Source / raw / processed: `{item['source_bytes'] / 1_000_000_000:.9f}` / `{item['raw_bytes'] / 1_000_000_000:.9f}` / `{item['processed_bytes'] / 1_000_000_000:.9f} GB`",
        f"- Retrieval footprint / source-byte ratio: `{item['archive_to_source_byte_ratio']:.6f}x`",
        f"- Cohort product / action / byte share: `{item['cohort_product_share']:.3%}` / `{item['cohort_action_share']:.3%}` / `{item['cohort_byte_share']:.3%}`",
        f"- Plan-window rank (products / actions / bytes): `{item['product_rank']}` / `{item['action_rank']}` / `{item['byte_rank']}` of `{item['plan_windows_with_actions']}`",
        f"- Scheduled Sunset entries in plan: `{item['scheduled_sunset_entries']}`",
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
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--mutation")
    args = parser.parse_args(argv)
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10s(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
