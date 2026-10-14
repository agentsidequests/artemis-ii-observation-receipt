#!/usr/bin/env python3
"""Verify Stage 10Q's independent Sunset transcript-alignment canary."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_json, parse_utc
from stage10p_capture_run_concentration import verify_stage10p


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "episode_kind": "time_bounded_observation_episode",
        "visual_redundancy_established": False,
        "transcript_kind": "independent_execution_record",
        "speaker_camera_attribution": False,
        "result_kind": "expected_crossing_hazard",
        "scope": "one_verified_cohort_episode",
        "performance_effect_inferred": False,
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    mapping = {
        "call_episode_a_semantic_scene": ("episode_kind", "semantic_scene"),
        "call_every_image_visually_redundant": ("visual_redundancy_established", True),
        "call_transcript_pixel_ground_truth": ("transcript_kind", "pixel_ground_truth"),
        "attribute_camera_to_named_speaker": ("speaker_camera_attribution", True),
        "call_expected_crossing_observed_leakage": ("result_kind", "observed_leakage"),
        "generalize_episode_to_archive": ("scope", "all_archive_products"),
        "infer_model_performance_effect": ("performance_effect_inferred", True),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_alignment_canary": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    state[key] = value
    return mutated


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-9)


def iso_utc(value: str) -> str:
    return parse_utc(value).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def verify_stage10q(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10q.json"), mutation)
    expected = spec["frozen_observables"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    stage10p = verify_stage10p(root)
    stage10p_ok = (
        stage10p["pass"]
        and stage10p["largest_cluster"]["largest_cluster_id"] == expected["cluster_id"]
        and stage10p["largest_cluster"]["start_utc"] == expected["cluster_start_utc"]
        and stage10p["largest_cluster"]["end_utc"] == expected["cluster_end_utc"]
    )
    add_check(checks, errors, "stage10p_cluster_identity", stage10p_ok,
              error="The Stage 10P cluster identity or interval changed.")

    source = spec["source_contract"]
    transcript_path = root / source["transcript_path"]
    transcript_ok = (
        transcript_path.is_file()
        and transcript_path.stat().st_size == source["transcript_bytes"]
        and sha256_file(transcript_path) == source["transcript_sha256"]
    )
    add_check(checks, errors, "transcript_identity", transcript_ok,
              error="The pinned PCD3 transcript bytes changed.")

    rows: list[dict[str, str]] = []
    if transcript_ok:
        with transcript_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    start = parse_utc(expected["cluster_start_utc"])
    end = parse_utc(expected["cluster_end_utc"])
    ordered = sorted(rows, key=lambda row: parse_utc(row["utc"]))
    inside = [row for row in ordered if start <= parse_utc(row["utc"]) <= end]
    prior = [row for row in ordered if parse_utc(row["utc"]) < start]
    after = [row for row in ordered if parse_utc(row["utc"]) > end]
    joined = " ".join(row["text"] for row in inside).casefold()
    derived = {
        "inside_utterances": len(inside),
        "inside_speaker_counts": dict(sorted(Counter(row["speaker"] for row in inside).items())),
        "first_inside_utc": iso_utc(inside[0]["utc"]) if inside else None,
        "first_inside_offset_seconds": (parse_utc(inside[0]["utc"]) - start).total_seconds() if inside else None,
        "last_inside_utc": iso_utc(inside[-1]["utc"]) if inside else None,
        "last_inside_lead_seconds": (end - parse_utc(inside[-1]["utc"])).total_seconds() if inside else None,
        "nearest_prior_utc": iso_utc(prior[-1]["utc"]) if prior else None,
        "nearest_prior_lead_seconds": (start - parse_utc(prior[-1]["utc"])).total_seconds() if prior else None,
        "nearest_after_utc": iso_utc(after[0]["utc"]) if after else None,
        "nearest_after_offset_seconds": (parse_utc(after[0]["utc"]) - end).total_seconds() if after else None,
        "required_inside_terms": [term for term in expected["required_inside_terms"] if term.casefold() in joined],
    }
    exact_keys = ("inside_utterances", "inside_speaker_counts", "first_inside_utc", "last_inside_utc",
                  "nearest_prior_utc", "nearest_after_utc", "required_inside_terms")
    float_keys = ("first_inside_offset_seconds", "last_inside_lead_seconds",
                  "nearest_prior_lead_seconds", "nearest_after_offset_seconds")
    alignment_ok = (
        all(derived[key] == expected[key] for key in exact_keys)
        and all(close(float(derived[key]), float(expected[key])) for key in float_keys)
    )
    add_check(checks, errors, "transcript_interval_alignment", alignment_ok,
              error="The transcript interval alignment or content anchors changed.", derived=derived)

    state = spec["mutation_state"]
    boundary_ok = (
        state["episode_kind"] == "time_bounded_observation_episode"
        and not state["visual_redundancy_established"]
        and state["transcript_kind"] == "independent_execution_record"
        and not state["speaker_camera_attribution"]
        and state["result_kind"] == "expected_crossing_hazard"
        and state["scope"] == "one_verified_cohort_episode"
        and not state["performance_effect_inferred"]
        and not state["scientific_discovery_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited scene, visual, attribution, leakage, scope, performance, discovery, priority, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_TRANSCRIPT_ALIGNED_OBSERVATION_EPISODE" if stage10p_ok and transcript_ok and alignment_ok else "TRANSCRIPT_ALIGNMENT_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED", "alignment": derived,
        "verified": "The exact 143.61-second Stage 10P Sunset interval contains 35 timestamped transcript utterances (34 Hansen, one Wiseman) about the Sun, Moon, glow, plume, and streamer. Related utterances bracket the interval by 2.084 seconds before and 0.013 seconds after.",
        "decision_use": "This independent execution record supports calling the concentration microcase one time-bounded observation episode. It makes the grouping hazard concrete without establishing semantic scene identity or visual redundancy.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10q(root)
    names = load_json(root / "spec/stage10q.json")["hard_negatives"]
    mutations = {name: verify_stage10q(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10Q hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["alignment"]
    lines = [
        "# Stage 10Q — Sunset Transcript Alignment", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Transcript utterances inside cluster: `{item['inside_utterances']}`",
        f"- Speakers inside cluster: `{item['inside_speaker_counts']}`",
        f"- Nearest related boundary offsets: `{item['nearest_prior_lead_seconds']:.3f} seconds before` / `{item['nearest_after_offset_seconds']:.3f} seconds after`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10q(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
