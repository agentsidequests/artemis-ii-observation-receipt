#!/usr/bin/env python3
"""Verify Stage 11U's selection and weighting cascade."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from stage10w_target_tag_selection import verify_stage10w


TARGET = "Sunset"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator <= 0:
        raise ValueError("Ratio denominator must be positive")
    return numerator / denominator


def concentration_equivalent(weights: list[float]) -> float:
    total = sum(weights)
    if total <= 0:
        raise ValueError("Concentration weights must sum to a positive value")
    return total * total / sum(weight * weight for weight in weights)


def source_identity(root: Path, expected: dict[str, Any]) -> dict[str, Any]:
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
    return observed


def derive(rows: list[dict[str, str]]) -> dict[str, Any]:
    source_rows = [row for row in rows if row["collection_id"] == "data_source"]
    tagged_source = [row for row in source_rows if row["target_id"]]
    sunset_source = [row for row in source_rows if row["target_id"] == TARGET]

    action_tags: dict[str, set[str]] = defaultdict(set)
    action_source_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        action_source_rows[row["action_id"]].append(row)
        if row["target_id"]:
            action_tags[row["action_id"]].add(row["target_id"])

    selected_actions = {action_id for action_id, tags in action_tags.items() if tags}
    sunset_actions = {action_id for action_id, tags in action_tags.items() if TARGET in tags}
    tagged_capture_ids = {row["capture_identity"] for row in tagged_source}
    sunset_capture_ids = {row["capture_identity"] for row in sunset_source}

    tagged_products = [row for row in rows if row["capture_identity"] in tagged_capture_ids]
    sunset_products = [row for row in rows if row["capture_identity"] in sunset_capture_ids]
    selected_action_products = [row for row in rows if row["action_id"] in selected_actions]
    sunset_action_products = [row for row in rows if row["action_id"] in sunset_actions]

    strict_action_share = ratio(len(sunset_actions), len(selected_actions))
    strict_exposure_share = ratio(len(sunset_source), len(tagged_source))
    strict_product_share = ratio(len(sunset_products), len(tagged_products))
    tagged_bytes = sum(int(row["archive_size_bytes"]) for row in tagged_products)
    sunset_bytes = sum(int(row["archive_size_bytes"]) for row in sunset_products)
    strict_byte_share = ratio(sunset_bytes, tagged_bytes)

    selected_action_exposures = sum(len(action_source_rows[action_id]) for action_id in selected_actions)
    sunset_action_exposures = sum(len(action_source_rows[action_id]) for action_id in sunset_actions)
    selected_action_bytes = sum(int(row["archive_size_bytes"]) for row in selected_action_products)
    sunset_action_bytes = sum(int(row["archive_size_bytes"]) for row in sunset_action_products)
    collection_byte_sensitivity = {}
    for collection_id in ("data_source", "data_raw", "data_processed"):
        tagged_collection = [
            row for row in tagged_products if row["collection_id"] == collection_id
        ]
        sunset_collection = [
            row for row in sunset_products if row["collection_id"] == collection_id
        ]
        tagged_collection_bytes = sum(int(row["archive_size_bytes"]) for row in tagged_collection)
        sunset_collection_bytes = sum(int(row["archive_size_bytes"]) for row in sunset_collection)
        collection_byte_sensitivity[collection_id] = {
            "sunset_bytes": sunset_collection_bytes,
            "tagged_bytes": tagged_collection_bytes,
            "sunset_share": ratio(sunset_collection_bytes, tagged_collection_bytes),
        }

    attribution_activity = "24_Sunset"
    outside_activity_source = [
        row for row in source_rows if row["activity_id"] != attribution_activity
    ]
    outside_activity_tags: dict[str, set[str]] = defaultdict(set)
    for row in outside_activity_source:
        if row["target_id"]:
            outside_activity_tags[row["action_id"]].add(row["target_id"])
    outside_selected_actions = {
        action_id for action_id, tags in outside_activity_tags.items() if tags
    }
    outside_sunset_actions = {
        action_id for action_id, tags in outside_activity_tags.items() if TARGET in tags
    }
    outside_tagged_source = [row for row in outside_activity_source if row["target_id"]]
    outside_sunset_source = [
        row for row in outside_tagged_source if row["target_id"] == TARGET
    ]
    outside_tagged_capture_ids = {
        row["capture_identity"] for row in outside_tagged_source
    }
    outside_sunset_capture_ids = {
        row["capture_identity"] for row in outside_sunset_source
    }
    outside_tagged_products = [
        row for row in rows if row["capture_identity"] in outside_tagged_capture_ids
    ]
    outside_sunset_products = [
        row for row in rows if row["capture_identity"] in outside_sunset_capture_ids
    ]
    outside_tagged_bytes = sum(
        int(row["archive_size_bytes"]) for row in outside_tagged_products
    )
    outside_sunset_bytes = sum(
        int(row["archive_size_bytes"]) for row in outside_sunset_products
    )
    sunset_in_attribution_activity = sum(
        row["target_id"] == TARGET and row["activity_id"] == attribution_activity
        for row in source_rows
    )

    tag_values = sorted({row["target_id"] for row in tagged_source})
    capture_tags = {row["capture_identity"]: row["target_id"] for row in tagged_source}
    fractional_action_weights = {tag: 0.0 for tag in tag_values}
    raw_action_memberships = 0
    for tags in action_tags.values():
        if not tags:
            continue
        raw_action_memberships += len(tags)
        for tag in tags:
            fractional_action_weights[tag] += 1.0 / len(tags)
    exposure_weights = {
        tag: float(sum(row["target_id"] == tag for row in tagged_source))
        for tag in tag_values
    }
    product_weights = {
        tag: float(sum(capture_tags.get(row["capture_identity"]) == tag for row in rows))
        for tag in tag_values
    }
    byte_weights = {
        tag: float(sum(
            int(row["archive_size_bytes"])
            for row in rows
            if capture_tags.get(row["capture_identity"]) == tag
        ))
        for tag in tag_values
    }

    def rank_of_target(weights: dict[str, float]) -> int:
        ordered = sorted(weights, key=lambda tag: (-weights[tag], tag))
        return ordered.index(TARGET) + 1

    sunset_partial_presence_actions = sum(
        any(not row["target_id"] for row in action_source_rows[action_id])
        for action_id in sunset_actions
    )
    total_bytes = sum(int(row["archive_size_bytes"]) for row in rows)
    selection_all_share = ratio(len(sunset_source), len(source_rows))
    selection_tagged_share = strict_exposure_share

    return {
        "all_cohort": {
            "actions": len(action_source_rows),
            "source_exposures": len(source_rows),
            "products": len(rows),
            "archive_size_bytes": total_bytes,
        },
        "selection_panel": {
            "tagged_source_exposures": len(tagged_source),
            "blank_source_exposures": len(source_rows) - len(tagged_source),
            "sunset_tagged_source_exposures": len(sunset_source),
            "sunset_tag_occupancy_all_source_exposures": selection_all_share,
            "sunset_share_of_tagged_source_exposures": selection_tagged_share,
            "nonblank_conditioning_amplification": ratio(selection_tagged_share, selection_all_share),
        },
        "strict_tagged_weighting_panel": {
            "selected_actions": len(selected_actions),
            "sunset_tagged_actions": len(sunset_actions),
            "sunset_share_of_selected_actions": strict_action_share,
            "tagged_exposures": len(tagged_source),
            "sunset_tagged_exposures": len(sunset_source),
            "sunset_share_of_tagged_exposures": strict_exposure_share,
            "tagged_products": len(tagged_products),
            "sunset_tagged_products": len(sunset_products),
            "sunset_share_of_tagged_products": strict_product_share,
            "tagged_archive_size_bytes": tagged_bytes,
            "sunset_tagged_archive_size_bytes": sunset_bytes,
            "sunset_share_of_tagged_bytes": strict_byte_share,
            "action_to_exposure_amplification": ratio(strict_exposure_share, strict_action_share),
            "exposure_to_byte_amplification": ratio(strict_byte_share, strict_exposure_share),
            "action_to_byte_amplification": ratio(strict_byte_share, strict_action_share),
            "representations_per_exposure": ratio(len(tagged_products), len(tagged_source)),
        },
        "action_carried_sensitivity": {
            "selected_action_exposures": selected_action_exposures,
            "sunset_action_exposures": sunset_action_exposures,
            "sunset_share_of_selected_action_exposures": ratio(
                sunset_action_exposures, selected_action_exposures
            ),
            "selected_action_products": len(selected_action_products),
            "sunset_action_products": len(sunset_action_products),
            "sunset_share_of_selected_action_products": ratio(
                len(sunset_action_products), len(selected_action_products)
            ),
            "selected_action_archive_size_bytes": selected_action_bytes,
            "sunset_action_archive_size_bytes": sunset_action_bytes,
            "sunset_share_of_selected_action_bytes": ratio(
                sunset_action_bytes, selected_action_bytes
            ),
        },
        "collection_byte_sensitivity": collection_byte_sensitivity,
        "activity_structure_attribution": {
            "activity_id": attribution_activity,
            "sunset_tagged_exposures_in_activity": sunset_in_attribution_activity,
            "sunset_tagged_exposures_all": len(sunset_source),
            "share_of_sunset_tagged_exposures_from_activity": ratio(
                sunset_in_attribution_activity, len(sunset_source)
            ),
            "outside_activity": {
                "selected_actions": len(outside_selected_actions),
                "sunset_tagged_actions": len(outside_sunset_actions),
                "sunset_share_of_selected_actions": ratio(
                    len(outside_sunset_actions), len(outside_selected_actions)
                ),
                "tagged_exposures": len(outside_tagged_source),
                "sunset_tagged_exposures": len(outside_sunset_source),
                "sunset_share_of_tagged_exposures": ratio(
                    len(outside_sunset_source), len(outside_tagged_source)
                ),
                "tagged_archive_size_bytes": outside_tagged_bytes,
                "sunset_tagged_archive_size_bytes": outside_sunset_bytes,
                "sunset_share_of_tagged_bytes": ratio(
                    outside_sunset_bytes, outside_tagged_bytes
                ),
            },
        },
        "all_tag_countercheck": {
            "target_tag_values": len(tag_values),
            "raw_action_tag_memberships": raw_action_memberships,
            "fractional_action_weight_total": sum(fractional_action_weights.values()),
            "multi_target_actions": sum(len(tags) > 1 for tags in action_tags.values()),
            "concentration_equivalent_target_tag_values": {
                "fractional_actions": concentration_equivalent(list(fractional_action_weights.values())),
                "exposures": concentration_equivalent(list(exposure_weights.values())),
                "products": concentration_equivalent(list(product_weights.values())),
                "archive_size_bytes": concentration_equivalent(list(byte_weights.values())),
            },
            "sunset_rank": {
                "fractional_actions": rank_of_target(fractional_action_weights),
                "exposures": rank_of_target(exposure_weights),
                "products": rank_of_target(product_weights),
                "archive_size_bytes": rank_of_target(byte_weights),
            },
        },
        "structure_checks": {
            "sunset_multitarget_actions": sum(
                TARGET in action_tags[action_id] and len(action_tags[action_id]) > 1
                for action_id in sunset_actions
            ),
            "sunset_partial_presence_actions": sunset_partial_presence_actions,
            "tagged_bytes_share_of_all_bytes": ratio(tagged_bytes, total_bytes),
            "sunset_tagged_bytes_share_of_all_bytes": ratio(sunset_bytes, total_bytes),
        },
    }


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "blank_tags_are_negative_examples": False,
        "tag_share_is_physical_prevalence": False,
        "bytes_are_scientific_value": False,
        "actual_pipeline_used_cascade": False,
        "observed_model_bias": False,
        "model_performance_effect": False,
        "products_are_independent_examples": False,
        "action_carried_tags_are_ground_truth": False,
        "concentration_is_effective_class_count": False,
        "every_representation_layer_has_byte_majority": False,
        "cascade_is_activity_invariant": False,
        "share_labels": "population_and_unit_declared",
        "scope": "frozen_stage10o_complete_action_cohort",
        "novelty_or_priority": False,
        "pixel_payload_bytes": 0,
    }
    if mutation is None:
        return mutated
    mapping = {
        "call_blank_tags_negative_examples": ("blank_tags_are_negative_examples", True),
        "call_tag_share_physical_prevalence": ("tag_share_is_physical_prevalence", True),
        "call_bytes_scientific_value": ("bytes_are_scientific_value", True),
        "claim_actual_pipeline_used_cascade": ("actual_pipeline_used_cascade", True),
        "claim_observed_model_bias": ("observed_model_bias", True),
        "claim_model_performance_effect": ("model_performance_effect", True),
        "call_products_independent_examples": ("products_are_independent_examples", True),
        "call_action_carried_tags_ground_truth": ("action_carried_tags_are_ground_truth", True),
        "call_concentration_effective_class_count": ("concentration_is_effective_class_count", True),
        "call_every_representation_layer_byte_majority": ("every_representation_layer_has_byte_majority", True),
        "call_cascade_activity_invariant": ("cascade_is_activity_invariant", True),
        "omit_population_or_unit_labels": ("share_labels", "ambiguous"),
        "generalize_beyond_frozen_cohort": ("scope", "all_artemis_or_lunar_observations"),
        "claim_novelty_or_priority": ("novelty_or_priority", True),
        "open_pixels": ("pixel_payload_bytes", 1),
    }
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    key, value = mapping[mutation]
    mutated["mutation_state"][key] = value
    return mutated


def values_match(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and values_match(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, float):
        return math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=1e-12)
    return actual == expected


def prepare_verification(
    root: Path, spec: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    identity = source_identity(root, spec["sources"][0])
    prior = verify_stage10w(root)
    rows = read_csv(root / spec["sources"][0]["path"])
    return identity, prior, derive(rows)


def verify_stage11u(
    root: Path,
    mutation: str | None = None,
    prepared: tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec/stage11u.json"), mutation)
    identity, prior, metrics = prepared or prepare_verification(root, spec)
    state = spec["mutation_state"]

    strict = metrics["strict_tagged_weighting_panel"]
    sensitivity = metrics["action_carried_sensitivity"]
    collection_sensitivity = metrics["collection_byte_sensitivity"]
    activity_attribution = metrics["activity_structure_attribution"]
    countercheck = metrics["all_tag_countercheck"]
    arithmetic = (
        math.isclose(
            strict["sunset_share_of_tagged_exposures"],
            strict["sunset_share_of_tagged_products"],
            rel_tol=0.0,
            abs_tol=1e-15,
        )
        and strict["representations_per_exposure"] == 3.0
        and strict["sunset_share_of_tagged_bytes"] > 0.5
        and sensitivity["sunset_share_of_selected_action_bytes"] > 0.5
        and collection_sensitivity["data_source"]["sunset_share"] < 0.5
        and collection_sensitivity["data_raw"]["sunset_share"] > 0.5
        and collection_sensitivity["data_processed"]["sunset_share"] > 0.5
        and activity_attribution["outside_activity"]["sunset_share_of_tagged_exposures"] < 0.5
        and activity_attribution["outside_activity"]["sunset_share_of_tagged_bytes"] < 0.5
        and countercheck["concentration_equivalent_target_tag_values"]["fractional_actions"]
        > countercheck["concentration_equivalent_target_tag_values"]["exposures"]
        > countercheck["concentration_equivalent_target_tag_values"]["archive_size_bytes"]
    )
    prohibited = {
        key: state[key]
        for key in (
            "blank_tags_are_negative_examples",
            "tag_share_is_physical_prevalence",
            "bytes_are_scientific_value",
            "actual_pipeline_used_cascade",
            "observed_model_bias",
            "model_performance_effect",
            "products_are_independent_examples",
            "action_carried_tags_are_ground_truth",
            "concentration_is_effective_class_count",
            "every_representation_layer_has_byte_majority",
            "cascade_is_activity_invariant",
            "novelty_or_priority",
        )
    }
    checks = {
        "source_identity": identity["match"],
        "stage10w_replays": prior["pass"],
        "frozen_observables": values_match(metrics, spec["frozen_observables"]),
        "arithmetic_identities": arithmetic,
        "claim_boundaries": not any(prohibited.values()),
        "population_and_unit_labels": state["share_labels"] == "population_and_unit_declared",
        "scope_boundary": state["scope"] == "frozen_stage10o_complete_action_cohort",
        "zero_pixel_access": state["pixel_payload_bytes"] == 0,
    }
    passed = all(checks.values())
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": (
            "VERIFIED_SELECTION_WEIGHTING_CASCADE"
            if passed
            else "REJECTED_SELECTION_WEIGHTING_CASCADE"
        ),
        "checks": checks,
        "source_identity": identity,
        "metrics": metrics,
        "finding": (
            "In the frozen cohort, conditioning source-exposure rows on nonblank target tags "
            "raises Sunset's descriptive tag share from 20.418% to 45.502%. Inside the selected "
            "tagged subset, Sunset is 33.989% of actions, 45.502% of exposures and products, and "
            "52.413% of bytes. An action-carried sensitivity remains a 51.495% byte share."
        ),
        "prohibited_claims": prohibited,
        "pixel_payload_bytes_opened": state["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"],
        "verification_receipt": spec["verification_receipt"],
        "next_step_logic": spec["next_step_logic"],
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec/stage11u.json")
    prepared = prepare_verification(root, spec)
    baseline = verify_stage11u(root, prepared=prepared)
    hard_negatives = {
        name: verify_stage11u(root, name, prepared=prepared)
        for name in spec["hard_negatives"]
    }
    hard_negatives_pass = all(not result["pass"] for result in hard_negatives.values())
    return {
        **baseline,
        "hard_negatives": hard_negatives,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
    }


def render_markdown(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    selection = metrics["selection_panel"]
    strict = metrics["strict_tagged_weighting_panel"]
    sensitivity = metrics["action_carried_sensitivity"]
    collection_sensitivity = metrics["collection_byte_sensitivity"]
    activity_attribution = metrics["activity_structure_attribution"]
    countercheck = metrics["all_tag_countercheck"]
    concentration = countercheck["concentration_equivalent_target_tag_values"]
    return f"""# Stage 11U: Selection and Weighting Cascade

- Verification: `{'PASS' if result['pass'] else 'FAIL'}`
- Evidence state: `{result['evidence_state']}`
- Frozen cohort: `{metrics['all_cohort']['actions']:,}` actions, `{metrics['all_cohort']['source_exposures']:,}` source exposures, `{metrics['all_cohort']['products']:,}` products
- Pixel payload bytes opened: `{result['pixel_payload_bytes_opened']}`

## Panel A: selection conditioning

| Declared population and unit | Sunset rows | Denominator | Sunset share |
| --- | ---: | ---: | ---: |
| All source-exposure target fields | {selection['sunset_tagged_source_exposures']:,} | {metrics['all_cohort']['source_exposures']:,} | {selection['sunset_tag_occupancy_all_source_exposures']:.3%} |
| Nonblank source-exposure target fields | {selection['sunset_tagged_source_exposures']:,} | {selection['tagged_source_exposures']:,} | {selection['sunset_share_of_tagged_source_exposures']:.3%} |

Conditioning on a nonblank target field changes this descriptive share by `{selection['nonblank_conditioning_amplification']:.3f}x`. Blank fields remain unknown, not negative examples.

## Panel B: unit weighting inside the tagged subset

| Declared unit | Sunset | Selected/tagged denominator | Sunset share |
| --- | ---: | ---: | ---: |
| Actions with any nonblank tag | {strict['sunset_tagged_actions']:,} | {strict['selected_actions']:,} | {strict['sunset_share_of_selected_actions']:.3%} |
| Nonblank-tagged source exposures | {strict['sunset_tagged_exposures']:,} | {strict['tagged_exposures']:,} | {strict['sunset_share_of_tagged_exposures']:.3%} |
| Products derived from those exposures | {strict['sunset_tagged_products']:,} | {strict['tagged_products']:,} | {strict['sunset_share_of_tagged_products']:.3%} |
| Bytes attached to those products | {strict['sunset_tagged_archive_size_bytes']:,} | {strict['tagged_archive_size_bytes']:,} | {strict['sunset_share_of_tagged_bytes']:.3%} |

The action-to-byte change is `{strict['action_to_byte_amplification']:.3f}x`. The exposure and product shares are identical because every admitted exposure has exactly three representations; the extra products do not create new independent observations.

## Action-carried sensitivity

If each selected action's nonblank tag membership is conservatively carried across that action's blank exposures, Sunset remains `{sensitivity['sunset_share_of_selected_action_bytes']:.3%}` of the selected byte mass. This sensitivity does not make carried tags ground truth.

The overall byte majority is representation-sensitive: Sunset is `{collection_sensitivity['data_source']['sunset_share']:.3%}` of tagged source-representation bytes, `{collection_sensitivity['data_raw']['sunset_share']:.3%}` of tagged raw-representation bytes, and `{collection_sensitivity['data_processed']['sunset_share']:.3%}` of tagged processed-representation bytes.

The cascade is also activity-conditioned. `{activity_attribution['activity_id']}` supplies `{activity_attribution['sunset_tagged_exposures_in_activity']:,}` of the `{activity_attribution['sunset_tagged_exposures_all']:,}` Sunset-tagged exposures. Outside that activity, Sunset is `{activity_attribution['outside_activity']['sunset_share_of_tagged_exposures']:.3%}` of tagged exposures and `{activity_attribution['outside_activity']['sunset_share_of_tagged_bytes']:.3%}` of tagged bytes. This attribution check is not a substitute target population.

## All-tag countercheck

Across all `{countercheck['target_tag_values']}` nonblank target-tag values, the concentration equivalent is `{concentration['fractional_actions']:.3f}` tag values under fractional action weighting, `{concentration['exposures']:.3f}` under exposure or product weighting, and `{concentration['archive_size_bytes']:.3f}` under byte weighting. Sunset ranks first under every declared unit. The concentration equivalent is a descriptive index, not an effective number of physical classes.

## Finding

{result['finding']}

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
    result = verify_with_mutations(root) if args.command == "verify" else verify_stage11u(root, args.mutation)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
