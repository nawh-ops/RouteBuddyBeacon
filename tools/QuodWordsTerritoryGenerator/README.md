# QuodWords Territory Generator

Status: Provisional engineering tool

## Purpose

This offline tool will generate deterministic QuodWords territory resources from frozen geographic source data.

The first implementation targets the GB namespace, but the architecture is intended to support future territories worldwide through configuration rather than territory-specific rewrites.

The tool will:

1. load a frozen OpenStreetMap snapshot;
2. select qualifying territory land and inland water;
3. transform geometry into the configured projected coordinate system;
4. construct the approved marine coverage mask;
5. resolve neighbouring-territory overlaps;
6. apply the fixed QuodWords grid;
7. select valid cells using the approved centre-point rule;
8. merge valid cells into ordered row spans;
9. generate provisional national indices;
10. produce audit reports, maps, statistics and checksums.

## Current GB configuration

The provisional GB resource uses:

- territory code: `GB`;
- public grammar: `LLLDDDL`;
- formal grammar: `GB-LLLDDDL`;
- projection: `EPSG:3035`;
- grid origin: `(0, 0)`;
- base cell size: `32 m`;
- inclusion rule: cell centre covered by final mask;
- marine distance: `25 nautical miles`;
- geometry source: frozen OpenStreetMap snapshot;
- Northern Ireland included in the GB namespace;
- neighbouring namespaces reserved where appropriate.

All qualifying permanent GB land generates the 25 NM marine buffer regardless of area. Rockall is the configured non-buffer-generating exception.

The candidate island-area thresholds remain available only for geographic audit and comparison; they do not determine production buffer eligibility.

Required test outcomes include:

- Foula generates marine coverage;
- Fair Isle generates marine coverage;
- Rockall does not independently generate a 25 NM marine buffer.

## Current-code policy

This generator must not alter or replace the temporary Beacon mapper during the provisional phase.

Permanent public QuodWords indices must not be released until:

- geometry policy is approved;
- source data is frozen and archived;
- provisional coverage has passed geographic audit;
- capacity has been verified;
- row-span invariants have passed;
- binary resource format is approved;
- mapping-version policy is approved.

## Verification commands

Validate the territory configuration and require frozen source metadata:

```bash
~/miniforge3/bin/conda run -n quodwords-territory \
  python tools/QuodWordsTerritoryGenerator/src/validate_config.py \
  tools/QuodWordsTerritoryGenerator/config/GB.provisional.yaml \
  --require-frozen-source
```

Verify the actual frozen geographic source file against the configured filename and SHA-256 checksum:

```bash
~/miniforge3/bin/conda run -n quodwords-territory \
  python tools/QuodWordsTerritoryGenerator/src/verify_source.py \
  tools/QuodWordsTerritoryGenerator/config/GB.provisional.yaml \
  --input-directory \
  tools/QuodWordsTerritoryGenerator/input
```

Generate the provisional GB permanent-land candidate dataset:

```bash
~/miniforge3/bin/conda run -n quodwords-territory \
  python tools/QuodWordsTerritoryGenerator/src/select_gb_land.py \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/uk-boundary-only.geojson \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/island-candidates.geojson \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/gb-land-candidates.geojson
```

The generated land-candidate file is an ignored geographic-audit artifact. It is not a released QuodWords index and does not alter the temporary Beacon mapper.

Run the complete configured island-policy audit against the generated island dataset:

```bash
~/miniforge3/bin/conda run -n quodwords-territory \
  python tools/QuodWordsTerritoryGenerator/src/verify_island_policy.py \
  tools/QuodWordsTerritoryGenerator/config/GB.provisional.yaml \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/island-candidates.geojson
```

The combined command verifies the configured exception matches and the required outcomes for Foula, Fair Isle and Rockall. The lower-level `verify_marine_exceptions.py` and `verify_required_islands.py` commands remain available for diagnosis.

Run the complete automated test suite:

```bash
~/miniforge3/bin/conda run -n quodwords-territory \
  pytest -q tools/QuodWordsTerritoryGenerator/tests
```

## Directory structure

- `config/` — territory configuration files
- `src/` — generator source code
- `tests/` — generator and geometry tests
- `input/` — local source data; large source files should not be committed
- `output/` — generated provisional artefacts; generated files should not be committed unless explicitly approved

## Worldwide architecture

The generator is intended to support future territories through configuration of:

- territory identifier;
- governing OSM geometry;
- projection and shared grid origin;
- cell size and resource type;
- marine-buffer policy;
- neighbouring territories;
- acceptance-test catalogue.

The 32 m territory-base mapping is permanent once publicly released.

Future finer-resolution products must be separate, aligned refinement resources and must not renumber or replace the released 32 m territory mapping.
