"""Tests for the repeatable GB land-selection command."""

from __future__ import annotations

import json
import sys
from pathlib import Path

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT / "src"))

from select_gb_land import main  # noqa: E402


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


def write_geojson(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": features,
        }),
        encoding="utf-8",
    )


def boundary_feature() -> dict:
    return {
        "type": "Feature",
        "properties": {"name": "Test GB"},
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": square(0, 0, 10, 10),
        },
    }


def island_feature() -> dict:
    return {
        "type": "Feature",
        "id": "inside",
        "properties": {
            "name": "Inside Island",
            "place": "island",
        },
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": square(2, 2, 4, 4),
        },
    }


def test_main_writes_selected_land_dataset(
    tmp_path: Path,
    capsys,
) -> None:
    boundary_path = tmp_path / "boundary.geojson"
    candidate_path = tmp_path / "candidates.geojson"
    output_path = tmp_path / "selected.geojson"

    write_geojson(boundary_path, [boundary_feature()])
    write_geojson(candidate_path, [island_feature()])

    exit_code = main([
        str(boundary_path),
        str(candidate_path),
        str(output_path),
    ])

    captured = capsys.readouterr()
    result = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "GB land selection succeeded" in captured.out
    assert "Selected land features: 1" in captured.out
    assert captured.err == ""
    assert result["features"][0]["id"] == "inside"


def test_main_reports_missing_boundary(
    tmp_path: Path,
    capsys,
) -> None:
    candidate_path = tmp_path / "candidates.geojson"
    output_path = tmp_path / "selected.geojson"
    write_geojson(candidate_path, [island_feature()])

    exit_code = main([
        str(tmp_path / "missing.geojson"),
        str(candidate_path),
        str(output_path),
    ])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "GB land selection error:" in captured.err
    assert "GB boundary dataset not found" in captured.err
    assert not output_path.exists()


def test_main_reports_invalid_candidate_geojson(
    tmp_path: Path,
    capsys,
) -> None:
    boundary_path = tmp_path / "boundary.geojson"
    candidate_path = tmp_path / "candidates.geojson"
    output_path = tmp_path / "selected.geojson"

    write_geojson(boundary_path, [boundary_feature()])
    candidate_path.write_text("{invalid", encoding="utf-8")

    exit_code = main([
        str(boundary_path),
        str(candidate_path),
        str(output_path),
    ])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Invalid GeoJSON" in captured.err
    assert not output_path.exists()


def test_main_creates_output_directory(
    tmp_path: Path,
    capsys,
) -> None:
    boundary_path = tmp_path / "boundary.geojson"
    candidate_path = tmp_path / "candidates.geojson"
    output_path = tmp_path / "nested" / "selected.geojson"

    write_geojson(boundary_path, [boundary_feature()])
    write_geojson(candidate_path, [island_feature()])

    exit_code = main([
        str(boundary_path),
        str(candidate_path),
        str(output_path),
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output_path.is_file()
