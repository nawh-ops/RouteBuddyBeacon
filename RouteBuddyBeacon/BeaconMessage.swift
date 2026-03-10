import Foundation

struct BeaconMessage {
    let deviceID: String
    let timestamp: Date
    let quodWordsCode: String
    let latitude: Double
    let longitude: Double
    let horizontalAccuracy: Double
    let speed: Double?
    let course: Double?

    var payload: [String: Any] {
        return [
            "device_id": deviceID,
            "timestamp": timestamp.timeIntervalSince1970,
            "quodwords": quodWordsCode,
            "lat": latitude,
            "lon": longitude,
            "accuracy": horizontalAccuracy,
            "speed": speed ?? -1.0,
            "course": course ?? -1.0
        ]
    }
        var json: String? {
            guard JSONSerialization.isValidJSONObject(payload),
                  let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted])
            else { return nil }

            return String(data: data, encoding: .utf8)
        }
    }
