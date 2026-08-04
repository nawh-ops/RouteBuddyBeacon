import CoreLocation
import XCTest
@testable import RouteBuddyBeacon

final class ETRS89LAEAProjectionTests: XCTestCase {
    private struct ReferenceVector {
        let name: String
        let longitude: Double
        let latitude: Double
        let expectedX: Double
        let expectedY: Double
    }

    private let referenceVectors = [
        ReferenceVector(
            name: "East Clandon",
            longitude: -0.480067,
            latitude: 51.252992,
            expectedX: 3_592_220.924102,
            expectedY: 3_179_287.513009
        ),
        ReferenceVector(
            name: "London",
            longitude: -0.1278,
            latitude: 51.5074,
            expectedX: 3_620_438.012102,
            expectedY: 3_203_903.360058
        ),
        ReferenceVector(
            name: "Edinburgh",
            longitude: -3.1883,
            latitude: 55.9533,
            expectedX: 3_501_984.832437,
            expectedY: 3_725_343.877057
        ),
        ReferenceVector(
            name: "Cardiff",
            longitude: -3.1791,
            latitude: 51.4816,
            expectedX: 3_411_207.057850,
            expectedY: 3_234_782.086052
        ),
        ReferenceVector(
            name: "Belfast",
            longitude: -5.9301,
            latitude: 54.5973,
            expectedX: 3_300_763.893963,
            expectedY: 3_612_229.441792
        ),
        ReferenceVector(
            name: "Lerwick",
            longitude: -1.1494,
            latitude: 60.1550,
            expectedX: 3_703_115.028701,
            expectedY: 4_165_893.410590
        ),
        ReferenceVector(
            name: "Hugh Town",
            longitude: -6.3170,
            latitude: 49.9140,
            expectedX: 3_160_015.575950,
            expectedY: 3_107_832.560481
        ),
    ]

    func testEPSGCode() {
        XCTAssertEqual(
            ETRS89LAEAProjection.epsgCode,
            3035
        )
    }

    func testForwardProjectionMatchesPROJReferenceVectors() {
        for vector in referenceVectors {
            let projected = ETRS89LAEAProjection.project(
                longitude: vector.longitude,
                latitude: vector.latitude
            )

            XCTAssertEqual(
                projected.x,
                vector.expectedX,
                accuracy: 0.001,
                "\(vector.name) easting differs"
            )

            XCTAssertEqual(
                projected.y,
                vector.expectedY,
                accuracy: 0.001,
                "\(vector.name) northing differs"
            )
        }
    }

    func testCoreLocationConvenienceMethod() {
        let projected = ETRS89LAEAProjection.project(
            CLLocationCoordinate2D(
                latitude: 51.252992,
                longitude: -0.480067
            )
        )

        XCTAssertEqual(
            projected.x,
            3_592_220.924102,
            accuracy: 0.001
        )

        XCTAssertEqual(
            projected.y,
            3_179_287.513009,
            accuracy: 0.001
        )
    }
}
