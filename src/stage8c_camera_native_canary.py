#!/usr/bin/env python3
"""Form and verify the frozen Stage 8C camera-native ordinal canary."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    spec = copy.deepcopy(spec)
    if mutation is None:
        return spec
    if mutation == "make_matched_pair_primary_over_joint_frame":
        spec["comparison_hierarchy"]["primary"] = "matched_400mm_pair"
    elif mutation == "select_alternate_or_additional_exposures":
        spec["budget"]["scored_png_images"] = 4
    elif mutation == "hand_draw_regions_from_visible_rays":
        spec["coordinate_model"]["fit"] = "Hand-draw bright ray regions after inspection."
    elif mutation == "swap_label_coordinate_axes":
        spec["coordinate_model"]["image_x_field"] = "horizontal_coordinate_pixel"
        spec["coordinate_model"]["image_y_field"] = "vertical_coordinate_pixel"
    elif mutation == "shift_pixel_coordinate_origin_after_outcome":
        spec["coordinate_model"]["pixel_center_coordinates"] = (
            "Add a half-pixel offset after inspecting the outcome."
        )
    elif mutation == "treat_browse_code_values_as_physical_albedo":
        spec["representation_contract"]["pixel_value_name"] = "physical albedo"
        spec["representation_contract"]["physical_claims_excluded"] = []
    elif mutation == "treat_correlated_pixels_as_independent_significance":
        spec["endpoint"]["reason"] = "Use every pixel as an independent significance sample."
    elif mutation == "call_camera_image_hansen_perception":
        spec["claim_ceiling"] = "The camera image reconstructs Hansen's perception."
    elif mutation == "claim_joint_and_pair_are_independent_replications":
        spec["comparison_hierarchy"]["independence"] = (
            "The joint and paired checks are independent replications."
        )
    elif mutation == "remove_strict_glushko_greater_than_ohm_direction":
        spec["oracle"]["require_glushko_greater_than_ohm"] = False
    elif mutation == "weaken_similarity_after_outcome":
        spec["oracle"]["minimum_similarity_ratio"] = 0.5
    elif mutation == "reinterpret_stage8a_failure_as_support":
        spec["prior_stage_boundary"]["forbidden_reopenings"] = []
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec


def png_structure(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    width, height, bit_depth, color_type, compression, filtering, interlace = (
        struct.unpack(">IIBBBBB", data[16:29])
    )
    offset = 8
    palette_entries = 0
    idat_bytes = 0
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        if chunk_type == b"PLTE":
            palette_entries = length // 3
        elif chunk_type == b"IDAT":
            idat_bytes += length
        offset += 12 + length
        if chunk_type == b"IEND":
            break
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "compression": compression,
        "filter": filtering,
        "interlace": interlace,
        "palette_entries": palette_entries,
        "idat_bytes": idat_bytes,
        "idat_decompressed": False,
    }


def pixel_intercepts(path: Path) -> list[dict[str, float]]:
    records: list[dict[str, float]] = []
    root = ET.parse(path).getroot()
    required = {
        "vertical_coordinate_pixel",
        "horizontal_coordinate_pixel",
        "pixel_latitude",
        "pixel_longitude",
    }
    for element in root.iter():
        if element.tag.split("}")[-1] != "Pixel_Intercept":
            continue
        values = {
            child.tag.split("}")[-1]: (child.text or "").strip()
            for child in element.iter()
        }
        if required.issubset(values):
            records.append({key: float(values[key]) for key in required})
    return records


def solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    size = len(vector)
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        if abs(scale) < 1e-12:
            raise ValueError("Singular affine fit")
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column])
            ]
    return [row[-1] for row in augmented]


def least_squares(rows: list[list[float]], values: list[float]) -> list[float]:
    width = len(rows[0])
    normal = [[0.0] * width for _ in range(width)]
    rhs = [0.0] * width
    for row, value in zip(rows, values):
        for left in range(width):
            rhs[left] += row[left] * value
            for right in range(width):
                normal[left][right] += row[left] * row[right]
    return solve(normal, rhs)


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def local_coordinates(
    latitude: float, longitude: float, target: dict[str, Any]
) -> tuple[float, float]:
    delta_longitude = (
        longitude - target["longitude_east_deg"] + 180.0
    ) % 360.0 - 180.0
    return (
        delta_longitude * math.cos(math.radians(target["latitude_deg"])),
        latitude - target["latitude_deg"],
    )


def geometry_preflight(
    records: list[dict[str, float]],
    target: dict[str, Any],
    model: dict[str, Any],
    outer_radius_craters: float,
    width: int,
    height: int,
) -> dict[str, Any]:
    crater_radius_deg = math.degrees(
        (target["diameter_km"] / 2.0) / model["moon_radius_km"]
    )
    fit_radius_deg = max(4.0, 1.35 * outer_radius_craters * crater_radius_deg)
    points: list[tuple[float, float, float, float]] = []
    for record in records:
        u, v = local_coordinates(
            record["pixel_latitude"], record["pixel_longitude"], target
        )
        if math.hypot(u, v) <= fit_radius_deg:
            points.append(
                (
                    u,
                    v,
                    record[model["image_x_field"]],
                    record[model["image_y_field"]],
                )
            )
    points.sort()
    training = [point for index, point in enumerate(points) if index % 5]
    validation = [point for index, point in enumerate(points) if index % 5 == 0]
    if len(training) < 3 or len(validation) < 1:
        return {"pass": False, "point_count": len(points), "error": "too few points"}
    rows = [[1.0, u, v] for u, v, _, _ in training]
    x_parameters = least_squares(rows, [x for _, _, x, _ in training])
    y_parameters = least_squares(rows, [y for _, _, _, y in training])
    residuals: list[float] = []
    for u, v, x, y in validation:
        row = [1.0, u, v]
        predicted_x = sum(a * b for a, b in zip(row, x_parameters))
        predicted_y = sum(a * b for a, b in zip(row, y_parameters))
        residuals.append(math.hypot(predicted_x - x, predicted_y - y))
    median_residual = percentile(residuals, 0.5)
    p90_residual = percentile(residuals, 0.9)
    maximum_residual = max(residuals)
    region_radius_deg = outer_radius_craters * crater_radius_deg
    x_extent = region_radius_deg * math.hypot(x_parameters[1], x_parameters[2])
    y_extent = region_radius_deg * math.hypot(y_parameters[1], y_parameters[2])
    complete_region = (
        0 <= x_parameters[0] - x_extent
        and x_parameters[0] + x_extent < width
        and 0 <= y_parameters[0] - y_extent
        and y_parameters[0] + y_extent < height
    )
    passed = (
        len(training) >= model["minimum_training_points"]
        and len(validation) >= model["minimum_validation_points"]
        and median_residual <= model["maximum_validation_median_residual_pixels"]
        and p90_residual <= model["maximum_validation_p90_residual_pixels"]
        and maximum_residual <= model["maximum_validation_residual_pixels"]
        and (complete_region or not model["require_complete_regions_inside_image"])
    )
    return {
        "pass": passed,
        "point_count": len(points),
        "training_points": len(training),
        "validation_points": len(validation),
        "fit_radius_deg": fit_radius_deg,
        "crater_radius_deg": crater_radius_deg,
        "validation_median_residual_pixels": median_residual,
        "validation_p90_residual_pixels": p90_residual,
        "validation_maximum_residual_pixels": maximum_residual,
        "predicted_center": [x_parameters[0], y_parameters[0]],
        "complete_region": complete_region,
    }


def official_targets(path: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for item in load_json(path):
        properties = item.get("target_properties", {})
        name = properties.get("target_name")
        if name not in {"Glushko Crater", "Ohm Crater"} or name in found:
            continue
        found[name] = {
            "latitude_deg": float(properties["latitude"]),
            "longitude_east_deg": float(properties["longitude"]),
            "diameter_km": float(properties["diameter"]),
            "unaided_eye_actions": properties.get("unaided_eye_actions", ""),
            "camera_actions": properties.get("camera_actions", ""),
        }
    return found


def verify_formation(root: Path, mutation: str | None = None) -> dict[str, Any]:
    raw_spec = load_json(root / "spec" / "stage8c.json")
    spec = apply_mutation(raw_spec, mutation)
    receipt = load_json(root / "evidence" / "stage8c" / "formation-receipt.json")
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    spec_hash = sha256_file(root / "spec" / "stage8c.json")
    freeze_ok = (
        receipt["status"] == "FORMED_NO_CAMERA_VALUE_SCORING"
        and receipt["spec_sha256"] == spec_hash
        and receipt["formed_at_utc"] == raw_spec["formed_at_utc"]
        and receipt["image_code_values_scored_before_formation"] == 0
        and receipt["png_idat_streams_decompressed_before_formation"] == 0
    )
    add_check(
        checks,
        errors,
        "pre_score_freeze_and_identity",
        freeze_ok,
        "The formation identity or zero-scoring boundary changed.",
        spec_sha256=spec_hash,
    )

    sources_ok = len(spec["source_files"]) == 7
    source_details: dict[str, Any] = {}
    for source in spec["source_files"]:
        path = root / source["path"]
        valid = path.is_file() and sha256_file(path) == source["sha256"]
        sources_ok = sources_ok and valid
        source_details[source["role"]] = {"pass": valid, "path": source["path"]}
    add_check(
        checks,
        errors,
        "exact_source_identity",
        sources_ok,
        "The exact seven-file source boundary changed.",
        sources=source_details,
    )

    prior = spec["prior_stage_boundary"]
    prior_result_path = root / prior["stage8b_result_path"]
    prior_result = load_json(prior_result_path)
    prior_ok = (
        sha256_file(root / prior["stage8b_spec_path"]) == prior["stage8b_spec_sha256"]
        and sha256_file(prior_result_path) == prior["stage8b_result_sha256"]
        and prior_result["evidence_state"] == prior["required_stage8b_evidence_state"]
        and prior_result["disposition"] == prior["required_stage8b_disposition"]
        and set(prior["forbidden_reopenings"])
        == {
            "retune_stage8a_geometry_band_or_thresholds",
            "select_stage8b_fallback_exposures",
            "search_additional_camera_frames",
            "reinterpret_stage8a_failure_as_support",
        }
    )
    add_check(
        checks,
        errors,
        "stage8b_admission_and_stage8a_non_reopening",
        prior_ok,
        "The Stage 8B admission or Stage 8A non-reopening boundary changed.",
    )

    hierarchy = spec["comparison_hierarchy"]
    hierarchy_ok = (
        hierarchy["primary"] == "joint_same_frame"
        and hierarchy["secondary"] == "matched_400mm_pair"
        and "cannot outrank" in hierarchy["rationale"]
        and "not independent replications" in hierarchy["independence"]
        and spec["budget"]["scored_png_images"] == 3
        and spec["budget"]["additional_source_files"] == 0
        and spec["budget"]["additional_network_bytes"] == 0
    )
    add_check(
        checks,
        errors,
        "joint_primary_pair_secondary",
        hierarchy_ok,
        "The within-frame primary, matched-pair secondary, or three-image budget changed.",
    )

    source_by_role = {item["role"]: item for item in spec["source_files"]}
    target_source = root / source_by_role["official_target_request"]["path"]
    observed_targets = official_targets(target_source)
    targets_ok = set(observed_targets) == {"Glushko Crater", "Ohm Crater"}
    for key, frozen in spec["targets"].items():
        observed = observed_targets.get(frozen["official_name"], {})
        targets_ok = targets_ok and all(
            math.isclose(observed.get(field, math.nan), frozen[field], abs_tol=1e-12)
            for field in ("latitude_deg", "longitude_east_deg", "diameter_km")
        )
        targets_ok = (
            targets_ok
            and "Compare the ejecta/ray systems" in observed.get("unaided_eye_actions", "")
            and "Image and compare the brightness and extent" in observed.get("camera_actions", "")
        )
    add_check(
        checks,
        errors,
        "official_target_geometry_and_action_separation",
        targets_ok,
        "Official target geometry or the camera/unaided-eye action separation changed.",
    )

    representation = spec["representation_contract"]
    png_roles = ["matched_glushko_image", "matched_ohm_image", "joint_image"]
    png_details: dict[str, Any] = {}
    png_ok = True
    for role in png_roles:
        structure = png_structure(root / source_by_role[role]["path"])
        valid = (
            structure["width"] == representation["expected_width"]
            and structure["height"] == representation["expected_height"]
            and structure["bit_depth"] == representation["expected_bit_depth"]
            and structure["color_type"] == representation["expected_png_color_type"]
            and structure["interlace"] == representation["expected_interlace_method"]
            and 1 <= structure["palette_entries"] <= 256
            and structure["idat_decompressed"] is False
        )
        png_ok = png_ok and valid
        png_details[role] = {**structure, "pass": valid}
    excluded = set(representation["physical_claims_excluded"])
    representation_ok = (
        png_ok
        and representation["pixel_value_name"]
        == "uncalibrated RGB palette code-value lightness"
        and representation["lightness_integer_formula"]
        == "L = (54*R + 183*G + 19*B + 128) // 256"
        and {"reflectance", "absolute_albedo", "retinal_luminance", "perceived_brightness"}.issubset(excluded)
    )
    add_check(
        checks,
        errors,
        "png_and_uncalibrated_representation_boundary",
        representation_ok,
        "The PNG identity or uncalibrated code-value boundary changed.",
        images=png_details,
    )

    model = spec["coordinate_model"]
    outer_radius = max(cell["outer_crater_radii"][1] for cell in spec["region_cells"])
    label_roles = {
        "matched_glushko": ("matched_glushko_label", "glushko"),
        "matched_ohm": ("matched_ohm_label", "ohm"),
        "joint_glushko": ("joint_label", "glushko"),
        "joint_ohm": ("joint_label", "ohm"),
    }
    geometry_details: dict[str, Any] = {}
    geometry_ok = (
        model["image_x_field"] == "vertical_coordinate_pixel"
        and model["image_y_field"] == "horizontal_coordinate_pixel"
        and model["pixel_center_coordinates"].startswith(
            "Use zero-based raster coordinates"
        )
        and "Hand-draw" not in model["fit"]
        and len(spec["region_cells"]) == 3
        and sum(bool(cell.get("primary")) for cell in spec["region_cells"]) == 1
        and all(
            cell["boundary_rule"] == "lower inclusive, upper exclusive"
            for cell in spec["region_cells"]
        )
    )
    for role, (label_role, target_key) in label_roles.items():
        details = geometry_preflight(
            pixel_intercepts(root / source_by_role[label_role]["path"]),
            spec["targets"][target_key],
            model,
            outer_radius,
            representation["expected_width"],
            representation["expected_height"],
        )
        geometry_details[role] = details
        geometry_ok = geometry_ok and details["pass"]
    add_check(
        checks,
        errors,
        "coordinate_derived_regions_and_geometry_preflight",
        geometry_ok,
        "A coordinate axis, region freeze, or held-out geometry preflight failed.",
        fits=geometry_details,
    )

    endpoint = spec["endpoint"]
    oracle = spec["oracle"]
    endpoint_ok = (
        endpoint["name"] == "rank_probability_local_ray_excess"
        and "256-bin histograms" in endpoint["per_target_metric"]
        and "does not use pixel-count significance" in endpoint["reason"]
        and oracle["minimum_auc_each"] == 0.55
        and oracle["minimum_similarity_ratio"] == 0.75
        and oracle["require_glushko_greater_than_ohm"] is True
        and oracle["minimum_passing_cells_per_view"] == 2
        and oracle["required_primary_cell_id"]
        == "inner_1p50_3p00_outer_3p00_4p00"
    )
    add_check(
        checks,
        errors,
        "rank_endpoint_and_frozen_oracle",
        endpoint_ok,
        "The rank endpoint, material-effect threshold, similarity, or direction changed.",
    )

    ceiling = spec["claim_ceiling"].lower()
    boundary_ok = (
        "would not establish physical albedo" in ceiling
        and "hansen's retinal or perceived stimulus" in ceiling
        and "causal explanation" in ceiling
        and "independent replication" in ceiling
        and "public scientific finding" in ceiling
        and "do not change products, regions, endpoint, or thresholds"
        in spec["next_step_logic"]["if_indeterminate"].lower()
    )
    add_check(
        checks,
        errors,
        "claim_ceiling_and_branch_complete_next_steps",
        boundary_ok,
        "The photographic claim ceiling or repair-only next step changed.",
    )

    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": "FORMED_NO_CAMERA_VALUE_SCORING" if not errors else "FORMATION_FAILED",
        "disposition": "ADMIT_FROZEN_OFFLINE_CAMERA_SCORING" if not errors else "STOP_REPAIR_FORMATION_ONLY",
        "image_code_values_scored": 0,
        "png_idat_streams_decompressed": 0,
        "checks": checks,
        "errors": errors,
    }


def verify_formation_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_formation(root)
    mutations = {
        mutation: verify_formation(root, mutation)
        for mutation in load_json(root / "spec" / "stage8c.json")["hard_negatives"]
    }
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "pass": baseline["pass"] and hard_negatives_pass,
        "hard_negatives_pass": hard_negatives_pass,
        "hard_negatives": mutations,
    }


def paeth_predictor(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def unfilter_indexed_scanlines(raw: bytes, width: int, height: int) -> bytes:
    expected = (width + 1) * height
    if len(raw) != expected:
        raise ValueError(
            f"Unexpected decompressed PNG size: {len(raw)} instead of {expected}"
        )
    pixels = bytearray(width * height)
    source_offset = 0
    for row in range(height):
        filter_type = raw[source_offset]
        source_offset += 1
        row_offset = row * width
        previous_offset = (row - 1) * width
        for column in range(width):
            encoded = raw[source_offset]
            source_offset += 1
            left = pixels[row_offset + column - 1] if column else 0
            up = pixels[previous_offset + column] if row else 0
            upper_left = (
                pixels[previous_offset + column - 1] if row and column else 0
            )
            if filter_type == 0:
                value = encoded
            elif filter_type == 1:
                value = encoded + left
            elif filter_type == 2:
                value = encoded + up
            elif filter_type == 3:
                value = encoded + ((left + up) // 2)
            elif filter_type == 4:
                value = encoded + paeth_predictor(left, up, upper_left)
            else:
                raise ValueError(f"Unsupported PNG filter type: {filter_type}")
            pixels[row_offset + column] = value & 0xFF
    return bytes(pixels)


def decode_indexed_png(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    offset = 8
    header: tuple[int, int, int, int, int, int, int] | None = None
    palette: list[tuple[int, int, int]] = []
    compressed = bytearray()
    chunk_count = 0
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("Truncated PNG chunk header")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        if chunk_end > len(data):
            raise ValueError("Truncated PNG chunk payload")
        payload = data[offset + 8 : offset + 8 + length]
        stored_crc = struct.unpack(">I", data[offset + 8 + length : chunk_end])[0]
        computed_crc = zlib.crc32(chunk_type)
        computed_crc = zlib.crc32(payload, computed_crc) & 0xFFFFFFFF
        if stored_crc != computed_crc:
            raise ValueError(f"PNG CRC mismatch in {chunk_type!r}")
        chunk_count += 1
        if chunk_type == b"IHDR":
            header = struct.unpack(">IIBBBBB", payload)
        elif chunk_type == b"PLTE":
            if length % 3:
                raise ValueError("PNG palette length is not divisible by three")
            palette = [tuple(payload[index : index + 3]) for index in range(0, length, 3)]
        elif chunk_type == b"IDAT":
            compressed.extend(payload)
        elif chunk_type == b"IEND":
            break
        offset = chunk_end
    if header is None:
        raise ValueError("PNG lacks IHDR")
    width, height, bit_depth, color_type, compression, filtering, interlace = header
    if (bit_depth, color_type, compression, filtering, interlace) != (8, 3, 0, 0, 0):
        raise ValueError("PNG is not the frozen 8-bit non-interlaced indexed representation")
    if not palette or len(palette) > 256 or not compressed:
        raise ValueError("PNG lacks a valid palette or compressed image data")
    raw = zlib.decompress(bytes(compressed))
    pixels = unfilter_indexed_scanlines(raw, width, height)
    if max(pixels) >= len(palette):
        raise ValueError("PNG uses a palette index outside PLTE")
    lightness = [
        (54 * red + 183 * green + 19 * blue + 128) // 256
        for red, green, blue in palette
    ]
    return {
        "width": width,
        "height": height,
        "pixels": pixels,
        "palette_lightness": lightness,
        "palette_entries": len(palette),
        "chunk_count": chunk_count,
        "decoded_pixel_count": len(pixels),
        "crc_validated": True,
    }


def full_affine_geometry(
    records: list[dict[str, float]],
    target: dict[str, Any],
    model: dict[str, Any],
    outer_radius_craters: float,
) -> dict[str, Any]:
    crater_radius_deg = math.degrees(
        (target["diameter_km"] / 2.0) / model["moon_radius_km"]
    )
    fit_radius_deg = max(4.0, 1.35 * outer_radius_craters * crater_radius_deg)
    points: list[tuple[float, float, float, float]] = []
    for record in records:
        u, v = local_coordinates(
            record["pixel_latitude"], record["pixel_longitude"], target
        )
        if math.hypot(u, v) <= fit_radius_deg:
            points.append(
                (
                    u,
                    v,
                    record[model["image_x_field"]],
                    record[model["image_y_field"]],
                )
            )
    points.sort()
    rows = [[1.0, u, v] for u, v, _, _ in points]
    x_parameters = least_squares(rows, [x for _, _, x, _ in points])
    y_parameters = least_squares(rows, [y for _, _, _, y in points])
    determinant = (
        x_parameters[1] * y_parameters[2]
        - x_parameters[2] * y_parameters[1]
    )
    if abs(determinant) < 1e-12:
        raise ValueError("Local affine geometry is singular")
    return {
        "point_count": len(points),
        "crater_radius_deg": crater_radius_deg,
        "x_parameters": x_parameters,
        "y_parameters": y_parameters,
        "determinant": determinant,
    }


def histogram_percentile(histogram: list[int], fraction: float) -> int:
    total = sum(histogram)
    if total <= 0:
        raise ValueError("Cannot take a percentile of an empty histogram")
    threshold = math.ceil(fraction * total)
    cumulative = 0
    for value, count in enumerate(histogram):
        cumulative += count
        if cumulative >= threshold:
            return value
    raise AssertionError("Histogram percentile failed to terminate")


def histogram_auc(inner: list[int], outer: list[int]) -> float:
    inner_total = sum(inner)
    outer_total = sum(outer)
    if inner_total <= 0 or outer_total <= 0:
        raise ValueError("Cannot compute AUC from an empty region")
    outer_less = 0
    doubled_wins = 0
    for value in range(256):
        doubled_wins += inner[value] * (2 * outer_less + outer[value])
        outer_less += outer[value]
    return doubled_wins / (2.0 * inner_total * outer_total)


def score_target(
    decoded: dict[str, Any],
    geometry: dict[str, Any],
    cells: list[dict[str, Any]],
    minimum_pixels: int,
) -> dict[str, Any]:
    width = decoded["width"]
    height = decoded["height"]
    pixels = decoded["pixels"]
    lightness = decoded["palette_lightness"]
    x_parameters = geometry["x_parameters"]
    y_parameters = geometry["y_parameters"]
    determinant = geometry["determinant"]
    crater_radius_deg = geometry["crater_radius_deg"]
    maximum_radius = max(cell["outer_crater_radii"][1] for cell in cells)
    region_radius_deg = maximum_radius * crater_radius_deg
    x_extent = region_radius_deg * math.hypot(x_parameters[1], x_parameters[2])
    y_extent = region_radius_deg * math.hypot(y_parameters[1], y_parameters[2])
    minimum_column = max(0, math.floor(x_parameters[0] - x_extent) - 1)
    maximum_column = min(width - 1, math.ceil(x_parameters[0] + x_extent) + 1)
    minimum_row = max(0, math.floor(y_parameters[0] - y_extent) - 1)
    maximum_row = min(height - 1, math.ceil(y_parameters[0] + y_extent) + 1)
    histograms = {
        cell["id"]: {"inner": [0] * 256, "outer": [0] * 256}
        for cell in cells
    }
    for row in range(minimum_row, maximum_row + 1):
        delta_y = row - y_parameters[0]
        row_offset = row * width
        for column in range(minimum_column, maximum_column + 1):
            delta_x = column - x_parameters[0]
            u = (y_parameters[2] * delta_x - x_parameters[2] * delta_y) / determinant
            v = (-y_parameters[1] * delta_x + x_parameters[1] * delta_y) / determinant
            radius = math.hypot(u, v) / crater_radius_deg
            if radius >= maximum_radius:
                continue
            value = lightness[pixels[row_offset + column]]
            for cell in cells:
                inner_low, inner_high = cell["inner_crater_radii"]
                outer_low, outer_high = cell["outer_crater_radii"]
                if inner_low <= radius < inner_high:
                    histograms[cell["id"]]["inner"][value] += 1
                elif outer_low <= radius < outer_high:
                    histograms[cell["id"]]["outer"][value] += 1
    results: dict[str, Any] = {}
    for cell in cells:
        record = histograms[cell["id"]]
        inner_count = sum(record["inner"])
        outer_count = sum(record["outer"])
        if inner_count < minimum_pixels or outer_count < minimum_pixels:
            raise ValueError(
                f"Region {cell['id']} has too few pixels: {inner_count}/{outer_count}"
            )
        auc = histogram_auc(record["inner"], record["outer"])
        results[cell["id"]] = {
            "inner_pixels": inner_count,
            "outer_pixels": outer_count,
            "auc": auc,
            "local_ray_excess": auc - 0.5,
            "inner_median_code_value": histogram_percentile(record["inner"], 0.5),
            "outer_median_code_value": histogram_percentile(record["outer"], 0.5),
            "inner_p75_code_value": histogram_percentile(record["inner"], 0.75),
            "outer_p75_code_value": histogram_percentile(record["outer"], 0.75),
        }
    return {
        "geometry": {
            "control_points": geometry["point_count"],
            "crater_radius_deg": crater_radius_deg,
            "predicted_center": [x_parameters[0], y_parameters[0]],
            "crop": [minimum_column, minimum_row, maximum_column, maximum_row],
        },
        "cells": results,
    }


def compare_view(
    glushko: dict[str, Any],
    ohm: dict[str, Any],
    cells: list[dict[str, Any]],
    oracle: dict[str, Any],
    include_direct_same_frame: bool,
) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for cell in cells:
        cell_id = cell["id"]
        glushko_cell = glushko["cells"][cell_id]
        ohm_cell = ohm["cells"][cell_id]
        glushko_excess = glushko_cell["local_ray_excess"]
        ohm_excess = ohm_cell["local_ray_excess"]
        similarity = (
            min(glushko_excess, ohm_excess) / max(glushko_excess, ohm_excess)
            if min(glushko_excess, ohm_excess) > 0
            else None
        )
        signal_pass = (
            glushko_cell["auc"] >= oracle["minimum_auc_each"]
            and ohm_cell["auc"] >= oracle["minimum_auc_each"]
        )
        similarity_pass = (
            similarity is not None and similarity >= oracle["minimum_similarity_ratio"]
        )
        direction_pass = glushko_excess > ohm_excess
        passed = signal_pass and similarity_pass and direction_pass
        comparison: dict[str, Any] = {
            "pass": passed,
            "signal_pass": signal_pass,
            "similarity_pass": similarity_pass,
            "direction_pass": direction_pass,
            "similarity_ratio": similarity,
            "glushko": glushko_cell,
            "ohm": ohm_cell,
        }
        if include_direct_same_frame:
            glushko_p75 = glushko_cell["inner_p75_code_value"]
            ohm_p75 = ohm_cell["inner_p75_code_value"]
            comparison["descriptive_same_frame_inner_p75"] = {
                "glushko": glushko_p75,
                "ohm": ohm_p75,
                "similarity_ratio": min(glushko_p75, ohm_p75)
                / max(glushko_p75, ohm_p75),
                "glushko_greater_than_ohm": glushko_p75 > ohm_p75,
                "controls_disposition": False,
            }
        comparisons[cell_id] = comparison
    passing_cells = sum(record["pass"] for record in comparisons.values())
    primary_pass = comparisons[oracle["required_primary_cell_id"]]["pass"]
    return {
        "pass": primary_pass
        and passing_cells >= oracle["minimum_passing_cells_per_view"],
        "primary_cell_pass": primary_pass,
        "passing_cells": passing_cells,
        "total_cells": len(cells),
        "glushko_geometry": glushko["geometry"],
        "ohm_geometry": ohm["geometry"],
        "cells": comparisons,
    }


def verify_sources(
    root: Path, source_mutation: str | None = None
) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage8c.json")
    if source_mutation == "tamper_joint_image_hash":
        spec = copy.deepcopy(spec)
        for source in spec["source_files"]:
            if source["role"] == "joint_image":
                source["sha256"] = "0" * 64
    elif source_mutation is not None:
        raise ValueError(f"Unknown source mutation: {source_mutation}")
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    formation = verify_formation(root)
    add_check(
        checks,
        errors,
        "committed_formation_gate",
        formation["pass"],
        "The committed Stage 8C formation gate failed.",
    )
    source_identity_ok = all(
        (root / source["path"]).is_file()
        and sha256_file(root / source["path"]) == source["sha256"]
        for source in spec["source_files"]
    )
    add_check(
        checks,
        errors,
        "hash_pinned_offline_sources",
        source_identity_ok,
        "A frozen Stage 8C source is missing or changed.",
    )
    if errors:
        return {
            "testbed_id": spec["testbed_id"],
            "source_mutation": source_mutation,
            "pass": False,
            "evidence_state": spec["oracle"]["indeterminate_state"],
            "disposition": "STOP_REPAIR_NAMED_SOURCE_ONLY",
            "views": {},
            "verification_network_bytes": 0,
            "claim_ceiling": spec["claim_ceiling"],
            "next_step_logic": spec["next_step_logic"],
            "checks": checks,
            "errors": errors,
        }

    source_by_role = {item["role"]: item for item in spec["source_files"]}
    model = spec["coordinate_model"]
    cells = spec["region_cells"]
    maximum_radius = max(cell["outer_crater_radii"][1] for cell in cells)
    minimum_pixels = model["minimum_pixels_per_region"]
    decoded_receipts: dict[str, Any] = {}
    try:
        joint_decoded = decode_indexed_png(root / source_by_role["joint_image"]["path"])
        decoded_receipts["joint_image"] = {
            key: joint_decoded[key]
            for key in (
                "width",
                "height",
                "palette_entries",
                "chunk_count",
                "decoded_pixel_count",
                "crc_validated",
            )
        }
        joint_records = pixel_intercepts(root / source_by_role["joint_label"]["path"])
        joint_glushko = score_target(
            joint_decoded,
            full_affine_geometry(
                joint_records, spec["targets"]["glushko"], model, maximum_radius
            ),
            cells,
            minimum_pixels,
        )
        joint_ohm = score_target(
            joint_decoded,
            full_affine_geometry(
                joint_records, spec["targets"]["ohm"], model, maximum_radius
            ),
            cells,
            minimum_pixels,
        )
        del joint_decoded

        glushko_decoded = decode_indexed_png(
            root / source_by_role["matched_glushko_image"]["path"]
        )
        decoded_receipts["matched_glushko_image"] = {
            key: glushko_decoded[key]
            for key in (
                "width",
                "height",
                "palette_entries",
                "chunk_count",
                "decoded_pixel_count",
                "crc_validated",
            )
        }
        matched_glushko = score_target(
            glushko_decoded,
            full_affine_geometry(
                pixel_intercepts(root / source_by_role["matched_glushko_label"]["path"]),
                spec["targets"]["glushko"],
                model,
                maximum_radius,
            ),
            cells,
            minimum_pixels,
        )
        del glushko_decoded

        ohm_decoded = decode_indexed_png(
            root / source_by_role["matched_ohm_image"]["path"]
        )
        decoded_receipts["matched_ohm_image"] = {
            key: ohm_decoded[key]
            for key in (
                "width",
                "height",
                "palette_entries",
                "chunk_count",
                "decoded_pixel_count",
                "crc_validated",
            )
        }
        matched_ohm = score_target(
            ohm_decoded,
            full_affine_geometry(
                pixel_intercepts(root / source_by_role["matched_ohm_label"]["path"]),
                spec["targets"]["ohm"],
                model,
                maximum_radius,
            ),
            cells,
            minimum_pixels,
        )
        del ohm_decoded
    except (KeyError, OSError, ValueError, zlib.error) as error:
        errors.append(f"Camera scoring failed: {error}")
        return {
            "testbed_id": spec["testbed_id"],
            "source_mutation": source_mutation,
            "pass": False,
            "evidence_state": spec["oracle"]["indeterminate_state"],
            "disposition": "STOP_REPAIR_NAMED_GEOMETRY_OR_DECODER_DEFECT_ONLY",
            "views": {},
            "verification_network_bytes": 0,
            "claim_ceiling": spec["claim_ceiling"],
            "next_step_logic": spec["next_step_logic"],
            "checks": checks,
            "errors": errors,
        }

    add_check(
        checks,
        errors,
        "crc_validated_three_image_decode",
        len(decoded_receipts) == 3
        and all(item["crc_validated"] for item in decoded_receipts.values())
        and all(item["decoded_pixel_count"] == 5568 * 3712 for item in decoded_receipts.values()),
        "One of the three frozen PNGs did not decode under the CRC-validated contract.",
        images=decoded_receipts,
    )
    joint_view = compare_view(
        joint_glushko, joint_ohm, cells, spec["oracle"], include_direct_same_frame=True
    )
    pair_view = compare_view(
        matched_glushko,
        matched_ohm,
        cells,
        spec["oracle"],
        include_direct_same_frame=False,
    )
    views = {"joint_same_frame": joint_view, "matched_400mm_pair": pair_view}
    complete_scores = all(
        record["glushko"]["inner_pixels"] >= minimum_pixels
        and record["glushko"]["outer_pixels"] >= minimum_pixels
        and record["ohm"]["inner_pixels"] >= minimum_pixels
        and record["ohm"]["outer_pixels"] >= minimum_pixels
        for view in views.values()
        for record in view["cells"].values()
    )
    add_check(
        checks,
        errors,
        "complete_frozen_regions_and_oracle",
        complete_scores,
        "A frozen region did not meet its minimum pixel or complete-score contract.",
        views={
            key: {
                "pass": value["pass"],
                "primary_cell_pass": value["primary_cell_pass"],
                "passing_cells": value["passing_cells"],
            }
            for key, value in views.items()
        },
    )

    oracle = spec["oracle"]
    if errors:
        evidence_state = oracle["indeterminate_state"]
        disposition = "STOP_REPAIR_NAMED_GEOMETRY_OR_DECODER_DEFECT_ONLY"
    elif joint_view["pass"] and pair_view["pass"]:
        evidence_state = oracle["strong_state"]
        disposition = "CONTINUE_BOUNDED_CONFOUND_PRESSURE_TEST"
    elif joint_view["pass"]:
        evidence_state = oracle["joint_only_state"]
        disposition = "RETAIN_JOINT_ONLY_STOP_IMAGE_SELECTION"
    elif pair_view["pass"]:
        evidence_state = oracle["pair_only_state"]
        disposition = "STOP_PAIR_INSUFFICIENT_WITHOUT_JOINT"
    else:
        evidence_state = oracle["discordant_state"]
        disposition = "CLOSE_CAMERA_NATIVE_GLUSHKO_OHM_LANE"
    return {
        "testbed_id": spec["testbed_id"],
        "source_mutation": source_mutation,
        "pass": not errors,
        "evidence_state": evidence_state,
        "disposition": disposition,
        "views": views,
        "verification_network_bytes": 0,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 8C — Camera-Native Ordinal Canary",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Verification network bytes: `{result['verification_network_bytes']}`",
        "",
    ]
    view_labels = {
        "joint_same_frame": "Joint Same Frame",
        "matched_400mm_pair": "Matched 400 mm Pair",
    }
    for view_name, view in result.get("views", {}).items():
        lines.extend(
            [
                f"## {view_labels.get(view_name, view_name.replace('_', ' ').title())}",
                "",
                f"- Complete view pass: `{view['pass']}`",
                f"- Primary cell pass: `{view['primary_cell_pass']}`",
                f"- Passing robustness cells: `{view['passing_cells']} / {view['total_cells']}`",
                "",
                "| Cell | Glushko AUC | Ohm AUC | Similarity | Direction | Pass |",
                "| --- | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for cell_id, cell in view["cells"].items():
            similarity = (
                f"{cell['similarity_ratio']:.6f}"
                if cell["similarity_ratio"] is not None
                else "undefined"
            )
            lines.append(
                f"| `{cell_id}` | {cell['glushko']['auc']:.6f} | {cell['ohm']['auc']:.6f} | {similarity} | "
                f"{'Glushko > Ohm' if cell['direction_pass'] else 'not Glushko > Ohm'} | `{cell['pass']}` |"
            )
        lines.append("")
    if result["evidence_state"] == "NO_CAMERA_NATIVE_ORDINAL_CONCORDANCE":
        lines.extend(
            [
                "## Result",
                "",
                "All six frozen cells preserve the Glushko-greater-than-Ohm direction, but none passes the complete two-target signal and similarity oracle. Direction alone does not reproduce Hansen's compound comparison, so the exact camera-native lane closes without retuning.",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation boundary",
            "",
            result["claim_ceiling"],
            "",
            "## Next-step logic",
            "",
            f"- Strong: {result['next_step_logic']['if_strong']}",
            f"- Joint only: {result['next_step_logic']['if_joint_only']}",
            f"- Pair only: {result['next_step_logic']['if_pair_only']}",
            f"- Discordant: {result['next_step_logic']['if_discordant']}",
            f"- Indeterminate: {result['next_step_logic']['if_indeterminate']}",
            f"- Cross-lanes: {result['next_step_logic']['cross_lanes']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
        result = verify_sources(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
