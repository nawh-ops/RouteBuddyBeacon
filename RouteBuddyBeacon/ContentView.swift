import SwiftUI
import CoreLocation
import MapKit
import UIKit

struct ContentView: View {
    @State private var pasteStatusMessage: String? = nil
    @State private var emergencyPhoneNumber: String = "07974919020"
    @StateObject private var locationManager = LocationManager()
    @State private var showDebug = false
    @State private var cameraPosition: MapCameraPosition = .region(
        MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: 52.5, longitude: -1.5),
            span: MKCoordinateSpan(latitudeDelta: 3.0, longitudeDelta: 3.0)
        )
    )
    @State private var autoFollow = true
    @State private var showCopiedToast = false
    @State private var pastedCoordinate: CLLocationCoordinate2D?
    @State private var manualInput: String = ""
    @FocusState private var manualInputFocused: Bool
    @State private var showPhoneticCode = false
    
    let showAdvanced = false
    let showRecordingUI = false
    
    private var currentGridRegion: MKCoordinateRegion {
        MKCoordinateRegion(
            center: locationManager.currentFix?.coordinate
                ?? CLLocationCoordinate2D(latitude: 52.5, longitude: -1.5),
            span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
        )
    }

    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                ZStack {
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
                    
                    MapGridOverlay(region: currentGridRegion)
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
                    VStack(alignment: .center, spacing: 16) {
                        Text("RouteBuddy\nBeacon")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .multilineTextAlignment(.center)
                        
                        if let fix = locationManager.currentFix {
                            VStack(spacing: 8) {
                                VStack(spacing: 6) {
                                    Text("Your Location")
                                        .font(.system(size: 20, weight: .semibold))
                                        .foregroundStyle(.primary)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                    
                                    Text(QuodWordsResolver.encodeTAQ56(from: fix.coordinate))
                                        .font(.system(size: 50, weight: .heavy, design: .monospaced))
                                        .padding(.vertical, 6)
                                        .contentShape(Rectangle())
                                        .onTapGesture {
                                            let code = QuodWordsResolver.encodeTAQ56(from: fix.coordinate)
                                            UIPasteboard.general.string = code
                                            
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
                                    
                                    HStack {
                                        Button("Spell Code") {
                                            showPhoneticCode = true
                                        }
                                        .buttonStyle(.bordered)
                                        .font(.footnote)

                                        Spacer()
                                    }
                                    .padding(.top, 4)
                                    
                                    HStack(spacing: 6) {
                                        Circle()
                                            .fill(.green)
                                            .frame(width: 8, height: 8)
                                        
                                        Text("Live")
                                            .font(.footnote)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                
                                VStack(spacing: 8) {
                                    Text("Navigate To Me")
                                        .font(.headline)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                    
                                    Button("Share Route") {
                                        sendMyLocationSMS(using: fix)
                                    }
                                    .buttonStyle(.bordered)
                                }
                                .padding(.horizontal)
                                .padding(.top, 4)
                                
                                Capsule()
                                    .fill(Color.secondary.opacity(0.4))
                                    .frame(width: 40, height: 5)
                                    .padding(.top, 8)
                                    .padding(.bottom, 4)
                                
                                
                                VStack(spacing: 12) {
                                    Text("Find a Person")
                                        .font(.headline)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                    
                                    TextField("Paste location or code", text: $manualInput)
                                        .textFieldStyle(.roundedBorder)
                                        .autocorrectionDisabled()
                                        .textInputAutocapitalization(.never)
                                        .focused($manualInputFocused)
                                        .onSubmit {
                                            resolveManualInput()
                                        }
                                    
                                    Button("Find") {
                                        resolveManualInput()
                                    }
                                    .buttonStyle(.borderedProminent)
                                }
                                .padding()
                                .frame(maxWidth: .infinity)
                                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
                                .padding(.horizontal)
                                
                                // POST-BETA: Extract this entire block into AdvancedDebugView
                                if showAdvanced {
                                    
                                    ShareLink(item: fix.quodWordsCode) {
                                        Label("Share QuodWords", systemImage: "square.and.arrow.up")
                                    }
                                    
                                    Button("Paste QuodWords") {
                                        pasteQuodWordsFromClipboard()
                                    }
                                    .buttonStyle(.bordered)
                                    
                                    if let pasteStatusMessage {
                                        Text(pasteStatusMessage)
                                            .font(.headline)
                                            .foregroundColor(
                                                pasteStatusMessage == "Location loaded" ? .green : .red
                                            )
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
                            }
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
                            .padding(.horizontal)
                            
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
                        
                        if showRecordingUI {
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
                        }
                        
                        if showRecordingUI {
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
            }
            .scrollDismissesKeyboard(.interactively)
            
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
        .alert("Spell Code", isPresented: $showPhoneticCode) {
            Button("OK", role: .cancel) { }
        } message: {
            if let fix = locationManager.currentFix {
                let code = QuodWordsResolver.encodeTAQ56(from: fix.coordinate)
                Text("\(code)\n\n\(phoneticCode(code))")
            }
        }
    }
        private struct MapGridOverlay: View {
        let region: MKCoordinateRegion
        private let gridSizeMeters: CLLocationDistance = 9
        private let minimumScreenSpacing: CGFloat = 12

        var body: some View {
            GeometryReader { geo in
                let centerLatitudeRadians = region.center.latitude * .pi / 180
                let metersPerDegreeLongitude = 111_320 * cos(centerLatitudeRadians)
                let visibleWidthMeters = region.span.longitudeDelta * metersPerDegreeLongitude
                let visibleHeightMeters = region.span.latitudeDelta * 111_320

                let pointsPerMeterX = geo.size.width / max(visibleWidthMeters, 1)
                let pointsPerMeterY = geo.size.height / max(visibleHeightMeters, 1)

                let spacingX: CGFloat = gridSizeMeters * pointsPerMeterX
                let spacingY: CGFloat = gridSizeMeters * pointsPerMeterY

                if spacingX >= minimumScreenSpacing && spacingY >= minimumScreenSpacing {
                    Path { path in
                        stride(from: 0, through: geo.size.width, by: spacingX).forEach { x in
                            path.move(to: CGPoint(x: x, y: 0))
                            path.addLine(to: CGPoint(x: x, y: geo.size.height))
                        }

                        stride(from: 0, through: geo.size.height, by: spacingY).forEach { y in
                            path.move(to: CGPoint(x: 0, y: y))
                            path.addLine(to: CGPoint(x: geo.size.width, y: y))
                        }
                    }
                    .stroke(Color.blue.opacity(0.25), lineWidth: 0.5)
                }
            }
            .allowsHitTesting(false)
        }
    }
    private func updateCameraForFollowMode() {
        guard autoFollow else {
            return
        }

        if let fix = locationManager.currentFix {
            cameraPosition = .region(
                MKCoordinateRegion(
                    center: fix.coordinate,
                    span: MKCoordinateSpan(
                        latitudeDelta: 0.01,
                        longitudeDelta: 0.01
                    )
                )
            )
        }
    }

    private func pasteQuodWordsFromClipboard() {
        guard let raw = UIPasteboard.general.string, !raw.isEmpty else {
            pasteStatusMessage = "Clipboard is empty"
            DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                pasteStatusMessage = nil
            }
            return
        }

        guard let coordinate = QuodWordsResolver.resolve(raw) else {
            pasteStatusMessage = "Invalid location"
            DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                pasteStatusMessage = nil
            }
            return
        }

        pastedCoordinate = coordinate
        autoFollow = false

        cameraPosition = .region(
            MKCoordinateRegion(
                center: coordinate,
                span: MKCoordinateSpan(
                    latitudeDelta: 0.01,
                    longitudeDelta: 0.01
                )
            )
        )

        pasteStatusMessage = "Location loaded"
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            pasteStatusMessage = nil
        }
    }
    
    private func resolveManualInput() {
        manualInputFocused = false

        let trimmed = manualInput.trimmingCharacters(in: .whitespacesAndNewlines)

        guard !trimmed.isEmpty else {
            pasteStatusMessage = "Enter a location"
            DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                pasteStatusMessage = nil
            }
            return
        }

        let separators = CharacterSet.whitespacesAndNewlines
            .union(.punctuationCharacters)

        let candidates = trimmed
            .components(separatedBy: separators)
            .map { $0.uppercased() }
            .filter { !$0.isEmpty }

        for candidate in candidates {
            if let coordinate = QuodWordsResolver.resolve(candidate) {
                pastedCoordinate = coordinate
                autoFollow = false

                cameraPosition = .region(
                    MKCoordinateRegion(
                        center: coordinate,
                        span: MKCoordinateSpan(
                            latitudeDelta: 0.01,
                            longitudeDelta: 0.01
                        )
                    )
                )

                manualInput = ""
                pasteStatusMessage = "Location loaded"

                DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                    pasteStatusMessage = nil
                }

                return
            }
        }

        pasteStatusMessage = "Invalid location"
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            pasteStatusMessage = nil
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
    
    private func phoneticCode(_ code: String) -> String {
        let words: [Character: String] = [
            "A": "Alpha", "B": "Bravo", "C": "Charlie", "D": "Delta",
            "E": "Echo", "F": "Foxtrot", "G": "Golf", "H": "Hotel",
            "I": "India", "J": "Juliett", "K": "Kilo", "L": "Lima",
            "M": "Mike", "N": "November", "O": "Oscar", "P": "Papa",
            "Q": "Quebec", "R": "Romeo", "S": "Sierra", "T": "Tango",
            "U": "Uniform", "V": "Victor", "W": "Whiskey", "X": "X-ray",
            "Y": "Yankee", "Z": "Zulu",
            "0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four",
            "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"
        ]

        return code.uppercased()
            .compactMap { words[$0] }
            .joined(separator: " ")
    }
    
    private func sendMyLocationSMS(using fix: BeaconFix) {
        pasteStatusMessage = nil

        guard !emergencyPhoneNumber.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            pasteStatusMessage = "No phone number set"
            return
        }

        let introMessage = "I'm here"
        let codeMessage = QuodWordsResolver.encodeTAQ56(from: fix.coordinate)
        let message = "\(introMessage)\n\n\(codeMessage)"

        let encodedMessage =
            message.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        let cleanedNumber = cleanPhoneNumber(emergencyPhoneNumber)
        let smsURLString = "sms:\(cleanedNumber)&body=\(encodedMessage)"

        if let url = URL(string: smsURLString) {
            UIApplication.shared.open(url)
        } else {
            pasteStatusMessage = "Could not open Messages"
        }
        
    }
    private func cleanPhoneNumber(_ input: String) -> String {
        var result = input.trimmingCharacters(in: .whitespacesAndNewlines)

        if result.hasPrefix("00") {
            result = "+" + result.dropFirst(2)
        }

        result = result.filter { $0.isNumber || $0 == "+" }

        if result.hasPrefix("+") {
            result = "+" + result.dropFirst().filter { $0.isNumber }
        } else {
            result = result.filter { $0.isNumber }
        }

        return result
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
