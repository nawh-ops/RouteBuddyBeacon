import Foundation
import CoreLocation

enum QuodWordsError: Error, Equatable {
    case unsupportedTerritory
    case invalidFormat
    case invalidCode
    case coordinateOutsideTerritory
}

enum QuodWordsTerritory: String, CaseIterable {
    case gb = "GB"
}

struct QuodWordsGridPoint: Equatable {
    let x: Double
    let y: Double
}

struct QuodWordsCell: Equatable {
    let territory: QuodWordsTerritory
    let xIndex: Int
    let yIndex: Int
    let index: Int
    let code: QuodWordsCode
}

struct QuodWordsCode: Equatable {
    let territory: QuodWordsTerritory
    let nationalCellCode: String

    var formalCode: String {
        "\(territory.rawValue)-\(nationalCellCode)"
    }
}

enum QuodWords {
    static let cellSizeMetres: Double = 32.0

    // LLLDDDL = 26 × 26 × 26 × 10 × 10 × 10 × 26
    static let nationalCellCapacity: Int = 456_976_000
    
    // Temporary GB v1 internal grid bounds.
    // These are deliberately generous WGS84 bounds for UK testing.
    static let gbMinLatitude: Double = 49.5
    static let gbMaxLatitude: Double = 61.0
    static let gbMinLongitude: Double = -8.7
    static let gbMaxLongitude: Double = 2.0

    // Approximate metres per degree near GB.
    // Good enough for the first code skeleton; replace later with a proper GB projection.
    static let gbOriginLatitude: Double = 49.5
    static let gbOriginLongitude: Double = -8.7
    static let metresPerDegreeLatitude: Double = 111_320.0
    static let metresPerDegreeLongitudeAtGB: Double = 70_000.0

    static let gbGridWidthCells: Int = 24_000

    static let letterAlphabet = Array("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    static let digitAlphabet = Array("0123456789")

    static func validateNationalCellCode(_ code: String) -> Bool {
        let upper = code.uppercased()

        guard upper.count == 7 else {
            return false
        }

        let chars = Array(upper)

        return isLetter(chars[0])
            && isLetter(chars[1])
            && isLetter(chars[2])
            && isDigit(chars[3])
            && isDigit(chars[4])
            && isDigit(chars[5])
            && isLetter(chars[6])
    }

    static func parse(_ input: String, defaultTerritory: QuodWordsTerritory? = nil) throws -> QuodWordsCode {
        let cleaned = input
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .uppercased()

        let parts = cleaned.split(separator: "-").map(String.init)

        if parts.count == 2 {
            guard let territory = QuodWordsTerritory(rawValue: parts[0]) else {
                throw QuodWordsError.unsupportedTerritory
            }

            let nationalCellCode = parts[1]

            guard validateNationalCellCode(nationalCellCode) else {
                throw QuodWordsError.invalidFormat
            }

            return QuodWordsCode(
                territory: territory,
                nationalCellCode: nationalCellCode
            )
        }

        if parts.count == 1, let territory = defaultTerritory {
            let nationalCellCode = parts[0]

            guard validateNationalCellCode(nationalCellCode) else {
                throw QuodWordsError.invalidFormat
            }

            return QuodWordsCode(
                territory: territory,
                nationalCellCode: nationalCellCode
            )
        }

        throw QuodWordsError.invalidFormat
    }

    static func nationalCellCode(from index: Int) throws -> String {
        guard index >= 0 && index < nationalCellCapacity else {
            throw QuodWordsError.invalidCode
        }

        var remaining = index

        let finalLetterIndex = remaining % 26
        remaining /= 26

        let d3 = remaining % 10
        remaining /= 10

        let d2 = remaining % 10
        remaining /= 10

        let d1 = remaining % 10
        remaining /= 10

        let l3 = remaining % 26
        remaining /= 26

        let l2 = remaining % 26
        remaining /= 26

        let l1 = remaining % 26

        return "\(letterAlphabet[l1])\(letterAlphabet[l2])\(letterAlphabet[l3])\(d1)\(d2)\(d3)\(letterAlphabet[finalLetterIndex])"
    }

    static func index(fromNationalCellCode code: String) throws -> Int {
        let upper = code.uppercased()

        guard validateNationalCellCode(upper) else {
            throw QuodWordsError.invalidFormat
        }

        let chars = Array(upper)

        guard
            let l1 = letterAlphabet.firstIndex(of: chars[0]),
            let l2 = letterAlphabet.firstIndex(of: chars[1]),
            let l3 = letterAlphabet.firstIndex(of: chars[2]),
            let d1 = digitAlphabet.firstIndex(of: chars[3]),
            let d2 = digitAlphabet.firstIndex(of: chars[4]),
            let d3 = digitAlphabet.firstIndex(of: chars[5]),
            let finalLetter = letterAlphabet.firstIndex(of: chars[6])
        else {
            throw QuodWordsError.invalidFormat
        }

        var index = l1
        index = index * 26 + l2
        index = index * 26 + l3
        index = index * 10 + d1
        index = index * 10 + d2
        index = index * 10 + d3
        index = index * 26 + finalLetter

        guard index >= 0 && index < nationalCellCapacity else {
            throw QuodWordsError.invalidCode
        }

        return index
    }

    private static func isLetter(_ character: Character) -> Bool {
        character >= "A" && character <= "Z"
    }

    private static func isDigit(_ character: Character) -> Bool {
        character >= "0" && character <= "9"
    }
    
    static func encodeFormalCode(for coordinate: CLLocationCoordinate2D) throws -> String {
        let cell = try encodeGBCoordinate(coordinate)
        return cell.code.formalCode
    }
    
    static func encodeGBCoordinate(_ coordinate: CLLocationCoordinate2D) throws -> QuodWordsCell {
        guard coordinate.latitude >= gbMinLatitude,
              coordinate.latitude <= gbMaxLatitude,
              coordinate.longitude >= gbMinLongitude,
              coordinate.longitude <= gbMaxLongitude
        else {
            throw QuodWordsError.coordinateOutsideTerritory
        }

        let point = gbGridPoint(from: coordinate)

        let xIndex = Int(floor(point.x / cellSizeMetres))
        let yIndex = Int(floor(point.y / cellSizeMetres))

        guard xIndex >= 0, yIndex >= 0 else {
            throw QuodWordsError.coordinateOutsideTerritory
        }

        let index = yIndex * gbGridWidthCells + xIndex

        guard index >= 0 && index < nationalCellCapacity else {
            throw QuodWordsError.coordinateOutsideTerritory
        }

        let nationalCode = try nationalCellCode(from: index)
        let qwCode = QuodWordsCode(territory: .gb, nationalCellCode: nationalCode)

        return QuodWordsCell(
            territory: .gb,
            xIndex: xIndex,
            yIndex: yIndex,
            index: index,
            code: qwCode
        )
    }

    static func decodeGBCode(_ code: QuodWordsCode) throws -> CLLocationCoordinate2D {
        guard code.territory == .gb else {
            throw QuodWordsError.unsupportedTerritory
        }

        let index = try self.index(fromNationalCellCode: code.nationalCellCode)

        let yIndex = index / gbGridWidthCells
        let xIndex = index % gbGridWidthCells

        let centreX = (Double(xIndex) + 0.5) * cellSizeMetres
        let centreY = (Double(yIndex) + 0.5) * cellSizeMetres

        return coordinateFromGBGridPoint(
            QuodWordsGridPoint(x: centreX, y: centreY)
        )
    }

    static func gbGridPoint(from coordinate: CLLocationCoordinate2D) -> QuodWordsGridPoint {
        let x = (coordinate.longitude - gbOriginLongitude) * metresPerDegreeLongitudeAtGB
        let y = (coordinate.latitude - gbOriginLatitude) * metresPerDegreeLatitude

        return QuodWordsGridPoint(x: x, y: y)
    }

    static func coordinateFromGBGridPoint(_ point: QuodWordsGridPoint) -> CLLocationCoordinate2D {
        let longitude = gbOriginLongitude + (point.x / metresPerDegreeLongitudeAtGB)
        let latitude = gbOriginLatitude + (point.y / metresPerDegreeLatitude)

        return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
    
    static func decodeCoordinate(from input: String, defaultTerritory: QuodWordsTerritory? = .gb) throws -> CLLocationCoordinate2D {
        let parsedCode = try parse(input, defaultTerritory: defaultTerritory)
        return try decodeGBCode(parsedCode)
    }
    
    static func debugSelfTest() {
        do {
            let testIndices = [
                0,
                1,
                25,
                26,
                999,
                1_000,
                123_456_789,
                nationalCellCapacity - 1
            ]

            print("----- QuodWords self-test -----")

            for index in testIndices {
                let code = try nationalCellCode(from: index)
                let decodedIndex = try self.index(fromNationalCellCode: code)

                print("\(index) -> \(code) -> \(decodedIndex)")

                assert(index == decodedIndex, "Round-trip failed for \(index)")
            }

            let parsedFormal = try parse("GB-ABC123D")
            print("Parsed formal:", parsedFormal.formalCode)

            let parsedShort = try parse("ABC123D", defaultTerritory: .gb)
            print("Parsed short with GB context:", parsedShort.formalCode)

            let testCoordinate = CLLocationCoordinate2D(
                latitude: 51.252992,
                longitude: -0.480067
            )

            let encodedCell = try encodeGBCoordinate(testCoordinate)
            let decodedCentre = try decodeGBCode(encodedCell.code)

            print("Encoded coordinate:", encodedCell.code.formalCode)
            print("Cell index:", encodedCell.index)
            print("Cell x/y:", encodedCell.xIndex, encodedCell.yIndex)
            print("Decoded centre:", decodedCentre.latitude, decodedCentre.longitude)
            
            let decodedFromFormal = try decodeCoordinate(from: encodedCell.code.formalCode)
            let decodedFromShort = try decodeCoordinate(from: encodedCell.code.nationalCellCode)

            print("Decoded from formal:", decodedFromFormal.latitude, decodedFromFormal.longitude)
            print("Decoded from short:", decodedFromShort.latitude, decodedFromShort.longitude)
            
            print("----- QuodWords self-test passed -----")
        } catch {
            print("QuodWords self-test failed:", error)
        }
    }
}
