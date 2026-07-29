from __future__ import annotations


STANDARD_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
STANDARD_DIGITS = "0123456789"


class PublicCodeGrammarError(ValueError):
    """Raised when a public-code grammar is invalid."""


def calculate_capacity(
    national_pattern: str,
    final_suffix_excludes: tuple[str, ...] = (),
) -> int:
    """Return the number of codes provided by a national grammar."""

    if not isinstance(national_pattern, str) or not national_pattern:
        raise PublicCodeGrammarError(
            "national_pattern must be a non-empty string."
        )

    if any(symbol not in {"L", "D"} for symbol in national_pattern):
        raise PublicCodeGrammarError(
            "national_pattern may contain only L and D symbols."
        )

    if national_pattern[-1] != "L":
        raise PublicCodeGrammarError(
            "national_pattern must end with the suffix letter L."
        )

    if not isinstance(final_suffix_excludes, tuple):
        raise PublicCodeGrammarError(
            "final_suffix_excludes must be a tuple."
        )

    if len(set(final_suffix_excludes)) != len(final_suffix_excludes):
        raise PublicCodeGrammarError(
            "final_suffix_excludes values must be unique."
        )

    for letter in final_suffix_excludes:
        if (
            not isinstance(letter, str)
            or len(letter) != 1
            or letter not in STANDARD_LETTERS
        ):
            raise PublicCodeGrammarError(
                "Every excluded suffix value must be one uppercase letter."
            )

    final_suffix_count = (
        len(STANDARD_LETTERS) - len(final_suffix_excludes)
    )

    if final_suffix_count <= 0:
        raise PublicCodeGrammarError(
            "At least one final suffix letter must remain available."
        )

    leading_letter_count = national_pattern.count("L") - 1
    digit_count = national_pattern.count("D")

    return (
        len(STANDARD_LETTERS) ** leading_letter_count
        * len(STANDARD_DIGITS) ** digit_count
        * final_suffix_count
    )
