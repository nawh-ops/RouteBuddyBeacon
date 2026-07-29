from __future__ import annotations

import sys
from pathlib import Path

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

import inspect_source  # noqa: E402
from source_file_inspector import (  # noqa: E402
    SourceFileInspection,
    SourceFileInspectionError,
)


def test_format_summary_includes_metadata(tmp_path: Path) -> None:
    source_path = tmp_path / "candidate.osm.pbf"
    inspection = SourceFileInspection(
        path=source_path,
        file_format="PBF",
        data_format="OSM",
        file_size_bytes=1234567,
        header={
            "generator": "test-generator",
            "osmosis_replication_timestamp": "2026-07-29T12:00:00Z",
        },
    )

    summary = inspect_source.format_summary(inspection)

    assert "inspection succeeded" in summary
    assert f"File: {source_path}" in summary
    assert "File format: PBF" in summary
    assert "Data format: OSM" in summary
    assert "File size: 1,234,567 bytes" in summary
    assert "Header generator: test-generator" in summary
    assert "Replication timestamp: 2026-07-29T12:00:00Z" in summary


def test_format_summary_handles_missing_optional_header_values(
    tmp_path: Path,
) -> None:
    inspection = SourceFileInspection(
        path=tmp_path / "candidate.osm.pbf",
        file_format="PBF",
        data_format="OSM",
        file_size_bytes=1,
        header={},
    )

    summary = inspect_source.format_summary(inspection)

    assert "Header generator: not supplied" in summary
    assert "Replication timestamp: not supplied" in summary


def test_main_prints_summary(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    source_path = tmp_path / "candidate.osm.pbf"
    inspection = SourceFileInspection(
        path=source_path,
        file_format="PBF",
        data_format="OSM",
        file_size_bytes=25,
        header={},
    )

    monkeypatch.setattr(
        inspect_source,
        "inspect_source_file",
        lambda path: inspection,
    )

    exit_code = inspect_source.main([str(source_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "inspection succeeded" in captured.out
    assert captured.err == ""


def test_main_reports_inspection_error(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    source_path = tmp_path / "invalid.osm.pbf"

    def reject_source(path):
        raise SourceFileInspectionError("invalid source file")

    monkeypatch.setattr(
        inspect_source,
        "inspect_source_file",
        reject_source,
    )

    exit_code = inspect_source.main([str(source_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Source inspection error: invalid source file" in captured.err
