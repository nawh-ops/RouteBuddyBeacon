import Foundation
import CoreLocation

struct QuodWordsResolver {
    
    static func resolve(_ input: String) -> CLLocationCoordinate2D? {
        let cleaned = clean(input)
        // 1. Try TAQ56 short code
        if let coord = parseTAQ56(cleaned) {
            return coord
        }
        
        // 2. Try full QuodWords format
        if let coord = QuodWordsEncoder.decode(cleaned) {
            return coord
        }
        
        // 3. Try lat/lon formats
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
    
    private static func parseTAQ56(_ input: String) -> CLLocationCoordinate2D? {
        let pattern = #"^[A-Z]{3}[0-9]{2}$"#

        guard input.range(of: pattern, options: .regularExpression) != nil else {
            return nil
        }

        let letters = Array(input.prefix(3))
        let digits = Array(input.suffix(2))

        func letterValue(_ c: Character) -> Int? {
            guard let ascii = c.asciiValue, ascii >= 65, ascii <= 90 else {
                return nil
            }
            return Int(ascii - 65)
        }

        guard
            let a = letterValue(letters[0]),
            let b = letterValue(letters[1]),
            let c = letterValue(letters[2]),
            let subRow = digits[0].wholeNumberValue,
            let subCol = digits[1].wholeNumberValue
        else {
            return nil
        }

        // LLL -> base-26 index: 0...(26^3 - 1)
        let cellIndex = a * 26 * 26 + b * 26 + c

        // UK bounding box
        let minLat = 49.5
        let maxLat = 59.0
        let minLon = -8.5
        let maxLon = 2.5

        // Near-square grid large enough to hold 17,576 cells
        let gridCols = 133
        let gridRows = 133
        let totalCells = 26 * 26 * 26

        guard cellIndex < totalCells else {
            return nil
        }

        let row = cellIndex / gridCols
        let col = cellIndex % gridCols

        guard row < gridRows, col < gridCols else {
            return nil
        }

        let majorLatSpan = (maxLat - minLat) / Double(gridRows)
        let majorLonSpan = (maxLon - minLon) / Double(gridCols)

        // Row 0 at north, increasing southwards
        let majorMaxLat = maxLat - (Double(row) * majorLatSpan)
        let majorMinLat = majorMaxLat - majorLatSpan

        let majorMinLon = minLon + (Double(col) * majorLonSpan)
        let majorMaxLon = majorMinLon + majorLonSpan

        // DD -> 10x10 sub-grid
        let subLatSpan = majorLatSpan / 10.0
        let subLonSpan = majorLonSpan / 10.0

        // First digit = sub-row (north to south)
        let subMaxLat = majorMaxLat - (Double(subRow) * subLatSpan)
        let subMinLat = subMaxLat - subLatSpan

        // Second digit = sub-col (west to east)
        let subMinLon = majorMinLon + (Double(subCol) * subLonSpan)
        let subMaxLon = subMinLon + subLonSpan

        let latitude = (subMinLat + subMaxLat) / 2.0
        let longitude = (subMinLon + subMaxLon) / 2.0

        return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}
