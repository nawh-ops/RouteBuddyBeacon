import Foundation
import CoreLocation

struct QuodWordsEncoder {

    // MARK: - UK beta grid constants

    // UK beta origin. This is a simple deterministic engineering grid,
    // not yet the later land-only / polygon-optimised QuodWords zone model.
    private static let countryCode = "GB"
    private static let originLatitude = 49.5
    private static let originLongitude = -8.5

    // Approximate UK mid-latitude used for a simple equirectangular projection.
    // Good enough for beta testing the code structure and 30m cell behaviour.
    private static let projectionLatitude = 55.0

    private static let metersPerDegreeLatitude = 111_320.0
    private static var metersPerDegreeLongitude: Double {
        metersPerDegreeLatitude * cos(projectionLatitude * .pi / 180.0)
    }

    // LLLDD gives 1,757,600 possible values.
    // 1325 x 1325 = 1,755,625 cells, so it fits inside one LLLDD block.
    private static let cellSizeMeters = 30.0
    private static let cellsPerZoneSide = 1325
    private static var zoneSizeMeters: Double {
        Double(cellsPerZoneSide) * cellSizeMeters
    }

    // Covers the UK beta bounding rectangle from roughly -8.5 to +2.5 longitude.
    // Kept fixed so zone numbers are stable.
    private static let zoneColumnCount = 18

    // MARK: - Public encoding API

    static func encode(_ fix: BeaconFix) -> String {
        fullAreaCode(from: fix.coordinate)
    }

    static func shortCode(from coordinate: CLLocationCoordinate2D) -> String {
        let encoded = encodeCoordinate(coordinate)
        return encoded.areaBlock
    }

    static func fullAreaCode(from coordinate: CLLocationCoordinate2D) -> String {
        let encoded = encodeCoordinate(coordinate)
        return "QW-\(countryCode)-\(encoded.zoneString)-\(encoded.areaBlock)"
    }

    static func zoneCode(from coordinate: CLLocationCoordinate2D) -> String {
        let encoded = encodeCoordinate(coordinate)
        return "\(countryCode)-\(encoded.zoneString)"
    }

    // MARK: - Public decoding API

    static func decode(_ code: String) -> CLLocationCoordinate2D? {
        let cleaned = code
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .uppercased()
            .replacingOccurrences(of: " ", with: "")

        // Backward compatibility with old internal lat/lon wrapper.
        if let legacy = decodeLegacyLatLon(cleaned) {
            return legacy
        }

        // Accept QW-GB-123-VPN57 and GB-123-VPN57.
        let withoutPrefix: String
        if cleaned.hasPrefix("QW-") {
            withoutPrefix = String(cleaned.dropFirst(3))
        } else {
            withoutPrefix = cleaned
        }

        let parts = withoutPrefix.split(separator: "-").map(String.init)
        guard parts.count == 3 else {
            return nil
        }

        let country = parts[0]
        let zoneString = parts[1]
        let areaBlock = parts[2]

        guard country == countryCode else {
            return nil
        }

        guard let zoneNumber = Int(zoneString) else {
            return nil
        }

        return decodeAreaCode(zoneNumber: zoneNumber, areaBlock: areaBlock)
    }

    // MARK: - Core encoding

    private static func encodeCoordinate(_ coordinate: CLLocationCoordinate2D) -> EncodedQuodWordsArea {
        let xMeters = (coordinate.longitude - originLongitude) * metersPerDegreeLongitude
        let yMeters = (coordinate.latitude - originLatitude) * metersPerDegreeLatitude

        let safeX = max(0.0, xMeters)
        let safeY = max(0.0, yMeters)

        let zoneCol = Int(floor(safeX / zoneSizeMeters))
        let zoneRow = Int(floor(safeY / zoneSizeMeters))
        let zoneNumber = zoneRow * zoneColumnCount + zoneCol

        let zoneOriginX = Double(zoneCol) * zoneSizeMeters
        let zoneOriginY = Double(zoneRow) * zoneSizeMeters

        let localX = safeX - zoneOriginX
        let localY = safeY - zoneOriginY

        let cellCol = max(0, min(cellsPerZoneSide - 1, Int(floor(localX / cellSizeMeters))))
        let cellRow = max(0, min(cellsPerZoneSide - 1, Int(floor(localY / cellSizeMeters))))

        let cellIndex = cellRow * cellsPerZoneSide + cellCol
        let areaBlock = blockFromIndex(cellIndex)

        return EncodedQuodWordsArea(
            zoneNumber: zoneNumber,
            zoneString: String(format: "%03d", zoneNumber),
            areaBlock: areaBlock
        )
    }

    private static func decodeAreaCode(zoneNumber: Int, areaBlock: String) -> CLLocationCoordinate2D? {
        guard let cellIndex = indexFromBlock(areaBlock) else {
            return nil
        }

        let cellRow = cellIndex / cellsPerZoneSide
        let cellCol = cellIndex % cellsPerZoneSide

        guard cellRow >= 0,
              cellRow < cellsPerZoneSide,
              cellCol >= 0,
              cellCol < cellsPerZoneSide else {
            return nil
        }

        let zoneRow = zoneNumber / zoneColumnCount
        let zoneCol = zoneNumber % zoneColumnCount

        let zoneOriginX = Double(zoneCol) * zoneSizeMeters
        let zoneOriginY = Double(zoneRow) * zoneSizeMeters

        let cellCenterX = zoneOriginX + (Double(cellCol) + 0.5) * cellSizeMeters
        let cellCenterY = zoneOriginY + (Double(cellRow) + 0.5) * cellSizeMeters

        let longitude = originLongitude + (cellCenterX / metersPerDegreeLongitude)
        let latitude = originLatitude + (cellCenterY / metersPerDegreeLatitude)

        guard (-90.0...90.0).contains(latitude),
              (-180.0...180.0).contains(longitude) else {
            return nil
        }

        return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }

    // MARK: - LLLDD conversion

    private static func blockFromIndex(_ index: Int) -> String {
        let letterValue = index / 100
        let digitValue = index % 100

        let a = letterValue / (26 * 26)
        let b = (letterValue / 26) % 26
        let c = letterValue % 26

        return "\(letter(a))\(letter(b))\(letter(c))\(String(format: "%02d", digitValue))"
    }

    private static func indexFromBlock(_ block: String) -> Int? {
        let pattern = #"^[A-Z]{3}[0-9]{2}$"#
        guard block.range(of: pattern, options: .regularExpression) != nil else {
            return nil
        }

        let letters = Array(block.prefix(3))
        let digits = String(block.suffix(2))

        guard let a = letterValue(letters[0]),
              let b = letterValue(letters[1]),
              let c = letterValue(letters[2]),
              let digitValue = Int(digits) else {
            return nil
        }

        let letterValue = a * 26 * 26 + b * 26 + c
        let index = letterValue * 100 + digitValue

        guard index >= 0,
              index < cellsPerZoneSide * cellsPerZoneSide else {
            return nil
        }

        return index
    }

    private static func letter(_ value: Int) -> Character {
        Character(UnicodeScalar(65 + value)!)
    }

    private static func letterValue(_ character: Character) -> Int? {
        guard let ascii = character.asciiValue,
              ascii >= 65,
              ascii <= 90 else {
            return nil
        }

        return Int(ascii - 65)
    }

    // MARK: - Legacy support

    private static func decodeLegacyLatLon(_ code: String) -> CLLocationCoordinate2D? {
        guard code.hasPrefix("QW|") else {
            return nil
        }

        let parts = code.split(separator: "|", omittingEmptySubsequences: false)
        guard parts.count == 3 else {
            return nil
        }

        guard let latitude = Double(String(parts[1])),
              let longitude = Double(String(parts[2])) else {
            return nil
        }

        guard (-90.0...90.0).contains(latitude),
              (-180.0...180.0).contains(longitude) else {
            return nil
        }

        return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }

    private struct EncodedQuodWordsArea {
        let zoneNumber: Int
        let zoneString: String
        let areaBlock: String
    }
}
