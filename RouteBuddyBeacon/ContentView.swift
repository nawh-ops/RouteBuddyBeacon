import SwiftUI
import CoreLocation
import MapKit
import UIKit

struct ContentView: View {
    @StateObject private var locationManager = LocationManager()
    @State private var showDebug = false
    @State private var cameraPosition: MapCameraPosition = .automatic
    @State private var autoFollow = true
    @State private var showCopiedToast = false

    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                Map(position: $cameraPosition, interactionModes: .all) {
                    if locationManager.recordedLocations.count > 1 {
                        MapPolyline(
                            coordinates: locationManager.recordedLocations.map { $0.coordinate }
                        )
                        .stroke(.blue, lineWidth: 4)
                    }

                    if let location = locationManager.lastLocation {
                        Marker("You", coordinate: location.coordinate)
                    }
                }
                .frame(height: 260)
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
                            VStack(spacing: 8) {
                                Text("QuodWords: \(fix.quodWordsCode)")
                                    .font(.headline)
                                    .onTapGesture {
                                        UIPasteboard.general.string = fix.quodWordsCode
                                     

                                        let generator = UIImpactFeedbackGenerator(style: .light)
                                        generator.prepare()
                                        generator.impactOccurred()

                                        withAnimation {
                                            showCopiedToast = true
                                        }

                                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) {
                                            withAnimation {
                                                showCopiedToast = false
                                            }
                                        }
                                    }
                                ShareLink(item: fix.quodWordsCode) {
                                        Label("Share QuodWords", systemImage: "square.and.arrow.up")
                                    }

                                if let speedKPH = fix.speedKPH {
                                    Text("Speed: \(speedKPH, specifier: "%.1f") km/h")
                                } else {
                                    Text("Speed: unavailable")
                                }

                                Text("Course: \(fix.courseDescription)")

                                DisclosureGroup("Debug Information", isExpanded: $showDebug) {
                                    VStack(spacing: 6) {
                                        Text("Latitude: \(fix.latitude, specifier: "%.6f")")
                                        Text("Longitude: \(fix.longitude, specifier: "%.6f")")
                                        Text("Accuracy: \(fix.accuracyDescription)")
                                        Text("Timestamp: \(fix.timestamp.formatted())")
                                        Text("Device ID: \(fix.asBeaconMessage().deviceID)")

                                        Text("Payload keys: \(fix.asBeaconMessage().payload.keys.sorted().joined(separator: ", "))")
                                            .font(.footnote)
                                            .multilineTextAlignment(.center)
                                            .foregroundStyle(.secondary)
                                    }
                                    .font(.caption)
                                }
                                .padding(.top, 6)
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

                        VStack(spacing: 6) {
                            Text("Session Stats")
                                .font(.headline)

                            Text("Distance: \(locationManager.sessionStats.distanceKM, specifier: "%.3f") km")
                            Text("Points: \(locationManager.sessionStats.pointCount)")
                            Text("Unique Cells: \(locationManager.sessionStats.uniqueCellCount)")
                                .foregroundStyle(.secondary)
                            Text("Duration: \(formatDuration(locationManager.sessionStats.duration))")
                            Text("Avg Speed: \(locationManager.sessionStats.averageSpeedKPH, specifier: "%.1f") km/h")
                        }
                        .font(.subheadline)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))

                        VStack(spacing: 12) {
                            Text("Recording state: \(recordingStateText)")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)

                            HStack(spacing: 12) {
                                Button("Request Permission") {
                                    locationManager.requestLocationPermission()
                                }
                                .buttonStyle(.borderedProminent)

                                switch locationManager.recordingState {
                                case .idle:
                                    Button("Start Recording") {
                                        locationManager.startRecording()
                                    }
                                    .buttonStyle(.bordered)

                                case .recording:
                                    Button("Pause") {
                                        locationManager.pauseRecording()
                                    }
                                    .buttonStyle(.bordered)

                                    Button("Stop") {
                                        locationManager.stopRecording()
                                    }
                                    .buttonStyle(.borderedProminent)

                                case .paused:
                                    Button("Resume") {
                                        locationManager.resumeRecording()
                                    }
                                    .buttonStyle(.bordered)

                                    Button("Stop") {
                                        locationManager.stopRecording()
                                    }
                                    .buttonStyle(.borderedProminent)
                                }
                            }
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
                        }
                        .padding()
                    }
                }
            }

            if showCopiedToast {
                VStack {
                    Spacer()

                    Text("Copied")
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.black.opacity(0.8), in: Capsule())
                        .shadow(radius: 4)
                        .padding(.bottom, 40)
                }
                .transition(.opacity)
            }
        }
        .sheet(isPresented: $locationManager.shouldShowShareSheet, onDismiss: {
            locationManager.exportURLs.removeAll()
        }) {
            ShareSheet(items: locationManager.exportURLs)
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

    private func formatDuration(_ seconds: TimeInterval) -> String {
        let totalSeconds = Int(seconds)

        let hours = totalSeconds / 3600
        let minutes = (totalSeconds % 3600) / 60
        let secs = totalSeconds % 60

        if hours > 0 {
            return String(format: "%02d:%02d:%02d", hours, minutes, secs)
        } else {
            return String(format: "%02d:%02d", minutes, secs)
        }
    }

    private var recordingStateText: String {
        switch locationManager.recordingState {
        case .idle:
            return "Idle"
        case .recording:
            return "Recording"
        case .paused:
            return "Paused"
        }
    }
}

#Preview {
    ContentView()
}
