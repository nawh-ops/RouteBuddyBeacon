from __future__ import annotations

import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from grid_math import GridCell  # noqa: E402
from row_spans import RowSpan  # noqa: E402
from territory_resource import (  # noqa: E402
    HEADER_SIZE,
    MAGIC,
    SCHEMA_VERSION,
    SPAN_STRUCT,
    TerritoryResourceError,
    read_territory_resource,
    write_territory_resource,
)


def _example_spans() -> tuple[RowSpan, ...]:
    return (
        RowSpan(row=-2, start_column=4, end_column=6),
        RowSpan(row=1, start_column=-3, end_column=-1),
        RowSpan(row=1, start_column=5, end_column=7),
    )


def test_round_trip_preserves_metadata_spans_and_index(
    tmp_path: Path,
) -> None:
    resource_path = tmp_path / "GB.qwtr"

    metadata = write_territory_resource(
        resource_path,
        territory_code="GB",
        projection_epsg=3035,
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
        spans=_example_spans(),
        maximum_code_count=100,
    )

    resource = read_territory_resource(resource_path)

    assert metadata == resource.metadata
    assert resource.metadata.territory_code == "GB"
    assert resource.metadata.schema_version == SCHEMA_VERSION
    assert resource.metadata.projection_epsg == 3035
    assert resource.metadata.cell_size_metres == 32
    assert resource.metadata.span_count == 3
    assert resource.metadata.cell_count == 9
    assert resource.metadata.maximum_code_count == 100
    assert resource.spans == _example_spans()

    assert (
        resource.territory_index.index_for_cell(
            GridCell(column=4, row=-2)
        )
        == 0
    )
    assert (
        resource.territory_index.index_for_cell(
            GridCell(column=7, row=1)
        )
        == 8
    )
    assert resource.territory_index.cell_for_index(0) == GridCell(
        column=4,
        row=-2,
    )
    assert resource.territory_index.cell_for_index(8) == GridCell(
        column=7,
        row=1,
    )


def test_output_is_deterministic(tmp_path: Path) -> None:
    first_path = tmp_path / "first.qwtr"
    second_path = tmp_path / "second.qwtr"

    arguments = dict(
        territory_code="GB",
        projection_epsg=3035,
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
        spans=_example_spans(),
        maximum_code_count=100,
    )

    write_territory_resource(first_path, **arguments)
    write_territory_resource(second_path, **arguments)

    assert first_path.read_bytes() == second_path.read_bytes()


def test_resource_has_fixed_header_and_span_record_sizes(
    tmp_path: Path,
) -> None:
    resource_path = tmp_path / "GB.qwtr"

    write_territory_resource(
        resource_path,
        territory_code="GB",
        projection_epsg=3035,
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
        spans=_example_spans(),
        maximum_code_count=100,
    )

    assert resource_path.stat().st_size == (
        HEADER_SIZE + 3 * SPAN_STRUCT.size
    )
    assert resource_path.read_bytes().startswith(MAGIC)


def test_invalid_magic_is_rejected(tmp_path: Path) -> None:
    resource_path = tmp_path / "GB.qwtr"

    write_territory_resource(
        resource_path,
        territory_code="GB",
        projection_epsg=3035,
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
        spans=_example_spans(),
        maximum_code_count=100,
    )

    content = bytearray(resource_path.read_bytes())
    content[:8] = b"NOTQWTR!"
    resource_path.write_bytes(content)

    with pytest.raises(
        TerritoryResourceError,
        match="invalid magic identifier",
    ):
        read_territory_resource(resource_path)


def test_truncated_resource_is_rejected(tmp_path: Path) -> None:
    resource_path = tmp_path / "GB.qwtr"

    write_territory_resource(
        resource_path,
        territory_code="GB",
        projection_epsg=3035,
        origin_x=0,
        origin_y=0,
        cell_size_metres=32,
        spans=_example_spans(),
        maximum_code_count=100,
    )

    resource_path.write_bytes(resource_path.read_bytes()[:-1])

    with pytest.raises(
        TerritoryResourceError,
        match="size does not match",
    ):
        read_territory_resource(resource_path)


def test_invalid_territory_code_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(
        TerritoryResourceError,
        match="two uppercase ASCII letters",
    ):
        write_territory_resource(
            tmp_path / "invalid.qwtr",
            territory_code="Gb",
            projection_epsg=3035,
            origin_x=0,
            origin_y=0,
            cell_size_metres=32,
            spans=_example_spans(),
            maximum_code_count=100,
        )


def test_capacity_overflow_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match="exceeds maximum public-code capacity",
    ):
        write_territory_resource(
            tmp_path / "too-small.qwtr",
            territory_code="GB",
            projection_epsg=3035,
            origin_x=0,
            origin_y=0,
            cell_size_metres=32,
            spans=_example_spans(),
            maximum_code_count=8,
        )
