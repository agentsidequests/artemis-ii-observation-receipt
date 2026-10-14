#!/usr/bin/env python3
"""Acquire the frozen Stage 10A Atlas response and official label definitions."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
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
    spec = load_json(root / "spec" / "stage10a.json")
    contract = spec["source_contract"]
    query_path = root / contract["atlas_query_path"]
    query_bytes = query_path.read_bytes()
    expected = int(contract["expected_hits"])
    page_size = int(contract["page_size"])
    expected_pages = int(contract["expected_pages"])
    page_directory = root / contract["atlas_page_directory"]
    page_directory.mkdir(parents=True, exist_ok=True)
    page_receipts: list[dict[str, Any]] = []
    returned_ids: list[str] = []
    base_query = load_json(query_path)
    for page_index in range(expected_pages):
        request_payload = deepcopy(base_query)
        request_payload["from"] = page_index * page_size
        request_bytes = (json.dumps(request_payload, separators=(",", ":")) + "\n").encode("utf-8")
        atlas_request = urllib.request.Request(
            contract["atlas_endpoint"],
            method="POST",
            data=request_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Artemis-II-Testbed/1.0-stage10a",
            },
        )
        atlas_bytes, atlas_headers = fetch(
            atlas_request, int(contract["max_response_bytes_each"])
        )
        atlas = json.loads(atlas_bytes)
        total = atlas.get("hits", {}).get("total", {})
        hits = atlas.get("hits", {}).get("hits", [])
        expected_on_page = min(page_size, expected - page_index * page_size)
        if (
            total.get("relation") != "eq"
            or total.get("value") != expected
            or len(hits) != expected_on_page
        ):
            raise ValueError(
                f"Atlas page {page_index} completeness failed: total={total!r}, "
                f"returned={len(hits)}, expected_on_page={expected_on_page}"
            )
        ids = [str(hit.get("_id")) for hit in hits]
        if any(value == "None" for value in ids):
            raise ValueError(f"Atlas page {page_index} contains a hit without _id")
        returned_ids.extend(ids)
        request_path = page_directory / f"request-{page_index:02d}.json"
        response_path = page_directory / f"response-{page_index:02d}.json"
        request_path.write_bytes(request_bytes)
        response_path.write_bytes(atlas_bytes)
        page_receipts.append(
            {
                "page_index": page_index,
                "from": page_index * page_size,
                "hits": len(hits),
                "request_path": request_path.relative_to(root).as_posix(),
                "request_bytes": len(request_bytes),
                "request_sha256": sha256_bytes(request_bytes),
                "response_path": response_path.relative_to(root).as_posix(),
                "response_bytes": len(atlas_bytes),
                "response_sha256": sha256_bytes(atlas_bytes),
                "response_headers": atlas_headers,
            }
        )
    if len(returned_ids) != expected or len(set(returned_ids)) != expected:
        raise ValueError(
            f"Atlas pagination identity failed: returned={len(returned_ids)}, "
            f"unique={len(set(returned_ids))}, expected={expected}"
        )

    definitions_request = urllib.request.Request(
        contract["label_definitions_url"],
        headers={"Accept": "text/html", "User-Agent": "Artemis-II-Testbed/1.0-stage10a"},
    )
    definitions_bytes, definitions_headers = fetch(definitions_request, 3_000_000)
    required_phrases = (
        b"Identifier specifying the activity this observation is a part of",
        b"These were not thoroughly verified post-mission and may contain errors",
    )
    if not all(phrase in definitions_bytes for phrase in required_phrases):
        raise ValueError("Official label definitions lack the frozen decision-bearing phrases")

    definitions_path = root / contract["label_definitions_path"]
    definitions_path.write_bytes(definitions_bytes)

    receipt = {
        "receipt_id": "artemis2-stage10a-metadata-acquisition-v1",
        "completed_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": "COMPLETED",
        "pixel_payload_bytes": 0,
        "sources": [
            {
                "path": contract["atlas_query_path"],
                "url": contract["atlas_endpoint"],
                "bytes": len(query_bytes),
                "sha256": sha256_bytes(query_bytes),
                "role": "frozen query",
            },
            {
                "path": contract["label_definitions_path"],
                "url": contract["label_definitions_url"],
                "bytes": len(definitions_bytes),
                "sha256": sha256_bytes(definitions_bytes),
                "headers": definitions_headers,
                "role": "official field definitions and target-tag limitation",
            },
        ],
        "atlas_pages": page_receipts,
    }
    receipt_path = root / "evidence" / "stage10a" / "acquisition-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        receipt = acquire(args.root.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "STOPPED", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
