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

Verify all actual frozen geographic source files against their configured filenames and SHA-256 checksums:

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

Validate the generated GB permanent-land candidate dataset:

```bash
~/miniforge3/bin/conda run -n quodwords-territory \
  python tools/QuodWordsTerritoryGenerator/src/validate_gb_land.py \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/gb-land-candidates.geojson
```

Build the five-territory foreign-land dataset from the exported boundary GeoJSON files:

```bash
~/miniforge3/bin/conda run --no-capture-output \
  -n quodwords-territory \
  python tools/QuodWordsTerritoryGenerator/src/build_gb_foreign_land.py \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/metropolitan-france-boundary.geojson \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/channel-islands-boundaries-complete.geojson \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/ireland-isle-of-man-boundaries.geojson \
  --output tools/QuodWordsTerritoryGenerator/output/geographic-audit/gb-foreign-land.geojson
```

The builder requires and writes exactly five neighbouring territories in deterministic order: FR, GG, JE, IE and IM.

After generating the GB coverage mask, validate the key real-world geographic checks:

```bash
~/miniforge3/bin/conda run --no-capture-output \
  -n quodwords-territory \
  python tools/QuodWordsTerritoryGenerator/src/validate_gb_coverage_geography.py \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/gb-coverage-mask.geojson
```

The validator confirms that Letterkenny and Calais are excluded while retained marine coverage remains present in the English Channel and Irish Sea near Anglesey.
Generate the provisional GB permanent-land plus 25 NM marine coverage mask:

```bash
~/miniforge3/bin/conda run --no-capture-output \
  -n quodwords-territory \
  python tools/QuodWordsTerritoryGenerator/src/generate_gb_coverage_mask.py \
  tools/QuodWordsTerritoryGenerator/config/GB.provisional.yaml \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/gb-land-candidates.geojson \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/gb-land-plus-25nm-coverage-mask.geojson \
  --foreign-land-dataset \
  tools/QuodWordsTerritoryGenerator/output/geographic-audit/gb-foreign-land.geojson
```

The generated mask is an ignored geographic-audit artefact in EPSG:3035. It combines permanent GB land with the configured 46,300 m marine buffer. Rockall remains covered as permanent land but does not independently generate a marine buffer.
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

## Phase 7 Beacon mapper substitution checkpoint

Beacon's production QuodWords encoding path now uses the permanent GB territory mapper:

```text
GPS
→ EPSG:3035
→ 32 m territory cell
→ immutable national index
→ LLLDDDL
→ GB-LLLDDDL
```

`QuodWordsEncoder.swift` now contains only permanent production encoding.

The former 30 m beta mapper has been removed from the production encoder. Its decoding logic is retained separately in `LegacyQuodWordsDecoder.swift` solely for compatibility with previously issued beta codes.

`QuodWordsResolver.swift` resolves inputs in this order:

1. permanent national or formal GB QuodWords code;
2. legacy formal beta code;
3. legacy local beta code near a reference coordinate;
4. latitude and longitude input.

Verification completed on 5 August 2026:

- full Swift test suite passed;
- six QuodWords resolver tests passed;
- Python territory-generator suite: 223 passed;
- simulator round trip passed for `IPA151I`;
- simulator formal-code round trip passed for `GB-IPA151I`;
- legacy compatibility lookup passed for `GB-121-AAA00`.

The controlled substitution of Beacon's temporary live mapper is complete at code, automated-test and simulator level.

### Phase 7 out-of-coverage handling

Beacon now treats coordinates outside the permanent GB QuodWords territory resource as unavailable rather than exposing `INVALID` or `GB-INVALID`.

For an out-of-coverage location:

- the live code display shows `Outside QuodWords coverage`;
- Send My Location, Copy, Spell and Speak are disabled;
- Navigate to Me remains available through the Apple Maps coordinate link;
- its message reports `Unavailable outside coverage` instead of including an invalid QuodWords code.

This behaviour was verified in the iPhone 17 Pro simulator using Paris coordinates and then rechecked after returning to a valid UK location.

### Phase 8 frozen GB resource reproducibility

The frozen GB territory resource can be regenerated as a candidate without
modifying either the approved release resource or Beacon's bundled copy:

```bash
~/miniforge3/bin/conda run --no-capture-output \
  -n quodwords-territory \
  python \
  tools/QuodWordsTerritoryGenerator/src/build_gb_territory_resource.py



Default input:

```text
tools/QuodWordsTerritoryGenerator/release/GB/gb-coverage-mask.geojson
```

Default candidate output:

```text
tools/QuodWordsTerritoryGenerator/output/reproducibility/GB.candidate.qwtr
```

Verified on 5 August 2026:

- row spans: 53,362;
- included cells: 433,083,140;
- maximum public-code count: 439,400,000;
- file size: 640,408 bytes;
- SHA-256: `2c1d6975258430574873180d795663894fe659d9f9fe03386e352b60a929488a`;
- the regenerated candidate was byte-for-byte identical to `release/GB/GB.qwtr`.

The builder writes to the candidate output by default and does not alter the frozen release resource.

Clean-checkout verification completed on 5 August 2026:

- repository freshly cloned from `quodwords-gb-coverage`;
- builder executed using the declared `quodwords-territory` Conda environment;
- regenerated candidate checksum matched the frozen release resource;
- byte-for-byte result: `CLEAN CHECKOUT: IDENTICAL`.

Phase 8 automated verification completed on 5 August 2026:

- Python territory-generator suite: 223 passed;
- complete Swift test suite executed on the iPhone 17 Pro simulator;
- xcodebuild exit status: 0;
- result: `PHASE 8 SWIFT TESTS: PASSED`.
