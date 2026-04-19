import Foundation
import CoreLocation

struct QuodWordsEncoder {
    static func encode(_ fix: BeaconFix) -> String {
        let lat = String(format: "%.5f", fix.latitude)
        let lon = String(format: "%.5f", fix.longitude)
        return "QW|\(lat)|\(lon)"
    }

    static func decode(_ code: String) -> CLLocationCoordinate2D? {
        let trimmed = code
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .uppercased()

        guard trimmed.hasPrefix("QW|") else { return nil }

        let parts = trimmed.split(separator: "|", omittingEmptySubsequences: false)
        guard parts.count == 3 else { return nil }

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
}
