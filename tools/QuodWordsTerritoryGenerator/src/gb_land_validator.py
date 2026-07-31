"""Validate a generated GB permanent-land candidate dataset."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from shapely.geometry import MultiPolygon, shape


class GBLandValidationError(ValueError):
    """Raised when a GB land-candidate dataset is invalid."""


@dataclass(frozen=True)
class GBLandValidationSummary:
    """Summary of a successfully validated GB land dataset."""

    feature_count: int
    required_feature_count: int


def validate_gb_land_dataset(
    dataset: Mapping[str, Any],
    *,
    required_names: Sequence[str] = (
        "Foula",
        "Fair Isle",
        "Rockall",
    ),
) -> GBLandValidationSummary:
    """Validate structure, identifiers, geometry and required features."""

    if dataset.get("type") != "FeatureCollection":
        raise GBLandValidationError(
            "GB land dataset must be a GeoJSON FeatureCollection."
        )

    features = dataset.get("features")
    if not isinstance(features, list):
        raise GBLandValidationError(
            "GB land dataset must contain a features list."
        )

    if not features:
        raise GBLandValidationError(
            "GB land dataset must contain at least one feature."
        )

    feature_ids: set[str] = set()
    names: Counter[str] = Counter()

    for index, feature in enumerate(features):
        if not isinstance(feature, Mapping):
            raise GBLandValidationError(
                f"GB land feature {index} must be an object."
            )

        feature_id = feature.get("id")
        if not isinstance(feature_id, str) or not feature_id:
            raise GBLandValidationError(
                f"GB land feature {index} must have a non-empty string ID."
            )

        if feature_id in feature_ids:
            raise GBLandValidationError(
                f"Duplicate GB land feature ID: {feature_id}"
            )
        feature_ids.add(feature_id)

        properties = feature.get("properties")
        if not isinstance(properties, Mapping):
            raise GBLandValidationError(
                f"GB land feature {feature_id} must contain properties."
            )

        place = properties.get("place")
        if place not in {"island", "islet"}:
            raise GBLandValidationError(
                f"GB land feature {feature_id} must be an island or islet."
            )

        name = properties.get("name")
        if name is not None and not isinstance(name, str):
            raise GBLandValidationError(
                f"GB land feature {feature_id} name must be a string or null."
            )
        if isinstance(name, str):
            names[name] += 1

        geometry_data = feature.get("geometry")
        if not isinstance(geometry_data, Mapping):
            raise GBLandValidationError(
                f"GB land feature {feature_id} must contain geometry."
            )

        if geometry_data.get("type") != "MultiPolygon":
            raise GBLandValidationError(
                f"GB land feature {feature_id} geometry must be MultiPolygon."
            )

        try:
            geometry = shape(geometry_data)
        except (TypeError, ValueError) as exc:
            raise GBLandValidationError(
                f"GB land feature {feature_id} has invalid GeoJSON: {exc}"
            ) from exc

        if not isinstance(geometry, MultiPolygon):
            raise GBLandValidationError(
                f"GB land feature {feature_id} geometry must be MultiPolygon."
            )

        if geometry.is_empty:
            raise GBLandValidationError(
                f"GB land feature {feature_id} geometry must not be empty."
            )

        if not geometry.is_valid:
            raise GBLandValidationError(
                f"GB land feature {feature_id} geometry must be valid."
            )

    for required_name in required_names:
        count = names[required_name]
        if count != 1:
            raise GBLandValidationError(
                f"Required GB land feature {required_name!r} "
                f"must occur exactly once; found {count}."
            )

    return GBLandValidationSummary(
        feature_count=len(features),
        required_feature_count=len(required_names),
    )
