from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from source_file_verifier import (  # noqa: E402
    SourceFileVerificationError,
    calculate_sha256,
    verify_source_file,
)


def expected_checksum(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def test_calculate_sha256_returns_manifest_format(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.osm.pbf"
    source_path.write_bytes(b"QuodWords test source")

    assert calculate_sha256(source_path) == expected_checksum(
        b"QuodWords test source"
    )


def test_matching_source_file_is_returned(tmp_path: Path) -> None:
    content = b"verified source data"
    source_path = tmp_path / "source.osm.pbf"
    source_path.write_bytes(content)

    assert verify_source_file(
        source_path,
        expected_checksum(content),
    ) == source_path


def test_missing_source_file_is_rejected(tmp_path: Path) -> None:
    source_path = tmp_path / "missing.osm.pbf"

    with pytest.raises(
        SourceFileVerificationError,
        match="Source file not found",
    ):
        calculate_sha256(source_path)


def test_checksum_mismatch_is_rejected(tmp_path: Path) -> None:
    source_path = tmp_path / "source.osm.pbf"
    source_path.write_bytes(b"actual source data")

    with pytest.raises(
        SourceFileVerificationError,
        match="checksum mismatch",
    ):
        verify_source_file(
            source_path,
            expected_checksum(b"different source data"),
        )


def test_invalid_expected_checksum_is_rejected(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.osm.pbf"
    source_path.write_bytes(b"source data")

    with pytest.raises(
        SourceFileVerificationError,
        match="expected_checksum must use the form",
    ):
        verify_source_file(source_path, "sha256:test")


def test_non_positive_chunk_size_is_rejected(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.osm.pbf"
    source_path.write_bytes(b"source data")

    with pytest.raises(
        SourceFileVerificationError,
        match="chunk_size must be greater than zero",
    ):
        calculate_sha256(source_path, chunk_size=0)
