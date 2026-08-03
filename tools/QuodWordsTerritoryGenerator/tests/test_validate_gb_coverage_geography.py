"""Tests for the real-world GB coverage geography validator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from pyproj import Transformer
from shapely.geometry import Point, mapping
from shapely.ops import unary_union

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT / "src"))

from validate_gb_coverage_geography import (  # noqa: E402
    CoverageGeographyValidationError,
    load_mask,
    main,
    validate_geography,
)


from validate_gb_coverage_geography import CHECKS  # noqa: E402


def projected_point(longitude: float, latitude: float) -> Point:
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:3035",
        always_xy=True,
    )
    x, y = transformer.transform(longitude, latitude)
    return Point(x, y)


def write_mask(path: Path, geometry) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": mapping(geometry),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def valid_test_geometry():
    return unary_union(
        [
            projected_point(longitude, latitude).buffer(1_000)
            for _, longitude, latitude, expected_covered in CHECKS
            if expected_covered
        ]
    )


def test_valid_real_world_geography_is_accepted(
    tmp_path: Path,
) -> None:
    path = tmp_path / "coverage.geojson"
    write_mask(path, valid_test_geometry())

    geometry = load_mask(path)
    results = validate_geography(geometry)

    assert results == [
        (
            f"{name}: covered={expected_covered}; "
            f"expected={expected_covered}"
        )
        for name, _, _, expected_covered in CHECKS
    ]


def test_incorrect_foreign_land_coverage_is_rejected() -> None:
    geometry = unary_union(
        [
            valid_test_geometry(),
            projected_point(-7.734, 54.955).buffer(1_000),
        ]
    )

    with pytest.raises(
        CoverageGeographyValidationError,
        match="Letterkenny, Ireland expected covered=False",
    ):
        validate_geography(geometry)


def test_main_reports_missing_mask(
    tmp_path: Path,
    capsys,
) -> None:
    missing_path = tmp_path / "missing.geojson"

    exit_code = main([str(missing_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Coverage mask not found" in captured.err
