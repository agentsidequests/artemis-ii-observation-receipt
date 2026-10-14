#!/usr/bin/env python3
"""Screen the bounded overlapping SAW3 clip without making a photometric claim."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, check=True)
    return json.loads(completed.stdout)


def screen(root: Path, ffmpeg: str, ffprobe: str) -> dict[str, Any]:
    spec = json.loads((root / "spec/stage11p.json").read_text(encoding="utf-8"))
    source = root / spec["source"]["path"]
    source_identity = {
        "path": spec["source"]["path"],
        "bytes": source.stat().st_size,
        "sha256": sha256_file(source),
    }
    identity_match = (
        source_identity["bytes"] == spec["source"]["bytes"]
        and source_identity["sha256"] == spec["source"]["sha256"]
    )

    probe = run_json([
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
        "-of", "json",
        str(source),
    ])
    video = probe["streams"][0]
    width = int(video["width"])
    height = int(video["height"])
    frame_count = int(video["nb_frames"])
    numerator, denominator = (int(part) for part in video["r_frame_rate"].split("/"))
    fps = numerator / denominator
    expected = spec["video_oracle"]
    video_match = (
        width == expected["width"]
        and height == expected["height"]
        and frame_count == expected["frames"]
        and numerator == expected["frame_rate_numerator"]
        and denominator == expected["frame_rate_denominator"]
        and abs(float(video["duration"]) - expected["duration_seconds"]) < 0.001
    )

    process = subprocess.Popen(
        [
            ffmpeg,
            "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(source),
            "-map", "0:v:0",
            "-f", "rawvideo",
            "-pix_fmt", "gray",
            "pipe:1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdout is None:
        raise RuntimeError("FFmpeg stdout pipe was not created")
    roi_spec = spec["screen"]["roi"]
    x0, y0, x1, y1 = (roi_spec[key] for key in ("x0", "y0", "x1", "y1"))
    threshold = int(spec["screen"]["bright_pixel_threshold_gray"])
    frame_bytes = width * height
    roi_sums: list[int] = []
    roi_maxima: list[int] = []
    bright_counts: list[int] = []
    bboxes: list[list[int] | None] = []
    while True:
        payload = process.stdout.read(frame_bytes)
        if not payload:
            break
        if len(payload) != frame_bytes:
            raise RuntimeError("FFmpeg returned a partial grayscale frame")
        frame = np.frombuffer(payload, dtype=np.uint8).reshape((height, width))
        roi = frame[y0:y1, x0:x1]
        roi_sums.append(int(roi.sum(dtype=np.uint64)))
        roi_maxima.append(int(roi.max()))
        mask = roi > threshold
        bright_counts.append(int(mask.sum()))
        ys, xs = np.where(mask)
        bboxes.append(
            [int(xs.min() + x0), int(ys.min() + y0), int(xs.max() + x0), int(ys.max() + y0)]
            if xs.size
            else None
        )
    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError(f"FFmpeg raw decode failed: {stderr}")

    values = np.asarray(roi_sums, dtype=np.float64)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    robust_z = np.zeros_like(values) if mad == 0 else 0.67448975 * (values - median) / mad
    relative = np.zeros_like(values) if median == 0 else (values - median) / median
    report_offset_seconds = 5.947
    event_start = max(0, int((report_offset_seconds - spec["screen"]["event_window_before_seconds"]) * fps))
    event_stop = min(len(values), int((report_offset_seconds + spec["screen"]["event_window_after_seconds"]) * fps) + 1)
    candidate_mask = (
        (robust_z >= spec["screen"]["robust_z_screen_threshold"])
        & (relative >= spec["screen"]["relative_increase_screen_threshold"])
    )
    candidate_indices = np.where(candidate_mask)[0]
    event_candidate_indices = candidate_indices[(candidate_indices >= event_start) & (candidate_indices < event_stop)]

    report_frame = min(len(values) - 1, round(report_offset_seconds * fps))
    report_bbox = bboxes[report_frame]
    apparent_width = 0 if report_bbox is None else report_bbox[2] - report_bbox[0] + 1
    apparent_height = 0 if report_bbox is None else report_bbox[3] - report_bbox[1] + 1
    apparent_diameter = max(apparent_width, apparent_height)
    km_per_apparent_pixel = (
        spec["screen"]["moon_diameter_km"] / apparent_diameter if apparent_diameter else None
    )
    checks = {
        "source_identity": identity_match,
        "video_geometry": video_match,
        "all_frames_decoded": len(values) == frame_count,
        "claim_boundaries_preserved": not any(spec["claim_boundaries"].values()),
    }
    passed = all(checks.values())
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "pass": passed,
        "evidence_state": "VERIFIED_CONTEXTUAL_PIXEL_SCREEN" if passed else "FAILED_CONTEXTUAL_PIXEL_SCREEN",
        "checks": checks,
        "source_identity": source_identity,
        "video": {
            "width": width,
            "height": height,
            "frames_decoded": len(values),
            "fps": fps,
            "duration_seconds": float(video["duration"]),
            "transcode_note": spec["source"]["transcode_note"],
        },
        "lunar_footprint": {
            "report_frame_index": report_frame,
            "threshold_gray": threshold,
            "bbox_xyxy": report_bbox,
            "apparent_width_pixels": apparent_width,
            "apparent_height_pixels": apparent_height,
            "apparent_diameter_pixels": apparent_diameter,
            "illustrative_km_per_apparent_pixel": km_per_apparent_pixel,
            "interpretation": "Threshold-defined image footprint only, not an optical-resolution or geolocation measurement.",
        },
        "pulse_screen": {
            "roi_xyxy": [x0, y0, x1, y1],
            "roi_sum_median": median,
            "roi_sum_mad": mad,
            "maximum_robust_z": float(robust_z.max()),
            "maximum_relative_increase": float(relative.max()),
            "candidate_frame_count": int(candidate_indices.size),
            "candidate_frames": candidate_indices.astype(int).tolist(),
            "event_window_frames": [event_start, event_stop - 1],
            "event_window_candidate_frame_count": int(event_candidate_indices.size),
            "event_window_candidate_frames": event_candidate_indices.astype(int).tolist(),
            "report_frame_roi_sum": roi_sums[report_frame],
            "report_frame_roi_max": roi_maxima[report_frame],
            "report_frame_bright_pixels": bright_counts[report_frame],
            "roi_sum_series": roi_sums,
            "robust_z_series": [round(float(value), 6) for value in robust_z],
            "interpretation": "A thresholded screen of a transcoded contextual clip. No screened pulse does not exclude the crew event.",
        },
        "claim_boundaries": spec["claim_boundaries"],
        "claim_ceiling": spec["authority"],
        "next_step_logic": spec["next_step_logic"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        parser.error("ffmpeg and ffprobe must resolve")
    root = args.root.resolve()
    result = screen(root, ffmpeg, ffprobe)
    if args.write:
        output = root / "results/stage11p-overlap-pixel-screen.json"
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
