from __future__ import annotations

from collections.abc import Collection


class MarineBufferEligibilityError(ValueError):
    """Raised when marine-buffer eligibility inputs are invalid."""


def generates_marine_buffer(
    feature_name: str | None,
    *,
    non_buffer_generating_exceptions: Collection[str],
) -> bool:
    if feature_name is not None and not isinstance(feature_name, str):
        raise MarineBufferEligibilityError(
            "feature_name must be a string or None."
        )

    if any(
        not isinstance(exception, str)
        for exception in non_buffer_generating_exceptions
    ):
        raise MarineBufferEligibilityError(
            "Every non-buffer-generating exception must be a string."
        )

    return feature_name not in non_buffer_generating_exceptions


def generates_marine_buffer_from_config(
    feature_name: str | None,
    *,
    marine_config: object,
) -> bool:
    try:
        exceptions = marine_config.non_buffer_generating_exceptions
    except AttributeError as exc:
        raise MarineBufferEligibilityError(
            "marine_config must provide "
            "non_buffer_generating_exceptions."
        ) from exc

    return generates_marine_buffer(
        feature_name,
        non_buffer_generating_exceptions=exceptions,
    )
