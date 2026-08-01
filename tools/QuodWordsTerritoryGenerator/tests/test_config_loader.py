from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from config_loader import ConfigError, load_config  # noqa: E402


GB_CONFIG_PATH = GENERATOR_ROOT / "config" / "GB.provisional.yaml"


def test_loads_provisional_gb_config() -> None:
    config = load_config(GB_CONFIG_PATH)

    assert config.territory_code == "GB"
    assert config.status == "provisional"
    assert config.resource_type == "territoryBase"

    assert config.geometry_source.source_type == "OpenStreetMap"
    assert config.geometry_source.snapshot_date == "2026-07-26"
    assert config.geometry_source.extract_provider == "Geofabrik"
    assert (
        config.geometry_source.download_filename
        == "britain-and-ireland-260726.osm.pbf"
    )
    assert (
        config.geometry_source.source_checksum
        == "sha256:c5a12a4c9b55fc870b78eda356f0d739"
        "967fdb1d920003ccabc2cd3a19c7321c"
    )
    assert config.geometry_source.licence == "ODbL-1.0"

    assert len(config.foreign_boundary_sources) == 2

    for source in config.foreign_boundary_sources:
        assert source.source_type == "OpenStreetMap"
        assert source.snapshot_date is None
        assert source.extract_provider == "Geofabrik"
        assert source.download_filename is None
        assert source.source_checksum is None
        assert source.licence == "ODbL-1.0"

    assert config.coverage.include_england is True
    assert config.coverage.include_scotland is True
    assert config.coverage.include_wales is True
    assert config.coverage.include_northern_ireland is True
    assert config.coverage.include_inland_water is True
    assert config.coverage.exclude_foreign_land is True
    assert config.coverage.reserve_neighbouring_namespace_cells is True

    assert config.grid.projection == "EPSG:3035"
    assert config.grid.origin_x == 0
    assert config.grid.origin_y == 0
    assert config.grid.base_cell_size_metres == 32
    assert config.grid.inclusion_rule == "centreCovered"
    assert config.grid.boundary_centre_counts_as_covered is True

    assert config.marine.buffer_distance_nautical_miles == 25
    assert config.marine.buffer_distance_metres == 46300
    assert config.marine.candidate_island_thresholds_hectares == (
        0,
        1,
        5,
        10,
        25,
        50,
        100,
    )

    assert config.neighbouring_territories == ("IE", "IM", "JE", "GG", "FR")

    assert config.required_island_tests.buffer_generating == (
        "Foula",
        "Fair Isle",
    )
    assert config.required_island_tests.non_buffer_generating == (
        "Rockall",
    )

    assert config.public_grammar.national == "LLLDDDL"
    assert config.public_grammar.formal == "GB-LLLDDDL"
    assert config.public_grammar.final_suffix_excludes == ("O",)
    assert config.public_grammar.maximum_code_count == 439400000
    assert config.maximum_code_count == 439400000


def test_missing_file_is_rejected(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config(missing_path)


def test_invalid_territory_code_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["territoryCode"] = "GBR"

    config_path = tmp_path / "invalid-territory.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="territoryCode must be exactly two letters",
    ):
        load_config(config_path)


def test_marine_distance_must_match_nautical_miles(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["marine"]["bufferDistanceMetres"] = 46000

    config_path = tmp_path / "invalid-distance.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="bufferDistanceMetres must equal",
    ):
        load_config(config_path)


def test_thresholds_must_be_unique_and_sorted(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["marine"]["candidateIslandThresholdsHectares"] = [0, 5, 1, 5]

    config_path = tmp_path / "invalid-thresholds.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="unique and in ascending order",
    ):
        load_config(config_path)


def test_territory_cannot_be_its_own_neighbour(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["neighbouringTerritories"].append("GB")

    config_path = tmp_path / "invalid-neighbour.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="cannot list itself",
    ):
        load_config(config_path)


def test_string_boolean_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["grid"]["boundaryCentreCountsAsCovered"] = "false"

    config_path = tmp_path / "string-boolean.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="grid.boundaryCentreCountsAsCovered must be a boolean",
    ):
        load_config(config_path)


def test_string_cell_size_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["grid"]["baseCellSizeMetres"] = "32"

    config_path = tmp_path / "string-cell-size.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="grid.baseCellSizeMetres must be an integer",
    ):
        load_config(config_path)


def test_float_origin_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["grid"]["originX"] = 0.0

    config_path = tmp_path / "float-origin.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="grid.originX must be an integer",
    ):
        load_config(config_path)


def test_boolean_maximum_code_count_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["publicGrammar"]["maximumCodeCount"] = True

    config_path = tmp_path / "boolean-capacity.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="publicGrammar.maximumCodeCount must be an integer",
    ):
        load_config(config_path)


def test_string_threshold_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["marine"]["candidateIslandThresholdsHectares"][2] = "5"

    config_path = tmp_path / "string-threshold.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match=(
            r"marine\.candidateIslandThresholdsHectares\[2\] "
            r"must be an integer"
        ),
    ):
        load_config(config_path)


def test_non_string_neighbour_code_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["neighbouringTerritories"][0] = 12

    config_path = tmp_path / "numeric-neighbour.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match=r"neighbouringTerritories\[0\] must be a string",
    ):
        load_config(config_path)


def test_geometry_source_optional_metadata_accepts_strings(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["geometrySource"]["snapshotDate"] = "2026-07-29"
    raw["geometrySource"]["extractProvider"] = "Test Provider"
    raw["geometrySource"]["downloadFilename"] = "planet-test.osm.pbf"
    raw["geometrySource"]["sourceChecksum"] = "sha256:test"

    config_path = tmp_path / "geometry-metadata.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    config = load_config(config_path)

    assert config.geometry_source.snapshot_date == "2026-07-29"
    assert config.geometry_source.extract_provider == "Test Provider"
    assert (
        config.geometry_source.download_filename
        == "planet-test.osm.pbf"
    )
    assert config.geometry_source.source_checksum == "sha256:test"


def test_geometry_source_numeric_snapshot_date_is_rejected(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["geometrySource"]["snapshotDate"] = 20260729

    config_path = tmp_path / "numeric-snapshot-date.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="geometrySource.snapshotDate must be a string",
    ):
        load_config(config_path)


def test_geometry_source_type_must_be_string(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["geometrySource"]["type"] = 123

    config_path = tmp_path / "numeric-source-type.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="geometrySource.type must be a string",
    ):
        load_config(config_path)


def test_coverage_string_boolean_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["coverage"]["includeNorthernIreland"] = "true"

    config_path = tmp_path / "string-coverage-boolean.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="coverage.includeNorthernIreland must be a boolean",
    ):
        load_config(config_path)


def test_coverage_integer_boolean_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["coverage"]["excludeForeignLand"] = 1

    config_path = tmp_path / "integer-coverage-boolean.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="coverage.excludeForeignLand must be a boolean",
    ):
        load_config(config_path)


def test_island_cannot_be_in_both_required_test_lists(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["requiredIslandTests"]["nonBufferGenerating"].append("Foula")

    config_path = tmp_path / "overlapping-island-tests.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match=(
            "requiredIslandTests entries cannot appear in both "
            "bufferGenerating and nonBufferGenerating: Foula"
        ),
    ):
        load_config(config_path)


def test_duplicate_required_island_name_is_rejected(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["requiredIslandTests"]["bufferGenerating"].append("Foula")

    config_path = tmp_path / "duplicate-island-test.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match=(
            "requiredIslandTests.bufferGenerating "
            "values must be unique"
        ),
    ):
        load_config(config_path)


def test_non_string_public_grammar_is_rejected(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["publicGrammar"]["national"] = 1234567

    config_path = tmp_path / "numeric-public-grammar.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="publicGrammar.national must be a string",
    ):
        load_config(config_path)


def test_public_grammar_capacity_mismatch_is_rejected(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(
        GB_CONFIG_PATH.read_text(encoding="utf-8")
    )
    raw["publicGrammar"]["maximumCodeCount"] = 439_399_999

    config_path = tmp_path / "capacity-mismatch.yaml"
    config_path.write_text(
        yaml.safe_dump(raw),
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigError,
        match="does not match the capacity calculated",
    ):
        load_config(config_path)


def test_invalid_public_grammar_pattern_is_rejected(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(
        GB_CONFIG_PATH.read_text(encoding="utf-8")
    )
    raw["publicGrammar"]["national"] = "LLXDDDL"

    config_path = tmp_path / "invalid-grammar.yaml"
    config_path.write_text(
        yaml.safe_dump(raw),
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigError,
        match="Invalid publicGrammar configuration",
    ):
        load_config(config_path)

def test_marine_policy_is_loaded() -> None:
    config = load_config(GB_CONFIG_PATH)

    assert (
        config.marine.buffer_eligibility_policy
        == "allQualifyingPermanentLand"
    )
    assert config.marine.non_buffer_generating_exceptions == (
        "Rockall",
    )


def test_unknown_marine_policy_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["marine"]["bufferEligibilityPolicy"] = "areaThreshold"

    config_path = tmp_path / "unknown-marine-policy.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="must be allQualifyingPermanentLand",
    ):
        load_config(config_path)


def test_duplicate_non_buffer_exceptions_are_rejected(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["marine"]["nonBufferGeneratingExceptions"] = [
        "Rockall",
        "Rockall",
    ]

    config_path = tmp_path / "duplicate-marine-exceptions.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match="values must be unique",
    ):
        load_config(config_path)


def test_non_buffer_exception_must_be_a_string(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["marine"]["nonBufferGeneratingExceptions"] = [123]

    config_path = tmp_path / "numeric-marine-exception.yaml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match=(
            r"marine\.nonBufferGeneratingExceptions\[0\] "
            r"must be a string"
        ),
    ):
        load_config(config_path)

