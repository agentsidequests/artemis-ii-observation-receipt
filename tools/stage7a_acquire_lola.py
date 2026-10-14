#!/usr/bin/env python3
"""Acquire bounded LOLA latitude strips for the frozen Stage 7A canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
USER_AGENT = "Artemis-II-Testbed/0.7a"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
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


def pixel_latitude(line_index: int, contract: dict[str, Any]) -> float:
    return (
        contract["line_projection_offset_pixels"] - line_index
    ) / contract["map_resolution_pixels_per_degree"]


def required_line_range(spec: dict[str, Any], semantic: dict[str, Any]) -> tuple[int, int]:
    contract = spec["raster_contract"]
    radius_km = max(spec["regions"]["robustness_radii_km"])
    angular_radius_deg = math.degrees(radius_km / contract["moon_radius_km"])
    centers = [
        item
        for item in semantic["feature_coordinates"].values()
        if isinstance(item, dict) and "latitude_deg" in item
    ]
    if len(centers) != 2:
        raise ValueError(f"Expected exactly two feature centers, observed {len(centers)}")
    minimum_latitude = min(item["latitude_deg"] for item in centers) - angular_radius_deg
    maximum_latitude = max(item["latitude_deg"] for item in centers) + angular_radius_deg
    lines = [
        line_index
        for line_index in range(contract["lines"])
        if minimum_latitude <= pixel_latitude(line_index, contract) <= maximum_latitude
    ]
    if not lines or lines != list(range(lines[0], lines[-1] + 1)):
        raise ValueError("The required latitude strip is empty or non-contiguous")
    return lines[0], lines[-1]


def retained_headers(headers: Any) -> dict[str, str]:
    allowed = {
        "content-length",
        "content-range",
        "content-type",
        "etag",
        "last-modified",
    }
    return {
        key.lower(): value
        for key, value in headers.items()
        if key.lower() in allowed
    }


def get_bytes(url: str, *, byte_range: tuple[int, int] | None = None) -> tuple[bytes, int, str, dict[str, str]]:
    headers = {"User-Agent": USER_AGENT}
    if byte_range is not None:
        headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"
    request = urllib.request.Request(url, method="GET", headers=headers)
    with urllib.request.urlopen(request, timeout=90) as response:
        body = response.read()
        return body, response.status, response.geturl(), retained_headers(response.headers)


def label_value(text: str, field: str) -> str:
    match = re.search(rf"^\s*{re.escape(field)}\s*=\s*([^\r\n]+)", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"Missing {field} in PDS label")
    return match.group(1).strip().strip('"')


def validate_label(text: str, product: dict[str, Any], contract: dict[str, Any]) -> None:
    expected = {
        "PRODUCT_ID": product["id"].upper(),
        "FILE_RECORDS": str(contract["lines"]),
        "RECORD_BYTES": str(contract["pds_label_record_bytes_reported"]),
        "LINES": str(contract["lines"]),
        "LINE_SAMPLES": str(contract["line_samples"]),
        "SAMPLE_TYPE": contract["sample_type"],
        "SAMPLE_BITS": str(contract["sample_bits"]),
        "MAP_RESOLUTION": f"{contract['map_resolution_pixels_per_degree']} <pix/deg>",
    }
    actual = {field: label_value(text, field) for field in expected}
    if actual != expected:
        raise ValueError(f"PDS label contract mismatch: expected {expected}, observed {actual}")
    if f"{product['baseline_m']}-m" not in text:
        raise ValueError(f"PDS label does not bind the {product['baseline_m']} m baseline")


def acquire(root: Path) -> dict[str, Any]:
    spec_path = root / "spec" / "stage7a.json"
    spec = load_json(spec_path)
    semantic_path = root / spec["semantic_evidence"]["path"]
    semantic = load_json(semantic_path)
    semantic_hash = sha256_file(semantic_path)
    if semantic_hash != spec["semantic_evidence"]["sha256"]:
        raise ValueError("Semantic evidence changed after the Stage 7A freeze")
    if not semantic.get("frozen_before_lola_value_access"):
        raise ValueError("Semantic coding is not marked frozen before LOLA value access")

    source_root = root / "evidence" / "stage7a" / "source"
    work_root = root / "work" / "stage7a-acquisition"
    source_root.mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=True, exist_ok=True)

    contract = spec["raster_contract"]
    acquisition = spec["acquisition"]
    line_start, line_end = required_line_range(spec, semantic)
    expected_remote_total = (
        contract["lines"]
        * contract["line_samples"]
        * contract["sample_bits"]
        // 8
    )
    if expected_remote_total != acquisition["require_remote_total_bytes"]:
        raise ValueError(
            "Physical raster geometry does not match the frozen remote byte count"
        )
    if contract["physical_row_bytes"] != (
        contract["line_samples"] * contract["sample_bits"] // 8
    ):
        raise ValueError("Physical row stride does not match sample geometry")
    byte_start = line_start * contract["physical_row_bytes"]
    byte_end = (line_end + 1) * contract["physical_row_bytes"] - 1
    expected_strip_bytes = byte_end - byte_start + 1
    remote_total = acquisition["require_remote_total_bytes"]

    label_bytes_total = 0
    img_bytes_total = 0
    items: list[dict[str, Any]] = []
    manifest_files: list[dict[str, Any]] = []
    started_at = utc_now()

    for product in spec["source_products"]:
        label_body, label_status, label_resolved, label_headers = get_bytes(product["label_url"])
        if label_status != 200:
            raise ValueError(f"{product['id']} label returned HTTP {label_status}, expected 200")
        label_bytes_total += len(label_body)
        if label_bytes_total > acquisition["maximum_total_label_bytes"]:
            raise ValueError("PDS labels exceeded the frozen byte budget")
        label_text = label_body.decode("ascii")
        validate_label(label_text, product, contract)
        label_path = source_root / f"{product['id']}.LBL"
        label_temp = work_root / f"{product['id']}.LBL.partial"
        label_temp.write_bytes(label_body)
        shutil.move(str(label_temp), str(label_path))
        label_hash = sha256_file(label_path)

        strip_body, strip_status, strip_resolved, strip_headers = get_bytes(
            product["img_url"], byte_range=(byte_start, byte_end)
        )
        expected_content_range = f"bytes {byte_start}-{byte_end}/{remote_total}"
        if strip_status != acquisition["required_http_status"]:
            raise ValueError(
                f"{product['id']} strip returned HTTP {strip_status}, expected {acquisition['required_http_status']}"
            )
        if strip_headers.get("content-range") != expected_content_range:
            raise ValueError(
                f"{product['id']} returned Content-Range {strip_headers.get('content-range')!r}, expected {expected_content_range!r}"
            )
        if len(strip_body) != expected_strip_bytes:
            raise ValueError(
                f"{product['id']} strip has {len(strip_body)} bytes, expected {expected_strip_bytes}"
            )
        img_bytes_total += len(strip_body)
        if img_bytes_total > acquisition["maximum_total_img_bytes"]:
            raise ValueError("LOLA strips exceeded the frozen image-byte budget")
        if label_bytes_total + img_bytes_total > acquisition["maximum_total_network_bytes"]:
            raise ValueError("Stage 7A acquisition exceeded the frozen total network-byte budget")
        strip_path = source_root / f"{product['id']}-lines-{line_start}-{line_end}.bin"
        strip_temp = work_root / f"{product['id']}.bin.partial"
        strip_temp.write_bytes(strip_body)
        shutil.move(str(strip_temp), str(strip_path))
        strip_hash = sha256_file(strip_path)

        items.append(
            {
                "product_id": product["id"],
                "baseline_m": product["baseline_m"],
                "label": {
                    "url": product["label_url"],
                    "resolved_url": label_resolved,
                    "status": label_status,
                    "headers": label_headers,
                    "bytes": len(label_body),
                    "sha256": label_hash,
                    "local_path": label_path.relative_to(root).as_posix(),
                },
                "strip": {
                    "url": product["img_url"],
                    "resolved_url": strip_resolved,
                    "status": strip_status,
                    "headers": strip_headers,
                    "byte_range": [byte_start, byte_end],
                    "line_range_zero_based_inclusive": [line_start, line_end],
                    "bytes": len(strip_body),
                    "sha256": strip_hash,
                    "local_path": strip_path.relative_to(root).as_posix(),
                },
            }
        )
        manifest_files.extend(
            [
                {
                    "product_id": product["id"],
                    "kind": "pds_label",
                    "path": label_path.relative_to(root).as_posix(),
                    "bytes": len(label_body),
                    "sha256": label_hash,
                },
                {
                    "product_id": product["id"],
                    "kind": "latitude_strip",
                    "path": strip_path.relative_to(root).as_posix(),
                    "bytes": len(strip_body),
                    "sha256": strip_hash,
                    "line_range_zero_based_inclusive": [line_start, line_end],
                    "byte_range_inclusive": [byte_start, byte_end],
                },
            ]
        )

    receipt = {
        "receipt_id": "artemis2-stage7a-lola-bounded-acquisition-v1",
        "status": "COMPLETED",
        "started_at_utc": started_at,
        "completed_at_utc": utc_now(),
        "spec_path": spec_path.relative_to(root).as_posix(),
        "spec_sha256": sha256_file(spec_path),
        "semantic_path": semantic_path.relative_to(root).as_posix(),
        "semantic_sha256": semantic_hash,
        "semantic_frozen_before_lola_value_access": True,
        "line_range_zero_based_inclusive": [line_start, line_end],
        "latitude_centers_deg": [
            pixel_latitude(line_start, contract),
            pixel_latitude(line_end, contract),
        ],
        "img_bytes": img_bytes_total,
        "label_bytes": label_bytes_total,
        "network_bytes": img_bytes_total + label_bytes_total,
        "network_budget_bytes": acquisition["maximum_total_network_bytes"],
        "items": items,
    }
    manifest = {
        "manifest_id": "artemis2-stage7a-lola-source-manifest-v1",
        "source_class": "NASA LRO LOLA PDS3 bounded latitude strips",
        "files": manifest_files,
    }
    write_json(root / "evidence" / "stage7a" / "acquisition-receipt.json", receipt)
    write_json(root / "evidence" / "stage7a" / "source-manifest.json", manifest)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        receipt = acquire(args.root.resolve())
    except (OSError, ValueError, UnicodeError, urllib.error.URLError) as exc:
        print(json.dumps({"status": "STOPPED", "error": str(exc)}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "line_range_zero_based_inclusive": receipt[
                    "line_range_zero_based_inclusive"
                ],
                "img_bytes": receipt["img_bytes"],
                "label_bytes": receipt["label_bytes"],
                "network_bytes": receipt["network_bytes"],
                "network_budget_bytes": receipt["network_budget_bytes"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
