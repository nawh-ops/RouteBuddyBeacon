"""Validate key real-world points against a generated GB coverage mask."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry


class CoverageGeographyValidationError(ValueError):
    """Raised when the generated GB coverage mask fails geographic checks."""


CHECKS = (
    # Principal GB and Northern Ireland land.
    ("London", -0.1276, 51.5072, True),
    ("Edinburgh", -3.1883, 55.9533, True),
    ("Cardiff", -3.1791, 51.4816, True),
    ("Belfast", -5.9301, 54.5973, True),

    # Representative permanent islands.
    ("Lerwick, Shetland", -1.1494, 60.1550, True),
    ("Kirkwall, Orkney", -2.9590, 58.9847, True),
    ("Stornoway, Lewis", -6.2603, 58.2093, True),
    ("Hugh Town, Isles of Scilly", -6.3170, 49.9140, True),
    ("Foula", -2.0530, 60.1370, True),
    ("Fair Isle", -1.6290, 59.5360, True),

    # Retained marine coverage.
    ("English Channel sea", -0.5000, 50.4000, True),
    ("Irish Sea near Anglesey", -4.4000, 53.3500, True),
    ("North Sea east of Aberdeen", -1.5000, 57.1000, True),
    ("The Minch", -6.0000, 57.8000, True),

    # Northern Ireland and Ireland separation.
    ("Newry, Northern Ireland", -6.3370, 54.1750, True),
    ("Dundalk, Ireland", -6.4050, 54.0000, False),
    ("Letterkenny, Ireland", -7.7340, 54.9550, False),
    ("Dublin, Ireland", -6.2603, 53.3498, False),

    # Other neighbouring territories.
    ("Douglas, Isle of Man", -4.4817, 54.1523, False),
    ("St Helier, Jersey", -2.1312, 49.1868, False),
    ("St Peter Port, Guernsey", -2.5369, 49.4550, False),
    ("Calais, France", 1.8587, 50.9513, False),
    ("Cherbourg, France", -1.6220, 49.6330, False),

    # Clearly beyond the intended marine reach.
    ("Atlantic west of Ireland", -15.0000, 55.0000, False),
    ("Bay of Biscay", -5.0000, 47.0000, False),
)


def load_mask(path: Path) -> BaseGeometry:
    try:
        dataset: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CoverageGeographyValidationError(
            f"Coverage mask not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise CoverageGeographyValidationError(
            f"Invalid GeoJSON in {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise CoverageGeographyValidationError(
            f"Unable to read {path}: {exc}"
        ) from exc

    if not isinstance(dataset, dict):
        raise CoverageGeographyValidationError(
            "Coverage mask must contain a GeoJSON object."
        )

    features = dataset.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise CoverageGeographyValidationError(
            "Coverage mask must contain exactly one feature."
        )

    feature = features[0]
    if not isinstance(feature, dict):
        raise CoverageGeographyValidationError(
            "Coverage-mask feature must be an object."
        )

    geometry_data = feature.get("geometry")
    if not isinstance(geometry_data, dict):
        raise CoverageGeographyValidationError(
            "Coverage-mask feature must contain geometry."
        )

    try:
        geometry = shape(geometry_data)
    except (TypeError, ValueError) as exc:
        raise CoverageGeographyValidationError(
            f"Invalid coverage-mask geometry: {exc}"
        ) from exc

    if geometry.is_empty:
        raise CoverageGeographyValidationError(
            "Coverage-mask geometry must not be empty."
        )

    if not geometry.is_valid:
        raise CoverageGeographyValidationError(
            "Coverage-mask geometry must be valid."
        )

    return geometry


def validate_geography(geometry: BaseGeometry) -> list[str]:
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:3035",
        always_xy=True,
    )

    results: list[str] = []
    failures: list[str] = []

    for name, longitude, latitude, expected_covered in CHECKS:
        x, y = transformer.transform(longitude, latitude)
        covered = geometry.covers(Point(x, y))

        results.append(
            f"{name}: covered={covered}; expected={expected_covered}"
        )

        if covered != expected_covered:
            failures.append(
                f"{name} expected covered={expected_covered}, "
                f"but received covered={covered}."
            )

    if failures:
        raise CoverageGeographyValidationError(" ".join(failures))

    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate key real-world points against the generated "
            "QuodWords GB coverage mask."
        )
    )
    parser.add_argument("coverage_mask", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        geometry = load_mask(args.coverage_mask)
        results = validate_geography(geometry)
    except CoverageGeographyValidationError as exc:
        print(
            f"GB coverage geographic validation error: {exc}",
            file=sys.stderr,
        )
        return 1

    print("QuodWords GB geographic validation succeeded.")
    print(f"Geometry type: {geometry.geom_type}")

    for result in results:
        print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
