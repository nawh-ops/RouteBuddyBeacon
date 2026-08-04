# QuodWords GB Territory Geometry — Phase 2 Completion Record

## Status

Phase 2 is complete.

The GB land-and-marine coverage geometry has been accepted as the
release candidate for subsequent 32 metre cell and territory-index
generation.

This phase does not create separate QuodWords territories for Ireland,
the Isle of Man, Jersey, Guernsey or France. Their national polygons are
used only to remove foreign land from the GB coverage geometry.

## Approved release artefact

- Territory: GB
- Geometry: `gb-coverage-mask.geojson`
- Geometry type: `MultiPolygon`
- Projection: `EPSG:3035`
- File size: 849,496 bytes
- SHA-256:
  `d14f9e8e2c013f8ae4b89fff375bb5036c60665258bdbbb23e337f287a3d1b86`

The tracked release artefact is:

`tools/QuodWordsTerritoryGenerator/release/GB/gb-coverage-mask.geojson`

Its machine-readable provenance and acceptance record is:

`tools/QuodWordsTerritoryGenerator/release/GB/phase-2-manifest.json`

## Accepted territory policy

- Great Britain and Northern Ireland are included.
- Qualifying permanent islands are included.
- Inland water is included.
- The internal marine generation buffer is 17 nautical miles / 31,484 metres.
- All qualifying permanent land generates marine coverage except
  configured exceptions.
- Rockall remains covered as permanent land but does not independently
  generate a marine buffer.
- Foreign land is excluded.
- The neighbouring territory polygons used for foreign-land subtraction
  are IE, IM, JE, GG and FR.
- The future base grid uses 32 metre cells.
- Cell inclusion is determined by the cell centre.
- A centre lying exactly on the boundary counts as covered.

## Geographic acceptance

The release geometry passed 25 permanent real-world checks covering:

- England, Scotland, Wales and Northern Ireland;
- Shetland, Orkney, Lewis, the Isles of Scilly, Foula and Fair Isle;
- the English Channel, Irish Sea, North Sea and The Minch;
- the Northern Ireland–Ireland separation;
- exclusion of Ireland, the Isle of Man, Jersey, Guernsey and France;
- exclusion of locations clearly beyond the intended marine reach.

The acceptance validator is:

`tools/QuodWordsTerritoryGenerator/src/validate_gb_coverage_geography.py`

## Automated verification

At approval:

- permanent geographic checks: 25 passed;
- full automated suite: 223 passed;
- geometry was valid and non-empty;
- candidate and tracked release checksums were identical.

## Phase boundary

Phase 2 approves the geographic coverage shape only.

The next substantial stage is to convert the approved geometry into the
release-ready 32 metre QuodWords GB cell/index resource and then integrate
that resource into RouteBuddy Beacon.

## Final marine coverage and capacity policy

- Public marine guarantee: **15 nautical miles** from qualifying British land and islands.
- Internal marine generation buffer: **17 nautical miles / 31,484 metres**.
- Included 32 metre cells: **433,083,140**.
- Maximum public-code capacity: **439,400,000**.
- Remaining capacity: **6,316,860 codes**.
- Capacity used: **98.5624%**.
- The released GB cell and index mapping is immutable. Later source-data or policy changes must not renumber the original mapping.

## Frozen GB territory resource

- File: `GB.qwtr`.
- Binary format: `QWTRSPAN`, schema version 1.
- Projection: EPSG:3035.
- Grid origin: `(0, 0)`.
- Cell size: 32 metres.
- Row spans: 53,362.
- Included cells: 433,083,140.
- Maximum public-code capacity: 439,400,000.
- Remaining capacity: 6,316,860.
- File size: 640,408 bytes.
- SHA-256: `2c1d6975258430574873180d795663894fe659d9f9fe03386e352b60a929488a`.
- The row-span ordering and resulting national indices are immutable.
