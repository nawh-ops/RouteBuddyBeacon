from __future__ import annotations

import sys
from pathlib import Path

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from shapely.geometry import Polygon

from coverage_row_spans import generate_coverage_row_spans
from grid_math import GridDefinition
from row_spans import RowSpan


def test_generates_one_span_for_single_covered_row() -> None:
    grid = GridDefinition(
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
    )

    geometry = Polygon(
        [
            (0, 0),
            (96, 0),
            (96, 32),
            (0, 32),
            (0, 0),
        ]
    )

    assert generate_coverage_row_spans(geometry, grid) == (
        RowSpan(row=0, start_column=0, end_column=2),
    )


def test_separate_covered_sections_become_separate_spans() -> None:
    grid = GridDefinition(
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
    )

    geometry = Polygon(
        [
            (0, 0),
            (32, 0),
            (32, 32),
            (64, 32),
            (64, 0),
            (96, 0),
            (96, 64),
            (0, 64),
            (0, 0),
        ]
    )

    assert generate_coverage_row_spans(geometry, grid) == (
        RowSpan(row=0, start_column=0, end_column=0),
        RowSpan(row=0, start_column=2, end_column=2),
        RowSpan(row=1, start_column=0, end_column=2),
    )


def test_centre_on_geometry_boundary_counts_as_covered() -> None:
    grid = GridDefinition(
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
    )

    geometry = Polygon(
        [
            (16, 0),
            (48, 0),
            (48, 32),
            (16, 32),
            (16, 0),
        ]
    )

    assert generate_coverage_row_spans(geometry, grid) == (
        RowSpan(row=0, start_column=0, end_column=1),
    )


def test_geometry_outside_positive_grid_coordinates_is_supported() -> None:
    grid = GridDefinition(
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
    )

    geometry = Polygon(
        [
            (-64, -64),
            (0, -64),
            (0, 0),
            (-64, 0),
            (-64, -64),
        ]
    )

    assert generate_coverage_row_spans(geometry, grid) == (
        RowSpan(row=-2, start_column=-2, end_column=-1),
        RowSpan(row=-1, start_column=-2, end_column=-1),
    )
