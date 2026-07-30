from __future__ import annotations

import sys
from pathlib import Path

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from validate_config import format_summary, main  # noqa: E402
from config_loader import load_config  # noqa: E402


GB_CONFIG_PATH = GENERATOR_ROOT / "config" / "GB.provisional.yaml"


def test_format_summary_contains_key_gb_settings() -> None:
    config = load_config(GB_CONFIG_PATH)

    summary = format_summary(config)

    assert "Territory: GB" in summary
    assert "Projection: EPSG:3035" in summary
    assert "Grid: 32 m cells, origin (0, 0)" in summary
    assert "Marine buffer: 25 NM (46300 m)" in summary
    assert (
        "Marine eligibility: allQualifyingPermanentLand"
        in summary
    )
    assert (
        "Non-buffer-generating exceptions: Rockall"
        in summary
    )
    assert "Neighbouring territories: IE, IM, JE, GG, FR" in summary
    assert "Maximum public-code capacity: 439,400,000" in summary


def test_main_returns_zero_for_valid_config(capsys) -> None:
    exit_code = main([str(GB_CONFIG_PATH)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "configuration is valid" in captured.out
    assert captured.err == ""


def test_main_returns_one_for_missing_config(
    tmp_path: Path,
    capsys,
) -> None:
    missing_path = tmp_path / "missing.yaml"

    exit_code = main([str(missing_path)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Configuration error:" in captured.err
    assert "Configuration file not found" in captured.err



def test_provisional_config_passes_without_frozen_source_requirement(
    capsys,
) -> None:
    exit_code = main([str(GB_CONFIG_PATH)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "configuration is valid" in captured.out
    assert captured.err == ""


def test_provisional_config_fails_when_frozen_source_is_required(
    capsys,
) -> None:
    exit_code = main([
        str(GB_CONFIG_PATH),
        "--require-frozen-source",
    ])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Configuration error:" in captured.err
    assert "missing required metadata" in captured.err
    assert "snapshot_date" in captured.err
    assert "source_checksum" in captured.err
