"""Tests for the repeatable GB land-dataset validation command."""

from __future__ import annotations

import json
import sys
from pathlib import Path

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT / "src"))

from validate_gb_land import main  # noqa: E402


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
            "coordinates": square(0, 0, 1, 1),
        },
    }


def write_valid_dataset(path: Path) -> None:
    path.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [
                feature("foula", "Foula"),
                feature("fair-isle", "Fair Isle"),
                feature("rockall", "Rockall", place="islet"),
            ],
        }),
        encoding="utf-8",
    )


def test_main_reports_success(
    tmp_path: Path,
    capsys,
) -> None:
    dataset_path = tmp_path / "gb-land.geojson"
    write_valid_dataset(dataset_path)

    exit_code = main([str(dataset_path)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "validation succeeded" in captured.out
    assert "Land features: 3" in captured.out
    assert "Required features verified: 3" in captured.out
    assert captured.err == ""


def test_main_reports_missing_dataset(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = main([
        str(tmp_path / "missing.geojson"),
    ])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "GB land dataset validation error:" in captured.err
    assert "dataset not found" in captured.err


def test_main_reports_invalid_geojson(
    tmp_path: Path,
    capsys,
) -> None:
    dataset_path = tmp_path / "invalid.geojson"
    dataset_path.write_text("{invalid", encoding="utf-8")

    exit_code = main([str(dataset_path)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Invalid GeoJSON" in captured.err


def test_main_reports_invalid_dataset(
    tmp_path: Path,
    capsys,
) -> None:
    dataset_path = tmp_path / "empty.geojson"
    dataset_path.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [],
        }),
        encoding="utf-8",
    )

    exit_code = main([str(dataset_path)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "must contain at least one feature" in captured.err
