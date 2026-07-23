# QuodWords V1 — GB Geographic Test-Point Catalogue

Status: Design fixture catalogue  
Branch: `quodwords-gb-coverage`  
Purpose: Define representative geographic expectations before changing the production QuodWords mapping.

## 1. Rules for this catalogue

These coordinates are fixed design fixtures.

They define what the QuodWords GB implementation is expected to do. They do not by themselves define legal, administrative or maritime boundaries.

Each test point has one of these expected results:

- `includedGB` — must generate a valid `GB-LLLDDDL` code.
- `excludedGB` — must not generate a GB code.
- `pendingBoundaryDecision` — outcome must not be coded until the territory dataset and boundary method are formally selected.

For every `includedGB` point, later automated tests must verify:

1. encoding succeeds;
2. the formal code begins with `GB-`;
3. the national component conforms to `LLLDDDL`;
4. decoding the generated code succeeds;
5. the decoded coordinate lies within the original 32 m cell;
6. encoding the decoded coordinate returns the same code.

For every `excludedGB` point, later automated tests must verify:

1. GB encoding fails with `coordinateOutsideTerritory`;
2. no string such as `GB-INVALID` is treated as a valid code;
3. no coordinate is clamped into GB coverage.

## 2. Uncontroversial GB land fixtures

These are deliberately well inside the intended GB territory, away from disputed or delicate boundaries.

| ID | Name | Latitude | Longitude | Expected result | Notes |
|---|---|---:|---:|---|---|
| GB-LAND-001 | East Clandon, Surrey | 51.252992 | -0.480067 | includedGB | Existing Beacon development reference point |
| GB-LAND-002 | Newport, Isle of Wight | 50.701000 | -1.291000 | includedGB | Principal Isle of Wight test |
| GB-LAND-003 | Land’s End, Cornwall | 50.066000 | -5.714000 | includedGB | Far south-west mainland |
| GB-LAND-004 | St Mary’s, Isles of Scilly | 49.914000 | -6.315000 | includedGB | Offshore inhabited UK island |
| GB-LAND-005 | Aberystwyth, west Wales | 52.415000 | -4.083000 | includedGB | West Wales |
| GB-LAND-006 | Caernarfon, north Wales | 53.140000 | -4.276000 | includedGB | North Wales |
| GB-LAND-007 | Newcastle upon Tyne | 54.978000 | -1.617000 | includedGB | Northern England |
| GB-LAND-008 | Edinburgh | 55.953000 | -3.189000 | includedGB | Southern Scotland |
| GB-LAND-009 | Fort William | 56.820000 | -5.105000 | includedGB | Mainland Highlands |
| GB-LAND-010 | Ullapool | 57.895000 | -5.160000 | includedGB | North-west Highlands |
| GB-LAND-011 | Stornoway, Lewis | 58.209000 | -6.389000 | includedGB | Outer Hebrides |
| GB-LAND-012 | Tobermory, Mull | 56.623000 | -6.069000 | includedGB | Inner Hebrides |
| GB-LAND-013 | Kirkwall, Orkney | 58.982000 | -2.960000 | includedGB | Orkney |
| GB-LAND-014 | Lerwick, Shetland | 60.155000 | -1.145000 | includedGB | Shetland |
| GB-LAND-015 | Belfast | 54.597000 | -5.930000 | includedGB | Northern Ireland remains within GB namespace |
| GB-LAND-016 | Enniskillen | 54.344000 | -7.638000 | includedGB | Western Northern Ireland |
| GB-LAND-017 | Lundy Island | 51.171000 | -4.667000 | includedGB | Small UK island |
| GB-LAND-018 | Holy Island, Northumberland | 55.680000 | -1.802000 | includedGB | Tidal UK island |
| GB-LAND-019 | Isle of Arran | 55.576000 | -5.150000 | includedGB | Scottish island |
| GB-LAND-020 | Barra, Outer Hebrides | 56.954000 | -7.488000 | includedGB | Western island coverage |

## 3. Non-GB territory fixtures

These points must not be encoded as GB. Their future namespaces are shown for design context only.

| ID | Name | Latitude | Longitude | Expected result | Intended namespace |
|---|---|---:|---:|---|---|
| NONGB-001 | Douglas, Isle of Man | 54.150000 | -4.482000 | excludedGB | IM |
| NONGB-002 | Dublin, Republic of Ireland | 53.349000 | -6.260000 | excludedGB | IE |
| NONGB-003 | Letterkenny, Republic of Ireland | 54.950000 | -7.734000 | excludedGB | IE |
| NONGB-004 | Saint Helier, Jersey | 49.186000 | -2.107000 | excludedGB | JE |
| NONGB-005 | Saint Peter Port, Guernsey | 49.455000 | -2.536000 | excludedGB | GG |
| NONGB-006 | Cherbourg, France | 49.638000 | -1.622000 | excludedGB | FR |
| NONGB-007 | Calais, France | 50.952000 | 1.858000 | excludedGB | FR |

## 4. Clearly outside all intended GB coverage

These fixtures are well beyond any reasonable GB land or coastal coding boundary.

| ID | Name | Latitude | Longitude | Expected result | Notes |
|---|---|---:|---:|---|---|
| OUTSIDE-001 | Central North Sea | 56.000000 | 3.000000 | excludedGB | Far east of Great Britain |
| OUTSIDE-002 | North Atlantic west of Hebrides | 58.000000 | -10.000000 | excludedGB | Well beyond intended coastal coverage |
| OUTSIDE-003 | Bay of Biscay | 47.000000 | -5.000000 | excludedGB | Far south of GB |
| OUTSIDE-004 | Norwegian Sea | 63.000000 | 0.000000 | excludedGB | North of Shetland and outside GB coverage |
| OUTSIDE-005 | Inland France | 49.000000 | 1.000000 | excludedGB | Foreign land territory |

## 5. Coastal-water fixtures

The product principle is to include a defined coastal marine zone around GB land and associated islands.

The exact buffer distance, coastline dataset, island handling and neighbouring-namespace division have not yet been fixed.

The following coordinates are therefore catalogue placeholders and must remain `pendingBoundaryDecision` until the generated GB territory mask exists.

| ID | Description | Latitude | Longitude | Expected result | Decision required |
|---|---|---:|---:|---|---|
| GB-SEA-001 | Near-shore water south of Isle of Wight | 50.540000 | -1.300000 | pendingBoundaryDecision | Confirm inside generated GB coastal mask |
| GB-SEA-002 | Near-shore water west of Cornwall | 50.070000 | -5.850000 | pendingBoundaryDecision | Confirm inside generated GB coastal mask |
| GB-SEA-003 | Near-shore water west of Lewis | 58.200000 | -6.700000 | pendingBoundaryDecision | Confirm island buffering |
| GB-SEA-004 | Near-shore water east of Shetland | 60.150000 | -0.850000 | pendingBoundaryDecision | Confirm northern island buffering |
| GB-SEA-005 | Near-shore water north of Northern Ireland | 55.250000 | -6.500000 | pendingBoundaryDecision | Confirm Northern Ireland coastal coverage |

## 6. Intended outer marine-limit fixtures

These must not be assigned final expected results merely by measuring a nominal number of nautical miles from an approximate shoreline point.

They must be generated from the selected coastline dataset and the formal QuodWords coverage-buffer process.

For each chosen coast section, the generated test set must eventually contain:

- one point clearly inside the coastal mask;
- one point close to the intended outer limit but inside;
- one point immediately outside;
- the expected distance and mask version;
- the processing-script version.

Required regions:

| ID group | Region | Status |
|---|---|---|
| GB-LIMIT-SOUTH-* | English Channel south of Great Britain | pendingBoundaryDecision |
| GB-LIMIT-WEST-* | Atlantic west of Cornwall or Wales | pendingBoundaryDecision |
| GB-LIMIT-NW-* | Atlantic west of the Hebrides | pendingBoundaryDecision |
| GB-LIMIT-NORTH-* | Waters north of Shetland | pendingBoundaryDecision |
| GB-LIMIT-NI-* | Waters around Northern Ireland | pendingBoundaryDecision |

## 7. GB and Ireland namespace-boundary fixtures

No artificial straight-line namespace division is approved by this catalogue.

Once GB and IE territory resources exist, paired points must be generated on opposing sides of the adopted coding boundary in at least these regions:

| ID group | Region | Expected namespaces |
|---|---|---|
| GB-IE-BOUNDARY-001A/B | North Channel | GB / IE or excluded marine area, according to adopted product mask |
| GB-IE-BOUNDARY-002A/B | Irish Sea | GB / IE or excluded marine area, according to adopted product mask |
| GB-IE-BOUNDARY-003A/B | Waters near Northern Ireland and Donegal | GB / IE |

All are currently:

`pendingBoundaryDecision`

## 8. GB and France namespace-boundary fixtures

Once GB and FR territory resources exist, paired points must be generated on opposing sides of the adopted coding boundary in the English Channel.

Required areas:

| ID group | Region | Expected namespaces |
|---|---|---|
| GB-FR-BOUNDARY-001A/B | Dover–Calais sector | GB / FR or excluded marine area, according to adopted product mask |
| GB-FR-BOUNDARY-002A/B | Central English Channel | GB / FR or excluded marine area, according to adopted product mask |
| GB-FR-BOUNDARY-003A/B | Channel Islands and Normandy sector | JE, GG, FR or GB according to the adopted product masks |

All are currently:

`pendingBoundaryDecision`

## 9. Special island rules to verify

The final GB territory resource must be checked for accidental omission of:

- Isle of Wight;
- Isles of Scilly;
- Lundy;
- Anglesey;
- Holy Island;
- Scottish Inner Hebrides;
- Scottish Outer Hebrides;
- Orkney;
- Shetland;
- smaller inhabited UK islands represented by the selected source dataset.

The presence of one island must not be treated as proof that all islands are included.

## 10. Altitude and vehicle independence

The expected namespace result must depend only on horizontal position.

The same latitude and longitude must return the same QuodWords code when used:

- on foot;
- in a road vehicle;
- aboard a vessel;
- in an aircraft;
- at different valid AMSL altitudes.

Altitude, vertical accuracy, speed and course may be retained as separate Beacon metadata, but must not alter the QuodWords cell code.

## 11. Web, iOS and Android parity

The fixed fixtures in this catalogue must ultimately produce identical results in:

- RouteBuddy Beacon for iOS;
- the future Android implementation;
- the QuodWords web encoder/decoder;
- any command-line dataset-generation or audit tool.

A platform-specific result is a failure.

## 12. Dataset-derived tests still required

After a coastline and territory dataset has been selected, the processing tools must automatically generate additional tests for:

- every disconnected GB land polygon above the adopted inclusion threshold;
- every row-span start and end;
- cells immediately before and after compact-index span boundaries;
- first valid GB compact index;
- last valid GB compact index;
- unassigned grammatical codes above the valid GB cell count;
- encode/decode round trips across the entire valid resource;
- random valid-cell samples;
- random invalid and outside-territory samples;
- resource checksum and version mismatch handling.

## 13. Compatibility fixtures

Before replacing the current mapping, record the provisional Build 11 codes for at least:

- East Clandon, Surrey;
- Newport, Isle of Wight.

These codes are reference information only.

They may be preserved where practical, but the corrected national architecture takes priority because no permanent public compatibility promise has yet been made.

Build 11 beta testers must be told that earlier QuodWords codes were provisional and should not be retained as permanent references.

## 14. Approval state

Approved now:

- GB includes England, Scotland, Wales and Northern Ireland.
- GB includes associated UK islands represented by the approved source dataset.
- Isle of Man is not GB.
- Republic of Ireland is not GB.
- Jersey is not GB.
- Guernsey is not GB.
- France is not GB.
- Altitude does not alter the QuodWords code.
- No outside coordinate may be silently clamped into coverage.

Not yet approved:

- final coastline dataset;
- precise coastal-buffer distance and construction method;
- treatment of extremely small rocks or features;
- marine divisions between neighbouring namespaces;
- final projection;
- final compact territory-index ordering;
- compatibility of provisional Build 11 codes.

No production mapping constants or encoder logic shall be changed until the pending design decisions required for implementation have been resolved.