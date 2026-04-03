#!/usr/bin/env python3
"""Poll LMU/rF2 telemetry shared memory and POST frames to Delta Engineer API.

Intended to be spawned by the Electron main process. Requires:
  - Windows + LMU running with rF2 Shared Memory Map plugin enabled
  - Delta Engineer API running (``POST /telemetry``)
  - An existing session id (create via ``POST /sessions`` or the UI)

Repository root must be importable (script prepends it to ``sys.path``).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Repo root = parent of scripts/
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.capture.lmu_shared_memory import read_rf2_telemetry_buffer  # noqa: E402
from src.core.parser import (  # noqa: E402
    TelemetryParseError,
    parse_telemetry_frame,
    parse_telemetry_header,
)


def post_frames(
    api_base: str,
    session_id: int,
    frames: list[dict],
    timeout_s: float = 5.0,
) -> dict:
    url = api_base.rstrip("/") + "/telemetry/"
    body = json.dumps({"session_id": session_id, "frames": frames}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_loop(
    api_base: str,
    session_id: int,
    vehicle_index: int,
    poll_interval_s: float,
    verbose: bool,
) -> None:
    last_version: int | None = None

    while True:
        raw = read_rf2_telemetry_buffer()
        if raw is None:
            if verbose:
                print(
                    "LMU telemetry mapping not found (is LMU running with the plugin?)",
                    file=sys.stderr,
                    flush=True,
                )
            time.sleep(max(poll_interval_s, 0.5))
            continue

        if len(raw) < 16:
            time.sleep(poll_interval_s)
            continue

        try:
            header = parse_telemetry_header(raw)
        except TelemetryParseError:
            time.sleep(poll_interval_s)
            continue

        if header.version_update_begin != header.version_update_end:
            time.sleep(poll_interval_s)
            continue

        if last_version is not None and header.version_update_begin == last_version:
            time.sleep(poll_interval_s)
            continue

        try:
            frame = parse_telemetry_frame(raw, vehicle_index)
        except TelemetryParseError as e:
            if "mid-update" in e.message.lower():
                time.sleep(poll_interval_s)
                continue
            print(f"parse error: {e.message}", file=sys.stderr, flush=True)
            time.sleep(poll_interval_s)
            continue

        payload = frame.model_dump(mode="json")
        try:
            receipt = post_frames(api_base, session_id, [payload])
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"HTTP {e.code}: {body}", file=sys.stderr, flush=True)
            time.sleep(1.0)
            continue
        except urllib.error.URLError as e:
            print(f"network error: {e.reason}", file=sys.stderr, flush=True)
            time.sleep(1.0)
            continue

        last_version = header.version_update_begin
        tick = {
            "type": "tick",
            "version": last_version,
            "frames_stored": receipt.get("frames_stored", 0),
        }
        print(json.dumps(tick), flush=True)

        time.sleep(poll_interval_s)


def main() -> None:
    p = argparse.ArgumentParser(description="LMU → Delta Engineer telemetry bridge")
    p.add_argument("--api-base-url", required=True, help="e.g. http://127.0.0.1:8000")
    p.add_argument("--session-id", type=int, required=True)
    p.add_argument("--vehicle-index", type=int, default=0)
    p.add_argument(
        "--poll-interval-ms",
        type=int,
        default=10,
        help="Sleep between attempts when idle or after a successful post",
    )
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    interval = max(args.poll_interval_ms, 1) / 1000.0
    run_loop(
        args.api_base_url,
        args.session_id,
        args.vehicle_index,
        interval,
        args.verbose,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
