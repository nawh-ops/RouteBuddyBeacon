
import Foundation
import CoreLocation
import Combine

enum RecordingState {
    case idle
    case recording
    case paused
}

@MainActor
final class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()

    @Published var authorizationStatus: CLAuthorizationStatus
    @Published var lastLocation: CLLocation?
    @Published var currentFix: BeaconFix?
    @Published var latitude: Double?
    @Published var longitude: Double?
    @Published var sessionStats = SessionStats()
    @Published var recordedLocations: [CLLocation] = []
    @Published var horizontalAccuracy: Double?
    @Published var timestamp: Date?
    @Published var speed: Double?
    @Published var course: Double?
    @Published var trackSegments: [[CLLocationCoordinate2D]] = []
    @Published var errorMessage: String?
    @Published var recordingState: RecordingState = .idle
    @Published var exportURLs: [URL] = []
    @Published var shouldShowShareSheet = false

    override init() {
        self.authorizationStatus = manager.authorizationStatus
        super.init()

        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.distanceFilter = kCLDistanceFilterNone
    }

    func requestLocationPermission() {
        manager.requestWhenInUseAuthorization()
    }

    func startUpdatingLocation() {
        guard CLLocationManager .locationServicesEnabled() else {
            errorMessage = "Location Services are disabled on this device."
            return
        }

        switch manager.authorizationStatus {
        case .notDetermined:
            requestLocationPermission()

        case .restricted, .denied:
            errorMessage = "Location access is denied. Please enable it in Settings."

        case .authorizedWhenInUse, .authorizedAlways:
            errorMessage = nil
            manager.startUpdatingLocation()

        @unknown default:
            errorMessage = "Unknown location authorization state."
        }
    }

    func stopUpdatingLocation() {
        manager.stopUpdatingLocation()
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {

          authorizationStatus = manager.authorizationStatus

          switch manager.authorizationStatus {

          case .authorizedWhenInUse, .authorizedAlways:
              errorMessage = nil
              manager.startUpdatingLocation()

          case .denied:
              errorMessage = "Location access denied."

          case .restricted:
              errorMessage = "Location access restricted."

          case .notDetermined:
              errorMessage = nil

          @unknown default:
              errorMessage = "Unknown location authorization state."
          }
        }


        func startRecording() {
            clearTrack()
            recordingState = .recording
            startUpdatingLocation()
            sessionStats.start()
            recordedLocations = []
        }

        func pauseRecording() {
            recordingState = .paused
            stopUpdatingLocation()
        }

        func resumeRecording() {
            recordingState = .recording
            startUpdatingLocation()
        }

    func stopRecording() {
        recordingState = .idle
        stopUpdatingLocation()

        var urls: [URL] = []

        if let gpxURL = exportGPX() {
            urls.append(gpxURL)
        }

        if let csvURL = exportCSV() {
            urls.append(csvURL)
        }

        if let quodWordsURL = exportQuodWordsSession() {
            urls.append(quodWordsURL)
        }

        exportURLs = urls

#if targetEnvironment(simulator)
shouldShowShareSheet = false
#else
if !exportURLs.isEmpty {
    shouldShowShareSheet = true
}
#endif

        sessionStats.stop()
    }

    private func exportGPX() -> URL? {
        
        guard !recordedLocations.isEmpty else {
            print("GPX EXPORT: no recorded locations")
            return nil
        }

        let gpxString = GPXExporter.generateGPX(from: recordedLocations)

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd_HH-mm-ss"

        let filename = "beacon-track-\(formatter.string(from: Date())).gpx"
        let url: URL

        #if targetEnvironment(simulator)
        let hostHome = ProcessInfo.processInfo.environment["SIMULATOR_HOST_HOME"] ?? NSHomeDirectory()
        let desktop = URL(fileURLWithPath: hostHome).appendingPathComponent("Desktop")
        url = desktop.appendingPathComponent(filename)
        #else
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        url = documents.appendingPathComponent(filename)
        #endif

        do {
            try gpxString.write(to: url, atomically: true, encoding: .utf8)
            print("GPX EXPORT SUCCESS: \(url.path)")
            return url
        } catch {
            print("GPX EXPORT FAILED: \(error.localizedDescription)")
            return nil
        }
    }

    private func exportCSV() -> URL? {
        
        guard !recordedLocations.isEmpty else {
            print("CSV EXPORT: no recorded locations")
            return nil
        }

        var csv = "lat,lon,time,speed,course,quodwords\n"
        let isoFormatter = ISO8601DateFormatter()

        for location in recordedLocations {
            let lat = location.coordinate.latitude
            let lon = location.coordinate.longitude
            let time = isoFormatter.string(from: location.timestamp)
            let speed = location.speed >= 0 ? location.speed : 0
            let course = location.course >= 0 ? location.course : 0

            let fix = BeaconFix(
                coordinate: location.coordinate,
                horizontalAccuracy: location.horizontalAccuracy,
                timestamp: location.timestamp,
                speed: location.speed >= 0 ? location.speed : nil,
                course: location.course >= 0 ? location.course : nil
            )

            let quodWordsCode = fix.quodWordsCode

            csv += "\(lat),\(lon),\(time),\(speed),\(course),\(quodWordsCode)\n"
        }

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd_HH-mm-ss"

        let filename = "beacon-track-\(formatter.string(from: Date())).csv"
        let url: URL

        #if targetEnvironment(simulator)
        let hostHome = ProcessInfo.processInfo.environment["SIMULATOR_HOST_HOME"] ?? NSHomeDirectory()
        let desktop = URL(fileURLWithPath: hostHome).appendingPathComponent("Desktop")
        url = desktop.appendingPathComponent(filename)
        #else
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        url = documents.appendingPathComponent(filename)
        #endif

        do {
            try csv.write(to: url, atomically: true, encoding: .utf8)
            print("CSV EXPORT SUCCESS: \(url.path)")
            return url
        } catch {
            print("CSV EXPORT FAILED: \(error.localizedDescription)")
            return nil
        }
    }

    private func exportQuodWordsSession() -> URL? {
        guard !recordedLocations.isEmpty else {
            print("QUODWORDS EXPORT: no recorded locations")
            return nil
        }

        let report = QuodWordsSessionExporter.generateSessionReport(from: recordedLocations)

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd_HH-mm-ss"

        let filename = "beacon-quodwords-session-\(formatter.string(from: Date())).txt"
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let url = documents.appendingPathComponent(filename)

        do {
            try report.write(to: url, atomically: true, encoding: .utf8)
            print("QUODWORDS EXPORT SUCCESS: \(url.path)")
            return url
        } catch {
            print("QUODWORDS EXPORT FAILED: \(error.localizedDescription)")
            return nil
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        if recordingState == .recording {
            sessionStats.addLocation(location)
            recordedLocations.append(location)
        }

        lastLocation = location
        latitude = location.coordinate.latitude
        longitude = location.coordinate.longitude
        horizontalAccuracy = location.horizontalAccuracy
        timestamp = location.timestamp
        

        speed = location.speed >= 0 ? location.speed : nil
        course = location.course >= 0 ? location.course : nil
        
        let fix = BeaconFix(
            coordinate: location.coordinate,
            horizontalAccuracy: location.horizontalAccuracy,
            timestamp: location.timestamp,
            speed: location.speed >= 0 ? location.speed : nil,
            course: location.course >= 0 ? location.course : nil
        )

        currentFix = fix
        
        let message = fix.asBeaconMessage()
        BeaconLogger.log(message)

        let coordinate = location.coordinate
        let accuracy = location.horizontalAccuracy

        // Reject obviously poor or invalid fixes.
        guard accuracy >= 0, accuracy <= 50 else {
            errorMessage = String(format: "Skipping low-quality fix (%.1f m).", accuracy)
            return
        }

        if trackSegments.isEmpty {
            trackSegments.append([coordinate])
        } else {
            guard var currentSegment = trackSegments.last else { return }

            if let previous = currentSegment.last {
                let previousLocation = CLLocation(latitude: previous.latitude, longitude: previous.longitude)
                let distance = location.distance(from: previousLocation)

                // Ignore tiny jitter.
                if distance <= 3 {
                    errorMessage = nil
                    return
                }

                // If the jump is too large, start a new segment instead of drawing
                // a fake straight line across the gap.
                if distance > 100 {
                    trackSegments.append([coordinate])
                } else {
                    currentSegment.append(coordinate)
                    trackSegments[trackSegments.count - 1] = currentSegment
                }
            } else {
                currentSegment.append(coordinate)
                trackSegments[trackSegments.count - 1] = currentSegment
            }
        }

        // Limit total stored points so the debug trail does not grow forever.
        let totalPoints = trackSegments.reduce(0) { $0 + $1.count }
        if totalPoints > 500 {
            while trackSegments.count > 1 &&
                  !(trackSegments.first?.isEmpty ?? true) &&
                  totalPointsOfSegments() > 500 {
                trackSegments.removeFirst()
            }
        }

        errorMessage = nil
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        errorMessage = error.localizedDescription
    }
    
    private func totalPointsOfSegments() -> Int {
        trackSegments.reduce(0) { $0 + $1.count }
    }
    
    func clearTrack() {
        trackSegments.removeAll()
    }
}
