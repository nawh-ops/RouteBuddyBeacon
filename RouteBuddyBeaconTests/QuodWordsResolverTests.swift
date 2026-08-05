import XCTest
import CoreLocation
@testable import RouteBuddyBeacon

final class QuodWordsResolverTests: XCTestCase {

    private let london = CLLocationCoordinate2D(
        latitude: 51.5074,
        longitude: -0.1278
    )

    func testResolvesPermanentFormalGBCode() throws {
        let formalCode = try QuodWords.encodeFormalCode(
            for: london
        )

        let resolved = QuodWordsResolver.resolve(formalCode)

        let coordinate = try XCTUnwrap(resolved)

        XCTAssertEqual(
            try QuodWords.encodeFormalCode(for: coordinate),
            formalCode
        )
    }

    func testResolvesPermanentNationalCode() throws {
        let original = try QuodWords.encodeGBCoordinate(london)
        let nationalCode = original.code.nationalCellCode

        let resolved = QuodWordsResolver.resolve(nationalCode)

        let coordinate = try XCTUnwrap(resolved)
        let roundTrip = try QuodWords.encodeGBCoordinate(coordinate)

        XCTAssertEqual(
            roundTrip.code.nationalCellCode,
            nationalCode
        )
    }

    func testResolvesLatitudeLongitude() throws {
        let resolved = QuodWordsResolver.resolve(
            "51.5074,-0.1278"
        )

        let coordinate = try XCTUnwrap(resolved)

        XCTAssertEqual(
            coordinate.latitude,
            51.5074,
            accuracy: 0.000_001
        )

        XCTAssertEqual(
            coordinate.longitude,
            -0.1278,
            accuracy: 0.000_001
        )
    }

    func testRejectsInvalidInput() {
        XCTAssertNil(
            QuodWordsResolver.resolve(
                "THIS-IS-NOT-A-LOCATION"
            )
        )
    }
}

extension QuodWordsResolverTests {

    private var legacyReference: CLLocationCoordinate2D {
        CLLocationCoordinate2D(
            latitude: 51.5074,
            longitude: -0.1278
        )
    }

    func testResolvesLegacyFormalCode() throws {
        let resolved = QuodWordsResolver.resolve(
            "GB-121-AAA00"
        )

        let coordinate = try XCTUnwrap(resolved)

        XCTAssertEqual(
            coordinate.latitude,
            51.64260689902982,
            accuracy: 0.000_000_001
        )

        XCTAssertEqual(
            coordinate.longitude,
            -0.4066449574278046,
            accuracy: 0.000_000_001
        )
    }

    func testResolvesLegacyShortCodeNearReference() throws {
        let resolved = QuodWordsResolver.resolve(
            "AAA00",
            near: legacyReference
        )

        let coordinate = try XCTUnwrap(resolved)

        XCTAssertEqual(
            coordinate.latitude,
            51.64260689902982,
            accuracy: 0.000_000_001
        )

        XCTAssertEqual(
            coordinate.longitude,
            -0.4066449574278046,
            accuracy: 0.000_000_001
        )
    }
}
