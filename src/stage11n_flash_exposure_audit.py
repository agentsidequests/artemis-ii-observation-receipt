#!/usr/bin/env python3
"""Build and verify the Stage 11N Artemis II flash exposure receipt."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import math
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def parse_utc(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def xml_text_by_local_name(root: ET.Element, name: str) -> str:
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == name:
            return (element.text or "").strip()
    raise ValueError(f"XML element not found: {name}")


def add_check(
    checks: list[dict[str, Any]],
    errors: list[str],
    name: str,
    passed: bool,
    error: str,
    **details: Any,
) -> None:
    checks.append({"name": name, "pass": bool(passed), **details})
    if not passed:
        errors.append(error)


def contains_all(text: str, phrases: list[str]) -> tuple[bool, list[str]]:
    def normalized(value: str) -> str:
        value = re.sub(r"-\s*\n\s*", "", value)
        return " ".join(value.casefold().split())

    folded = normalized(text)
    missing = [phrase for phrase in phrases if normalized(phrase) not in folded]
    return not missing, missing


def source_receipts(root: Path, spec: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    receipts: list[dict[str, Any]] = []
    all_match = True
    for expected in spec["source_contract"]:
        path = root / expected["path"]
        if not path.exists():
            receipts.append({**expected, "exists": False, "identity_match": False})
            all_match = False
            continue
        payload = path.read_bytes()
        actual = {"bytes": len(payload), "sha256": sha256(payload)}
        match = actual["bytes"] == expected["bytes"] and actual["sha256"] == expected["sha256"]
        receipts.append({
            "path": expected["path"],
            "role": expected["role"],
            "exists": True,
            "expected": {"bytes": expected["bytes"], "sha256": expected["sha256"]},
            "actual": actual,
            "identity_match": match,
        })
        all_match = all_match and match
    return receipts, all_match


def transcript_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def find_transcript_anchor(rows: list[dict[str, str]], timestamp: str, phrase: str) -> bool:
    target = parse_utc(timestamp)
    for row in rows:
        value = row.get("utc", "").strip()
        if not value:
            continue
        row_time = parse_utc(value.replace(" ", "T") + "Z")
        if row_time == target and phrase.casefold() in row.get("text", "").casefold():
            return True
    return False


def apply_mutation(claims: dict[str, bool], mutation: str | None) -> dict[str, bool]:
    claims = copy.deepcopy(claims)
    mapping = {
        "call_five_a_flux_estimate": "five_events_are_calibrated_flux",
        "promote_count_floor_to_completeness_corrected_flux": "conservative_count_floor_is_promoted_to_completeness_corrected_flux",
        "promote_no_screened_pulse_to_event_exclusion": "no_screened_pulse_excludes_crew_event",
        "call_high_speed_camera_simultaneous": "later_30fps_null_is_simultaneous_event_non_detection",
        "force_one_to_one_event_mapping": "transcript_candidates_map_one_to_one_to_annotation_events",
        "use_capture_recapture_estimate": "observer_overlap_supports_capture_recapture_estimate",
        "call_cm_size_measured": "centimeter_scale_is_independently_measured",
        "call_citizen_candidate_confirmed_match": "citizen_candidate_is_confirmed_ground_match",
        "call_global_novelty": "recommendations_are_globally_novel",
        "omit_nasa_existing_recommendations": "nasa_existing_recommendations_are_omitted",
    }
    if mutation is None:
        return claims
    if mutation not in mapping:
        raise ValueError(f"Unknown mutation: {mutation}")
    claims[mapping[mutation]] = True
    return claims


def audit_stage11n(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = load_json(root / "spec/stage11n.json")
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    receipts, sources_match = source_receipts(root, spec)
    add_check(
        checks,
        errors,
        "source_artifact_identities",
        sources_match,
        "One or more frozen source artifacts changed or are missing.",
        sources=len(receipts),
    )

    pcd_rows = transcript_rows(root / "corpus/transcripts/art002a000052_pcd3_trn-csv_v01.csv")
    anchors = spec["transcript_anchors"]
    pcd_expectations = [
        (anchors["first_clear_candidate_utc"], "just saw a flash"),
        (anchors["shared_candidate_utc"], "just saw a meteorite"),
        (anchors["ambiguous_candidate_utc"], "less sure"),
        (anchors["later_clear_candidate_utc"], "just saw another one"),
        (anchors["last_clear_candidate_utc"], "just saw another one"),
    ]
    anchor_states = [find_transcript_anchor(pcd_rows, when, phrase) for when, phrase in pcd_expectations]
    add_check(
        checks,
        errors,
        "pcd_transcript_anchors",
        all(anchor_states),
        "One or more PCD flash anchors did not reproduce.",
        anchors_found=sum(anchor_states),
        anchors_expected=len(anchor_states),
    )

    oe_text = (root / "evidence/stage11n/source/art002_2026-04-07_oe1_trn-csv_v01.csv").read_text(encoding="utf-8-sig")
    oe_required = [
        "do not feel we have clarity on when the first four",
        "We didn't necessarily announce everyone",
        "maybe it was a priming bias",
        "my eyes were adjusting",
        "made observing for impact flashes possible",
    ]
    oe_ok, oe_missing = contains_all(oe_text, oe_required)
    add_check(
        checks,
        errors,
        "crew_detection_context",
        oe_ok,
        "The operations transcript no longer supports all frozen detection-context findings.",
        missing=oe_missing,
    )

    report_text = (root / "evidence/stage11n/source/artemis-ii-preliminary-report-flash-pages.txt").read_text(encoding="utf-8")
    report_ok, report_missing = contains_all(report_text, spec["required_nasa_findings"])
    add_check(
        checks,
        errors,
        "nasa_report_findings_and_recommendations",
        report_ok,
        "The frozen NASA report extract does not contain all required findings and recommendations.",
        missing=report_missing,
    )

    feature_text = (root / "evidence/stage11n/source/nasa-preliminary-report-feature.html").read_text(encoding="utf-8")
    feature_required = [
        "#1 with a blue dot",
        "#2 is circled with a red dot",
        "#3 with a red dot",
        "#4 is circled with a red dot",
        "#5 with a blue dot",
        "46,000 miles away from the Moon",
    ]
    feature_ok, feature_missing = contains_all(feature_text, feature_required)
    add_check(
        checks,
        errors,
        "nasa_annotation_key_and_range",
        feature_ok,
        "NASA's feature no longer reproduces the event key or observing range.",
        missing=feature_missing,
    )

    volunteer_text = (root / "evidence/stage11n/source/nasa-volunteers-lunar-flashes.html").read_text(encoding="utf-8")
    volunteer_required = [
        "videos people submitted",
        "Impact Flash team is just getting started",
        "impact flash candidate",
    ]
    volunteer_ok, volunteer_missing = contains_all(volunteer_text, volunteer_required)
    crew_ground_limit = "do not suspect any that I saw would be able to be correlated from an Earth-based science team"
    ground_state_ok = volunteer_ok and crew_ground_limit.casefold() in oe_text.casefold()
    add_check(
        checks,
        errors,
        "ground_candidate_not_confirmed_match",
        ground_state_ok,
        "The sources no longer support the candidate-not-confirmed ground-correlation boundary.",
        missing=volunteer_missing,
    )

    moon_facts_text = (root / "evidence/stage11n/source/nasa-moon-facts.html").read_text(encoding="utf-8")
    moon_facts_required = [
        "radius of about 1,080 miles (1,740 kilometers)",
        "average of 238,855 miles (384,400 kilometers) away",
    ]
    moon_facts_ok, moon_facts_missing = contains_all(moon_facts_text, moon_facts_required)
    add_check(
        checks,
        errors,
        "nasa_moon_geometry_inputs",
        moon_facts_ok,
        "NASA's frozen Moon facts no longer reproduce the radius and average distance inputs.",
        missing=moon_facts_missing,
    )

    events = copy.deepcopy(spec["annotation_events"])
    witness_marks = sum(len(event["observers"]) for event in events)
    multi_witness = sum(len(event["observers"]) >= 2 for event in events)
    triple_witness = sum(len(event["observers"]) == 3 for event in events)
    single_witness = sum(len(event["observers"]) == 1 for event in events)
    observers = sorted({observer for event in events for observer in event["observers"]})
    witness_metrics = {
        "annotated_events": len(events),
        "witness_marks": witness_marks,
        "distinct_observers": len(observers),
        "single_witness_events": single_witness,
        "multi_witness_events": multi_witness,
        "triple_witness_events": triple_witness,
    }
    witness_ok = witness_metrics == {
        "annotated_events": 5,
        "witness_marks": 8,
        "distinct_observers": 3,
        "single_witness_events": 3,
        "multi_witness_events": 2,
        "triple_witness_events": 1,
    }
    add_check(
        checks,
        errors,
        "annotation_witness_pattern",
        witness_ok,
        "The five-event, eight-mark witness pattern did not reproduce.",
        **witness_metrics,
    )

    camera_xml = ET.parse(root / "evidence/stage11n/source/art002m1200970119_saw3_raw_v01.xml").getroot()
    camera_start = parse_utc(xml_text_by_local_name(camera_xml, "start_date_time"))
    camera_stop = parse_utc(xml_text_by_local_name(camera_xml, "stop_date_time"))
    duration_seconds = int(xml_text_by_local_name(camera_xml, "duration_seconds"))
    acquisition_fps = float(xml_text_by_local_name(camera_xml, "acquisition_frame_rate"))
    payload_bytes = int(xml_text_by_local_name(camera_xml, "file_size"))
    annotation_time = parse_utc(anchors["annotation_ledger_utc"])
    gap_seconds = int((camera_start - annotation_time).total_seconds())
    camera_metrics = {
        "annotation_ledger_utc": annotation_time.isoformat().replace("+00:00", "Z"),
        "camera_start_utc": camera_start.isoformat().replace("+00:00", "Z"),
        "camera_stop_utc": camera_stop.isoformat().replace("+00:00", "Z"),
        "duration_seconds": duration_seconds,
        "acquisition_frame_rate_fps": acquisition_fps,
        "payload_bytes": payload_bytes,
        "starts_after_ledger_seconds": gap_seconds,
        "starts_after_ledger_hhmmss": "00:15:13",
        "simultaneous_with_any_ledgered_event": False,
    }
    camera_ok = (
        camera_start == parse_utc("2026-04-07T01:19:13Z")
        and camera_stop == parse_utc("2026-04-07T01:21:23Z")
        and duration_seconds == 130
        and acquisition_fps == 30.0
        and payload_bytes == 733443159
        and gap_seconds == 913
    )
    add_check(
        checks,
        errors,
        "later_30fps_window_timing",
        camera_ok,
        "The later 30 fps camera-window timing did not reproduce.",
        **camera_metrics,
    )

    overlap_receipt = load_json(root / "evidence/stage11o/acquisition-receipt.json")
    pixel_screen = load_json(root / "results/stage11p-overlap-pixel-screen.json")
    overlap_metrics = {
        "transport_state": overlap_receipt.get("state"),
        "clip_bytes": overlap_receipt.get("clip", {}).get("bytes"),
        "accepted_media_body_bytes": overlap_receipt.get("accepted_media_body_bytes"),
        "screen_state": pixel_screen.get("evidence_state"),
        "frames_screened": pixel_screen.get("video", {}).get("frames_decoded"),
        "frame_rate_fps": pixel_screen.get("video", {}).get("fps"),
        "apparent_lunar_diameter_pixels": pixel_screen.get("lunar_footprint", {}).get("apparent_diameter_pixels"),
        "illustrative_km_per_apparent_pixel": pixel_screen.get("lunar_footprint", {}).get("illustrative_km_per_apparent_pixel"),
        "screened_pulse_candidates": pixel_screen.get("pulse_screen", {}).get("candidate_frame_count"),
        "screen_excludes_crew_event": False,
        "maps_one_to_one_to_annotated_event": False,
        "source_pixel_photometry": False,
    }
    overlap_ok = (
        overlap_receipt.get("state") == "VERIFIED_BOUNDED_EXTRACTION"
        and overlap_receipt.get("clip", {}).get("sha256") == "a2dc14c6060de9bb8858d4d9d49b207c99d6dacdd5943fb84bb3448f67762eec"
        and pixel_screen.get("pass") is True
        and overlap_metrics["frames_screened"] == 900
        and overlap_metrics["apparent_lunar_diameter_pixels"] == 10
        and overlap_metrics["screened_pulse_candidates"] == 0
        and overlap_metrics["screen_excludes_crew_event"] is False
    )
    add_check(
        checks,
        errors,
        "overlapping_context_clip_and_pixel_screen",
        overlap_ok,
        "The bounded overlap clip or its contextual pixel screen did not reproduce.",
        **overlap_metrics,
    )

    first = parse_utc(anchors["first_clear_candidate_utc"])
    last = parse_utc(anchors["last_clear_candidate_utc"])
    clear_report_span_seconds = (last - first).total_seconds()
    distance = spec["distance_inputs"]
    distance_ratio = distance["average_earth_to_moon_miles"] / distance["orion_to_moon_miles"]
    flux_advantage = distance_ratio**2
    magnitude_advantage = 5.0 * math.log10(distance_ratio)
    hemisphere_area = 2.0 * math.pi * distance["moon_radius_km"] ** 2
    full_surface_area = 2.0 * hemisphere_area
    short_window_hours = clear_report_span_seconds / 3600.0
    naive_short = len(events) / (short_window_hours * hemisphere_area)
    naive_one_hour = len(events) / hemisphere_area
    all_lunar_one_hour_count_floor = len(events) / full_surface_area
    geometry = {
        "distance_ratio_earth_average_to_orion": distance_ratio,
        "inverse_square_received_flux_advantage": flux_advantage,
        "magnitude_advantage": magnitude_advantage,
        "visible_lunar_hemisphere_area_km2": hemisphere_area,
        "full_lunar_surface_area_km2": full_surface_area,
        "first_to_last_clear_report_span_seconds": clear_report_span_seconds,
        "naive_full_hemisphere_short_window_rate_km2_hour": naive_short,
        "naive_full_hemisphere_one_hour_rate_km2_hour": naive_one_hour,
        "naive_denominator_sensitivity_factor": naive_short / naive_one_hour,
        "rate_values_are_valid_flux_estimates": False,
        "all_lunar_one_hour_detected_count_floor_km2_hour": all_lunar_one_hour_count_floor,
        "count_floor_status": "CONSERVATIVE_OBSERVED_COUNT_DENSITY_ONLY",
        "count_floor_assumptions": [
            "All five annotated events are accepted as impacts.",
            "All five occurred within the nearly hour-long eclipse, conservatively rounded up to one hour.",
            "The entire lunar surface is used as the maximum spatial denominator.",
            "The value is not corrected for missed events, brightness threshold, detection completeness, or long-run sampling uncertainty.",
        ],
        "interpretation": distance["interpretation"],
    }
    geometry_ok = (
        5.19 < distance_ratio < 5.20
        and 26.9 < flux_advantage < 27.1
        and 3.57 < magnitude_advantage < 3.59
        and 19_010_000 < hemisphere_area < 19_030_000
        and 38_030_000 < full_surface_area < 38_060_000
        and 1324.2 < clear_report_span_seconds < 1324.3
        and geometry["rate_values_are_valid_flux_estimates"] is False
        and 1.31e-7 < all_lunar_one_hour_count_floor < 1.32e-7
    )
    add_check(
        checks,
        errors,
        "distance_and_denominator_sensitivity",
        geometry_ok,
        "The observing-geometry or denominator-sensitivity calculation did not reproduce.",
    )

    benchmarks = spec["survey_benchmarks"]
    benchmark_checks = [
        "4 million square kilometers" in (root / "evidence/stage11n/source/nasa-lunar-impact-monitoring-2024.txt").read_text(encoding="utf-8"),
        "266.88 hr" in (root / "evidence/stage11n/source/suggs-flux-kilogram-meteoroids.txt").read_text(encoding="utf-8"),
        "50% detection" in (root / "evidence/stage11n/source/neliota-wide-field-high-cadence.txt").read_text(encoding="utf-8"),
        benchmarks["suggs_2014"]["reported_flux_km2_hour"] == 1.03e-7,
        benchmarks["neliota"]["reported_flux_km2_hour"] == 1.96e-7,
    ]
    add_check(
        checks,
        errors,
        "established_survey_denominators",
        all(benchmark_checks),
        "One or more established-survey denominator benchmarks did not reproduce.",
    )

    claims = apply_mutation(spec["claim_boundaries"], mutation)
    claim_ok = not any(claims.values())
    add_check(
        checks,
        errors,
        "claim_and_method_boundaries",
        claim_ok,
        "A prohibited flash, flux, timing, size, or novelty inference was asserted.",
        claims=claims,
    )

    result = {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": not errors,
        "evidence_state": "VERIFIED_FLASH_EXPOSURE_RECEIPT" if not errors else "FAILED_FLASH_EXPOSURE_RECEIPT",
        "disposition": "USE_EXPOSURE_GAP_AND_LATER_CAMERA_TIMING" if not errors else "WITHHOLD_FLASH_INFERENCE",
        "checks": checks,
        "errors": errors,
        "source_receipts": receipts,
        "witness_metrics": witness_metrics,
        "annotation_events": events,
        "camera_window": camera_metrics,
        "overlap_camera": overlap_metrics,
        "geometry": geometry,
        "survey_benchmarks": benchmarks,
        "calibrated_flux_state": "UNAVAILABLE_FROM_PUBLIC_RECORD",
        "strongest_supported_inference": "Five conservatively curated, cross-witnessed crew events support a conservative all-lunar detected-count floor, but not a completeness-corrected, brightness-threshold impact flux.",
        "most_consequential_archive_finding": "The assessed 30 fps null video begins 15 minutes 13 seconds after the official five-event ledger timestamp, so it is a later null window rather than a simultaneous test of any confirmed event.",
        "overlap_camera_finding": "A separately materialized 60 fps SAW3 clip spans the 00:51:15.947 crew report, but the threshold-defined lunar image is only ten pixels across. A frozen screen found no qualifying pulse in the transcoded clip; that result is contextual and does not exclude the crew event.",
        "ground_correlation_state": "NASA publicly highlighted a volunteer impact-flash candidate but did not identify it as a confirmed match to a crew event; the crew record says the observed flashes were not expected to be Earth-correlatable.",
        "recommendations": spec["recommendations"],
        "claim_boundaries": claims,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
    }
    return result


def verify_hard_negatives(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec/stage11n.json")
    outcomes: dict[str, Any] = {}
    for mutation in spec["hard_negatives"]:
        result = audit_stage11n(root, mutation=mutation)
        failed_checks = [check["name"] for check in result["checks"] if not check["pass"]]
        outcomes[mutation] = {
            "rejected": not result["pass"],
            "failed_checks": failed_checks,
            "required_failed_check": "claim_and_method_boundaries",
        }
    passed = all(
        outcome["rejected"] and outcome["required_failed_check"] in outcome["failed_checks"]
        for outcome in outcomes.values()
    )
    return {"pass": passed, "hard_negatives": outcomes}


def render_event_receipt(result: dict[str, Any]) -> bytes:
    fields = [
        "event_id",
        "observers",
        "witness_count",
        "annotation_note",
        "exact_event_utc",
        "transcript_mapping",
        "overlapping_30fps_event_frame",
        "inference_state",
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for event in result["annotation_events"]:
        writer.writerow({
            "event_id": event["event_id"],
            "observers": "; ".join(event["observers"]),
            "witness_count": len(event["observers"]),
            "annotation_note": event["annotation_note"],
            "exact_event_utc": "not independently resolved",
            "transcript_mapping": "not assigned one-to-one",
            "overlapping_30fps_event_frame": "not established",
            "inference_state": "NASA-confirmed annotated event; no calibrated brightness or exposure denominator",
        })
    return stream.getvalue().encode("utf-8")


def render_markdown(result: dict[str, Any]) -> str:
    camera = result["camera_window"]
    geometry = result["geometry"]
    witness = result["witness_metrics"]
    lines = [
        "# Stage 11N: Artemis II flash exposure audit",
        "",
        f"**State:** {result['evidence_state']}",
        "",
        "## Result",
        "",
        result["strongest_supported_inference"],
        "",
        result["most_consequential_archive_finding"],
        "",
        "## Reproduced event structure",
        "",
        f"- Annotated events: {witness['annotated_events']}",
        f"- Witness marks: {witness['witness_marks']}",
        f"- Multi-witness events: {witness['multi_witness_events']}",
        f"- Three-witness events: {witness['triple_witness_events']}",
        f"- Single-witness events: {witness['single_witness_events']}",
        "",
        "## Camera timing",
        "",
        f"- Five-event annotation timestamp: {camera['annotation_ledger_utc']}",
        f"- Assessed 30 fps video: {camera['camera_start_utc']} to {camera['camera_stop_utc']}",
        f"- Start lag after the ledger: {camera['starts_after_ledger_seconds']} seconds ({camera['starts_after_ledger_hhmmss']})",
        "- Meaning: a later null interval, not a simultaneous non-detection of a confirmed event.",
        "",
        "## Overlapping camera context",
        "",
        result["overlap_camera_finding"],
        "",
        f"The bounded extraction screened {result['overlap_camera']['frames_screened']} frames at about {result['overlap_camera']['frame_rate_fps']:.2f} fps. At the report frame, the Moon occupied a threshold-defined {result['overlap_camera']['apparent_lunar_diameter_pixels']}-pixel footprint, equivalent to about {result['overlap_camera']['illustrative_km_per_apparent_pixel']:.0f} kilometers per apparent pixel as a sampling illustration. This is not source-pixel photometry or an optical-resolution measurement.",
        "",
        "## What five can and cannot say about flux",
        "",
        f"NASA's lower-bound language is defensible in a narrow sense. If all five accepted events occurred within the nearly hour-long eclipse, rounding the interval up to one hour and dividing by the Moon's entire {geometry['full_lunar_surface_area_km2']:,.0f} square-kilometer surface gives a conservative detected-count floor of {geometry['all_lunar_one_hour_detected_count_floor_km2_hour']:.2e} per square kilometer per hour. Missed events can only raise the realized all-lunar count density for that interval.",
        "",
        "That floor is not a completeness-corrected or brightness-threshold flux and is not directly comparable to established surveys. Such a measurement needs brightness-dependent detection probability integrated over monitored area and live time. The public event record does not supply a calibrated human or instrument detection function, photometric threshold, observer live-time ledger, or continuously overlapping calibrated event frames.",
        "",
        f"The first-to-last clear transcript reports span {geometry['first_to_last_clear_report_span_seconds']:.3f} seconds. Choosing that span instead of one hour changes a naive visible-hemisphere denominator by {geometry['naive_denominator_sensitivity_factor']:.2f} times before any completeness correction. Those narrower-denominator values remain invalid as calibrated flux estimates.",
        "",
        "## Observing-geometry illustration",
        "",
        f"At 46,000 miles versus the average Earth-Moon distance of 238,855 miles, inverse-square point-source geometry gives about {geometry['inverse_square_received_flux_advantage']:.1f} times more received flux, equivalent to {geometry['magnitude_advantage']:.2f} magnitudes. This helps explain why faint events were visible, but it is not flash photometry.",
        "",
        "## Recommendations",
        "",
    ]
    for recommendation in result["recommendations"]:
        lines.extend([
            f"### {recommendation['id']}. {recommendation['name']}",
            "",
            recommendation["requirement"],
            "",
            f"Acceptance: {recommendation['acceptance']}",
            "",
        ])
    lines.extend([
        "## Claim ceiling",
        "",
        result["claim_ceiling"],
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--verify-hard-negatives", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    result = audit_stage11n(root)
    if args.verify_hard_negatives:
        result["hard_negative_verification"] = verify_hard_negatives(root)
        result["pass"] = result["pass"] and result["hard_negative_verification"]["pass"]
    if args.write:
        result_dir = root / "results"
        result_dir.mkdir(parents=True, exist_ok=True)
        (result_dir / "stage11n-result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (result_dir / "stage11n-result.md").write_text(render_markdown(result), encoding="utf-8")
        (result_dir / "stage11n-event-receipt.csv").write_bytes(render_event_receipt(result))
    print(json.dumps({
        "pass": result["pass"],
        "evidence_state": result["evidence_state"],
        "errors": result["errors"],
        "camera_gap_seconds": result["camera_window"]["starts_after_ledger_seconds"],
        "witness_metrics": result["witness_metrics"],
        "hard_negative_verification": result.get("hard_negative_verification"),
    }, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
