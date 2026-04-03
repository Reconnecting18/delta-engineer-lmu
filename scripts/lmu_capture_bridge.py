#!/usr/bin/env python3
"""Poll LMU/rF2 shared memory and POST frames to Delta Engineer API.

Manual mode: ``--session-id`` — POST with fixed session id.

Automatic mode: ``--auto`` — reads ``$rFactor2SMMP_Scoring$`` for track / car /
driver / session type, then ``POST /telemetry`` without ``session_id`` so the API
``get_or_create_session`` pipeline assigns sessions (including on practice→qual
transitions).

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

from src.capture.lmu_shared_memory import (  # noqa: E402
    read_rf2_scoring_buffer,
    read_rf2_telemetry_buffer,
)
from src.capture.scoring_parser import (  # noqa: E402
    parse_scoring_buffer,
    should_post_telemetry,
)
from src.core.parser import (  # noqa: E402
    TelemetryParseError,
    parse_telemetry_frame,
    parse_telemetry_header,
)


def post_telemetry_manual(
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


def post_telemetry_auto(
    api_base: str,
    track_name: str,
    car_name: str,
    driver_name: str,
    session_type: str,
    frames: list[dict],
    timeout_s: float = 5.0,
) -> dict:
    url = api_base.rstrip("/") + "/telemetry/"
    body = json.dumps(
        {
            "track_name": track_name,
            "car_name": car_name,
            "driver_name": driver_name,
            "session_type": session_type,
            "frames": frames,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_loop_manual(
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
            receipt = post_telemetry_manual(api_base, session_id, [payload])
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
        _emit_tick(
            last_version,
            receipt,
            capture_mode="manual",
        )

        time.sleep(poll_interval_s)


def run_loop_auto(
    api_base: str,
    vehicle_index: int,
    poll_interval_s: float,
    verbose: bool,
) -> None:
    last_telemetry_version: int | None = None

    while True:
        raw_t = read_rf2_telemetry_buffer()
        raw_s = read_rf2_scoring_buffer()

        if raw_t is None:
            if verbose:
                print(
                    "LMU telemetry mapping not found (is LMU running with the plugin?)",
                    file=sys.stderr,
                    flush=True,
                )
            time.sleep(max(poll_interval_s, 0.5))
            continue

        ctx = parse_scoring_buffer(raw_s)
        if ctx is None or not should_post_telemetry(ctx):
            if verbose and raw_s is None:
                print(
                    "Scoring mapping not found — enable Scoring in plugin subscription",
                    file=sys.stderr,
                    flush=True,
                )
            time.sleep(max(poll_interval_s, 0.05))
            continue

        if len(raw_t) < 16:
            time.sleep(poll_interval_s)
            continue

        try:
            header = parse_telemetry_header(raw_t)
        except TelemetryParseError:
            time.sleep(poll_interval_s)
            continue

        if header.version_update_begin != header.version_update_end:
            time.sleep(poll_interval_s)
            continue

        if (
            last_telemetry_version is not None
            and header.version_update_begin == last_telemetry_version
        ):
            time.sleep(poll_interval_s)
            continue

        try:
            frame = parse_telemetry_frame(raw_t, vehicle_index)
        except TelemetryParseError as e:
            if "mid-update" in e.message.lower():
                time.sleep(poll_interval_s)
                continue
            print(f"parse error: {e.message}", file=sys.stderr, flush=True)
            time.sleep(poll_interval_s)
            continue

        payload = frame.model_dump(mode="json")
        try:
            receipt = post_telemetry_auto(
                api_base,
                ctx.track_name,
                ctx.car_name,
                ctx.driver_name,
                ctx.session_type,
                [payload],
            )
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"HTTP {e.code}: {body}", file=sys.stderr, flush=True)
            time.sleep(1.0)
            continue
        except urllib.error.URLError as e:
            print(f"network error: {e.reason}", file=sys.stderr, flush=True)
            time.sleep(1.0)
            continue

        last_telemetry_version = header.version_update_begin
        _emit_tick(
            last_telemetry_version,
            receipt,
            capture_mode="auto",
            track_name=ctx.track_name,
            session_type=ctx.session_type,
            game_phase=ctx.game_phase,
            current_et=ctx.current_et,
            end_et=ctx.end_et,
            max_laps=ctx.max_laps,
        )

        time.sleep(poll_interval_s)


def _emit_tick(
    version: int,
    receipt: dict,
    capture_mode: str,
    track_name: str | None = None,
    session_type: str | None = None,
    game_phase: int | None = None,
    current_et: float | None = None,
    end_et: float | None = None,
    max_laps: int | None = None,
) -> None:
    tick: dict = {
        "type": "tick",
        "version": version,
        "frames_stored": receipt.get("frames_stored", 0),
        "api_session_id": receipt.get("session_id"),
        "capture_mode": capture_mode,
    }
    if track_name is not None:
        tick["track_name"] = track_name
    if session_type is not None:
        tick["session_type"] = session_type
    if game_phase is not None:
        tick["game_phase"] = game_phase
    if current_et is not None:
        tick["current_et"] = current_et
    if end_et is not None:
        tick["end_et"] = end_et
    if max_laps is not None:
        tick["max_laps"] = max_laps
    print(json.dumps(tick), flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description="LMU → Delta Engineer telemetry bridge")
    p.add_argument("--api-base-url", required=True, help="e.g. http://127.0.0.1:8000")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--session-id", type=int, help="Fixed API session id (manual mode)")
    g.add_argument(
        "--auto",
        action="store_true",
        help="Derive track/car/driver/session type from scoring shared memory",
    )
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
    if args.auto:
        run_loop_auto(
            args.api_base_url,
            args.vehicle_index,
            interval,
            args.verbose,
        )
    else:
        run_loop_manual(
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
