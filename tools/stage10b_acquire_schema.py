#!/usr/bin/env python3
"""Acquire the exact official schema and freeze Stage 10B reused-source identities."""

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


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def source_record(root: Path, relative_path: str, role: str) -> dict[str, Any]:
    path = root / relative_path
    payload = path.read_bytes()
    return {
        "path": relative_path,
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "role": role,
    }


def acquire(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage10b.json")
    contract = spec["source_contract"]
    request = urllib.request.Request(
        contract["schema_url"],
        headers={
            "Accept": "application/xml,text/xml",
            "User-Agent": "Artemis-II-Testbed/1.0-stage10b",
        },
    )
    cap = int(contract["maximum_schema_bytes"])
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status} for {request.full_url}")
        payload = response.read(cap + 1)
        if len(payload) > cap:
            raise ValueError(f"Schema exceeds cap {cap}")
        headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"content-length", "content-type", "etag", "last-modified"}
        }
    required = (
        b'<xs:complexType name="Observational_Intent">',
        b'<xs:element name="activity_id" type="msn_surface:activity_id" minOccurs="0" maxOccurs="1">',
        b'<xs:simpleType name="activity_id">',
    )
    if not all(value in payload for value in required):
        raise ValueError("Official schema lacks the frozen activity cardinality declarations")

    schema_path = root / contract["schema_path"]
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_bytes(payload)
    sources = [
        {
            "path": contract["schema_path"],
            "url": contract["schema_url"],
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
            "headers": headers,
            "role": "official Observational_Intent and activity_id cardinality schema",
        },
        source_record(
            root,
            contract["stage10a_result_path"],
            "verified complete-cohort bracket result",
        ),
        source_record(
            root,
            contract["outgoing_target_request_path"],
            "mission target plan and request timing",
        ),
        source_record(
            root,
            contract["transcript_path"],
            "contemporaneous PCD3 transcript",
        ),
    ]
    receipt = {
        "receipt_id": "artemis2-stage10b-schema-and-reuse-v1",
        "completed_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "status": "COMPLETED",
        "pixel_payload_bytes": 0,
        "sources": sources,
    }
    receipt_path = root / contract["receipt_path"]
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
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
