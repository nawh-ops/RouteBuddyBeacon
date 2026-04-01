import Foundation
import CoreLocation

struct QuodWordsSpacingConfig {
    let walkingThreshold: Double = 50.0      // metres
    let cyclingThreshold: Double = 75.0      // metres
    let drivingThreshold: Double = 120.0     // metres
    
    let walkingSpeedUpperBound: Double = 1.5 // m/s   (~5.4 km/h)
    let cyclingSpeedUpperBound: Double = 6.0 // m/s   (~21.6 km/h)
    
    let maxAcceptedHorizontalAccuracy: Double = 20.0 // metres
    let minEmitTimeGap: TimeInterval = 5.0           // seconds
    let maxReasonableSpeed: Double = 40.0            // m/s (~144 km/h)
    let fallbackSpeedWhenUnavailable: Double = 1.0   // m/s
}

final class QuodWordsAnnotationController {
    
    private let config = QuodWordsSpacingConfig()
    
    /// Last location that triggered a QuodWords emission.
    private var lastEmittedLocation: CLLocation?
    
    /// Timestamp of the last emission.
    private var lastEmitDate: Date?
    
    /// Call this for each accepted live location update.
    /// Returns true when this point should receive a QuodWords annotation.
    func shouldEmitQuodWords(for location: CLLocation) -> Bool {
        
        guard isLocationUsable(location) else {
            return false
        }
        
        // Always emit first valid point.
        guard let lastEmittedLocation else {
            registerEmission(at: location)
            return true
        }
        
        // Optional anti-spam guard for rapid duplicate/jitter updates.
        if let lastEmitDate,
           location.timestamp.timeIntervalSince(lastEmitDate) < config.minEmitTimeGap {
            return false
        }
        
        let safeSpeed = effectiveSpeed(from: location)
        let threshold = spacingThreshold(for: safeSpeed)
        let distanceFromLastEmit = location.distance(from: lastEmittedLocation)
        
        guard distanceFromLastEmit >= threshold else {
            return false
        }
        
        registerEmission(at: location)
        return true
    }
    
    /// Reset between recording sessions if needed.
    func reset() {
        lastEmittedLocation = nil
        lastEmitDate = nil
    }
    
    // MARK: - Helpers
    
    private func isLocationUsable(_ location: CLLocation) -> Bool {
        guard location.horizontalAccuracy >= 0 else { return false }
        guard location.horizontalAccuracy <= config.maxAcceptedHorizontalAccuracy else { return false }
        return true
    }
    
    private func effectiveSpeed(from location: CLLocation) -> Double {
        let rawSpeed = location.speed
        
        // CoreLocation uses -1 when speed is invalid/unavailable.
        let speed = rawSpeed >= 0 ? rawSpeed : config.fallbackSpeedWhenUnavailable
        
        // Clamp absurd GPS spikes.
        return max(0, min(speed, config.maxReasonableSpeed))
    }
    
    private func spacingThreshold(for speed: Double) -> Double {
        if speed < config.walkingSpeedUpperBound {
            return config.walkingThreshold
        } else if speed < config.cyclingSpeedUpperBound {
            return config.cyclingThreshold
        } else {
            return config.drivingThreshold
        }
    }
    
    private func registerEmission(at location: CLLocation) {
        lastEmittedLocation = location
        lastEmitDate = location.timestamp
    }
}

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
        
        let annotationController = QuodWordsAnnotationController()
        
        for location in locations {
            let lat = location.coordinate.latitude
            let lon = location.coordinate.longitude
            let time = formatter.string(from: location.timestamp)
            
            let shouldAnnotateQuodWords = annotationController.shouldEmitQuodWords(for: location)
            
            let fix = BeaconFix(
                coordinate: location.coordinate,
                horizontalAccuracy: location.horizontalAccuracy,
                timestamp: location.timestamp,
                speed: location.speed >= 0 ? location.speed : nil,
                course: location.course >= 0 ? location.course : nil
            )
            
            let quodWordsCode = fix.quodWordsCode
            
            let nameLine = shouldAnnotateQuodWords
            ? "  <name>\(quodWordsCode)</name>\n"
            : ""
            
            let commentLine = shouldAnnotateQuodWords
            ? "  <cmt>QW: \(quodWordsCode)</cmt>\n"
            : ""
            
            let extensionsLine = shouldAnnotateQuodWords
            ? """
              <extensions>
                <beacon:quodwords>\(quodWordsCode)</beacon:quodwords>
              </extensions>\n
              """
            : ""
            
            let eleLine = location.altitude != 0
            ? "  <ele>\(location.altitude)</ele>\n"
            : ""
            
            let speedLine = location.speed >= 0
            ? "  <speed>\(location.speed)</speed>\n"
            : ""
            
            let courseLine = location.course >= 0
            ? "  <course>\(location.course)</course>\n"
            : ""
            
            let trackPoint = """
            <trkpt lat="\(lat)" lon="\(lon)">
            \(eleLine)  <time>\(time)</time>
            \(speedLine)\(courseLine)\(nameLine)\(commentLine)\(extensionsLine)</trkpt>

            """
            
            gpx += trackPoint
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
