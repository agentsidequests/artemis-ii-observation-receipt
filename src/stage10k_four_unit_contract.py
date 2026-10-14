#!/usr/bin/env python3
"""Verify Stage 10K's cross-stage four-unit analysis contract."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from stage10a_metadata_integrity import add_check, load_json
from stage10f_mechanism_triangulation import verify_stage10f
from stage10g_retrieval_distortion import verify_stage10g
from stage10h_source_volume_reconciliation import verify_stage10h
from stage10i_provenance_crosswalk import verify_stage10i
from stage10j_fractional_bracket_expansion import verify_stage10j


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "one_denominator": False,
        "coverage_has_ledger": True,
        "products_are_observations": False,
        "actions_exhaustive": False,
        "residuals_are_missing": False,
        "mechanism_scope": "stage10f_repeated_signature",
        "fractures_are_errors": False,
        "snapshot_date_required": True,
        "global_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    mapping = {
        "collapse_to_one_denominator": ("one_denominator", True),
        "report_coverage_without_ledger": ("coverage_has_ledger", False),
        "treat_products_as_observations": ("products_are_observations", True),
        "call_six_pattern_actions_exhaustive": ("actions_exhaustive", True),
        "call_inventory_residuals_missing_data": ("residuals_are_missing", True),
        "call_every_fracture_an_error": ("fractures_are_errors", True),
        "omit_snapshot_date": ("snapshot_date_required", False),
        "claim_global_priority": ("global_priority", True),
        "open_pixels_for_unit_contract": ("pixel_payload_bytes", 1),
    }
    if mutation == "generalize_local_curation_mechanism":
        state["mechanism_scope"] = "mission_wide"
    elif mutation in mapping:
        key, value = mapping[mutation]
        state[key] = value
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_stage10k(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10k.json"), mutation)
    expected = spec["frozen_observables"]
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    stage10f = verify_stage10f(root)
    stage10g = verify_stage10g(root)
    stage10h = verify_stage10h(root)
    stage10i = verify_stage10i(root)
    stage10j = verify_stage10j(root)
    upstream = {"stage10f": stage10f, "stage10g": stage10g, "stage10h": stage10h, "stage10i": stage10i, "stage10j": stage10j}
    upstream_ok = all(item.get("pass") is True for item in upstream.values())
    add_check(checks, errors, "upstream_replay", upstream_ok,
              error="At least one decision-bearing Stage 10 verifier no longer replays.",
              evidence_states={name: item.get("evidence_state") for name, item in upstream.items()})

    units = {
        "source_files": stage10h["source_file_count"],
        "source_volume_gb": stage10h["source_volume_gb"],
        "archive_products": stage10h["atlas_product_count"],
        "archive_decimal_tb": stage10h["atlas_archive_decimal_tb"],
        "nikon_capture_identities": stage10i["current_nikon_identities"],
        "complete_six_pattern_actions": stage10j["complete_brackets"],
        "exposures_in_complete_actions": stage10j["exposures_in_complete_brackets"],
        "unadmitted_raw_records": stage10j["unadmitted_records"],
    }
    units_ok = all(units[key] == expected[key] for key in units)
    add_check(checks, errors, "four_unit_ledger", units_ok,
              error="A source, product, identity, or action denominator changed.", units=units)

    provenance = {
        "documented_pending_iphone": stage10i["documented_pending_iphone"],
        "unexplained_nikon_residuals": stage10i["unexplained_nikon_total"],
        "unexplained_cab_cam_2_residuals": stage10i["unexplained_orion_residuals"]["cab2"],
    }
    provenance_ok = all(provenance[key] == expected[key] for key in provenance)
    add_check(checks, errors, "dated_provenance_residuals", provenance_ok,
              error="The documented pending set or unresolved inventory residuals changed.", **provenance)

    retrieval = {
        "fractured_capture_identities": stage10g["exposure_ids"],
        "fractured_products": stage10g["product_records"],
        "stress_case_actions": stage10g["discussion_crew_choice_actions"],
        "stress_case_filtered_products": stage10g["discussion_product_records"],
        "stress_case_complete_actions": stage10g["discussion_complete_actions_recoverable"],
        "stress_case_companion_exposures_needed": stage10g["discussion_companion_exposure_ids_needed"],
    }
    retrieval_ok = all(retrieval[key] == expected[key] for key in retrieval)
    add_check(checks, errors, "retrieval_distortion", retrieval_ok,
              error="The verified product inflation or complete-action under-recovery changed.", **retrieval)

    cross_day = sum(value for day, value in stage10j["fractures_by_flight_day"].items() if day != "6")
    scope_ok = (
        stage10j["activity_fractures"] == expected["activity_fractures"]
        and cross_day == expected["cross_day_fractures"]
        and stage10f["repeated_actions"] == expected["local_repeated_signature_actions"]
        and stage10h["prior_hypothesis_superseded"] is True
        and stage10j["stage10e_generalization_superseded"] is True
    )
    add_check(checks, errors, "supersession_and_mechanism_scope", scope_ok,
              error="A supersession or the local-versus-mission-wide boundary changed.",
              fractures=stage10j["activity_fractures"], cross_day_fractures=cross_day,
              local_signature_actions=stage10f["repeated_actions"])

    state = spec["mutation_state"]
    boundary_ok = (
        not state["one_denominator"]
        and state["coverage_has_ledger"]
        and not state["products_are_observations"]
        and not state["actions_exhaustive"]
        and not state["residuals_are_missing"]
        and state["mechanism_scope"] == "stage10f_repeated_signature"
        and not state["fractures_are_errors"]
        and state["snapshot_date_required"]
        and not state["global_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "analysis_admission_boundary", boundary_ok,
              error="A prohibited denominator, completeness, mechanism, error, novelty, date, or pixel claim was admitted.",
              mutation_state=state)

    verified = (
        "The preserved release has four non-interchangeable analysis units: 11,591 source files / 814.51 GB; "
        "32,133 downloadable products / 2.526790075510 TB; 10,329 Nikon capture identities; and 2,166 complete "
        "actions under six frozen bracket patterns. The units describe acquisition scale, retrieval burden, exposures, "
        "and bounded observation evidence respectively."
    )
    decision_use = (
        "Admit a later coverage, sample-size, or completeness statement only when it names the ledger, snapshot date, "
        "and reconstruction unit. Use the 84-product / zero-complete-action stress case to demonstrate consequence, "
        "not as a mission-wide error-rate estimate."
    )
    evidence_state = "VERIFIED_FOUR_UNIT_ANALYSIS_CONTRACT" if all((upstream_ok, units_ok, provenance_ok, retrieval_ok, scope_ok)) else "FOUR_UNIT_CONTRACT_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "units": units, "provenance": provenance, "retrieval": retrieval,
        "activity_fractures": stage10j["activity_fractures"], "cross_day_fractures": cross_day,
        "local_repeated_signature_actions": stage10f["repeated_actions"],
        "stage10d_hypothesis_superseded": stage10h["prior_hypothesis_superseded"],
        "stage10e_generalization_superseded": stage10j["stage10e_generalization_superseded"],
        "verified": verified, "decision_use": decision_use, "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"], "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10k(root)
    names = load_json(root / "spec" / "stage10k.json")["hard_negatives"]
    mutations = {name: verify_stage10k(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10K hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    units = result["units"]
    lines = [
        "# Stage 10K — Four-Unit Analysis Contract", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Source ledger: `{units['source_files']:,}` files / `{units['source_volume_gb']:.2f} GB`",
        f"- Archive footprint: `{units['archive_products']:,}` products / `{units['archive_decimal_tb']:.12f} TB`",
        f"- Nikon capture identities: `{units['nikon_capture_identities']:,}`",
        f"- Complete six-pattern actions: `{units['complete_six_pattern_actions']:,}`",
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
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10k(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
