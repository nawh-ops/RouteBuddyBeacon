import Foundation
import CoreLocation

struct QuodWordsEncoder {
    static func encode(_ fix: BeaconFix) -> String {
        let lat = String(format: "%.5f", fix.latitude)
        let lon = String(format: "%.5f", fix.longitude)

        return "QW-\(lat)-\(lon)"
            .replacingOccurrences(of: ".", with: "_")
            .replacingOccurrences(of: "-", with: "M")
    }

    static func decode(_ code: String) -> CLLocationCoordinate2D? {
        let trimmed = code
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .uppercased()

        let pattern = #"^QW(M?)(\d+_\d{5})M(M?)(\d+_\d{5})$"#

        guard let regex = try? NSRegularExpression(pattern: pattern) else {
            return nil
        }

        let range = NSRange(trimmed.startIndex..<trimmed.endIndex, in: trimmed)
        guard let match = regex.firstMatch(in: trimmed, options: [], range: range),
              match.numberOfRanges == 5,
              let latSignRange = Range(match.range(at: 1), in: trimmed),
              let latValueRange = Range(match.range(at: 2), in: trimmed),
              let lonSignRange = Range(match.range(at: 3), in: trimmed),
              let lonValueRange = Range(match.range(at: 4), in: trimmed) else {
            return nil
        }

        let latIsNegative = !trimmed[latSignRange].isEmpty
        let lonIsNegative = !trimmed[lonSignRange].isEmpty

        let latString = trimmed[latValueRange].replacingOccurrences(of: "_", with: ".")
        let lonString = trimmed[lonValueRange].replacingOccurrences(of: "_", with: ".")

        guard var latitude = Double(latString),
              var longitude = Double(lonString) else {
            return nil
        }

        if latIsNegative { latitude *= -1 }
        if lonIsNegative { longitude *= -1 }

        guard (-90.0...90.0).contains(latitude),
              (-180.0...180.0).contains(longitude) else {
            return nil
        }

        return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}
