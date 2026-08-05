import Foundation
import CoreLocation

struct QuodWordsResolver {

    static func resolve(_ input: String, near referenceCoordinate: CLLocationCoordinate2D? = nil) -> CLLocationCoordinate2D? {
        let cleaned = clean(input)

        // 1. Try new QuodWords v1 format, e.g.
        //    GB-IIN614R or IIN614R.
        if let coord = try? QuodWords.decodeCoordinate(from: cleaned, defaultTerritory: .gb) {
            return coord
        }

        // 2. Temporary fallback: try old QuodWords format, e.g.
        //    QW-GB-123-WXW37 or GB-123-WXW37.
        if let coord = LegacyQuodWordsDecoder.decode(cleaned) {
            return coord
        }

        // 3. Temporary fallback: try old bare local short code, e.g. WXW37,
        //    using current/live location as context.
        if let referenceCoordinate,
           let coord =
            LegacyQuodWordsDecoder.decodeShortCode(cleaned,
                                             near: referenceCoordinate) {
            return coord
        }

        // 4. Try lat/lon formats.
        if let coord = parseLatLon(cleaned) {
            return coord
        }

        return nil
    }

    private static func clean(_ input: String) -> String {
        return input
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "\n", with: "")
            .replacingOccurrences(of: " ", with: "")
            .uppercased()
    }

    private static func parseLatLon(_ input: String) -> CLLocationCoordinate2D? {
        let separators = [",", "|"]

        for sep in separators {
            let parts = input.split(separator: Character(sep))
            if parts.count == 2 {
                if let lat = Double(parts[0]),
                   let lon = Double(parts[1]),
                   (-90.0...90.0).contains(lat),
                   (-180.0...180.0).contains(lon) {
                    return CLLocationCoordinate2D(latitude: lat, longitude: lon)
                }
            }
        }

        return nil
    }
}
