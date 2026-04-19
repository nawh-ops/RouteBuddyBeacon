import Foundation
import CoreLocation

struct QuodWordsResolver {
    
    static func resolve(_ input: String) -> CLLocationCoordinate2D? {
        let cleaned = clean(input)
        
        // 1. Try full QuodWords format
        if let coord = QuodWordsEncoder.decode(cleaned) {
            return coord
        }
        
        // 2. Try lat/lon formats
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
