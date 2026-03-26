import Foundation
import CoreLocation

struct GPXExporter {
    static func generateGPX(from locations: [CLLocation]) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]

        let startTime = locations.first?.timestamp ?? Date()
        let endTime = locations.last?.timestamp ?? startTime

        let durationSeconds = max(0, endTime.timeIntervalSince(startTime))
        let distanceMeters = totalDistance(from: locations)
        let distanceKM = distanceMeters / 1000.0
        let avgSpeedKPH = durationSeconds > 0 ? (distanceMeters / durationSeconds) * 3.6 : 0.0

        var gpx = """
        <?xml version="1.0" encoding="UTF-8"?>
        <gpx version="1.1" creator="RouteBuddy Beacon"
             xmlns="http://www.topografix.com/GPX/1/1"
             xmlns:beacon="https://routebuddy.com/beacon/gpx">

          <metadata>
            <name>Beacon Session</name>
            <time>\(formatter.string(from: startTime))</time>
            <desc>End=\(formatter.string(from: endTime)); DistanceKM=\(String(format: "%.3f", distanceKM)); DurationSec=\(Int(durationSeconds)); AvgSpeedKPH=\(String(format: "%.1f", avgSpeedKPH))</desc>
          </metadata>

          <trk>
            <name>RouteBuddy Beacon Track</name>
            <trkseg>

        """

        for location in locations {
            let lat = location.coordinate.latitude
            let lon = location.coordinate.longitude
            let time = formatter.string(from: location.timestamp)

            let fix = BeaconFix(
                coordinate: location.coordinate,
                horizontalAccuracy: location.horizontalAccuracy,
                timestamp: location.timestamp,
                speed: location.speed >= 0 ? location.speed : nil,
                course: location.course >= 0 ? location.course : nil
            )

            let quodWordsCode = fix.quodWordsCode

            gpx += """
                <trkpt lat="\(lat)" lon="\(lon)">
            """

            if location.altitude != 0 {
                gpx += """
                      <ele>\(location.altitude)</ele>
                """
            }

            gpx += """
                      <time>\(time)</time>
            """

            if location.speed >= 0 {
                gpx += """
                      <speed>\(location.speed)</speed>
                """
            }

            if location.course >= 0 {
                gpx += """
                      <course>\(location.course)</course>
                """
            }

            gpx += """
                      <cmt>QW: \(quodWordsCode)</cmt>
                      <extensions>
                        <beacon:quodwords>\(quodWordsCode)</beacon:quodwords>
                      </extensions>
                </trkpt>

            """
        }

        gpx += """
            </trkseg>
          </trk>
        </gpx>
        """

        return gpx
    }

    private static func totalDistance(from locations: [CLLocation]) -> CLLocationDistance {
        guard locations.count > 1 else { return 0 }

        var total: CLLocationDistance = 0
        for index in 1..<locations.count {
            total += locations[index].distance(from: locations[index - 1])
        }
        return total
    }
}
