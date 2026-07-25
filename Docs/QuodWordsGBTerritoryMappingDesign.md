# QuodWords GB Territory Mapping Design

Status: Architecture specification  
Branch: `quodwords-gb-coverage`

## 1. Purpose

Replace the temporary rectangular GB mapper with a compact, deterministic
territory mapper that assigns QuodWords codes only to approved GB cells.

This document defines the architecture. It does not yet select the final
coastline dataset, projection or marine boundary.

## 2. Fixed public grammar

The national code grammar remains:

`LLLDDDL`

The formal GB code remains:

`GB-LLLDDDL`

The final suffix letter excludes `O`.

Total grammatical capacity:

`439,400,000` national codes.

The geographic mapper may use fewer than this capacity. Any grammatical code
whose index is greater than or equal to the valid GB cell count is invalid.

## 3. Fixed cell size

Base QuodWords cells are:

`32 m × 32 m`

Cell size is not changed by this work.

Altitude, speed, course and device type do not alter the cell code.

## 4. Territory meaning

The GB namespace includes:

- England;
- Scotland;
- Wales;
- Northern Ireland;
- associated GB islands represented by the approved source dataset;
- any separately approved coastal-water mask.

The GB namespace excludes:

- Republic of Ireland;
- Isle of Man;
- the Bailiwick of Jersey;
- the Bailiwick of Guernsey, including Alderney, Sark, Herm and associated islands;
- France;
- other foreign territory;
- open water outside the adopted GB marine mask.

No outside coordinate may be clamped into GB coverage.


## 4A. Outside-territory behaviour

A coordinate outside the active territory mask must not return a fabricated code.

The app should behave as follows:

- if the coordinate lies inside another supported territory, return that territory’s code;
- if the coordinate lies outside all supported territory masks, show:
  `No QuodWords code is available for this location.`;
- if the coordinate is invalid or the system cannot generate a code, show:
  `Unable to generate location code.`;
- strings such as `GB-INVALID` must not be presented as user-facing codes.


## 5. Grid model

The territory resource uses one projected coordinate system and one fixed
origin.

For any projected coordinate:

- `xIndex = floor((x - originX) / 32)`
- `yIndex = floor((y - originY) / 32)`

A grid cell is identified internally by:

- `xIndex`
- `yIndex`

This two-dimensional grid identity is separate from the compact national index.

## 6. Row-span representation

Valid cells are stored as horizontal spans grouped by row.

Each span contains:

- `yIndex`
- `startXIndex`
- `cellCount`
- `firstNationalIndex`

Example conceptual record:

    row: 120
    startX: 450
    count: 37
    firstNationalIndex: 92810

This represents 37 valid consecutive cells:

    x = 450 ... 486

Their compact national indices are:

    92810 ... 92846

Only valid territory cells appear in the resource.

## 7. Required ordering

Spans are ordered deterministically by:

1. increasing `yIndex`;
2. increasing `startXIndex` within each row.

National indices are assigned consecutively in that order.

For every span after the first:

    span.firstNationalIndex
    =
    previousSpan.firstNationalIndex
    + previousSpan.cellCount

The first span begins at national index `0`.

## 8. Encoding

Encoding a coordinate performs these steps:

1. reject invalid latitude or longitude;
2. project the coordinate;
3. calculate `xIndex` and `yIndex`;
4. find the row for `yIndex`;
5. find the span containing `xIndex`;
6. reject the coordinate if no span contains the cell;
7. calculate:

    nationalIndex
    =
    span.firstNationalIndex
    + (xIndex - span.startXIndex)

8. convert the national index to `LLLDDDL`;
9. return the territory, grid cell and code.

Encoding must never invent, clamp or substitute a nearby valid cell.

## 9. Decoding

Decoding a GB code performs these steps:

1. parse and validate the grammar;
2. convert `LLLDDDL` to its national index;
3. reject the index if it is greater than or equal to `validCellCount`;
4. locate the span whose national-index range contains the index;
5. calculate:

    xIndex
    =
    span.startXIndex
    + (nationalIndex - span.firstNationalIndex)

6. use the span’s `yIndex`;
7. calculate the projected centre of the 32 m cell;
8. inverse-project the centre to latitude and longitude.

Decode must return the centre of the encoded cell.

## 10. Search structures

The production resource should support efficient binary search.

Recommended runtime structures:

    struct QuodWordsRow {
        let yIndex: Int32
        let firstSpanIndex: Int32
        let spanCount: Int32
    }

    struct QuodWordsSpan {
        let startXIndex: Int32
        let cellCount: Int32
        let firstNationalIndex: Int64
    }

The resource also stores:

- `validCellCount`
- grid origin
- cell size
- projection identifier
- resource version
- resource checksum

The exact integer widths must be verified against final resource dimensions.

## 11. Two distinct searches

Coordinate-to-index encoding searches by:

    yIndex, then xIndex

Index-to-coordinate decoding searches by:

    firstNationalIndex

The implementation may provide a second index-ordered lookup table if profiling
shows that it is useful.

Correctness takes priority over premature optimisation.

## 12. Resource generation

The runtime app must not perform polygon processing.

An offline generation tool will:

1. load the approved territory geometry;
2. transform it into the approved projection;
3. apply any approved coastal-water construction;
4. determine which 32 m cells are valid;
5. merge consecutive valid cells into row spans;
6. assign compact national indices;
7. write the versioned runtime resource;
8. generate audit statistics and tests;
9. calculate a checksum.

The same generated resource must be usable by iOS, Android and web
implementations.

## 13. Inclusion rule

The exact rule for deciding whether a 32 m cell is included must be fixed before
resource generation.

Candidate rules include:

- cell centre lies inside the territory mask;
- cell intersects the territory mask;
- a defined minimum proportion of the cell lies inside the mask.

The selected rule must be deterministic and documented.

No implementation assumption is approved by this document yet.

## 14. Boundary stability

Once publicly released, the mapping must not silently change when a newer
coastline dataset becomes available.

Every released mapping resource therefore requires:

- a permanent version identifier;
- a checksum;
- archived source geometry;
- archived generation settings;
- reproducible generation tooling.

A revised territory resource would require an explicit compatibility and
migration decision.

## 15. Required invariants

Automated tests must prove:

- every valid cell has exactly one national index;
- every valid national index has exactly one cell;
- spans do not overlap;
- spans within a row are ordered;
- national-index ranges are continuous;
- `validCellCount <= 439,400,000`;
- every valid encoded code decodes to its original cell;
- every decoded valid code re-encodes to the same code;
- every index at or above `validCellCount` is rejected;
- coordinates outside all spans are rejected;
- no coordinate is clamped;
- the resource checksum matches the compiled expectation.

## 16. Separation from public grammar

The following functions are conceptually independent:

### Grammar layer

- validate `LLLDDDL`;
- convert national index to code;
- convert code to national index;
- parse territory prefix.

### Territory layer

- coordinate to valid compact national index;
- valid compact national index to cell centre;
- territory membership;
- resource version and checksum.

The existing grammar functions should remain unchanged unless tests prove a
specific defect.

## 17. Proposed Swift separation

Suggested future source files:

    QuodWords.swift
    QuodWordsCodeGrammar.swift
    QuodWordsGBTerritory.swift
    QuodWordsGBTerritoryResource.swift

The exact refactor will be performed only after the resource interface and tests
are agreed.

## 18. Decisions still required

Before implementation:

- projected coordinate reference system;
- fixed projected origin;
- authoritative coastline and island geometry;
- Northern Ireland geometry source;
- cell-inclusion rule;
- coastal-water distance and construction method;
- treatment of very small islands, rocks and tidal features;
- overlap rules between future neighbouring namespaces;
- binary resource format;
- public mapping version policy.

## 19. Current-code policy

The temporary rectangle mapper remains in place while this design is reviewed.

No temporary mapping constant will be edited merely to extend its northern
coverage.

The corrected mapper will be developed behind tests and substituted as one
controlled architectural change.


