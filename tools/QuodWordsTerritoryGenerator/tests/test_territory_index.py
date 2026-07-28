from __future__ import annotations

import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from grid_math import GridCell  # noqa: E402
from row_spans import RowSpan  # noqa: E402
from territory_index import (  # noqa: E402
    TerritoryIndex,
    TerritoryIndexError,
    verify_capacity,
)


def test_empty_resource_has_zero_cells() -> None:
    territory = TerritoryIndex.from_spans(
        [],
        maximum_code_count=100,
    )

    assert territory.cell_count == 0
    assert territory.remaining_capacity == 100


def test_single_span_assigns_zero_based_indices() -> None:
    territory = TerritoryIndex.from_spans(
        [RowSpan(row=4, start_column=10, end_column=12)],
        maximum_code_count=100,
    )

    assert territory.index_for_cell(GridCell(column=10, row=4)) == 0
    assert territory.index_for_cell(GridCell(column=11, row=4)) == 1
    assert territory.index_for_cell(GridCell(column=12, row=4)) == 2


def test_indices_continue_across_gaps_and_rows() -> None:
    territory = TerritoryIndex.from_spans(
        [
            RowSpan(row=0, start_column=2, end_column=3),
            RowSpan(row=0, start_column=7, end_column=7),
            RowSpan(row=5, start_column=-2, end_column=0),
        ],
        maximum_code_count=100,
    )

    assert territory.index_for_cell(GridCell(column=2, row=0)) == 0
    assert territory.index_for_cell(GridCell(column=3, row=0)) == 1
    assert territory.index_for_cell(GridCell(column=7, row=0)) == 2
    assert territory.index_for_cell(GridCell(column=-2, row=5)) == 3
    assert territory.index_for_cell(GridCell(column=0, row=5)) == 5


def test_reverse_lookup_returns_exact_cells() -> None:
    territory = TerritoryIndex.from_spans(
        [
            RowSpan(row=-3, start_column=-4, end_column=-2),
            RowSpan(row=2, start_column=8, end_column=9),
        ],
        maximum_code_count=100,
    )

    assert territory.cell_for_index(0) == GridCell(column=-4, row=-3)
    assert territory.cell_for_index(2) == GridCell(column=-2, row=-3)
    assert territory.cell_for_index(3) == GridCell(column=8, row=2)
    assert territory.cell_for_index(4) == GridCell(column=9, row=2)


def test_every_cell_round_trips() -> None:
    territory = TerritoryIndex.from_spans(
        [
            RowSpan(row=-1, start_column=-2, end_column=1),
            RowSpan(row=3, start_column=10, end_column=12),
        ],
        maximum_code_count=100,
    )

    for index in range(territory.cell_count):
        cell = territory.cell_for_index(index)
        assert territory.index_for_cell(cell) == index


def test_cell_in_gap_is_rejected() -> None:
    territory = TerritoryIndex.from_spans(
        [
            RowSpan(row=1, start_column=0, end_column=2),
            RowSpan(row=1, start_column=5, end_column=7),
        ],
        maximum_code_count=100,
    )

    with pytest.raises(
        TerritoryIndexError,
        match="not present",
    ):
        territory.index_for_cell(GridCell(column=4, row=1))


def test_cell_on_unrepresented_row_is_rejected() -> None:
    territory = TerritoryIndex.from_spans(
        [RowSpan(row=1, start_column=0, end_column=2)],
        maximum_code_count=100,
    )

    with pytest.raises(
        TerritoryIndexError,
        match="not present",
    ):
        territory.index_for_cell(GridCell(column=1, row=2))


def test_negative_index_is_rejected() -> None:
    territory = TerritoryIndex.from_spans(
        [RowSpan(row=0, start_column=0, end_column=0)],
        maximum_code_count=100,
    )

    with pytest.raises(
        TerritoryIndexError,
        match="must not be negative",
    ):
        territory.cell_for_index(-1)


def test_index_beyond_generated_range_is_rejected() -> None:
    territory = TerritoryIndex.from_spans(
        [RowSpan(row=0, start_column=0, end_column=2)],
        maximum_code_count=100,
    )

    with pytest.raises(
        TerritoryIndexError,
        match="outside the generated cell range",
    ):
        territory.cell_for_index(3)


def test_exact_capacity_is_allowed() -> None:
    territory = TerritoryIndex.from_spans(
        [RowSpan(row=0, start_column=0, end_column=4)],
        maximum_code_count=5,
    )

    assert territory.cell_count == 5
    assert territory.remaining_capacity == 0
    assert verify_capacity(territory.spans, 5) == 0


def test_capacity_excess_is_rejected() -> None:
    spans = [RowSpan(row=0, start_column=0, end_column=5)]

    with pytest.raises(
        TerritoryIndexError,
        match="exceeds maximum",
    ):
        TerritoryIndex.from_spans(
            spans,
            maximum_code_count=5,
        )

    with pytest.raises(
        TerritoryIndexError,
        match="exceeds maximum",
    ):
        verify_capacity(spans, 5)
