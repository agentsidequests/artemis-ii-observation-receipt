"""Sharp, assumption-bound target-field accounting sensitivity. No pixel access."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("paper-review/tag-weight-robustness")
COLLECTIONS = ("data_source", "data_raw", "data_processed")
UNITS = ("exposure_fields", "products", *(c + "_bytes" for c in COLLECTIONS), "all_representation_bytes")
FORBIDDEN = {"observed_tag_errors", "validated_content_labels", "physical_prevalence", "statistical_confidence_interval",
             "audit_sample_size", "actual_audit_or_pixel_access", "cost_optimal_under_heterogeneous_cost",
             "physical_identity_or_independence", "nasa_acceptance_or_global_novelty", "replacement_of_existing_scientific_receipts"}


@dataclass(frozen=True)
class Field:
    identity: str
    target: str
    action: str
    activity: str
    source_bytes: int
    raw_bytes: int
    processed_bytes: int

    def weight(self, unit: str) -> int:
        weights = dict(zip(UNITS, (1, 3, self.source_bytes, self.raw_bytes, self.processed_bytes,
                                  self.source_bytes + self.raw_bytes + self.processed_bytes)))
        if unit not in weights:
            raise ValueError("Unknown accounting unit")
        return weights[unit]


def ratio(numerator: int, denominator: int) -> dict:
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise ValueError("Ratios require exact integer weights and positive denominator")
    return {"numerator": numerator, "denominator": denominator, "share": numerator / denominator,
            "percentage": 100 * numerator / denominator}


def parse_manifest(payload: bytes) -> list[Field]:
    captures: dict[str, dict] = {}
    product_ids = set()
    for row in csv.DictReader(io.StringIO(payload.decode("utf-8"))):
        product = row["product_id"]
        capture = row["capture_identity"]
        collection = row["collection_id"]
        size = int(row["archive_size_bytes"])
        if not product or product in product_ids or not capture or collection not in COLLECTIONS or size <= 0:
            raise ValueError("Invalid product identity, collection or positive byte size")
        product_ids.add(product)
        group = captures.setdefault(capture, {})
        if collection in group:
            raise ValueError("Duplicate capture representation")
        group[collection] = row
    fields = []
    for identity, group in sorted(captures.items()):
        if set(group) != set(COLLECTIONS):
            raise ValueError("Incomplete capture representation inventory")
        source = group["data_source"]
        for key in ("target_id", "action_id", "activity_id", "camera_serial", "exposure_position", "exposures_in_action"):
            if len({r[key] for r in group.values()}) != 1:
                raise ValueError("Conflicting per-capture fields: " + key)
        fields.append(Field(identity, source["target_id"], source["action_id"], source["activity_id"],
                            *(int(group[c]["archive_size_bytes"]) for c in COLLECTIONS)))
    if not fields:
        raise ValueError("Empty manifest")
    return fields


def order(fields: list[Field], unit: str) -> list[Field]:
    return sorted(fields, key=lambda field: (-field.weight(unit), field.identity))


def validate_weights(fields: list[Field], unit: str) -> None:
    if len({f.identity for f in fields}) != len(fields):
        raise ValueError("Duplicate field identity")
    if any(type(f.weight(unit)) is not int or f.weight(unit) <= 0 for f in fields):
        raise ValueError("Weights must be positive integers")


def bounds(fields: list[Field], unit: str, target: str, budget: int = 0, include_blanks: bool = True) -> dict:
    if type(budget) is not int or budget < 0:
        raise ValueError("Reassignment budget must be a nonnegative integer")
    if not isinstance(target, str) or not target:
        raise ValueError("Target must be a nonblank field value")
    validate_weights(fields, unit)
    selected = [f for f in fields if include_blanks or f.target]
    denominator = sum(f.weight(unit) for f in selected)
    if denominator <= 0:
        raise ValueError("Empty weighted analysis population")
    positive = order([f for f in selected if f.target == target], unit)
    negative = order([f for f in selected if f.target and f.target != target], unit)
    unknown = [f for f in selected if not f.target]
    known_weight = sum(f.weight(unit) for f in positive)
    unknown_weight = sum(f.weight(unit) for f in unknown)
    down = positive[:budget]
    up = negative[:budget]
    lower = known_weight - sum(f.weight(unit) for f in down)
    upper = known_weight + unknown_weight + sum(f.weight(unit) for f in up)
    return {"unit": unit, "population": "full_cohort" if include_blanks else "frozen_nonblank_subset",
            "reassignment_budget": budget, "total_weight": denominator, "known_target_weight": known_weight,
            "blank_weight": unknown_weight, "lower": ratio(lower, denominator), "upper": ratio(upper, denominator),
            "width": ratio(upper - lower, denominator), "lower_reassigned_ids": [f.identity for f in down],
            "upper_reassigned_ids": [f.identity for f in up],
            "extrema_are_separate_witnesses": True}


def majority_witness(fields: list[Field], unit: str, target: str) -> dict:
    validate_weights(fields, unit)
    selected = [f for f in fields if f.target]
    total = sum(f.weight(unit) for f in selected)
    if total <= 0:
        raise ValueError("Empty recorded-field population")
    positive = order([f for f in selected if f.target == target], unit)
    original = sum(f.weight(unit) for f in positive)
    remaining = original
    picked = []
    previous = None
    for f in positive:
        if 2 * remaining <= total:
            break
        previous = remaining
        picked.append(f)
        remaining -= f.weight(unit)
    crossed = 2 * remaining <= total
    if not crossed or (picked and 2 * previous <= total):
        raise AssertionError("Strict-majority crossing failure")
    return {"unit": unit, "denominator": total, "original": ratio(original, total),
            "initial_strict_majority": 2 * original > total,
            "minimum_fields_to_lose_strict_majority": len(picked), "after": ratio(remaining, total),
            "predecessor": ratio(previous, total) if previous is not None else None,
            "reassigned_ids": [f.identity for f in picked],
            "removed_weight": original - remaining, "population_and_weights_unchanged": True}


def completion_budget(fields: list[Field], unit: str, numerator: int, denominator: int) -> dict:
    validate_weights(fields, unit)
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0 or not 0 <= numerator <= denominator:
        raise ValueError("Width target must be a rational in [0,1]")
    total = sum(f.weight(unit) for f in fields)
    if total <= 0:
        raise ValueError("Empty weighted population")
    blanks = order([f for f in fields if not f.target], unit)
    remaining = sum(f.weight(unit) for f in blanks)
    picked = []
    previous = None
    for f in blanks:
        if remaining * denominator <= total * numerator:
            break
        previous = remaining
        picked.append(f)
        remaining -= f.weight(unit)
    if remaining * denominator > total * numerator:
        raise AssertionError("Completion threshold not reached")
    if picked and previous * denominator <= total * numerator:
        raise AssertionError("Completion predecessor already qualified")
    return {"unit": unit, "target_width": ratio(numerator, denominator),
            "minimum_fields_resolved_equal_field_cost": len(picked), "remaining_width": ratio(remaining, total),
            "predecessor_width": ratio(previous, total) if previous is not None else None,
            "resolved_ids": [f.identity for f in picked], "real_resolution_or_cost_optimality": False}


def validate_contract(contract: dict) -> None:
    if tuple(contract["units"]) != UNITS or contract["target"] != "Sunset":
        raise ValueError("Unexpected unit/target contract")
    if set(contract["forbidden_claims"]) != FORBIDDEN or any(value is not False for value in contract["forbidden_claims"].values()):
        raise ValueError("Unsupported declaration")
    if contract["assumptions"]["resolution_cost"] != "one unit per individual field; real viewing, adjudication, retrieval and support costs unknown":
        raise ValueError("Unsupported cost model")


def run(root: Path = ROOT) -> tuple[dict, list[dict], list[dict], str]:
    contract = json.loads((root / OUT / "contract.json").read_text(encoding="utf-8"))
    validate_contract(contract)
    expected = contract["source"]
    payload = (root / expected["path"]).read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) != expected["bytes"] or digest != expected["sha256"]:
        raise ValueError("Frozen source identity mismatch")
    fields = parse_manifest(payload)
    partition = {"products": len(fields) * 3, "exposure_fields": len(fields),
                 "recorded_fields": sum(bool(f.target) for f in fields),
                 "blank_fields": sum(not f.target for f in fields),
                 "recorded_sunset_fields": sum(f.target == contract["target"] for f in fields)}
    if partition != contract["frozen_partition"]:
        raise ValueError("Frozen partition mismatch")
    target = contract["target"]
    summaries = []
    intervals = []
    witness_rows = []
    priority_rows = []
    by_id = {f.identity: f for f in fields}
    for unit in UNITS:
        completion = bounds(fields, unit, target)
        selected = bounds(fields, unit, target, include_blanks=False)
        majority = majority_witness(fields, unit, target)
        budgets = {item["name"]: completion_budget(fields, unit, item["numerator"], item["denominator"])
                   for item in contract["completion_width_targets"]}
        summaries.append({"unit": unit, "completion": completion, "selected": selected,
                          "majority_sensitivity": majority, "completion_budgets": budgets})
        for r in contract["recorded_field_reassignment_budgets"]:
            for full in (True, False):
                interval = bounds(fields, unit, target, r, full)
                intervals.append(interval)
        for rank, identity in enumerate(majority["reassigned_ids"], 1):
            f = by_id[identity]
            witness_rows.append({"unit": unit, "rank": rank, "capture_identity": identity,
                                 "action_id": f.action, "activity_id": f.activity, "original_target": f.target,
                                 "counterfactual_target": "non-Sunset nonblank", "weight": f.weight(unit),
                                 "kind": "hypothetical_reassignment_not_observed_error"})
        remaining = completion["blank_weight"]
        for rank, f in enumerate(order([f for f in fields if not f.target], unit), 1):
            remaining -= f.weight(unit)
            priority_rows.append({"unit": unit, "equal_field_cost_rank": rank, "capture_identity": f.identity,
                                  "accounting_weight": f.weight(unit), "remaining_unknown_weight": remaining,
                                  "denominator": completion["total_weight"], "real_audit_performed": "false"})
    result = {"id": contract["id"], "version": contract["version"], "pass": True,
              "evidence_state": "COMPUTED_ASSUMPTION_BOUND_METADATA_SENSITIVITY",
              "source_identity": {**expected, "match": True}, "partition": partition,
              "units": summaries, "reassignment_sensitivity": intervals,
              "forbidden_claims": contract["forbidden_claims"], "claim_ceiling": contract["claim_ceiling"],
              "new_pixel_bytes_opened": 0, "source_or_prior_receipts_modified": False,
              "oracle_independence": "Partial: common metadata/assumptions; separate native recount and small exhaustive oracle required."}
    report = render_report(result)
    return result, witness_rows, priority_rows, report


def render_report(result: dict) -> str:
    combined = next(s for s in result["units"] if s["unit"] == "all_representation_bytes")
    m = combined["majority_sensitivity"]
    lines = ["# Artemis II tag-weight robustness", "", "13 October 2026. Private exploratory accounting follow-on, not a new physical or image-content result.", "",
             "## The new bounded result", "",
             f"Sunset occupies {m['original']['percentage']:.6f}% of the bytes in the original nonblank-tag subset. "
             f"Reassigning the {m['minimum_fields_to_lose_strict_majority']} largest Sunset-tagged exposure fields to another nonblank target "
             f"would reduce its byte share to {m['after']['percentage']:.6f}%; the best {m['minimum_fields_to_lose_strict_majority'] - 1}-field reassignment "
             f"still leaves {m['predecessor']['percentage']:.6f}%. The query, total bytes, capture keys and representations remain fixed.", "",
             "These are hypothetical memberships, not detected tag errors. The source is not relabeled. This sensitivity concerns a narrow majority claim, not Sunset's ranking or physical presence.", "",
             "## Missingness survives the weighting change", "",
             "Nonblank values are held fixed here, with each blank unconstrained for one target value. These are sharp marginal metadata-completion ranges, not confidence intervals, content prevalence or jointly achievable multiclass endpoints.", "",
             "| Unit | Lower share | Upper share | Width | Minimum blank-field resolutions for ≤5pp width |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for s in result["units"]:
        b = s["completion"]
        lines.append(f"| {s['unit']} | {b['lower']['percentage']:.3f}% | {b['upper']['percentage']:.3f}% | {b['width']['percentage']:.3f}pp | {s['completion_budgets']['5pp']['minimum_fields_resolved_equal_field_cost']:,} |")
    lines += ["", "For combined archive bytes the possible full-cohort Sunset membership range remains 25.189%-77.130%. "
              "The 51.940pp width is unresolved accounting mass. Prioritizing the highest-weight blank fields minimizes the number of perfectly resolved fields "
              "under equal field cost, but still requires 3,747 resolutions for a worst-case width at most 5pp. The exposure-weighted baseline needs 3,813. "
              "Changing the unit or sorting the blanks does not make this a small deterministic completion task.", "",
              "## Constructive witnesses and proof", "",
              "For fixed positive weights, each completion endpoint is attained by setting every blank target membership to zero or one. "
              "For an at-most-r recorded-field reassignment budget, the lower endpoint removes the r largest known-positive weights; "
              "the upper endpoint adds the r largest known-negative weights. These are separate realizable witnesses. "
              "The sum of the r largest weights is an upper bound on every r-field subset, so the majority witness and equal-field-cost budget are cardinality-minimal. "
              "Integer predecessor checks avoid floating-point decisions at 50% or the requested width.", "",
              "The saved JSON also contains 0, 1, 25, 47, 48, 50, 100 and 200-field sensitivity bounds for both populations and all six units. "
              "Budgets are assumptions, not estimates of the archive's error rate. The CSV witness identifies exact frozen capture keys, actions, activities and weights; "
              "the priority CSV is a hypothetical field-resolution order, not a reviewer queue or an executed audit.", "",
              "## Explicit recommendations", "",
              "1. If asserting a selected-byte majority, publish the smallest known-tag perturbation that changes it, alongside the query, weights and source version. "
              "In this frozen reconstruction, the diagnostic threshold is 48 fields out of 3,413 recorded fields (about 1.41%); that is not a measured error rate.",
              "2. Distinguish completing blanks from validating recorded tags. A blank-only audit cannot establish the accuracy of the selected-byte majority.",
              "3. Declare the audit job before prioritizing: worst-case individual-field completion, probability-based estimation, or majority robustness. "
              "Do not use the 3,747-field guarantee as a statistical sample size or demand NASA backfill an archive not designed for this target task.",
              "4. Use weight-descending priority only for an accepted equal-field-cost completion objective. If retrieval, viewing or adjudication costs differ, "
              "freeze those costs and solve the appropriate constrained problem; weight sorting is not generally cost-optimal. "
              "Image-content judgments still require a qualified concept, reference and reviewer workflow.", "",
              "NASA/PDS already supply substantial provenance and relevant scientific practice. These are task-specific receipt proposals for review, not NASA-accepted requirements or evidence of an archive defect.", "",
              "## Limits and replay", "",
              result["claim_ceiling"], "",
              "Original filename/order-conditioned grouping and physical-identity uncertainty remain active. The one-action conditional sensitivity is not silently substituted. "
              "Flash timing, distance withdrawals, no-photometry and no-calibrated-flux ceilings are unchanged. No pixels, new source acquisitions, image labels, actual audits, outreach or publication were performed.", "",
              "From the owning private Testbed, run `python -B -m src.tag_weight_robustness --check`. "
              "The contract, result, witness and source hash are under `paper-review/tag-weight-robustness/`; the exact source manifest remains unmodified. "
              "See `VERIFICATION.md` for measured checks and native-oracle scope. This report alone does not establish those checks passed.", ""]
    return "\n".join(lines)


def csv_bytes(rows: list[dict]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def artifacts(root: Path = ROOT) -> dict[str, bytes]:
    result, witnesses, priorities, report = run(root)
    return {"result.json": (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            "majority-reassignment-witness.csv": csv_bytes(witnesses),
            "blank-resolution-priority.csv": csv_bytes(priorities), "REPORT.md": report.encode("utf-8")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Recompute and compare all saved artifacts; never write")
    args = parser.parse_args()
    try:
        outputs = artifacts()
        for name, payload in outputs.items():
            destination = ROOT / OUT / name
            if args.check:
                if not destination.is_file() or destination.read_bytes() != payload:
                    raise ValueError("Saved artifact drift: " + name)
            else:
                destination.write_bytes(payload)
        print(json.dumps({"pass": True, "mode": "check" if args.check else "write", "artifacts": len(outputs),
                          "new_pixel_bytes_opened": 0}))
        return 0
    except (ValueError, KeyError, AssertionError, OSError) as exc:
        print(json.dumps({"pass": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
