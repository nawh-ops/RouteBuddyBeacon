"""Tests for the deterministic GB foreign-land dataset builder."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT / "src"))

from build_gb_foreign_land import (  # noqa: E402
    ForeignLandBuildError,
    build_foreign_land,
    main,
)


def polygon() -> dict:
    return {
        "type": "MultiPolygon",
        "coordinates": [
            [
                [
                    [0.0, 0.0],
                    [1.0, 0.0],
                    [1.0, 1.0],
                    [0.0, 1.0],
                    [0.0, 0.0],
                ]
            ]
        ],
    }


def feature(
    *,
    name: str,
    code: str | None,
    admin_level: str,
) -> dict:
    properties = {
        "name": name,
        "admin_level": admin_level,
    }

    if code is not None:
        properties["ISO3166-1"] = code

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": polygon(),
    }


def write_dataset(
    path: Path,
    features: list[dict],
) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
            }
        ),
        encoding="utf-8",
    )


def complete_input_paths(tmp_path: Path) -> list[Path]:
    france_path = tmp_path / "france.geojson"
    channel_path = tmp_path / "channel-islands.geojson"
    ireland_path = tmp_path / "ireland-isle-of-man.geojson"

    write_dataset(
        france_path,
        [
            feature(
                name="France métropolitaine",
                code=None,
                admin_level="3",
            )
        ],
    )

    write_dataset(
        channel_path,
        [
            feature(
                name="Guernsey",
                code="GG",
                admin_level="2",
            ),
            feature(
                name="Jersey",
                code="JE",
                admin_level="2",
            ),
        ],
    )

    write_dataset(
        ireland_path,
        [
            feature(
                name="Éire / Ireland",
                code="IE",
                admin_level="2",
            ),
            feature(
                name="Isle of Man",
                code="IM",
                admin_level="2",
            ),
        ],
    )

    return [
        france_path,
        channel_path,
        ireland_path,
    ]


def test_builds_five_territories_in_deterministic_order(
    tmp_path: Path,
) -> None:
    dataset = build_foreign_land(
        complete_input_paths(tmp_path)
    )

    assert dataset["type"] == "FeatureCollection"
    assert [
        item["properties"]["territoryCode"]
        for item in dataset["features"]
    ] == ["FR", "GG", "JE", "IE", "IM"]

    assert [
        item["properties"]["name"]
        for item in dataset["features"]
    ] == [
        "France métropolitaine",
        "Guernsey",
        "Jersey",
        "Ireland",
        "Isle of Man",
    ]

    assert all(
        item["geometry"]["type"] == "MultiPolygon"
        for item in dataset["features"]
    )


def test_missing_required_territory_is_rejected(
    tmp_path: Path,
) -> None:
    paths = complete_input_paths(tmp_path)

    ireland_dataset = json.loads(
        paths[2].read_text(encoding="utf-8")
    )
    ireland_dataset["features"] = [
        item
        for item in ireland_dataset["features"]
        if item["properties"].get("ISO3166-1") != "IM"
    ]
    paths[2].write_text(
        json.dumps(ireland_dataset),
        encoding="utf-8",
    )

    with pytest.raises(
        ForeignLandBuildError,
        match="Missing required national polygons: IM",
    ):
        build_foreign_land(paths)


def test_duplicate_national_polygon_is_rejected(
    tmp_path: Path,
) -> None:
    paths = complete_input_paths(tmp_path)

    duplicate_path = tmp_path / "duplicate.geojson"
    write_dataset(
        duplicate_path,
        [
            feature(
                name="Jersey",
                code="JE",
                admin_level="2",
            )
        ],
    )

    with pytest.raises(
        ForeignLandBuildError,
        match="Duplicate national polygon found for JE",
    ):
        build_foreign_land(paths + [duplicate_path])


def test_main_reports_missing_input_file(
    tmp_path: Path,
    capsys,
) -> None:
    output_path = tmp_path / "foreign.geojson"

    exit_code = main([
        str(tmp_path / "missing.geojson"),
        "--output",
        str(output_path),
    ])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Boundary dataset not found" in captured.err
    assert not output_path.exists()
