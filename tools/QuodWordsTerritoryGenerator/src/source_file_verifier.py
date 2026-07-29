from __future__ import annotations

import hashlib
from pathlib import Path

from geometry_source_manifest import SHA256_PATTERN


class SourceFileVerificationError(ValueError):
    """Raised when a geographic source file cannot be verified."""


def calculate_sha256(
    path: str | Path,
    *,
    chunk_size: int = 1024 * 1024,
) -> str:
    """Calculate a source file checksum in manifest format."""

    source_path = Path(path)

    if not source_path.is_file():
        raise SourceFileVerificationError(
            f"Source file not found: {source_path}"
        )

    if chunk_size <= 0:
        raise SourceFileVerificationError(
            "chunk_size must be greater than zero."
        )

    digest = hashlib.sha256()

    with source_path.open("rb") as source_file:
        while chunk := source_file.read(chunk_size):
            digest.update(chunk)

    return f"sha256:{digest.hexdigest()}"


def verify_source_file(
    path: str | Path,
    expected_checksum: str,
) -> Path:
    """Verify a source file against its frozen SHA-256 checksum."""

    source_path = Path(path)

    if SHA256_PATTERN.fullmatch(expected_checksum) is None:
        raise SourceFileVerificationError(
            "expected_checksum must use the form sha256: followed by "
            "64 lowercase hexadecimal characters."
        )

    actual_checksum = calculate_sha256(source_path)

    if actual_checksum != expected_checksum:
        raise SourceFileVerificationError(
            "Source file checksum mismatch: "
            f"expected {expected_checksum}, got {actual_checksum}."
        )

    return source_path
