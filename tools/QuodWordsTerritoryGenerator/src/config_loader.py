from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from config_values import (
    ConfigValueError,
    require_boolean,
    require_integer,
    require_integer_list,
    require_string,
)


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


def _require_value(
    mapping: dict[str, Any],
    key: str,
    section: str,
) -> Any:
    if key not in mapping:
        raise ConfigError(f"Missing required setting: {section}.{key}")
    return mapping[key]


def _parse_territory_code(value: Any, *, field: str) -> str:
    code = require_string(value, field=field).upper()

    if len(code) != 2 or not code.isalpha():
        raise ConfigValueError(
            f"{field} must be exactly two letters."
        )

    return code


def _parse_neighbouring_territories(
    value: Any,
    *,
    territory_code: str,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigValueError(
            "neighbouringTerritories must be a list."
        )

    neighbours = tuple(
        _parse_territory_code(
            item,
            field=f"neighbouringTerritories[{index}]",
        )
        for index, item in enumerate(value)
    )

    if territory_code in neighbours:
        raise ConfigValueError(
            "A territory cannot list itself as a neighbouring territory."
        )

    return neighbours


def load_config(path: str | Path) -> TerritoryConfig:
    config_path = Path(path)

    if not config_path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(
            f"Invalid YAML in {config_path}: {exc}"
        ) from exc

    try:
        root = _require_mapping(raw, "Configuration root")
        grid_raw = _require_mapping(
            _require_value(root, "grid", "root"),
            "grid",
        )
        marine_raw = _require_mapping(
            _require_value(root, "marine", "root"),
            "marine",
        )
        grammar_raw = _require_mapping(
            _require_value(root, "publicGrammar", "root"),
            "publicGrammar",
        )

        territory_code = _parse_territory_code(
            _require_value(root, "territoryCode", "root"),
            field="territoryCode",
        )

        status = require_string(
            _require_value(root, "status", "root"),
            field="status",
        )
        resource_type = require_string(
            _require_value(root, "resourceType", "root"),
            field="resourceType",
        )

        projection = require_string(
            _require_value(grid_raw, "projection", "grid"),
            field="grid.projection",
        )
        origin_x = require_integer(
            _require_value(grid_raw, "originX", "grid"),
            field="grid.originX",
        )
        origin_y = require_integer(
            _require_value(grid_raw, "originY", "grid"),
            field="grid.originY",
        )
        cell_size = require_integer(
            _require_value(
                grid_raw,
                "baseCellSizeMetres",
                "grid",
            ),
            field="grid.baseCellSizeMetres",
            minimum=1,
        )
        inclusion_rule = require_string(
            _require_value(grid_raw, "inclusionRule", "grid"),
            field="grid.inclusionRule",
        )
        boundary_centre_counts_as_covered = require_boolean(
            _require_value(
                grid_raw,
                "boundaryCentreCountsAsCovered",
                "grid",
            ),
            field="grid.boundaryCentreCountsAsCovered",
        )

        buffer_nm = require_integer(
            _require_value(
                marine_raw,
                "bufferDistanceNauticalMiles",
                "marine",
            ),
            field="marine.bufferDistanceNauticalMiles",
            minimum=1,
        )
        buffer_metres = require_integer(
            _require_value(
                marine_raw,
                "bufferDistanceMetres",
                "marine",
            ),
            field="marine.bufferDistanceMetres",
            minimum=1,
        )

        expected_metres = buffer_nm * 1852
        if buffer_metres != expected_metres:
            raise ConfigValueError(
                "marine.bufferDistanceMetres must equal "
                "marine.bufferDistanceNauticalMiles × 1852."
            )

        thresholds_raw = _require_value(
            marine_raw,
            "candidateIslandThresholdsHectares",
            "marine",
        )

        if not isinstance(thresholds_raw, list) or not thresholds_raw:
            raise ConfigValueError(
                "marine.candidateIslandThresholdsHectares "
                "must be a non-empty list."
            )

        thresholds = require_integer_list(
            thresholds_raw,
            field="marine.candidateIslandThresholdsHectares",
            minimum=0,
        )

        if tuple(sorted(set(thresholds))) != thresholds:
            raise ConfigValueError(
                "Island thresholds must be unique and in ascending order."
            )

        neighbours = _parse_neighbouring_territories(
            _require_value(
                root,
                "neighbouringTerritories",
                "root",
            ),
            territory_code=territory_code,
        )

        maximum_code_count = require_integer(
            _require_value(
                grammar_raw,
                "maximumCodeCount",
                "publicGrammar",
            ),
            field="publicGrammar.maximumCodeCount",
            minimum=1,
        )

    except ConfigValueError as exc:
        raise ConfigError(str(exc)) from exc

    return TerritoryConfig(
        territory_code=territory_code,
        status=status,
        resource_type=resource_type,
        grid=GridConfig(
            projection=projection,
            origin_x=origin_x,
            origin_y=origin_y,
            base_cell_size_metres=cell_size,
            inclusion_rule=inclusion_rule,
            boundary_centre_counts_as_covered=(
                boundary_centre_counts_as_covered
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
