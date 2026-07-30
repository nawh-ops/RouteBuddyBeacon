from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from config_loader import ConfigError, load_config
from marine_buffer_eligibility import generates_marine_buffer_from_config


class MarineExceptionVerificationError(ValueError):
    """Raised when the marine-exception dataset cannot be verified."""


def load_features(path: str | Path) -> list[dict[str, Any]]:
    dataset_path = Path(path)

    if not dataset_path.is_file():
        raise MarineExceptionVerificationError(
            f"Island dataset not found: {dataset_path}"
        )

    try:
        data = json.loads(dataset_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MarineExceptionVerificationError(
            f"Invalid GeoJSON in {dataset_path}: {exc}"
        ) from exc

    features = data.get("features")
    if not isinstance(features, list):
        raise MarineExceptionVerificationError(
            "GeoJSON must contain a features list."
        )

    return features


def verify_marine_exceptions(
    config_path: str | Path,
    dataset_path: str | Path,
) -> tuple[int, tuple[tuple[str, str, str], ...]]:
    config = load_config(config_path)
    features = load_features(dataset_path)

    checked = 0
    excluded: list[tuple[str, str, str]] = []

    for feature in features:
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}

        if geometry.get("type") != "MultiPolygon":
            continue

        place = properties.get("place")
        if place not in {"island", "islet"}:
            continue

        checked += 1
        name = properties.get("name")

        if not generates_marine_buffer_from_config(
            name,
            marine_config=config.marine,
        ):
            excluded.append(
                (
                    name,
                    place,
                    str(feature.get("id")),
                )
            )

    expected = set(config.marine.non_buffer_generating_exceptions)
    matched = {name for name, _, _ in excluded}

    if matched != expected:
        raise MarineExceptionVerificationError(
            "Configured marine exceptions do not match the dataset: "
            f"expected {sorted(expected)}, found {sorted(matched)}."
        )

    return checked, tuple(excluded)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify configured marine-buffer exceptions against "
            "an island GeoJSON dataset."
        )
    )
    parser.add_argument("config", type=Path)
    parser.add_argument("dataset", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        config = load_config(args.config)
        checked, excluded = verify_marine_exceptions(
            args.config,
            args.dataset,
        )
    except (ConfigError, MarineExceptionVerificationError) as exc:
        print(f"Marine exception verification error: {exc}", file=sys.stderr)
        return 1

    print("QuodWords marine exception verification succeeded.")
    print(f"Island/islet polygons checked: {checked}")
    print(
        "Configured exceptions: "
        + ", ".join(config.marine.non_buffer_generating_exceptions)
    )
    print(f"Non-buffer-generating matches: {len(excluded)}")

    for name, place, feature_id in excluded:
        print(
            f"Name: {name} | place: {place} | "
            f"feature ID: {feature_id}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
