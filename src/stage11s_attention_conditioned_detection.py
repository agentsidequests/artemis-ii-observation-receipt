#!/usr/bin/env python3
"""Verify the Stage 11S attention-conditioned flash observation audit."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_utc(value: str) -> datetime:
    normalized = value.replace(" ", "T")
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def find_anchor(rows: list[dict[str, str]], anchor: dict[str, str]) -> dict[str, str] | None:
    expected_time = parse_utc(anchor["utc"])
    expected_speaker = anchor["speaker"].casefold()
    expected_phrase = anchor["phrase"].casefold()
    for row in rows:
        if not row.get("utc"):
            continue
        if (
            parse_utc(row["utc"]) == expected_time
            and expected_speaker in row.get("speaker", "").casefold()
            and expected_phrase in row.get("text", "").casefold()
        ):
            return row
    return None


def contains_context(rows: list[dict[str, str]], context: dict[str, Any]) -> bool:
    speaker = context["speaker"].casefold()
    phrases = [phrase.casefold() for phrase in context["phrases"]]
    for row in rows:
        text = " ".join(row.get("text", "").split()).casefold()
        if speaker in row.get("speaker", "").casefold() and all(phrase in text for phrase in phrases):
            return True
    return False


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


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "drop_anchor": None,
        "search_intent_override_utc": None,
        "drop_crew_context": None,
        "raw_clock_time_is_homogeneous_exposure": False,
        "reports_are_independent_physical_events": False,
        "ground_prompt_caused_candidate": False,
        "count_divided_by_clock_time_is_calibrated_rate": False,
        "physical_clustering_inferred": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "drop_display_dimming_anchor": ("drop_anchor", "display_dimming"),
        "move_search_intent_after_shared_report": (
            "search_intent_override_utc",
            "2026-04-07T00:51:16.947Z",
        ),
        "drop_priming_context": ("drop_crew_context", "priming_and_correlation"),
        "call_clock_time_homogeneous_exposure": ("raw_clock_time_is_homogeneous_exposure", True),
        "call_reports_independent_physical_events": ("reports_are_independent_physical_events", True),
        "call_ground_prompt_causal": ("ground_prompt_caused_candidate", True),
        "call_count_over_time_calibrated_rate": ("count_divided_by_clock_time_is_calibrated_rate", True),
        "infer_physical_clustering": ("physical_clustering_inferred", True),
        "open_pixels": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def verify_stage11s(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11s.json"), mutation)
    state = spec["mutation_state"]
    identities = source_identities(root, spec)
    pcd_rows = read_csv(root / spec["sources"][0]["path"])
    crew_rows = read_csv(root / spec["sources"][1]["path"])

    ledger = []
    anchor_checks = []
    for anchor in spec["timeline_anchors"]:
        found = find_anchor(pcd_rows, anchor)
        if state["drop_anchor"] == anchor["id"]:
            found = None
        observed_utc = anchor["utc"]
        if anchor["id"] == "explicit_search_intent" and state["search_intent_override_utc"]:
            observed_utc = state["search_intent_override_utc"]
        anchor_checks.append(found is not None)
        ledger.append({
            "id": anchor["id"],
            "utc": observed_utc,
            "phase": anchor["phase"],
            "speaker": anchor["speaker"],
            "anchor_found": found is not None,
            "source_text": found["text"] if found else None,
        })

    times = {item["id"]: parse_utc(item["utc"]) for item in ledger}
    ordering_ids = spec["required_order"]
    ordering_ok = all(times[left] < times[right] for left, right in zip(ordering_ids, ordering_ids[1:]))

    deltas = {
        "first_report_to_search_intent_seconds": (
            times["explicit_search_intent"] - times["first_pre_explicit_search_report"]
        ).total_seconds(),
        "first_report_to_display_dimming_seconds": (
            times["display_dimming"] - times["first_pre_explicit_search_report"]
        ).total_seconds(),
        "dedicated_watch_to_shared_report_seconds": (
            times["shared_report"] - times["dedicated_watch_start"]
        ).total_seconds(),
        "dedicated_watch_to_timeline_return_seconds": (
            times["timeline_return"] - times["dedicated_watch_start"]
        ).total_seconds(),
        "shared_report_to_ambiguous_candidate_seconds": (
            times["ambiguous_candidate"] - times["shared_report"]
        ).total_seconds(),
        "ground_prompt_end_to_candidate_seconds": (
            times["prompt_proximate_candidate"] - times["ground_prompt_end"]
        ).total_seconds(),
        "first_to_last_clear_report_seconds": (
            times["last_clear_report"] - times["first_pre_explicit_search_report"]
        ).total_seconds(),
    }
    deltas_ok = all(
        math.isclose(deltas[key], expected, rel_tol=0.0, abs_tol=1e-6)
        for key, expected in spec["frozen_deltas_seconds"].items()
    )

    context_checks = {}
    for context in spec["crew_context"]:
        present = contains_context(crew_rows, context)
        if state["drop_crew_context"] == context["id"]:
            present = False
        context_checks[context["id"]] = present

    prohibited_claims = {
        key: state[key]
        for key in (
            "raw_clock_time_is_homogeneous_exposure",
            "reports_are_independent_physical_events",
            "ground_prompt_caused_candidate",
            "count_divided_by_clock_time_is_calibrated_rate",
            "physical_clustering_inferred",
        )
    }
    checks = {
        "source_identities": all(item["match"] for item in identities),
        "all_timeline_anchors": all(anchor_checks),
        "required_temporal_order": ordering_ok,
        "frozen_deltas": deltas_ok,
        "crew_detection_context": all(context_checks.values()),
        "claim_boundaries": not any(prohibited_claims.values()),
        "zero_pixel_access": state["pixel_payload_bytes"] == 0,
    }
    passed = all(checks.values())
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": (
            "VERIFIED_ATTENTION_CONDITIONED_OBSERVATION_PROCESS"
            if passed
            else "REJECTED_ATTENTION_CONDITIONED_OBSERVATION_PROCESS"
        ),
        "checks": checks,
        "source_identities": identities,
        "timeline": ledger,
        "deltas_seconds": deltas,
        "crew_context_checks": context_checks,
        "detection_regime_finding": (
            "The first retained report preceded explicit search intent. Attention, display luminance, "
            "glare management, dark adaptation, workflow state, and ground prompting then changed "
            "during the retained report sequence. Raw eclipse clock time is therefore a composite, "
            "unsegmented human observation opportunity rather than a calibrated exposure denominator."
        ),
        "prohibited_claims": prohibited_claims,
        "pixel_payload_bytes_opened": state["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec/stage11s.json")
    baseline = verify_stage11s(root)
    hard_negatives = {
        name: verify_stage11s(root, name) for name in spec["hard_negatives"]
    }
    hard_negatives_pass = all(not result["pass"] for result in hard_negatives.values())
    return {
        **baseline,
        "hard_negatives": hard_negatives,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
    }


def render_markdown(result: dict[str, Any]) -> str:
    d = result["deltas_seconds"]
    rows = "\n".join(
        f"| {item['utc']} | {item['phase']} | {item['source_text']} |"
        for item in result["timeline"]
    )
    return f"""# Stage 11S: Attention-Conditioned Flash Observation Process

- Verification: `{'PASS' if result['pass'] else 'FAIL'}`
- Evidence state: `{result['evidence_state']}`
- Pixel payload bytes opened: `{result['pixel_payload_bytes_opened']}`

## Verified timeline

| UTC | Observation state | Transcript anchor |
| --- | --- | --- |
{rows}

## Exact intervals

- First report to explicit search intent: `{d['first_report_to_search_intent_seconds']:.3f} s`
- First report to display dimming: `{d['first_report_to_display_dimming_seconds']:.3f} s`
- Dedicated watching to the shared report: `{d['dedicated_watch_to_shared_report_seconds']:.3f} s`
- Dedicated watching to timeline return: `{d['dedicated_watch_to_timeline_return_seconds']:.3f} s`
- Shared report to explicitly ambiguous candidate: `{d['shared_report_to_ambiguous_candidate_seconds']:.3f} s`
- Ground prompt end to prompt-proximate candidate: `{d['ground_prompt_end_to_candidate_seconds']:.3f} s`
- First to last clear report: `{d['first_to_last_clear_report_seconds']:.3f} s`

## Result

{result['detection_regime_finding']}

This verifies nonstationary observation conditions. It does not establish how detection probability changed, whether any report was caused by prompting, or whether the physical events were clustered.

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
    result = verify_with_mutations(root) if args.command == "verify" else verify_stage11s(root, args.mutation)
    if args.json_output:
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
