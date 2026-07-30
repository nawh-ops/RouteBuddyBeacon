"""Select permanent-land candidates within the GB jurisdiction boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, mapping, shape
from shapely.geometry.base import BaseGeometry


class GBLandSelectionError(ValueError):
    """Raised when GB land-selection input is invalid."""


def _feature_list(
    dataset: Mapping[str, Any],
    *,
    label: str,
) -> list[Mapping[str, Any]]:
    if dataset.get("type") != "FeatureCollection":
        raise GBLandSelectionError(
            f"{label} must be a GeoJSON FeatureCollection."
        )

    features = dataset.get("features")
    if not isinstance(features, list):
        raise GBLandSelectionError(
            f"{label} must contain a features list."
        )

    if not all(isinstance(feature, Mapping) for feature in features):
        raise GBLandSelectionError(
            f"Every {label} feature must be an object."
        )

    return features


def _geometry_from_feature(
    feature: Mapping[str, Any],
    *,
    label: str,
) -> BaseGeometry:
    geometry_data = feature.get("geometry")
    if not isinstance(geometry_data, Mapping):
        raise GBLandSelectionError(
            f"{label} must contain a GeoJSON geometry."
        )

    try:
        geometry = shape(geometry_data)
    except (TypeError, ValueError) as exc:
        raise GBLandSelectionError(
            f"{label} contains invalid GeoJSON geometry: {exc}"
        ) from exc

    if geometry.is_empty:
        raise GBLandSelectionError(f"{label} geometry must not be empty.")

    if not geometry.is_valid:
        raise GBLandSelectionError(f"{label} geometry must be valid.")

    return geometry


def _polygonal_geometry(geometry: BaseGeometry) -> MultiPolygon | None:
    if isinstance(geometry, Polygon):
        return MultiPolygon([geometry])

    if isinstance(geometry, MultiPolygon):
        return geometry

    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []

        for part in geometry.geoms:
            if isinstance(part, Polygon):
                polygons.append(part)
            elif isinstance(part, MultiPolygon):
                polygons.extend(part.geoms)

        if polygons:
            return MultiPolygon(polygons)

    return None


def select_gb_land_features(
    boundary_dataset: Mapping[str, Any],
    candidate_dataset: Mapping[str, Any],
) -> dict[str, Any]:
    """Clip island and islet polygons to the GB jurisdiction boundary."""

    boundary_features = _feature_list(
        boundary_dataset,
        label="GB boundary dataset",
    )
    if len(boundary_features) != 1:
        raise GBLandSelectionError(
            "GB boundary dataset must contain exactly one feature."
        )

    boundary = _geometry_from_feature(
        boundary_features[0],
        label="GB boundary feature",
    )
    if not isinstance(boundary, (Polygon, MultiPolygon)):
        raise GBLandSelectionError(
            "GB boundary feature must be Polygon or MultiPolygon."
        )

    candidate_features = _feature_list(
        candidate_dataset,
        label="Land candidate dataset",
    )

    selected: list[dict[str, Any]] = []

    for index, feature in enumerate(candidate_features):
        properties = feature.get("properties")
        if not isinstance(properties, Mapping):
            continue

        if properties.get("place") not in {"island", "islet"}:
            continue

        geometry_data = feature.get("geometry")
        if not isinstance(geometry_data, Mapping):
            raise GBLandSelectionError(
                f"Land candidate feature {index} has no geometry."
            )

        if geometry_data.get("type") != "MultiPolygon":
            continue

        candidate = _geometry_from_feature(
            feature,
            label=f"Land candidate feature {index}",
        )

        clipped = _polygonal_geometry(candidate.intersection(boundary))
        if clipped is None or clipped.is_empty:
            continue

        output_feature: dict[str, Any] = {
            "type": "Feature",
            "properties": dict(properties),
            "geometry": mapping(clipped),
        }

        if "id" in feature:
            output_feature["id"] = feature["id"]

        selected.append(output_feature)

    return {
        "type": "FeatureCollection",
        "features": selected,
    }
