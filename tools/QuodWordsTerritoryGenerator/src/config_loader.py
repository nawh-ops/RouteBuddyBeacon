from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from public_code_grammar import (
    PublicCodeGrammarError,
    calculate_capacity,
)

from config_values import (
    ConfigValueError,
    require_boolean,
    require_integer,
    require_integer_list,
    require_optional_string,
    require_string,
    require_string_list,
)


class ConfigError(ValueError):
    """Raised when a territory configuration is missing or invalid."""


@dataclass(frozen=True)
class GeometrySourceConfig:
    source_type: str
    snapshot_date: str | None
    extract_provider: str | None
    download_filename: str | None
    source_checksum: str | None
    licence: str


@dataclass(frozen=True)
class CoverageConfig:
    include_england: bool
    include_scotland: bool
    include_wales: bool
    include_northern_ireland: bool
    include_inland_water: bool
    exclude_foreign_land: bool
    reserve_neighbouring_namespace_cells: bool


@dataclass(frozen=True)
class RequiredIslandTestsConfig:
    buffer_generating: tuple[str, ...]
    non_buffer_generating: tuple[str, ...]


@dataclass(frozen=True)
class PublicGrammarConfig:
    national: str
    formal: str
    final_suffix_excludes: tuple[str, ...]
    maximum_code_count: int


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
    public_guaranteed_distance_nautical_miles: int
    buffer_distance_nautical_miles: int
    buffer_distance_metres: int
    buffer_eligibility_policy: str
    non_buffer_generating_exceptions: tuple[str, ...]
    candidate_island_thresholds_hectares: tuple[int, ...]


@dataclass(frozen=True)
class TerritoryConfig:
    territory_code: str
    status: str
    resource_type: str
    geometry_source: GeometrySourceConfig
    foreign_boundary_sources: tuple[GeometrySourceConfig, ...]
    coverage: CoverageConfig
    required_island_tests: RequiredIslandTestsConfig
    public_grammar: PublicGrammarConfig
    grid: GridConfig
    marine: MarineConfig
    neighbouring_territories: tuple[str, ...]

    @property
    def maximum_code_count(self) -> int:
        return self.public_grammar.maximum_code_count


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


def _parse_geometry_source(
    raw: dict[str, Any],
    *,
    section: str,
) -> GeometrySourceConfig:
    return GeometrySourceConfig(
        source_type=require_string(
            _require_value(raw, "type", section),
            field=f"{section}.type",
        ),
        snapshot_date=require_optional_string(
            _require_value(raw, "snapshotDate", section),
            field=f"{section}.snapshotDate",
        ),
        extract_provider=require_optional_string(
            _require_value(raw, "extractProvider", section),
            field=f"{section}.extractProvider",
        ),
        download_filename=require_optional_string(
            _require_value(raw, "downloadFilename", section),
            field=f"{section}.downloadFilename",
        ),
        source_checksum=require_optional_string(
            _require_value(raw, "sourceChecksum", section),
            field=f"{section}.sourceChecksum",
        ),
        licence=require_string(
            _require_value(raw, "licence", section),
            field=f"{section}.licence",
        ),
    )

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

        geometry_raw = _require_mapping(
            _require_value(root, "geometrySource", "root"),
            "geometrySource",
        )
        foreign_boundary_sources_raw = _require_value(
            root,
            "foreignBoundarySources",
            "root",
        )
        if not isinstance(foreign_boundary_sources_raw, list):
            raise ConfigError(
                "foreignBoundarySources must be a list."
            )
        if not foreign_boundary_sources_raw:
            raise ConfigError(
                "foreignBoundarySources must not be empty."
            )
        coverage_raw = _require_mapping(
            _require_value(root, "coverage", "root"),
            "coverage",
        )
        grid_raw = _require_mapping(
            _require_value(root, "grid", "root"),
            "grid",
        )
        marine_raw = _require_mapping(
            _require_value(root, "marine", "root"),
            "marine",
        )
        island_tests_raw = _require_mapping(
            _require_value(root, "requiredIslandTests", "root"),
            "requiredIslandTests",
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

        geometry_source = _parse_geometry_source(
            geometry_raw,
            section="geometrySource",
        )
        foreign_boundary_sources = tuple(
            _parse_geometry_source(
                _require_mapping(
                    source,
                    f"foreignBoundarySources[{index}]",
                ),
                section=f"foreignBoundarySources[{index}]",
            )
            for index, source in enumerate(
                foreign_boundary_sources_raw
            )
        )

        coverage = CoverageConfig(
            include_england=require_boolean(
                _require_value(
                    coverage_raw,
                    "includeEngland",
                    "coverage",
                ),
                field="coverage.includeEngland",
            ),
            include_scotland=require_boolean(
                _require_value(
                    coverage_raw,
                    "includeScotland",
                    "coverage",
                ),
                field="coverage.includeScotland",
            ),
            include_wales=require_boolean(
                _require_value(
                    coverage_raw,
                    "includeWales",
                    "coverage",
                ),
                field="coverage.includeWales",
            ),
            include_northern_ireland=require_boolean(
                _require_value(
                    coverage_raw,
                    "includeNorthernIreland",
                    "coverage",
                ),
                field="coverage.includeNorthernIreland",
            ),
            include_inland_water=require_boolean(
                _require_value(
                    coverage_raw,
                    "includeInlandWater",
                    "coverage",
                ),
                field="coverage.includeInlandWater",
            ),
            exclude_foreign_land=require_boolean(
                _require_value(
                    coverage_raw,
                    "excludeForeignLand",
                    "coverage",
                ),
                field="coverage.excludeForeignLand",
            ),
            reserve_neighbouring_namespace_cells=require_boolean(
                _require_value(
                    coverage_raw,
                    "reserveNeighbouringNamespaceCells",
                    "coverage",
                ),
                field=(
                    "coverage."
                    "reserveNeighbouringNamespaceCells"
                ),
            ),
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

        public_guaranteed_nm = require_integer(
        _require_value(
            marine_raw,
            "publicGuaranteedDistanceNauticalMiles",
            "marine",
        ),
        field="marine.publicGuaranteedDistanceNauticalMiles",
        minimum=1,
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

        if public_guaranteed_nm > buffer_nm:
            raise ConfigValueError(
            "marine.publicGuaranteedDistanceNauticalMiles must not exceed "
            "marine.bufferDistanceNauticalMiles."
        )

        expected_metres = buffer_nm * 1852
        if buffer_metres != expected_metres:
            raise ConfigValueError(
                "marine.bufferDistanceMetres must equal "
                "marine.bufferDistanceNauticalMiles × 1852."
            )

        buffer_eligibility_policy = require_string(
            _require_value(
                marine_raw,
                "bufferEligibilityPolicy",
                "marine",
            ),
            field="marine.bufferEligibilityPolicy",
        )
        if buffer_eligibility_policy != "allQualifyingPermanentLand":
            raise ConfigValueError(
                "marine.bufferEligibilityPolicy must be "
                "allQualifyingPermanentLand."
            )

        non_buffer_generating_exceptions = require_string_list(
            _require_value(
                marine_raw,
                "nonBufferGeneratingExceptions",
                "marine",
            ),
            field="marine.nonBufferGeneratingExceptions",
            require_unique=True,
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

        buffer_generating = require_string_list(
            _require_value(
                island_tests_raw,
                "bufferGenerating",
                "requiredIslandTests",
            ),
            field="requiredIslandTests.bufferGenerating",
            allow_empty_list=False,
            require_unique=True,
        )
        non_buffer_generating = require_string_list(
            _require_value(
                island_tests_raw,
                "nonBufferGenerating",
                "requiredIslandTests",
            ),
            field="requiredIslandTests.nonBufferGenerating",
            allow_empty_list=False,
            require_unique=True,
        )

        island_overlap = set(buffer_generating) & set(non_buffer_generating)
        if island_overlap:
            overlapping_names = ", ".join(sorted(island_overlap))
            raise ConfigError(
                "requiredIslandTests entries cannot appear in both "
                "bufferGenerating and nonBufferGenerating: "
                f"{overlapping_names}"
            )

        national_grammar = require_string(
            _require_value(grammar_raw, "national", "publicGrammar"),
            field="publicGrammar.national",
        )
        formal_grammar = require_string(
            _require_value(grammar_raw, "formal", "publicGrammar"),
            field="publicGrammar.formal",
        )
        final_suffix_excludes = require_string_list(
            _require_value(
                grammar_raw,
                "finalSuffixExcludes",
                "publicGrammar",
            ),
            field="publicGrammar.finalSuffixExcludes",
            allow_empty_list=False,
            require_unique=True,
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

        try:
            calculated_code_count = calculate_capacity(
                national_grammar,
                final_suffix_excludes,
            )
        except PublicCodeGrammarError as exc:
            raise ConfigError(
                f"Invalid publicGrammar configuration: {exc}"
            ) from exc

        if maximum_code_count != calculated_code_count:
            raise ConfigError(
                "publicGrammar.maximumCodeCount does not match the "
                "capacity calculated from publicGrammar.national and "
                "publicGrammar.finalSuffixExcludes: "
                f"configured {maximum_code_count:,}, "
                f"calculated {calculated_code_count:,}."
            )

    except ConfigValueError as exc:
        raise ConfigError(str(exc)) from exc

    return TerritoryConfig(
        territory_code=territory_code,
        status=status,
        resource_type=resource_type,
        geometry_source=geometry_source,
        foreign_boundary_sources=foreign_boundary_sources,
        coverage=coverage,
        required_island_tests=RequiredIslandTestsConfig(
            buffer_generating=buffer_generating,
            non_buffer_generating=non_buffer_generating,
        ),
        public_grammar=PublicGrammarConfig(
            national=national_grammar,
            formal=formal_grammar,
            final_suffix_excludes=final_suffix_excludes,
            maximum_code_count=maximum_code_count,
        ),
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
            public_guaranteed_distance_nautical_miles=public_guaranteed_nm,
            buffer_distance_nautical_miles=buffer_nm,
            buffer_distance_metres=buffer_metres,
            buffer_eligibility_policy=buffer_eligibility_policy,
            non_buffer_generating_exceptions=(
                non_buffer_generating_exceptions
            ),
            candidate_island_thresholds_hectares=thresholds,
        ),
        neighbouring_territories=neighbours,
    )
