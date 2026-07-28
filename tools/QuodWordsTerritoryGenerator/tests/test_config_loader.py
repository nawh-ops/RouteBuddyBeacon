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
