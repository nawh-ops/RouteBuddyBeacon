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
    ("Letterkenny", -7.734, 54.955, False),
    ("Calais", 1.8587, 50.9513, False),
    ("English Channel sea", -0.50, 50.40, True),
    ("Irish Sea near Anglesey", -4.40, 53.35, True),
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
