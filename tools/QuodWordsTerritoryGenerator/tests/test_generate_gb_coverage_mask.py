"""Tests for the progress-reporting GB coverage-mask command."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, shape

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT / "src"))

from generate_gb_coverage_mask import main  # noqa: E402


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
            "coordinates": square(-1.0, 50.0, -0.99, 50.01),
        },
    }


def write_land_dataset(path: Path) -> None:
    path.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [
                feature("foula", "Foula"),
                feature("rockall", "Rockall", place="islet"),
            ],
        }),
        encoding="utf-8",
    )



def write_foreign_land_dataset(path: Path) -> None:
    path.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "foreign-land",
                    "properties": {
                        "name": "Foreign Land",
                    },
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": square(
                            -0.985,
                            50.0,
                            -0.975,
                            50.01,
                        ),
                    },
                },
            ],
        }),
        encoding="utf-8",
    )



def test_main_generates_coverage_mask(
    tmp_path: Path,
    capsys,
) -> None:
    land_path = tmp_path / "land.geojson"
    output_path = tmp_path / "coverage.geojson"
    write_land_dataset(land_path)

    exit_code = main([
        str(GENERATOR_ROOT / "config" / "GB.provisional.yaml"),
        str(land_path),
        str(output_path),
    ])

    captured = capsys.readouterr()
    result = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "Loading territory configuration." in captured.out
    assert "Loaded 2 land features." in captured.out
    assert "Generating configured marine buffer in bounded batches." in captured.out
    assert "coverage-mask generation succeeded" in captured.out
    assert "Buffer-generating land features: 1" in captured.out
    assert "Excluded from independent buffering: Rockall" in captured.out
    assert captured.err == ""
    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1
    assert result["features"][0]["geometry"]["type"] == "MultiPolygon"



def test_main_removes_supplied_foreign_land(
    tmp_path: Path,
    capsys,
) -> None:
    land_path = tmp_path / "land.geojson"
    foreign_path = tmp_path / "foreign.geojson"
    output_path = tmp_path / "coverage.geojson"

    write_land_dataset(land_path)
    write_foreign_land_dataset(foreign_path)

    exit_code = main([
        str(GENERATOR_ROOT / "config" / "GB.provisional.yaml"),
        str(land_path),
        str(output_path),
        "--foreign-land-dataset",
        str(foreign_path),
    ])

    captured = capsys.readouterr()
    result = json.loads(output_path.read_text(encoding="utf-8"))
    geometry = shape(result["features"][0]["geometry"])

    transformer = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:3035",
        always_xy=True,
    )
    foreign_x, foreign_y = transformer.transform(
        -0.98,
        50.005,
    )

    assert exit_code == 0
    assert "Loading foreign-land dataset." in captured.out
    assert "Loaded 1 foreign-land features." in captured.out
    assert captured.err == ""
    assert not geometry.contains(Point(foreign_x, foreign_y))



def test_main_reports_missing_land_dataset(
    tmp_path: Path,
    capsys,
) -> None:
    output_path = tmp_path / "coverage.geojson"

    exit_code = main([
        str(GENERATOR_ROOT / "config" / "GB.provisional.yaml"),
        str(tmp_path / "missing.geojson"),
        str(output_path),
    ])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Loading territory configuration." in captured.out
    assert "Loading validated GB land dataset." in captured.out
    assert "coverage-mask generation error:" in captured.err
    assert "GB land dataset not found" in captured.err
    assert not output_path.exists()


def test_main_reports_invalid_land_geojson(
    tmp_path: Path,
    capsys,
) -> None:
    land_path = tmp_path / "invalid.geojson"
    output_path = tmp_path / "coverage.geojson"
    land_path.write_text("{invalid", encoding="utf-8")

    exit_code = main([
        str(GENERATOR_ROOT / "config" / "GB.provisional.yaml"),
        str(land_path),
        str(output_path),
    ])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Invalid GeoJSON" in captured.err
    assert not output_path.exists()
