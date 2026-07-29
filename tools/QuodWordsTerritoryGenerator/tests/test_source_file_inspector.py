from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from source_file_inspector import (  # noqa: E402
    SourceFileInspectionError,
    inspect_source_file,
)


def _completed_process(
    *,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["osmium"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_valid_osmium_metadata_is_returned(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_path = tmp_path / "great-britain.osm.pbf"
    source_path.write_bytes(b"test source")

    metadata = {
        "file": {
            "format": "PBF",
            "data_format": "OSM",
        },
        "header": {
            "generator": "test-generator",
            "osmosis_replication_timestamp": "2026-07-29T00:00:00Z",
        },
    }

    def fake_run(*args, **kwargs):
        return _completed_process(stdout=json.dumps(metadata))

    monkeypatch.setattr(subprocess, "run", fake_run)

    inspection = inspect_source_file(source_path)

    assert inspection.path == source_path
    assert inspection.file_format == "PBF"
    assert inspection.data_format == "OSM"
    assert inspection.file_size_bytes == len(b"test source")
    assert inspection.header == metadata["header"]


def test_expected_osmium_command_is_used(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_path = tmp_path / "source.osm.pbf"
    source_path.write_bytes(b"x")
    recorded: dict[str, object] = {}

    metadata = {
        "file": {
            "format": "PBF",
            "data_format": "OSM",
        },
        "header": {},
    }

    def fake_run(command, **kwargs):
        recorded["command"] = command
        recorded["kwargs"] = kwargs
        return _completed_process(stdout=json.dumps(metadata))

    monkeypatch.setattr(subprocess, "run", fake_run)

    inspect_source_file(
        source_path,
        osmium_command="/test/bin/osmium",
    )

    assert recorded["command"] == [
        "/test/bin/osmium",
        "fileinfo",
        "--json",
        str(source_path),
    ]
    assert recorded["kwargs"] == {
        "check": False,
        "capture_output": True,
        "text": True,
    }


def test_missing_source_file_is_rejected(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.osm.pbf"

    with pytest.raises(
        SourceFileInspectionError,
        match="Source file not found",
    ):
        inspect_source_file(missing_path)


def test_missing_osmium_command_is_rejected(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_path = tmp_path / "source.osm.pbf"
    source_path.write_bytes(b"x")

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("osmium not found")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(
        SourceFileInspectionError,
        match="Unable to run osmium command",
    ):
        inspect_source_file(source_path)


def test_osmium_failure_is_rejected(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_path = tmp_path / "invalid.osm.pbf"
    source_path.write_bytes(b"not a PBF")

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: _completed_process(
            returncode=1,
            stderr="unknown file format",
        ),
    )

    with pytest.raises(
        SourceFileInspectionError,
        match="unknown file format",
    ):
        inspect_source_file(source_path)


def test_invalid_json_is_rejected(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_path = tmp_path / "source.osm.pbf"
    source_path.write_bytes(b"x")

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: _completed_process(
            stdout="not JSON",
        ),
    )

    with pytest.raises(
        SourceFileInspectionError,
        match="invalid JSON metadata",
    ):
        inspect_source_file(source_path)


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        ([], "metadata root must be a JSON object"),
        ({"header": {}}, "missing the file section"),
        (
            {"file": {"format": "PBF", "data_format": "OSM"}},
            "missing the header section",
        ),
        (
            {"file": {"data_format": "OSM"}, "header": {}},
            "missing the file format",
        ),
        (
            {"file": {"format": "PBF"}, "header": {}},
            "missing the data format",
        ),
    ],
)
def test_incomplete_metadata_is_rejected(
    tmp_path: Path,
    monkeypatch,
    metadata,
    message: str,
) -> None:
    source_path = tmp_path / "source.osm.pbf"
    source_path.write_bytes(b"x")

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: _completed_process(
            stdout=json.dumps(metadata),
        ),
    )

    with pytest.raises(SourceFileInspectionError, match=message):
        inspect_source_file(source_path)
