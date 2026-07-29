from __future__ import annotations

import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from config_values import (  # noqa: E402
    ConfigValueError,
    require_boolean,
    require_integer,
    require_integer_list,
    require_optional_string,
    require_string,
    require_string_list,
)


def test_valid_string_is_returned() -> None:
    assert require_string("GB", field="territoryCode") == "GB"


def test_empty_string_is_rejected() -> None:
    with pytest.raises(ConfigValueError, match="must not be empty"):
        require_string("", field="territoryCode")


def test_non_string_is_rejected() -> None:
    with pytest.raises(ConfigValueError, match="must be a string"):
        require_string(123, field="territoryCode")


def test_real_boolean_is_returned() -> None:
    assert require_boolean(True, field="coverage.includeEngland") is True
    assert require_boolean(False, field="coverage.includeEngland") is False


@pytest.mark.parametrize(
    "invalid_value",
    ["true", "false", 1, 0, None],
)
def test_boolean_lookalikes_are_rejected(invalid_value) -> None:
    with pytest.raises(ConfigValueError, match="must be a boolean"):
        require_boolean(
            invalid_value,
            field="coverage.includeEngland",
        )


def test_valid_integer_is_returned() -> None:
    assert require_integer(
        32,
        field="grid.baseCellSizeMetres",
        minimum=1,
    ) == 32


@pytest.mark.parametrize(
    "invalid_value",
    ["32", 32.0, True, False, None],
)
def test_integer_lookalikes_are_rejected(invalid_value) -> None:
    with pytest.raises(ConfigValueError, match="must be an integer"):
        require_integer(
            invalid_value,
            field="grid.baseCellSizeMetres",
        )


def test_integer_below_minimum_is_rejected() -> None:
    with pytest.raises(
        ConfigValueError,
        match="greater than or equal to 1",
    ):
        require_integer(
            0,
            field="grid.baseCellSizeMetres",
            minimum=1,
        )


def test_valid_integer_list_is_returned() -> None:
    assert require_integer_list(
        [0, 1, 5, 10],
        field="marine.candidateThresholds",
        minimum=0,
        require_unique=True,
        require_ascending=True,
    ) == (0, 1, 5, 10)


def test_non_list_is_rejected() -> None:
    with pytest.raises(ConfigValueError, match="must be a list"):
        require_integer_list(
            "0, 1, 5",
            field="marine.candidateThresholds",
        )


def test_duplicate_list_values_are_rejected() -> None:
    with pytest.raises(ConfigValueError, match="must be unique"):
        require_integer_list(
            [0, 1, 1, 5],
            field="marine.candidateThresholds",
            require_unique=True,
        )


def test_unsorted_list_values_are_rejected() -> None:
    with pytest.raises(ConfigValueError, match="ascending order"):
        require_integer_list(
            [0, 5, 1],
            field="marine.candidateThresholds",
            require_ascending=True,
        )


def test_optional_string_accepts_none() -> None:
    assert require_optional_string(
        None,
        field="geometrySource.snapshotDate",
    ) is None


def test_optional_string_accepts_string() -> None:
    assert require_optional_string(
        "2026-07-29",
        field="geometrySource.snapshotDate",
    ) == "2026-07-29"


def test_optional_string_rejects_non_string_value() -> None:
    with pytest.raises(ConfigValueError, match="must be a string"):
        require_optional_string(
            20260729,
            field="geometrySource.snapshotDate",
        )


def test_valid_string_list_is_returned() -> None:
    assert require_string_list(
        ["Foula", "Fair Isle"],
        field="requiredIslandTests.bufferGenerating",
        allow_empty_list=False,
        require_unique=True,
    ) == ("Foula", "Fair Isle")


def test_string_list_rejects_non_list() -> None:
    with pytest.raises(ConfigValueError, match="must be a list"):
        require_string_list(
            "Foula",
            field="requiredIslandTests.bufferGenerating",
        )


def test_string_list_rejects_non_string_member() -> None:
    with pytest.raises(
        ConfigValueError,
        match=r"bufferGenerating\[1\] must be a string",
    ):
        require_string_list(
            ["Foula", 12],
            field="requiredIslandTests.bufferGenerating",
        )


def test_required_string_list_rejects_empty_list() -> None:
    with pytest.raises(ConfigValueError, match="must not be empty"):
        require_string_list(
            [],
            field="requiredIslandTests.bufferGenerating",
            allow_empty_list=False,
        )


def test_string_list_rejects_duplicates_when_required() -> None:
    with pytest.raises(ConfigValueError, match="must be unique"):
        require_string_list(
            ["Foula", "Foula"],
            field="requiredIslandTests.bufferGenerating",
            require_unique=True,
        )
