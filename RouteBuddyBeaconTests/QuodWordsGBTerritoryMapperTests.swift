import CoreLocation
import XCTest
@testable import RouteBuddyBeacon

final class QuodWordsGBTerritoryMapperTests: XCTestCase {
    private struct IncludedVector {
        let name: String
        let longitude: Double
        let latitude: Double
        let column: Int32
        let row: Int32
        let index: UInt64
    }

    private struct ExcludedVector {
        let name: String
        let longitude: Double
        let latitude: Double
        let column: Int32
        let row: Int32
    }

    private let includedVectors = [
        IncludedVector(
            name: "East Clandon",
            longitude: -0.480067,
            latitude: 51.252992,
            column: 112_256,
            row: 99_352,
            index: 52_506_428
        ),
        IncludedVector(
            name: "London",
            longitude: -0.127800,
            latitude: 51.507400,
            column: 113_138,
            row: 100_121,
            index: 64_336_645
        ),
        IncludedVector(
            name: "Edinburgh",
            longitude: -3.188300,
            latitude: 55.953300,
            column: 109_437,
            row: 116_416,
            index: 278_313_955
        ),
        IncludedVector(
            name: "Cardiff",
            longitude: -3.179100,
            latitude: 51.481600,
            column: 106_600,
            row: 101_086,
            index: 78_892_020
        ),
        IncludedVector(
            name: "Belfast",
            longitude: -5.930100,
            latitude: 54.597300,
            column: 103_148,
            row: 112_882,
            index: 234_006_392
        ),
        IncludedVector(
            name: "Lerwick",
            longitude: -1.149400,
            latitude: 60.155000,
            column: 115_722,
            row: 130_184,
            index: 422_106_344
        ),
        IncludedVector(
            name: "Hugh Town",
            longitude: -6.317000,
            latitude: 49.914000,
            column: 98_750,
            row: 97_119,
            index: 13_193_493
        ),
    ]

    private let excludedVectors = [
        ExcludedVector(
            name: "Dublin",
            longitude: -6.2603,
            latitude: 53.3498,
            column: 101_517,
            row: 108_786
        ),
        ExcludedVector(
            name: "Douglas",
            longitude: -4.4817,
            latitude: 54.1523,
            column: 105_685,
            row: 110_749
        ),
        ExcludedVector(
            name: "Calais",
            longitude: 1.8587,
            latitude: 50.9513,
            column: 117_195,
            row: 97_660
        ),
    ]

    private func loadMapper() throws
        -> QuodWordsGBTerritoryMapper
    {
        try QuodWordsGBTerritoryMapper.bundledGB(
            bundle: .main
        )
    }

    func testIncludedReferenceVectorsMatchPythonResource() throws {
        let mapper = try loadMapper()

        for vector in includedVectors {
            let coordinate = CLLocationCoordinate2D(
                latitude: vector.latitude,
                longitude: vector.longitude
            )

            let result = try mapper.map(coordinate)

            XCTAssertEqual(
                result.cell,
                QuodWordsTerritoryGridCell(
                    column: vector.column,
                    row: vector.row
                ),
                "\(vector.name) grid cell differs"
            )

            XCTAssertEqual(
                result.nationalIndex,
                vector.index,
                "\(vector.name) national index differs"
            )

            XCTAssertEqual(
                try mapper.resource.cell(
                    forIndex: result.nationalIndex
                ),
                result.cell,
                "\(vector.name) index round-trip differs"
            )
        }
    }

    func testExcludedReferenceVectorsAreRejected() throws {
        let mapper = try loadMapper()

        for vector in excludedVectors {
            let coordinate = CLLocationCoordinate2D(
                latitude: vector.latitude,
                longitude: vector.longitude
            )

            let projected =
                ETRS89LAEAProjection.project(coordinate)

            XCTAssertEqual(
                mapper.gridCell(for: projected),
                QuodWordsTerritoryGridCell(
                    column: vector.column,
                    row: vector.row
                ),
                "\(vector.name) grid cell differs"
            )

            XCTAssertThrowsError(
                try mapper.map(coordinate),
                "\(vector.name) unexpectedly mapped"
            ) { error in
                XCTAssertEqual(
                    error as? QuodWordsTerritoryResourceError,
                    .cellOutsideTerritory
                )
            }
        }
    }

    func testConvenienceIndexMethodMatchesFullResult() throws {
        let mapper = try loadMapper()

        let coordinate = CLLocationCoordinate2D(
            latitude: 51.252992,
            longitude: -0.480067
        )

        XCTAssertEqual(
            try mapper.nationalIndex(for: coordinate),
            52_506_428
        )
    }
}
