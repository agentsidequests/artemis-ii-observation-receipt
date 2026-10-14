#!/usr/bin/env python3
"""Acquire Stage 10D Atlas snapshots and official NASA/PDS documentation."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader


UTC = timezone.utc


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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


def source_record(root: Path, path: Path, url: str, role: str, **extra: Any) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "url": url,
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "role": role,
        **extra,
    }


def acquire(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage10d.json")
    contract = spec["source_contract"]
    expected = spec["frozen_observables"]
    source_dir = root / "evidence" / "stage10d" / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    sources: list[dict[str, Any]] = []

    atlas_expected = {
        "mission_footprint": expected["mission_products"],
        "forward_look_products": expected["forward_look_product_records"],
        "forward_look_actions": expected["forward_look_action_product_records"],
    }
    for name, relative_query_path in contract["atlas_queries"].items():
        query_path = root / relative_query_path
        query_bytes = query_path.read_bytes()
        request = urllib.request.Request(
            contract["atlas_endpoint"],
            method="POST",
            data=query_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Artemis-II-Testbed/1.0-stage10d",
            },
        )
        response_bytes, response_headers = fetch(request, 2_000_000)
        response = json.loads(response_bytes)
        total = response.get("hits", {}).get("total", {})
        if total.get("relation") != "eq" or total.get("value") != atlas_expected[name]:
            raise ValueError(f"Atlas {name} total changed: {total!r}")
        response_path = source_dir / f"atlas-{name.replace('_', '-')}-response.json"
        response_path.write_bytes(response_bytes)
        sources.extend(
            [
                source_record(root, query_path, contract["atlas_endpoint"], f"frozen {name} query"),
                source_record(
                    root,
                    response_path,
                    contract["atlas_endpoint"],
                    f"Atlas {name} response",
                    headers=response_headers,
                ),
            ]
        )

    nasa_request = urllib.request.Request(
        contract["nasa_release_url"],
        headers={"Accept": "text/html", "User-Agent": "Artemis-II-Testbed/1.0-stage10d"},
    )
    nasa_bytes, nasa_headers = fetch(nasa_request, 1_000_000)
    if b"more than 800 gigabytes" not in nasa_bytes.lower():
        raise ValueError("NASA release no longer contains the frozen size statement")
    nasa_path = root / contract["nasa_release_path"]
    nasa_path.write_bytes(nasa_bytes)
    sources.append(
        source_record(root, nasa_path, contract["nasa_release_url"], "official NASA release statement", headers=nasa_headers)
    )

    guide_request = urllib.request.Request(
        contract["user_guide_url"],
        headers={"Accept": "application/pdf", "User-Agent": "Artemis-II-Testbed/1.0-stage10d"},
    )
    guide_bytes, guide_headers = fetch(guide_request, 12_000_000)
    if not guide_bytes.startswith(b"%PDF"):
        raise ValueError("Data User Guide response is not a PDF")
    guide_path = root / contract["user_guide_path"]
    guide_path.write_bytes(guide_bytes)
    reader = PdfReader(io.BytesIO(guide_bytes))
    guide_text = "\n\n".join(
        f"--- PDF page {index + 1} ---\n{page.extract_text() or ''}"
        for index, page in enumerate(reader.pages)
    ) + "\n"
    guide_text_bytes = guide_text.encode("utf-8")
    guide_text_path = root / contract["user_guide_text_path"]
    guide_text_path.write_bytes(guide_text_bytes)
    normalized = " ".join(guide_text.lower().split())
    required = (
        "source nikon d5 and z9 camera images",
        "converted raw nikon d5 and z9 images",
        "processed nikon d5 and z9 images",
        "by comparing the timeline in the ltp with the timestamp of each data item",
        "the analyst designated activity overrides the ltp timeline activity",
    )
    if not all(phrase in normalized for phrase in required):
        raise ValueError("Data User Guide extraction lacks a frozen decision-bearing phrase")
    sources.extend(
        [
            source_record(root, guide_path, contract["user_guide_url"], "official Artemis II Data User Guide", headers=guide_headers),
            source_record(root, guide_text_path, contract["user_guide_url"], "deterministic full-text extraction of official Data User Guide", extractor="pypdf"),
        ]
    )

    receipt = {
        "receipt_id": "artemis2-stage10d-archive-unit-acquisition-v1",
        "completed_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": "COMPLETED",
        "pixel_payload_bytes": 0,
        "sources": sources,
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
