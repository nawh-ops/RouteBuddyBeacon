from __future__ import annotations

import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from marine_buffer_eligibility import (  # noqa: E402
    MarineBufferEligibilityError,
    generates_marine_buffer,
    generates_marine_buffer_from_config,
)


EXCEPTIONS = ("Rockall",)


@pytest.mark.parametrize(
    "feature_name",
    (
        "Foula",
        "Fair Isle",
        "Sule Skerry",
        "Sùlaisgeir",
        "Grassholm",
    ),
)
def test_qualifying_permanent_land_generates_buffer(
    feature_name: str,
) -> None:
    assert generates_marine_buffer(
        feature_name,
        non_buffer_generating_exceptions=EXCEPTIONS,
    )


def test_rockall_does_not_generate_buffer() -> None:
    assert not generates_marine_buffer(
        "Rockall",
        non_buffer_generating_exceptions=EXCEPTIONS,
    )


def test_unnamed_qualifying_land_generates_buffer() -> None:
    assert generates_marine_buffer(
        None,
        non_buffer_generating_exceptions=EXCEPTIONS,
    )


def test_exception_matching_is_exact() -> None:
    assert generates_marine_buffer(
        "rockall",
        non_buffer_generating_exceptions=EXCEPTIONS,
    )


def test_non_string_feature_name_is_rejected() -> None:
    with pytest.raises(
        MarineBufferEligibilityError,
        match="must be a string or None",
    ):
        generates_marine_buffer(
            123,  # type: ignore[arg-type]
            non_buffer_generating_exceptions=EXCEPTIONS,
        )


def test_non_string_exception_is_rejected() -> None:
    with pytest.raises(
        MarineBufferEligibilityError,
        match="Every non-buffer-generating exception",
    ):
        generates_marine_buffer(
            "Foula",
            non_buffer_generating_exceptions=(
                "Rockall",
                123,  # type: ignore[arg-type]
            ),
        )


def test_loaded_configuration_controls_eligibility() -> None:
    from config_loader import load_config

    config = load_config(
        GENERATOR_ROOT / "config" / "GB.provisional.yaml"
    )

    assert generates_marine_buffer_from_config(
        "Foula",
        marine_config=config.marine,
    )
    assert not generates_marine_buffer_from_config(
        "Rockall",
        marine_config=config.marine,
    )


def test_config_without_exception_setting_is_rejected() -> None:
    class InvalidMarineConfig:
        pass

    with pytest.raises(
        MarineBufferEligibilityError,
        match=(
            "marine_config must provide "
            "non_buffer_generating_exceptions"
        ),
    ):
        generates_marine_buffer_from_config(
            "Foula",
            marine_config=InvalidMarineConfig(),
        )
