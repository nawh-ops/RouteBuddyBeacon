from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when a territory configuration is missing or invalid."""


@dataclass(frozen=True)
class GridConfig:
    projection: str
    origin_x: int
    origin_y: int
    base_cell_size_metres: int
    inclusion_rule: str
    boundary_centre_counts_as_covered: bool


@dataclass(frozen=True)
class MarineConfig:
    buffer_distance_nautical_miles: int
    buffer_distance_metres: int
    candidate_island_thresholds_hectares: tuple[int, ...]


@dataclass(frozen=True)
class TerritoryConfig:
    territory_code: str
    status: str
    resource_type: str
    grid: GridConfig
    marine: MarineConfig
    neighbouring_territories: tuple[str, ...]
    maximum_code_count: int


def _require_mapping(data: Any, name: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigError(f"{name} must be a mapping.")
    return data


def _require_value(mapping: dict[str, Any], key: str, section: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Missing required setting: {section}.{key}")
    return mapping[key]


def load_config(path: str | Path) -> TerritoryConfig:
    config_path = Path(path)

    if not config_path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    root = _require_mapping(raw, "Configuration root")
    grid_raw = _require_mapping(_require_value(root, "grid", "root"), "grid")
    marine_raw = _require_mapping(_require_value(root, "marine", "root"), "marine")
    grammar_raw = _require_mapping(
        _require_value(root, "publicGrammar", "root"), "publicGrammar"
    )

    territory_code = str(_require_value(root, "territoryCode", "root")).upper()

    if len(territory_code) != 2 or not territory_code.isalpha():
        raise ConfigError("territoryCode must be exactly two letters.")

    cell_size = int(
        _require_value(grid_raw, "baseCellSizeMetres", "grid")
    )
    if cell_size <= 0:
        raise ConfigError("grid.baseCellSizeMetres must be greater than zero.")

    buffer_nm = int(
        _require_value(marine_raw, "bufferDistanceNauticalMiles", "marine")
    )
    buffer_metres = int(
        _require_value(marine_raw, "bufferDistanceMetres", "marine")
    )

    if buffer_nm <= 0 or buffer_metres <= 0:
        raise ConfigError("Marine buffer distances must be greater than zero.")

    expected_metres = buffer_nm * 1852
    if buffer_metres != expected_metres:
        raise ConfigError(
            "marine.bufferDistanceMetres must equal "
            "marine.bufferDistanceNauticalMiles × 1852."
        )

    thresholds_raw = _require_value(
        marine_raw, "candidateIslandThresholdsHectares", "marine"
    )
    if not isinstance(thresholds_raw, list) or not thresholds_raw:
        raise ConfigError(
            "marine.candidateIslandThresholdsHectares must be a non-empty list."
        )

    thresholds = tuple(int(value) for value in thresholds_raw)
    if any(value < 0 for value in thresholds):
        raise ConfigError("Island thresholds cannot be negative.")
    if tuple(sorted(set(thresholds))) != thresholds:
        raise ConfigError(
            "Island thresholds must be unique and in ascending order."
        )

    neighbours_raw = _require_value(
        root, "neighbouringTerritories", "root"
    )
    if not isinstance(neighbours_raw, list):
        raise ConfigError("neighbouringTerritories must be a list.")

    neighbours = tuple(str(code).upper() for code in neighbours_raw)
    if any(len(code) != 2 or not code.isalpha() for code in neighbours):
        raise ConfigError(
            "Every neighbouring territory code must be exactly two letters."
        )
    if territory_code in neighbours:
        raise ConfigError(
            "A territory cannot list itself as a neighbouring territory."
        )

    maximum_code_count = int(
        _require_value(grammar_raw, "maximumCodeCount", "publicGrammar")
    )
    if maximum_code_count <= 0:
        raise ConfigError(
            "publicGrammar.maximumCodeCount must be greater than zero."
        )

    return TerritoryConfig(
        territory_code=territory_code,
        status=str(_require_value(root, "status", "root")),
        resource_type=str(_require_value(root, "resourceType", "root")),
        grid=GridConfig(
            projection=str(
                _require_value(grid_raw, "projection", "grid")
            ),
            origin_x=int(_require_value(grid_raw, "originX", "grid")),
            origin_y=int(_require_value(grid_raw, "originY", "grid")),
            base_cell_size_metres=cell_size,
            inclusion_rule=str(
                _require_value(grid_raw, "inclusionRule", "grid")
            ),
            boundary_centre_counts_as_covered=bool(
                _require_value(
                    grid_raw,
                    "boundaryCentreCountsAsCovered",
                    "grid",
                )
            ),
        ),
        marine=MarineConfig(
            buffer_distance_nautical_miles=buffer_nm,
            buffer_distance_metres=buffer_metres,
            candidate_island_thresholds_hectares=thresholds,
        ),
        neighbouring_territories=neighbours,
        maximum_code_count=maximum_code_count,
    )
