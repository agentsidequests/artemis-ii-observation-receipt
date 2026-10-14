#!/usr/bin/env python3
"""Run the bounded Stage 5A SAW3 transport canary.

This acquisition helper is the only networked part of Stage 5A. Scored
verification is performed later, offline, from the preserved receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


RANGE_RE = re.compile(r"^bytes=(\d+)-(\d*)$")
CONTENT_RANGE_RE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_range_header(value: str, source_bytes: int) -> tuple[int, int | None]:
    match = RANGE_RE.fullmatch(value.strip())
    if not match:
        raise ValueError("Only one explicit or open-ended byte range is allowed")
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else None
    if start >= source_bytes or (end is not None and end < start):
        raise ValueError("Range is outside the admitted source")
    if end is not None:
        end = min(end, source_bytes - 1)
    return start, end


def parse_content_range(value: str) -> tuple[int, int, int]:
    match = CONTENT_RANGE_RE.fullmatch(value.strip())
    if not match:
        raise ValueError("Invalid Content-Range")
    return tuple(int(match.group(index)) for index in range(1, 4))  # type: ignore[return-value]


def parse_atom_header(data: bytes, offset: int) -> dict[str, Any]:
    if len(data) < 8:
        raise ValueError("MP4 atom header is shorter than 8 bytes")
    size32 = int.from_bytes(data[:4], "big")
    atom_type = data[4:8].decode("ascii", errors="replace")
    header_bytes = 8
    if size32 == 1:
        if len(data) < 16:
            raise ValueError("Extended MP4 atom header is shorter than 16 bytes")
        size = int.from_bytes(data[8:16], "big")
        header_bytes = 16
    elif size32 == 0:
        size = 0
    else:
        size = size32
    if size != 0 and size < header_bytes:
        raise ValueError("MP4 atom size is smaller than its header")
    return {
        "type": atom_type,
        "offset": offset,
        "size": size,
        "header_bytes": header_bytes,
    }


def is_client_disconnect(exc: OSError) -> bool:
    """Classify the normal socket failures produced when FFmpeg stops a range read."""
    return isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError))


@dataclass
class Budget:
    limit: int
    accepted: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.accepted)

    def add(self, count: int) -> None:
        with self.lock:
            if self.accepted + count > self.limit:
                raise RuntimeError("BUDGET_EXHAUSTED")
            self.accepted += count


class CanaryStop(RuntimeError):
    def __init__(self, state: str, message: str):
        super().__init__(message)
        self.state = state


class Acquisition:
    def __init__(self, spec: dict[str, Any]):
        self.spec = spec
        self.source_url = spec["source"]["url"]
        self.source_bytes = spec["source"]["expected_bytes"]
        self.timeout = spec["budget"]["timeout_seconds"]
        self.budget = Budget(spec["budget"]["aggregate_media_body_bytes"])
        self.requests: list[dict[str, Any]] = []
        self.user_agent = f"Artemis-II-Observation-Testbed/{spec['version']}"

    def _validate_final_url(self, observed: str) -> None:
        allowed_urls = (self.source_url, self.spec["source"]["delivery_url"])
        actual = urllib.parse.urlsplit(observed)
        allowed = {
            (parsed.scheme, parsed.netloc, parsed.path)
            for parsed in (urllib.parse.urlsplit(value) for value in allowed_urls)
        }
        if (actual.scheme, actual.netloc, actual.path) not in allowed:
            raise CanaryStop("SOURCE_IDENTITY_MISMATCH", f"Unexpected final URL: {observed}")

    def head(self) -> dict[str, Any]:
        request = urllib.request.Request(
            self.source_url,
            method="HEAD",
            headers={"User-Agent": self.user_agent, "Accept-Encoding": "identity"},
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                self._validate_final_url(response.geturl())
                record = {
                    "method": "HEAD",
                    "status": response.status,
                    "final_url": response.geturl(),
                    "content_length": response.headers.get("Content-Length"),
                    "accept_ranges": response.headers.get("Accept-Ranges"),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "media_body_bytes": 0,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                }
        except (OSError, urllib.error.URLError) as exc:
            raise CanaryStop("TRANSPORT_ERROR", f"HEAD failed: {exc}") from exc
        self.requests.append(record)
        length = record["content_length"]
        if length is not None and int(length) != self.source_bytes:
            raise CanaryStop("SOURCE_IDENTITY_MISMATCH", "HEAD Content-Length differs from label")
        return record

    def get_range(self, start: int, end: int, purpose: str) -> bytes:
        if start < 0 or end < start or end >= self.source_bytes:
            raise CanaryStop("SOURCE_IDENTITY_MISMATCH", "Requested range is outside source")
        requested = end - start + 1
        if requested > self.budget.remaining:
            raise CanaryStop("BUDGET_EXHAUSTED", "Range would exceed aggregate budget")
        request = urllib.request.Request(
            self.source_url,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
        )
        started = time.monotonic()
        record: dict[str, Any] = {
            "method": "GET",
            "purpose": purpose,
            "requested_range": f"bytes={start}-{end}",
            "media_body_bytes": 0,
        }
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                self._validate_final_url(response.geturl())
                record.update(
                    {
                        "status": response.status,
                        "final_url": response.geturl(),
                        "content_range": response.headers.get("Content-Range"),
                        "content_length": response.headers.get("Content-Length"),
                    }
                )
                if response.status != 206:
                    raise CanaryStop("SERVER_IGNORED_RANGE", f"Range returned HTTP {response.status}")
                try:
                    observed_start, observed_end, observed_total = parse_content_range(
                        record["content_range"] or ""
                    )
                except ValueError as exc:
                    raise CanaryStop("SOURCE_IDENTITY_MISMATCH", str(exc)) from exc
                if (observed_start, observed_end, observed_total) != (
                    start,
                    end,
                    self.source_bytes,
                ):
                    raise CanaryStop("SOURCE_IDENTITY_MISMATCH", "Content-Range differs from request or label")
                chunks: list[bytes] = []
                remaining = requested
                while remaining:
                    chunk = response.read(min(65536, remaining))
                    if not chunk:
                        break
                    self.budget.add(len(chunk))
                    record["media_body_bytes"] += len(chunk)
                    chunks.append(chunk)
                    remaining -= len(chunk)
                body = b"".join(chunks)
                if len(body) != requested or response.read(1):
                    raise CanaryStop("SOURCE_IDENTITY_MISMATCH", "Range body length differs from Content-Range")
        except CanaryStop:
            raise
        except urllib.error.HTTPError as exc:
            record.update({"status": exc.code, "error": str(exc)})
            raise CanaryStop("TRANSPORT_ERROR", f"Range request failed: HTTP {exc.code}") from exc
        except (OSError, urllib.error.URLError) as exc:
            record["error"] = str(exc)
            raise CanaryStop("TRANSPORT_ERROR", f"Range request failed: {exc}") from exc
        finally:
            record["elapsed_seconds"] = round(time.monotonic() - started, 3)
            self.requests.append(record)
        return body

    def map_top_level_atoms(self) -> list[dict[str, Any]]:
        probe_bytes = self.spec["budget"]["initial_probe_bytes"]
        prefix = self.get_range(0, probe_bytes - 1, "initial_container_probe")
        atoms: list[dict[str, Any]] = []
        offset = 0
        for _ in range(self.spec["budget"]["maximum_top_level_atom_headers"]):
            if offset + 16 <= len(prefix):
                header = prefix[offset : offset + 16]
            else:
                header = self.get_range(
                    offset,
                    min(offset + 15, self.source_bytes - 1),
                    "top_level_atom_header",
                )
            atom = parse_atom_header(header, offset)
            if atom["size"] == 0:
                atom["size"] = self.source_bytes - offset
            if atom["size"] <= 0 or offset + atom["size"] > self.source_bytes:
                raise CanaryStop("SOURCE_IDENTITY_MISMATCH", "Top-level MP4 atom exceeds source")
            atoms.append(atom)
            offset += atom["size"]
            if offset == self.source_bytes:
                break
        if not any(atom["type"] == "moov" for atom in atoms):
            raise CanaryStop("SOURCE_IDENTITY_MISMATCH", "No top-level moov atom found")
        return atoms


def make_proxy_handler(acquisition: Acquisition, max_response: int):
    class RangeProxy(http.server.BaseHTTPRequestHandler):
        server_version = "Stage5ARangeGate/0.5"

        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def do_HEAD(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Length", str(acquisition.source_bytes))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Type", "video/mp4")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            range_value = self.headers.get("Range")
            if not range_value:
                acquisition.requests.append(
                    {
                        "method": "LOCAL_PROXY_GET",
                        "purpose": "ffmpeg",
                        "requested_range": None,
                        "status": 403,
                        "media_body_bytes": 0,
                        "classification": "UNRESTRICTED_CLIENT_REQUEST",
                    }
                )
                self.send_error(403, "A byte Range header is required")
                return
            try:
                start, requested_end = parse_range_header(range_value, acquisition.source_bytes)
            except ValueError as exc:
                self.send_error(416, str(exc))
                return
            remaining = acquisition.budget.remaining
            if remaining <= 0:
                self.send_error(429, "Aggregate media-byte budget exhausted")
                return
            end = min(
                requested_end if requested_end is not None else acquisition.source_bytes - 1,
                start + max_response - 1,
                start + remaining - 1,
                acquisition.source_bytes - 1,
            )
            started = time.monotonic()
            record: dict[str, Any] = {
                "method": "GET",
                "purpose": "ffmpeg_proxy",
                "requested_range": f"bytes={start}-{end}",
                "media_body_bytes": 0,
            }
            request = urllib.request.Request(
                acquisition.source_url,
                headers={
                    "User-Agent": acquisition.user_agent,
                    "Accept-Encoding": "identity",
                    "Range": f"bytes={start}-{end}",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=acquisition.timeout) as response:
                    acquisition._validate_final_url(response.geturl())
                    record.update(
                        {
                            "status": response.status,
                            "final_url": response.geturl(),
                            "content_range": response.headers.get("Content-Range"),
                            "content_length": response.headers.get("Content-Length"),
                        }
                    )
                    if response.status != 206:
                        raise CanaryStop(
                            "SERVER_IGNORED_RANGE", f"Range returned HTTP {response.status}"
                        )
                    try:
                        observed = parse_content_range(record["content_range"] or "")
                    except ValueError as exc:
                        raise CanaryStop("SOURCE_IDENTITY_MISMATCH", str(exc)) from exc
                    if observed != (start, end, acquisition.source_bytes):
                        raise CanaryStop(
                            "SOURCE_IDENTITY_MISMATCH",
                            "Content-Range differs from request or label",
                        )

                    self.send_response(206)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header(
                        "Content-Range", f"bytes {start}-{end}/{acquisition.source_bytes}"
                    )
                    self.send_header("Content-Length", str(end - start + 1))
                    self.end_headers()
                    remaining_body = end - start + 1
                    while remaining_body:
                        chunk = response.read(min(65536, remaining_body))
                        if not chunk:
                            record["classification"] = "TRUNCATED_UPSTREAM_BODY"
                            break
                        acquisition.budget.add(len(chunk))
                        record["media_body_bytes"] += len(chunk)
                        remaining_body -= len(chunk)
                        try:
                            self.wfile.write(chunk)
                        except OSError as exc:
                            if is_client_disconnect(exc):
                                record["classification"] = "CLIENT_CLOSED_RANGE"
                                break
                            raise
            except CanaryStop as exc:
                record["classification"] = exc.state
                self.send_error(502, f"{exc.state}: {exc}")
                return
            except urllib.error.HTTPError as exc:
                record.update(
                    {
                        "status": exc.code,
                        "classification": "TRANSPORT_ERROR",
                        "error": str(exc),
                    }
                )
                self.send_error(502, f"Upstream HTTP {exc.code}")
                return
            except (OSError, urllib.error.URLError, RuntimeError) as exc:
                record.update(
                    {
                        "classification": (
                            "BUDGET_EXHAUSTED"
                            if str(exc) == "BUDGET_EXHAUSTED"
                            else "TRANSPORT_ERROR"
                        ),
                        "error": str(exc),
                    }
                )
                self.send_error(502, str(exc))
                return
            finally:
                record["elapsed_seconds"] = round(time.monotonic() - started, 3)
                acquisition.requests.append(record)

    return RangeProxy


def run_ffmpeg(
    acquisition: Acquisition,
    spec: dict[str, Any],
    ffmpeg_path: str,
    output_path: Path,
) -> dict[str, Any]:
    handler = make_proxy_handler(acquisition, spec["budget"]["maximum_proxy_response_bytes"])
    server = http.server.HTTPServer(("127.0.0.1", 0), handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    proxy_url = f"http://127.0.0.1:{server.server_port}/video.mp4"
    command = [
        ffmpeg_path,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "info",
        "-rw_timeout",
        "15000000",
        "-ss",
        str(spec["subset"]["source_offset_seconds"]),
        "-i",
        proxy_url,
        "-t",
        str(spec["subset"]["duration_seconds"]),
        "-map",
        "0:v:0",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-y",
        str(output_path),
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": None,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "timed_out": False,
    }


def run_ffprobe(ffprobe_path: str, clip_path: Path) -> dict[str, Any]:
    command = [
        ffprobe_path,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(clip_path),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    payload: dict[str, Any] = {
        "command": command,
        "exit_code": completed.returncode,
        "stderr": completed.stderr,
    }
    if completed.returncode == 0:
        payload["probe"] = json.loads(completed.stdout)
    else:
        payload["stdout"] = completed.stdout
    return payload


def artifact_passes(spec: dict[str, Any], probe: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    oracle = spec["success_oracle"]
    streams = probe.get("probe", {}).get("streams", [])
    videos = [item for item in streams if item.get("codec_type") == "video"]
    audios = [item for item in streams if item.get("codec_type") == "audio"]
    if len(videos) != 1:
        errors.append("Expected exactly one video stream")
    else:
        video = videos[0]
        if video.get("codec_name") != oracle["video_codec"]:
            errors.append("Unexpected video codec")
        if video.get("width") != oracle["width"] or video.get("height") != oracle["height"]:
            errors.append("Unexpected video dimensions")
    if len(audios) != oracle["audio_streams"]:
        errors.append("Unexpected audio stream count")
    try:
        duration = float(probe["probe"]["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        duration = -1
    if not oracle["minimum_duration_seconds"] <= duration <= oracle["maximum_duration_seconds"]:
        errors.append("Clip duration is outside the frozen tolerance")
    return not errors, errors


def run(root: Path, ffmpeg_path: str, ffprobe_path: str) -> dict[str, Any]:
    spec_path = root / "spec" / "stage5a.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    acquisition = Acquisition(spec)
    evidence_dir = root / "evidence" / "stage5a"
    derived_dir = evidence_dir / "derived"
    work_dir = root / "work" / "stage5a"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    final_clip = derived_dir / "art002m1010962338_saw3_005110_005125_stage5a.mp4"
    temp_clip = work_dir / "stage5a-partial.mp4"
    if final_clip.exists() or temp_clip.exists():
        raise RuntimeError("Refusing to overwrite an existing Stage 5A clip or partial")

    receipt: dict[str, Any] = {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "run_started_utc": utc_now(),
        "spec_path": "spec/stage5a.json",
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
        "requests": acquisition.requests,
    }
    try:
        receipt["head"] = acquisition.head()
        receipt["top_level_atoms"] = acquisition.map_top_level_atoms()
        receipt["ffmpeg"] = run_ffmpeg(acquisition, spec, ffmpeg_path, temp_clip)
        unrestricted = any(
            item.get("classification") == "UNRESTRICTED_CLIENT_REQUEST"
            for item in acquisition.requests
        )
        if unrestricted:
            raise CanaryStop("UNRESTRICTED_CLIENT_REQUEST", "FFmpeg attempted a request without Range")
        if acquisition.budget.accepted >= acquisition.budget.limit:
            raise CanaryStop("BUDGET_EXHAUSTED", "Aggregate media-byte budget was exhausted")
        proxy_failures = [
            item.get("classification")
            for item in acquisition.requests
            if item.get("purpose") == "ffmpeg_proxy"
            and item.get("classification")
            not in (None, "CLIENT_CLOSED_RANGE")
        ]
        for state in (
            "SERVER_IGNORED_RANGE",
            "SOURCE_IDENTITY_MISMATCH",
            "BUDGET_EXHAUSTED",
            "TRANSPORT_ERROR",
        ):
            if state in proxy_failures:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    parser.add_argument("--ffprobe", default=shutil.which("ffprobe"))
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("evidence/stage5a/acquisition-receipt.json"),
    )
    args = parser.parse_args(argv)
    if not args.ffmpeg or not args.ffprobe:
        parser.error("ffmpeg and ffprobe must resolve before the canary starts")
    root = args.root.resolve()
    receipt_path = args.receipt if args.receipt.is_absolute() else root / args.receipt
    if receipt_path.exists():
        parser.error(f"refusing to overwrite receipt: {receipt_path}")
    payload = run(root, args.ffmpeg, args.ffprobe)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["state"] == "VERIFIED_BOUNDED_EXTRACTION" else 2


if __name__ == "__main__":
    sys.exit(main())
