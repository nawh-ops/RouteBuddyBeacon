from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

from grid_math import GridCell


class RowSpanError(ValueError):
    """Raised when row-span data is invalid."""


@dataclass(frozen=True, order=True)
class RowSpan:
    row: int
    start_column: int
    end_column: int

    def __post_init__(self) -> None:
        if self.end_column < self.start_column:
            raise RowSpanError(
                "end_column must be greater than or equal to start_column."
            )

    @property
    def cell_count(self) -> int:
        return self.end_column - self.start_column + 1

    def cells(self) -> Iterator[GridCell]:
        for column in range(self.start_column, self.end_column + 1):
            yield GridCell(column=column, row=self.row)


def compress_cells(cells: Iterable[GridCell]) -> tuple[RowSpan, ...]:
    ordered_cells = sorted(set(cells), key=lambda cell: (cell.row, cell.column))

    if not ordered_cells:
        return ()

    spans: list[RowSpan] = []

    current_row = ordered_cells[0].row
    start_column = ordered_cells[0].column
    end_column = ordered_cells[0].column

    for cell in ordered_cells[1:]:
        is_same_row = cell.row == current_row
        is_adjacent = cell.column == end_column + 1

        if is_same_row and is_adjacent:
            end_column = cell.column
            continue

        spans.append(
            RowSpan(
                row=current_row,
                start_column=start_column,
                end_column=end_column,
            )
        )

        current_row = cell.row
        start_column = cell.column
        end_column = cell.column

    spans.append(
        RowSpan(
            row=current_row,
            start_column=start_column,
            end_column=end_column,
        )
    )

    return tuple(spans)


def expand_spans(spans: Iterable[RowSpan]) -> tuple[GridCell, ...]:
    validated_spans = validate_spans(spans)

    cells: list[GridCell] = []
    for span in validated_spans:
        cells.extend(span.cells())

    return tuple(cells)


def validate_spans(spans: Iterable[RowSpan]) -> tuple[RowSpan, ...]:
    ordered_spans = tuple(spans)

    previous: RowSpan | None = None

    for span in ordered_spans:
        if previous is not None:
            if span.row < previous.row:
                raise RowSpanError("Row spans must be sorted by row.")

            if span.row == previous.row:
                if span.start_column <= previous.end_column:
                    raise RowSpanError(
                        "Row spans on the same row must not overlap."
                    )

                if span.start_column == previous.end_column + 1:
                    raise RowSpanError(
                        "Adjacent spans on the same row must be merged."
                    )

        previous = span

    return ordered_spans


def count_cells(spans: Iterable[RowSpan]) -> int:
    return sum(span.cell_count for span in validate_spans(spans))
