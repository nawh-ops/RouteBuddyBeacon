from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SourceFileInspectionError(ValueError):
    """Raised when osmium cannot inspect a geographic source file."""


@dataclass(frozen=True)
class SourceFileInspection:
    path: Path
    file_format: str
    data_format: str
    file_size_bytes: int
    header: dict[str, Any]


def inspect_source_file(
    path: str | Path,
    *,
    osmium_command: str = "osmium",
) -> SourceFileInspection:
    source_path = Path(path)

    if not source_path.is_file():
        raise SourceFileInspectionError(
            f"Source file not found: {source_path}"
        )

    try:
        result = subprocess.run(
            [
                osmium_command,
                "fileinfo",
                "--json",
                str(source_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise SourceFileInspectionError(
            f"Unable to run osmium command: {exc}"
        ) from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or "unknown osmium error"
        raise SourceFileInspectionError(
            f"Unable to inspect source file: {detail}"
        )

    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SourceFileInspectionError(
            "osmium returned invalid JSON metadata."
        ) from exc

    if not isinstance(metadata, dict):
        raise SourceFileInspectionError(
            "osmium metadata root must be a JSON object."
        )

    file_info = metadata.get("file")
    header = metadata.get("header")

    if not isinstance(file_info, dict):
        raise SourceFileInspectionError(
            "osmium metadata is missing the file section."
        )

    if not isinstance(header, dict):
        raise SourceFileInspectionError(
            "osmium metadata is missing the header section."
        )

    file_format = file_info.get("format")
    data_format = file_info.get("data_format", file_format)

    if not isinstance(file_format, str) or not file_format:
        raise SourceFileInspectionError(
            "osmium metadata is missing the file format."
        )

    if not isinstance(data_format, str) or not data_format:
        raise SourceFileInspectionError(
            "osmium metadata is missing the data format."
        )

    return SourceFileInspection(
        path=source_path,
        file_format=file_format,
        data_format=data_format,
        file_size_bytes=source_path.stat().st_size,
        header=header,
    )
