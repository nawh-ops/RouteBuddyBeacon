from __future__ import annotations

import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from grid_math import GridCell, GridDefinition, GridError  # noqa: E402


@pytest.fixture
def grid() -> GridDefinition:
    return GridDefinition(
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
    )


def test_origin_is_in_cell_zero_zero(grid: GridDefinition) -> None:
    assert grid.cell_for_point(0, 0) == GridCell(column=0, row=0)


def test_point_just_inside_first_cell(grid: GridDefinition) -> None:
    assert grid.cell_for_point(31.999, 31.999) == GridCell(
        column=0,
        row=0,
    )


def test_positive_boundary_enters_next_cell(grid: GridDefinition) -> None:
    assert grid.cell_for_point(32, 32) == GridCell(column=1, row=1)


def test_negative_coordinate_uses_floor_not_truncation(
    grid: GridDefinition,
) -> None:
    assert grid.cell_for_point(-0.001, -0.001) == GridCell(
        column=-1,
        row=-1,
    )


def test_negative_boundary_is_exact(grid: GridDefinition) -> None:
    assert grid.cell_for_point(-32, -32) == GridCell(
        column=-1,
        row=-1,
    )


def test_negative_point_beyond_boundary_enters_previous_cell(
    grid: GridDefinition,
) -> None:
    assert grid.cell_for_point(-32.001, -32.001) == GridCell(
        column=-2,
        row=-2,
    )


def test_cell_bounds(grid: GridDefinition) -> None:
    assert grid.cell_bounds(GridCell(column=2, row=-3)) == (
        64,
        -96,
        96,
        -64,
    )


def test_cell_centre(grid: GridDefinition) -> None:
    assert grid.cell_centre(GridCell(column=2, row=-3)) == (
        80,
        -80,
    )


def test_non_zero_origin() -> None:
    grid = GridDefinition(
        origin_x=100,
        origin_y=-200,
        cell_size_metres=32,
    )

    assert grid.cell_for_point(100, -200) == GridCell(
        column=0,
        row=0,
    )
    assert grid.cell_centre(GridCell(column=0, row=0)) == (
        116,
        -184,
    )


def test_zero_cell_size_is_rejected() -> None:
    with pytest.raises(
        GridError,
        match="must be greater than zero",
    ):
        GridDefinition(
            origin_x=0,
            origin_y=0,
            cell_size_metres=0,
        )
