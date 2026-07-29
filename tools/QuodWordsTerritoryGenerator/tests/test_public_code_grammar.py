from __future__ import annotations

import sys
from pathlib import Path

import pytest


GENERATOR_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = GENERATOR_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from public_code_grammar import (  # noqa: E402
    PublicCodeGrammarError,
    calculate_capacity,
)


def test_gb_public_grammar_capacity() -> None:
    assert calculate_capacity(
        "LLLDDDL",
        ("O",),
    ) == 439_400_000


def test_no_suffix_exclusion_uses_all_letters() -> None:
    assert calculate_capacity("LDL") == 6_760


def test_empty_pattern_is_rejected() -> None:
    with pytest.raises(
        PublicCodeGrammarError,
        match="non-empty string",
    ):
        calculate_capacity("")


def test_unknown_pattern_symbol_is_rejected() -> None:
    with pytest.raises(
        PublicCodeGrammarError,
        match="only L and D",
    ):
        calculate_capacity("LLXDDDL")


def test_pattern_must_end_with_suffix_letter() -> None:
    with pytest.raises(
        PublicCodeGrammarError,
        match="must end with",
    ):
        calculate_capacity("LLLDDD")


def test_suffix_exclusions_must_be_a_tuple() -> None:
    with pytest.raises(
        PublicCodeGrammarError,
        match="must be a tuple",
    ):
        calculate_capacity("LLLDDDL", ["O"])  # type: ignore[arg-type]


def test_duplicate_suffix_exclusions_are_rejected() -> None:
    with pytest.raises(
        PublicCodeGrammarError,
        match="must be unique",
    ):
        calculate_capacity("LLLDDDL", ("O", "O"))


@pytest.mark.parametrize(
    "excluded",
    [
        ("o",),
        ("OO",),
        ("7",),
    ],
)
def test_invalid_suffix_exclusions_are_rejected(
    excluded: tuple[str, ...],
) -> None:
    with pytest.raises(
        PublicCodeGrammarError,
        match="one uppercase letter",
    ):
        calculate_capacity("LLLDDDL", excluded)


def test_excluding_every_suffix_letter_is_rejected() -> None:
    with pytest.raises(
        PublicCodeGrammarError,
        match="At least one",
    ):
        calculate_capacity(
            "LLLDDDL",
            tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        )
