from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config_loader import ConfigError, load_config
from geometry_source_manifest import (
    GeometrySourceManifestError,
    validate_frozen_geometry_source,
)
from source_file_verifier import (
    SourceFileVerificationError,
    verify_source_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the geographic source file recorded by a frozen "
            "QuodWords territory configuration."
        )
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the frozen territory YAML configuration.",
    )
    parser.add_argument(
        "--input-directory",
        type=Path,
        required=True,
        help="Directory containing the downloaded geographic source file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        config = load_config(args.config)
        source = validate_frozen_geometry_source(
            config.geometry_source
        )

        assert source.download_filename is not None
        assert source.source_checksum is not None

        source_path = (
            args.input_directory / source.download_filename
        )

        verified_path = verify_source_file(
            source_path,
            source.source_checksum,
        )
    except (
        ConfigError,
        GeometrySourceManifestError,
        SourceFileVerificationError,
    ) as exc:
        print(f"Source verification error: {exc}", file=sys.stderr)
        return 1

    print(f"Geographic source file verified: {verified_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
