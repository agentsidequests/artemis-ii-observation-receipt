#!/usr/bin/env python3
"""Verify the frozen Stage 8B actual-stimulus recoverability gate."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


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


def transcript_text(path: Path) -> str:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return " ".join(row.get("text", "") for row in csv.DictReader(handle))


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    spec = copy.deepcopy(spec)
    if mutation is None:
        return spec
    if mutation == "reopen_or_retune_stage8a":
        spec["prior_stage_boundary"]["forbidden_reopenings"] = []
    elif mutation == "treat_target_tags_as_proof_of_visible_content":
        spec["recoverability_dimensions"]["B_named_target_content_visible"] = (
            "Official target tags alone prove visible content."
        )
    elif mutation == "treat_processed_camera_image_as_retinal_stimulus":
        spec["claim_ceiling"] = "The processed camera image is Hansen's retinal stimulus."
    elif mutation == "infer_spacecraft_geometry_from_clock_directions":
        spec["recoverability_dimensions"]["E_spacecraft_and_view_geometry"] = (
            "Infer geometry from transcript clock directions."
        )
    elif mutation == "assume_unreleased_spice_exists":
        spec["official_archive"]["spice_state_at_formation"] = (
            "Assume complete SPICE is released."
        )
    elif mutation == "select_alternate_exposure_after_seeing_outcome_without_trigger":
        spec["fallback_rule"] = "Choose whichever exposure looks best after inspection."
    elif mutation == "ignore_window_angle_or_visual_adaptation":
        spec["recoverability_dimensions"]["F_human_optical_mapping"] = (
            "Ignore window angle and visual adaptation."
        )
    elif mutation == "claim_camera_proxy_reconstructs_human_perception":
        spec["next_step_logic"]["if_camera_proxy"] = (
            "Call the camera proxy Hansen's reconstructed perception."
        )
    elif mutation == "expand_to_bulk_archive_search_after_frozen_three_scene_gate":
        spec["inspection_contract"]["maximum_primary_browse_images"] = 100
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec


def verify_formation(root: Path, mutation: str | None = None) -> dict[str, Any]:
    raw = load_json(root / "spec" / "stage8b.json")
    spec = apply_mutation(raw, mutation)
    receipt = load_json(root / "evidence" / "stage8b" / "formation-receipt.json")
    correction = load_json(root / receipt["formation_time_correction_path"])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    spec_hash = sha256_file(root / "spec" / "stage8b.json")
    current_spec_bytes = (root / "spec" / "stage8b.json").read_bytes()
    reconstructed_original_bytes = current_spec_bytes.replace(
        correction["corrected_formed_at_utc"].encode(),
        correction["original_formed_at_utc"].encode(),
        1,
    )
    correction_ok = (
        correction["classification"]
        == "REPRESENTATION_ONLY_FORMATION_TIME_CORRECTION"
        and correction["corrected_spec_sha256"] == spec_hash
        and hashlib.sha256(reconstructed_original_bytes).hexdigest()
        == correction["original_spec_sha256"]
        == receipt["original_formation_spec_sha256"]
        and correction["changed_fields"] == ["formed_at_utc"]
        and correction["formation_commit"]
        == "45804fa0472e21ef6e2a6a9bb07e6eec82d88a7d"
        and correction["formation_commit_time"] == "2026-10-09T17:31:36-05:00"
        and correction["corrected_formed_at_utc"] == raw["formed_at_utc"]
        and correction["selected_products_changed"] is False
        and correction["oracle_changed"] is False
        and correction["inspection_contract_changed"] is False
        and correction["hard_negatives_changed"] is False
        and correction["next_step_logic_changed"] is False
        and correction["browse_images_inspected_before_formation_commit"] == 0
        and correction["source_acquisition_began_after_formation_commit"] is True
    )
    identity_ok = (
        receipt["spec_sha256"] == spec_hash
        and correction_ok
        and receipt["browse_pixel_bytes_accessed_before_formation"] == 0
        and receipt["browse_images_inspected_before_formation"] == 0
        and spec["inspection_contract"]["pixel_access_before_formation"] == 0
    )
    add_check(
        checks,
        errors,
        "pre_pixel_freeze_and_identity",
        identity_ok,
        "The gate was not hash-bound before browse-pixel access.",
        spec_sha256=spec_hash,
    )

    transcript_ok = True
    transcript_details: list[dict[str, Any]] = []
    for source in spec["transcript_sources"]:
        path = root / source["path"]
        actual_hash = sha256_file(path) if path.is_file() else None
        text = transcript_text(path).lower() if path.is_file() else ""
        missing = [anchor for anchor in source["required_anchors"] if anchor.lower() not in text]
        valid = actual_hash == source["sha256"] and not missing
        transcript_ok = transcript_ok and valid
        transcript_details.append(
            {
                "id": source["id"],
                "sha256": actual_hash,
                "missing_anchors": missing,
                "pass": valid,
            }
        )
    add_check(
        checks,
        errors,
        "transcript_identity_and_anchors",
        transcript_ok,
        "A transcript identity or decision-bearing anchor changed.",
        sources=transcript_details,
    )

    products = {item["role"]: item for item in spec["selected_products"]}
    selected_ok = (
        set(products) == {"matched_glushko", "matched_ohm", "joint_context"}
        and products["matched_glushko"]["product_id"]
        == "art002e012219_nkd5015_prc_v01"
        and products["matched_ohm"]["product_id"]
        == "art002e012252_nkd5015_prc_v01"
        and products["joint_context"]["product_id"]
        == "art002e012264_nkd5015_prc_v01"
        and products["joint_context"]["target_tags"] == ["Glushko", "Ohm"]
        and all(item["f_number"] == 8.0 for item in products.values())
    )
    add_check(
        checks,
        errors,
        "three_predeclared_products",
        selected_ok,
        "The three predeclared product identities or roles changed.",
    )

    matched_fields = (
        "camera",
        "lens",
        "focal_length_mm",
        "f_number",
        "iso",
        "exposure_seconds",
    )
    glushko = products["matched_glushko"]
    ohm = products["matched_ohm"]
    settings_ok = all(glushko[field] == ohm[field] for field in matched_fields)
    add_check(
        checks,
        errors,
        "matched_pair_camera_state",
        settings_ok,
        "The selected Glushko and Ohm camera states are not exactly matched.",
        fields=list(matched_fields),
    )

    boundary_ok = (
        len(spec["prior_stage_boundary"]["forbidden_reopenings"]) == 4
        and spec["prior_stage_boundary"]["required_stage8a_evidence_state"]
        == "NO_REFLECTANCE_CONCORDANCE"
        and "Do not use this gate to optimize appearance" in spec["stop_rules"][1]
    )
    add_check(
        checks,
        errors,
        "stage8a_non_reopening_boundary",
        boundary_ok,
        "The failed Stage 8A lane was reopened or made tunable.",
    )

    dimensions = spec["recoverability_dimensions"]
    dimensions_ok = (
        set(dimensions)
        == {
            "A_temporal_and_provenance_binding",
            "B_named_target_content_visible",
            "C_matched_camera_state",
            "D_same_frame_joint_context",
            "E_spacecraft_and_view_geometry",
            "F_human_optical_mapping",
        }
        and "visibly support" in dimensions["B_named_target_content_visible"].lower()
        and "position" in dimensions["E_spacecraft_and_view_geometry"].lower()
        and "naked-eye" in dimensions["F_human_optical_mapping"].lower()
        and "adaptation" in dimensions["F_human_optical_mapping"].lower()
    )
    add_check(
        checks,
        errors,
        "six_dimension_recoverability_boundary",
        dimensions_ok,
        "The source, geometry, or human-mapping dimensions were weakened.",
    )

    spice_state = spec["official_archive"]["spice_state_at_formation"]
    spice_boundary_ok = (
        "anticipated date of 2026-10-10" in spice_state
        and "actual release date of TBD" in spice_state
        and "recheck trigger" in spice_state
    )
    add_check(
        checks,
        errors,
        "dated_spice_release_boundary",
        spice_boundary_ok,
        "The dated SPICE availability boundary was replaced by an assumption.",
    )

    oracle = spec["oracle"]
    oracle_ok = (
        oracle["full_human_requires"] == ["A", "B", "C", "D", "E", "F"]
        and oracle["camera_proxy_requires"] == ["A", "B", "C", "D"]
        and oracle["metadata_only_requires"] == ["A", "C"]
        and oracle["classification_order"]
        == ["indeterminate", "full_human", "camera_proxy", "metadata_only", "no_reconstruction"]
    )
    add_check(
        checks,
        errors,
        "ordered_oracle",
        oracle_ok,
        "The recoverability oracle or its precedence changed.",
    )

    inspection = spec["inspection_contract"]
    acquisition_ok = (
        inspection["maximum_primary_browse_images"] == 3
        and inspection["maximum_scene_count_including_fallbacks"] == 3
        and inspection["maximum_label_files"] == 9
        and inspection["maximum_calendar_documents"] == 1
        and inspection["maximum_total_network_bytes"] == 67108864
        and inspection["verification_network_bytes"] == 0
        and len(spec["predeclared_bracket_fallbacks"]) == 3
        and "missing, corrupt, unreadable" in spec["fallback_rule"]
    )
    add_check(
        checks,
        errors,
        "bounded_inspection_and_fallback",
        acquisition_ok,
        "The three-scene inspection or fallback budget was widened.",
    )

    ceiling = spec["claim_ceiling"].lower()
    ceiling_ok = (
        "would not reconstruct hansen's retinal stimulus" in ceiling
        and "camera as the judgment carrier" in ceiling
        and "visual adaptation" in ceiling
        and "public scientific claim" in ceiling
    )
    add_check(
        checks,
        errors,
        "claim_ceiling",
        ceiling_ok,
        "The camera-proxy or scientific claim ceiling was weakened.",
    )

    next_steps = spec["next_step_logic"]
    next_steps_ok = (
        "camera-native" in next_steps["if_camera_proxy"]
        and "do not call it Hansen's actual stimulus" in next_steps["if_camera_proxy"]
        and "New trajectory geometry may change E" in next_steps["recheck_trigger"]
        and "cannot by itself satisfy F" in next_steps["recheck_trigger"]
    )
    add_check(
        checks,
        errors,
        "branch_complete_next_step_logic",
        next_steps_ok,
        "The next-step logic no longer preserves the geometry and human-mapping limits.",
    )

    return {
        "testbed_id": spec["testbed_id"],
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": "FORMED_METADATA_ONLY_NO_PIXEL_ACCESS" if not errors else "FORMATION_FAILED",
        "disposition": "ADMIT_THREE_SCENE_SOURCE_ACQUISITION" if not errors else "STOP_REPAIR_FORMATION_ONLY",
        "browse_pixel_bytes_accessed": receipt["browse_pixel_bytes_accessed_before_formation"],
        "browse_images_inspected": receipt["browse_images_inspected_before_formation"],
        "checks": checks,
        "errors": errors,
    }


def verify_formation_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_formation(root)
    mutations = {
        mutation: verify_formation(root, mutation)
        for mutation in load_json(root / "spec" / "stage8b.json")["hard_negatives"]
    }
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "pass": baseline["pass"] and hard_negatives_pass,
        "hard_negatives_pass": hard_negatives_pass,
        "hard_negatives": mutations,
    }


def xml_values(path: Path) -> tuple[dict[str, list[str]], ET.Element]:
    root = ET.parse(path).getroot()
    values: dict[str, list[str]] = {}
    for element in root.iter():
        tag = element.tag.split("}")[-1]
        text = (element.text or "").strip()
        if text:
            values.setdefault(tag, []).append(text)
    return values, root


def pixel_intercepts(xml_root: ET.Element) -> list[dict[str, float]]:
    records: list[dict[str, float]] = []
    required = {
        "vertical_coordinate_pixel",
        "horizontal_coordinate_pixel",
        "pixel_latitude",
        "pixel_longitude",
    }
    for element in xml_root.iter():
        if element.tag.split("}")[-1] != "Pixel_Intercept":
            continue
        values = {
            child.tag.split("}")[-1]: (child.text or "").strip()
            for child in element.iter()
        }
        if required.issubset(values):
            records.append({key: float(values[key]) for key in required})
    return records


def nearest_control_point(
    records: list[dict[str, float]], latitude: float, longitude: float
) -> tuple[float, dict[str, float]]:
    def distance(record: dict[str, float]) -> float:
        delta_latitude = record["pixel_latitude"] - latitude
        delta_longitude = (
            (record["pixel_longitude"] - longitude + 180.0) % 360.0
        ) - 180.0
        return math.hypot(
            delta_latitude,
            delta_longitude * math.cos(math.radians(latitude)),
        )

    record = min(records, key=distance)
    return distance(record), record


def png_dimensions(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", header[16:24])


def artemis_spice_calendar_row(path: Path) -> dict[str, str] | None:
    spreadsheet_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    relationships_ns = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    )
    ns = {"m": spreadsheet_ns, "r": relationships_ns}
    with zipfile.ZipFile(path) as archive:
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        shared = [
            "".join(
                node.text or "" for node in item.iter() if node.tag.endswith("}t")
            )
            for item in shared_root
        ]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        targets = {
            element.attrib["Id"]: element.attrib["Target"]
            for element in relationships
        }
        sheets = workbook.find("m:sheets", ns)
        if sheets is None:
            return None
        for sheet in sheets:
            target = targets[sheet.attrib[f"{{{relationships_ns}}}id"]]
            if target.startswith("/"):
                target = target.lstrip("/")
            elif not target.startswith("xl/"):
                target = "xl/" + target
            worksheet = ET.fromstring(archive.read(target))
            for row in worksheet.findall(".//m:row", ns):
                cells: dict[str, str] = {}
                for cell in row.findall("m:c", ns):
                    value_node = cell.find("m:v", ns)
                    if value_node is None:
                        value = ""
                    elif cell.attrib.get("t") == "s":
                        value = shared[int(value_node.text or "0")]
                    else:
                        value = value_node.text or ""
                    column = "".join(
                        character
                        for character in cell.attrib.get("r", "")
                        if character.isalpha()
                    )
                    cells[column] = value
                if cells.get("B") == "Artemis II" and cells.get("C") == "SPICE":
                    return cells
    return None


def verify_sources(root: Path, source_mutation: str | None = None) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage8b.json")
    formation = verify_formation_with_mutations(root)
    receipt = load_json(root / "evidence" / "stage8b" / "acquisition-receipt.json")
    manifest = load_json(root / receipt["source_manifest_path"])
    inspection = load_json(root / receipt["inspection_record_path"])
    if source_mutation == "tamper_source_manifest_hash":
        manifest = copy.deepcopy(manifest)
        manifest["files"][0]["sha256"] = "0" * 64
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    add_check(
        checks,
        errors,
        "formed_design_and_hard_negatives",
        formation["pass"],
        "The formation or a hard-negative rejection failed.",
    )

    files_ok = True
    for item in manifest["files"]:
        path = root / item["path"]
        if (
            not path.is_file()
            or path.stat().st_size != item["bytes"]
            or sha256_file(path) != item["sha256"]
        ):
            files_ok = False
    add_check(
        checks,
        errors,
        "hash_pinned_source_manifest",
        files_ok,
        "A downloaded official source is missing, changed, or not hash-bound.",
    )

    manifest_records = {
        (item["kind"], item["product_id"]): item for item in manifest["files"]
    }
    selected_label_contracts: dict[str, dict[str, Any]] = {}
    selected_labels_ok = files_ok
    selected_xml: dict[str, tuple[dict[str, list[str]], ET.Element]] = {}
    for product in spec["selected_products"]:
        product_id = product["product_id"]
        label_record = manifest_records.get(("science_label", product_id))
        if label_record is None:
            selected_labels_ok = False
            continue
        values, xml_root = xml_values(root / label_record["path"])
        selected_xml[product_id] = (values, xml_root)
        start_time = values.get("start_date_time", [""])[0]
        target_ids = values.get("target_id", [])
        expected_targets = product["target_tags"]
        target_ok = all(
            any(target.lower() in actual.lower() for actual in target_ids)
            for target in expected_targets
        )
        contract_ok = (
            start_time.endswith(product["observed_time_utc"] + "Z")
            and values.get("file_name", [None])[0] == product["file_name"]
            and values.get("camera_name", [None])[0] == product["camera"]
            and values.get("lens_name", [None])[0] == product["lens"]
            and float(values.get("focal_length", ["nan"])[0])
            == product["focal_length_mm"]
            and float(values.get("f_number", ["nan"])[0]) == product["f_number"]
            and int(values.get("iso_number", ["-1"])[0]) == product["iso"]
            and float(values.get("exposure_duration", ["nan"])[0])
            == product["exposure_seconds"]
            and target_ok
        )
        selected_labels_ok = selected_labels_ok and contract_ok
        selected_label_contracts[product_id] = {
            "pass": contract_ok,
            "start_date_time": start_time,
            "target_ids": target_ids,
            "camera_name": values.get("camera_name", [None])[0],
            "lens_name": values.get("lens_name", [None])[0],
            "focal_length_mm": values.get("focal_length", [None])[0],
            "f_number": values.get("f_number", [None])[0],
            "iso": values.get("iso_number", [None])[0],
            "exposure_seconds": values.get("exposure_duration", [None])[0],
            "pixel_intercept_count": len(pixel_intercepts(xml_root)),
        }
    add_check(
        checks,
        errors,
        "selected_pds4_label_contracts",
        selected_labels_ok,
        "A selected PDS4 label no longer matches the frozen product, time, target, or camera-state contract.",
        products=selected_label_contracts,
    )

    product_ids = {item["product_id"] for item in spec["selected_products"]}
    inspected_ids = {item["product_id"] for item in inspection["images"]}
    image_records = [item for item in manifest["files"] if item["kind"] == "browse_image"]
    label_records = [item for item in manifest["files"] if item["kind"] == "science_label"]
    calendar_records = [item for item in manifest["files"] if item["kind"] == "release_calendar"]
    accepted_payload_bytes = sum(
        item["network_bytes_this_stage"] for item in manifest["files"]
    )
    receipt_ok = (
        receipt["status"] == "COMPLETED"
        and receipt["formation_spec_sha256"] == sha256_file(root / "spec" / "stage8b.json")
        and receipt["formation_time_correction_receipt_sha256"]
        == sha256_file(root / "evidence" / "stage8b" / "formation-time-correction-receipt.json")
        and receipt["total_network_bytes"] == accepted_payload_bytes
        and receipt["total_network_bytes"] <= spec["inspection_contract"]["maximum_total_network_bytes"]
        and receipt["verification_network_bytes"] == 0
        and len(image_records) == 3
        and len(label_records) == 9
        and len(calendar_records) == 1
        and {item["product_id"] for item in image_records} == product_ids
        and inspected_ids == product_ids
        and inspection["fallbacks_used"] == []
    )
    add_check(
        checks,
        errors,
        "bounded_three_scene_acquisition",
        receipt_ok,
        "The acquisition exceeded the frozen source, scene, fallback, or network boundary.",
        total_network_bytes=receipt.get("total_network_bytes"),
    )

    image_contracts: dict[str, Any] = {}
    pngs_ok = files_ok
    for image in inspection["images"]:
        dimensions = png_dimensions(root / image["path"])
        valid = (
            image["decode_success"] is True
            and dimensions is not None
            and list(dimensions) == image["image_dimensions"] == [5568, 3712]
            and image["named_target_content_visible"] is True
        )
        pngs_ok = pngs_ok and valid
        image_contracts[image["product_id"]] = {
            "pass": valid,
            "dimensions": list(dimensions) if dimensions else None,
        }
    add_check(
        checks,
        errors,
        "decoded_visible_browse_images",
        pngs_ok,
        "A selected browse image failed its PNG, dimension, decode, or visible-content record.",
        products=image_contracts,
    )

    target_request_record = manifest_records.get(
        ("existing_target_request", "artemis2_outgoing_target_request")
    )
    target_payload = (
        load_json(root / target_request_record["path"])
        if target_request_record is not None
        else []
    )
    official_coordinates: dict[str, tuple[float, float]] = {}
    for item in target_payload:
        properties = item.get("target_properties", {})
        name = properties.get("target_name")
        if name in {"Glushko Crater", "Ohm Crater"} and name not in official_coordinates:
            official_coordinates[name] = (
                float(properties["latitude"]),
                float(properties["longitude"]),
            )
    control_points_ok = set(official_coordinates) == {"Glushko Crater", "Ohm Crater"}
    control_point_details: dict[str, Any] = {}
    for image in inspection["images"]:
        product_id = image["product_id"]
        if product_id not in selected_xml:
            control_points_ok = False
            continue
        records = pixel_intercepts(selected_xml[product_id][1])
        control_points_ok = control_points_ok and len(records) == image["label_pixel_intercept_count"]
        targets = (
            {"Glushko Crater": image["nearest_label_control_point"]}
            if image["role"] == "matched_glushko"
            else {"Ohm Crater": image["nearest_label_control_point"]}
            if image["role"] == "matched_ohm"
            else {
                "Glushko Crater": image["nearest_label_control_points"]["glushko"],
                "Ohm Crater": image["nearest_label_control_points"]["ohm"],
            }
        )
        per_target: dict[str, Any] = {}
        for target_name, frozen in targets.items():
            distance, nearest = nearest_control_point(
                records, *official_coordinates[target_name]
            )
            valid = (
                distance <= 0.2
                and math.isclose(
                    distance, frozen["angular_separation_deg"], abs_tol=1e-12
                )
                and math.isclose(
                    nearest["pixel_latitude"], frozen["pixel_latitude_deg"], abs_tol=1e-12
                )
                and math.isclose(
                    nearest["pixel_longitude"],
                    frozen["pixel_longitude_east_deg"],
                    abs_tol=1e-12,
                )
            )
            control_points_ok = control_points_ok and valid
            per_target[target_name] = {
                "pass": valid,
                "nearest_control_point_deg": distance,
            }
        control_point_details[product_id] = per_target
    add_check(
        checks,
        errors,
        "official_coordinate_control_points",
        control_points_ok,
        "The official target coordinates no longer bind to the selected label control points.",
        products=control_point_details,
    )

    calendar_record = manifest_records.get(
        ("release_calendar", "PDS_Data_Release_Calendar_20261008_v0")
    )
    calendar_row = (
        artemis_spice_calendar_row(root / calendar_record["path"])
        if calendar_record is not None and files_ok
        else None
    )
    calendar_ok = (
        calendar_row is not None
        and calendar_row.get("F") == "46305"
        and calendar_row.get("G") == "TBD"
        and calendar_row.get("H") == "-"
    )
    add_check(
        checks,
        errors,
        "dated_artemis_spice_release_state",
        calendar_ok,
        "The official 2026-10-08 calendar no longer shows Artemis II SPICE anticipated for 2026-10-10 with actual release TBD.",
        calendar_row=calendar_row,
    )

    dimensions = inspection["dimensions"]
    dimension_keys_ok = set(dimensions) == {"A", "B", "C", "D", "E", "F"}
    inspection_fields_ok = all(
        set(spec["inspection_contract"]["required_observations_per_image"]).issubset(item)
        for item in inspection["images"]
    )
    add_check(
        checks,
        errors,
        "complete_inspection_record",
        dimension_keys_ok and inspection_fields_ok,
        "The six dimensions or required per-image observations are incomplete.",
    )

    dimension_evidence_ok = (
        dimensions["A"]["satisfied"] is True
        and dimensions["B"]["satisfied"] is True
        and dimensions["C"]["satisfied"] is True
        and dimensions["D"]["satisfied"] is True
        and dimensions["E"]["satisfied"] is False
        and dimensions["F"]["satisfied"] is False
        and "2-D fitted pixel-to-lunar-coordinate" in dimensions["E"]["evidence"]
        and "actual release date TBD" in dimensions["E"]["evidence"]
        and "naked-eye versus optical viewfinder versus display" in dimensions["F"]["evidence"]
    )
    add_check(
        checks,
        errors,
        "dimension_evidence_and_limits",
        dimension_evidence_ok,
        "The availability result no longer preserves the partial geometry or human-mapping boundary.",
    )

    evidence_indeterminate = bool(errors) or inspection.get("source_identity_ambiguous", False)
    passed_dimensions = {key for key, value in dimensions.items() if value["satisfied"] is True}
    oracle = spec["oracle"]
    if evidence_indeterminate:
        state = oracle["indeterminate_state"]
        disposition = "STOP_REPAIR_NAMED_SOURCE_OR_INSPECTION_ONLY"
    elif set(oracle["full_human_requires"]).issubset(passed_dimensions):
        state = oracle["full_human_stimulus_state"]
        disposition = "ADMIT_SEPARATE_HUMAN_STIMULUS_RECONSTRUCTION_TEST"
    elif set(oracle["camera_proxy_requires"]).issubset(passed_dimensions):
        state = oracle["camera_proxy_state"]
        disposition = "ADMIT_SEPARATE_CAMERA_NATIVE_CANARY"
    elif set(oracle["metadata_only_requires"]).issubset(passed_dimensions):
        state = oracle["metadata_only_state"]
        disposition = "STOP_IMAGE_INTERPRETATION_PRESERVE_METADATA"
    else:
        state = oracle["no_reconstruction_state"]
        disposition = "CLOSE_STIMULUS_RECOVERABILITY_LANE"

    return {
        "testbed_id": spec["testbed_id"],
        "source_mutation": source_mutation,
        "pass": not errors,
        "evidence_state": state,
        "disposition": disposition,
        "dimensions": dimensions,
        "images": inspection["images"],
        "total_network_bytes": receipt["total_network_bytes"],
        "verification_network_bytes": 0,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "checks": checks,
        "errors": errors,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 8B — Actual-Stimulus Recoverability Gate",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        "",
        "## Recoverability result",
        "",
    ]
    for key in ("A", "B", "C", "D", "E", "F"):
        record = result["dimensions"][key]
        lines.append(
            f"- **{key} — {'SATISFIED' if record['satisfied'] else 'NOT SATISFIED'}:** {record['evidence']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The archive classification is an availability result. It does not by itself validate a reconstruction or explain the failed Stage 8A reflectance proxy.",
            "",
            "## Claim ceiling",
            "",
            result["claim_ceiling"],
            "",
            "## Next-step logic",
            "",
            f"- Full human stimulus: {result['next_step_logic']['if_full_human_stimulus']}",
            f"- Camera proxy: {result['next_step_logic']['if_camera_proxy']}",
            f"- Metadata only: {result['next_step_logic']['if_metadata_only']}",
            f"- No reconstruction: {result['next_step_logic']['if_no_reconstruction']}",
            f"- Indeterminate: {result['next_step_logic']['if_indeterminate']}",
            f"- Recheck trigger: {result['next_step_logic']['recheck_trigger']}",
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
