import XCTest
@testable import RouteBuddyBeacon

final class QuodWordsTerritoryResourceTests: XCTestCase {
    private func loadGBResource() throws
        -> QuodWordsTerritoryResource
    {
        try QuodWordsTerritoryResource.bundledGB(
            bundle: .main
        )
    }

    func testBundledGBResourceMetadata() throws {
        let resource = try loadGBResource()
        let metadata = resource.metadata

        XCTAssertEqual(metadata.territoryCode, "GB")
        XCTAssertEqual(metadata.schemaVersion, 1)
        XCTAssertEqual(metadata.projectionEPSG, 3035)
        XCTAssertEqual(metadata.originX, 0)
        XCTAssertEqual(metadata.originY, 0)
        XCTAssertEqual(metadata.cellSizeMetres, 32)
        XCTAssertEqual(metadata.spanCount, 53_362)
        XCTAssertEqual(metadata.cellCount, 433_083_140)
        XCTAssertEqual(metadata.maximumCodeCount, 439_400_000)
        XCTAssertEqual(resource.spans.count, 53_362)
    }

    func testFirstNationalIndexRoundTrip() throws {
        let resource = try loadGBResource()

        let cell = try resource.cell(forIndex: 0)

        XCTAssertEqual(
            cell,
            QuodWordsTerritoryGridCell(
                column: 101_150,
                row: 95_749
            )
        )

        XCTAssertEqual(
            try resource.index(forCell: cell),
            0
        )
    }

    func testLastNationalIndexRoundTrip() throws {
        let resource = try loadGBResource()
        let lastIndex = resource.metadata.cellCount - 1

        let cell = try resource.cell(
            forIndex: lastIndex
        )

        XCTAssertEqual(
            cell,
            QuodWordsTerritoryGridCell(
                column: 116_602,
                row: 133_516
            )
        )

        XCTAssertEqual(
            try resource.index(forCell: cell),
            lastIndex
        )
    }

    func testIndexOutsideGeneratedRangeIsRejected() throws {
        let resource = try loadGBResource()

        XCTAssertThrowsError(
            try resource.cell(
                forIndex: resource.metadata.cellCount
            )
        ) { error in
            XCTAssertEqual(
                error as? QuodWordsTerritoryResourceError,
                .indexOutsideTerritory
            )
        }
    }

    func testCellBeforeFirstSpanIsRejected() throws {
        let resource = try loadGBResource()

        XCTAssertThrowsError(
            try resource.index(
                forCell: QuodWordsTerritoryGridCell(
                    column: 101_149,
                    row: 95_749
                )
            )
        ) { error in
            XCTAssertEqual(
                error as? QuodWordsTerritoryResourceError,
                .cellOutsideTerritory
            )
        }
    }
}
