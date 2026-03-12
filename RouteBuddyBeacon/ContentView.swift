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
                    if segment.count > 1 {
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
                    
                    if let fix = locationManager.currentFix {
                        let message = fix.asBeaconMessage()
                        
                        VStack(spacing: 8) {
                            Text("Latitude: \(fix.latitude, specifier: "%.6f")")
                            Text("Longitude: \(fix.longitude, specifier: "%.6f")")
                            Text("Accuracy: \(fix.accuracyDescription)")
                            Text("Timestamp: \(fix.timestamp.formatted())")
                            Text("QuodWords: \(fix.quodWordsCode)")
                            Text("Device ID: \(message.deviceID)")
                            Text("Payload keys: \(message.payload.keys.sorted().joined(separator: ", "))")
                                .font(.footnote)
                                .multilineTextAlignment(.center)
                                .foregroundStyle(.secondary)
                            
                            if let speedKPH = fix.speedKPH {
                                Text("Speed: \(speedKPH, specifier: "%.1f") km/h")
                            } else {
                                Text("Speed: unavailable")
                            }
                            
                            Text("Course: \(fix.courseDescription)")
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
        guard autoFollow else {
            if let location = locationManager.lastLocation {
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
            return
        }
        
        if let fix = locationManager.currentFix,
           let speedKPH = fix.speedKPH,
           speedKPH > 5,
           fix.course != nil {
            cameraPosition = .userLocation(
                followsHeading: true,
                fallback: .automatic
            )
        } else {
            cameraPosition = .userLocation(
                followsHeading: false,
                fallback: .automatic
            )
        }
    }
}
    #Preview {
        ContentView()
    }
