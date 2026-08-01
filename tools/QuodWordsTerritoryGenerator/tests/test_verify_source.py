from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"
GB_CONFIG_PATH = GENERATOR_ROOT / "config" / "GB.provisional.yaml"

sys.path.insert(0, str(SRC_DIR))

from verify_source import main  # noqa: E402


def write_frozen_config(
    tmp_path: Path,
    *,
    filename: str,
    content: bytes,
) -> Path:
    raw = yaml.safe_load(GB_CONFIG_PATH.read_text(encoding="utf-8"))
    source_metadata = {
        "snapshotDate": "2026-07-29",
        "extractProvider": "Test Provider",
        "downloadFilename": filename,
        "sourceChecksum": (
            "sha256:" + hashlib.sha256(content).hexdigest()
        ),
    }

    raw["geometrySource"].update(source_metadata)

    for source in raw["foreignBoundarySources"]:
        source.update(source_metadata)

    config_path = tmp_path / "GB.frozen.yaml"
    config_path.write_text(
        yaml.safe_dump(raw),
        encoding="utf-8",
    )
    return config_path


def test_matching_frozen_source_is_verified(
    tmp_path: Path,
    capsys,
) -> None:
    content = b"verified geographic source"
    filename = "great-britain.osm.pbf"
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    (input_directory / filename).write_bytes(content)

    config_path = write_frozen_config(
        tmp_path,
        filename=filename,
        content=content,
    )

    exit_code = main([
        str(config_path),
        "--input-directory",
        str(input_directory),
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert (
        captured.out.count("Geographic source file verified:")
        == 3
    )
    assert captured.out.count(filename) == 3
    assert captured.err == ""



def test_missing_named_source_file_is_rejected(
    tmp_path: Path,
    capsys,
) -> None:
    content = b"expected geographic source"
    filename = "missing.osm.pbf"

    config_path = write_frozen_config(
        tmp_path,
        filename=filename,
        content=content,
    )

    exit_code = main([
        str(config_path),
        "--input-directory",
        str(tmp_path / "input"),
    ])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Source file not found" in captured.err


def test_checksum_mismatch_is_rejected(
    tmp_path: Path,
    capsys,
) -> None:
    filename = "great-britain.osm.pbf"
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    (input_directory / filename).write_bytes(b"altered source")

    config_path = write_frozen_config(
        tmp_path,
        filename=filename,
        content=b"expected source",
    )

    exit_code = main([
        str(config_path),
        "--input-directory",
        str(input_directory),
    ])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "checksum mismatch" in captured.err
