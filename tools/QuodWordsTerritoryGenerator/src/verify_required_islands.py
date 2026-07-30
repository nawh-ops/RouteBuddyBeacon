from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from config_loader import ConfigError, load_config
from marine_buffer_eligibility import generates_marine_buffer_from_config


class RequiredIslandVerificationError(ValueError):
    """Raised when configured required-island outcomes are not satisfied."""


def load_features(path: str | Path) -> list[dict[str, Any]]:
    dataset_path = Path(path)

    if not dataset_path.is_file():
        raise RequiredIslandVerificationError(
            f"Island dataset not found: {dataset_path}"
        )

    try:
        data = json.loads(dataset_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RequiredIslandVerificationError(
            f"Invalid GeoJSON in {dataset_path}: {exc}"
        ) from exc

    features = data.get("features")
    if not isinstance(features, list):
        raise RequiredIslandVerificationError(
            "GeoJSON must contain a features list."
        )

    return features


def verify_required_islands(
    config_path: str | Path,
    dataset_path: str | Path,
) -> tuple[tuple[str, str, str, bool], ...]:
    config = load_config(config_path)
    features = load_features(dataset_path)

    required_outcomes = {
        name: True
        for name in config.required_island_tests.buffer_generating
    }
    required_outcomes.update(
        {
            name: False
            for name in config.required_island_tests.non_buffer_generating
        }
    )

    matches: dict[str, list[tuple[str, str, bool]]] = {
        name: [] for name in required_outcomes
    }

    for feature in features:
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}

        if geometry.get("type") != "MultiPolygon":
            continue

        place = properties.get("place")
        if place not in {"island", "islet"}:
            continue

        name = properties.get("name")
        if name not in matches:
            continue

        generates = generates_marine_buffer_from_config(
            name,
            marine_config=config.marine,
        )
        matches[name].append(
            (
                place,
                str(feature.get("id")),
                generates,
            )
        )

    verified: list[tuple[str, str, str, bool]] = []

    for name, expected in required_outcomes.items():
        island_matches = matches[name]

        if len(island_matches) != 1:
            raise RequiredIslandVerificationError(
                f"Required island {name!r} must match exactly one "
                f"dataset feature; found {len(island_matches)}."
            )

        place, feature_id, actual = island_matches[0]

        if actual != expected:
            raise RequiredIslandVerificationError(
                f"Required island {name!r} has buffer outcome "
                f"{actual}, expected {expected}."
            )

        verified.append((name, place, feature_id, actual))

    return tuple(verified)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify configured required-island outcomes against "
            "an island GeoJSON dataset."
        )
    )
    parser.add_argument("config", type=Path)
    parser.add_argument("dataset", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        verified = verify_required_islands(
            args.config,
            args.dataset,
        )
    except (ConfigError, RequiredIslandVerificationError) as exc:
        print(
            f"Required island verification error: {exc}",
            file=sys.stderr,
        )
        return 1

    print("QuodWords required island verification succeeded.")

    for name, place, feature_id, generates in verified:
        outcome = "generates buffer" if generates else "does not generate buffer"
        print(
            f"Name: {name} | place: {place} | "
            f"feature ID: {feature_id} | {outcome}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
