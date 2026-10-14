#!/usr/bin/env python3
"""Acquire the frozen SAW3 raw-label set and locate Stage 2B event frames."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc
CHUNK_BYTES = 64 * 1024
PDS_NS = {"pds": "http://pds.nasa.gov/pds4/pds/v1"}
MSN_NS = {"msn": "http://pds.nasa.gov/pds4/msn/v1"}


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")


def inventory_stems(path: Path) -> list[str]:
    stems: list[str] = []
    pattern = re.compile(r":(art002e\d{6}_saw3_raw)\.tif::1\.0$")
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) != 2 or row[0] != "P":
                continue
            match = pattern.search(row[1])
            if match:
                stems.append(match.group(1))
    if len(stems) != len(set(stems)):
        raise ValueError("SAW3 inventory contains duplicate identities")
    return sorted(stems)


def download_bounded(url: str, destination: Path, max_bytes: int, remaining: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/xml,text/xml", "User-Agent": "Artemis-II-Testbed/0.4"},
    )
    digest = hashlib.sha256()
    received = 0
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_length = response.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("Label GET omitted Content-Length")
        declared = int(raw_length)
        if declared > max_bytes or declared > remaining:
            raise ValueError(
                f"Declared label length {declared} exceeds file cap {max_bytes} or remaining {remaining}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(CHUNK_BYTES)
                if not chunk:
                    break
                received += len(chunk)
                if received > declared:
                    raise ValueError("Label body exceeded declared Content-Length")
                handle.write(chunk)
                digest.update(chunk)
        if received != declared:
            raise ValueError(f"Label body length {received} differs from declared {declared}")
        headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"content-length", "content-type", "etag", "last-modified"}
        }
        return {
            "bytes": received,
            "sha256": digest.hexdigest(),
            "resolved_url": response.geturl(),
            "headers": headers,
        }


def label_metadata(path: Path) -> tuple[str, int]:
    root = ET.parse(path).getroot()
    time_node = root.find(
        ".//pds:Time_Coordinates/pds:start_date_time", PDS_NS
    )
    flight_day_node = root.find(".//msn:Mission_Information/msn:flight_day_number", MSN_NS)
    if time_node is None or time_node.text is None:
        raise ValueError(f"Label has no acquisition start: {path.name}")
    if flight_day_node is None or flight_day_node.text is None:
        raise ValueError(f"Label has no flight-day number: {path.name}")
    return time_node.text, int(flight_day_node.text)


def archive_path_for_stem(contract: dict[str, Any], stem: str) -> str:
    match = re.fullmatch(r"art002e(\d{6})_saw3_raw", stem)
    if match is None:
        raise ValueError(f"Unexpected inventory stem: {stem}")
    product_number = int(match.group(1))
    template = contract["default_path_template"]
    for override in contract["path_overrides"]:
        if override["product_number_min"] <= product_number <= override["product_number_max"]:
            template = override["path_template"]
            break
    return template.replace("{inventory_product_stem}", stem)


def scan(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage2b.json")
    fallback = spec["candidate_discovery"]["inventory_fallback"]
    contract = fallback["label_scan"]
    inventory_path = root / "evidence" / "stage2b" / "collection_data_raw_image_inventory.csv"
    if inventory_path.stat().st_size != fallback["expected_bytes_from_head"]:
        raise ValueError("Inventory byte length differs from frozen contract")
    if sha256_file(inventory_path) != fallback["sha256"]:
        raise ValueError("Inventory SHA-256 differs from frozen contract")
    stems = inventory_stems(inventory_path)
    if len(stems) != contract["expected_members"]:
        raise ValueError(f"Inventory has {len(stems)} SAW3 members, expected {contract['expected_members']}")

    source_root = root / "evidence" / "stage2b" / "label-scan" / "source"
    reused_root = root / "evidence" / "stage2a" / "source"
    prior_manifest_path = root / "evidence" / "stage2b" / "label-scan-manifest-attempt-1.json"
    prior_manifest = load_json(prior_manifest_path)
    prior_by_path = {item["path"]: item for item in prior_manifest["files"]}
    accepted_network_bytes = 0
    manifest: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    status = "COMPLETED"
    error: str | None = None

    for stem in stems:
        file_name = stem + "_v01.xml"
        archive_path = archive_path_for_stem(contract, stem)
        url = spec["oracle"]["archive_base"] + archive_path
        reused_path = reused_root / file_name
        destination = source_root / file_name
        record: dict[str, Any] = {"file_name": file_name, "archive_path": archive_path, "url": url}
        try:
            destination_relative = destination.relative_to(root).as_posix()
            prior_item = prior_by_path.get(destination_relative)
            if destination.is_file() and prior_item is not None:
                if destination.stat().st_size != prior_item["bytes"]:
                    raise ValueError("Prior checkpoint byte length mismatch")
                if sha256_file(destination) != prior_item["sha256"]:
                    raise ValueError("Prior checkpoint SHA-256 mismatch")
                path = destination
                result = {
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "resolved_url": None,
                    "headers": {},
                }
                record["transfer"] = "REUSED_HASH_PINNED_STAGE2B_CHECKPOINT"
            elif reused_path.is_file():
                path = reused_path
                result = {
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "resolved_url": None,
                    "headers": {},
                }
                record["transfer"] = "REUSED_HASH_PINNED_STAGE2A_LABEL"
            else:
                remaining = contract["aggregate_max_bytes"] - accepted_network_bytes
                result = download_bounded(
                    url, destination, contract["max_label_bytes_each"], remaining
                )
                path = destination
                accepted_network_bytes += result["bytes"]
                record["transfer"] = "DOWNLOADED"
            acquisition_time, flight_day = label_metadata(path)
            record.update(
                {
                    "status": "ACCEPTED",
                    "path": path.relative_to(root).as_posix(),
                    "time_utc": acquisition_time,
                    "flight_day": flight_day,
                    **result,
                    "aggregate_network_bytes": accepted_network_bytes,
                }
            )
            manifest.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "archive_path": archive_path,
                    "bytes": result["bytes"],
                    "sha256": result["sha256"],
                    "time_utc": acquisition_time,
                    "flight_day": flight_day,
                    "transfer": record["transfer"],
                }
            )
        except (OSError, ValueError, ET.ParseError) as exc:
            status = "STOPPED"
            error = f"{file_name}: {exc}"
            record.update({"status": "STOPPED", "error": str(exc)})
        attempts.append(record)
        if status == "STOPPED":
            break

    matches: dict[str, list[dict[str, Any]]] = {}
    if status == "COMPLETED":
        for event in spec["events"]:
            start, end = event["candidate_time_range_utc"]
            matches[event["event_id"]] = [
                {
                    "path": item["path"],
                    "archive_path": item["archive_path"],
                    "time_utc": item["time_utc"],
                    "bytes": item["bytes"],
                    "sha256": item["sha256"],
                }
                for item in sorted(manifest, key=lambda candidate: candidate["time_utc"])
                if start <= item["time_utc"] <= end
            ]

    receipt = {
        "receipt_id": "artemis2-stage2b-saw3-label-scan-v1",
        "completed_at_utc": utc_now(),
        "status": status,
        "error": error,
        "inventory_path": inventory_path.relative_to(root).as_posix(),
        "inventory_members": len(stems),
        "accepted_labels": len(manifest),
        "network_downloaded_labels": sum(1 for item in attempts if item.get("transfer") == "DOWNLOADED"),
        "reused_stage2a_labels": sum(
            1 for item in attempts if item.get("transfer") == "REUSED_HASH_PINNED_STAGE2A_LABEL"
        ),
        "reused_stage2b_checkpoint_labels": sum(
            1
            for item in attempts
            if item.get("transfer") == "REUSED_HASH_PINNED_STAGE2B_CHECKPOINT"
        ),
        "aggregate_network_bytes": accepted_network_bytes,
        "aggregate_max_bytes": contract["aggregate_max_bytes"],
        "event_matches": matches,
        "attempts": attempts,
    }
    manifest_payload = {
        "manifest_id": "artemis2-stage2b-saw3-label-scan-manifest-v1",
        "inventory_sha256": fallback["sha256"],
        "files": manifest,
    }
    write_json(root / "evidence" / "stage2b" / "label-scan-receipt.json", receipt)
    write_json(root / "evidence" / "stage2b" / "label-scan-manifest.json", manifest_payload)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    receipt = scan(args.root.resolve())
    summary = {
        key: receipt[key]
        for key in (
            "status",
            "error",
            "inventory_members",
            "accepted_labels",
            "network_downloaded_labels",
            "reused_stage2a_labels",
            "reused_stage2b_checkpoint_labels",
            "aggregate_network_bytes",
            "aggregate_max_bytes",
        )
    }
    summary["event_matches"] = {
        event_id: [item["time_utc"] for item in items]
        for event_id, items in receipt["event_matches"].items()
    }
    print(json.dumps(summary, indent=2))
    return 0 if receipt["status"] == "COMPLETED" else 1


if __name__ == "__main__":
    sys.exit(main())
