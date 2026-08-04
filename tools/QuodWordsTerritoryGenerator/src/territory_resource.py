from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Iterable

from row_spans import RowSpan, count_cells, validate_spans
from territory_index import TerritoryIndex, verify_capacity


MAGIC = b"QWTRSPAN"
SCHEMA_VERSION = 1
HEADER_SIZE = 64

HEADER_STRUCT = struct.Struct("<8sH2sHIddIQQI6x")
SPAN_STRUCT = struct.Struct("<iii")


class TerritoryResourceError(ValueError):
    """Raised when a territory resource is invalid or incompatible."""


@dataclass(frozen=True)
class TerritoryResourceMetadata:
    territory_code: str
    schema_version: int
    projection_epsg: int
    origin_x: float
    origin_y: float
    cell_size_metres: int
    span_count: int
    cell_count: int
    maximum_code_count: int


@dataclass(frozen=True)
class TerritoryResource:
    metadata: TerritoryResourceMetadata
    spans: tuple[RowSpan, ...]
    territory_index: TerritoryIndex


def _validate_territory_code(territory_code: str) -> bytes:
    if len(territory_code) != 2 or not territory_code.isascii():
        raise TerritoryResourceError(
            "territory_code must contain exactly two ASCII characters."
        )

    encoded = territory_code.encode("ascii")

    if not territory_code.isupper() or not territory_code.isalpha():
        raise TerritoryResourceError(
            "territory_code must contain two uppercase ASCII letters."
        )

    return encoded


def _require_int32(value: int, *, field: str) -> None:
    minimum = -(2**31)
    maximum = 2**31 - 1

    if value < minimum or value > maximum:
        raise TerritoryResourceError(
            f"{field} must fit in a signed 32-bit integer."
        )


def write_territory_resource(
    path: str | Path,
    *,
    territory_code: str,
    projection_epsg: int,
    origin_x: float,
    origin_y: float,
    cell_size_metres: int,
    spans: Iterable[RowSpan],
    maximum_code_count: int,
) -> TerritoryResourceMetadata:
    encoded_territory = _validate_territory_code(territory_code)

    if projection_epsg <= 0:
        raise TerritoryResourceError(
            "projection_epsg must be greater than zero."
        )

    if cell_size_metres <= 0:
        raise TerritoryResourceError(
            "cell_size_metres must be greater than zero."
        )

    if maximum_code_count <= 0:
        raise TerritoryResourceError(
            "maximum_code_count must be greater than zero."
        )

    ordered_spans = validate_spans(spans)
    cell_count = count_cells(ordered_spans)
    verify_capacity(ordered_spans, maximum_code_count)

    for span in ordered_spans:
        _require_int32(span.row, field="row")
        _require_int32(span.start_column, field="start_column")
        _require_int32(span.end_column, field="end_column")

    metadata = TerritoryResourceMetadata(
        territory_code=territory_code,
        schema_version=SCHEMA_VERSION,
        projection_epsg=projection_epsg,
        origin_x=float(origin_x),
        origin_y=float(origin_y),
        cell_size_metres=cell_size_metres,
        span_count=len(ordered_spans),
        cell_count=cell_count,
        maximum_code_count=maximum_code_count,
    )

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wb") as output:
        output.write(
            HEADER_STRUCT.pack(
                MAGIC,
                SCHEMA_VERSION,
                encoded_territory,
                HEADER_SIZE,
                projection_epsg,
                float(origin_x),
                float(origin_y),
                cell_size_metres,
                len(ordered_spans),
                cell_count,
                maximum_code_count,
            )
        )

        for span in ordered_spans:
            output.write(
                SPAN_STRUCT.pack(
                    span.row,
                    span.start_column,
                    span.end_column,
                )
            )

    return metadata


def read_territory_resource(
    path: str | Path,
) -> TerritoryResource:
    resource_path = Path(path)
    content = resource_path.read_bytes()

    if len(content) < HEADER_SIZE:
        raise TerritoryResourceError(
            "Territory resource is smaller than its required header."
        )

    (
        magic,
        schema_version,
        encoded_territory,
        header_size,
        projection_epsg,
        origin_x,
        origin_y,
        cell_size_metres,
        span_count,
        stored_cell_count,
        maximum_code_count,
    ) = HEADER_STRUCT.unpack_from(content, 0)

    if magic != MAGIC:
        raise TerritoryResourceError(
            "Territory resource has an invalid magic identifier."
        )

    if schema_version != SCHEMA_VERSION:
        raise TerritoryResourceError(
            f"Unsupported territory-resource schema version: "
            f"{schema_version}."
        )

    if header_size != HEADER_SIZE:
        raise TerritoryResourceError(
            f"Unsupported territory-resource header size: {header_size}."
        )

    try:
        territory_code = encoded_territory.decode("ascii")
    except UnicodeDecodeError as exc:
        raise TerritoryResourceError(
            "Territory resource contains an invalid territory code."
        ) from exc

    _validate_territory_code(territory_code)

    expected_size = HEADER_SIZE + span_count * SPAN_STRUCT.size

    if len(content) != expected_size:
        raise TerritoryResourceError(
            "Territory resource size does not match its declared "
            "row-span count."
        )

    spans: list[RowSpan] = []

    offset = HEADER_SIZE

    for _ in range(span_count):
        row, start_column, end_column = SPAN_STRUCT.unpack_from(
            content,
            offset,
        )
        offset += SPAN_STRUCT.size

        spans.append(
            RowSpan(
                row=row,
                start_column=start_column,
                end_column=end_column,
            )
        )

    ordered_spans = validate_spans(spans)
    calculated_cell_count = count_cells(ordered_spans)

    if calculated_cell_count != stored_cell_count:
        raise TerritoryResourceError(
            "Territory resource cell count does not match its row spans."
        )

    verify_capacity(ordered_spans, maximum_code_count)

    territory_index = TerritoryIndex.from_spans(
        ordered_spans,
        maximum_code_count,
    )

    metadata = TerritoryResourceMetadata(
        territory_code=territory_code,
        schema_version=schema_version,
        projection_epsg=projection_epsg,
        origin_x=origin_x,
        origin_y=origin_y,
        cell_size_metres=cell_size_metres,
        span_count=span_count,
        cell_count=stored_cell_count,
        maximum_code_count=maximum_code_count,
    )

    return TerritoryResource(
        metadata=metadata,
        spans=ordered_spans,
        territory_index=territory_index,
    )
