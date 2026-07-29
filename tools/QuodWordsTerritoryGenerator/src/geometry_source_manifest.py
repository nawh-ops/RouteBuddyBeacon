from __future__ import annotations

import re

from config_loader import GeometrySourceConfig


SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class GeometrySourceManifestError(ValueError):
    """Raised when a frozen geometry-source manifest is incomplete."""


def validate_frozen_geometry_source(
    source: GeometrySourceConfig,
) -> GeometrySourceConfig:
    """Validate metadata required to reproduce a frozen source dataset."""

    required_values = {
        "snapshot_date": source.snapshot_date,
        "extract_provider": source.extract_provider,
        "download_filename": source.download_filename,
        "source_checksum": source.source_checksum,
    }

    missing = tuple(
        field
        for field, value in required_values.items()
        if value is None
    )

    if missing:
        raise GeometrySourceManifestError(
            "Frozen geometry source is missing required metadata: "
            + ", ".join(missing)
            + "."
        )

    assert source.source_checksum is not None

    if SHA256_PATTERN.fullmatch(source.source_checksum) is None:
        raise GeometrySourceManifestError(
            "source_checksum must use the form sha256: followed by "
            "64 lowercase hexadecimal characters."
        )

    return source
