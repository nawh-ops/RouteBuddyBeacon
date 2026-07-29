from __future__ import annotations

import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from config_loader import GeometrySourceConfig  # noqa: E402
from geometry_source_manifest import (  # noqa: E402
    GeometrySourceManifestError,
    validate_frozen_geometry_source,
)


def make_source(
    *,
    snapshot_date: str | None = "2026-07-29",
    extract_provider: str | None = "Test Provider",
    download_filename: str | None = "great-britain.osm.pbf",
    source_checksum: str | None = "sha256:" + "a" * 64,
) -> GeometrySourceConfig:
    return GeometrySourceConfig(
        source_type="OpenStreetMap",
        snapshot_date=snapshot_date,
        extract_provider=extract_provider,
        download_filename=download_filename,
        source_checksum=source_checksum,
        licence="ODbL-1.0",
    )


def test_complete_frozen_manifest_is_returned() -> None:
    source = make_source()

    assert validate_frozen_geometry_source(source) is source


def test_missing_archival_metadata_is_rejected() -> None:
    source = make_source(
        snapshot_date=None,
        extract_provider=None,
    )

    with pytest.raises(
        GeometrySourceManifestError,
        match=(
            "missing required metadata: "
            "snapshot_date, extract_provider"
        ),
    ):
        validate_frozen_geometry_source(source)


def test_invalid_checksum_is_rejected() -> None:
    source = make_source(source_checksum="sha256:test")

    with pytest.raises(
        GeometrySourceManifestError,
        match="64 lowercase hexadecimal characters",
    ):
        validate_frozen_geometry_source(source)


def test_uppercase_checksum_is_rejected() -> None:
    source = make_source(source_checksum="sha256:" + "A" * 64)

    with pytest.raises(
        GeometrySourceManifestError,
        match="64 lowercase hexadecimal characters",
    ):
        validate_frozen_geometry_source(source)
