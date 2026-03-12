import Foundation
import CoreLocation

struct GPXExporter {

    static func generateGPX(from locations: [CLLocation]) -> String {
        var gpx = """
        <?xml version="1.0" encoding="UTF-8"?>
        <gpx version="1.1" creator="RouteBuddy Beacon"
             xmlns="http://www.topografix.com/GPX/1/1">
        <trk>
        <name>RouteBuddy Beacon Track</name>
        <trkseg>
        """

        let formatter = ISO8601DateFormatter()

        for location in locations {
            let lat = location.coordinate.latitude
            let lon = location.coordinate.longitude
            let time = formatter.string(from: location.timestamp)

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
}
