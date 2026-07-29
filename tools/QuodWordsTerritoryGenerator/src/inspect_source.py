from __future__ import annotations

import argparse
import sys
from pathlib import Path

from source_file_inspector import (
    SourceFileInspection,
    SourceFileInspectionError,
    inspect_source_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect an OpenStreetMap source file using osmium."
    )
    parser.add_argument(
        "source_file",
        type=Path,
        help="Path to the candidate OSM source file.",
    )
    return parser


def format_summary(inspection: SourceFileInspection) -> str:
    header_options = inspection.header.get("option", {})
    if not isinstance(header_options, dict):
        header_options = {}

    header_generator = inspection.header.get(
        "generator", header_options.get("generator")
    )
    replication_timestamp = inspection.header.get(
        "osmosis_replication_timestamp",
        header_options.get("osmosis_replication_timestamp"),
    )

    generator_text = (
        header_generator
        if isinstance(header_generator, str) and header_generator
        else "not supplied"
    )
    timestamp_text = (
        replication_timestamp
        if isinstance(replication_timestamp, str)
        and replication_timestamp
        else "not supplied"
    )

    return "\n".join(
        (
            "QuodWords geographic source inspection succeeded.",
            f"File: {inspection.path}",
            f"File format: {inspection.file_format}",
            f"Data format: {inspection.data_format}",
            f"File size: {inspection.file_size_bytes:,} bytes",
            f"Header generator: {generator_text}",
            f"Replication timestamp: {timestamp_text}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        inspection = inspect_source_file(args.source_file)
    except SourceFileInspectionError as exc:
        print(f"Source inspection error: {exc}", file=sys.stderr)
        return 1

    print(format_summary(inspection))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
