from __future__ import annotations

from dataclasses import dataclass
from math import floor


class GridError(ValueError):
    """Raised when grid parameters are invalid."""


@dataclass(frozen=True, order=True)
class GridCell:
    column: int
    row: int


@dataclass(frozen=True)
class GridDefinition:
    origin_x: float
    origin_y: float
    cell_size_metres: float

    def __post_init__(self) -> None:
        if self.cell_size_metres <= 0:
            raise GridError("cell_size_metres must be greater than zero.")

    def cell_for_point(self, x: float, y: float) -> GridCell:
        column = floor((x - self.origin_x) / self.cell_size_metres)
        row = floor((y - self.origin_y) / self.cell_size_metres)
        return GridCell(column=column, row=row)

    def cell_bounds(
        self,
        cell: GridCell,
    ) -> tuple[float, float, float, float]:
        min_x = self.origin_x + cell.column * self.cell_size_metres
        min_y = self.origin_y + cell.row * self.cell_size_metres
        max_x = min_x + self.cell_size_metres
        max_y = min_y + self.cell_size_metres
        return min_x, min_y, max_x, max_y

    def cell_centre(self, cell: GridCell) -> tuple[float, float]:
        min_x, min_y, max_x, max_y = self.cell_bounds(cell)
        return (min_x + max_x) / 2, (min_y + max_y) / 2
