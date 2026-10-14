#!/usr/bin/env python3
"""Form and later verify the frozen Stage 8A Glushko/Ohm reflectance canary."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import statistics
import struct
import sys
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file


def load_payload(path: Path) -> Any:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def frozen_design_sha256(spec: dict[str, Any]) -> str:
    fields = (
        "question",
        "baseline",
        "treatment",
        "semantic_evidence",
        "geometry",
        "endpoint",
        "oracle",
        "hard_negatives",
        "claim_ceiling",
        "next_step_logic",
    )
    payload = {field: spec[field] for field in fields}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def initial_bearing_deg(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Return the initial great-circle bearing clockwise from north."""
    lat_a = math.radians(latitude_a)
    lat_b = math.radians(latitude_b)
    delta_lon = math.radians(((longitude_b - longitude_a + 180.0) % 360.0) - 180.0)
    y = math.sin(delta_lon) * math.cos(lat_b)
    x = (
        math.cos(lat_a) * math.sin(lat_b)
        - math.sin(lat_a) * math.cos(lat_b) * math.cos(delta_lon)
    )
    return math.degrees(math.atan2(y, x)) % 360.0


def angular_difference_deg(angle: float, center: float) -> float:
    """Return the signed shortest angular difference in [-180, 180)."""
    return ((angle - center + 180.0) % 360.0) - 180.0


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


def transcript_anchors_present(root: Path, record: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    path = root / record["transcript_path"]
    if sha256_file(path) != record["transcript_sha256"]:
        return False, [f"Transcript identity changed: {record['transcript_path']}"]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = {line_number: row for line_number, row in enumerate(csv.DictReader(handle), 2)}
    missing_rows = [line_number for line_number in record["rows"] if line_number not in rows]
    if missing_rows:
        errors.append(f"Missing frozen transcript rows: {missing_rows}")
    selected = [rows[line_number] for line_number in record["rows"] if line_number in rows]
    joined = " ".join(row["text"] for row in selected).lower()
    for anchor in record["decision_text_anchors"]:
        if anchor.lower() not in joined:
            errors.append(f"Missing transcript anchor: {anchor}")
    if any(row["speaker"].strip() != record["speaker"] for row in selected):
        errors.append(f"A frozen transcript row is not attributed to {record['speaker']}")
    return not errors, errors


def target_records_present(root: Path, semantic: dict[str, Any]) -> tuple[bool, list[str]]:
    source = semantic["coordinate_source"]
    path = root / source["path"]
    errors: list[str] = []
    if sha256_file(path) != source["sha256"]:
        return False, ["The outgoing target-request identity changed"]
    payload = load_payload(path)
    if not isinstance(payload, list):
        return False, ["The outgoing target-request payload is not a list"]
    available = [item.get("target_properties", {}) for item in payload]
    for key, expected in source["records"].items():
        matches = [
            item
            for item in available
            if item.get("target_name") == expected["target_name"]
            and float(item.get("latitude")) == expected["latitude_deg"]
            and float(item.get("longitude")) == expected["longitude_east_deg"]
            and (
                "diameter_km" not in expected
                or float(item.get("diameter")) == expected["diameter_km"]
            )
        ]
        if not matches:
            errors.append(f"Official coordinate record changed or is absent: {key}")
    return not errors, errors


def apply_formation_mutation(
    spec: dict[str, Any], semantic: dict[str, Any], mutation: str | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = copy.deepcopy(spec)
    semantic = copy.deepcopy(semantic)
    if mutation is None:
        return spec, semantic
    if mutation == "access_wac_values_before_semantic_freeze":
        semantic["wac_value_bytes_accessed_before_freeze"] = 1
    elif mutation == "trace_ray_sectors_from_brightness_pixels":
        spec["geometry"]["axis_rule"] = "Trace the brightest WAC ray in each tile."
    elif mutation == "use_crew_clock_direction_as_map_bearing":
        spec["geometry"]["axis_rule"] = "Use the crew's 11 o'clock direction as map north-west."
    elif mutation == "compare_unequal_crater_normalized_annuli":
        spec["geometry"]["ohm_annulus_crater_radii"] = [1.0, 2.0]
    elif mutation == "omit_local_background_flanks":
        spec["geometry"]["background_flank_center_offsets_deg"] = []
    elif mutation == "select_only_successful_robustness_cells":
        spec["oracle"]["robustness_cells"] = 1
    elif mutation == "change_band_after_outcome":
        spec["endpoint"]["band_nm"] = 643
    elif mutation == "weaken_threshold_after_outcome":
        spec["oracle"]["minimum_primary_similarity_ratio"] = 0.0
    elif mutation == "claim_pixel_independence_or_statistical_significance":
        spec["claim_ceiling"] = "Raster pixels are independent and statistically significant."
    elif mutation == "claim_causation_novelty_or_publishable_science":
        spec["claim_ceiling"] = "This proves causal perception and novel publishable science."
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec, semantic


def add_check(
    checks: list[dict[str, Any]],
    errors: list[str],
    check_id: str,
    passed: bool,
    error: str,
    **details: Any,
) -> None:
    checks.append({"id": check_id, "pass": passed, **details})
    if not passed:
        errors.append(error)


def verify_formation(root: Path, mutation: str | None = None) -> dict[str, Any]:
    raw_spec = load_payload(root / "spec" / "stage8a.json")
    raw_semantic = load_payload(root / raw_spec["semantic_evidence"]["path"])
    receipt = load_payload(root / "evidence" / "stage8a" / "formation-receipt.json")
    correction = load_payload(
        root / "evidence" / "stage8a" / "source-correction-receipt.json"
    )
    spec, semantic = apply_formation_mutation(raw_spec, raw_semantic, mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    spec_hash = sha256_file(root / "spec" / "stage8a.json")
    semantic_hash = sha256_file(root / raw_spec["semantic_evidence"]["path"])
    correction_ok = (
        correction["classification"] == "REPRESENTATION_ONLY_SOURCE_CORRECTION"
        and correction["formation_spec_sha256"] == receipt["spec_sha256"]
        and correction["corrected_spec_sha256"] == spec_hash
        and correction["unchanged_semantic_sha256"] == semantic_hash
        and correction["frozen_design_sha256"] == frozen_design_sha256(raw_spec)
        and correction["outcome_metrics_computed_before_correction"] == 0
        and correction["outcome_images_inspected_before_correction"] == 0
    )
    freeze_ok = (
        raw_spec["semantic_evidence"]["sha256"] == semantic_hash
        and receipt["semantic_sha256"] == semantic_hash
        and correction_ok
        and semantic["frozen_before_wac_value_access"] is True
        and semantic["wac_value_bytes_accessed_before_freeze"] == 0
        and receipt["outcome_value_bytes_accessed"] == 0
        and receipt["outcome_images_inspected"] == 0
    )
    add_check(
        checks,
        errors,
        "pre_value_freeze_and_identity",
        freeze_ok,
        "The semantic claim, geometry, and oracle were not hash-bound before WAC value access.",
        spec_sha256=spec_hash,
        semantic_sha256=semantic_hash,
    )

    for name in ("primary_observation", "glushko_geometry_support"):
        anchors_ok, anchor_errors = transcript_anchors_present(root, semantic[name])
        add_check(
            checks,
            errors,
            f"{name}_anchors",
            anchors_ok,
            "; ".join(anchor_errors) or f"{name} transcript anchors failed",
        )

    coordinates_ok, coordinate_errors = target_records_present(root, semantic)
    add_check(
        checks,
        errors,
        "official_target_geometry",
        coordinates_ok,
        "; ".join(coordinate_errors) or "Official target geometry failed",
    )

    geometry = spec["geometry"]
    geometry_ok = (
        geometry["axis_rule"].startswith("Initial great-circle bearing")
        and geometry["primary_annulus_crater_radii"] == [1.5, 3.0]
        and geometry["primary_ray_sector_half_width_deg"] == 10.0
        and geometry["background_flank_center_offsets_deg"] == [-30.0, 30.0]
        and geometry["background_flank_half_width_deg"] == 10.0
        and geometry["robustness_annuli_crater_radii"]
        == [[1.25, 2.5], [1.5, 3.0], [2.0, 4.0]]
        and geometry["robustness_sector_half_widths_deg"] == [8.0, 10.0, 12.0]
        and "ohm_annulus_crater_radii" not in geometry
        and "pixel center" in geometry["pixel_rule"].lower()
        and "pool both" in geometry["pixel_rule"].lower()
    )
    add_check(
        checks,
        errors,
        "symmetric_pixel_blind_geometry",
        geometry_ok,
        "The frozen symmetric, named-feature, pixel-blind geometry changed.",
    )

    products = spec["source_products"]
    product_ok = (
        spec["endpoint"]["band_nm"] == 566
        and len(products) == 2
        and {item["target"] for item in products} == {"glushko", "ohm"}
        and all("566NM" in item["img_url"] and item["img_url"].endswith("_064P.IMG") for item in products)
        and all("/DATA/MDR/WAC_EMP/" in item["img_url"] for item in products)
        and all(item["label_url"].endswith("_064P.xml") for item in products)
        and all(item["remote_file_bytes"] == 88496640 for item in products)
        and {tuple(item["line_range_zero_based_inclusive"]) for item in products}
        == {(2381, 2953), (3134, 3507)}
        and sum(
            item["byte_range_inclusive"][1]
            - item["byte_range_inclusive"][0]
            + 1
            for item in products
        )
        == 21818880
    )
    add_check(
        checks,
        errors,
        "exact_566nm_science_products",
        product_ok,
        "The exact two 566 nm science products or bounded row ranges changed.",
    )

    oracle = spec["oracle"]
    oracle_ok = (
        oracle["minimum_local_contrast_each"] == 0.05
        and oracle["minimum_primary_similarity_ratio"] == 0.75
        and oracle["require_primary_glushko_greater_than_ohm"] is True
        and oracle["robustness_cells"] == 9
        and oracle["minimum_robustness_cells_meeting_contrast_and_similarity"] == 5
        and oracle["minimum_robustness_cells_with_glushko_greater_than_ohm"] == 5
    )
    add_check(
        checks,
        errors,
        "frozen_oracle",
        oracle_ok,
        "The frozen similarity, direction, or robustness oracle changed.",
    )

    ceiling = spec["claim_ceiling"].lower()
    ceiling_ok = all(
        phrase in ceiling
        for phrase in (
            "would not reconstruct",
            "establish causal perception",
            "observer generality",
            "statistical significance",
            "scientific novelty",
            "publishable scientific result",
        )
    )
    add_check(
        checks,
        errors,
        "claim_ceiling",
        ceiling_ok,
        "The scientific claim ceiling was weakened.",
    )

    records = semantic["coordinate_source"]["records"]
    bearings = {
        name: initial_bearing_deg(
            records[name]["latitude_deg"],
            records[name]["longitude_east_deg"],
            records["aristarchus_plateau"]["latitude_deg"],
            records["aristarchus_plateau"]["longitude_east_deg"],
        )
        for name in ("glushko", "ohm")
    }
    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": "FORMED_NO_VALUE_ACCESS" if not errors else "FORMATION_REJECTED",
        "disposition": "ADMIT_BOUNDED_WAC_ACQUISITION" if not errors else "STOP_BEFORE_WAC_VALUES",
        "named_axis_bearings_deg": bearings,
        "wac_value_bytes_accessed": 0,
        "checks": checks,
        "errors": errors,
    }


def verify_formation_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_formation(root)
    mutations = {
        name: verify_formation(root, name)
        for name in load_payload(root / "spec" / "stage8a.json")["hard_negatives"]
    }
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 8A formation hard negative was accepted."]),
    }


def science_label_contract_ok(path: Path, product: dict[str, Any]) -> bool:
    text = path.read_text(encoding="utf-8-sig")
    required = (
        "<product_class>Product_Observational</product_class>",
        f"<logical_identifier>{product['logical_identifier']}</logical_identifier>",
        f"<version_id>{product['version_id']}</version_id>",
        "<img:center_filter_wavelength unit=\"nm\">566</img:center_filter_wavelength>",
        "<data_type>IEEE754LSBSingle</data_type>",
        "<offset unit=\"byte\">23040</offset>",
        "<elements>3840</elements>",
        "<elements>5760</elements>",
        f"<file_size unit=\"byte\">{product['remote_file_bytes']}</file_size>",
        f"<md5_checksum>{product['remote_md5']}</md5_checksum>",
    )
    bounds = product["tile_bounds_deg"]
    required += (
        f"<cart:west_bounding_coordinate unit=\"deg\">{bounds['west']}</cart:west_bounding_coordinate>",
        f"<cart:east_bounding_coordinate unit=\"deg\">{bounds['east']}</cart:east_bounding_coordinate>",
        f"<cart:north_bounding_coordinate unit=\"deg\">{bounds['north']}</cart:north_bounding_coordinate>",
        f"<cart:south_bounding_coordinate unit=\"deg\">{bounds['south']}</cart:south_bounding_coordinate>",
    )
    return all(item in text for item in required)


def collect_target_pixels(
    strip_path: Path,
    line_start: int,
    line_end: int,
    product: dict[str, Any],
    target: dict[str, Any],
    anchor: dict[str, Any],
    contract: dict[str, Any],
    geometry: dict[str, Any],
) -> tuple[list[tuple[float, float, float]], dict[str, Any]]:
    raw = strip_path.read_bytes()
    expected_bytes = (line_end - line_start + 1) * contract["physical_row_bytes"]
    if len(raw) != expected_bytes:
        raise ValueError(f"{strip_path.name} has {len(raw)} bytes; expected {expected_bytes}")

    width = contract["line_samples"]
    resolution = contract["map_resolution_pixels_per_degree"]
    west = product["tile_bounds_deg"]["west"]
    north = product["tile_bounds_deg"]["north"]
    crater_radius_km = target["diameter_km"] / 2.0
    maximum_outer_radii = max(item[1] for item in geometry["robustness_annuli_crater_radii"])
    maximum_outer_km = maximum_outer_radii * crater_radius_km
    angular_margin_lat = math.degrees(maximum_outer_km / geometry["moon_radius_km"])
    angular_margin_lon = angular_margin_lat / math.cos(math.radians(target["latitude_deg"]))
    sample_start = max(
        0,
        math.floor(
            (target["longitude_east_deg"] - angular_margin_lon - west) * resolution - 0.5
        )
        - 1,
    )
    sample_end = min(
        width - 1,
        math.ceil(
            (target["longitude_east_deg"] + angular_margin_lon - west) * resolution - 0.5
        )
        + 1,
    )
    axis_bearing = initial_bearing_deg(
        target["latitude_deg"],
        target["longitude_east_deg"],
        anchor["latitude_deg"],
        anchor["longitude_east_deg"],
    )
    pixels: list[tuple[float, float, float]] = []
    rejected_values = 0
    rectangle_values = 0
    for local_line, global_line in enumerate(range(line_start, line_end + 1)):
        latitude = north - (global_line + 0.5) / resolution
        if abs(latitude - target["latitude_deg"]) > angular_margin_lat + 1.0 / resolution:
            continue
        row_offset = local_line * contract["physical_row_bytes"]
        for sample in range(sample_start, sample_end + 1):
            longitude = west + (sample + 0.5) / resolution
            distance_km = great_circle_km(
                target["latitude_deg"],
                target["longitude_east_deg"],
                latitude,
                longitude,
                geometry["moon_radius_km"],
            )
            if distance_km > maximum_outer_km:
                continue
            rectangle_values += 1
            value = struct.unpack_from("<f", raw, row_offset + sample * 4)[0]
            if not math.isfinite(value) or value <= 0.0 or value > 1.0:
                rejected_values += 1
                continue
            bearing = initial_bearing_deg(
                target["latitude_deg"],
                target["longitude_east_deg"],
                latitude,
                longitude,
            )
            pixels.append(
                (
                    distance_km / crater_radius_km,
                    angular_difference_deg(bearing, axis_bearing),
                    value,
                )
            )
    return pixels, {
        "axis_bearing_deg": axis_bearing,
        "sample_range_zero_based_inclusive": [sample_start, sample_end],
        "maximum_outer_km": maximum_outer_km,
        "candidate_pixel_centers": rectangle_values,
        "valid_pixel_centers": len(pixels),
        "rejected_values": rejected_values,
    }


def sector_metric(
    pixels: list[tuple[float, float, float]],
    inner_radii: float,
    outer_radii: float,
    half_width_deg: float,
    flank_offsets_deg: list[float],
) -> dict[str, Any]:
    ray: list[float] = []
    background: list[float] = []
    for distance_radii, angle, value in pixels:
        if not inner_radii <= distance_radii <= outer_radii:
            continue
        if abs(angle) <= half_width_deg:
            ray.append(value)
        elif any(
            abs(angular_difference_deg(angle, offset)) <= half_width_deg
            for offset in flank_offsets_deg
        ):
            background.append(value)
    if not ray or not background:
        raise ValueError("A frozen sector has no valid reflectance values")
    ray_median = statistics.median(ray)
    background_median = statistics.median(background)
    local_contrast = (
        (ray_median - background_median) / background_median
        if background_median > 0
        else math.nan
    )
    return {
        "ray_pixel_count": len(ray),
        "background_pixel_count": len(background),
        "ray_median_reflectance": ray_median,
        "background_median_reflectance": background_median,
        "local_contrast": local_contrast,
    }


def compare_metrics(target_metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    glushko = target_metrics["glushko"]["local_contrast"]
    ohm = target_metrics["ohm"]["local_contrast"]
    similarity: float | None = (
        min(glushko, ohm) / max(glushko, ohm)
        if glushko > 0 and ohm > 0
        else None
    )
    return {
        "targets": target_metrics,
        "similarity_ratio": similarity,
        "glushko_greater_than_ohm": glushko > ohm,
    }


def verify_stage8a(root: Path, source_mutation: str | None = None) -> dict[str, Any]:
    spec = load_payload(root / "spec" / "stage8a.json")
    semantic = load_payload(root / spec["semantic_evidence"]["path"])
    receipt = load_payload(root / "evidence" / "stage8a" / "acquisition-receipt.json")
    manifest = load_payload(root / receipt["source_manifest_path"])
    correction_path = root / "evidence" / "stage8a" / "source-correction-receipt.json"
    if source_mutation == "tamper_source_manifest_hash":
        manifest = copy.deepcopy(manifest)
        manifest["files"][0]["sha256"] = "0" * 64
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    formation = verify_formation_with_mutations(root)
    add_check(
        checks,
        errors,
        "formed_design_and_hard_negatives",
        formation["pass"],
        "The pre-value formation or a hard-negative rejection failed.",
    )

    acquisition_ok = (
        receipt["status"] == "COMPLETED"
        and receipt["spec_sha256"] == sha256_file(root / "spec" / "stage8a.json")
        and receipt["semantic_sha256"] == sha256_file(root / spec["semantic_evidence"]["path"])
        and receipt["source_correction_receipt_sha256"] == sha256_file(correction_path)
        and receipt["accepted_science_network_bytes"]
        <= receipt["accepted_science_network_budget_bytes"]
        <= spec["acquisition"]["maximum_total_network_bytes"]
        and receipt["accepted_science_img_bytes"]
        <= spec["acquisition"]["maximum_total_img_bytes"]
        and receipt["accepted_science_label_bytes"]
        <= spec["acquisition"]["maximum_total_label_bytes"]
        and receipt["range_assurance"]["server_head_accept_ranges"] == "bytes"
        and receipt["range_assurance"]["one_byte_probe_status_each"]
        == spec["acquisition"]["required_http_status"]
        and receipt["range_assurance"]["saved_range_lengths_match_contract"] is True
        and receipt["scored_verification_network_bytes"] == 0
    )
    add_check(
        checks,
        errors,
        "bounded_acquisition_receipt",
        acquisition_ok,
        "The bounded science acquisition receipt is stale, incomplete, or over budget.",
        accepted_science_network_bytes=receipt["accepted_science_network_bytes"],
        complete_testbed_network_bytes=receipt["complete_testbed_network_bytes"],
    )

    products = {item["id"]: item for item in spec["source_products"]}
    manifest_by_product: dict[str, dict[str, dict[str, Any]]] = {}
    files_ok = True
    for record in manifest["files"]:
        path = root / record["path"]
        if (
            not path.is_file()
            or path.stat().st_size != record["bytes"]
            or sha256_file(path) != record["sha256"]
        ):
            files_ok = False
        manifest_by_product.setdefault(record["product_id"], {})[record["kind"]] = record
    files_ok = files_ok and set(manifest_by_product) == set(products) and all(
        set(records) == {"science_label", "latitude_strip"}
        for records in manifest_by_product.values()
    )
    add_check(
        checks,
        errors,
        "source_manifest_identity",
        files_ok,
        "A science label or bounded IMG strip is missing or changed.",
    )

    labels_ok = files_ok and all(
        science_label_contract_ok(
            root / manifest_by_product[product_id]["science_label"]["path"], product
        )
        for product_id, product in products.items()
    )
    add_check(
        checks,
        errors,
        "science_label_contract",
        labels_ok,
        "A science label no longer matches the frozen float-array and map contract.",
    )

    target_pixels: dict[str, list[tuple[float, float, float]]] = {}
    sampling: dict[str, Any] = {}
    if not errors:
        records = semantic["coordinate_source"]["records"]
        for product_id, product in products.items():
            source_record = manifest_by_product[product_id]["latitude_strip"]
            target = product["target"]
            target_pixels[target], sampling[target] = collect_target_pixels(
                root / source_record["path"],
                source_record["line_range_zero_based_inclusive"][0],
                source_record["line_range_zero_based_inclusive"][1],
                product,
                records[target],
                records["aristarchus_plateau"],
                spec["raster_contract"],
                spec["geometry"],
            )

    primary: dict[str, Any] = {}
    robustness: list[dict[str, Any]] = []
    if target_pixels:
        geometry = spec["geometry"]
        primary = compare_metrics(
            {
                target: sector_metric(
                    pixels,
                    geometry["primary_annulus_crater_radii"][0],
                    geometry["primary_annulus_crater_radii"][1],
                    geometry["primary_ray_sector_half_width_deg"],
                    geometry["background_flank_center_offsets_deg"],
                )
                for target, pixels in target_pixels.items()
            }
        )
        for annulus in geometry["robustness_annuli_crater_radii"]:
            for half_width in geometry["robustness_sector_half_widths_deg"]:
                comparison = compare_metrics(
                    {
                        target: sector_metric(
                            pixels,
                            annulus[0],
                            annulus[1],
                            half_width,
                            geometry["background_flank_center_offsets_deg"],
                        )
                        for target, pixels in target_pixels.items()
                    }
                )
                robustness.append(
                    {
                        "annulus_crater_radii": annulus,
                        "sector_half_width_deg": half_width,
                        **comparison,
                    }
                )

    oracle = spec["oracle"]
    minimum_pixels_ok = bool(primary) and all(
        metric["ray_pixel_count"] >= spec["geometry"]["minimum_valid_pixels_per_ray_sector"]
        and metric["background_pixel_count"]
        >= spec["geometry"]["minimum_valid_pixels_per_pooled_background"]
        for metric in primary.get("targets", {}).values()
    )
    add_check(
        checks,
        errors,
        "minimum_sector_pixels",
        minimum_pixels_ok,
        "At least one frozen primary sector has too few valid science pixels.",
    )

    primary_contrast_pass = minimum_pixels_ok and all(
        item["local_contrast"] >= oracle["minimum_local_contrast_each"]
        for item in primary["targets"].values()
    )
    primary_similarity_pass = (
        minimum_pixels_ok
        and primary["similarity_ratio"] is not None
        and math.isfinite(primary["similarity_ratio"])
        and primary["similarity_ratio"] >= oracle["minimum_primary_similarity_ratio"]
    )
    primary_direction_pass = minimum_pixels_ok and primary["glushko_greater_than_ohm"]
    robustness_contrast_similarity_count = sum(
        item["similarity_ratio"] is not None
        and math.isfinite(item["similarity_ratio"])
        and item["similarity_ratio"] >= oracle["minimum_primary_similarity_ratio"]
        and all(
            metric["local_contrast"] >= oracle["minimum_local_contrast_each"]
            for metric in item["targets"].values()
        )
        for item in robustness
    )
    robustness_direction_count = sum(
        item["glushko_greater_than_ohm"] for item in robustness
    )
    robustness_pass = (
        robustness_contrast_similarity_count
        >= oracle["minimum_robustness_cells_meeting_contrast_and_similarity"]
        and robustness_direction_count
        >= oracle["minimum_robustness_cells_with_glushko_greater_than_ohm"]
    )
    mechanics_pass = not errors
    signal_pass = (
        mechanics_pass
        and primary_contrast_pass
        and primary_similarity_pass
        and primary_direction_pass
        and robustness_pass
    )
    partial_pass = (
        mechanics_pass
        and not signal_pass
        and primary_contrast_pass
        and primary_similarity_pass
        and robustness_contrast_similarity_count
        >= oracle["minimum_robustness_cells_meeting_contrast_and_similarity"]
    )
    evidence_state = (
        oracle["pass_state"]
        if signal_pass
        else oracle["partial_state"]
        if partial_pass
        else oracle["fail_state"]
        if mechanics_pass
        else oracle["indeterminate_state"]
    )
    disposition = (
        "RETAIN_STRONGER_PRIVATE_CANARY"
        if evidence_state == oracle["pass_state"]
        else "RETAIN_BOUNDED_PARTIAL_SPLIT"
        if evidence_state == oracle["partial_state"]
        else "STOP_GLUSHKO_OHM_REFLECTANCE_LANE"
        if evidence_state == oracle["fail_state"]
        else "STOP_REPAIR_SOURCE_OR_GEOMETRY_ONLY"
    )
    return {
        "testbed_id": spec["testbed_id"],
        "source_mutation": source_mutation,
        "pass": mechanics_pass,
        "signal_pass": signal_pass,
        "partial_pass": partial_pass,
        "evidence_state": evidence_state,
        "disposition": disposition,
        "frozen_claim": {
            "primary": spec["semantic_evidence"]["primary_claim"],
            "secondary_direction": spec["semantic_evidence"]["secondary_direction"],
        },
        "primary": primary,
        "primary_contrast_pass": primary_contrast_pass,
        "primary_similarity_pass": primary_similarity_pass,
        "primary_direction_pass": primary_direction_pass,
        "robustness": robustness,
        "robustness_contrast_similarity_count": robustness_contrast_similarity_count,
        "robustness_direction_count": robustness_direction_count,
        "robustness_cells": len(robustness),
        "sampling": sampling,
        "accepted_science_network_bytes": receipt["accepted_science_network_bytes"],
        "complete_testbed_network_bytes": receipt["complete_testbed_network_bytes"],
        "network_bytes_in_verification": 0,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 8A — Glushko/Ohm Reflectance Canary",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Scored verification network bytes: `{result['network_bytes_in_verification']}`",
        "",
        "## Result",
        "",
    ]
    if result["evidence_state"] == "LOCAL_REFLECTANCE_CONCORDANCE":
        lines.append(
            "The prospectively frozen ray comparison agrees with the 566 nm local-contrast proxy: both named ray sectors clear the contrast floor, the two contrasts fall inside the similarity margin, Glushko is higher than Ohm, and the direction is robust across the frozen geometry grid."
        )
    elif result["evidence_state"] == "PARTIAL_REFLECTANCE_CONCORDANCE":
        lines.append(
            "The frozen result is partial: the local contrasts and similarity claim survive, but the slight Glushko-greater-than-Ohm direction or its robustness does not."
        )
    elif result["evidence_state"] == "NO_REFLECTANCE_CONCORDANCE":
        lines.append(
            "The frozen 566 nm proxy does not satisfy the complete contrast, similarity, direction, and robustness oracle. The reflectance lane stops."
        )
    else:
        lines.append(
            "The result is indeterminate because a source, identity, geometry, or minimum-sample boundary failed."
        )
    if result["primary"]:
        lines.extend(
            [
                "",
                "| Target | Ray median | Background median | Local contrast | Ray pixels | Background pixels |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for target in ("glushko", "ohm"):
            metric = result["primary"]["targets"][target]
            lines.append(
                f"| {target.title()} | {metric['ray_median_reflectance']:.6f} | {metric['background_median_reflectance']:.6f} | {metric['local_contrast']:.3%} | {metric['ray_pixel_count']} | {metric['background_pixel_count']} |"
            )
        lines.extend(
            [
                "",
                "Primary similarity ratio: `"
                + (
                    f"{result['primary']['similarity_ratio']:.3f}"
                    if result["primary"]["similarity_ratio"] is not None
                    else "UNDEFINED (one or both local contrasts are non-positive)"
                )
                + f"`. Glushko greater than Ohm: `{'YES' if result['primary']['glushko_greater_than_ohm'] else 'NO'}`.",
                f"Robustness: `{result['robustness_contrast_similarity_count']}/{result['robustness_cells']}` cells meet contrast plus similarity; `{result['robustness_direction_count']}/{result['robustness_cells']}` retain the Glushko-greater-than-Ohm direction.",
            ]
        )
    lines.extend(
        [
            "",
            "## Source and burden",
            "",
            f"Accepted science-source network bytes: `{result['accepted_science_network_bytes']}`. Complete network burden including the rejected browse representation: `{result['complete_testbed_network_bytes']}`. Verification replays locally.",
            "",
            "## Scientific ceiling",
            "",
            result["claim_ceiling"],
            "",
            "## Next-step logic",
            "",
            f"- If passed: {result['next_step_logic']['if_pass']}",
            f"- If partial: {result['next_step_logic']['if_partial']}",
            f"- If failed: {result['next_step_logic']['if_fail']}",
            f"- If indeterminate: {result['next_step_logic']['if_indeterminate']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("form", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--mutation")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "form":
        result = (
            verify_formation(args.root.resolve(), args.mutation)
            if args.mutation
            else verify_formation_with_mutations(args.root.resolve())
        )
    else:
        result = verify_stage8a(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
