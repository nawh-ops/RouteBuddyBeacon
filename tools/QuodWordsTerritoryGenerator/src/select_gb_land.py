"""Generate GB permanent-land candidates from audited GeoJSON inputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from gb_land_selector import GBLandSelectionError, select_gb_land_features


class GBLandCommandError(ValueError):
    """Raised when a GB land-selection command cannot be completed."""


def _load_geojson(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise GBLandCommandError(f"{label} not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GBLandCommandError(
            f"Invalid GeoJSON in {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise GBLandCommandError(
            f"Unable to read {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise GBLandCommandError(
            f"{label} must contain a GeoJSON object."
        )

    return data


def _write_geojson(path: Path, dataset: dict[str, Any]) -> None:
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
        raise GBLandCommandError(
            f"Unable to write {path}: {exc}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Clip audited island and islet polygons to the "
            "GB jurisdiction boundary."
        )
    )
    parser.add_argument(
        "boundary",
        type=Path,
        help="GeoJSON FeatureCollection containing one GB boundary feature.",
    )
    parser.add_argument(
        "candidates",
        type=Path,
        help="Audited island-candidate GeoJSON FeatureCollection.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Destination for the selected GB land GeoJSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        boundary = _load_geojson(
            args.boundary,
            label="GB boundary dataset",
        )
        candidates = _load_geojson(
            args.candidates,
            label="Land candidate dataset",
        )
        selected = select_gb_land_features(
            boundary,
            candidates,
        )
        _write_geojson(args.output, selected)
    except (GBLandCommandError, GBLandSelectionError) as exc:
        print(f"GB land selection error: {exc}", file=sys.stderr)
        return 1

    print("QuodWords GB land selection succeeded.")
    print(f"Selected land features: {len(selected['features'])}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
