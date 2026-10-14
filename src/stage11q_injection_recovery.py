#!/usr/bin/env python3
"""Measure digital-domain recovery of frozen synthetic pulses in the overlap clip."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def robust_screen(values: np.ndarray, z_threshold: float, relative_threshold: float, scale: float) -> tuple[np.ndarray, float, float]:
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    robust_z = np.zeros_like(values) if mad == 0 else scale * (values - median) / mad
    relative = np.zeros_like(values) if median == 0 else (values - median) / median
    return (robust_z >= z_threshold) & (relative >= relative_threshold), median, mad


def gaussian_kernel(sigma: float, radius: int, requested_dn: int) -> np.ndarray:
    coordinates = np.arange(-radius, radius + 1, dtype=np.float64)
    xx, yy = np.meshgrid(coordinates, coordinates)
    weights = np.exp(-(xx * xx + yy * yy) / (2.0 * sigma * sigma))
    weights /= weights.sum()
    return np.rint(weights * requested_dn).astype(np.int32)


def first_amplitude(curve: list[dict[str, Any]], threshold: float) -> int | None:
    for row in curve:
        if row["recovery_fraction"] >= threshold:
            return int(row["requested_integrated_dn_per_frame"])
    return None


def run(root: Path, ffmpeg: str) -> dict[str, Any]:
    spec = json.loads((root / "spec/stage11q.json").read_text(encoding="utf-8"))
    identities = []
    for expected in spec["sources"]:
        path = root / expected["path"]
        observed = {"path": expected["path"], "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        observed["match"] = observed["bytes"] == expected["bytes"] and observed["sha256"] == expected["sha256"]
        identities.append(observed)

    clip_path = root / spec["sources"][0]["path"]
    width = int(spec["video"]["width"])
    height = int(spec["video"]["height"])
    frame_count = int(spec["video"]["frames"])
    x0, y0, x1, y1 = (int(value) for value in spec["video"]["roi_xyxy"])
    process = subprocess.Popen(
        [
            ffmpeg,
            "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(clip_path),
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
    frame_bytes = width * height
    roi_frames: list[np.ndarray] = []
    while True:
        payload = process.stdout.read(frame_bytes)
        if not payload:
            break
        if len(payload) != frame_bytes:
            raise RuntimeError("FFmpeg returned a partial grayscale frame")
        frame = np.frombuffer(payload, dtype=np.uint8).reshape((height, width))
        roi_frames.append(frame[y0:y1, x0:x1].copy())
    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    if process.wait() != 0:
        raise RuntimeError(f"FFmpeg raw decode failed: {stderr}")
    if len(roi_frames) != frame_count:
        raise RuntimeError(f"Expected {frame_count} frames, decoded {len(roi_frames)}")

    roi_stack = np.stack(roi_frames)
    baseline_sums = roi_stack.sum(axis=(1, 2), dtype=np.uint64).astype(np.float64)
    screen_spec = spec["screen"]
    z_threshold = float(screen_spec["robust_z_threshold"])
    relative_threshold = float(screen_spec["relative_increase_threshold"])
    scale = float(screen_spec["robust_scale_constant"])
    baseline_mask, baseline_median, baseline_mad = robust_screen(
        baseline_sums, z_threshold, relative_threshold, scale
    )
    robust_delta = z_threshold * baseline_mad / scale if scale else math.inf
    relative_delta = relative_threshold * baseline_median

    injection = spec["injection"]
    radius = int(injection["kernel_radius_pixels"])
    sigma = float(injection["sigma_pixels"])
    trials: list[dict[str, Any]] = []
    aggregate: dict[tuple[int, int], list[bool]] = defaultdict(list)
    realized_by_amplitude: dict[int, list[int]] = defaultdict(list)

    for amplitude in injection["requested_integrated_dn_per_frame"]:
        kernel = gaussian_kernel(sigma, radius, int(amplitude))
        for location_x, location_y in injection["locations_xy"]:
            center_x = int(location_x) - x0
            center_y = int(location_y) - y0
            left = center_x - radius
            top = center_y - radius
            right = center_x + radius + 1
            bottom = center_y + radius + 1
            if left < 0 or top < 0 or right > x1 - x0 or bottom > y1 - y0:
                raise RuntimeError("Frozen injection kernel extends outside ROI")
            for start_frame in injection["start_frames"]:
                for duration in injection["durations_frames"]:
                    injected_indices = list(range(int(start_frame), int(start_frame) + int(duration)))
                    if injected_indices[-1] >= frame_count:
                        raise RuntimeError("Frozen injection extends outside video")
                    trial_sums = baseline_sums.copy()
                    realized_values = []
                    for frame_index in injected_indices:
                        original = roi_stack[frame_index, top:bottom, left:right].astype(np.int32)
                        modified = np.clip(original + kernel, 0, 255)
                        realized = int((modified - original).sum(dtype=np.int64))
                        realized_values.append(realized)
                        trial_sums[frame_index] += realized
                    candidate_mask, _, _ = robust_screen(
                        trial_sums, z_threshold, relative_threshold, scale
                    )
                    recovered = bool(candidate_mask[injected_indices].any())
                    record = {
                        "requested_integrated_dn_per_frame": int(amplitude),
                        "location_xy": [int(location_x), int(location_y)],
                        "start_frame": int(start_frame),
                        "duration_frames": int(duration),
                        "realized_added_dn_per_frame": realized_values,
                        "recovered": recovered,
                    }
                    trials.append(record)
                    aggregate[(int(amplitude), int(duration))].append(recovered)
                    realized_by_amplitude[int(amplitude)].extend(realized_values)

    curve = []
    duration_curves: dict[str, list[dict[str, Any]]] = {
        str(int(duration)): [] for duration in injection["durations_frames"]
    }
    for amplitude in injection["requested_integrated_dn_per_frame"]:
        amplitude = int(amplitude)
        outcomes = [trial["recovered"] for trial in trials if trial["requested_integrated_dn_per_frame"] == amplitude]
        realized = realized_by_amplitude[amplitude]
        row = {
            "requested_integrated_dn_per_frame": amplitude,
            "trials": len(outcomes),
            "recovered": int(sum(outcomes)),
            "recovery_fraction": sum(outcomes) / len(outcomes),
            "realized_added_dn_per_frame_min": min(realized),
            "realized_added_dn_per_frame_median": float(np.median(realized)),
            "realized_added_dn_per_frame_max": max(realized),
        }
        curve.append(row)
        for duration in injection["durations_frames"]:
            subset = aggregate[(amplitude, int(duration))]
            duration_curves[str(int(duration))].append({
                "requested_integrated_dn_per_frame": amplitude,
                "trials": len(subset),
                "recovered": int(sum(subset)),
                "recovery_fraction": sum(subset) / len(subset),
            })

    fractions = [float(row["recovery_fraction"]) for row in curve]
    expected_trials = (
        len(injection["requested_integrated_dn_per_frame"])
        * len(injection["locations_xy"])
        * len(injection["start_frames"])
        * len(injection["durations_frames"])
    )
    checks = {
        "source_identities": all(identity["match"] for identity in identities),
        "all_frames_decoded": len(roi_frames) == frame_count,
        "baseline_candidate_free": int(baseline_mask.sum()) == 0,
        "all_trials_executed": len(trials) == expected_trials == 1458,
        "recovery_curve_nondecreasing": all(a <= b for a, b in zip(fractions, fractions[1:])),
        "claim_boundaries_preserved": not any(spec["claim_boundaries"].values()),
    }
    passed = all(checks.values())
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "pass": passed,
        "evidence_state": "VERIFIED_TRANSCODED_INJECTION_RECOVERY" if passed else "FAILED_TRANSCODED_INJECTION_RECOVERY",
        "checks": checks,
        "source_identities": identities,
        "baseline": {
            "frames": len(roi_frames),
            "roi_xyxy": [x0, y0, x1, y1],
            "roi_sum_median": baseline_median,
            "roi_sum_mad": baseline_mad,
            "candidate_frames": int(baseline_mask.sum()),
            "analytic_added_dn_for_robust_z_at_median": robust_delta,
            "analytic_added_dn_for_relative_threshold_at_median": relative_delta,
            "controlling_threshold_at_median": "robust_z" if robust_delta >= relative_delta else "relative_increase",
        },
        "injection_model": {
            "description": injection["model"],
            "sigma_pixels": sigma,
            "kernel_radius_pixels": radius,
            "locations_xy": injection["locations_xy"],
            "start_frames": injection["start_frames"],
            "durations_frames": injection["durations_frames"],
            "trial_count": len(trials),
        },
        "recovery_curve": curve,
        "duration_curves": duration_curves,
        "threshold_summary": {
            "first_amplitude_with_any_recovery": first_amplitude(curve, 1.0 / 162.0),
            "first_amplitude_at_or_above_50_percent": first_amplitude(curve, 0.5),
            "first_amplitude_at_or_above_90_percent": first_amplitude(curve, 0.9),
            "maximum_tested_amplitude": int(injection["requested_integrated_dn_per_frame"][-1]),
            "maximum_tested_recovery_fraction": fractions[-1],
        },
        "interpretation": "Digital-domain sensitivity of the frozen Stage 11P screen on the transcoded clip. It is not a physical brightness limit, source-pixel test, flight-sensor characterization, or event exclusion.",
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
    if not ffmpeg:
        parser.error("ffmpeg must resolve")
    root = args.root.resolve()
    result = run(root, ffmpeg)
    if args.write:
        path = root / "results/stage11q-injection-recovery.json"
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
