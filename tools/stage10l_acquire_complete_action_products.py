#!/usr/bin/env python3
"""Acquire metadata-only Atlas aggregation for Stage 10L's complete-action cohort."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10a_metadata_integrity import load_hits, load_json, normalize_hit  # noqa: E402
from stage10c_camera_action_integrity import detect_complete_brackets  # noqa: E402
from stage10e_all_days_integrity import load_daily_hits  # noqa: E402


UTC = timezone.utc


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def local_record(root: Path, path: Path, role: str, **extra: Any) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(payload), "sha256": sha256_bytes(payload), "role": role, **extra}


def complete_action_ids(root: Path, spec: dict[str, Any]) -> tuple[list[str], int]:
    contract = spec["source_contract"]
    fd6_hits, fd6_errors = load_hits(root, load_json(root / contract["stage10a_receipt_path"]))
    daily_hits, daily_errors = load_daily_hits(root, load_json(root / contract["stage10e_receipt_path"]))
    if fd6_errors or daily_errors:
        raise ValueError(f"Source page replay failed: {fd6_errors + daily_errors}")
    records = [normalize_hit(hit) for hit in daily_hits + fd6_hits]
    action_contract = copy.deepcopy(load_json(root / contract["stage10c_spec_path"])["complete_bracket_contract"])
    action_contract["allowed_bracket_sequences"] = load_json(root / "spec/stage10j.json")["expanded_patterns"]
    actions = detect_complete_brackets(records, action_contract)
    internal_ids = sorted({name.split("_")[0] for action in actions for name in action["file_names"]})
    return internal_ids, len(actions)


def acquire(root: Path) -> dict[str, Any]:
    spec = load_json(root / "spec/stage10l.json")
    contract, expected = spec["source_contract"], spec["frozen_observables"]
    internal_ids, actions = complete_action_ids(root, spec)
    if actions != expected["complete_actions"] or len(internal_ids) != expected["capture_identities"]:
        raise ValueError(f"Stage 10J cohort changed: actions={actions}, identities={len(internal_ids)}")
    internal_id_field = "pds4_label.msn:Mission_Information/msn:internal_id"
    batch_dir = root / contract["atlas_batch_dir"]
    batch_dir.mkdir(parents=True, exist_ok=True)
    batch_sources: list[dict[str, Any]] = []
    total_products = 0
    total_identities = 0
    response_headers: dict[str, str] = {}
    for batch_index, offset in enumerate(range(0, len(internal_ids), contract["batch_size"]), start=1):
        batch_ids = internal_ids[offset : offset + contract["batch_size"]]
        query = {
            "_source": ["collection_id", "archive.size", internal_id_field],
            "size": len(batch_ids) * expected["expected_products_per_identity"],
            "track_total_hits": True,
            "query": {"bool": {"must": [
                {"match": {"gather.common.mission": "artemis2"}},
                {"match": {"bundle_id": "artemis2_crew_camera"}},
                {"terms": {internal_id_field: batch_ids}},
            ]}},
        }
        query_bytes = (json.dumps(query, indent=2) + "\n").encode("utf-8")
        query_path = batch_dir / f"batch-{batch_index:02d}-query.json"
        response_path = batch_dir / f"batch-{batch_index:02d}-response.json"
        query_path.write_bytes(query_bytes)
        request = urllib.request.Request(contract["atlas_endpoint"], method="POST", data=query_bytes, headers={
            "Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Artemis-II-Testbed/1.0-stage10l",
        })
        with urllib.request.urlopen(request, timeout=180) as response:
            response_bytes = response.read(contract["max_response_bytes_per_batch"] + 1)
            response_headers = {key.lower(): value for key, value in response.headers.items() if key.lower() in {"content-length", "content-type", "etag", "last-modified"}}
        if len(response_bytes) > contract["max_response_bytes_per_batch"]:
            raise ValueError(f"Atlas batch {batch_index} response exceeded cap")
        payload = json.loads(response_bytes)
        total = payload.get("hits", {}).get("total", {})
        hits = payload.get("hits", {}).get("hits", [])
        if total.get("relation") != "eq" or total.get("value") != len(batch_ids) * expected["expected_products_per_identity"]:
            raise ValueError(f"Atlas batch {batch_index} product total changed: {total!r}")
        if len(hits) != total["value"]:
            raise ValueError(f"Atlas batch {batch_index} returned {len(hits)} of {total['value']} products")
        by_identity: dict[str, list[str]] = defaultdict(list)
        for hit in hits:
            source = hit.get("_source", {})
            values = source.get("pds4_label", {}).get("msn:Mission_Information/msn:internal_id", [])
            if len(values) != 1:
                raise ValueError(f"Atlas batch {batch_index} has a non-scalar internal ID: {values!r}")
            by_identity[str(values[0])].append(str(source.get("collection_id")))
        expected_collections = set(expected["expected_collections"])
        bad_identities = {
            identity: collections
            for identity, collections in by_identity.items()
            if len(collections) != expected["expected_products_per_identity"] or set(collections) != expected_collections
        }
        if set(by_identity) != set(batch_ids) or bad_identities:
            raise ValueError(f"Atlas batch {batch_index} identity parity failed: missing={len(set(batch_ids) - set(by_identity))}, bad={len(bad_identities)}")
        response_path.write_bytes(response_bytes)
        total_products += total["value"]
        total_identities += len(by_identity)
        batch_sources.extend([
            local_record(root, query_path, f"Atlas batch {batch_index} query", url=contract["atlas_endpoint"]),
            local_record(root, response_path, f"Atlas batch {batch_index} response", url=contract["atlas_endpoint"], headers=response_headers),
        ])
    if total_products != expected["expected_products"] or total_identities != expected["capture_identities"]:
        raise ValueError(f"Atlas batch totals changed: products={total_products}, identities={total_identities}")
    receipt = {
        "receipt_id": "artemis2-stage10l-complete-action-products-v1",
        "completed_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": "COMPLETED",
        "pixel_payload_bytes": 0,
        "route_recovery": {"initial_failure": "HTTP_403_LARGE_REQUEST", "failure_class": "SURFACE_PREREQUISITE_MISSING", "fallback": "same_endpoint_bounded_batches"},
        "cohort": {"complete_actions": actions, "capture_identities": len(internal_ids), "products": total_products, "batches": (len(internal_ids) + contract["batch_size"] - 1) // contract["batch_size"]},
        "sources": [
            local_record(root, root / contract["stage10j_result_path"], "verified Stage 10J action denominator"),
            local_record(root, root / contract["rejected_query_path"], "rejected all-cohort query; HTTP 403 before response", url=contract["atlas_endpoint"]),
            *batch_sources,
        ],
    }
    receipt_path = root / contract["receipt_path"]
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
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
