#!/usr/bin/env python3
"""Verify Stage 3A target-entry and attention-allocation evidence offline."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from artemis_testbed import corpus_inventory, parse_utc


UTC = timezone.utc
ADMITTED_EPISODE_CLASSES = {
    "aristarchus_reiner_recovery": "DOCUMENTATION_RECOVERY",
    "vavilov_refocus": "RESISTED_DIVERSION",
    "crew_choice_terminator": "EXPECTED_CREW_CHOICE",
    "impact_flash_recording_gap": "ENTRY_INTERVAL_CENSORED",
    "forward_look_flash_candidate": "ATTENTION_SHIFT_CANDIDATE",
}


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def iso_millis(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def load_targets(root: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    payload = load_json(root / spec["corpus"]["otr_path"])
    if not isinstance(payload, list):
        raise ValueError("OTR source is not a list")
    return [item["target_properties"] for item in payload]


def find_target(targets: list[dict[str, Any]], ltp_name: str) -> dict[str, Any]:
    matches = [
        target
        for target in targets
        if str(target.get("ltp_name") or "").strip() == ltp_name
    ]
    if len(matches) != 1:
        raise ValueError(f"Target {ltp_name!r} resolved {len(matches)} times; expected one")
    return matches[0]


def find_cue(root: Path, transcript: str, cue: dict[str, str]) -> tuple[int, dict[str, str]]:
    path = root / transcript
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    speaker = cue["speaker"].strip().casefold()
    needle = cue["contains"].casefold()
    matches = [
        (index, row)
        for index, row in enumerate(rows, start=2)
        if row.get("speaker", "").strip().casefold() == speaker
        and needle in row.get("text", "").casefold()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Cue {cue['contains']!r} in {transcript} resolved {len(matches)} times; expected one"
        )
    return matches[0]


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    if mutation is None:
        return mutated
    if mutation == "silence_means_missed":
        mutated["analysis_overrides"] = {"unresolved_target_state": "MISSED"}
    elif mutation == "crew_choice_means_diverted":
        episode = next(
            item for item in mutated["attention_episodes"] if item["id"] == "crew_choice_terminator"
        )
        episode["classification"] = "DIVERTED"
    elif mutation == "background_mention_is_entry":
        mutated["entry_anchors"].append(
            {
                "id": "background_hertzsprung",
                "ltp_name": "Hertzsprung Basin",
                "transcript": "corpus/transcripts/art002a000028_pcd2_trn-csv_v01.csv",
                "speaker": "Wiseman",
                "cue_contains": "I see Hertzsprung",
                "expected_delta_seconds": 0.0,
            }
        )
    elif mutation == "overrun_proves_cause":
        anchor = next(item for item in mutated["entry_anchors"] if item["id"] == "ohm1")
        anchor["causal_claim"] = "Glushko displaced Ohm"
    elif mutation == "flash_is_validated":
        episode = next(
            item
            for item in mutated["attention_episodes"]
            if item["id"] == "forward_look_flash_candidate"
        )
        episode["classification"] = "VALIDATED_PHENOMENON"
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_stage3a(root: Path, mutation: str | None = None) -> dict[str, Any]:
    original_spec = load_json(root / "spec" / "stage3a.json")
    if not isinstance(original_spec, dict):
        raise ValueError("Stage 3A spec is not an object")
    spec = apply_mutation(original_spec, mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    inventory, aggregate, byte_count = corpus_inventory(root)
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

    targets: list[dict[str, Any]] = []
    numbered_targets: list[dict[str, Any]] = []
    schedule_controls: list[dict[str, Any]] = []
    try:
        targets = load_targets(root, spec)
        numbered_targets = [target for target in targets if isinstance(target.get("order"), int)]
        schedule_controls = [target for target in targets if not isinstance(target.get("order"), int)]
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"OTR load failure: {exc}")

    inventory_ok = (
        len(numbered_targets) == spec["corpus"]["expected_numbered_targets"]
        and len(schedule_controls) == spec["corpus"]["expected_schedule_controls"]
        and len({str(item.get("ltp_name") or "").strip() for item in numbered_targets})
        == len(numbered_targets)
    )
    checks.append(
        {
            "id": "plan_inventory",
            "pass": inventory_ok,
            "numbered_targets": len(numbered_targets),
            "schedule_controls": len(schedule_controls),
        }
    )
    if not inventory_ok:
        errors.append("Plan inventory differs from the frozen 30-target/9-control contract")

    anchor_results: list[dict[str, Any]] = []
    anchored_names: set[str] = set()
    for anchor in spec["entry_anchors"]:
        try:
            target = find_target(numbered_targets, anchor["ltp_name"])
            row_number, row = find_cue(
                root,
                anchor["transcript"],
                {"speaker": anchor["speaker"], "contains": anchor["cue_contains"]},
            )
            if "[[background voice" in row["text"].casefold():
                raise ValueError("background dialogue cannot establish target entry")
            if anchor.get("causal_claim"):
                raise ValueError("an entry delta cannot establish a causal displacement")
            planned = parse_utc(target["request_date_time"])
            observed = parse_utc(row["utc"])
            delta = round((observed - planned).total_seconds(), 3)
            passed = abs(delta - anchor["expected_delta_seconds"]) <= 0.001
            anchor_results.append(
                {
                    "id": anchor["id"],
                    "ltp_name": anchor["ltp_name"],
                    "planned_request_utc": iso_millis(planned),
                    "entry_cue_utc": iso_millis(observed),
                    "request_to_cue_delta_seconds": delta,
                    "direction": "early" if delta < 0 else "late" if delta > 0 else "on_time",
                    "transcript": anchor["transcript"],
                    "transcript_row": row_number,
                    "speaker": row["speaker"].strip(),
                    "cue_sha256": hashlib.sha256(row["text"].encode("utf-8")).hexdigest(),
                    "pass": passed,
                }
            )
            anchored_names.add(anchor["ltp_name"])
            if not passed:
                errors.append(
                    f"{anchor['id']} delta {delta:.3f}s differs from frozen expectation"
                )
        except (OSError, ValueError, KeyError, csv.Error) as exc:
            errors.append(f"Entry anchor {anchor['id']} failed: {exc}")

    unique_anchor_names = len(anchored_names) == len(anchor_results)
    anchors_ok = (
        len(anchor_results) == len(original_spec["entry_anchors"])
        and all(item["pass"] for item in anchor_results)
        and unique_anchor_names
    )
    checks.append(
        {
            "id": "exact_entry_anchors",
            "pass": anchors_ok,
            "observed": len(anchor_results),
        }
    )
    if not anchors_ok:
        errors.append("One or more exact entry anchors failed")

    unresolved_names = [
        str(target["ltp_name"]).strip()
        for target in sorted(numbered_targets, key=lambda item: int(item["order"]))
        if str(target["ltp_name"]).strip() not in anchored_names
    ]
    silence_override = spec.get("analysis_overrides", {}).get("unresolved_target_state")
    silence_ok = silence_override != "MISSED"
    checks.append(
        {
            "id": "silence_is_not_missed",
            "pass": silence_ok,
            "unresolved_entry_anchors": len(unresolved_names),
        }
    )
    if not silence_ok:
        errors.append("Silence or a missing exact entry cue cannot establish MISSED")

    episode_results: list[dict[str, Any]] = []
    for episode in spec["attention_episodes"]:
        try:
            target = find_target(numbered_targets, episode["ltp_name"])
            admitted = ADMITTED_EPISODE_CLASSES.get(episode["id"])
            if episode["classification"] != admitted:
                raise ValueError(
                    f"classification {episode['classification']} is not admitted; expected {admitted}"
                )
            if (
                episode["classification"] == "VALIDATED_PHENOMENON"
                and not episode.get("independent_oracle", False)
            ):
                raise ValueError("a transcript-only episode cannot validate a physical phenomenon")

            cue_results: list[dict[str, Any]] = []
            cue_times: list[datetime] = []
            for cue in episode["cues"]:
                row_number, row = find_cue(root, episode["transcript"], cue)
                observed = parse_utc(row["utc"])
                cue_times.append(observed)
                cue_results.append(
                    {
                        "utc": iso_millis(observed),
                        "speaker": row["speaker"].strip(),
                        "transcript_row": row_number,
                        "cue_sha256": hashlib.sha256(row["text"].encode("utf-8")).hexdigest(),
                    }
                )
            if cue_times != sorted(cue_times):
                raise ValueError("episode cues are not in chronological order")
            if episode.get("must_be_inside_request_window"):
                window_start = parse_utc(target["request_date_time"])
                window_end = window_start + timedelta(minutes=float(target["request_duration"]))
                if not all(window_start <= value <= window_end for value in cue_times):
                    raise ValueError("one or more cues fall outside the planned request window")

            episode_results.append(
                {
                    "id": episode["id"],
                    "ltp_name": episode["ltp_name"],
                    "classification": episode["classification"],
                    "first_cue_utc": iso_millis(cue_times[0]),
                    "last_cue_utc": iso_millis(cue_times[-1]),
                    "transcript": episode["transcript"],
                    "cues": cue_results,
                    "bounded_interpretation": episode["bounded_interpretation"],
                    "counterevidence": episode.get("counterevidence"),
                    "independent_oracle": episode.get("independent_oracle"),
                    "pass": True,
                }
            )
        except (OSError, ValueError, KeyError, csv.Error) as exc:
            errors.append(f"Attention episode {episode['id']} failed: {exc}")

    episodes_ok = len(episode_results) == len(original_spec["attention_episodes"])
    checks.append(
        {"id": "attention_episode_oracles", "pass": episodes_ok, "observed": len(episode_results)}
    )
    if not episodes_ok:
        errors.append("One or more attention episodes failed")

    deltas = [item["request_to_cue_delta_seconds"] for item in anchor_results]
    schedule_summary = {
        "early_anchor_count": sum(delta < 0 for delta in deltas),
        "late_anchor_count": sum(delta > 0 for delta in deltas),
        "on_time_anchor_count": sum(delta == 0 for delta in deltas),
        "minimum_delta_seconds": min(deltas) if deltas else None,
        "maximum_delta_seconds": max(deltas) if deltas else None,
        "median_delta_seconds": round(statistics.median(deltas), 3) if deltas else None,
        "interpretation_limit": spec["entry_anchor_semantics"],
    }

    flash_episode = next(
        (item for item in episode_results if item["id"] == "forward_look_flash_candidate"),
        None,
    )
    flash_state = (
        "UNVALIDATED_TWO_OBSERVER_CANDIDATE"
        if flash_episode
        and flash_episode["classification"] == "ATTENTION_SHIFT_CANDIDATE"
        and flash_episode.get("independent_oracle") is False
        else "UNESTABLISHED"
    )
    observed_result = {
        "evidence_state": "VERIFIED_PARTIAL_LEDGER" if not errors else "REJECTED",
        "numbered_targets": len(numbered_targets),
        "schedule_controls": len(schedule_controls),
        "exact_entry_anchors": len(anchor_results),
        "unresolved_entry_anchors": len(unresolved_names),
        "proven_missed_targets": 0,
        "proven_diverted_targets": 0,
        "flash_candidate_state": flash_state,
        "disposition": "CONTINUE_BOUNDED" if not errors else None,
    }
    result_match = observed_result == spec["expected_result"]
    checks.append({"id": "frozen_result", "pass": result_match, "observed": observed_result})
    if not result_match:
        errors.append("Observed Stage 3A result differs from the frozen contract")

    passed = not errors and all(item["pass"] for item in checks)
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": spec["expected_result"]["evidence_state"] if passed else "REJECTED",
        "disposition": spec["expected_result"]["disposition"] if passed else None,
        "plan_inventory": {
            "numbered_targets": len(numbered_targets),
            "schedule_controls": len(schedule_controls),
            "exact_entry_anchors": len(anchor_results),
            "unresolved_entry_anchors": unresolved_names,
        },
        "schedule_summary": schedule_summary,
        "entry_anchors": anchor_results,
        "attention_episodes": episode_results,
        "flash_candidate_state": flash_state,
        "checks": checks,
        "errors": errors,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"] if passed else None,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage3a(root)
    spec = load_json(root / "spec" / "stage3a.json")
    if not isinstance(spec, dict):
        raise ValueError("Stage 3A spec is not an object")
    mutations = {name: verify_stage3a(root, name) for name in spec["hard_negatives"]}
    hard_negatives_pass = all(not item["pass"] for item in mutations.values())
    passed = baseline["pass"] and hard_negatives_pass
    return {
        "baseline": baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": passed,
        "evidence_state": "VERIFIED_PARTIAL_LEDGER" if passed else "FAILED",
    }


def render_markdown(verification: dict[str, Any]) -> str:
    baseline = verification["baseline"]
    inventory = baseline["plan_inventory"]
    schedule = baseline["schedule_summary"]
    lines = [
        "# Artemis II Observation-Execution Testbed — Stage 3A Result",
        "",
        f"- Verification: **{'PASS' if verification['pass'] else 'FAIL'}**",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Planned science entries: **{inventory['numbered_targets']}**",
        f"- Exact entry anchors: **{inventory['exact_entry_anchors']}**",
        f"- Unresolved entry anchors: **{len(inventory['unresolved_entry_anchors'])}**",
        f"- Flash candidate: `{baseline['flash_candidate_state']}`",
        f"- Disposition: `{baseline.get('disposition') or 'UNSET'}`",
        "",
        "Stage 3A verifies a partial execution ledger, not a schedule-compliance score. Exact entry cues exist for 21 of 30 numbered targets, while nine remain unresolved rather than missed.",
        "",
        "## Entry-anchor distribution",
        "",
        f"- Early relative to request cue: {schedule['early_anchor_count']}",
        f"- Late relative to request cue: {schedule['late_anchor_count']}",
        f"- Range: {schedule['minimum_delta_seconds']:.3f} to {schedule['maximum_delta_seconds']:.3f} seconds",
        f"- Median: {schedule['median_delta_seconds']:.3f} seconds",
        "",
        schedule["interpretation_limit"],
        "",
        "## Attention-allocation findings",
        "",
        "| Episode | Classification | Evidence interval |",
        "| --- | --- | --- |",
    ]
    for episode in baseline["attention_episodes"]:
        lines.append(
            f"| {episode['id']} | `{episode['classification']}` | "
            f"{episode['first_cue_utc']} to {episode['last_cue_utc']} |"
        )
    lines.extend(
        [
            "",
            "The strongest new candidate is not a schedule delta. During the planned Forward Look window, the crew explicitly allocated attention to flash-watching, two crew reported the same pinpoint event, and the transcript then records a return to timeline coordination. That sequence is source-evidenced; the physical interpretation is not.",
            "",
            "Counterevidence matters: an earlier flash report was followed by uncertainty about eclipse-glasses timing, and Stage 3A admits no independently timed image or instrument product. No target is therefore classified as missed or diverted, and the flash remains unvalidated.",
            "",
            "## Unresolved entry anchors",
            "",
        ]
    )
    for name in inventory["unresolved_entry_anchors"]:
        lines.append(f"- {name}")
    lines.extend(
        [
            "",
            "## Next-step logic",
            "",
            f"**Recommended:** {baseline['next_step_logic']['recommended']}",
            "",
            f"Why: {baseline['next_step_logic']['why']}",
            "",
            f"Fallback: {baseline['next_step_logic']['fallback']}",
            "",
            f"Stop: {baseline['next_step_logic']['stop']}",
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
            "silence_means_missed",
            "crew_choice_means_diverted",
            "background_mention_is_entry",
            "overrun_proves_cause",
            "flash_is_validated",
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        payload = verify_with_mutations(args.root)
    else:
        payload = verify_stage3a(args.root, args.mutation)
    if args.json_output:
        write_json(args.json_output, payload)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_markdown(payload) if args.command == "verify" else json.dumps(payload, indent=2) + "\n"
        args.markdown_output.write_text(rendered, encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
