from __future__ import annotations

from typing import Any


class ConfigValueError(ValueError):
    """Raised when a configuration value has the wrong type or form."""


def require_string(
    value: Any,
    *,
    field: str,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        raise ConfigValueError(f"{field} must be a string.")

    if not allow_empty and not value.strip():
        raise ConfigValueError(f"{field} must not be empty.")

    return value


def require_boolean(value: Any, *, field: str) -> bool:
    if type(value) is not bool:
        raise ConfigValueError(f"{field} must be a boolean.")

    return value


def require_integer(
    value: Any,
    *,
    field: str,
    minimum: int | None = None,
) -> int:
    if type(value) is not int:
        raise ConfigValueError(f"{field} must be an integer.")

    if minimum is not None and value < minimum:
        raise ConfigValueError(
            f"{field} must be greater than or equal to {minimum}."
        )

    return value


def require_integer_list(
    value: Any,
    *,
    field: str,
    minimum: int | None = None,
    require_unique: bool = False,
    require_ascending: bool = False,
) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise ConfigValueError(f"{field} must be a list.")

    parsed = tuple(
        require_integer(
            item,
            field=f"{field}[{index}]",
            minimum=minimum,
        )
        for index, item in enumerate(value)
    )

    if require_unique and len(set(parsed)) != len(parsed):
        raise ConfigValueError(f"{field} values must be unique.")

    if require_ascending and tuple(sorted(parsed)) != parsed:
        raise ConfigValueError(
            f"{field} values must be in ascending order."
        )

    return parsed
