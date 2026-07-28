from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Iterable

from grid_math import GridCell
from row_spans import RowSpan, count_cells, validate_spans


class TerritoryIndexError(ValueError):
    """Raised when territory indexing data or a lookup is invalid."""


@dataclass(frozen=True)
class TerritoryIndex:
    spans: tuple[RowSpan, ...]
    maximum_code_count: int

    _span_start_indices: tuple[int, ...] = field(
        init=False,
        repr=False,
    )
    _span_keys: tuple[tuple[int, int], ...] = field(
        init=False,
        repr=False,
    )
    _cell_count: int = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if self.maximum_code_count <= 0:
            raise TerritoryIndexError(
                "maximum_code_count must be greater than zero."
            )

        validated_spans = validate_spans(self.spans)
        object.__setattr__(self, "spans", validated_spans)

        start_indices: list[int] = []
        next_index = 0

        for span in validated_spans:
            start_indices.append(next_index)
            next_index += span.cell_count

        if next_index > self.maximum_code_count:
            raise TerritoryIndexError(
                "Territory cell count exceeds maximum public-code capacity."
            )

        object.__setattr__(
            self,
            "_span_start_indices",
            tuple(start_indices),
        )
        object.__setattr__(
            self,
            "_span_keys",
            tuple(
                (span.row, span.start_column)
                for span in validated_spans
            ),
        )
        object.__setattr__(self, "_cell_count", next_index)

    @classmethod
    def from_spans(
        cls,
        spans: Iterable[RowSpan],
        maximum_code_count: int,
    ) -> TerritoryIndex:
        return cls(
            spans=tuple(spans),
            maximum_code_count=maximum_code_count,
        )

    @property
    def cell_count(self) -> int:
        return self._cell_count

    @property
    def remaining_capacity(self) -> int:
        return self.maximum_code_count - self.cell_count

    def index_for_cell(self, cell: GridCell) -> int:
        if not self.spans:
            raise TerritoryIndexError(
                f"Cell is not present in territory resource: {cell}"
            )

        candidate_position = bisect_right(
            self._span_keys,
            (cell.row, cell.column),
        ) - 1

        if candidate_position < 0:
            raise TerritoryIndexError(
                f"Cell is not present in territory resource: {cell}"
            )

        span = self.spans[candidate_position]

        if (
            cell.row != span.row
            or cell.column < span.start_column
            or cell.column > span.end_column
        ):
            raise TerritoryIndexError(
                f"Cell is not present in territory resource: {cell}"
            )

        return (
            self._span_start_indices[candidate_position]
            + cell.column
            - span.start_column
        )

    def cell_for_index(self, index: int) -> GridCell:
        if index < 0:
            raise TerritoryIndexError(
                "Territory index must not be negative."
            )

        if index >= self.cell_count:
            raise TerritoryIndexError(
                "Territory index is outside the generated cell range."
            )

        span_position = bisect_right(
            self._span_start_indices,
            index,
        ) - 1

        span = self.spans[span_position]
        offset = index - self._span_start_indices[span_position]

        return GridCell(
            column=span.start_column + offset,
            row=span.row,
        )


def verify_capacity(
    spans: Iterable[RowSpan],
    maximum_code_count: int,
) -> int:
    if maximum_code_count <= 0:
        raise TerritoryIndexError(
            "maximum_code_count must be greater than zero."
        )

    total = count_cells(spans)

    if total > maximum_code_count:
        raise TerritoryIndexError(
            "Territory cell count exceeds maximum public-code capacity."
        )

    return maximum_code_count - total
