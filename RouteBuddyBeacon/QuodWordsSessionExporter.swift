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

        let totalPoints = locations.count

        var distanceMeters: Double = 0
        for index in 1..<locations.count {
            distanceMeters += locations[index].distance(from: locations[index - 1])
        }

        let distanceKM = distanceMeters / 1000.0
        let durationSeconds = locations.last!.timestamp.timeIntervalSince(locations.first!.timestamp)
        let averageSpeedKPH = durationSeconds > 0 ? (distanceMeters / durationSeconds) * 3.6 : 0

        var report = """
        RouteBuddy Beacon QuodWords Session

        Start: \(startTime)
        End: \(endTime)
        Total Points: \(totalPoints)
        Distance: \(String(format: "%.3f", distanceKM)) km
        Duration: \(formatDuration(durationSeconds))
        Average Speed: \(String(format: "%.1f", averageSpeedKPH)) km/h

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

    private static func formatDuration(_ seconds: TimeInterval) -> String {
        let totalSeconds = Int(seconds)

        let hours = totalSeconds / 3600
        let minutes = (totalSeconds % 3600) / 60
        let secs = totalSeconds % 60

        if hours > 0 {
            return String(format: "%02d:%02d:%02d", hours, minutes, secs)
        } else {
            return String(format: "%02d:%02d", minutes, secs)
        }
    }
}
