#!/usr/bin/env python3
"""Verify the Stage 9B gray-feature source/control admission gate."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file


EXPECTED_DIMENSIONS = [
    "A_exact_event_and_recorder_identity",
    "B_synchronous_internal_camera_coverage",
    "C_earth_emergence_temporal_progression",
    "D_rigid_terrain_control",
    "E_observer_window_carrier_binding",
    "F_cabin_window_optical_control",
    "G_external_comparable_carrier",
    "H_event_geometry",
    "I_calibrated_faint_source_response",
]
EXPECTED_STATUSES = [
    "PASS",
    "PASS",
    "PASS",
    "PARTIAL",
    "PARTIAL",
    "FAIL",
    "FAIL",
    "FAIL",
    "FAIL",
]
EVENT_FRAME_IDS = [
    "art002e025029_nkd5015_raw_v01",
    "art002e025030_nkd5015_raw_v01",
    "art002e025031_nkd5015_raw_v01",
    "art002e025032_nkd5015_raw_v01",
    "art002e025033_nkd5015_raw_v01",
]
EVENT_TIMES = [
    "2026-04-06T23:22:39.030Z",
    "2026-04-06T23:22:39.130Z",
    "2026-04-06T23:22:39.220Z",
    "2026-04-06T23:22:39.310Z",
    "2026-04-06T23:22:39.400Z",
]
EVENT_SETTINGS = [
    ("400", "0.001", "8.0", "400.0"),
    ("400", "5.0E-4", "11.0", "400.0"),
    ("400", "6.25E-4", "10.0", "400.0"),
    ("400", "0.00125", "7.1", "400.0"),
    ("400", "0.002", "5.6", "400.0"),
]
EXPECTED_STATE = "VERIFIED_SOURCE_CONTROL_STOP"
EXPECTED_DISPOSITION = "SOURCE_CONTROL_INSUFFICIENT"
EXPECTED_LANE = "CLOSE_GRAY_FEATURE_IMAGE_LANE_AT_CURRENT_ARCHIVE_BOUNDARY"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


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


def parse_utc(value: str) -> datetime:
    value = value.replace(" ", "T").replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def first_text(root: ET.Element, local_name: str) -> str | None:
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == local_name:
            return element.text.strip() if element.text else ""
    return None


def pds_value(source: dict[str, Any], key: str) -> str | None:
    value = source.get("pds4_label", {}).get(key)
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value) if value is not None else None


def set_dimension(assessment: dict[str, Any], dimension_id: str, **updates: Any) -> None:
    for dimension in assessment["dimensions"]:
        if dimension["id"] == dimension_id:
            dimension.update(updates)
            return
    raise ValueError(f"Unknown dimension: {dimension_id}")


def apply_mutation(
    spec: dict[str, Any],
    assessment: dict[str, Any],
    manifest: dict[str, Any],
    mutation: str | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    spec = copy.deepcopy(spec)
    assessment = copy.deepcopy(assessment)
    manifest = copy.deepcopy(manifest)
    if mutation is None:
        return spec, assessment, manifest
    if mutation == "substitute_overlapping_pcd2_for_exact_pcd3_event_source":
        assessment["event"]["exact_transcript_product"] = (
            "art002a000049_pcd2_trn-csv_v01.csv"
        )
    elif mutation == "treat_time_alignment_as_operator_and_window_binding":
        set_dimension(
            assessment,
            "E_observer_window_carrier_binding",
            status="PASS",
            evidence="Timestamp agreement proves Koch operated this camera through the modeled window.",
        )
    elif mutation == "open_candidate_pixels_after_source_control_failure":
        spec["access_boundary"]["new_candidate_pixel_bytes"] = 1
        manifest["new_candidate_pixel_bytes"] = 1
        manifest["pixel_payloads_opened"] = ["event-frame.tif"]
    elif mutation == (
        "treat_external_camera_absence_as_refutation_without_sensitivity_equivalence"
    ):
        set_dimension(
            assessment,
            "G_external_comparable_carrier",
            status="PASS",
            evidence="A blank SAW frame refutes the crew report.",
        )
    elif mutation == "treat_any_external_feature_as_lunar_dust":
        spec["expected_result"]["claim_ceiling"] = (
            "Any feature in the external frame confirms lunar dust."
        )
    elif mutation == "ignore_documented_cabin_reflections":
        set_dimension(
            assessment,
            "F_cabin_window_optical_control",
            status="PASS",
            evidence="Cabin and window effects can be ignored.",
        )
    elif mutation == "promote_partial_terrain_control_to_exact_event_geometry":
        set_dimension(
            assessment,
            "D_rigid_terrain_control",
            status="PASS",
            evidence="The earlier terrain match supplies exact geometry for every event frame.",
        )
    elif mutation == "let_spice_alone_repair_window_and_sensitivity_gaps":
        spec["next_step_logic"]["recheck_trigger"] = (
            "Reopen as soon as SPICE is released; SPICE satisfies every missing control."
        )
    elif mutation == "treat_synchronized_d5_burst_as_calibrated_low_light_measurement":
        set_dimension(
            assessment,
            "I_calibrated_faint_source_response",
            status="PASS",
            evidence="The exposure bracket is a calibrated low-light measurement.",
        )
    elif mutation == "claim_source_control_insufficiency_means_no_lunar_dust":
        spec["expected_result"]["claim_ceiling"] = (
            "Source-control insufficiency proves that there was no lunar dust."
        )
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return spec, assessment, manifest


def verify_stage9b(root: Path, mutation: str | None = None) -> dict[str, Any]:
    raw_spec = load_json(root / "spec" / "stage9b.json")
    evidence = raw_spec["evidence"]
    manifest_path = root / evidence["source_manifest_path"]
    extracts_path = root / evidence["source_extracts_path"]
    assessment_path = root / evidence["control_assessment_path"]
    raw_manifest = load_json(manifest_path)
    extracts = load_json(extracts_path)
    raw_assessment = load_json(assessment_path)
    spec, assessment, manifest = apply_mutation(
        raw_spec, raw_assessment, raw_manifest, mutation
    )
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    evidence_identity_ok = (
        sha256_file(manifest_path) == evidence["source_manifest_sha256"]
        and sha256_file(extracts_path) == evidence["source_extracts_sha256"]
        and sha256_file(assessment_path) == evidence["control_assessment_sha256"]
    )
    add_check(
        checks,
        errors,
        "frozen_evidence_identity",
        evidence_identity_ok,
        error="A Stage 9B evidence owner changed.",
    )

    manifest_errors: list[str] = []
    for record in manifest.get("files", []) + manifest.get("reused_files", []):
        path = root / record["path"]
        if not path.is_file():
            manifest_errors.append(f"missing:{record['path']}")
            continue
        if path.stat().st_size != record["bytes"]:
            manifest_errors.append(f"bytes:{record['path']}")
        if sha256_file(path) != record["sha256"]:
            manifest_errors.append(f"sha256:{record['path']}")
    retained_bytes = sum(item["bytes"] for item in manifest.get("files", []))
    manifest_ok = (
        not manifest_errors
        and retained_bytes == manifest.get("retained_source_bytes") == 977121
    )
    add_check(
        checks,
        errors,
        "source_manifest_and_hashes",
        manifest_ok,
        error="A retained or reused source failed identity verification.",
        retained_source_bytes=retained_bytes,
        manifest_errors=manifest_errors,
    )

    access = spec.get("access_boundary", {})
    no_pixels_ok = (
        access.get("new_candidate_pixel_bytes") == 0
        and access.get("existing_candidate_pixels_opened_for_stage9b") is False
        and access.get("pixel_payloads_retained") == 0
        and manifest.get("new_candidate_pixel_bytes") == 0
        and manifest.get("pixel_payloads_opened") == []
    )
    add_check(
        checks,
        errors,
        "zero_candidate_pixel_access",
        no_pixels_ok,
        error="Stage 9B opened or retained candidate pixel payloads.",
        new_candidate_pixel_bytes=access.get("new_candidate_pixel_bytes"),
    )

    source_dir = root / "evidence" / "stage9b" / "source"
    inventory_text = (source_dir / "collection_data_transcripts_pcd_inventory.csv").read_text(
        encoding="utf-8-sig"
    )
    transcript_path = source_dir / "art002a000015_pcd3_trn-csv_v01.csv"
    with transcript_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    row_by_time = {row["utc"]: row for row in rows}
    exact_transcript_ok = (
        "art002a000015_pcd3_trn-csv.csv::1.0" in inventory_text
        and "art002a000049_pcd2_trn-csv.csv::1.0" in inventory_text
        and assessment["event"]["exact_transcript_product"]
        == "art002a000015_pcd3_trn-csv_v01.csv"
        and row_by_time.get("2026-04-06 23:22:39.010", {}).get("speaker") == "Koch"
        and row_by_time.get("2026-04-06 23:22:39.010", {}).get("text")
        == "There's some lofted dust."
        and "gray where it was popping out"
        in row_by_time.get("2026-04-06 23:22:41.594", {}).get("text", "")
        and "could just be an optical"
        in row_by_time.get("2026-04-06 23:22:47.702", {}).get("text", "")
    )
    add_check(
        checks,
        errors,
        "exact_pcd3_event_transcript",
        exact_transcript_ok,
        error="The exact PCD3 event transcript or its decisive cues are missing.",
    )

    transcript_text = " ".join(row["text"] for row in rows).lower()
    reflection_ok = all(
        phrase in transcript_text
        for phrase in (
            "this is what's reflecting for me right now",
            "that got rid of a lot of that reflections",
            "you can't make the sun not reflect",
        )
    )
    add_check(
        checks,
        errors,
        "same_recording_reflection_counterevidence",
        reflection_ok,
        error="The same-recording cabin-reflection counterevidence was omitted.",
    )

    transcript_label = ET.parse(
        source_dir / "art002a000015_pcd3_trn-csv_v01.xml"
    ).getroot()
    audio_label = ET.parse(source_dir / "art002a000015_pcd3_raw_v01.xml").getroot()
    audio_identity_ok = (
        "art002a000015_pcd3_trn-csv"
        in (first_text(transcript_label, "logical_identifier") or "")
        and "art002a000015_pcd3_raw"
        in (first_text(audio_label, "logical_identifier") or "")
        and first_text(transcript_label, "start_date_time")
        == "2026-04-06T23:13:37.428Z"
        and first_text(transcript_label, "stop_date_time")
        == "2026-04-06T23:23:39.992Z"
        and first_text(audio_label, "start_date_time") == "2026-04-06T23:13:36Z"
        and first_text(audio_label, "stop_date_time") == "2026-04-06T23:23:42Z"
    )
    add_check(
        checks,
        errors,
        "pcd3_label_and_audio_interval",
        audio_identity_ok,
        error="The PCD3 transcript/audio label identity or event coverage changed.",
    )

    query = load_json(source_dir / "atlas-event-window-query.json")
    atlas = load_json(source_dir / "atlas-event-window-response.json")
    hits = atlas.get("hits", {}).get("hits", [])
    total = atlas.get("hits", {}).get("total", {}).get("value")
    crew_hits = [
        hit
        for hit in hits
        if hit.get("_source", {}).get("bundle_id") == "artemis2_crew_camera"
        and hit.get("_source", {}).get("collection_id") == "data_raw"
    ]
    external_hits = [
        hit
        for hit in hits
        if hit.get("_source", {}).get("bundle_id") == "artemis2_orion_camera"
        and hit.get("_source", {}).get("collection_id") == "data_raw_image"
    ]
    range_clause = query["query"]["bool"]["must"][1]["range"][
        "gather.time.start_time"
    ]
    atlas_complete_ok = (
        total == len(hits) == 41
        and len(crew_hits) == 40
        and len(external_hits) == 1
        and range_clause
        == {
            "gte": "2026-04-06T23:22:37Z",
            "lte": "2026-04-06T23:22:49.5Z",
        }
        and query.get("size") == 100
    )
    add_check(
        checks,
        errors,
        "complete_bounded_atlas_window",
        atlas_complete_ok,
        error="The bounded Atlas query is incomplete, widened, or not fully returned.",
        total_hits=total,
        returned_hits=len(hits),
        crew_raw_hits=len(crew_hits),
        external_raw_hits=len(external_hits),
    )

    crew_hits.sort(key=lambda hit: hit["_source"]["gather"]["time"]["start_time"])
    crew_first = crew_hits[0]["_source"]["gather"]["time"]["start_time"]
    crew_last = crew_hits[-1]["_source"]["gather"]["time"]["start_time"]
    atlas_by_stem = {
        hit["_source"]["gather"]["pds_archive"]["file_name"].removesuffix(".tif"): hit[
            "_source"
        ]
        for hit in crew_hits
    }
    event_records: list[dict[str, str | None]] = []
    for frame_id in EVENT_FRAME_IDS:
        source = atlas_by_stem.get(frame_id, {})
        event_records.append(
            {
                "id": frame_id,
                "time": source.get("gather", {}).get("time", {}).get("start_time"),
                "iso": pds_value(source, "img:ISO/img:iso_number"),
                "exposure": pds_value(source, "img:Exposure/img:exposure_duration"),
                "f_number": pds_value(source, "img:Optical_Properties/img:f_number"),
                "focal": pds_value(source, "img:Optical_Properties/img:focal_length"),
            }
        )
    event_burst_ok = (
        crew_first == "2026-04-06T23:22:37.530Z"
        and crew_last == "2026-04-06T23:22:49.330Z"
        and [item["time"] for item in event_records] == EVENT_TIMES
        and [
            (item["iso"], item["exposure"], item["f_number"], item["focal"])
            for item in event_records
        ]
        == EVENT_SETTINGS
    )
    add_check(
        checks,
        errors,
        "synchronous_five_exposure_d5_burst",
        event_burst_ok,
        error="The exact event-time D5 burst or exposure sequence changed.",
        crew_first_utc=crew_first,
        crew_last_utc=crew_last,
        event_records=event_records,
    )

    label_records: list[dict[str, str | None]] = []
    for frame_id, expected_time, expected_settings in zip(
        EVENT_FRAME_IDS, EVENT_TIMES, EVENT_SETTINGS, strict=True
    ):
        label_path = source_dir / f"{frame_id}.xml"
        label = ET.parse(label_path).getroot()
        record = {
            "id": frame_id,
            "time": first_text(label, "start_date_time"),
            "serial": first_text(label, "instrument_serial_number"),
            "iso": first_text(label, "iso_number"),
            "exposure": first_text(label, "exposure_duration"),
            "f_number": first_text(label, "f_number"),
            "focal": first_text(label, "focal_length"),
            "activity": first_text(label, "activity_id"),
        }
        label_records.append(record)
    label_contracts_ok = all(
        record["time"] == expected_time.replace(".030Z", ".03Z")
        if index == 0
        else record["time"] == expected_time.replace(".130Z", ".13Z")
        if index == 1
        else record["time"] == expected_time.replace(".220Z", ".22Z")
        if index == 2
        else record["time"] == expected_time.replace(".310Z", ".31Z")
        if index == 3
        else record["time"] == expected_time.replace(".400Z", ".40Z")
        for index, (record, expected_time) in enumerate(zip(label_records, EVENT_TIMES))
    ) and all(
        record["serial"] == "3500015"
        and record["activity"] == "23_Earthrise"
        and (
            record["iso"],
            record["exposure"],
            record["f_number"],
            record["focal"],
        )
        == expected_settings
        for record, expected_settings in zip(label_records, EVENT_SETTINGS)
    )
    add_check(
        checks,
        errors,
        "event_label_contracts",
        label_contracts_ok,
        error="An exact D5 event label disagrees with the Atlas event burst.",
        labels=label_records,
    )

    saw_path = root / "evidence" / "stage2a" / "source" / "art002e016299_saw3_raw_v01.xml"
    saw = ET.parse(saw_path).getroot()
    saw_time = first_text(saw, "start_date_time")
    saw_settings = (
        first_text(saw, "iso_number"),
        first_text(saw, "exposure_duration"),
        first_text(saw, "f_number"),
        first_text(saw, "focal_length"),
    )
    saw_ok = saw_time == "2026-04-06T23:22:44Z" and saw_settings == (
        "100",
        "3.8402457757296467E-4",
        "2.8",
        "3.0",
    )
    add_check(
        checks,
        errors,
        "external_saw_carrier_contract",
        saw_ok,
        error="The near-time external SAW carrier metadata changed.",
        time_utc=saw_time,
        settings=saw_settings,
    )

    report_time = parse_utc(assessment["event"]["report_time_utc"])
    first_event_time = parse_utc(EVENT_TIMES[0])
    saw_event_time = parse_utc(saw_time or "")
    first_offset = (first_event_time - report_time).total_seconds()
    saw_offset = (saw_event_time - report_time).total_seconds()
    timing_ok = (
        abs(first_offset - assessment["coverage"]["event_bracket_first_offset_seconds"])
        < 1e-9
        and abs(saw_offset - assessment["coverage"]["external_frame_offset_seconds"])
        < 1e-9
    )
    add_check(
        checks,
        errors,
        "event_carrier_time_offsets",
        timing_ok,
        error="A frozen event-to-carrier time offset changed.",
        first_d5_offset_seconds=first_offset,
        saw_offset_seconds=saw_offset,
    )

    html = (
        source_dir / "pds-artemis2-mission-page-2026-10-09.html"
    ).read_text(encoding="utf-8-sig")
    findings = " ".join(item.get("finding", "") for item in extracts.get("sources", []))
    source_limits_ok = all(
        anchor in findings.lower()
        for anchor in (
            "no lofted dust or exospheric glow was definitively detected",
            "14.2 seconds later",
            "dedicated low-light camera",
            "complete three-pane stack could not be performed",
            "pcd3 recorded koch and wiseman",
        )
    ) and all(
        anchor in html
        for anchor in (
            "The Artemis II science\n   data archive is released",
            "The SPICE bundle at the",
            "NAIF node is delayed",
        )
    )
    add_check(
        checks,
        errors,
        "primary_source_limits_and_current_release_state",
        source_limits_ok,
        error="A decision-bearing NASA source limit or current release state is missing.",
    )

    dimensions = assessment.get("dimensions", [])
    dimension_ids = [item.get("id") for item in dimensions]
    statuses = [item.get("status") for item in dimensions]
    required_all_pass = all(
        item.get("status") == "PASS" for item in dimensions if item.get("required")
    )
    dimension_ok = (
        dimension_ids == EXPECTED_DIMENSIONS
        and statuses == EXPECTED_STATUSES
        and all(item.get("required") is True for item in dimensions)
        and required_all_pass is False
        and assessment.get("admitted") is False
        and assessment.get("evidence_state") == EXPECTED_STATE
        and assessment.get("disposition") == EXPECTED_DISPOSITION
        and assessment.get("lane_state") == EXPECTED_LANE
    )
    add_check(
        checks,
        errors,
        "all_required_dimensions_fail_closed",
        dimension_ok,
        error="The four-way admission oracle was weakened or the failed gate was admitted.",
        statuses=dict(zip(dimension_ids, statuses)),
    )

    ceiling = spec.get("expected_result", {}).get("claim_ceiling", "")
    ceiling_lower = ceiling.lower()
    ceiling_ok = all(
        phrase in ceiling_lower
        for phrase in (
            "does not inspect event pixels",
            "detect or exclude lunar dust",
            "refute koch",
            "public scientific finding",
        )
    ) and not any(
        phrase in ceiling_lower
        for phrase in (
            "confirms lunar dust",
            "proves that there was no lunar dust",
        )
    )
    add_check(
        checks,
        errors,
        "claim_ceiling",
        ceiling_ok,
        error="Stage 9B was promoted into a dust, refutation, or pixel-content claim.",
        claim_ceiling=ceiling,
    )

    next_logic = spec.get("next_step_logic", {})
    next_text = " ".join(str(value) for value in next_logic.values()).lower()
    next_logic_ok = all(
        phrase in next_text
        for phrase in (
            "measurement-design gap",
            "keep every gray-feature candidate pixel closed",
            "spice alone",
            "cannot satisfy the optical or sensitivity controls",
        )
    )
    add_check(
        checks,
        errors,
        "next_step_logic",
        next_logic_ok,
        error="The next-step logic bypasses the stop or lets SPICE repair unrelated gaps.",
    )

    outcome = spec.get("expected_result", {})
    outcome_ok = (
        outcome.get("evidence_state") == EXPECTED_STATE
        and outcome.get("disposition") == EXPECTED_DISPOSITION
        and outcome.get("lane_state") == EXPECTED_LANE
    )
    add_check(
        checks,
        errors,
        "expected_outcome",
        outcome_ok,
        error="The Stage 9B terminal state changed.",
    )

    return {
        "testbed_id": spec.get("testbed_id"),
        "mutation": mutation,
        "pass": not errors,
        "evidence_state": outcome.get("evidence_state") if not errors else "REJECTED",
        "disposition": outcome.get("disposition") if not errors else "REJECTED",
        "lane_state": outcome.get("lane_state") if not errors else "REJECTED",
        "new_candidate_pixel_bytes": access.get("new_candidate_pixel_bytes"),
        "retained_source_bytes": retained_bytes,
        "atlas_hits": total,
        "crew_raw_frames": len(crew_hits),
        "event_bracket_frames": EVENT_FRAME_IDS,
        "first_d5_offset_seconds": first_offset,
        "external_saw_offset_seconds": saw_offset,
        "dimension_statuses": dict(zip(dimension_ids, statuses)),
        "claim_ceiling": ceiling,
        "next_step_logic": next_logic,
        "checks": checks,
        "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage9b(root)
    mutations = {
        name: verify_stage9b(root, name)
        for name in load_json(root / "spec" / "stage9b.json")["hard_negatives"]
    }
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        **baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "errors": baseline["errors"]
        + ([] if hard_negatives_pass else ["At least one Stage 9B hard negative was accepted."]),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 9B — Gray-Feature Source/Control Gate",
        "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Disposition: `{result['disposition']}`",
        f"- Lane state: `{result['lane_state']}`",
        f"- New candidate-pixel bytes opened: `{result['new_candidate_pixel_bytes']}`",
        "",
        "## Result",
        "",
        "The exact event source is PCD3 product `art002a000015`, not the overlapping PCD2 transcript previously present in the Stage 0 corpus. A bounded archive query found 40 Nikon D5 raw frames from `23:22:37.530` through `23:22:49.330 UTC`. Five exposure-bracket frames begin `0.020–0.390 s` after Koch's `23:22:39.010 UTC` report.",
        "",
        "That unusually strong synchronization does not admit pixel inspection. The same recording documents persistent cabin reflections; the exact operator, eye/viewfinder state, and window path are not product-bound; the window stack lacks an event-specific optical model; the SPICE bundle is delayed; and the only near-time external frame is a different-viewpoint GoPro exposure at `+4.990 s`, ISO 100, about `0.000384 s`, and `-2 EV` with no faint-source sensitivity equivalence. NASA itself recommends a dedicated low-light limb camera for confident dust detection or non-detection.",
        "",
        "Therefore the current archive cannot distinguish all four required causes. The gray-feature image lane closes as `SOURCE_CONTROL_INSUFFICIENT` without opening event pixels. This is not evidence that dust was or was not present.",
        "",
        "## Control dimensions",
        "",
    ]
    for dimension_id, status in result["dimension_statuses"].items():
        lines.append(f"- `{dimension_id}`: `{status}`")
    lines.extend(
        [
            "",
            "## Claim ceiling",
            "",
            result["claim_ceiling"],
            "",
            "## Hard negatives",
            "",
        ]
    )
    for name, mutation_result in result.get("hard_negatives", {}).items():
        verdict = "REJECTED" if not mutation_result["pass"] else "UNEXPECTEDLY ACCEPTED"
        lines.append(f"- `{name}`: {verdict}")
    lines.extend(
        [
            "",
            "## Next-step logic",
            "",
            f"- Recommended: {result['next_step_logic']['recommended']}",
            f"- Fail action: {result['next_step_logic']['fail_action']}",
            f"- Secondary: {result['next_step_logic']['secondary']}",
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
        result = verify_stage9b(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(
            render_markdown(result)
            if args.command == "verify"
            else json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
