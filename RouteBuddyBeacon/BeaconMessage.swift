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
            "timestamp": Int(timestamp.timeIntervalSince1970),
            "quodwords": quodWordsCode,
            "lat": formattedString(latitude, places: 6),
            "lon": formattedString(longitude, places: 6),
            "accuracy": formattedString(horizontalAccuracy, places: 1),
            "speed": speed.map { formattedString($0, places: 2) } ?? "-1.0",
            "course": course.map { formattedString($0, places: 1) } ?? "-1.0"
        ]
    }

    var json: String? {
        guard JSONSerialization.isValidJSONObject(payload),
              let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted, .sortedKeys])
        else { return nil }

        return String(data: data, encoding: .utf8)
    }

    private func rounded(_ value: Double, places: Int) -> Double {
        let divisor = pow(10.0, Double(places))
        return (value * divisor).rounded() / divisor
    }
    private func formattedString(_ value: Double, places: Int) -> String {
        String(format: "%.\(places)f", value)
    }
}
