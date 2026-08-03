from collections.abc import Iterator

from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.prepared import prep

from grid_math import GridCell, GridDefinition
from row_spans import RowSpan


class CoverageRowSpanError(ValueError):
    """Raised when coverage row spans cannot be generated."""


def _candidate_cells(
    geometry: BaseGeometry,
    grid: GridDefinition,
) -> Iterator[GridCell]:
    if geometry.is_empty:
        return

    min_x, min_y, max_x, max_y = geometry.bounds

    minimum_cell = grid.cell_for_point(min_x, min_y)
    maximum_cell = grid.cell_for_point(max_x, max_y)

    # Include one extra row and column around the bounds. Cell centres are
    # tested below, so the additional candidates cannot create false coverage.
    minimum_column = minimum_cell.column - 1
    maximum_column = maximum_cell.column + 1
    minimum_row = minimum_cell.row - 1
    maximum_row = maximum_cell.row + 1

    for row in range(minimum_row, maximum_row + 1):
        for column in range(minimum_column, maximum_column + 1):
            yield GridCell(
                column=column,
                row=row,
            )


def generate_coverage_row_spans(
    geometry: BaseGeometry,
    grid: GridDefinition,
) -> tuple[RowSpan, ...]:
    """
    Generate ordered row spans for cells whose centres are covered.

    ``covers`` is deliberately used rather than ``contains`` so that a cell
    centre lying exactly on the geometry boundary counts as included.
    """

    if geometry.is_empty:
        return ()

    if not geometry.is_valid:
        raise CoverageRowSpanError("Coverage geometry must be valid.")

    prepared_geometry = prep(geometry)
    spans: list[RowSpan] = []

    current_row: int | None = None
    span_start_column: int | None = None
    span_end_column: int | None = None

    def finish_span() -> None:
        nonlocal span_start_column, span_end_column

        if (
            current_row is None
            or span_start_column is None
            or span_end_column is None
        ):
            return

        spans.append(
            RowSpan(
                row=current_row,
                start_column=span_start_column,
                end_column=span_end_column,
            )
        )

        span_start_column = None
        span_end_column = None

    for cell in _candidate_cells(geometry, grid):
        centre_x, centre_y = grid.cell_centre(cell)
        is_covered = prepared_geometry.covers(
            Point(centre_x, centre_y)
        )

        if current_row is None:
            current_row = cell.row

        if cell.row != current_row:
            finish_span()
            current_row = cell.row

        if is_covered:
            if span_start_column is None:
                span_start_column = cell.column

            span_end_column = cell.column
        else:
            finish_span()

    finish_span()

    return tuple(spans)
