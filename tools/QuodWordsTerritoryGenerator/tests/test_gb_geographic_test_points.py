"""Tests for the GB geographic acceptance-fixture catalogue parser."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GENERATOR_ROOT / "src"))

from gb_geographic_test_points import (  # noqa: E402
    GeographicTestPointError,
    load_fixed_geographic_test_points,
)


CATALOGUE_PATH = (
    REPOSITORY_ROOT
    / "Docs"
    / "QuodWordsGBGeographicTestPoints.md"
)


def test_loads_all_fixed_catalogue_fixtures() -> None:
    fixtures = load_fixed_geographic_test_points(
        CATALOGUE_PATH
    )

    assert len(fixtures) == 37
    assert len({
        fixture.fixture_id
        for fixture in fixtures
    }) == 37
    assert sum(
        fixture.expected_status == "includedGB"
        for fixture in fixtures
    ) == 25
    assert sum(
        fixture.expected_status == "excludedGB"
        for fixture in fixtures
    ) == 12


def test_loads_established_coastal_fixture() -> None:
    fixtures = load_fixed_geographic_test_points(
        CATALOGUE_PATH
    )
    fixture = next(
        item
        for item in fixtures
        if item.fixture_id == "GB-SEA-003"
    )

    assert fixture.name == "Near-shore water west of Lewis"
    assert fixture.latitude == pytest.approx(58.2)
    assert fixture.longitude == pytest.approx(-6.7)
    assert fixture.expected_status == "includedGB"


def test_pending_boundary_groups_are_not_loaded() -> None:
    fixtures = load_fixed_geographic_test_points(
        CATALOGUE_PATH
    )
    fixture_ids = {
        fixture.fixture_id
        for fixture in fixtures
    }

    assert not any(
        fixture_id.startswith("GB-LIMIT-")
        for fixture_id in fixture_ids
    )
    assert not any(
        fixture_id.startswith("GB-IE-BOUNDARY-")
        for fixture_id in fixture_ids
    )


def test_duplicate_fixture_id_is_rejected(
    tmp_path: Path,
) -> None:
    catalogue = tmp_path / "catalogue.md"
    catalogue.write_text(
        "\n".join([
            "| ID | Name | Latitude | Longitude | Expected result |",
            "|---|---:|---:|---:|---|",
            "| TEST-001 | First | 51.0 | -1.0 | includedGB |",
            "| TEST-001 | Second | 52.0 | -2.0 | excludedGB |",
        ])
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        GeographicTestPointError,
        match="Duplicate fixture ID",
    ):
        load_fixed_geographic_test_points(catalogue)


def test_invalid_coordinate_is_rejected(
    tmp_path: Path,
) -> None:
    catalogue = tmp_path / "catalogue.md"
    catalogue.write_text(
        "\n".join([
            "| ID | Name | Latitude | Longitude | Expected result |",
            "|---|---:|---:|---:|---|",
            "| TEST-001 | Invalid | north | -1.0 | includedGB |",
        ])
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        GeographicTestPointError,
        match="invalid latitude or longitude",
    ):
        load_fixed_geographic_test_points(catalogue)
