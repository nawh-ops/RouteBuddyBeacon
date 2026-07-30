"""Tests for clipping permanent-land candidates to the GB boundary."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT / "src"))

from gb_land_selector import (  # noqa: E402
    GBLandSelectionError,
    select_gb_land_features,
)


def feature(
    feature_id: str,
    *,
    place: str,
    coordinates: list,
    name: str | None = None,
) -> dict[str, object]:
    return {
        "type": "Feature",
        "id": feature_id,
        "properties": {
            "name": name,
            "place": place,
        },
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": coordinates,
        },
    }


def feature_collection(
    features: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": features,
    }


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


def boundary_dataset() -> dict[str, object]:
    return feature_collection([
        {
            "type": "Feature",
            "properties": {
                "name": "Test GB",
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": square(0, 0, 10, 10),
            },
        }
    ])


def test_fully_inside_island_is_selected() -> None:
    candidates = feature_collection([
        feature(
            "inside",
            place="island",
            name="Inside Island",
            coordinates=square(2, 2, 4, 4),
        )
    ])

    result = select_gb_land_features(
        boundary_dataset(),
        candidates,
    )

    assert len(result["features"]) == 1
    selected = result["features"][0]
    assert selected["id"] == "inside"
    assert selected["properties"]["name"] == "Inside Island"
    assert selected["geometry"]["type"] == "MultiPolygon"


def test_cross_boundary_island_is_clipped() -> None:
    candidates = feature_collection([
        feature(
            "crossing",
            place="island",
            name="Crossing Island",
            coordinates=square(8, 2, 12, 6),
        )
    ])

    result = select_gb_land_features(
        boundary_dataset(),
        candidates,
    )

    selected = result["features"][0]
    ring = selected["geometry"]["coordinates"][0][0]

    assert min(point[0] for point in ring) == 8
    assert max(point[0] for point in ring) == 10
    assert min(point[1] for point in ring) == 2
    assert max(point[1] for point in ring) == 6


def test_outside_island_is_excluded() -> None:
    candidates = feature_collection([
        feature(
            "outside",
            place="island",
            coordinates=square(20, 20, 22, 22),
        )
    ])

    result = select_gb_land_features(
        boundary_dataset(),
        candidates,
    )

    assert result["features"] == []


def test_non_island_place_is_excluded() -> None:
    candidates = feature_collection([
        feature(
            "lake",
            place="lake",
            coordinates=square(2, 2, 4, 4),
        )
    ])

    result = select_gb_land_features(
        boundary_dataset(),
        candidates,
    )

    assert result["features"] == []


def test_boundary_requires_exactly_one_feature() -> None:
    with pytest.raises(
        GBLandSelectionError,
        match="exactly one feature",
    ):
        select_gb_land_features(
            feature_collection([]),
            feature_collection([]),
        )


def test_invalid_candidate_geometry_is_rejected() -> None:
    candidates = feature_collection([
        feature(
            "invalid",
            place="island",
            coordinates=[[[
                [0, 0],
                [4, 4],
                [0, 4],
                [4, 0],
                [0, 0],
            ]]],
        )
    ])

    with pytest.raises(
        GBLandSelectionError,
        match="geometry must be valid",
    ):
        select_gb_land_features(
            boundary_dataset(),
            candidates,
        )
