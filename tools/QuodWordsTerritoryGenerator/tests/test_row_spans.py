from __future__ import annotations

import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from grid_math import GridCell  # noqa: E402
from row_spans import (  # noqa: E402
    RowSpan,
    RowSpanError,
    compress_cells,
    count_cells,
    expand_spans,
    validate_spans,
)


def test_empty_cells_produce_no_spans() -> None:
    assert compress_cells([]) == ()


def test_single_cell_produces_single_span() -> None:
    assert compress_cells([GridCell(column=4, row=7)]) == (
        RowSpan(row=7, start_column=4, end_column=4),
    )


def test_adjacent_cells_are_merged() -> None:
    cells = [
        GridCell(column=3, row=2),
        GridCell(column=4, row=2),
        GridCell(column=5, row=2),
    ]

    assert compress_cells(cells) == (
        RowSpan(row=2, start_column=3, end_column=5),
    )


def test_gap_creates_separate_spans() -> None:
    cells = [
        GridCell(column=1, row=0),
        GridCell(column=2, row=0),
        GridCell(column=4, row=0),
    ]

    assert compress_cells(cells) == (
        RowSpan(row=0, start_column=1, end_column=2),
        RowSpan(row=0, start_column=4, end_column=4),
    )


def test_different_rows_create_separate_spans() -> None:
    cells = [
        GridCell(column=1, row=0),
        GridCell(column=2, row=0),
        GridCell(column=1, row=1),
        GridCell(column=2, row=1),
    ]

    assert compress_cells(cells) == (
        RowSpan(row=0, start_column=1, end_column=2),
        RowSpan(row=1, start_column=1, end_column=2),
    )


def test_input_order_does_not_affect_output() -> None:
    cells = [
        GridCell(column=5, row=1),
        GridCell(column=3, row=1),
        GridCell(column=4, row=1),
    ]

    assert compress_cells(cells) == (
        RowSpan(row=1, start_column=3, end_column=5),
    )


def test_duplicate_cells_are_removed() -> None:
    cell = GridCell(column=8, row=-2)

    assert compress_cells([cell, cell, cell]) == (
        RowSpan(row=-2, start_column=8, end_column=8),
    )


def test_negative_rows_and_columns_are_supported() -> None:
    cells = [
        GridCell(column=-3, row=-4),
        GridCell(column=-2, row=-4),
        GridCell(column=-1, row=-4),
    ]

    assert compress_cells(cells) == (
        RowSpan(row=-4, start_column=-3, end_column=-1),
    )


def test_expand_reverses_compression() -> None:
    cells = (
        GridCell(column=-2, row=-1),
        GridCell(column=-1, row=-1),
        GridCell(column=4, row=3),
        GridCell(column=5, row=3),
        GridCell(column=6, row=3),
    )

    spans = compress_cells(cells)

    assert expand_spans(spans) == cells


def test_cell_count() -> None:
    spans = (
        RowSpan(row=0, start_column=1, end_column=3),
        RowSpan(row=2, start_column=10, end_column=11),
    )

    assert count_cells(spans) == 5


def test_invalid_reversed_span_is_rejected() -> None:
    with pytest.raises(
        RowSpanError,
        match="greater than or equal",
    ):
        RowSpan(row=0, start_column=5, end_column=4)


def test_unsorted_rows_are_rejected() -> None:
    spans = (
        RowSpan(row=2, start_column=0, end_column=1),
        RowSpan(row=1, start_column=0, end_column=1),
    )

    with pytest.raises(
        RowSpanError,
        match="sorted by row",
    ):
        validate_spans(spans)


def test_overlapping_spans_are_rejected() -> None:
    spans = (
        RowSpan(row=1, start_column=0, end_column=4),
        RowSpan(row=1, start_column=4, end_column=7),
    )

    with pytest.raises(
        RowSpanError,
        match="must not overlap",
    ):
        validate_spans(spans)


def test_adjacent_spans_are_rejected() -> None:
    spans = (
        RowSpan(row=1, start_column=0, end_column=4),
        RowSpan(row=1, start_column=5, end_column=7),
    )

    with pytest.raises(
        RowSpanError,
        match="must be merged",
    ):
        validate_spans(spans)
