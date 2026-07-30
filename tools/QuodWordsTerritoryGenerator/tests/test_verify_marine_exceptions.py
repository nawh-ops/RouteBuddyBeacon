from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"
GB_CONFIG_PATH = GENERATOR_ROOT / "config" / "GB.provisional.yaml"

sys.path.insert(0, str(SRC_DIR))

from verify_marine_exceptions import (  # noqa: E402
    MarineExceptionVerificationError,
    main,
    verify_marine_exceptions,
)


def write_dataset(
    path: Path,
    *,
    include_rockall: bool = True,
) -> None:
    features = [
        {
            "type": "Feature",
            "id": "a16499183",
            "properties": {
                "name": "Foula",
                "place": "island",
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [],
            },
        }
    ]

    if include_rockall:
        features.append(
            {
                "type": "Feature",
                "id": "a2679925368",
                "properties": {
                    "name": "Rockall",
                    "place": "islet",
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [],
                },
            }
        )

    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
            }
        ),
        encoding="utf-8",
    )


def test_configured_exception_matches_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "islands.geojson"
    write_dataset(dataset_path)

    checked, excluded = verify_marine_exceptions(
        GB_CONFIG_PATH,
        dataset_path,
    )

    assert checked == 2
    assert excluded == (
        ("Rockall", "islet", "a2679925368"),
    )


def test_missing_configured_exception_is_rejected(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "islands.geojson"
    write_dataset(dataset_path, include_rockall=False)

    with pytest.raises(
        MarineExceptionVerificationError,
        match="do not match the dataset",
    ):
        verify_marine_exceptions(
            GB_CONFIG_PATH,
            dataset_path,
        )


def test_main_reports_success(tmp_path: Path, capsys) -> None:
    dataset_path = tmp_path / "islands.geojson"
    write_dataset(dataset_path)

    exit_code = main(
        [
            str(GB_CONFIG_PATH),
            str(dataset_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "verification succeeded" in captured.out
    assert "Non-buffer-generating matches: 1" in captured.out
    assert "feature ID: a2679925368" in captured.out
    assert captured.err == ""


def test_main_reports_missing_dataset(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            str(GB_CONFIG_PATH),
            str(tmp_path / "missing.geojson"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Island dataset not found" in captured.err
