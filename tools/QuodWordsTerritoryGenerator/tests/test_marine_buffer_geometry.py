"""Tests for projected marine-buffer geometry generation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pyproj import Transformer
from shapely.geometry import Point, shape

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT / "src"))

from marine_buffer_geometry import (  # noqa: E402
    MarineBufferGeometryError,
    _batched_buffer_union,
    _batched_union,
    generate_marine_buffer_geometry,
)


def square(
    minimum_x: float,
    minimum_y: float,
    maximum_x: float,
    maximum_y: float,
) -> list:
    return [[[
        [minimum_x, minimum_y],
        [maximum_x, minimum_y],
        [maximum_x, maximum_y],
        [minimum_x, maximum_y],
        [minimum_x, minimum_y],
    ]]]


def feature(
    feature_id: str,
    name: str,
    coordinates: list,
) -> dict:
    return {
        "type": "Feature",
        "id": feature_id,
        "properties": {
            "name": name,
            "place": "island",
        },
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": coordinates,
        },
    }


def dataset(features: list[dict]) -> dict:
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def test_generates_projected_polygonal_buffer() -> None:
    result = generate_marine_buffer_geometry(
        dataset([
            feature(
                "land",
                "Test Island",
                square(-1.0, 50.0, -0.99, 50.01),
            )
        ]),
        buffer_distance_metres=46_300,
        projection="EPSG:3035",
    )

    geometry = shape(result["geometry"])

    assert result["geometry"]["type"] == "MultiPolygon"
    assert geometry.is_valid
    assert not geometry.is_empty
    assert result["properties"]["projection"] == "EPSG:3035"
    assert result["properties"]["bufferDistanceMetres"] == 46_300
    assert result["properties"]["eligibleLandFeatureCount"] == 1


def test_multiple_land_features_are_unioned() -> None:
    result = generate_marine_buffer_geometry(
        dataset([
            feature(
                "one",
                "Island One",
                square(-1.0, 50.0, -0.99, 50.01),
            ),
            feature(
                "two",
                "Island Two",
                square(-0.98, 50.0, -0.97, 50.01),
            ),
        ]),
        buffer_distance_metres=46_300,
        projection="EPSG:3035",
    )

    assert result["properties"]["eligibleLandFeatureCount"] == 2
    assert not shape(result["geometry"]).is_empty


def test_configured_exception_is_excluded() -> None:
    result = generate_marine_buffer_geometry(
        dataset([
            feature(
                "foula",
                "Foula",
                square(-1.0, 50.0, -0.99, 50.01),
            ),
            feature(
                "rockall",
                "Rockall",
                square(-10.0, 57.0, -9.999, 57.001),
            ),
        ]),
        buffer_distance_metres=46_300,
        projection="EPSG:3035",
        non_buffer_generating_names=("Rockall",),
    )

    assert result["properties"]["eligibleLandFeatureCount"] == 1
    assert result["properties"]["excludedFeatureNames"] == ["Rockall"]


def test_all_features_excluded_is_rejected() -> None:
    with pytest.raises(
        MarineBufferGeometryError,
        match="No buffer-generating land features remain",
    ):
        generate_marine_buffer_geometry(
            dataset([
                feature(
                    "rockall",
                    "Rockall",
                    square(-10.0, 57.0, -9.999, 57.001),
                )
            ]),
            buffer_distance_metres=46_300,
            projection="EPSG:3035",
            non_buffer_generating_names=("Rockall",),
        )


def test_non_positive_buffer_distance_is_rejected() -> None:
    with pytest.raises(
        MarineBufferGeometryError,
        match="greater than zero",
    ):
        generate_marine_buffer_geometry(
            dataset([]),
            buffer_distance_metres=0,
            projection="EPSG:3035",
        )


def test_invalid_land_geometry_is_rejected() -> None:
    invalid = feature(
        "invalid",
        "Invalid Island",
        [[[
            [0, 0],
            [1, 1],
            [0, 1],
            [1, 0],
            [0, 0],
        ]]],
    )

    with pytest.raises(
        MarineBufferGeometryError,
        match="geometry must be valid",
    ):
        generate_marine_buffer_geometry(
            dataset([invalid]),
            buffer_distance_metres=46_300,
            projection="EPSG:3035",
        )


def test_exception_land_is_retained_but_does_not_generate_buffer() -> None:
    result = generate_marine_buffer_geometry(
        dataset([
            feature(
                "foula",
                "Foula",
                square(-1.0, 50.0, -0.99, 50.01),
            ),
            feature(
                "rockall",
                "Rockall",
                square(-10.0, 57.0, -9.999, 57.001),
            ),
        ]),
        buffer_distance_metres=46_300,
        projection="EPSG:3035",
        non_buffer_generating_names=("Rockall",),
    )

    geometry = shape(result["geometry"])
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:3035",
        always_xy=True,
    )

    rockall_x, rockall_y = transformer.transform(
        -9.9995,
        57.0005,
    )
    nearby_x, nearby_y = transformer.transform(
        -9.8,
        57.0005,
    )

    assert geometry.contains(Point(rockall_x, rockall_y))
    assert not geometry.contains(Point(nearby_x, nearby_y))


def test_batched_union_combines_multiple_geometries() -> None:
    geometries = [
        shape({
            "type": "MultiPolygon",
            "coordinates": square(
                float(index),
                0.0,
                float(index) + 0.75,
                0.75,
            ),
        })
        for index in range(20)
    ]

    result = _batched_union(
        geometries,
        batch_size=4,
    )

    assert result.is_valid
    assert not result.is_empty
    assert result.area == pytest.approx(
        sum(geometry.area for geometry in geometries)
    )


def test_batched_union_rejects_invalid_batch_size() -> None:
    with pytest.raises(
        MarineBufferGeometryError,
        match="at least two",
    ):
        _batched_union(
            [shape({
                "type": "MultiPolygon",
                "coordinates": square(0, 0, 1, 1),
            })],
            batch_size=1,
        )


def test_batched_buffer_union_matches_complete_buffer() -> None:
    geometries = [
        shape({
            "type": "MultiPolygon",
            "coordinates": square(
                float(index) * 2.0,
                0.0,
                float(index) * 2.0 + 1.0,
                1.0,
            ),
        })
        for index in range(12)
    ]

    result = _batched_buffer_union(
        geometries,
        buffer_distance_metres=0.5,
        batch_size=3,
    )
    expected = _batched_union(
        geometries,
        batch_size=3,
    ).buffer(0.5)

    assert result.is_valid
    assert result.symmetric_difference(expected).area == pytest.approx(
        0.0,
        abs=1e-9,
    )
