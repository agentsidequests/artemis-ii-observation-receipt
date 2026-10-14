#!/usr/bin/env python3
"""Verify the Stage 5A bounded-transport canary offline."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


RANGE_RE = re.compile(r"^bytes=(\d+)-(\d+)$")
CONTENT_RANGE_RE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_range(value: str) -> tuple[int, int]:
    match = RANGE_RE.fullmatch(value)
    if not match:
        raise ValueError("Invalid or unrestricted request range")
    return int(match.group(1)), int(match.group(2))


def parse_content_range(value: str) -> tuple[int, int, int]:
    match = CONTENT_RANGE_RE.fullmatch(value)
    if not match:
        raise ValueError("Invalid Content-Range")
    return tuple(int(match.group(index)) for index in range(1, 4))  # type: ignore[return-value]


def apply_mutation(receipt: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(receipt)
    if mutation is None:
        return mutated
    if mutation == "budget_not_exhausted":
        mutated["accepted_media_body_bytes"] -= 1
        mutated["budget_remaining_bytes"] = 1
    elif mutation == "source_total_changed":
        for request in mutated["requests"]:
            if request.get("content_range"):
                request["content_range"] = request["content_range"].rsplit("/", 1)[0] + "/1"
                break
    elif mutation == "clip_claim_without_artifact":
        mutated["state"] = "VERIFIED_BOUNDED_EXTRACTION"
        mutated["clip"] = {
            "path": "evidence/stage5a/derived/nonexistent.mp4",
            "bytes": 1,
            "sha256": "0" * 64,
        }
    elif mutation == "unrestricted_request_admitted":
        for request in mutated["requests"]:
            if request.get("method") == "GET":
                request["requested_range"] = None
                break
    elif mutation == "moov_geometry_changed":
        mutated["top_level_atoms"][-1]["size"] += 1
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_stage5a(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = load_json(root / "spec" / "stage5a.json")
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    verification = spec["verification"]

    manifest_path = root / verification["manifest_path"]
    manifest_ok = (
        manifest_path.is_file()
        and manifest_path.stat().st_size == verification["manifest_bytes"]
        and sha256_file(manifest_path) == verification["manifest_sha256"]
    )
    checks.append({"id": "source_manifest_identity", "pass": manifest_ok})
    if not manifest_ok:
        errors.append("Stage 5A source-manifest identity mismatch")

    manifest = load_json(manifest_path)
    file_receipts: list[dict[str, Any]] = []
    for source in manifest["files"]:
        path = root / source["path"]
        exists = path.is_file()
        observed_bytes = path.stat().st_size if exists else None
        observed_hash = sha256_file(path) if exists else None
        passed = (
            exists
            and observed_bytes == source["bytes"]
            and observed_hash == source["sha256"]
        )
        file_receipts.append(
            {
                "path": source["path"],
                "pass": passed,
                "bytes": observed_bytes,
                "sha256": observed_hash,
            }
        )
        if not passed:
            errors.append(f"Evidence identity mismatch: {source['path']}")
    checks.append(
        {
            "id": "source_file_identities",
            "pass": all(item["pass"] for item in file_receipts),
            "files": file_receipts,
        }
    )

    frozen_spec = load_json(root / verification["frozen_run_spec_path"])
    terminal_path = root / verification["terminal_receipt_path"]
    raw_receipt = load_json(terminal_path)
    receipt = apply_mutation(raw_receipt, mutation)
    frozen_identity_ok = (
        raw_receipt["spec_sha256"]
        == sha256_file(root / verification["frozen_run_spec_path"])
        and raw_receipt["version"] == frozen_spec["version"]
        and raw_receipt["source_url"] == frozen_spec["source"]["url"]
        and raw_receipt["subset"] == frozen_spec["subset"]
    )
    checks.append({"id": "frozen_run_contract", "pass": frozen_identity_ok})
    if not frozen_identity_ok:
        errors.append("Terminal receipt is not bound to the frozen run contract")

    attempt1 = load_json(root / "evidence" / "stage5a" / "attempt-1-source-redirect-receipt.json")
    attempt1_ok = (
        attempt1["state"] == "SOURCE_IDENTITY_MISMATCH"
        and attempt1["accepted_media_body_bytes"] == 0
        and attempt1["budget_remaining_bytes"] == attempt1["budget_limit_bytes"]
        and frozen_spec["source"]["delivery_url"] in attempt1["stop_reason"]
    )
    checks.append(
        {
            "id": "zero_media_redirect_stop",
            "pass": attempt1_ok,
            "accepted_media_body_bytes": attempt1["accepted_media_body_bytes"],
        }
    )
    if not attempt1_ok:
        errors.append("Attempt 1 did not preserve the zero-media redirect stop")

    source_bytes = frozen_spec["source"]["expected_bytes"]
    allowed_final_urls = {
        frozen_spec["source"]["url"],
        frozen_spec["source"]["delivery_url"],
    }
    head = receipt.get("head", {})
    head_ok = (
        head.get("status") == 200
        and int(head.get("content_length", -1)) == source_bytes
        and head.get("accept_ranges") == "bytes"
        and head.get("final_url") in allowed_final_urls
        and head.get("media_body_bytes") == 0
    )
    checks.append(
        {
            "id": "source_head_identity",
            "pass": head_ok,
            "content_length": head.get("content_length"),
            "accept_ranges": head.get("accept_ranges"),
            "final_url": head.get("final_url"),
        }
    )
    if not head_ok:
        errors.append("HEAD receipt does not bind the admitted source and delivery route")

    range_errors: list[str] = []
    get_requests = [item for item in receipt.get("requests", []) if item.get("method") == "GET"]
    media_sum = 0
    for index, request in enumerate(get_requests):
        try:
            start, end = parse_range(request.get("requested_range"))
            content_start, content_end, content_total = parse_content_range(
                request.get("content_range", "")
            )
            body_bytes = int(request.get("media_body_bytes", -1))
            if request.get("status") != 206:
                range_errors.append(f"request {index} was not HTTP 206")
            if request.get("final_url") not in allowed_final_urls:
                range_errors.append(f"request {index} used an unapproved delivery URL")
            if (content_start, content_end) != (start, end) or content_total != source_bytes:
                range_errors.append(f"request {index} Content-Range mismatch")
            if not 0 <= body_bytes <= end - start + 1:
                range_errors.append(f"request {index} body count exceeds its range")
            media_sum += body_bytes
        except (TypeError, ValueError):
            range_errors.append(f"request {index} has an invalid or unrestricted range")
    ranges_ok = bool(get_requests) and not range_errors
    checks.append(
        {
            "id": "bounded_range_transport",
            "pass": ranges_ok,
            "http_206_requests": len(get_requests),
            "media_body_bytes": media_sum,
            "errors": range_errors,
        }
    )
    if not ranges_ok:
        errors.extend(range_errors or ["No HTTP 206 range requests were preserved"])

    observed_atoms = [
        [item["type"], item["offset"], item["size"]]
        for item in receipt.get("top_level_atoms", [])
    ]
    expected_atoms = verification["expected_top_level_atoms"]
    atoms_contiguous = all(
        observed_atoms[index][1] + observed_atoms[index][2] == observed_atoms[index + 1][1]
        for index in range(len(observed_atoms) - 1)
    )
    atoms_ok = (
        observed_atoms == expected_atoms
        and atoms_contiguous
        and observed_atoms[-1][1] + observed_atoms[-1][2] == source_bytes
    )
    checks.append(
        {
            "id": "mp4_top_level_geometry",
            "pass": atoms_ok,
            "atoms": observed_atoms,
        }
    )
    if not atoms_ok:
        errors.append("MP4 top-level atom geometry differs from the frozen receipt")

    budget_limit = frozen_spec["budget"]["aggregate_media_body_bytes"]
    budget_ok = (
        receipt.get("state") == verification["expected_receipt_state"]
        and receipt.get("accepted_media_body_bytes")
        == verification["expected_accepted_media_body_bytes"]
        == budget_limit
        and receipt.get("budget_remaining_bytes") == 0
        and media_sum == budget_limit
    )
    checks.append(
        {
            "id": "hard_budget_stop",
            "pass": budget_ok,
            "state": receipt.get("state"),
            "accepted_media_body_bytes": receipt.get("accepted_media_body_bytes"),
            "budget_limit_bytes": budget_limit,
        }
    )
    if not budget_ok:
        errors.append("Terminal receipt does not prove the exact 64 MiB budget stop")

    clip = receipt.get("clip")
    clip_path = root / clip["path"] if isinstance(clip, dict) and clip.get("path") else None
    clip_count = 1 if clip_path and clip_path.is_file() else 0
    extraction_stop_ok = (
        clip_count == verification["expected_clip_count"]
        and receipt.get("ffmpeg", {}).get("exit_code") not in (None, 0)
        and "moov atom not found" in receipt.get("ffmpeg", {}).get("stderr", "")
    )
    checks.append(
        {
            "id": "no_clip_claim_laundering",
            "pass": extraction_stop_ok,
            "clip_count": clip_count,
            "ffmpeg_exit_code": receipt.get("ffmpeg", {}).get("exit_code"),
        }
    )
    if not extraction_stop_ok:
        errors.append("Failed extraction was promoted or its artifact failure was not preserved")

    client_abort_noise = [
        item
        for item in receipt.get("requests", [])
        if item.get("classification") == "TRANSPORT_ERROR"
        and "WinError 10053" in item.get("error", "")
    ]
    checks.append(
        {
            "id": "raw_client_abort_misclassification_preserved",
            "pass": len(client_abort_noise) == 1,
            "count": len(client_abort_noise),
            "bounded_interpretation": (
                "The raw acquisition helper mislabeled one Windows client-close signal as a "
                "transport error. The terminal state was independently the exact byte-budget "
                "stop; the helper now classifies this socket condition as CLIENT_CLOSED_RANGE."
            ),
        }
    )
    if len(client_abort_noise) != 1:
        errors.append("Expected raw Windows client-close receipt was not preserved exactly")

    passed = not errors and all(item["pass"] for item in checks)
    evidence_state = verification["expected_evidence_state"] if passed else "REJECTED"
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mutation": mutation or "none",
        "pass": passed,
        "evidence_state": evidence_state,
        "receipt_state": receipt.get("state"),
        "range_transport_verified": ranges_ok and head_ok,
        "clip_materialized": clip_count == 1,
        "accepted_media_body_bytes": receipt.get("accepted_media_body_bytes"),
        "full_product_bytes": source_bytes,
        "fraction_of_full_product": round(budget_limit / source_bytes, 6),
        "top_level_atoms": receipt.get("top_level_atoms", []),
        "checks": checks,
        "errors": errors,
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"] if passed else None,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage5a(root)
    mutation_names = (
        "budget_not_exhausted",
        "source_total_changed",
        "clip_claim_without_artifact",
        "unrestricted_request_admitted",
        "moov_geometry_changed",
    )
    mutations = {name: verify_stage5a(root, name) for name in mutation_names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {
        "baseline": baseline,
        "hard_negatives": mutations,
        "hard_negatives_pass": hard_negatives_pass,
        "pass": baseline["pass"] and hard_negatives_pass,
        "evidence_state": baseline["evidence_state"] if hard_negatives_pass else "FAILED",
    }


def render_markdown(verification: dict[str, Any]) -> str:
    baseline = verification["baseline"]
    next_step = baseline.get("next_step_logic")
    atoms = {item["type"]: item for item in baseline["top_level_atoms"]}
    lines = [
        "# Artemis II Observation-Execution Testbed — Stage 5A Result",
        "",
        f"- Verification: **{'PASS' if verification['pass'] else 'FAIL'}**",
        f"- Evidence state: `{verification['evidence_state']}`",
        f"- Acquisition stop: `{baseline['receipt_state']}`",
        f"- Range transport: **{'verified' if baseline['range_transport_verified'] else 'not verified'}**",
        f"- 15-second clip: **{'materialized' if baseline['clip_materialized'] else 'not materialized'}**",
        f"- Accepted media-body bytes: **{baseline['accepted_media_body_bytes']:,} / {baseline['full_product_bytes']:,}**",
        "",
        "The official delivery path returned exact HTTP 206 byte ranges and a source length that "
        "matches the PDS label. The MP4 stores a 30,289,940-byte `moov` index at the file tail. "
        "The direct FFmpeg-through-range-gate treatment consumed the full 64 MiB ceiling while "
        "seeking and stopped without creating a clip.",
        "",
        "This is a verified budget stop, not a successful extraction and not proof that every "
        "bounded extraction strategy would fail. The terminal attempt accepted only "
        f"{baseline['fraction_of_full_product']:.3%} of the complete product.",
        "",
        "## Container geometry",
        "",
        f"- `mdat`: offset {atoms.get('mdat', {}).get('offset', 'unknown'):,}, size {atoms.get('mdat', {}).get('size', 0):,} bytes",
        f"- `moov`: offset {atoms.get('moov', {}).get('offset', 'unknown'):,}, size {atoms.get('moov', {}).get('size', 0):,} bytes",
        "",
        baseline["claim_ceiling"],
        "",
        "## Next-step logic",
        "",
        f"- Contract route after this stop: {next_step['on_transport_failure'] if next_step else 'Resolve verification errors.'}",
        f"- A later alternative, if separately authorized: {next_step['on_valid_transport_but_rejected_artifact'] if next_step else 'None.'}",
        f"- Stop boundary: {next_step['stop'] if next_step else 'Do not advance a rejected baseline.'}",
        "",
        "## Hard negatives",
        "",
    ]
    for name, result in verification["hard_negatives"].items():
        lines.append(f"- `{name}`: {'REJECTED' if not result['pass'] else 'UNEXPECTEDLY ACCEPTED'}")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument(
        "--mutation",
        choices=(
            "budget_not_exhausted",
            "source_total_changed",
            "clip_claim_without_artifact",
            "unrestricted_request_admitted",
            "moov_geometry_changed",
        ),
    )
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        payload = verify_with_mutations(args.root)
    else:
        payload = verify_stage5a(args.root, args.mutation)
    if args.json_output:
        write_json(args.json_output, payload)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_markdown(payload) if args.command == "verify" else json.dumps(payload, indent=2) + "\n"
        args.markdown_output.write_text(rendered, encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
