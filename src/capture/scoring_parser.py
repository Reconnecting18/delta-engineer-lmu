"""Parse rF2/LMU scoring shared memory for automatic capture context."""

from __future__ import annotations

from dataclasses import dataclass

from src.capture.rf2_scoring_ctypes import RF2_SCORING_BUFFER_BYTES, rF2Scoring
from src.core.parser import map_session_type


def _decode_rf2_bytes(buf: bytes) -> str:
    return buf.split(b"\x00", 1)[0].decode("latin-1", errors="replace").strip()


@dataclass(frozen=True)
class ScoringCaptureContext:
    """Session context from scoring buffer (player vehicle + session info)."""

    track_name: str
    car_name: str
    driver_name: str
    session_type: str
    game_phase: int
    in_realtime: bool
    current_et: float
    end_et: float
    max_laps: int
    num_vehicles: int


def parse_scoring_buffer(raw: bytes | None) -> ScoringCaptureContext | None:
    """Return player session context, or None if buffer missing / mid-update / invalid.

    None means: no scoring map, torn read, too small, or empty vehicle list.
    """
    if raw is None or len(raw) < RF2_SCORING_BUFFER_BYTES:
        return None

    begin = int.from_bytes(raw[0:4], "little", signed=True)
    end = int.from_bytes(raw[4:8], "little", signed=True)
    if begin != end:
        return None

    scoring = rF2Scoring.from_buffer_copy(raw)

    info = scoring.mScoringInfo
    n = int(info.mNumVehicles)
    if n < 1:
        return None

    player_idx = -1
    limit = min(n, 128)
    for i in range(limit):
        if scoring.mVehicles[i].mIsPlayer:
            player_idx = i
            break
    if player_idx < 0:
        player_idx = 0

    veh = scoring.mVehicles[player_idx]
    track = _decode_rf2_bytes(bytes(info.mTrackName))
    car = _decode_rf2_bytes(bytes(veh.mVehicleName))
    driver = _decode_rf2_bytes(bytes(veh.mDriverName))
    if not driver and info.mPlayerName:
        driver = _decode_rf2_bytes(bytes(info.mPlayerName))
    if not driver:
        driver = "Player"

    session_type = map_session_type(int(info.mSession))

    return ScoringCaptureContext(
        track_name=track,
        car_name=car,
        driver_name=driver,
        session_type=session_type,
        game_phase=int(info.mGamePhase),
        in_realtime=bool(info.mInRealtime),
        current_et=float(info.mCurrentET),
        end_et=float(info.mEndET),
        max_laps=int(info.mMaxLaps),
        num_vehicles=n,
    )


def should_post_telemetry(ctx: ScoringCaptureContext) -> bool:
    """True when the sim is in a state where ingesting telemetry frames makes sense."""
    if not ctx.track_name or not ctx.car_name:
        return False
    # Session over / stopped / heartbeat-only
    if ctx.game_phase in (7, 8, 9):
        return False
    # Menus / pre-session: wait until realtime or on-track phases
    if ctx.game_phase == 0 and not ctx.in_realtime:
        return False
    return True
