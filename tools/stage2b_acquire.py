#!/usr/bin/env python3
"""Acquire only the exact, budget-frozen Stage 2B PDS files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc
CHUNK_BYTES = 64 * 1024


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
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")


def source_items(spec: dict[str, Any]) -> list[dict[str, Any]]:
    templates = spec["source_template"]
    items: list[dict[str, Any]] = []
    for event in spec["events"]:
        if event["source_disposition"] != "ADMISSIBLE_SOURCE_SEQUENCE":
            continue
        for frame in event["selected_frames"]:
            raw_name = Path(frame["raw_label_path"]).name
            suffix = "_raw_v01.xml"
            if not raw_name.endswith(suffix):
                raise ValueError(f"Unexpected raw-label identity: {raw_name}")
            product_stem = raw_name[: -len(suffix)]
            for kind, archive_template in templates.items():
                archive_path = archive_template.replace(
                    "{raw_product_stem_without_raw}", product_stem
                )
                items.append(
                    {
                        "event_id": event["event_id"],
                        "event_max_bytes": event["max_bytes"],
                        "time_utc": frame["time_utc"],
                        "raw_label_path": frame["raw_label_path"],
                        "raw_label_sha256": frame["sha256"],
                        "kind": kind,
                        "archive_path": archive_path,
                        "url": spec["oracle"]["archive_base"] + archive_path,
                        "file_name": Path(archive_path).name,
                    }
                )
    return items


def range_probe(url: str) -> tuple[int, str, dict[str, str]]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "Artemis-II-Testbed/0.4", "Range": "bytes=0-0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 206:
            raise ValueError(f"Range probe returned HTTP {response.status}, expected 206")
        content_range = response.headers.get("Content-Range")
        match = re.fullmatch(r"bytes 0-0/(\d+)", content_range or "")
        if match is None:
            raise ValueError(f"Range probe returned invalid Content-Range {content_range!r}")
        body = response.read(2)
        if len(body) != 1:
            raise ValueError(f"Range probe returned {len(body)} body bytes, expected 1")
        headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower()
            in {"content-length", "content-range", "content-type", "etag", "last-modified"}
        }
        return int(match.group(1)), response.geturl(), headers


def download_exact(url: str, expected_bytes: int, temp_path: Path) -> tuple[str, dict[str, str]]:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "Artemis-II-Testbed/0.4"})
    digest = hashlib.sha256()
    received = 0
    with urllib.request.urlopen(request, timeout=90) as response, temp_path.open("wb") as handle:
        response_length = response.headers.get("Content-Length")
        if response_length is None or int(response_length) != expected_bytes:
            raise ValueError(
                f"GET Content-Length {response_length!r} does not match range-declared length {expected_bytes}"
            )
        while True:
            chunk = response.read(CHUNK_BYTES)
            if not chunk:
                break
            received += len(chunk)
            if received > expected_bytes:
                raise ValueError("GET body exceeded declared Content-Length")
            handle.write(chunk)
            digest.update(chunk)
        headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"content-length", "content-type", "etag", "last-modified"}
        }
    if received != expected_bytes:
        raise ValueError(
            f"GET body length {received} does not match range-declared length {expected_bytes}"
        )
    return digest.hexdigest(), headers


def acquire(root: Path) -> dict[str, Any]:
    spec_path = root / "spec" / "stage2b.json"
    spec = load_json(spec_path)
    budget = spec["acquisition_budget"]
    pixel_budget = budget["pixel_subset"]
    evidence_root = root / "evidence" / "stage2b"
    source_root = evidence_root / "source"
    temp_root = root / "work" / "stage2b-acquisition"
    temp_root.mkdir(parents=True, exist_ok=True)

    aggregate_accepted = 0
    per_event_accepted = {event["event_id"]: 0 for event in spec["events"]}
    receipt_items: list[dict[str, Any]] = []
    manifest_files: list[dict[str, Any]] = []
    status = "COMPLETED"
    error: str | None = None

    for item in source_items(spec):
        record = dict(item)
        record["range_probe_at_utc"] = utc_now()
        try:
            declared_bytes, resolved_url, range_headers = range_probe(item["url"])
            record.update(
                {
                    "declared_bytes": declared_bytes,
                    "resolved_url": resolved_url,
                    "range_probe_headers": range_headers,
                    "range_probe_body_bytes": 1,
                }
            )
            per_file_cap = (
                budget["max_jpeg_bytes_each"]
                if item["kind"] == "browse_image"
                else budget["max_label_bytes_each"]
            )
            if declared_bytes > per_file_cap:
                raise ValueError(
                    f"Declared length {declared_bytes} exceeds {item['kind']} cap {per_file_cap}"
                )
            event_remaining = item["event_max_bytes"] - per_event_accepted[item["event_id"]]
            aggregate_remaining = pixel_budget["aggregate_max_bytes"] - aggregate_accepted
            if declared_bytes > event_remaining:
                raise ValueError(
                    f"Declared length {declared_bytes} exceeds event remaining budget {event_remaining}"
                )
            if declared_bytes > aggregate_remaining:
                raise ValueError(
                    f"Declared length {declared_bytes} exceeds aggregate remaining budget {aggregate_remaining}"
                )

            event_dir = source_root / item["event_id"]
            event_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_root / (item["event_id"] + "-" + item["file_name"] + ".partial")
            if temp_path.exists():
                temp_path.unlink()
            record["get_at_utc"] = utc_now()
            digest, get_headers = download_exact(item["url"], declared_bytes, temp_path)
            destination = event_dir / item["file_name"]
            shutil.move(str(temp_path), str(destination))
            aggregate_accepted += declared_bytes
            per_event_accepted[item["event_id"]] += declared_bytes
            record.update(
                {
                    "status": "ACCEPTED",
                    "sha256": digest,
                    "get_headers": get_headers,
                    "local_path": destination.relative_to(root).as_posix(),
                    "aggregate_accepted_bytes": aggregate_accepted,
                    "event_accepted_bytes": per_event_accepted[item["event_id"]],
                }
            )
            manifest_files.append(
                {
                    "event_id": item["event_id"],
                    "kind": item["kind"],
                    "path": destination.relative_to(root).as_posix(),
                    "archive_path": item["archive_path"],
                    "bytes": declared_bytes,
                    "sha256": digest,
                }
            )
        except (OSError, ValueError, urllib.error.URLError) as exc:
            record["status"] = "STOPPED"
            record["error"] = str(exc)
            status = "STOPPED"
            error = f"{item['event_id']}:{item['file_name']}: {exc}"
            receipt_items.append(record)
            break
        receipt_items.append(record)

    receipt = {
        "receipt_id": "artemis2-stage2b-bounded-acquisition-v1",
        "started_from_frozen_spec": "spec/stage2b.json",
        "spec_sha256": sha256_file(spec_path),
        "completed_at_utc": utc_now(),
        "status": status,
        "error": error,
        "aggregate_max_bytes": pixel_budget["aggregate_max_bytes"],
        "aggregate_accepted_bytes": aggregate_accepted,
        "per_event_accepted_bytes": per_event_accepted,
        "requested_file_count": len(source_items(spec)),
        "accepted_file_count": len(manifest_files),
        "items": receipt_items,
    }
    manifest = {
        "manifest_id": "artemis2-stage2b-saw3-source-manifest-v1",
        "bundle_lidvid": spec["oracle"]["bundle_lidvid"],
        "archive_base": spec["oracle"]["archive_base"],
        "files": manifest_files,
    }
    evidence_root.mkdir(parents=True, exist_ok=True)
    write_json(evidence_root / "acquisition-receipt.json", receipt)
    write_json(evidence_root / "source-manifest.json", manifest)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    receipt = acquire(args.root.resolve())
    print(json.dumps({key: receipt[key] for key in (
        "status", "error", "requested_file_count", "accepted_file_count",
        "aggregate_max_bytes", "aggregate_accepted_bytes", "per_event_accepted_bytes"
    )}, indent=2))
    return 0 if receipt["status"] == "COMPLETED" else 1


if __name__ == "__main__":
    sys.exit(main())
