import XCTest
import CoreLocation
@testable import RouteBuddyBeacon

final class RouteBuddyBeaconTests: XCTestCase {

    func testNationalCodeValidationAcceptsValidCode() {
        XCTAssertTrue(
            QuodWords.validateNationalCellCode("ABC123D")
        )
    }

    func testNationalCodeValidationRejectsSuffixO() {
        XCTAssertFalse(
            QuodWords.validateNationalCellCode("ABC123O")
        )
    }

    func testIndexCodeRoundTrip() throws {
        let indices = [
            0,
            1,
            25,
            26,
            999,
            1_000,
            123_456_789,
            QuodWords.nationalCellCapacity - 1
        ]

        for index in indices {
            let code = try QuodWords.nationalCellCode(from: index)
            let decodedIndex = try QuodWords.index(
                fromNationalCellCode: code
            )

            XCTAssertEqual(decodedIndex, index)
        }
    }

    func testFormalCodeParsing() throws {
        let parsed = try QuodWords.parse("GB-ABC123D")

        XCTAssertEqual(parsed.territory.rawValue, "GB")
        XCTAssertEqual(parsed.nationalCellCode, "ABC123D")
        XCTAssertEqual(parsed.formalCode, "GB-ABC123D")
    }

    func testShortCodeParsingWithGBContext() throws {
        let parsed = try QuodWords.parse(
            "ABC123D",
            defaultTerritory: .gb
        )

        XCTAssertEqual(parsed.territory.rawValue, "GB")
        XCTAssertEqual(parsed.nationalCellCode, "ABC123D")
    }

    func testEastClandonCurrentMapperRoundTrip() throws {
        let coordinate = CLLocationCoordinate2D(
            latitude: 51.252992,
            longitude: -0.480067
        )

        let cell = try QuodWords.encodeGBCoordinate(coordinate)
        let decoded = try QuodWords.decodeGBCode(cell.code)
        let reencoded = try QuodWords.encodeGBCoordinate(decoded)

        XCTAssertEqual(
            reencoded.code.formalCode,
            cell.code.formalCode
        )
    }

    func testSandownCurrentMapperRoundTrip() throws {
        let coordinate = CLLocationCoordinate2D(
            latitude: 50.6560,
            longitude: -1.1530
        )

        let cell = try QuodWords.encodeGBCoordinate(coordinate)
        let decoded = try QuodWords.decodeGBCode(cell.code)
        let reencoded = try QuodWords.encodeGBCoordinate(decoded)

        XCTAssertEqual(
            reencoded.code.formalCode,
            cell.code.formalCode
        )
    }
}
