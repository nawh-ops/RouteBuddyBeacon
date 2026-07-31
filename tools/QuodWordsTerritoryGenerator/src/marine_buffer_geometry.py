"""Generate projected marine-buffer geometry from validated land features."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pyproj import Transformer
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform, unary_union


class MarineBufferGeometryError(ValueError):
    """Raised when marine-buffer geometry cannot be generated."""


def _polygonal_geometry(
    geometry: BaseGeometry,
) -> MultiPolygon:
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

    raise MarineBufferGeometryError(
        "Marine-buffer result must contain polygonal geometry."
    )


def _batched_union(
    geometries: Sequence[BaseGeometry],
    *,
    batch_size: int = 32,
    progress: Callable[[str], None] | None = None,
) -> BaseGeometry:
    if batch_size < 2:
        raise MarineBufferGeometryError(
            "Union batch size must be at least two."
        )

    remaining = list(geometries)

    if not remaining:
        raise MarineBufferGeometryError(
            "At least one geometry is required for union."
        )

    round_number = 0

    while len(remaining) > 1:
        round_number += 1

        if progress is not None:
            progress(
                f"Union round {round_number}: "
                f"{len(remaining)} geometries"
            )

        batch_count = (
            len(remaining) + batch_size - 1
        ) // batch_size
        reduced: list[BaseGeometry] = []

        for batch_number, index in enumerate(
            range(0, len(remaining), batch_size),
            start=1,
        ):
            reduced.append(
                unary_union(
                    remaining[index:index + batch_size]
                )
            )

            if progress is not None:
                progress(
                    f"Union round {round_number}: "
                    f"completed batch {batch_number} "
                    f"of {batch_count}"
                )

        remaining = reduced

    if progress is not None:
        progress(
            f"Union complete after {round_number} round(s)."
        )

    return remaining[0]


def _batched_buffer_union(
    geometries: Sequence[BaseGeometry],
    *,
    buffer_distance_metres: int,
    batch_size: int = 32,
    progress: Callable[[str], None] | None = None,
) -> BaseGeometry:
    if not geometries:
        raise MarineBufferGeometryError(
            "At least one geometry is required for buffering."
        )

    buffered_batches: list[BaseGeometry] = []
    batch_count = (
        len(geometries) + batch_size - 1
    ) // batch_size

    for batch_number, index in enumerate(
        range(0, len(geometries), batch_size),
        start=1,
    ):
        merged_batch = unary_union(
            geometries[index:index + batch_size]
        )
        buffered_batches.append(
            merged_batch.buffer(buffer_distance_metres)
        )

        if progress is not None:
            progress(
                f"Marine buffer: completed batch "
                f"{batch_number} of {batch_count}"
            )

    if progress is not None:
        progress("Combining buffered marine batches.")

    return _batched_union(
        buffered_batches,
        batch_size=batch_size,
        progress=progress,
    )


def generate_marine_buffer_geometry(
    land_dataset: Mapping[str, Any],
    *,
    buffer_distance_metres: int,
    projection: str,
    non_buffer_generating_names: Sequence[str] = (),
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Project eligible land, union it and generate its marine buffer."""

    if buffer_distance_metres <= 0:
        raise MarineBufferGeometryError(
            "buffer_distance_metres must be greater than zero."
        )

    if not isinstance(projection, str) or not projection:
        raise MarineBufferGeometryError(
            "projection must be a non-empty string."
        )

    if land_dataset.get("type") != "FeatureCollection":
        raise MarineBufferGeometryError(
            "Land dataset must be a GeoJSON FeatureCollection."
        )

    features = land_dataset.get("features")
    if not isinstance(features, list):
        raise MarineBufferGeometryError(
            "Land dataset must contain a features list."
        )

    exceptions = set(non_buffer_generating_names)
    eligible_geometries: list[BaseGeometry] = []
    excluded_geometries: list[BaseGeometry] = []

    for index, feature in enumerate(features):
        if not isinstance(feature, Mapping):
            raise MarineBufferGeometryError(
                f"Land feature {index} must be an object."
            )

        properties = feature.get("properties")
        if not isinstance(properties, Mapping):
            raise MarineBufferGeometryError(
                f"Land feature {index} must contain properties."
            )

        name = properties.get("name")

        geometry_data = feature.get("geometry")
        if not isinstance(geometry_data, Mapping):
            raise MarineBufferGeometryError(
                f"Land feature {index} must contain geometry."
            )

        try:
            geometry = shape(geometry_data)
        except (TypeError, ValueError) as exc:
            raise MarineBufferGeometryError(
                f"Land feature {index} contains invalid GeoJSON: {exc}"
            ) from exc

        if geometry.is_empty:
            raise MarineBufferGeometryError(
                f"Land feature {index} geometry must not be empty."
            )

        if not geometry.is_valid:
            raise MarineBufferGeometryError(
                f"Land feature {index} geometry must be valid."
            )

        if not isinstance(geometry, (Polygon, MultiPolygon)):
            raise MarineBufferGeometryError(
                f"Land feature {index} geometry must be polygonal."
            )

        if name in exceptions:
            excluded_geometries.append(geometry)
        else:
            eligible_geometries.append(geometry)

    if not eligible_geometries:
        raise MarineBufferGeometryError(
            "No buffer-generating land features remain."
        )

    try:
        transformer = Transformer.from_crs(
            "EPSG:4326",
            projection,
            always_xy=True,
        )
    except Exception as exc:
        raise MarineBufferGeometryError(
            f"Unable to create projection transformer: {exc}"
        ) from exc

    projected_eligible_land = [
        transform(transformer.transform, geometry)
        for geometry in eligible_geometries
    ]
    projected_excluded_land = [
        transform(transformer.transform, geometry)
        for geometry in excluded_geometries
    ]

    if progress is not None:
        progress(
            "Generating configured marine buffer "
            "in bounded batches."
        )

    buffered_eligible_land = _batched_buffer_union(
        projected_eligible_land,
        buffer_distance_metres=buffer_distance_metres,
        progress=progress,
    )

    if projected_excluded_land:
        if progress is not None:
            progress(
                "Adding non-buffer-generating permanent land."
            )

        excluded_land = _batched_union(
            projected_excluded_land,
            progress=progress,
        )
        coverage_mask = unary_union([
            buffered_eligible_land,
            excluded_land,
        ])
    else:
        coverage_mask = buffered_eligible_land
    polygonal_buffer = _polygonal_geometry(coverage_mask)

    if polygonal_buffer.is_empty:
        raise MarineBufferGeometryError(
            "Generated marine-buffer geometry must not be empty."
        )

    if not polygonal_buffer.is_valid:
        raise MarineBufferGeometryError(
            "Generated marine-buffer geometry must be valid."
        )

    return {
        "type": "Feature",
        "properties": {
            "projection": projection,
            "bufferDistanceMetres": buffer_distance_metres,
            "eligibleLandFeatureCount": len(eligible_geometries),
            "excludedFeatureNames": sorted(exceptions),
        },
        "geometry": mapping(polygonal_buffer),
    }
