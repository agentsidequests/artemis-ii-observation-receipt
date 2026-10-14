#!/usr/bin/env python3
"""Verify Stage 11V target-field completion bounds."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from stage11u_selection_weighting_cascade import verify_with_mutations as verify_stage11u


TARGET = "Sunset"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "blank_fields_are_negative": False,
        "nonblank_tags_validated": False,
        "sunset_bound_rule": "observed_to_observed_plus_all_blanks",
        "lower_bound_interpretation": "possible_field_completion_extreme",
        "upper_bound_interpretation": "possible_field_completion_extreme",
        "bounds_kind": "separate_marginal_membership_bounds",
        "estimand": "target_field_completion",
        "scope": "frozen_complete_action_cohort",
        "nasa_acceptance_novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_blank_fields_negative": ("blank_fields_are_negative", True),
        "call_nonblank_tags_validated": ("nonblank_tags_validated", True),
        "narrow_sunset_bound_without_assumption": ("sunset_bound_rule", "observed_to_observed_plus_half_blanks"),
        "call_lower_bound_prevalence": ("lower_bound_interpretation", "true_prevalence"),
        "call_upper_bound_prevalence": ("upper_bound_interpretation", "true_prevalence"),
        "call_marginal_bounds_simultaneous_distribution": ("bounds_kind", "simultaneous_multiclass_distribution"),
        "call_bounds_physical_prevalence": ("estimand", "physical_target_prevalence"),
        "generalize_beyond_frozen_cohort": ("scope", "all_artemis_archive_versions"),
        "claim_nasa_acceptance_novelty_or_priority": ("nasa_acceptance_novelty_or_priority", True),
        "open_pixels_for_completion_bounds": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def source_identity(root: Path, expected: dict[str, Any]) -> dict[str, Any]:
    path = root / expected["path"]
    observed = {
        "path": expected["path"],
        "bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() else None,
    }
    observed["match"] = observed["bytes"] == expected["bytes"] and observed["sha256"] == expected["sha256"]
    return observed


def completion_bounds(total: int, observed: int, blank: int) -> tuple[float, float]:
    if any(type(value) is not int for value in (total, observed, blank)):
        raise ValueError("Completion counts must be integers.")
    if total <= 0 or observed < 0 or blank < 0 or observed + blank > total:
        raise ValueError("Invalid completion-count partition.")
    return observed / total, (observed + blank) / total


def completion_budget(total: int, blank: int, width_denominator: int) -> dict[str, int]:
    completion_bounds(total, 0, blank)
    if type(width_denominator) is not int or width_denominator <= 0:
        raise ValueError("Width denominator must be a positive integer.")
    remaining = min(blank, total // width_denominator)
    return {"minimum_blank_fields_resolved": blank - remaining, "maximum_remaining_blank_fields": remaining}


def sunset_completion_witness(rows: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
    source = [row for row in rows if row["collection_id"] == "data_source"]
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("source_capture_id", "observed_target_field", "field_is_blank", "lower_possible_sunset_membership", "upper_possible_sunset_membership"))
    lower = upper = 0
    identities = set()
    for row in source:
        identity, value = row["capture_identity"], row["target_id"]
        if not identity or identity in identities:
            raise ValueError("Completion witness requires unique source capture identities.")
        identities.add(identity)
        low = int(value == TARGET)
        high = int(not value or value == TARGET)
        lower += low
        upper += high
        writer.writerow((identity, value, int(not value), low, high))
    text = output.getvalue()
    return text, {
        "source_rows": len(source), "lower_sunset_count": lower, "upper_sunset_count": upper,
        "known_fields_preserved": all(
            (int(row["target_id"] == TARGET) == int(not row["target_id"] or row["target_id"] == TARGET))
            for row in source if row["target_id"]
        ),
        "csv_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "interpretation": "Two possible binary field completions, not imputed physical labels or training data.",
    }


def derive(rows: list[dict[str, str]]) -> dict[str, Any]:
    source = [row for row in rows if row["collection_id"] == "data_source"]
    counts = Counter(row["target_id"] for row in source if row["target_id"])
    blank = sum(not row["target_id"] for row in source)
    total = len(source)
    nonblank = total - blank
    bounds = {}
    for value, observed in sorted(counts.items()):
        lower, upper = completion_bounds(total, observed, blank)
        bounds[value] = {
            "observed_count": observed,
            "lower_count": observed,
            "upper_count": observed + blank,
            "observed_share_among_nonblank": observed / nonblank,
            "lower_share_full_cohort": lower,
            "upper_share_full_cohort": upper,
            "bound_width": blank / total,
        }
    _, witness = sunset_completion_witness(rows)
    majority_count = total // 2 + 1
    majority_needed = majority_count - counts[TARGET]
    return {
        "source_exposures": total,
        "nonblank_target_fields": nonblank,
        "blank_target_fields": blank,
        "observed_target_field_values": len(counts),
        "blank_share": blank / total,
        "bounds_by_target_field_value": bounds,
        "sunset": bounds[TARGET],
        "sunset_majority": {
            "strict_majority_count": majority_count,
            "additional_blank_memberships_needed": majority_needed,
            "required_fraction_of_blank_fields": majority_needed / blank,
        },
        "deterministic_completion_budgets": {
            label: completion_budget(total, blank, denominator)
            for label, denominator in (("10_percentage_points", 10), ("5_percentage_points", 20), ("1_percentage_point", 100))
        },
        "completion_witness": witness,
        "extreme_assignments": {
            "no_blank_fields_assigned_to_sunset": {"sunset_count": witness["lower_sunset_count"], "cohort_count": witness["source_rows"]},
            "all_blank_fields_assigned_to_sunset": {"sunset_count": witness["upper_sunset_count"], "cohort_count": witness["source_rows"]},
        },
    }


def mapping_matches(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    for key, value in expected.items():
        observed = actual[key]
        if isinstance(value, dict):
            if not mapping_matches(observed, value):
                return False
        elif isinstance(value, float):
            if not close(float(observed), value):
                return False
        elif observed != value:
            return False
    return True


def prepare_verification(root: Path, spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    upstream = verify_stage11u(root)
    identity = source_identity(root, spec["sources"][0])
    with (root / spec["sources"][0]["path"]).open("r", encoding="utf-8", newline="") as stream:
        metrics = derive(list(csv.DictReader(stream)))
    return upstream, identity, metrics


def verify_stage11v(
    root: Path, mutation: str | None = None,
    prepared: tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11v.json"), mutation)
    checks: dict[str, bool] = {}
    errors: list[str] = []
    upstream, identity, metrics = prepared or prepare_verification(root, spec)
    checks["stage11u_replays"] = upstream["pass"]
    if not checks["stage11u_replays"]:
        errors.append("Stage 11U no longer verifies.")

    checks["source_identity"] = identity["match"]
    if not checks["source_identity"]:
        errors.append("The frozen relationship manifest identity changed.")

    frozen = spec["frozen_observables"]
    checks["frozen_observables"] = mapping_matches(metrics, frozen)
    if not checks["frozen_observables"]:
        errors.append("The frozen completion-bound observables changed.")

    widths = [item["bound_width"] for item in metrics["bounds_by_target_field_value"].values()]
    checks["equal_width_identity"] = bool(widths) and all(close(width, metrics["blank_share"]) for width in widths)
    if not checks["equal_width_identity"]:
        errors.append("At least one target-field marginal bound width differs from the blank-field share.")

    sunset = metrics["sunset"]
    extremes = metrics["extreme_assignments"]
    checks["sunset_extremes_materialized"] = (
        extremes["no_blank_fields_assigned_to_sunset"]["sunset_count"] == sunset["lower_count"]
        and extremes["all_blank_fields_assigned_to_sunset"]["sunset_count"] == sunset["upper_count"]
        and sunset["upper_count"] - sunset["lower_count"] == metrics["blank_target_fields"]
        and metrics["completion_witness"]["known_fields_preserved"]
        and metrics["completion_witness"]["source_rows"] == metrics["source_exposures"]
    )
    if not checks["sunset_extremes_materialized"]:
        errors.append("The Sunset extreme assignments do not reproduce the declared bounds.")

    state = spec["mutation_state"]
    checks["claim_and_access_boundaries"] = (
        not state["blank_fields_are_negative"]
        and not state["nonblank_tags_validated"]
        and state["sunset_bound_rule"] == "observed_to_observed_plus_all_blanks"
        and state["lower_bound_interpretation"] == "possible_field_completion_extreme"
        and state["upper_bound_interpretation"] == "possible_field_completion_extreme"
        and state["bounds_kind"] == "separate_marginal_membership_bounds"
        and state["estimand"] == "target_field_completion"
        and state["scope"] == "frozen_complete_action_cohort"
        and not state["nasa_acceptance_novelty_or_priority"]
        and state["pixel_payload_bytes"] == 0
    )
    if not checks["claim_and_access_boundaries"]:
        errors.append("A prohibited label, bound, distribution, prevalence, scope, acceptance, or pixel claim was admitted.")

    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": "VERIFIED_TARGET_FIELD_COMPLETION_BOUNDS" if not errors else "REJECTED",
        "source_identity": identity,
        "metrics": metrics,
        "finding": "With observed nonblank fields fixed and blanks unconstrained one target-field value at a time, Sunset spans 20.418% to 75.546% of the frozen cohort. The 55.128 percentage-point interval is the blank-field share, not an estimate of physical prevalence.",
        "decision_use": "Report tagged-subset balance together with full-cohort completion bounds. Narrow the interval only with a declared label audit or another independently justified constraint on blank fields.",
        "pixel_payload_bytes_opened": state["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec/stage11v.json")
    # All declaration mutations use one frozen input generation, as in Stage 11U.
    prepared = prepare_verification(root, spec)
    baseline = verify_stage11v(root, prepared=prepared)
    names = spec["hard_negatives"]
    mutations = {name: verify_stage11v(root, name, prepared=prepared) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 11V hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    sunset = metrics["sunset"]
    lines = [
        "# Stage 11V - Target-Field Completion Bounds",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Source exposures: `{metrics['source_exposures']:,}`",
        f"- Nonblank / blank target fields: `{metrics['nonblank_target_fields']:,}` / `{metrics['blank_target_fields']:,}`",
        f"- Observed target-field values: `{metrics['observed_target_field_values']}`",
        f"- Sunset observed share among nonblank fields: `{sunset['observed_share_among_nonblank']:.3%}`",
        f"- Sunset full-cohort completion bound: `{sunset['lower_share_full_cohort']:.3%}` to `{sunset['upper_share_full_cohort']:.3%}`",
        f"- Bound width: `{sunset['bound_width']:.3%}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes_opened']}`",
        f"- Row-level completion witnesses: `{metrics['completion_witness']['source_rows']:,}`",
        "",
        "## Finding",
        "",
        result["finding"],
        "",
        "## Decision use",
        "",
        result["decision_use"],
        "",
        "## Majority tipping point and audit job",
        "",
        "A strict Sunset field majority requires 2,251 of the 4,193 blank fields (53.685%) to be completed as Sunset. One fewer produces exactly 50%, not a majority. Neither side is established by the current fields.",
        "",
        "If no additional structural assumptions are made, resolving individual blank fields reduces the worst-case completion width by one divided by 7,606 per field. A width no greater than 10, 5 or 1 percentage points requires resolving at least 3,433, 3,813 or 4,117 blank fields respectively. These are deterministic completion budgets, not recommended statistical sample sizes.",
        "",
        "A sample-based estimate is a different job. Declare the sampling frame, inclusion probabilities, task-native label oracle, dependence handling and uncertainty model before using it to estimate composition. An estimated proportion or confidence interval is not a guarantee about all unreviewed fields. The observed tag values are themselves not validated image-content labels.",
        "",
        "## Claim ceiling",
        "",
        result["claim_ceiling"],
        "",
        "## Hard negatives",
        "",
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
    parser.add_argument("--extremes-output", type=Path)
    parser.add_argument("--mutation")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    outputs = [path.resolve() for path in (args.json_output, args.markdown_output, args.extremes_output) if path is not None]
    if len(outputs) != len(set(outputs)):
        raise ValueError("Output paths must be distinct.")
    frozen_source = (root / load_json(root / "spec/stage11v.json")["sources"][0]["path"]).resolve()
    for output in outputs:
        if output == frozen_source or any(output.is_relative_to((root / directory).resolve()) for directory in ("corpus", "evidence", "spec", "src", "tests")):
            raise ValueError("Outputs cannot overwrite source or verification evidence.")
    result = verify_with_mutations(root) if args.command == "verify" else verify_stage11v(root, args.mutation)
    if args.extremes_output:
        if not result["pass"]:
            raise ValueError("Completion witnesses are withheld when verification fails.")
        spec = load_json(root / "spec/stage11v.json")
        if not source_identity(root, spec["sources"][0])["match"]:
            raise ValueError("Completion source identity changed before export.")
        with (root / spec["sources"][0]["path"]).open("r", encoding="utf-8", newline="") as stream:
            text, witness = sunset_completion_witness(list(csv.DictReader(stream)))
        if not source_identity(root, spec["sources"][0])["match"] or witness != result["metrics"]["completion_witness"]:
            raise ValueError("Completion source changed between verification and export.")
        args.extremes_output.parent.mkdir(parents=True, exist_ok=True)
        args.extremes_output.write_text(text, encoding="utf-8", newline="")
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
