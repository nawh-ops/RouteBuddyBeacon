import Foundation

struct QuodWordsEncoder {
    static func encode(_ fix: BeaconFix) -> String {
        let lat = String(format: "%.5f", fix.latitude)
        let lon = String(format: "%.5f", fix.longitude)

        return "QW-\(lat)-\(lon)"
            .replacingOccurrences(of: ".", with: "_")
            .replacingOccurrences(of: "-", with: "M")
    }
}
