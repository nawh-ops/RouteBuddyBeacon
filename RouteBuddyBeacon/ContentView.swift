import SwiftUI
import CoreLocation
import MapKit

struct ContentView: View {
    @StateObject private var locationManager = LocationManager()

    @State private var cameraPosition: MapCameraPosition = .automatic
    @State private var autoFollow = true

    var body: some View {
        VStack(spacing: 0) {
            Map(position: $cameraPosition, interactionModes: .all) {
                ForEach(Array(locationManager.trackSegments.enumerated()), id: \.offset) { _, segment in
                    if !segment.isEmpty {
                        MapPolyline(coordinates: segment)
                            .stroke(.blue, lineWidth: 4)
                    }
                }

                if let location = locationManager.lastLocation {
                    Marker("You", coordinate: location.coordinate)
                }
            }
            .mapStyle(.standard(elevation: .realistic))
            .frame(height: 320)
            .onAppear {
                updateCameraForFollowMode()
            }
            .onChange(of: autoFollow) {
                updateCameraForFollowMode()
            }
            .onChange(of: locationManager.lastLocation) {
                if autoFollow {
                    updateCameraForFollowMode()
                }
            }

            ScrollView {
                VStack(spacing: 16) {
                    Text("RouteBuddy Beacon")
                        .font(.largeTitle)
                        .fontWeight(.bold)

                    Toggle("Auto-Follow", isOn: $autoFollow)
                        .font(.headline)
                        .padding(.horizontal)

                    Group {
                        switch locationManager.authorizationStatus {
                        case .notDetermined:
                            Text("Location permission not requested yet.")
                        case .restricted:
                            Text("Location access is restricted.")
                        case .denied:
                            Text("Location access denied.")
                        case .authorizedWhenInUse, .authorizedAlways:
                            Text("Location access granted.")
                        @unknown default:
                            Text("Unknown authorization state.")
                        }
                    }
                    .multilineTextAlignment(.center)

                    if let lat = locationManager.latitude,
                       let lon = locationManager.longitude {
                        VStack(spacing: 8) {
                            Text("Latitude: \(lat, specifier: "%.6f")")
                            Text("Longitude: \(lon, specifier: "%.6f")")

                            if let accuracy = locationManager.horizontalAccuracy {
                                Text("Accuracy: \(accuracy, specifier: "%.1f") m")
                            }

                            if let time = locationManager.timestamp {
                                Text("Timestamp: \(time.formatted())")
                            }

                            if let speed = locationManager.speed {
                                Text("Speed: \(speed * 3.6, specifier: "%.1f") km/h")
                            } else {
                                Text("Speed: unavailable")
                            }

                            if let course = locationManager.course {
                                Text("Course: \(course, specifier: "%.1f")°")
                            } else {
                                Text("Course: unavailable")
                            }
                        }
                        .font(.title3)
                    } else {
                        Text("Waiting for location...")
                            .foregroundStyle(.secondary)
                    }

                    if let errorMessage = locationManager.errorMessage {
                        Text(errorMessage)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                    }

                    HStack(spacing: 12) {
                        Button("Request Permission") {
                            locationManager.requestLocationPermission()
                        }
                        .buttonStyle(.borderedProminent)

                        Button("Start Location") {
                            locationManager.clearTrack()
                            locationManager.startUpdatingLocation()
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding()
            }
        }
    }

    private func updateCameraForFollowMode() {
        if autoFollow {
            cameraPosition = .userLocation(
                followsHeading: true,
                fallback: .automatic
            )
        } else if let location = locationManager.lastLocation {
            cameraPosition = .region(
                MKCoordinateRegion(
                    center: location.coordinate,
                    span: MKCoordinateSpan(
                        latitudeDelta: 0.01,
                        longitudeDelta: 0.01
                    )
                )
            )
        }
    }
}

#Preview {
    ContentView()
}
