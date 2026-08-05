from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from coverage_row_spans import generate_coverage_row_spans
from grid_math import GridDefinition
from territory_resource import write_territory_resource


DEFAULT_INPUT = Path(
    "tools/QuodWordsTerritoryGenerator/release/GB/"
    "gb-coverage-mask.geojson"
)

DEFAULT_OUTPUT = Path(
    "tools/QuodWordsTerritoryGenerator/output/reproducibility/"
    "GB.candidate.qwtr"
)

TERRITORY_CODE = "GB"
PROJECTION_EPSG = 3035
ORIGIN_X = 0.0
ORIGIN_Y = 0.0
CELL_SIZE_METRES = 32
MAXIMUM_CODE_COUNT = 439_400_000


def load_single_geometry(path: Path) -> BaseGeometry:
    try:
        dataset: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Coverage file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Coverage file is not valid JSON: {path}") from error

    if dataset.get("type") != "FeatureCollection":
        raise ValueError("Coverage input must be a GeoJSON FeatureCollection.")

    features = dataset.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise ValueError(
            "Coverage input must contain exactly one GeoJSON feature."
        )

    geometry_data = features[0].get("geometry")
    if not isinstance(geometry_data, dict):
        raise ValueError("The GeoJSON feature does not contain a geometry.")

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError("Coverage geometry is empty.")

    if not geometry.is_valid:
        raise ValueError("Coverage geometry is invalid.")

    return geometry


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def build_resource(input_path: Path, output_path: Path) -> None:
    geometry = load_single_geometry(input_path)

    grid = GridDefinition(
        origin_x=ORIGIN_X,
        origin_y=ORIGIN_Y,
        cell_size_metres=CELL_SIZE_METRES,
    )

    spans = generate_coverage_row_spans(
        geometry=geometry,
        grid=grid,
    )

    metadata = write_territory_resource(
        output_path,
        territory_code=TERRITORY_CODE,
        projection_epsg=PROJECTION_EPSG,
        origin_x=ORIGIN_X,
        origin_y=ORIGIN_Y,
        cell_size_metres=CELL_SIZE_METRES,
        spans=spans,
        maximum_code_count=MAXIMUM_CODE_COUNT,
    )

    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Territory: {metadata.territory_code}")
    print(f"Projection: EPSG:{metadata.projection_epsg}")
    print(f"Cell size: {metadata.cell_size_metres} metres")
    print(f"Row spans: {metadata.span_count:,}")
    print(f"Included cells: {metadata.cell_count:,}")
    print(f"Maximum code count: {metadata.maximum_code_count:,}")
    print(f"File size: {output_path.stat().st_size:,} bytes")
    print(f"SHA-256: {sha256(output_path)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build a candidate GB QuodWords territory resource from the "
            "frozen release coverage mask."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Coverage GeoJSON path (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Candidate resource path (default: {DEFAULT_OUTPUT})",
    )

    arguments = parser.parse_args()
    build_resource(arguments.input, arguments.output)


if __name__ == "__main__":
    main()
