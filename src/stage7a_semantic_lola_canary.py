#!/usr/bin/env python3
"""Verify and evaluate the frozen Stage 7A semantic-to-LOLA canary offline."""

from __future__ import annotations

import argparse
import bisect
import copy
import csv
import json
import math
import statistics
import struct
import sys
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


def pixel_latitude(line_index: int, contract: dict[str, Any]) -> float:
    return (
        contract["line_projection_offset_pixels"] - line_index
    ) / contract["map_resolution_pixels_per_degree"]


def pixel_longitude(sample_index: int, contract: dict[str, Any]) -> float:
    return (
        (sample_index - contract["sample_projection_offset_pixels"])
        / contract["map_resolution_pixels_per_degree"]
        + contract["center_longitude_deg"]
    ) % 360.0


def great_circle_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
    radius_km: float,
) -> float:
    lat_a = math.radians(latitude_a)
    lat_b = math.radians(latitude_b)
    delta_lat = lat_b - lat_a
    delta_lon = math.radians(((longitude_b - longitude_a + 180.0) % 360.0) - 180.0)
    haversine = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2.0) ** 2
    )
    return radius_km * 2.0 * math.asin(min(1.0, math.sqrt(haversine)))


def probability_superiority(higher: list[float], lower: list[float]) -> float:
    """Return P(higher > lower) + 0.5 P(equal) without assuming independence."""
    ordered = sorted(lower)
    wins = 0.0
    for value in higher:
        left = bisect.bisect_left(ordered, value)
        right = bisect.bisect_right(ordered, value)
        wins += left + 0.5 * (right - left)
    return wins / (len(higher) * len(lower))


def transcript_anchors_present(root: Path, semantic: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    primary = semantic["primary_observation"]
    transcript_path = root / primary["transcript_path"]
    if sha256_file(transcript_path) != primary["transcript_sha256"]:
        errors.append("Primary transcript identity changed")
        return False, errors
    with transcript_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [
        row
        for row in rows
        if primary["utc_start"] <= row["utc"] <= primary["utc_end"]
        and row["speaker"].strip() == primary["speaker"]
    ]
    joined = " ".join(row["text"] for row in selected).lower()
    for anchor in primary["decision_text_anchors"]:
        if anchor.lower() not in joined:
            errors.append(f"Missing primary transcript anchor: {anchor}")
    for support in semantic["supporting_observations"]:
        path = root / support["transcript_path"]
        if sha256_file(path) != support["transcript_sha256"]:
            errors.append(f"Supporting transcript identity changed: {support['transcript_path']}")
    return not errors, errors


def strip_values_by_region(
    strip_path: Path,
    line_start: int,
    line_end: int,
    contract: dict[str, Any],
    centers: dict[str, dict[str, Any]],
    radii_km: list[int],
) -> dict[str, dict[int, list[float]]]:
    raw_bytes = strip_path.read_bytes()
    expected_bytes = (line_end - line_start + 1) * contract["physical_row_bytes"]
    if len(raw_bytes) != expected_bytes:
        raise ValueError(
            f"Strip {strip_path} contains {len(raw_bytes)} bytes; expected {expected_bytes}"
        )
    raw_values = [value[0] for value in struct.iter_unpack("<h", raw_bytes)]
    expected_samples = (line_end - line_start + 1) * contract["line_samples"]
    if len(raw_values) != expected_samples:
        raise ValueError("Strip sample count does not match its declared row geometry")

    output = {
        name: {radius: [] for radius in radii_km}
        for name in centers
    }
    width = contract["line_samples"]
    for local_line, global_line in enumerate(range(line_start, line_end + 1)):
        latitude = pixel_latitude(global_line, contract)
        row_offset = local_line * width
        for sample_index in range(width):
            raw_value = raw_values[row_offset + sample_index]
            if raw_value <= contract["invalid_raw_at_or_below"]:
                continue
            longitude = pixel_longitude(sample_index, contract)
            slope_deg = raw_value * contract["scaling_factor"] + contract["offset_deg"]
            if slope_deg < 0:
                continue
            for name, center in centers.items():
                distance = great_circle_km(
                    latitude,
                    longitude,
                    center["latitude_deg"],
                    center["longitude_east_deg"],
                    contract["moon_radius_km"],
                )
                for radius in radii_km:
                    if distance <= radius:
                        output[name][radius].append(slope_deg)
    return output


def apply_mutation(
    spec: dict[str, Any], semantic: dict[str, Any], mutation: str | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = copy.deepcopy(spec)
    semantic = copy.deepcopy(semantic)
    if mutation is None:
        return spec, semantic
    if mutation == "use_orientale_as_evaluation_data":
        semantic["feature_coordinates"]["orientale"] = {
            "latitude_deg": -19.4,
            "longitude_east_deg": 265.0,
            "diameter_km": 930.0,
        }
    elif mutation == "change_semantic_direction_after_lola_access":
        semantic["primary_observation"]["coded_contrast"] = {
            "vavilov": "smoother",
            "hertzsprung": "rougher",
        }
    elif mutation == "compare_unequal_physical_radii":
        spec["regions"]["rule"] = "Use a 20 km Vavilov disk and a 30 km Hertzsprung disk."
    elif mutation == "accept_only_one_lola_baseline":
        spec["source_products"] = spec["source_products"][:1]
    elif mutation == "accept_a_ratio_below_the_frozen_threshold":
        spec["oracle"]["primary"]["minimum_vavilov_to_hertzsprung_median_ratio_each"] = 0.9
    elif mutation == "treat_interpolated_pixels_as_independent_samples":
        spec["claim_ceiling"] = "Raster pixels are independent scientific samples."
    elif mutation == "claim_control_for_geology_illumination_albedo_or_morphology":
        spec["claim_ceiling"] = "The canary controls geology, illumination, albedo, and morphology."
    elif mutation == "claim_novel_science_from_a_two-target_same-observer_canary":
        spec["claim_ceiling"] = "This is a novel publishable scientific result."
    elif mutation == "claim_sub_resolution_perception":
        spec["claim_ceiling"] = "This proves sub-resolution human perception."
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec, semantic


def add_check(
    checks: list[dict[str, Any]],
    errors: list[str],
    check_id: str,
    passed: bool,
    *,
    error: str,
    **details: Any,
) -> None:
    checks.append({"id": check_id, "pass": passed, **details})
    if not passed:
        errors.append(error)


def verify_stage7a(root: Path, mutation: str | None = None) -> dict[str, Any]:
    raw_spec = load_json(root / "spec" / "stage7a.json")
    raw_semantic = load_json(root / raw_spec["semantic_evidence"]["path"])
    spec, semantic = apply_mutation(raw_spec, raw_semantic, mutation)
    receipt = load_json(root / "evidence" / "stage7a" / "acquisition-receipt.json")
    manifest = load_json(root / "evidence" / "stage7a" / "source-manifest.json")
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    actual_semantic_hash = sha256_file(root / raw_spec["semantic_evidence"]["path"])
    semantic_identity_ok = (
        actual_semantic_hash == raw_spec["semantic_evidence"]["sha256"]
        and semantic.get("frozen_before_lola_value_access") is True
        and receipt["semantic_sha256"] == actual_semantic_hash
        and receipt["semantic_frozen_before_lola_value_access"] is True
    )
    add_check(
        checks,
        errors,
        "semantic_freeze_and_identity",
        semantic_identity_ok,
        error="Semantic evidence was not frozen and hash-bound before LOLA access.",
        actual_sha256=actual_semantic_hash,
        expected_sha256=raw_spec["semantic_evidence"]["sha256"],
    )

    anchors_ok, anchor_errors = transcript_anchors_present(root, semantic)
    add_check(
        checks,
        errors,
        "transcript_anchors",
        anchors_ok,
        error="; ".join(anchor_errors) or "Transcript anchors are incomplete.",
    )

    feature_records = {
        name: item
        for name, item in semantic["feature_coordinates"].items()
        if isinstance(item, dict) and "latitude_deg" in item
    }
    expected_features = {"vavilov", "hertzsprung"}
    contrast = semantic["primary_observation"]["coded_contrast"]
    held_out_ok = (
        set(feature_records) == expected_features
        and contrast == {"vavilov": "rougher", "hertzsprung": "smoother"}
        and all("orientale" not in name.lower() for name in feature_records)
        and "Orientale observations" in semantic["excluded_from_evaluation"]
    )
    add_check(
        checks,
        errors,
        "held_out_non_orientale_contrast",
        held_out_ok,
        error="The held-out Vavilov-versus-Hertzsprung semantic contrast changed or includes Orientale.",
        features=sorted(feature_records),
        contrast=contrast,
    )

    products = {(item["id"], item["baseline_m"]) for item in spec["source_products"]}
    product_contract_ok = products == {
        ("mas_57m_16", 57),
        ("mas_225m_16", 225),
        ("mas_560m_16", 560),
    }
    add_check(
        checks,
        errors,
        "three_scale_product_contract",
        product_contract_ok,
        error="The canary must retain all three frozen LOLA baselines.",
        products=sorted(products),
    )

    regions = spec["regions"]
    equal_regions_ok = (
        regions["primary_radius_km"] == 20
        and regions["robustness_radii_km"] == [10, 20, 30]
        and "identical physical radii" in regions["rule"].lower()
    )
    add_check(
        checks,
        errors,
        "equal_physical_regions",
        equal_regions_ok,
        error="The two targets no longer use identical frozen physical radii.",
        regions=regions,
    )

    primary_oracle = spec["oracle"]["primary"]
    oracle_ok = (
        primary_oracle["radius_km"] == 20
        and primary_oracle["required_baselines_m"] == [57, 225, 560]
        and primary_oracle["minimum_vavilov_to_hertzsprung_median_ratio_each"] == 1.2
        and primary_oracle["minimum_probability_superiority_each"] == 0.65
        and spec["oracle"]["robustness"]["minimum_comparisons_with_ratio_at_least_1_1"] == 8
    )
    add_check(
        checks,
        errors,
        "frozen_oracle",
        oracle_ok,
        error="The predeclared signal thresholds changed.",
        oracle=spec["oracle"],
    )

    claim_ceiling = spec["claim_ceiling"].lower()
    ceiling_ok = all(
        phrase in claim_ceiling
        for phrase in (
            "does not establish causation",
            "perception below resolution",
            "independence from geology or morphology",
            "statistical significance",
            "publishable scientific result",
        )
    )
    add_check(
        checks,
        errors,
        "claim_ceiling",
        ceiling_ok,
        error="The canary's scientific claim ceiling was weakened.",
        claim_ceiling=spec["claim_ceiling"],
    )

    receipt_ok = (
        receipt["status"] == "COMPLETED"
        and receipt["spec_sha256"] == sha256_file(root / "spec" / "stage7a.json")
        and receipt["network_bytes"] <= receipt["network_budget_bytes"]
        and receipt["img_bytes"] <= spec["acquisition"]["maximum_total_img_bytes"]
        and receipt["label_bytes"] <= spec["acquisition"]["maximum_total_label_bytes"]
    )
    add_check(
        checks,
        errors,
        "bounded_acquisition_receipt",
        receipt_ok,
        error="The acquisition receipt is incomplete, stale, or over budget.",
        network_bytes=receipt["network_bytes"],
        network_budget_bytes=receipt["network_budget_bytes"],
    )

    manifest_by_product: dict[str, dict[str, Any]] = {}
    files_ok = True
    for file_record in manifest["files"]:
        path = root / file_record["path"]
        if not path.is_file() or path.stat().st_size != file_record["bytes"] or sha256_file(path) != file_record["sha256"]:
            files_ok = False
        manifest_by_product.setdefault(file_record["product_id"], {})[
            file_record["kind"]
        ] = file_record
    files_ok = files_ok and set(manifest_by_product) == {
        "mas_57m_16",
        "mas_225m_16",
        "mas_560m_16",
    }
    add_check(
        checks,
        errors,
        "source_manifest_identity",
        files_ok,
        error="A bounded LOLA source file is missing or has changed.",
    )

    metrics: dict[str, Any] = {}
    if not errors:
        line_start, line_end = receipt["line_range_zero_based_inclusive"]
        radii = regions["robustness_radii_km"]
        product_by_id = {item["id"]: item for item in spec["source_products"]}
        for product_id, records in sorted(manifest_by_product.items(), key=lambda item: product_by_id[item[0]]["baseline_m"]):
            baseline_m = product_by_id[product_id]["baseline_m"]
            values = strip_values_by_region(
                root / records["latitude_strip"]["path"],
                line_start,
                line_end,
                spec["raster_contract"],
                feature_records,
                radii,
            )
            baseline_metrics: dict[str, Any] = {}
            for radius in radii:
                vavilov = values["vavilov"][radius]
                hertzsprung = values["hertzsprung"][radius]
                if not vavilov or not hertzsprung:
                    raise ValueError(f"No valid pixels for {baseline_m} m at {radius} km")
                v_median = statistics.median(vavilov)
                h_median = statistics.median(hertzsprung)
                ratio = v_median / h_median if h_median > 0 else math.inf
                baseline_metrics[str(radius)] = {
                    "vavilov_pixel_count": len(vavilov),
                    "hertzsprung_pixel_count": len(hertzsprung),
                    "vavilov_median_slope_deg": v_median,
                    "hertzsprung_median_slope_deg": h_median,
                    "median_difference_deg": v_median - h_median,
                    "median_ratio": ratio,
                    "probability_superiority_descriptive_only": probability_superiority(
                        vavilov, hertzsprung
                    ),
                }
            metrics[str(baseline_m)] = baseline_metrics

    primary_signal_pass = False
    robustness_count = 0
    if metrics:
        primary_signal_pass = all(
            metrics[str(baseline)]["20"]["median_ratio"]
            >= primary_oracle["minimum_vavilov_to_hertzsprung_median_ratio_each"]
            and metrics[str(baseline)]["20"]["probability_superiority_descriptive_only"]
            >= primary_oracle["minimum_probability_superiority_each"]
            for baseline in primary_oracle["required_baselines_m"]
        )
        robustness_count = sum(
            metrics[str(baseline)][str(radius)]["median_ratio"] >= 1.1
            for baseline in primary_oracle["required_baselines_m"]
            for radius in regions["robustness_radii_km"]
        )
    robustness_pass = (
        robustness_count
        >= spec["oracle"]["robustness"]["minimum_comparisons_with_ratio_at_least_1_1"]
    )
    signal_pass = primary_signal_pass and robustness_pass
    mechanics_pass = not errors
    evidence_state = (
        spec["oracle"]["pass_state"]
        if mechanics_pass and signal_pass
        else spec["oracle"]["fail_state"]
        if mechanics_pass
        else spec["oracle"]["indeterminate_state"]
    )
    disposition = (
        "CONTINUE_CONTROLLED_MULTI_TARGET"
        if evidence_state == spec["oracle"]["pass_state"]
        else "STOP_SEMANTIC_ROUGHNESS_LANE"
        if evidence_state == spec["oracle"]["fail_state"]
        else "STOP_REPAIR_NAMED_BOUNDARY_ONLY"
    )
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": mechanics_pass,
        "signal_pass": signal_pass,
        "evidence_state": evidence_state,
        "disposition": disposition,
        "semantic_prediction": "Vavilov rougher than Hertzsprung",
        "acquisition_network_bytes": receipt["network_bytes"],
        "network_bytes_in_verification": 0,
        "primary_signal_pass": primary_signal_pass,
        "robustness_pass": robustness_pass,
        "robustness_comparisons_passing": robustness_count,
        "robustness_comparisons_total": 9,
        "metrics": metrics,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage7a(root)
    mutation_names = load_json(root / "spec" / "stage7a.json")["hard_negatives"]
    mutations = {name: verify_stage7a(root, name) for name in mutation_names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 7A hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 7A — Held-Out Semantic-to-LOLA Canary",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Signal state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Frozen prediction: `{result['semantic_prediction']}`",
        f"- Acquisition bytes: `{result['acquisition_network_bytes']}`",
        f"- Scored verification network bytes: `{result['network_bytes_in_verification']}`",
        "",
        "## Result",
        "",
    ]
    if result["evidence_state"] == "COARSE_SEMANTIC_LOLA_CONCORDANCE":
        lines.append(
            "The pre-instrument transcript direction survived the frozen canary: equal-size regions centered on Vavilov are rougher in the LOLA products than equal-size regions centered on Hertzsprung at all required baselines, with the required robustness across radii."
        )
    elif result["evidence_state"] == "NO_STRONG_DIRECTIONAL_CONCORDANCE":
        lines.append(
            "The pre-instrument transcript direction did not meet the frozen strength and robustness thresholds. The semantic roughness lane stops here."
        )
    else:
        lines.append(
            "The canary could not be interpreted because a source, identity, or localization boundary failed."
        )
    lines.extend(
        [
            "",
            "| LOLA baseline | Radius | Vavilov median slope | Hertzsprung median slope | Ratio | Descriptive superiority |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for baseline, radii in result["metrics"].items():
        for radius, metric in radii.items():
            lines.append(
                f"| {baseline} m | {radius} km | {metric['vavilov_median_slope_deg']:.4f}° | {metric['hertzsprung_median_slope_deg']:.4f}° | {metric['median_ratio']:.3f} | {metric['probability_superiority_descriptive_only']:.3f} |"
            )
    lines.extend(
        [
            "",
            f"Primary thresholds: `{'PASS' if result['primary_signal_pass'] else 'FAIL'}`. Robustness: `{result['robustness_comparisons_passing']}/{result['robustness_comparisons_total']}` comparisons reached the frozen 1.10 ratio threshold.",
            "",
            "The superiority value is descriptive only. LOLA values are interpolated from overlapping windows and are not treated as independent observations; no p-value is claimed.",
            "",
            "## Scientific ceiling",
            "",
            result["claim_ceiling"],
            "",
            "The comparison uses one observer, two morphologically different craters, coarse center-disk localization, and no independent control for crater age, geology, illumination, albedo, or exact optical tool. Even a strong match cannot distinguish a subtle human sensing mechanism from obvious regional morphology.",
            "",
            "## Next-step logic",
            "",
            f"- If passed: {result['next_step_logic']['if_pass']}",
            f"- If failed: {result['next_step_logic']['if_fail']}",
            f"- If indeterminate: {result['next_step_logic']['if_indeterminate']}",
            "",
            "## Hard negatives",
            "",
        ]
    )
    for name, mutation_result in result.get("hard_negatives", {}).items():
        verdict = "REJECTED" if not mutation_result["pass"] else "UNEXPECTEDLY ACCEPTED"
        lines.append(f"- `{name}`: {verdict}")
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
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        result = verify_with_mutations(args.root.resolve())
    else:
        result = verify_stage7a(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(
            render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
