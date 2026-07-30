from __future__ import annotations

import json
import sys
from pathlib import Path

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"
GB_CONFIG_PATH = GENERATOR_ROOT / "config" / "GB.provisional.yaml"

sys.path.insert(0, str(SRC_DIR))

from verify_island_policy import main  # noqa: E402


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


def write_dataset(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    feature("Foula", "island", "a16499183"),
                    feature("Fair Isle", "island", "a6134821"),
                    feature("Rockall", "islet", "a2679925368"),
                ],
            }
        ),
        encoding="utf-8",
    )


def test_main_reports_complete_success(
    tmp_path: Path,
    capsys,
) -> None:
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
    assert "island policy verification succeeded" in captured.out
    assert "Island/islet polygons checked: 3" in captured.out
    assert "Configured exception matches: 1" in captured.out
    assert "Required island outcomes verified: 3" in captured.out
    assert captured.err == ""


def test_main_reports_failure_for_missing_dataset(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = main(
        [
            str(GB_CONFIG_PATH),
            str(tmp_path / "missing.geojson"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Island policy verification error:" in captured.err
