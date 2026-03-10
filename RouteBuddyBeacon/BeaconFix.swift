import Foundation
import CoreLocation

struct BeaconFix {
    let coordinate: CLLocationCoordinate2D
    let horizontalAccuracy: Double
    let timestamp: Date
    let speed: Double?
    let course: Double?

    var latitude: Double {
        coordinate.latitude
    }

    var longitude: Double {
        coordinate.longitude
    }

    var speedKPH: Double? {
        guard let speed else { return nil }
        return speed * 3.6
    }

    var courseDescription: String {
        guard let course else { return "unavailable" }
        return String(format: "%.1f°", course)
    }

    var accuracyDescription: String {
        String(format: "%.1f m", horizontalAccuracy)
    }
    
    var payload: [String: Any] {
        [
            "lat": latitude,
            "lon": longitude,
            "accuracy": horizontalAccuracy,
            "timestamp": timestamp.timeIntervalSince1970,
            "speed": speed ?? -1,
            "course": course ?? -1
        ]
    }
    
    var debugDescription: String {
        """
        BeaconFix
          lat: \(latitude)
          lon: \(longitude)
          acc: \(horizontalAccuracy)m
          speed: \(speedKPH ?? 0) km/h
          course: \(course ?? 0)
        """
    }
    
    var quodWordsCode: String {
        QuodWordsEncoder.encode(self)
    }
    
    func asBeaconMessage(deviceID: String = "beacon-ios-dev") -> BeaconMessage {
        BeaconMessage(
            deviceID: deviceID,
            timestamp: timestamp,
            quodWordsCode: quodWordsCode,
            latitude: latitude,
            longitude: longitude,
            horizontalAccuracy: horizontalAccuracy,
            speed: speed,
            course: course
        )
    }
}
