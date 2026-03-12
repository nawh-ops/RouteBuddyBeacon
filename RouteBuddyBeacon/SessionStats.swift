import Foundation
import CoreLocation
import Combine

class SessionStats: ObservableObject {

    @Published var distanceMeters: Double = 0
    @Published var pointCount: Int = 0
    @Published var startTime: Date?

    private var lastLocation: CLLocation?

    func start() {
        distanceMeters = 0
        pointCount = 0
        startTime = Date()
        lastLocation = nil
    }

    func stop() {
        lastLocation = nil
    }

    func addLocation(_ location: CLLocation) {
        pointCount += 1

        if let last = lastLocation {
            distanceMeters += location.distance(from: last)
        }

        lastLocation = location
    }

    var duration: TimeInterval {
        guard let start = startTime else { return 0 }
        return Date().timeIntervalSince(start)
    }

    var distanceKM: Double {
        distanceMeters / 1000
    }
}
