import XCTest
@testable import RouteBuddyBeacon

final class PermanentQuodWordsCodeTests: XCTestCase {
    private struct ReferenceVector {
        let name: String
        let index: Int
        let nationalCode: String
        let formalCode: String
    }

    private let referenceVectors = [
        ReferenceVector(
            name: "East Clandon",
            index: 52_506_428,
            nationalCode: "DCU257D",
            formalCode: "GB-DCU257D"
        ),
        ReferenceVector(
            name: "London",
            index: 64_336_645,
            nationalCode: "DUZ465V",
            formalCode: "GB-DUZ465V"
        ),
        ReferenceVector(
            name: "Edinburgh",
            index: 278_313_955,
            nationalCode: "QME558F",
            formalCode: "GB-QME558F"
        ),
        ReferenceVector(
            name: "Cardiff",
            index: 78_892_020,
            nationalCode: "ERJ680V",
            formalCode: "GB-ERJ680V"
        ),
        ReferenceVector(
            name: "Belfast",
            index: 234_006_392,
            nationalCode: "NWA255S",
            formalCode: "GB-NWA255S"
        ),
        ReferenceVector(
            name: "Lerwick",
            index: 422_106_344,
            nationalCode: "YZK253U",
            formalCode: "GB-YZK253U"
        ),
        ReferenceVector(
            name: "Hugh Town",
            index: 13_193_493,
            nationalCode: "AUH739T",
            formalCode: "GB-AUH739T"
        ),
    ]

    func testPermanentIndicesProduceExpectedCodes() throws {
        for vector in referenceVectors {
            let code = try QuodWords.nationalCellCode(
                from: vector.index
            )

            XCTAssertEqual(
                code,
                vector.nationalCode,
                "\(vector.name) national code differs"
            )

            XCTAssertEqual(
                code.count,
                7,
                "\(vector.name) code is not seven characters"
            )
        }
    }

    func testPermanentCodesMatchLLLDDDLGrammar() throws {
        for vector in referenceVectors {
            let code = try QuodWords.nationalCellCode(
                from: vector.index
            )

            let characters = Array(code)

            XCTAssertTrue(
                characters[0].isLetter
                    && characters[1].isLetter
                    && characters[2].isLetter,
                "\(vector.name) does not begin with three letters"
            )

            XCTAssertTrue(
                characters[3].isNumber
                    && characters[4].isNumber
                    && characters[5].isNumber,
                "\(vector.name) does not contain exactly three digits"
            )

            XCTAssertTrue(
                characters[6].isLetter,
                "\(vector.name) does not end with a letter"
            )

            XCTAssertNotEqual(
                characters[6],
                "O",
                "\(vector.name) uses forbidden final suffix O"
            )
        }
    }

    func testPermanentCodesRoundTripToOriginalIndices() throws {
        for vector in referenceVectors {
            let decodedIndex = try QuodWords.index(
                fromNationalCellCode: vector.nationalCode
            )

            XCTAssertEqual(
                decodedIndex,
                vector.index,
                "\(vector.name) index round-trip differs"
            )
        }
    }

    func testPermanentFormalCodesParseCorrectly() throws {
        for vector in referenceVectors {
            let parsed = try QuodWords.parse(
                vector.formalCode
            )

            XCTAssertEqual(
                parsed.territory,
                .gb,
                "\(vector.name) territory differs"
            )

            XCTAssertEqual(
                parsed.nationalCellCode,
                vector.nationalCode,
                "\(vector.name) parsed code differs"
            )

            XCTAssertEqual(
                parsed.formalCode,
                vector.formalCode,
                "\(vector.name) formal code differs"
            )
        }
    }
}
