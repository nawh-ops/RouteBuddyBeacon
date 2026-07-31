"""Generate the provisional GB land-plus-marine coverage mask."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from config_loader import ConfigError, load_config
from marine_buffer_geometry import (
    MarineBufferGeometryError,
    generate_marine_buffer_geometry,
)


class CoverageMaskCommandError(ValueError):
    """Raised when coverage-mask generation cannot be completed."""


def _load_geojson(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CoverageMaskCommandError(
            f"GB land dataset not found: {path}"
        )

    try:
        dataset = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CoverageMaskCommandError(
            f"Invalid GeoJSON in {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise CoverageMaskCommandError(
            f"Unable to read {path}: {exc}"
        ) from exc

    if not isinstance(dataset, dict):
        raise CoverageMaskCommandError(
            "GB land dataset must contain a GeoJSON object."
        )

    return dataset


def _write_geojson(
    path: Path,
    dataset: dict[str, Any],
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
        raise CoverageMaskCommandError(
            f"Unable to write {path}: {exc}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the provisional GB permanent-land "
            "plus configured marine-buffer coverage mask."
        )
    )
    parser.add_argument("config", type=Path)
    parser.add_argument("land_dataset", type=Path)
    parser.add_argument("output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        print("Loading territory configuration.", flush=True)
        config = load_config(args.config)

        print("Loading validated GB land dataset.", flush=True)
        land_dataset = _load_geojson(args.land_dataset)
        feature_count = len(land_dataset.get("features", []))
        print(
            f"Loaded {feature_count} land features.",
            flush=True,
        )

        print("Projecting and combining land geometry.", flush=True)
        feature = generate_marine_buffer_geometry(
            land_dataset,
            buffer_distance_metres=(
                config.marine.buffer_distance_metres
            ),
            projection=config.grid.projection,
            non_buffer_generating_names=(
                config.marine.non_buffer_generating_exceptions
            ),
            progress=lambda message: print(
                message,
                flush=True,
            ),
        )

        print("Writing coverage-mask GeoJSON.", flush=True)
        _write_geojson(
            args.output,
            {
                "type": "FeatureCollection",
                "features": [feature],
            },
        )
    except (
        ConfigError,
        CoverageMaskCommandError,
        MarineBufferGeometryError,
    ) as exc:
        print(
            f"GB coverage-mask generation error: {exc}",
            file=sys.stderr,
        )
        return 1

    properties = feature["properties"]

    print("QuodWords GB coverage-mask generation succeeded.")
    print(f"Input land features: {feature_count}")
    print(
        "Buffer-generating land features: "
        f"{properties['eligibleLandFeatureCount']}"
    )
    print(
        "Excluded from independent buffering: "
        + (
            ", ".join(properties["excludedFeatureNames"])
            or "none"
        )
    )
    print(f"Projection: {properties['projection']}")
    print(
        "Buffer distance: "
        f"{properties['bufferDistanceMetres']} metres"
    )
    print(f"Geometry type: {feature['geometry']['type']}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
