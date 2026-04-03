"""Tests for scoring buffer parsing helpers."""

from src.capture.scoring_parser import (
    ScoringCaptureContext,
    should_post_telemetry,
)


def test_should_post_telemetry_requires_track_and_car() -> None:
    ctx = ScoringCaptureContext(
        track_name="",
        car_name="GT",
        driver_name="Player",
        session_type="practice",
        game_phase=5,
        in_realtime=True,
        current_et=10.0,
        end_et=600.0,
        max_laps=0,
        num_vehicles=1,
    )
    assert should_post_telemetry(ctx) is False


def test_should_post_skips_session_over() -> None:
    ctx = ScoringCaptureContext(
        track_name="Le Mans",
        car_name="GT",
        driver_name="Player",
        session_type="race",
        game_phase=8,
        in_realtime=True,
        current_et=100.0,
        end_et=200.0,
        max_laps=10,
        num_vehicles=1,
    )
    assert should_post_telemetry(ctx) is False


def test_should_post_green_flag() -> None:
    ctx = ScoringCaptureContext(
        track_name="Le Mans",
        car_name="GT",
        driver_name="Player",
        session_type="practice",
        game_phase=5,
        in_realtime=True,
        current_et=50.0,
        end_et=1800.0,
        max_laps=0,
        num_vehicles=2,
    )
    assert should_post_telemetry(ctx) is True
