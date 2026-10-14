#!/usr/bin/env python3
"""Verify Stage 10V's task-conditioned representation-fitness gate."""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json
from stage10l_representation_compression import verify_stage10l
from stage10s_planned_sunset_window import verify_stage10s


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "processed_calibrated": False,
        "raw_calibrated": False,
        "representation_rank_rule": "task_conditioned",
        "processed_scientifically_invalid": False,
        "representations_wasteful": False,
        "specific_pixel_artifact_inferred": False,
        "quantitative_color_available": False,
        "scope": "verified_complete_action_cohort_and_fixed_sunset_block",
        "scientific_discovery_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_processed_products_calibrated": ("processed_calibrated", True),
        "call_raw_products_calibrated": ("raw_calibrated", True),
        "rank_largest_representation_as_best": ("representation_rank_rule", "largest_bytes_is_best"),
        "call_processed_products_scientifically_invalid": ("processed_scientifically_invalid", True),
        "call_representations_wasteful_duplicates": ("representations_wasteful", True),
        "infer_specific_pixel_artifact": ("specific_pixel_artifact_inferred", True),
        "claim_quantitative_color_available": ("quantitative_color_available", True),
        "generalize_byte_shares_to_all_archive_products": ("scope", "all_archive_products"),
        "claim_scientific_discovery_or_priority": ("scientific_discovery_or_priority", True),
        "open_pixels_for_representation_gate": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def verify_stage10v(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage10v.json"), mutation)
    expected = spec["frozen_observables"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    cohort = verify_stage10l(root)
    sunset = verify_stage10s(root)
    add_check(checks, errors, "representation_ledgers_replay", cohort["pass"] and sunset["pass"],
              error="Stage 10L or Stage 10S no longer verifies.")

    cohort_bytes = cohort["collection_bytes"]
    window = sunset["window"]
    derived = {
        "cohort_total_bytes": cohort["total_bytes"],
        "cohort_source_bytes": cohort_bytes["data_source"],
        "cohort_raw_bytes": cohort_bytes["data_raw"],
        "cohort_processed_bytes": cohort_bytes["data_processed"],
        "cohort_source_byte_share": cohort_bytes["data_source"] / cohort["total_bytes"],
        "cohort_raw_byte_share": cohort_bytes["data_raw"] / cohort["total_bytes"],
        "cohort_processed_byte_share": cohort_bytes["data_processed"] / cohort["total_bytes"],
        "cohort_processed_to_source_byte_ratio": cohort_bytes["data_processed"] / cohort_bytes["data_source"],
        "sunset_total_bytes": window["archive_size_bytes"],
        "sunset_source_bytes": window["source_bytes"],
        "sunset_raw_bytes": window["raw_bytes"],
        "sunset_processed_bytes": window["processed_bytes"],
        "sunset_processed_byte_share": window["processed_byte_share"],
        "calibrated_product_tiers": 0,
    }
    exact = [key for key, value in expected.items() if not isinstance(value, float)]
    floats = [key for key, value in expected.items() if isinstance(value, float)]
    footprint_ok = all(derived[key] == expected[key] for key in exact) and all(
        close(float(derived[key]), expected[key]) for key in floats
    )
    add_check(checks, errors, "representation_byte_footprints", footprint_ok,
              error="The frozen cohort or Sunset representation footprint changed.", derived=derived)

    guide = (root / spec["source_contract"]["data_user_guide_path"]).read_text(encoding="utf-8")
    compact = "".join(guide.casefold().split())
    guide_facts = {
        "no_calibration_applied": "nocalibrationhasbeenappliedtotheseproducts" in compact,
        "no_calibrated_products": "nocalibrateddataproductsareprovided" in compact,
        "source_preserves_native": "theypreservealloriginalembeddedmetadataandpixelvalues" in compact,
        "raw_preserves_bayer": "leavingthebayerpatternintact" in compact,
        "processed_is_interpreted": "processedproductsweregeneratedtoprovideuncalibratedbutinterpretedimageproducts" in compact,
        "processed_uses_srgb_autoscaling": "withsrgbandautoscalingapplied" in compact,
        "processed_may_reduce_detail": "mayreducefinedetails" in compact,
        "color_not_quantified": "colorsoutputbytheprocesscannotbecompletelyverifiedorquantified" in compact,
    }
    guide_ok = all(guide_facts.values())
    add_check(checks, errors, "data_user_guide_representation_semantics", guide_ok,
              error="A decision-bearing Data User Guide representation statement changed.", facts=guide_facts)

    gate = spec["task_representation_gate"]
    expected_gate = {
        "preserve_original_native_pixels_and_metadata": "source",
        "open_standardized_bayer_array_analysis": "raw",
        "human_viewable_vendor_interpretation": "processed",
        "instrument_independent_physical_measurement": "none_available",
        "quantitatively_verified_color": "none_available",
    }
    gate_ok = gate == expected_gate and len(set(gate.values())) == 4
    add_check(checks, errors, "task_conditioned_representation_gate", gate_ok,
              error="The task-conditioned representation gate changed.", gate=gate)

    state = spec["mutation_state"]
    boundary_ok = (
        not state["processed_calibrated"]
        and not state["raw_calibrated"]
        and state["representation_rank_rule"] == "task_conditioned"
        and not state["processed_scientifically_invalid"]
        and not state["representations_wasteful"]
        and not state["specific_pixel_artifact_inferred"]
        and not state["quantitative_color_available"]
        and state["scope"] == "verified_complete_action_cohort_and_fixed_sunset_block"
        and not state["scientific_discovery_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited calibration, ranking, quality, artifact, color, scope, discovery, or pixel claim was admitted.",
              mutation_state=state)

    evidence_state = "VERIFIED_STORAGE_WEIGHT_NOT_CALIBRATION_LEVEL" if footprint_ok and guide_ok and gate_ok else "REPRESENTATION_FITNESS_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "footprint": derived, "task_representation_gate": gate,
        "verified": "Processed TIFFs account for 67.932% of bytes in the verified complete-action cohort and 68.447% in the fixed Sunset block, yet the Data User Guide says no crew-camera products are calibrated and processed colors cannot be completely verified or quantified.",
        "decision_use": "Select the image representation after naming the task. Source preserves native pixels and metadata, raw exposes the Bayer array in an open archival format, processed provides a viewable vendor interpretation, and none supplies instrument-independent physical units or quantitatively verified color on its own.",
        "pixel_payload_bytes": state["pixel_payload_bytes"], "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10v(root)
    names = load_json(root / "spec/stage10v.json")["hard_negatives"]
    mutations = {name: verify_stage10v(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10V hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    item = result["footprint"]
    lines = [
        "# Stage 10V — Task-Conditioned Representation Fitness", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Complete-action cohort processed-byte share: `{item['cohort_processed_byte_share']:.3%}`",
        f"- Fixed Sunset block processed-byte share: `{item['sunset_processed_byte_share']:.3%}`",
        f"- Calibrated product tiers: `{item['calibrated_product_tiers']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`",
        "", "## Verified", "", result["verified"], "", "## Decision use", "", result["decision_use"],
        "", "## Task gate", "",
    ]
    for task, representation in result["task_representation_gate"].items():
        lines.append(f"- `{task}`: `{representation}`")
    lines.extend(["", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", ""])
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10v(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
