import Foundation
import CoreLocation

struct QuodWordsSessionExporter {

    static func generateSessionReport(from locations: [CLLocation]) -> String {
        guard !locations.isEmpty else {
            return "RouteBuddy Beacon QuodWords Session\n\nNo recorded locations."
        }

        let orderedCodes = locations.map { location in
            let fix = BeaconFix(
                coordinate: location.coordinate,
                horizontalAccuracy: location.horizontalAccuracy,
                timestamp: location.timestamp,
                speed: location.speed >= 0 ? location.speed : nil,
                course: location.course >= 0 ? location.course : nil
            )
            return QuodWordsEncoder.encode(fix)
        }

        let uniqueCodes = Array(Set(orderedCodes)).sorted()

        var hitCounts: [String: Int] = [:]
        for code in orderedCodes {
            hitCounts[code, default: 0] += 1
        }

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        let startTime = formatter.string(from: locations.first!.timestamp)
        let endTime = formatter.string(from: locations.last!.timestamp)

        var report = """
        RouteBuddy Beacon QuodWords Session

        Start: \(startTime)
        End: \(endTime)
        Total Points: \(locations.count)

        Ordered Cells:
        """

        for code in orderedCodes {
            report += "\n\(code)"
        }

        report += "\n\nUnique Cells Visited:\n"

        for code in uniqueCodes {
            report += "\(code)\n"
        }

        report += "\nCell Hit Counts:\n"

        for code in uniqueCodes {
            let count = hitCounts[code, default: 0]
            report += "\(code) = \(count)\n"
        }

        return report
    }
}
