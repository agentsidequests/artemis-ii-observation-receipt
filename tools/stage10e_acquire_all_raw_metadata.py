#!/usr/bin/env python3
"""Acquire all Artemis II raw crew-camera metadata for Stage 10E."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fetch(request: urllib.request.Request, max_bytes: int) -> tuple[bytes, dict[str, str]]:
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status} for {request.full_url}")
        declared = response.headers.get("Content-Length")
        if declared is not None and int(declared) > max_bytes:
            raise ValueError(f"Declared response {declared} exceeds cap {max_bytes}")
        payload = response.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise ValueError(f"Response exceeds cap {max_bytes}")
        headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"content-length", "content-type", "etag", "last-modified"}
        }
        return payload, headers


def acquire(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage10e.json")
    contract = spec["source_contract"]
    query_path = root / contract["atlas_query_path"]
    query_bytes = query_path.read_bytes()
    base_query = load_json(query_path)
    expected = int(contract["expected_hits"])
    page_size = int(contract["page_size"])
    expected_counts = {
        str(day): int(count) for day, count in contract["expected_flight_day_counts"].items()
    }
    page_directory = root / contract["atlas_page_directory"]
    page_directory.mkdir(parents=True, exist_ok=True)
    pages: list[dict[str, Any]] = []
    returned_ids: list[str] = []
    for day in range(1, 11):
        if day == 6:
            continue
        payload = deepcopy(base_query)
        payload["query"]["bool"]["must"].append(
            {
                "match": {
                    "pds4_label.msn:Mission_Information/msn:flight_day_number": str(day)
                }
            }
        )
        payload["from"] = 0
        request_bytes = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        request = urllib.request.Request(
            contract["atlas_endpoint"],
            method="POST",
            data=request_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Artemis-II-Testbed/1.0-stage10e",
            },
        )
        response_bytes, response_headers = fetch(
            request, int(contract["max_response_bytes_each"])
        )
        response = json.loads(response_bytes)
        total = response.get("hits", {}).get("total", {})
        hits = response.get("hits", {}).get("hits", [])
        expected_on_page = expected_counts[str(day)]
        if (
            total.get("relation") != "eq"
            or total.get("value") != expected_on_page
            or len(hits) != expected_on_page
        ):
            raise ValueError(
                f"Atlas flight day {day} completeness failed: total={total!r}, "
                f"returned={len(hits)}, expected_on_page={expected_on_page}"
            )
        ids = [str(hit.get("_id")) for hit in hits]
        if any(value == "None" for value in ids):
            raise ValueError(f"Atlas flight day {day} contains a hit without _id")
        returned_ids.extend(ids)
        request_path = page_directory / f"request-fd{day:02d}.json"
        response_path = page_directory / f"response-fd{day:02d}.json"
        request_path.write_bytes(request_bytes)
        response_path.write_bytes(response_bytes)
        pages.append(
            {
                "flight_day": day,
                "from": 0,
                "hits": len(hits),
                "request_path": request_path.relative_to(root).as_posix(),
                "request_bytes": len(request_bytes),
                "request_sha256": sha256_bytes(request_bytes),
                "response_path": response_path.relative_to(root).as_posix(),
                "response_bytes": len(response_bytes),
                "response_sha256": sha256_bytes(response_bytes),
                "response_headers": response_headers,
            },
        )
        time.sleep(2)
    expected_non_fd6 = expected - expected_counts["6"]
    if len(returned_ids) != expected_non_fd6 or len(set(returned_ids)) != expected_non_fd6:
        raise ValueError(
            f"Atlas non-FD6 identity failed: returned={len(returned_ids)}, "
            f"unique={len(set(returned_ids))}, expected={expected_non_fd6}"
        )
    stage10a_receipt_path = root / contract["stage10a_receipt_path"]
    stage10a_receipt_bytes = stage10a_receipt_path.read_bytes()
    receipt = {
        "receipt_id": "artemis2-stage10e-all-raw-metadata-v1",
        "completed_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": "COMPLETED",
        "pixel_payload_bytes": 0,
        "sources": [
            {
                "path": contract["atlas_query_path"],
                "url": contract["atlas_endpoint"],
                "bytes": len(query_bytes),
                "sha256": sha256_bytes(query_bytes),
                "role": "frozen complete all-flight-day raw crew-camera query",
            },
            {
                "path": contract["stage10a_receipt_path"],
                "bytes": len(stage10a_receipt_bytes),
                "sha256": sha256_bytes(stage10a_receipt_bytes),
                "role": "preserved complete Flight Day 6 acquisition receipt reused as the dominant cohort",
            }
        ],
        "atlas_pages": pages,
    }
    receipt_path = root / contract["receipt_path"]
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        result = acquire(args.root.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "STOPPED", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
