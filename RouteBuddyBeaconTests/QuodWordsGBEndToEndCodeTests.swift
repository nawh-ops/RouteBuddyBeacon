import CoreLocation
import XCTest
@testable import RouteBuddyBeacon

final class QuodWordsGBEndToEndCodeTests: XCTestCase {
    private struct ReferenceVector {
        let name: String
        let longitude: Double
        let latitude: Double
        let index: UInt64
        let nationalCode: String
        let formalCode: String
    }

    private let referenceVectors = [
        ReferenceVector(
            name: "East Clandon",
            longitude: -0.480067,
            latitude: 51.252992,
            index: 52_506_428,
            nationalCode: "DCU257D",
            formalCode: "GB-DCU257D"
        ),
        ReferenceVector(
            name: "London",
            longitude: -0.127800,
            latitude: 51.507400,
            index: 64_336_645,
            nationalCode: "DUZ465V",
            formalCode: "GB-DUZ465V"
        ),
        ReferenceVector(
            name: "Edinburgh",
            longitude: -3.188300,
            latitude: 55.953300,
            index: 278_313_955,
            nationalCode: "QME558F",
            formalCode: "GB-QME558F"
        ),
        ReferenceVector(
            name: "Cardiff",
            longitude: -3.179100,
            latitude: 51.481600,
            index: 78_892_020,
            nationalCode: "ERJ680V",
            formalCode: "GB-ERJ680V"
        ),
        ReferenceVector(
            name: "Belfast",
            longitude: -5.930100,
            latitude: 54.597300,
            index: 234_006_392,
            nationalCode: "NWA255S",
            formalCode: "GB-NWA255S"
        ),
        ReferenceVector(
            name: "Lerwick",
            longitude: -1.149400,
            latitude: 60.155000,
            index: 422_106_344,
            nationalCode: "YZK253U",
            formalCode: "GB-YZK253U"
        ),
        ReferenceVector(
            name: "Hugh Town",
            longitude: -6.317000,
            latitude: 49.914000,
            index: 13_193_493,
            nationalCode: "AUH739T",
            formalCode: "GB-AUH739T"
        ),
    ]

    private func loadMapper() throws
        -> QuodWordsGBTerritoryMapper
    {
        try QuodWordsGBTerritoryMapper.bundledGB(
            bundle: .main
        )
    }

    func testCoordinatesProducePermanentGBQuodWordsCodes()
        throws
    {
        let mapper = try loadMapper()

        for vector in referenceVectors {
            let coordinate = CLLocationCoordinate2D(
                latitude: vector.latitude,
                longitude: vector.longitude
            )

            let territoryResult = try mapper.map(
                coordinate
            )

            let code = try mapper.quodWordsCode(
                for: coordinate
            )

            XCTAssertEqual(
                territoryResult.nationalIndex,
                vector.index,
                "\(vector.name) index differs"
            )

            XCTAssertEqual(
                code.territory,
                .gb,
                "\(vector.name) territory differs"
            )

            XCTAssertEqual(
                code.nationalCellCode,
                vector.nationalCode,
                "\(vector.name) national code differs"
            )

            XCTAssertEqual(
                code.formalCode,
                vector.formalCode,
                "\(vector.name) formal code differs"
            )
        }
    }

    func testNationalAndFormalConvenienceMethods() throws {
        let mapper = try loadMapper()

        let coordinate = CLLocationCoordinate2D(
            latitude: 51.252992,
            longitude: -0.480067
        )

        XCTAssertEqual(
            try mapper.nationalCode(
                for: coordinate
            ),
            "DCU257D"
        )

        XCTAssertEqual(
            try mapper.formalCode(
                for: coordinate
            ),
            "GB-DCU257D"
        )
    }

    func testForeignLocationsRemainRejected() throws {
        let mapper = try loadMapper()

        let locations = [
            CLLocationCoordinate2D(
                latitude: 53.3498,
                longitude: -6.2603
            ),
            CLLocationCoordinate2D(
                latitude: 54.1523,
                longitude: -4.4817
            ),
            CLLocationCoordinate2D(
                latitude: 50.9513,
                longitude: 1.8587
            ),
        ]

        for coordinate in locations {
            XCTAssertThrowsError(
                try mapper.quodWordsCode(
                    for: coordinate
                )
            ) { error in
                XCTAssertEqual(
                    error as?
                        QuodWordsTerritoryResourceError,
                    .cellOutsideTerritory
                )
            }
        }
    }
}
