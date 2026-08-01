"""Read fixed GB geographic acceptance fixtures from the Markdown catalogue."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class GeographicTestPointError(ValueError):
    """Raised when the geographic fixture catalogue is invalid."""


@dataclass(frozen=True)
class GeographicTestPoint:
    fixture_id: str
    name: str
    latitude: float
    longitude: float
    expected_status: str


FIXED_STATUSES = frozenset({
    "includedGB",
    "excludedGB",
})


def load_fixed_geographic_test_points(
    catalogue_path: Path,
) -> tuple[GeographicTestPoint, ...]:
    if not catalogue_path.is_file():
        raise GeographicTestPointError(
            f"Geographic test-point catalogue not found: "
            f"{catalogue_path}"
        )

    try:
        lines = catalogue_path.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError as exc:
        raise GeographicTestPointError(
            f"Unable to read geographic test-point catalogue: {exc}"
        ) from exc

    fixtures: list[GeographicTestPoint] = []
    seen_ids: set[str] = set()

    for line_number, line in enumerate(lines, start=1):
        if not line.startswith("| "):
            continue

        if line.startswith("|---"):
            continue

        parts = [
            part.strip()
            for part in line.strip().strip("|").split("|")
        ]

        if len(parts) < 5:
            continue

        fixture_id = parts[0]
        status = parts[4]

        if fixture_id == "ID" or status not in FIXED_STATUSES:
            continue

        if fixture_id in seen_ids:
            raise GeographicTestPointError(
                f"Duplicate fixture ID {fixture_id!r} "
                f"at line {line_number}."
            )

        try:
            latitude = float(parts[2])
            longitude = float(parts[3])
        except ValueError as exc:
            raise GeographicTestPointError(
                f"Fixture {fixture_id!r} at line {line_number} "
                "contains an invalid latitude or longitude."
            ) from exc

        if not -90.0 <= latitude <= 90.0:
            raise GeographicTestPointError(
                f"Fixture {fixture_id!r} latitude is outside "
                "the valid range."
            )

        if not -180.0 <= longitude <= 180.0:
            raise GeographicTestPointError(
                f"Fixture {fixture_id!r} longitude is outside "
                "the valid range."
            )

        fixtures.append(
            GeographicTestPoint(
                fixture_id=fixture_id,
                name=parts[1],
                latitude=latitude,
                longitude=longitude,
                expected_status=status,
            )
        )
        seen_ids.add(fixture_id)

    if not fixtures:
        raise GeographicTestPointError(
            "The catalogue contains no fixed includedGB or "
            "excludedGB fixtures."
        )

    return tuple(fixtures)
