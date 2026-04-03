"""Unit tests for the car setup parameter schema (issue #12)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.schemas import SetupParameters


def test_setup_parameters_empty():
    p = SetupParameters()
    assert p.model_dump(exclude_none=True) == {}


def test_setup_parameters_known_fields():
    p = SetupParameters(
        front_wing=5,
        rear_wing=8,
        brake_bias=0.58,
        traction_control=2,
        abs_level=1,
        fuel_load_liters=45.5,
    )
    d = p.model_dump(mode="json")
    assert d["front_wing"] == 5
    assert d["rear_wing"] == 8
    assert d["brake_bias"] == 0.58
    assert d["traction_control"] == 2
    assert d["abs_level"] == 1
    assert d["fuel_load_liters"] == 45.5


def test_setup_parameters_extra_keys_round_trip():
    p = SetupParameters(rear_wing=7, damper_slow_fl=12, custom_map="B")
    d = p.model_dump(mode="json")
    assert d["rear_wing"] == 7
    assert d["damper_slow_fl"] == 12
    assert d["custom_map"] == "B"

    p2 = SetupParameters.model_validate(d)
    assert p2.rear_wing == 7
    assert p2.model_dump(mode="json")["damper_slow_fl"] == 12


@pytest.mark.parametrize(
    "field,value",
    [
        ("traction_control", -1),
        ("abs_level", -1),
        ("fuel_load_liters", -0.1),
    ],
)
def test_setup_parameters_rejects_invalid_known_fields(field: str, value):
    with pytest.raises(ValidationError):
        SetupParameters.model_validate({field: value})


def test_setup_parameters_from_partial_dict():
    p = SetupParameters.model_validate({"rear_wing": 4, "game_specific": True})
    assert p.rear_wing == 4
    assert p.model_dump(mode="json")["game_specific"] is True
