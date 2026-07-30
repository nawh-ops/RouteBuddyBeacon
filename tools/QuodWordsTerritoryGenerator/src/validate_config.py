from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config_loader import ConfigError, TerritoryConfig, load_config
from geometry_source_manifest import (
    GeometrySourceManifestError,
    validate_frozen_geometry_source,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a QuodWords territory configuration."
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the territory YAML configuration file.",
    )
    parser.add_argument(
        "--require-frozen-source",
        action="store_true",
        help=(
            "Require complete reproducibility metadata for the "
            "geometry source."
        ),
    )
    return parser


def format_summary(config: TerritoryConfig) -> str:
    neighbours = ", ".join(config.neighbouring_territories) or "none"
    thresholds = ", ".join(
        str(value)
        for value in config.marine.candidate_island_thresholds_hectares
    )
    exceptions = ", ".join(
        config.marine.non_buffer_generating_exceptions
    ) or "none"

    return "\n".join(
        (
            "QuodWords territory configuration is valid.",
            f"Territory: {config.territory_code}",
            f"Status: {config.status}",
            f"Resource type: {config.resource_type}",
            f"Projection: {config.grid.projection}",
            (
                "Grid: "
                f"{config.grid.base_cell_size_metres} m cells, "
                f"origin ({config.grid.origin_x}, {config.grid.origin_y})"
            ),
            (
                "Marine buffer: "
                f"{config.marine.buffer_distance_nautical_miles} NM "
                f"({config.marine.buffer_distance_metres} m)"
            ),
            (
                "Marine eligibility: "
                f"{config.marine.buffer_eligibility_policy}"
            ),
            (
                "Non-buffer-generating exceptions: "
                f"{exceptions}"
            ),
            f"Candidate island thresholds: {thresholds} hectares",
            f"Neighbouring territories: {neighbours}",
            f"Maximum public-code capacity: {config.maximum_code_count:,}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)

        if args.require_frozen_source:
            validate_frozen_geometry_source(config.geometry_source)
    except (ConfigError, GeometrySourceManifestError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    print(format_summary(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
