#!/usr/bin/env python3
"""Acquire every representation of Stage 10E's fractured camera actions."""

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
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def local_record(root: Path, path: Path, role: str, **extra: Any) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "role": role,
        **extra,
    }


def acquire(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage10g.json")
    contract = spec["source_contract"]
    expected = spec["frozen_observables"]
    stage10e_path = root / contract["stage10e_result_path"]
    stage10e = load_json(stage10e_path)
    internal_ids = sorted(
        {
            file_name.split("_")[0]
            for action in stage10e["activity_fractures"]
            for file_name in action["file_names"]
        }
    )
    if (
        len(stage10e["activity_fractures"]) != expected["fractured_actions"]
        or len(internal_ids) != expected["exposure_ids"]
    ):
        raise ValueError("Stage 10E fractured-action or exposure-ID denominator changed")
    query = {
        "_source": [
            "bundle_id",
            "collection_id",
            "archive.size",
            "gather.pds_archive.file_name",
            "pds4_label.msn:Mission_Information/msn:internal_id",
            "pds4_label.msn_surface:Observational_Intent/msn_surface:activity_id",
            "pds4_label.msn_surface:Observational_Intent/msn_surface:target_id",
        ],
        "size": 300,
        "track_total_hits": True,
        "query": {
            "bool": {
                "must": [
                    {"match": {"gather.common.mission": "artemis2"}},
                    {"match": {"bundle_id": "artemis2_crew_camera"}},
                    {
                        "terms": {
                            "pds4_label.msn:Mission_Information/msn:internal_id": internal_ids
                        }
                    },
                ]
            }
        },
    }
    query_bytes = (json.dumps(query, indent=2) + "\n").encode("utf-8")
    query_path = root / contract["atlas_query_path"]
    query_path.parent.mkdir(parents=True, exist_ok=True)
    query_path.write_bytes(query_bytes)
    request = urllib.request.Request(
        contract["atlas_endpoint"],
        method="POST",
        data=query_bytes,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Artemis-II-Testbed/1.0-stage10g",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        response_bytes = response.read(contract["max_response_bytes"] + 1)
        response_headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"content-length", "content-type", "etag", "last-modified"}
        }
    if len(response_bytes) > contract["max_response_bytes"]:
        raise ValueError("Atlas response exceeded cap")
    response = json.loads(response_bytes)
    total = response.get("hits", {}).get("total", {})
    hits = response.get("hits", {}).get("hits", [])
    if (
        total.get("relation") != "eq"
        or total.get("value") != expected["product_records"]
        or len(hits) != expected["product_records"]
    ):
        raise ValueError(f"Atlas fractured-product total changed: {total!r}, hits={len(hits)}")
    response_path = root / contract["atlas_response_path"]
    response_path.write_bytes(response_bytes)
    receipt = {
        "receipt_id": "artemis2-stage10g-fractured-product-acquisition-v1",
        "completed_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": "COMPLETED",
        "pixel_payload_bytes": 0,
        "sources": [
            local_record(root, stage10e_path, "verified fractured-action and exposure-ID denominator"),
            local_record(root, root / contract["stage10f_result_path"], "supported curation-mechanism result"),
            local_record(root, query_path, "frozen Atlas query for every fractured exposure identity", url=contract["atlas_endpoint"]),
            local_record(root, response_path, "Atlas products for every fractured exposure identity", url=contract["atlas_endpoint"], headers=response_headers),
        ],
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
