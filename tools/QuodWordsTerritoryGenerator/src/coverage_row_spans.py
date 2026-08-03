from __future__ import annotations

import math
from collections.abc import Iterable, Iterator

from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.prepared import prep

from grid_math import GridCell, GridDefinition
from row_spans import RowSpan


class CoverageRowSpanError(ValueError):
    """Raised when coverage row spans cannot be generated."""


def _validate_geometry(geometry: BaseGeometry) -> None:
    if not geometry.is_valid:
        raise CoverageRowSpanError("Coverage geometry must be valid.")


def _candidate_cells_reference(
    geometry: BaseGeometry,
    grid: GridDefinition,
) -> Iterator[GridCell]:
    min_x, min_y, max_x, max_y = geometry.bounds

    minimum_cell = grid.cell_for_point(min_x, min_y)
    maximum_cell = grid.cell_for_point(max_x, max_y)

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


def generate_coverage_row_spans_reference(
    geometry: BaseGeometry,
    grid: GridDefinition,
) -> tuple[RowSpan, ...]:
    """
    Generate spans by testing every candidate cell centre.

    This deliberately simple implementation is retained as a correctness
    reference for tests and small geometries. It is not suitable for the
    complete GB mask because that would require approximately one billion
    centre-point tests.
    """

    if geometry.is_empty:
        return ()

    _validate_geometry(geometry)

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

    for cell in _candidate_cells_reference(geometry, grid):
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


def _minimum_centre_index(
    coordinate: float,
    origin: float,
    cell_size: float,
) -> int:
    raw_index = ((coordinate - origin) / cell_size) - 0.5
    return math.ceil(raw_index - 1e-10)


def _maximum_centre_index(
    coordinate: float,
    origin: float,
    cell_size: float,
) -> int:
    raw_index = ((coordinate - origin) / cell_size) - 0.5
    return math.floor(raw_index + 1e-10)


def _line_intervals(
    geometry: BaseGeometry,
) -> Iterator[tuple[float, float]]:
    """
    Yield horizontal x intervals from a scanline intersection.

    Polygon intersections normally produce LineString or MultiLineString
    geometries. GeometryCollection is handled recursively. A Point can occur
    where the scanline only touches the polygon boundary.
    """

    if geometry.is_empty:
        return

    geometry_type = geometry.geom_type

    if geometry_type in {"LineString", "LinearRing"}:
        min_x, _, max_x, _ = geometry.bounds
        yield min_x, max_x
        return

    if geometry_type == "Point":
        yield geometry.x, geometry.x
        return

    if hasattr(geometry, "geoms"):
        for part in geometry.geoms:
            yield from _line_intervals(part)


def _merge_column_intervals(
    intervals: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    ordered = sorted(intervals)

    if not ordered:
        return ()

    merged: list[tuple[int, int]] = []
    current_start, current_end = ordered[0]

    for start, end in ordered[1:]:
        if start <= current_end + 1:
            current_end = max(current_end, end)
            continue

        merged.append((current_start, current_end))
        current_start = start
        current_end = end

    merged.append((current_start, current_end))

    return tuple(merged)


def generate_coverage_row_spans(
    geometry: BaseGeometry,
    grid: GridDefinition,
) -> tuple[RowSpan, ...]:
    """
    Generate ordered spans using one horizontal scanline per candidate row.

    Each scanline intersects the coverage geometry at the exact y coordinate
    of the 32 metre cell centres. The resulting horizontal intervals are
    converted directly into inclusive column ranges.

    Boundary coordinates remain inclusive, matching the documented rule that
    a cell centre exactly on the geometry boundary counts as covered.
    """

    if geometry.is_empty:
        return ()

    _validate_geometry(geometry)

    min_x, min_y, max_x, max_y = geometry.bounds
    cell_size = grid.cell_size_metres

    minimum_row = _minimum_centre_index(
        min_y,
        grid.origin_y,
        cell_size,
    )
    maximum_row = _maximum_centre_index(
        max_y,
        grid.origin_y,
        cell_size,
    )

    scanline_min_x = min_x - cell_size
    scanline_max_x = max_x + cell_size

    prepared_geometry = prep(geometry)
    spans: list[RowSpan] = []

    for row in range(minimum_row, maximum_row + 1):
        _, centre_y = grid.cell_centre(
            GridCell(column=0, row=row)
        )

        scanline = LineString(
            [
                (scanline_min_x, centre_y),
                (scanline_max_x, centre_y),
            ]
        )

        intersection = geometry.intersection(scanline)
        column_intervals: list[tuple[int, int]] = []

        for interval_min_x, interval_max_x in _line_intervals(
            intersection
        ):
            minimum_column = _minimum_centre_index(
                interval_min_x,
                grid.origin_x,
                cell_size,
            )
            maximum_column = _maximum_centre_index(
                interval_max_x,
                grid.origin_x,
                cell_size,
            )

            if minimum_column > maximum_column:
                continue

            # A point-only intersection is accepted only when the corresponding
            # grid centre is genuinely covered by the source geometry.
            if interval_min_x == interval_max_x:
                centre_x, _ = grid.cell_centre(
                    GridCell(
                        column=minimum_column,
                        row=row,
                    )
                )

                if not prepared_geometry.covers(
                    Point(centre_x, centre_y)
                ):
                    continue

            column_intervals.append(
                (minimum_column, maximum_column)
            )

        for start_column, end_column in _merge_column_intervals(
            column_intervals
        ):
            spans.append(
                RowSpan(
                    row=row,
                    start_column=start_column,
                    end_column=end_column,
                )
            )

    return tuple(spans)
