"""Tests for validating generated GB permanent-land candidates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT / "src"))

from gb_land_validator import (  # noqa: E402
    GBLandValidationError,
    validate_gb_land_dataset,
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
    *,
    place: str = "island",
    coordinates: list | None = None,
) -> dict:
    return {
        "type": "Feature",
        "id": feature_id,
        "properties": {
            "name": name,
            "place": place,
        },
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": coordinates or square(0, 0, 1, 1),
        },
    }


def valid_dataset() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            feature("foula", "Foula"),
            feature("fair-isle", "Fair Isle"),
            feature("rockall", "Rockall", place="islet"),
        ],
    }


def test_valid_dataset_returns_summary() -> None:
    summary = validate_gb_land_dataset(valid_dataset())

    assert summary.feature_count == 3
    assert summary.required_feature_count == 3


def test_empty_dataset_is_rejected() -> None:
    with pytest.raises(
        GBLandValidationError,
        match="at least one feature",
    ):
        validate_gb_land_dataset({
            "type": "FeatureCollection",
            "features": [],
        })


def test_duplicate_feature_id_is_rejected() -> None:
    dataset = valid_dataset()
    dataset["features"][1]["id"] = "foula"

    with pytest.raises(
        GBLandValidationError,
        match="Duplicate GB land feature ID",
    ):
        validate_gb_land_dataset(dataset)


def test_missing_required_feature_is_rejected() -> None:
    dataset = valid_dataset()
    dataset["features"] = [
        feature_item
        for feature_item in dataset["features"]
        if feature_item["properties"]["name"] != "Fair Isle"
    ]

    with pytest.raises(
        GBLandValidationError,
        match="'Fair Isle'.*found 0",
    ):
        validate_gb_land_dataset(dataset)


def test_duplicate_required_feature_is_rejected() -> None:
    dataset = valid_dataset()
    dataset["features"].append(
        feature("second-rockall", "Rockall", place="islet")
    )

    with pytest.raises(
        GBLandValidationError,
        match="'Rockall'.*found 2",
    ):
        validate_gb_land_dataset(dataset)


def test_non_island_place_is_rejected() -> None:
    dataset = valid_dataset()
    dataset["features"][0]["properties"]["place"] = "lake"

    with pytest.raises(
        GBLandValidationError,
        match="must be an island or islet",
    ):
        validate_gb_land_dataset(dataset)


def test_invalid_geometry_is_rejected() -> None:
    dataset = valid_dataset()
    dataset["features"][0]["geometry"]["coordinates"] = [[[
        [0, 0],
        [1, 1],
        [0, 1],
        [1, 0],
        [0, 0],
    ]]]

    with pytest.raises(
        GBLandValidationError,
        match="geometry must be valid",
    ):
        validate_gb_land_dataset(dataset)
