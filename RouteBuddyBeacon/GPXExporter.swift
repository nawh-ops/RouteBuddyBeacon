import Foundation
import CoreLocation

struct GPXExporter {

    
    static func generateGPX(from locations: [CLLocation]) -> String {
        
        let startTime = ISO8601DateFormatter().string(from: locations.first!.timestamp)
        let endTime = ISO8601DateFormatter().string(from: locations.last!.timestamp)
        
        var distanceMeters: Double = 0
        for i in 1..<locations.count {
            distanceMeters += locations[i].distance(from: locations[i-1])
        }
        
        let distanceKM = distanceMeters / 1000.0
        let durationSeconds = locations.last!.timestamp.timeIntervalSince(locations.first!.timestamp)
        let avgSpeedKPH = durationSeconds > 0 ? (distanceMeters / durationSeconds) * 3.6 : 0
        
        var gpx = """
        <?xml version="1.0" encoding="UTF-8"?>
        <gpx version="1.1" creator="RouteBuddy Beacon"
             xmlns="http://www.topografix.com/GPX/1/1">
 
        <metadata>
          <name>Beacon Session</name>
          <time>2026-03-14T17:24:15Z</time>
          <desc>
            End: 2026-03-14T17:36:10Z
            Distance: 1.342 km
            Duration: 420 seconds
            Avg Speed: 11.5 km/h
          </desc>
        </metadata>
 <desc>
 End: \(endTime)
 Distance: \(String(format: "%.3f", distanceKM)) km
 Duration: \(Int(durationSeconds)) seconds
 Avg Speed: \(String(format: "%.1f", avgSpeedKPH)) km/h
 </desc>
 </metadata>
 
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
