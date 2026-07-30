from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config_loader import ConfigError
from verify_marine_exceptions import (
    MarineExceptionVerificationError,
    verify_marine_exceptions,
)
from verify_required_islands import (
    RequiredIslandVerificationError,
    verify_required_islands,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the complete configured QuodWords island-policy audit."
        )
    )
    parser.add_argument("config", type=Path)
    parser.add_argument("dataset", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        checked, exceptions = verify_marine_exceptions(
            args.config,
            args.dataset,
        )
        required = verify_required_islands(
            args.config,
            args.dataset,
        )
    except (
        ConfigError,
        MarineExceptionVerificationError,
        RequiredIslandVerificationError,
    ) as exc:
        print(f"Island policy verification error: {exc}", file=sys.stderr)
        return 1

    print("QuodWords island policy verification succeeded.")
    print(f"Island/islet polygons checked: {checked}")
    print(f"Configured exception matches: {len(exceptions)}")
    print(f"Required island outcomes verified: {len(required)}")

    for name, place, feature_id, generates in required:
        outcome = (
            "generates buffer"
            if generates
            else "does not generate buffer"
        )
        print(
            f"Name: {name} | place: {place} | "
            f"feature ID: {feature_id} | {outcome}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
