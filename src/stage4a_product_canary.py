#!/usr/bin/env python3
"""Verify the Stage 4A label-only product-availability canary offline."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp lacks a timezone: {value}")
    return parsed.astimezone(UTC)


def iso_utc(value: datetime) -> str:
    text = value.astimezone(UTC).isoformat()
    return text.replace("+00:00", "Z")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def first_text(root: ET.Element, name: str, required: bool = True) -> str | None:
    for element in root.iter():
        if local_name(element.tag) == name and element.text and element.text.strip():
            return element.text.strip()
    if required:
        raise ValueError(f"Missing XML field {name}")
    return None


def direct_child_text(parent: ET.Element, name: str) -> str | None:
    for child in parent:
        if local_name(child.tag) == name and child.text and child.text.strip():
            return child.text.strip()
    return None


def target_names(root: ET.Element) -> list[str]:
    names: list[str] = []
    for element in root.iter():
        if local_name(element.tag) == "Target_Identification":
            name = direct_child_text(element, "name")
            if name:
                names.append(name)
    return names


def parse_label(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    start = first_text(root, "start_date_time")
    stop = first_text(root, "stop_date_time", required=False)
    exposure = first_text(root, "exposure_duration", required=False)
    return {
        "lid": first_text(root, "logical_identifier"),
        "version": first_text(root, "version_id"),
        "file_name": first_text(root, "file_name"),
        "start_utc": start,
        "stop_utc": stop,
        "exposure_seconds": float(exposure) if exposure is not None else None,
        "payload_bytes": int(first_text(root, "file_size")),
        "activity_id": first_text(root, "activity_id"),
        "target_names": target_names(root),
    }


def load_inventory(path: Path) -> set[str]:
    members: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) != 2 or row[0] != "P":
                raise ValueError(f"Malformed collection inventory row in {path}: {row}")
            members.add(row[1].strip())
    return members


def nested(payload: dict[str, Any], *keys: str) -> Any:
    value: Any = payload
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    if mutation is None:
        return mutated
    overrides = mutated.setdefault("analysis_overrides", {})
    if mutation == "label_creation_time_is_acquisition":
        overrides["timestamp_field"] = "creation_date_time"
    elif mutation == "derivatives_are_independent_acquisitions":
        for collection in ("data_processed", "data_source"):
            mutated["admission"]["canonical_collections"].append(
                {
                    "bundle": "artemis2_crew_camera",
                    "collection": collection,
                    "timing_rule": "label_start_inside",
                }
            )
    elif mutation == "target_tag_validates_impact":
        overrides["flash_state"] = "VALIDATED_LUNAR_IMPACT"
    elif mutation == "report_interval_is_flash_duration":
        overrides["report_interval_is_event_duration"] = True
    elif mutation == "outside_interval_product_is_admitted":
        image = next(item for item in mutated["expected_products"] if item["kind"] == "raw_image")
        image["start_utc"] = "2026-04-07T00:52:51.830Z"
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_stage4a(root: Path, mutation: str | None = None) -> dict[str, Any]:
    original_spec = load_json(root / "spec" / "stage4a.json")
    spec = apply_mutation(original_spec, mutation)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    manifest_path = root / spec["sources"]["manifest_path"]
    manifest_ok = (
        manifest_path.stat().st_size == spec["sources"]["manifest_bytes"]
        and sha256_file(manifest_path) == spec["sources"]["manifest_sha256"]
    )
    checks.append({"id": "source_manifest_identity", "pass": manifest_ok})
    if not manifest_ok:
        errors.append("Source manifest identity mismatch")

    manifest = load_json(manifest_path)
    source_receipts: list[dict[str, Any]] = []
    for source in manifest["files"]:
        path = root / source["path"]
        exists = path.is_file()
        observed_bytes = path.stat().st_size if exists else None
        observed_hash = sha256_file(path) if exists else None
        passed = (
            exists
            and observed_bytes == source["bytes"]
            and observed_hash == source["sha256"]
        )
        source_receipts.append(
            {
                "path": source["path"],
                "pass": passed,
                "bytes": observed_bytes,
                "sha256": observed_hash,
            }
        )
        if not passed:
            errors.append(f"Source identity mismatch: {source['path']}")

    query_path = root / spec["sources"]["atlas_query_path"]
    query_ok = (
        query_path.stat().st_size == spec["sources"]["atlas_query_bytes"]
        and sha256_file(query_path) == spec["sources"]["atlas_query_sha256"]
        and manifest["atlas_query"]["request_sha256"]
        == spec["sources"]["atlas_query_sha256"]
    )
    checks.append(
        {
            "id": "source_file_identities",
            "pass": all(item["pass"] for item in source_receipts) and query_ok,
            "files": source_receipts,
            "query_pass": query_ok,
        }
    )
    if not query_ok:
        errors.append("Atlas query identity mismatch")

    interval_start = parse_utc(spec["report_interval"]["start_utc"])
    interval_end = parse_utc(spec["report_interval"]["end_utc"])
    interval_seconds = round((interval_end - interval_start).total_seconds(), 3)
    interval_ok = interval_seconds == spec["report_interval"]["duration_seconds"]
    checks.append(
        {
            "id": "report_interval_semantics",
            "pass": interval_ok,
            "duration_seconds": interval_seconds,
            "meaning": spec["report_interval"]["meaning"],
        }
    )
    if not interval_ok:
        errors.append("Frozen report interval does not match its endpoints")
    if spec.get("analysis_overrides", {}).get("report_interval_is_event_duration"):
        errors.append("The report interval cannot be treated as the physical flash duration")

    query = load_json(query_path)
    query_text = json.dumps(query, sort_keys=True)
    query_contract_ok = all(
        value in query_text
        for value in (
            "artemis2",
            spec["report_interval"]["start_utc"],
            spec["report_interval"]["end_utc"],
        )
    )
    checks.append({"id": "atlas_query_contract", "pass": query_contract_ok})
    if not query_contract_ok:
        errors.append("Atlas query does not preserve the frozen mission and interval")

    atlas = load_json(root / spec["sources"]["atlas_response_path"])
    hits = nested(atlas, "hits", "hits") or []
    total_hits = nested(atlas, "hits", "total", "value")
    atlas_ok = total_hits == spec["sources"]["expected_atlas_hits"] == len(hits)
    checks.append(
        {
            "id": "atlas_response_inventory",
            "pass": atlas_ok,
            "total_hits": total_hits,
        }
    )
    if not atlas_ok:
        errors.append("Atlas overlap response differs from the frozen 21-record receipt")

    canonical_pairs = {
        (item["bundle"], item["collection"])
        for item in spec["admission"]["canonical_collections"]
    }
    atlas_records: list[dict[str, Any]] = []
    for hit in hits:
        source = hit.get("_source", {})
        record = {
            "bundle": nested(source, "gather", "pds_archive", "bundle_id"),
            "collection": nested(source, "gather", "pds_archive", "collection_id"),
            "file_name": nested(source, "gather", "pds_archive", "file_name"),
            "start_utc": nested(source, "gather", "time", "start_time"),
            "stop_utc": nested(source, "gather", "time", "stop_time"),
            "label_uri": nested(source, "gather", "pds_archive", "related", "label", "uri"),
        }
        atlas_records.append(record)

    admitted_records = [
        item for item in atlas_records if (item["bundle"], item["collection"]) in canonical_pairs
    ]
    derivative_records = [
        item
        for item in atlas_records
        if item["bundle"] == "artemis2_crew_camera"
        and item["collection"] in spec["admission"]["derivative_collections_not_independent"]
    ]
    unrelated_records = len(atlas_records) - len(admitted_records) - len(derivative_records)

    expected_names = {item["file_name"] for item in spec["expected_products"]}
    admitted_names = {item["file_name"] for item in admitted_records}
    atlas_admission_ok = admitted_names == expected_names and len(admitted_records) == len(expected_names)
    checks.append(
        {
            "id": "canonical_product_admission",
            "pass": atlas_admission_ok,
            "admitted": sorted(admitted_names),
            "derivative_records_excluded": len(derivative_records),
            "unrelated_records_excluded": unrelated_records,
        }
    )
    if not atlas_admission_ok:
        errors.append("Canonical Atlas product set differs from the seven-product contract")

    video_inventory = load_inventory(root / spec["sources"]["video_inventory_path"])
    image_inventory = load_inventory(root / spec["sources"]["image_inventory_path"])
    inventory_count_ok = (
        len(video_inventory) == spec["sources"]["video_inventory_members"]
        and len(image_inventory) == spec["sources"]["image_inventory_members"]
    )
    checks.append(
        {
            "id": "collection_inventory_counts",
            "pass": inventory_count_ok,
            "video_members": len(video_inventory),
            "image_members": len(image_inventory),
        }
    )
    if not inventory_count_ok:
        errors.append("Collection inventory member counts changed")

    timestamp_field = spec.get("analysis_overrides", {}).get("timestamp_field", "acquisition")
    if timestamp_field != "acquisition":
        errors.append("Label creation time cannot substitute for acquisition time")

    products: list[dict[str, Any]] = []
    for expected in spec["expected_products"]:
        try:
            label = parse_label(root / expected["label_path"])
            atlas_record = next(
                item for item in admitted_records if item["file_name"] == expected["file_name"]
            )
            inventory = video_inventory if expected["kind"] == "continuous_video" else image_inventory
            member_ok = f"{label['lid']}::{label['version']}" in inventory
            identity_ok = all(
                (
                    label["lid"] == expected["lid"],
                    label["file_name"] == expected["file_name"],
                    label["start_utc"] == expected["start_utc"],
                    label["payload_bytes"] == expected["payload_bytes"],
                    label["activity_id"] == expected["activity_id"],
                    spec["admission"]["target_name"] in label["target_names"],
                    Path(str(atlas_record["label_uri"])).name
                    == Path(expected["label_path"]).name,
                    parse_utc(str(atlas_record["start_utc"]))
                    == parse_utc(str(label["start_utc"])),
                )
            )
            if expected["kind"] == "continuous_video":
                identity_ok = identity_ok and label["stop_utc"] == expected["stop_utc"]
                timing_ok = (
                    parse_utc(label["start_utc"]) <= interval_start
                    and parse_utc(str(label["stop_utc"])) >= interval_end
                )
                identity_ok = identity_ok and parse_utc(str(atlas_record["stop_utc"])) == parse_utc(
                    str(label["stop_utc"])
                )
            else:
                identity_ok = identity_ok and label["stop_utc"] is None
                identity_ok = identity_ok and label["exposure_seconds"] == expected["exposure_seconds"]
                timing_ok = interval_start <= parse_utc(label["start_utc"]) <= interval_end

            passed = member_ok and identity_ok and timing_ok
            products.append(
                {
                    "kind": expected["kind"],
                    "lid": label["lid"],
                    "file_name": label["file_name"],
                    "start_utc": label["start_utc"],
                    "stop_utc": label["stop_utc"],
                    "exposure_seconds": label["exposure_seconds"],
                    "payload_bytes": label["payload_bytes"],
                    "activity_id": label["activity_id"],
                    "target_names": label["target_names"],
                    "inventory_member": member_ok,
                    "timing_rule_pass": timing_ok,
                    "pass": passed,
                }
            )
            if not passed:
                errors.append(f"Product label or timing failed: {expected['file_name']}")
        except (ET.ParseError, OSError, ValueError, KeyError, StopIteration) as exc:
            errors.append(f"Product verification failed for {expected['file_name']}: {exc}")

    products_ok = len(products) == len(spec["expected_products"]) and all(
        item["pass"] for item in products
    )
    checks.append(
        {
            "id": "label_inventory_and_timing",
            "pass": products_ok,
            "product_count": len(products),
        }
    )
    if not products_ok:
        errors.append("One or more admitted products failed label, inventory, or timing checks")

    video_products = [item for item in products if item["kind"] == "continuous_video"]
    image_products = [item for item in products if item["kind"] == "raw_image"]
    full_interval_videos = [
        item
        for item in video_products
        if parse_utc(item["start_utc"]) <= interval_start
        and item["stop_utc"] is not None
        and parse_utc(item["stop_utc"]) >= interval_end
    ]
    image_starts_inside = [
        item
        for item in image_products
        if interval_start <= parse_utc(item["start_utc"]) <= interval_end
    ]
    activity_tag_counts = dict(sorted(Counter(item["activity_id"] for item in products).items()))
    full_payload_bytes = sum(item["payload_bytes"] for item in products)

    flash_state = spec.get("analysis_overrides", {}).get(
        "flash_state", "UNVALIDATED_CAPTURE_CANDIDATE"
    )
    if flash_state != "UNVALIDATED_CAPTURE_CANDIDATE":
        errors.append("Target or activity tags cannot validate a physical lunar impact")

    observed_result = {
        "evidence_state": "VERIFIED_CAPTURE_AVAILABLE" if not errors else "REJECTED",
        "atlas_hits": total_hits,
        "admitted_products": len(products),
        "continuous_video_products": len(video_products),
        "raw_image_products": len(image_products),
        "full_interval_video_products": len(full_interval_videos),
        "image_starts_inside_interval": len(image_starts_inside),
        "derivative_records_excluded": len(derivative_records),
        "unrelated_records_excluded": unrelated_records,
        "full_payload_bytes": full_payload_bytes,
        "activity_tag_counts": activity_tag_counts,
        "flash_state": flash_state,
        "disposition": "NOMINATE_TINY_STAGE5_SUBSET" if not errors else None,
    }
    result_match = observed_result == spec["expected_result"]
    checks.append({"id": "frozen_result", "pass": result_match, "observed": observed_result})
    if not result_match:
        errors.append("Observed Stage 4A result differs from the frozen contract")

    passed = not errors and all(item["pass"] for item in checks)
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": spec["expected_result"]["evidence_state"] if passed else "REJECTED",
        "disposition": spec["expected_result"]["disposition"] if passed else None,
        "report_interval": {
            "start_utc": iso_utc(interval_start),
            "end_utc": iso_utc(interval_end),
            "duration_seconds": interval_seconds,
            "meaning": spec["report_interval"]["meaning"],
        },
        "products": products,
        "atlas_summary": {
            "total_hits": total_hits,
            "admitted_products": len(admitted_records),
            "derivative_records_excluded": len(derivative_records),
            "unrelated_records_excluded": unrelated_records,
        },
        "payload_burden": {
            "full_product_bytes": full_payload_bytes,
            "decimal_gigabytes": round(full_payload_bytes / 1_000_000_000, 3),
            "gibibytes": round(full_payload_bytes / (1024**3), 3),
        },
        "metadata_friction": {
            "activity_tag_counts": activity_tag_counts,
            "bounded_interpretation": (
                "The five-frame Z9 burst carries two activity IDs: one Forward Look label and four "
                "Sunset labels. This is an official metadata inconsistency within the nominated "
                "burst, not evidence of pointing, content, cause, or operator error."
            ),
        },
        "flash_state": flash_state,
        "checks": checks,
        "errors": errors,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"] if passed else None,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage4a(root)
    spec = load_json(root / "spec" / "stage4a.json")
    mutations = {name: verify_stage4a(root, name) for name in spec["hard_negatives"]}
    hard_negatives_pass = all(not item["pass"] for item in mutations.values())
    passed = baseline["pass"] and hard_negatives_pass
    return {
        "baseline": baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": passed,
        "evidence_state": "VERIFIED_CAPTURE_AVAILABLE" if passed else "FAILED",
    }


def render_markdown(verification: dict[str, Any]) -> str:
    baseline = verification["baseline"]
    next_step = baseline.get("next_step_logic")
    lines = [
        "# Artemis II Observation-Execution Testbed — Stage 4A Result",
        "",
        f"- Verification: **{'PASS' if verification['pass'] else 'FAIL'}**",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Admitted products: **{len(baseline['products'])}**",
        f"- Flash state: `{baseline['flash_state']}`",
        f"- Disposition: `{baseline.get('disposition') or 'UNSET'}`",
        "",
        "The official PDS inventory contains label-timed coverage of the report interval: two "
        "SAW3 stream-channel products span the whole interval, and five Nikon Z9 raw exposures "
        "start inside it. The channel products are not two independent viewpoints, and coverage "
        "does not establish that the reported flash appears in any media.",
        "",
        "## Admitted products",
        "",
        "| Product | Kind | Acquisition time | Activity tag | Payload bytes |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for product in baseline["products"]:
        time_text = product["start_utc"]
        if product["stop_utc"]:
            time_text += f" to {product['stop_utc']}"
        elif product["exposure_seconds"] is not None:
            time_text += f" ({product['exposure_seconds']:g}s exposure)"
        lines.append(
            f"| {product['file_name']} | {product['kind']} | {time_text} | "
            f"{product['activity_id']} | {product['payload_bytes']} |"
        )
    lines.extend(
        [
            "",
            "## Decision-relevant limits",
            "",
            "The five still exposures begin about 36 seconds after the first report and before "
            "the later joint characterization. Their timing cannot establish that they captured "
            "the initially reported transient. Four are tagged `24_Sunset`; one is tagged "
            "`25_Discussion #6: Forward Look`. That split is a bounded metadata-friction finding, "
            "not pointing or impact validation.",
            "",
            f"Fetching all seven full payloads would require {baseline['payload_burden']['full_product_bytes']} "
            f"bytes ({baseline['payload_burden']['decimal_gigabytes']:.3f} GB; "
            f"{baseline['payload_burden']['gibibytes']:.3f} GiB). No media bytes were downloaded.",
            "",
            baseline["claim_ceiling"],
            "",
            "## Next-step logic",
            "",
            f"**Recommended:** {next_step['recommended'] if next_step else 'None; verification failed.'}",
            "",
            f"Why: {next_step['why'] if next_step else 'Resolve the reported verification errors first.'}",
            "",
            f"Alternative: {next_step['alternative'] if next_step else 'None while the baseline is rejected.'}",
            "",
            f"Fallback: {next_step['fallback'] if next_step else 'Retain the last verified recovery point.'}",
            "",
            f"Stop: {next_step['stop'] if next_step else 'Do not advance a rejected baseline.'}",
            "",
            "## Hard negatives",
            "",
        ]
    )
    for name, result in verification["hard_negatives"].items():
        lines.append(f"- `{name}`: {'REJECTED' if not result['pass'] else 'UNEXPECTEDLY ACCEPTED'}")
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
    parser.add_argument(
        "--mutation",
        choices=(
            "label_creation_time_is_acquisition",
            "derivatives_are_independent_acquisitions",
            "target_tag_validates_impact",
            "report_interval_is_flash_duration",
            "outside_interval_product_is_admitted",
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        payload = verify_with_mutations(args.root)
    else:
        payload = verify_stage4a(args.root, args.mutation)
    if args.json_output:
        write_json(args.json_output, payload)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_markdown(payload) if args.command == "verify" else json.dumps(payload, indent=2) + "\n"
        args.markdown_output.write_text(rendered, encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
