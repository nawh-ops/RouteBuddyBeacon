"""Build the frozen neighbouring-territory dataset for GB coverage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


class ForeignLandBuildError(ValueError):
    """Raised when the GB foreign-land dataset cannot be built."""


TERRITORIES = {
    "FR": "France métropolitaine",
    "GG": "Guernsey",
    "JE": "Jersey",
    "IE": "Ireland",
    "IM": "Isle of Man",
}

OUTPUT_ORDER = ("FR", "GG", "JE", "IE", "IM")


def _load_geojson(path: Path) -> Mapping[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ForeignLandBuildError(
            f"Boundary dataset not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ForeignLandBuildError(
            f"Invalid GeoJSON in {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise ForeignLandBuildError(
            f"Unable to read {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ForeignLandBuildError(
            f"Boundary dataset must contain a GeoJSON object: {path}"
        )

    if data.get("type") != "FeatureCollection":
        raise ForeignLandBuildError(
            f"Boundary dataset must be a FeatureCollection: {path}"
        )

    features = data.get("features")
    if not isinstance(features, list):
        raise ForeignLandBuildError(
            f"Boundary dataset must contain a features list: {path}"
        )

    return data


def _territory_code(properties: Mapping[str, Any]) -> str | None:
    code = (
        properties.get("territoryCode")
        or properties.get("ISO3166-1")
        or properties.get("ISO3166-1:alpha2")
    )

    if isinstance(code, str):
        return code

    name = properties.get("name")
    name_fallbacks = {
        "France métropolitaine": "FR",
        "Guernsey": "GG",
        "Jersey": "JE",
        "Ireland": "IE",
        "Éire / Ireland": "IE",
        "Isle of Man": "IM",
    }

    if isinstance(name, str):
        return name_fallbacks.get(name)

    return None


def _select_boundaries(
    datasets: list[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}

    for dataset in datasets:
        for index, feature in enumerate(dataset["features"]):
            if not isinstance(feature, dict):
                raise ForeignLandBuildError(
                    f"Boundary feature {index} must be an object."
                )

            properties = feature.get("properties")
            geometry = feature.get("geometry")

            if not isinstance(properties, dict):
                continue

            if not isinstance(geometry, dict):
                continue

            code = _territory_code(properties)
            if code not in TERRITORIES:
                continue

            geometry_type = geometry.get("type")
            if geometry_type not in {"Polygon", "MultiPolygon"}:
                continue

            admin_level = properties.get("admin_level")
            if admin_level not in {None, "2", 2, "3", 3}:
                continue

            if code in selected:
                raise ForeignLandBuildError(
                    f"Duplicate national polygon found for {code}."
                )

            selected[code] = {
                "type": "Feature",
                "properties": {
                    "name": TERRITORIES[code],
                    "territoryCode": code,
                    "source": "OpenStreetMap",
                    "licence": "ODbL-1.0",
                },
                "geometry": geometry,
            }

    missing = set(TERRITORIES) - set(selected)
    if missing:
        raise ForeignLandBuildError(
            "Missing required national polygons: "
            + ", ".join(sorted(missing))
        )

    return selected


def build_foreign_land(
    input_paths: list[Path],
) -> dict[str, Any]:
    datasets = [_load_geojson(path) for path in input_paths]
    selected = _select_boundaries(datasets)

    return {
        "type": "FeatureCollection",
        "features": [
            selected[code]
            for code in OUTPUT_ORDER
        ],
    }


def _write_geojson(
    path: Path,
    dataset: Mapping[str, Any],
) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                dataset,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
    except OSError as exc:
        raise ForeignLandBuildError(
            f"Unable to write {path}: {exc}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the five-territory foreign-land dataset used "
            "when generating the QuodWords GB coverage mask."
        )
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Boundary GeoJSON input files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output GeoJSON path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        dataset = build_foreign_land(args.inputs)
        _write_geojson(args.output, dataset)
    except ForeignLandBuildError as exc:
        print(
            f"GB foreign-land build error: {exc}",
            file=sys.stderr,
        )
        return 1

    print("QuodWords GB foreign-land dataset created.")
    print(f"Feature count: {len(dataset['features'])}")

    for feature in dataset["features"]:
        properties = feature["properties"]
        print(
            f"{properties['territoryCode']}: "
            f"{properties['name']} "
            f"({feature['geometry']['type']})"
        )

    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
