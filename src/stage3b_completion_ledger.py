#!/usr/bin/env python3
"""Verify the Stage 3B completion ledger from pinned plan and transcript bytes."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from artemis_testbed import corpus_inventory, parse_utc
from stage3_attention_allocation import verify_stage3a
from stage4a_product_canary import verify_stage4a


UTC = timezone.utc
ADMITTED_TERMINAL_STATES = {
    "CONTENT_LED_ENTRY": {"DESCRIBED", "OBSERVED_AND_DESCRIBED"},
    "ENTRY_INTERVAL_CENSORED": {"OBSERVED_NEGATIVE"},
    "CONCURRENT_CONTENT_EVIDENCE": {
        "DESCRIBED_AND_CAPTURE_REPORTED",
        "OBSERVED_AND_CAPTURE_REPORTED",
    },
    "CONTINUED_CONTENT_EVIDENCE": {"DESCRIBED"},
    "UNRESOLVED_NO_DISTINCT_ENTRY": {"UNRESOLVED"},
}


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def iso_millis(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    """Parse either source-style UTC timestamps or frozen ISO-8601 receipts."""
    try:
        return parse_utc(value)
    except ValueError:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)


def load_targets(root: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    payload = load_json(root / spec["corpus"]["otr_path"])
    if not isinstance(payload, list):
        raise ValueError("OTR source is not a list")
    return [item["target_properties"] for item in payload]


def find_target(targets: list[dict[str, Any]], order: int, ltp_name: str) -> dict[str, Any]:
    matches = [
        target
        for target in targets
        if target.get("order") == order
        and str(target.get("ltp_name") or "").strip() == ltp_name
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Target order {order} / {ltp_name!r} resolved {len(matches)} times; expected one"
        )
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
    resolutions = {item["id"]: item for item in mutated["resolutions"]}
    if mutation == "missing_cue_means_missed":
        resolutions["discussion6_forward_look"]["terminal_state"] = "MISSED"
    elif mutation == "parallel_windows_are_merged":
        mutated["analysis_overrides"] = {"overlap_policy": "MERGED"}
    elif mutation == "background_only_is_entry":
        resolutions["deep_space_2"]["entry_cue"] = {
            "speaker": "Glover",
            "contains": "[[background voices",
            "expected_utc": "2026-04-07T01:10:49.090Z",
        }
    elif mutation == "content_cue_is_exact_title":
        resolutions["discussion2_near_farside"]["anchor_claim"] = "EXACT_TITLE_ENTRY"
    elif mutation == "reported_capture_is_product_validated":
        resolutions["eclipsed_moon_1"]["product_validated"] = True
    elif mutation == "metadata_label_proves_forward_look":
        item = resolutions["discussion6_forward_look"]
        item["evidence_class"] = "CONTENT_LED_ENTRY"
        item["terminal_state"] = "DESCRIBED"
        item["evidence_source"] = "STAGE4A_ACTIVITY_LABEL"
        item["entry_cue"] = item["context_cues"][0]
    elif mutation == "flash_candidate_is_validated":
        mutated["analysis_overrides"] = {"flash_state": "VALIDATED_LUNAR_IMPACT"}
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_cue(
    root: Path,
    transcript: str,
    cue: dict[str, str],
    role: str,
) -> dict[str, Any]:
    row_number, row = find_cue(root, transcript, cue)
    observed = parse_utc(row["utc"])
    expected = parse_timestamp(cue["expected_utc"])
    if observed != expected:
        raise ValueError(
            f"{role} cue timestamp {iso_millis(observed)} differs from frozen "
            f"{iso_millis(expected)}"
        )
    text = row["text"]
    if role == "entry" and text.lstrip().casefold().startswith("[[background"):
        raise ValueError("background-only dialogue cannot establish entry")
    return {
        "role": role,
        "utc": iso_millis(observed),
        "speaker": row["speaker"].strip(),
        "transcript_row": row_number,
        "cue_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def verify_stage3b(root: Path, mutation: str | None = None) -> dict[str, Any]:
    original_spec = load_json(root / "spec" / "stage3b.json")
    if not isinstance(original_spec, dict):
        raise ValueError("Stage 3B spec is not an object")
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
    try:
        targets = load_targets(root, spec)
        numbered_targets = [target for target in targets if isinstance(target.get("order"), int)]
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"OTR load failure: {exc}")
    plan_ok = (
        len(numbered_targets) == spec["corpus"]["expected_numbered_targets"]
        and len({int(item["order"]) for item in numbered_targets}) == len(numbered_targets)
    )
    checks.append({"id": "plan_inventory", "pass": plan_ok, "observed": len(numbered_targets)})
    if not plan_ok:
        errors.append("Plan inventory differs from the frozen 30-target contract")

    stage3a = verify_stage3a(root)
    stage3a_names = {item["ltp_name"] for item in stage3a.get("entry_anchors", [])}
    resolution_names = {item["ltp_name"] for item in original_spec["resolutions"]}
    target_names = {str(item.get("ltp_name") or "").strip() for item in numbered_targets}
    partition_ok = (
        stage3a["pass"]
        and len(stage3a_names) == spec["corpus"]["stage3a_exact_anchors"]
        and len(resolution_names) == spec["corpus"]["stage3a_unresolved_targets"]
        and stage3a_names.isdisjoint(resolution_names)
        and stage3a_names | resolution_names == target_names
    )
    checks.append(
        {
            "id": "stage3a_stage3b_partition",
            "pass": partition_ok,
            "observed": {
                "stage3a_exact_anchors": len(stage3a_names),
                "stage3b_resolution_names": len(resolution_names),
                "union": len(stage3a_names | resolution_names),
            },
        }
    )
    if not partition_ok:
        errors.append("Stage 3A anchors and Stage 3B resolutions do not partition all 30 targets")

    overlap_policy_ok = spec.get("analysis_overrides", {}).get("overlap_policy") != "MERGED"
    checks.append({"id": "parallel_targets_remain_distinct", "pass": overlap_policy_ok})
    if not overlap_policy_ok:
        errors.append("Simultaneous Eclipsed Moon and Deep Space targets cannot be merged")

    resolution_results: list[dict[str, Any]] = []
    for resolution in spec["resolutions"]:
        try:
            target = find_target(numbered_targets, resolution["order"], resolution["ltp_name"])
            evidence_class = resolution["evidence_class"]
            terminal_state = resolution["terminal_state"]
            admitted_states = ADMITTED_TERMINAL_STATES.get(evidence_class)
            if admitted_states is None or terminal_state not in admitted_states:
                raise ValueError(
                    f"{terminal_state} is not admitted for evidence class {evidence_class}"
                )
            if resolution.get("anchor_claim") == "EXACT_TITLE_ENTRY":
                raise ValueError("content-led evidence cannot be relabeled as an exact-title entry")
            if resolution.get("product_validated"):
                raise ValueError("crew-reported capture is not product validation")
            if resolution.get("evidence_source") == "STAGE4A_ACTIVITY_LABEL":
                raise ValueError("an activity metadata label cannot establish target execution")

            planned = parse_utc(target["request_date_time"])
            window_end = planned + timedelta(minutes=float(target["request_duration"]))
            cue_results: list[dict[str, Any]] = []
            entry_time: datetime | None = None
            if evidence_class == "UNRESOLVED_NO_DISTINCT_ENTRY":
                if "entry_cue" in resolution:
                    raise ValueError("an unresolved target cannot carry an admitted entry cue")
                for cue in resolution.get("context_cues", []):
                    result = verify_cue(root, resolution["transcript"], cue, "context")
                    cue_time = parse_timestamp(result["utc"])
                    if not planned <= cue_time <= window_end:
                        raise ValueError("Forward Look context cue falls outside its planned window")
                    cue_results.append(result)
            else:
                entry_result = verify_cue(
                    root, resolution["transcript"], resolution["entry_cue"], "entry"
                )
                cue_results.append(entry_result)
                entry_time = parse_timestamp(entry_result["utc"])
                for cue in resolution.get("corroborating_cues", []):
                    cue_results.append(
                        verify_cue(root, resolution["transcript"], cue, "corroborating")
                    )
            cue_times = [parse_timestamp(item["utc"]) for item in cue_results]
            if cue_times != sorted(cue_times):
                raise ValueError("resolution cues are not in chronological order")

            resolution_results.append(
                {
                    "id": resolution["id"],
                    "order": resolution["order"],
                    "ltp_name": resolution["ltp_name"],
                    "planned_request_utc": iso_millis(planned),
                    "request_duration_minutes": target["request_duration"],
                    "evidence_class": evidence_class,
                    "terminal_state": terminal_state,
                    "entry_cue_utc": iso_millis(entry_time) if entry_time else None,
                    "request_to_entry_cue_seconds": (
                        round((entry_time - planned).total_seconds(), 3) if entry_time else None
                    ),
                    "overlap_group": resolution.get("overlap_group"),
                    "transcript": resolution["transcript"],
                    "cues": cue_results,
                    "bounded_interpretation": resolution["bounded_interpretation"],
                    "pass": True,
                }
            )
        except (OSError, ValueError, KeyError, csv.Error) as exc:
            errors.append(f"Resolution {resolution['id']} failed: {exc}")

    resolutions_ok = len(resolution_results) == len(original_spec["resolutions"])
    checks.append(
        {"id": "nine_resolution_oracles", "pass": resolutions_ok, "observed": len(resolution_results)}
    )
    if not resolutions_ok:
        errors.append("One or more Stage 3B resolutions failed")

    overlap_results: list[dict[str, Any]] = []
    for contract in spec["overlap_contracts"]:
        members = [
            item for item in resolution_results if item.get("overlap_group") == contract["id"]
        ]
        hashes = {
            cue["cue_sha256"]
            for item in members
            for cue in item["cues"]
            if cue["role"] == "entry"
        }
        shared_request = {item["planned_request_utc"] for item in members}
        passed = (
            len(members) == 2
            and sorted(item["order"] for item in members) == contract["orders"]
            and shared_request == {contract["shared_request_utc"]}
            and len(hashes) == 2
        )
        overlap_results.append(
            {"id": contract["id"], "orders": contract["orders"], "distinct_entry_cues": len(hashes), "pass": passed}
        )
        if not passed:
            errors.append(f"Overlap contract {contract['id']} failed")
    overlaps_ok = len(overlap_results) == 2 and all(item["pass"] for item in overlap_results)
    checks.append({"id": "overlap_contracts", "pass": overlaps_ok, "observed": overlap_results})

    stage4a = verify_stage4a(root)
    flash_state = spec.get("analysis_overrides", {}).get(
        "flash_state", stage4a.get("flash_state", "UNESTABLISHED")
    )
    flash_ok = stage4a["pass"] and flash_state == "UNVALIDATED_CAPTURE_CANDIDATE"
    checks.append({"id": "flash_claim_ceiling", "pass": flash_ok, "observed": flash_state})
    if not flash_ok:
        errors.append("Transcript and product availability cannot validate a lunar impact")

    terminal_counts = dict(sorted(Counter(item["terminal_state"] for item in resolution_results).items()))
    evidence_counts = dict(sorted(Counter(item["evidence_class"] for item in resolution_results).items()))
    execution_supported = sum(item["terminal_state"] != "UNRESOLVED" for item in resolution_results)
    unresolved = sum(item["terminal_state"] == "UNRESOLVED" for item in resolution_results)
    observed_result = {
        "evidence_state": "VERIFIED_COMPLETE_CLASSIFICATION_LEDGER" if not errors else "REJECTED",
        "numbered_targets": len(numbered_targets),
        "stage3a_exact_anchors": len(stage3a_names),
        "stage3b_resolutions": len(resolution_results),
        "classified_targets": len(stage3a_names) + len(resolution_results),
        "execution_supported_resolutions": execution_supported,
        "unresolved_resolutions": unresolved,
        "proven_missed_targets": 0,
        "proven_diverted_targets": 0,
        "flash_candidate_state": flash_state,
        "disposition": "SYNTHESIZE_AND_HOLD" if not errors else None,
    }
    result_match = observed_result == spec["expected_result"]
    checks.append({"id": "frozen_result", "pass": result_match, "observed": observed_result})
    if not result_match:
        errors.append("Observed Stage 3B result differs from the frozen contract")

    passed = not errors and all(item["pass"] for item in checks)
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": spec["expected_result"]["evidence_state"] if passed else "REJECTED",
        "disposition": spec["expected_result"]["disposition"] if passed else None,
        "ledger_summary": {
            "numbered_targets": len(numbered_targets),
            "stage3a_exact_anchors": len(stage3a_names),
            "stage3b_resolutions": len(resolution_results),
            "classified_targets": len(stage3a_names) + len(resolution_results),
            "execution_supported_resolutions": execution_supported,
            "unresolved_resolutions": unresolved,
            "terminal_state_counts": terminal_counts,
            "evidence_class_counts": evidence_counts,
        },
        "resolutions": resolution_results,
        "overlap_contracts": overlap_results,
        "flash_candidate_state": flash_state,
        "checks": checks,
        "errors": errors,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"] if passed else None,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage3b(root)
    spec = load_json(root / "spec" / "stage3b.json")
    if not isinstance(spec, dict):
        raise ValueError("Stage 3B spec is not an object")
    mutations = {name: verify_stage3b(root, name) for name in spec["hard_negatives"]}
    hard_negatives_pass = all(not item["pass"] for item in mutations.values())
    passed = baseline["pass"] and hard_negatives_pass
    return {
        "baseline": baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": passed,
        "evidence_state": "VERIFIED_COMPLETE_CLASSIFICATION_LEDGER" if passed else "FAILED",
    }


def render_markdown(verification: dict[str, Any]) -> str:
    baseline = verification["baseline"]
    summary = baseline["ledger_summary"]
    lines = [
        "# Artemis II Observation-Execution Testbed — Stage 3B Result",
        "",
        f"- Verification: **{'PASS' if verification['pass'] else 'FAIL'}**",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Classified plan entries: **{summary['classified_targets']} of {summary['numbered_targets']}**",
        f"- Exact Stage 3A title/recorder anchors: **{summary['stage3a_exact_anchors']}**",
        f"- Additional execution-supported Stage 3B resolutions: **{summary['execution_supported_resolutions']}**",
        f"- Unresolved after source review: **{summary['unresolved_resolutions']}**",
        f"- Flash candidate: `{baseline['flash_candidate_state']}`",
        f"- Disposition: `{baseline.get('disposition') or 'UNSET'}`",
        "",
        "Stage 3B completes the classification ledger without pretending that every target has an exact spoken-title entry. Eight of the nine former gaps have direct execution evidence; Forward Look remains unresolved rather than missed.",
        "",
        "## Nine resolved classifications",
        "",
        "| Order | Plan entry | Evidence class | Terminal state | Entry/context cue |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for item in baseline["resolutions"]:
        cue = item["entry_cue_utc"] or item["cues"][0]["utc"]
        lines.append(
            f"| {item['order']} | {item['ltp_name']} | `{item['evidence_class']}` | "
            f"`{item['terminal_state']}` | {cue} |"
        )
    lines.extend(
        [
            "",
            "The two Eclipsed Moon/Deep Space pairs retain separate entry cues despite sharing request times. Reported camera use remains reported capture, not product-content validation. The Forward Look window contains source-evidenced competing activity and timeline re-synchronization, but no distinct forward-looking synthesis.",
            "",
            "## Next-step logic",
            "",
            f"**Recommended:** {baseline['next_step_logic']['recommended']}",
            "",
            f"Why: {baseline['next_step_logic']['why']}",
            "",
            f"Alternative: {baseline['next_step_logic']['alternative']}",
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
            "missing_cue_means_missed",
            "parallel_windows_are_merged",
            "background_only_is_entry",
            "content_cue_is_exact_title",
            "reported_capture_is_product_validated",
            "metadata_label_proves_forward_look",
            "flash_candidate_is_validated",
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        payload = verify_with_mutations(args.root)
    else:
        payload = verify_stage3b(args.root, args.mutation)
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
