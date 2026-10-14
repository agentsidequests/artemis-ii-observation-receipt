#!/usr/bin/env python3
"""Run the three frozen Stage 2B Atlas metadata queries and select SAW3 candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")


def post_bounded(endpoint: str, body: bytes, max_bytes: int) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        endpoint,
        method="POST",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Artemis-II-Testbed/0.4",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        if response.status != 200:
            raise ValueError(f"Atlas returned HTTP {response.status}")
        raw_length = response.headers.get("Content-Length")
        if raw_length is not None and int(raw_length) > max_bytes:
            raise ValueError(f"Atlas declared {raw_length} bytes, above cap {max_bytes}")
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"Atlas response exceeded cap {max_bytes}")
        headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"content-length", "content-type", "etag", "last-modified"}
        }
        return data, headers


def one(value: Any) -> str | None:
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value) if value is not None else None


def atlas_uri_to_archive_path(uri: str) -> str:
    marker = ":/artemis2_orion_camera/"
    if marker not in uri:
        raise ValueError(f"Unexpected Artemis II Orion URI: {uri}")
    return uri.split(marker, 1)[1]


def select_saw3(payload: dict[str, Any], event: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
    hits_container = payload.get("hits", {})
    total_value = hits_container.get("total", {}).get("value")
    hits = hits_container.get("hits", [])
    if not isinstance(total_value, int) or not isinstance(hits, list):
        raise ValueError("Atlas response has no exact hit count")
    if total_value != len(hits):
        raise ValueError(f"Atlas returned {len(hits)} of {total_value} hits")

    selected: list[dict[str, Any]] = []
    for hit in hits:
        source = hit.get("_source", {})
        gather = source.get("gather", {})
        pds_archive = gather.get("pds_archive", {})
        file_name = pds_archive.get("file_name")
        if source.get("bundle_id") != "artemis2_orion_camera":
            continue
        if source.get("collection_id") != "data_raw_image":
            continue
        if not isinstance(file_name, str) or not file_name.endswith("_saw3_raw_v01.tif"):
            continue
        start_utc = gather.get("time", {}).get("start_time")
        related = pds_archive.get("related", {})
        label_uri = related.get("label", {}).get("uri")
        browse_uri = related.get("browse", {}).get("uri")
        pds4_label = source.get("pds4_label", {})
        label_file_ref = one(pds4_label.get("ops:Label_File_Info/ops:file_ref"))
        if not all(isinstance(value, str) for value in (start_utc, label_uri, browse_uri, label_file_ref)):
            raise ValueError(f"Selected SAW3 record lacks source identity: {file_name}")
        selected.append(
            {
                "time_utc": start_utc,
                "data_file_name": file_name,
                "raw_label_archive_path": label_file_ref.lstrip("/"),
                "raw_label_uri": label_uri,
                "browse_image_archive_path": atlas_uri_to_archive_path(browse_uri),
                "browse_image_uri": browse_uri,
                "lid": source.get("lid"),
                "lidvid": source.get("lidvid"),
            }
        )
    selected.sort(key=lambda item: item["time_utc"])
    if len(selected) != event["frame_count"]:
        raise ValueError(
            f"{event['event_id']} selected {len(selected)} SAW3 frames, expected {event['frame_count']}"
        )
    observed_times = [item["time_utc"] for item in selected]
    if observed_times[0] != event["candidate_time_range_utc"][0]:
        raise ValueError(f"{event['event_id']} first time differs from frozen range")
    if observed_times[-1] != event["candidate_time_range_utc"][1]:
        raise ValueError(f"{event['event_id']} last time differs from frozen range")
    parsed_times = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in observed_times]
    cadence = [
        (parsed_times[index] - parsed_times[index - 1]).total_seconds()
        for index in range(1, len(parsed_times))
    ]
    if cadence != [30.0] * (len(parsed_times) - 1):
        raise ValueError(f"{event['event_id']} cadence is not a strict 30 seconds: {cadence}")
    return total_value, selected


def discover(root: Path, selected_event_ids: set[str] | None = None) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage2b.json")
    discovery = spec["candidate_discovery"]
    event_by_id = {event["event_id"]: event for event in spec["events"]}
    result_events: list[dict[str, Any]] = []
    status = "COMPLETED"
    error: str | None = None

    for event_id, relative_query_path in discovery["query_paths"].items():
        if selected_event_ids is not None and event_id not in selected_event_ids:
            continue
        query_path = root / relative_query_path
        query_bytes = query_path.read_bytes()
        response_path = root / "evidence" / "stage2b" / f"atlas-response-{event_id}.json"
        record: dict[str, Any] = {
            "event_id": event_id,
            "query_path": relative_query_path,
            "query_bytes": len(query_bytes),
            "query_sha256": sha256_bytes(query_bytes),
            "queried_at_utc": utc_now(),
        }
        try:
            response_bytes, headers = post_bounded(
                discovery["endpoint"], query_bytes, discovery["max_response_bytes_each"]
            )
            write_bytes(response_path, response_bytes)
            response = json.loads(response_bytes)
            if not isinstance(response, dict):
                raise ValueError("Atlas response is not an object")
            total_hits, selected = select_saw3(response, event_by_id[event_id])
            if total_hits > discovery["max_hits_each"]:
                raise ValueError(f"Atlas total {total_hits} exceeds cap")
            record.update(
                {
                    "status": "ACCEPTED",
                    "response_path": response_path.relative_to(root).as_posix(),
                    "response_bytes": len(response_bytes),
                    "response_sha256": sha256_bytes(response_bytes),
                    "response_headers": headers,
                    "total_hits": total_hits,
                    "selected_count": len(selected),
                    "selected": selected,
                }
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            status = "STOPPED"
            error = f"{event_id}: {exc}"
            record.update({"status": "STOPPED", "error": str(exc)})
        result_events.append(record)
        if status == "STOPPED":
            break

    receipt = {
        "receipt_id": "artemis2-stage2b-atlas-candidate-discovery-v1",
        "completed_at_utc": utc_now(),
        "endpoint": discovery["endpoint"],
        "status": status,
        "error": error,
        "events": result_events,
    }
    if selected_event_ids is None:
        receipt_name = "atlas-discovery-receipt.json"
    else:
        ordered_ids = [
            event_id
            for event_id in discovery["query_paths"]
            if event_id in selected_event_ids
        ]
        receipt_name = "atlas-discovery-receipt-" + "-".join(ordered_ids) + ".json"
    write_json(root / "evidence" / "stage2b" / receipt_name, receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--event",
        action="append",
        choices=("earthset", "sunset", "sunrise"),
        help="Run only the named frozen event query; may be repeated.",
    )
    args = parser.parse_args(argv)
    event_filter = set(args.event) if args.event else None
    receipt = discover(args.root.resolve(), event_filter)
    summary = {
        "status": receipt["status"],
        "error": receipt["error"],
        "events": [
            {
                "event_id": event["event_id"],
                "status": event["status"],
                "total_hits": event.get("total_hits"),
                "selected_count": event.get("selected_count"),
                "times": [item["time_utc"] for item in event.get("selected", [])],
            }
            for event in receipt["events"]
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0 if receipt["status"] == "COMPLETED" else 1


if __name__ == "__main__":
    sys.exit(main())
