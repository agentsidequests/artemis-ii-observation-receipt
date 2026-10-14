#!/usr/bin/env python3
"""Run the bounded Stage 11O overlapping-video transport canary."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from stage5a_transport_canary import (
    Acquisition,
    CanaryStop,
    artifact_passes,
    run_ffmpeg,
    run_ffprobe,
    sha256_file,
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def run(root: Path, ffmpeg_path: str, ffprobe_path: str) -> dict[str, Any]:
    spec_path = root / "spec" / "stage11o.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    acquisition = Acquisition(spec)
    evidence_dir = root / "evidence" / "stage11o"
    derived_dir = evidence_dir / "derived"
    work_dir = root / "work" / "stage11o"
    derived_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    final_clip = derived_dir / "art002m1010962338_saw3_005110_005125_stage11o.mp4"
    temp_clip = work_dir / "stage11o-partial.mp4"
    if final_clip.exists() or temp_clip.exists():
        raise RuntimeError("Refusing to overwrite an existing Stage 11O clip or partial")

    receipt: dict[str, Any] = {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_started_utc": utc_now(),
        "spec_path": "spec/stage11o.json",
        "spec_sha256": sha256_file(spec_path),
        "source_url": spec["source"]["url"],
        "source_expected_bytes": spec["source"]["expected_bytes"],
        "budget_limit_bytes": spec["budget"]["aggregate_media_body_bytes"],
        "subset": spec["subset"],
        "runtime": {
            "python": sys.version,
            "python_executable": sys.executable,
            "ffmpeg": ffmpeg_path,
            "ffprobe": ffprobe_path,
        },
        "state": "TRANSPORT_ERROR",
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
    }
    try:
        receipt["head"] = acquisition.head()
        receipt["top_level_atoms"] = acquisition.map_top_level_atoms()
        receipt["ffmpeg"] = run_ffmpeg(acquisition, spec, ffmpeg_path, temp_clip)
        if acquisition.budget.accepted >= acquisition.budget.limit:
            raise CanaryStop("BUDGET_EXHAUSTED", "Aggregate media-byte budget was exhausted")
        failures = [
            item.get("classification")
            for item in acquisition.requests
            if item.get("purpose") == "ffmpeg_proxy"
            and item.get("classification") not in (None, "CLIENT_CLOSED_RANGE")
        ]
        for state in (
            "SERVER_IGNORED_RANGE",
            "SOURCE_IDENTITY_MISMATCH",
            "BUDGET_EXHAUSTED",
            "TRANSPORT_ERROR",
        ):
            if state in failures:
                raise CanaryStop(state, f"Proxy observed {state}")
        if receipt["ffmpeg"]["exit_code"] != 0 or not temp_clip.is_file():
            raise CanaryStop("EXTRACTION_FAILED_WITHIN_BUDGET", "FFmpeg did not produce a clip")
        receipt["ffprobe"] = run_ffprobe(ffprobe_path, temp_clip)
        artifact_ok, artifact_errors = artifact_passes(spec, receipt["ffprobe"])
        receipt["artifact_errors"] = artifact_errors
        if not artifact_ok:
            raise CanaryStop("ARTIFACT_REJECTED", "FFprobe artifact oracle failed")
        temp_clip.replace(final_clip)
        receipt["clip"] = {
            "path": final_clip.relative_to(root).as_posix(),
            "bytes": final_clip.stat().st_size,
            "sha256": sha256_file(final_clip),
        }
        receipt["state"] = "VERIFIED_BOUNDED_EXTRACTION"
    except CanaryStop as exc:
        receipt["state"] = exc.state
        receipt["stop_reason"] = str(exc)
        if temp_clip.exists():
            receipt["partial_clip"] = {
                "path": temp_clip.relative_to(root).as_posix(),
                "bytes": temp_clip.stat().st_size,
                "sha256": sha256_file(temp_clip),
            }
    finally:
        receipt["requests"] = acquisition.requests
        receipt["accepted_media_body_bytes"] = acquisition.budget.accepted
        receipt["budget_remaining_bytes"] = acquisition.budget.remaining
        receipt["run_finished_utc"] = utc_now()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    parser.add_argument("--ffprobe", default=shutil.which("ffprobe"))
    args = parser.parse_args()
    if not args.ffmpeg or not args.ffprobe:
        parser.error("ffmpeg and ffprobe must resolve before the canary starts")
    root = args.root.resolve()
    receipt_path = root / "evidence" / "stage11o" / "acquisition-receipt.json"
    if receipt_path.exists():
        parser.error(f"refusing to overwrite receipt: {receipt_path}")
    payload = run(root, args.ffmpeg, args.ffprobe)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "state": payload["state"],
        "accepted_media_body_bytes": payload["accepted_media_body_bytes"],
        "budget_remaining_bytes": payload["budget_remaining_bytes"],
        "clip": payload.get("clip"),
        "stop_reason": payload.get("stop_reason"),
    }, indent=2))
    return 0 if payload["state"] == "VERIFIED_BOUNDED_EXTRACTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
