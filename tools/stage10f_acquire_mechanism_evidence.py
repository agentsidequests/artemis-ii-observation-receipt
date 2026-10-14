#!/usr/bin/env python3
"""Acquire focused official evidence for Stage 10F's mechanism triangulation."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter


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
    spec = load_json(root / "spec" / "stage10f.json")
    contract = spec["source_contract"]
    source_dir = root / "evidence" / "stage10f" / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    api_request = urllib.request.Request(
        contract["ntrs_api_url"],
        headers={"Accept": "application/json", "User-Agent": "Artemis-II-Testbed/1.0-stage10f"},
    )
    with urllib.request.urlopen(api_request, timeout=120) as response:
        api_bytes = response.read(1_000_001)
        api_headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"content-length", "content-type", "etag", "last-modified"}
        }
    if len(api_bytes) > 1_000_000:
        raise ValueError("NTRS API response exceeded cap")
    api = json.loads(api_bytes)
    downloads = api.get("downloads", [])
    expected_download_path = urllib.parse.urlparse(contract["ntrs_download_url"]).path
    if (
        api.get("id") != 20260009221
        or api.get("title") != "Artemis II Preliminary Science Report"
        or not any(item.get("links", {}).get("original") == expected_download_path for item in downloads)
    ):
        raise ValueError("NTRS citation identity or official download link changed")
    api_path = root / contract["ntrs_api_path"]
    api_path.write_bytes(api_bytes)

    head_request = urllib.request.Request(
        contract["ntrs_download_url"],
        method="HEAD",
        headers={"User-Agent": "Artemis-II-Testbed/1.0-stage10f"},
    )
    with urllib.request.urlopen(head_request, timeout=120) as response:
        if response.status != 200:
            raise ValueError(f"Official report HEAD returned HTTP {response.status}")
        head_headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"content-length", "content-type", "etag", "last-modified"}
        }
    if int(head_headers.get("content-length", -1)) != contract["parent_report_bytes"]:
        raise ValueError("Official report content length changed")

    parent_path = root / contract["parent_report_work_path"]
    parent_bytes = parent_path.read_bytes()
    if (
        len(parent_bytes) != contract["parent_report_bytes"]
        or sha256_bytes(parent_bytes) != contract["parent_report_sha256"]
    ):
        raise ValueError("Local official parent report does not match the frozen identity")
    reader = PdfReader(io.BytesIO(parent_bytes))
    page_index = int(contract["report_page_number"]) - 1
    page = reader.pages[page_index]
    writer = PdfWriter()
    writer.add_page(page)
    page_buffer = io.BytesIO()
    writer.write(page_buffer)
    page_bytes = page_buffer.getvalue()
    page_path = root / contract["report_page_path"]
    page_path.write_bytes(page_bytes)
    page_text = page.extract_text() or ""
    page_text_path = root / contract["report_page_text_path"]
    page_text_path.write_text(page_text + "\n", encoding="utf-8", newline="\n")
    normalized = " ".join(page_text.lower().split())
    for phrase in (
        "figure 4.1: as-executed timeline",
        "crew choice",
        "discussion #4: terminator",
        "times are in utc and span flight day 06",
    ):
        if phrase not in normalized:
            raise ValueError(f"Focused report page lacks phrase: {phrase}")

    sources = [
        local_record(root, api_path, "official NTRS citation and download identity", url=contract["ntrs_api_url"], headers=api_headers),
        local_record(root, page_path, "focused exact PDF page containing NASA's as-executed timeline", parent_sha256=contract["parent_report_sha256"], parent_url=contract["ntrs_download_url"]),
        local_record(root, page_text_path, "text extraction from focused as-executed timeline page", extractor="pypdf"),
        local_record(root, root / contract["stage10c_result_path"], "verified repeated position-specific metadata signature"),
        local_record(root, root / contract["user_guide_text_path"], "official activity and target metadata-generation rules"),
        local_record(root, root / contract["outgoing_target_request_path"], "archived outgoing target request timing"),
        local_record(root, root / contract["transcript_path"], "contemporaneous crew transcript"),
    ]
    receipt = {
        "receipt_id": "artemis2-stage10f-mechanism-evidence-v1",
        "completed_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": "COMPLETED",
        "pixel_payload_bytes": 0,
        "external_parent_sources": [
            {
                "url": contract["ntrs_download_url"],
                "bytes": contract["parent_report_bytes"],
                "sha256": contract["parent_report_sha256"],
                "headers": head_headers,
                "role": "official full parent report; exact focused page preserved locally",
            }
        ],
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
