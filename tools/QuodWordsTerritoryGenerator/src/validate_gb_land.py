"""Validate a generated GB permanent-land candidate dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from gb_land_validator import (
    GBLandValidationError,
    validate_gb_land_dataset,
)


class GBLandValidationCommandError(ValueError):
    """Raised when the GB land-validation command cannot be completed."""


def _load_geojson(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GBLandValidationCommandError(
            f"GB land dataset not found: {path}"
        )

    try:
        dataset = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GBLandValidationCommandError(
            f"Invalid GeoJSON in {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise GBLandValidationCommandError(
            f"Unable to read {path}: {exc}"
        ) from exc

    if not isinstance(dataset, dict):
        raise GBLandValidationCommandError(
            "GB land dataset must contain a GeoJSON object."
        )

    return dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the generated GB permanent-land "
            "candidate GeoJSON dataset."
        )
    )
    parser.add_argument(
        "dataset",
        type=Path,
        help="Generated GB land-candidate GeoJSON file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        dataset = _load_geojson(args.dataset)
        summary = validate_gb_land_dataset(dataset)
    except (
        GBLandValidationCommandError,
        GBLandValidationError,
    ) as exc:
        print(
            f"GB land dataset validation error: {exc}",
            file=sys.stderr,
        )
        return 1

    print("QuodWords GB land dataset validation succeeded.")
    print(f"Land features: {summary.feature_count}")
    print(
        "Required features verified: "
        f"{summary.required_feature_count}"
    )
    print(f"Dataset: {args.dataset}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
