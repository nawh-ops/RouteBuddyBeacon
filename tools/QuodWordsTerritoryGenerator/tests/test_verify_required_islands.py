from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"
GB_CONFIG_PATH = GENERATOR_ROOT / "config" / "GB.provisional.yaml"

sys.path.insert(0, str(SRC_DIR))

from verify_required_islands import (  # noqa: E402
    RequiredIslandVerificationError,
    main,
    verify_required_islands,
)


def feature(
    name: str,
    place: str,
    feature_id: str,
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
            "coordinates": [],
        },
    }


def write_dataset(
    path: Path,
    *,
    include_fair_isle: bool = True,
) -> None:
    features = [
        feature("Foula", "island", "a16499183"),
        feature("Rockall", "islet", "a2679925368"),
    ]

    if include_fair_isle:
        features.append(
            feature("Fair Isle", "island", "a6134821")
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


def test_required_island_outcomes_match_dataset(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "islands.geojson"
    write_dataset(dataset_path)

    verified = verify_required_islands(
        GB_CONFIG_PATH,
        dataset_path,
    )

    assert verified == (
        ("Foula", "island", "a16499183", True),
        ("Fair Isle", "island", "a6134821", True),
        ("Rockall", "islet", "a2679925368", False),
    )


def test_missing_required_island_is_rejected(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "islands.geojson"
    write_dataset(dataset_path, include_fair_isle=False)

    with pytest.raises(
        RequiredIslandVerificationError,
        match="Fair Isle.*found 0",
    ):
        verify_required_islands(
            GB_CONFIG_PATH,
            dataset_path,
        )


def test_duplicate_required_island_is_rejected(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "islands.geojson"
    write_dataset(dataset_path)

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    data["features"].append(
        feature("Foula", "island", "duplicate-foula")
    )
    dataset_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(
        RequiredIslandVerificationError,
        match="Foula.*found 2",
    ):
        verify_required_islands(
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
    assert "Foula" in captured.out
    assert "Fair Isle" in captured.out
    assert "Rockall" in captured.out
    assert "does not generate buffer" in captured.out
    assert captured.err == ""
