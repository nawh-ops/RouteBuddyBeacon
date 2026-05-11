import SwiftUI
import CoreLocation
import MapKit
import UIKit
import AVFoundation

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
    @State private var speechSynthesizer = AVSpeechSynthesizer()
    @State private var isPulsing = false
    @State private var showAdvanced = false
    @State private var showRecordingUI = false
    
    @State private var currentGridRegion = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 52.5, longitude: -1.5),
        span: MKCoordinateSpan(latitudeDelta: 0.01,
                               longitudeDelta: 0.01)
    )
    
    var body: some View {
        
        ZStack {
            VStack(spacing: 0) {
                
                ZStack(alignment: .bottomTrailing) {
                    
                    Map(position: $cameraPosition, interactionModes: [.pan, .zoom]) {
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
                    
                    if let location = locationManager.lastLocation {
                        CurrentCellHighlightOverlay(
                            region: currentGridRegion,
                            coordinate: location.coordinate
                        )
                        .allowsHitTesting(false)
                    }
                    
                    if let pastedCoordinate {
                        CurrentCellHighlightOverlay(
                            region: currentGridRegion,
                            coordinate: pastedCoordinate
                        )
                        .allowsHitTesting(false)
                    }
                    
                    Button {
                        recenterOnUser()
                    } label: {
                        Image(systemName: "location.fill")
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(.white)
                            .padding(10)
                            .background(Color.blue)
                            .clipShape(Circle())
                    }
                    .padding(12)
                    
                }
                
                .frame(height: 260)
                .clipped()
                .onMapCameraChange(frequency: .continuous) { context in
                    currentGridRegion = context.region
                }
                .onMapCameraChange(frequency: .onEnd) { _ in
                    autoFollow = false
                }
                .onAppear { updateCameraForFollowMode() }
                .onChange(of: autoFollow) { updateCameraForFollowMode() }
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
                            .offset(y: 6)
                        
                        if let fix = locationManager.currentFix {
                            VStack(spacing: 8) {
                                VStack(spacing: 6) {
                                    Text("Your QuodWords Location")
                                        .font(.system(size: 20, weight: .semibold))
                                        .foregroundStyle(.primary)
                                        .frame(maxWidth: .infinity, alignment: .center)
                                    
                                    Text(QuodWordsEncoder.shortCode(from: fix.coordinate))
                                        .font(.system(size: 50, weight: .heavy, design: .monospaced))
                                        .padding(.vertical, 6)
                                        .padding(.bottom, 12)
                                    
                                    Button("Send Location") {
                                        sendLocation()
                                    }
                                    .buttonStyle(.borderedProminent)
                                    .padding(.bottom, 12)
                                    
                                    HStack(spacing: 22) {
                                        Button("Copy") {
                                            let code = QuodWordsEncoder.shortCode(from: fix.coordinate)
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
                                        .buttonStyle(.borderedProminent)
                                        .font(.footnote)
                                        
                                        Button("Spell") {
                                            showPhoneticCode = true
                                        }
                                        .buttonStyle(.bordered)
                                        .tint(.blue)
                                        .font(.footnote.weight(.semibold))
                                        
                                        Button("Speak") {
                                            let code = QuodWordsEncoder.shortCode(from: fix.coordinate)
                                            let spoken = phoneticCode(code)
                                                .replacingOccurrences(of: " ", with: ", ")
                                            
                                            speak(spoken)
                                        }
                                        .buttonStyle(.bordered)
                                        .tint(.blue)
                                        .font(.footnote.weight(.semibold))
                                    }
                                    .padding(.bottom, 12)
                                    .padding(.top, 4)
                                    
                                    let fix = locationManager.currentFix
                                    
                                    Group {
                                        if fix != nil {
                                            HStack(spacing: 6) {
                                                Circle()
                                                    .fill(Color.green)
                                                    .frame(width: 8, height: 8)
                                                
                                                Text("Live")
                                                    .font(.footnote)
                                                    .foregroundStyle(.secondary)
                                            }
                                        } else {
                                            HStack(spacing: 6) {
                                                Circle()
                                                    .fill(Color.red)
                                                    .frame(width: 8, height: 8)
                                                
                                                Text("Waiting for GPS…")
                                                    .font(.footnote)
                                                    .foregroundStyle(.secondary)
                                            }
                                        }
                                    }
                                    .padding(.bottom, 40)
                                    
                                    
                                    Rectangle()
                                        .fill(Color(.systemGray4))
                                        .frame(height: 1.5)
                                        .opacity(0.5)
                                        .padding(.horizontal)
                                        .padding(.bottom, 12)
                                }
                                
                                VStack(spacing: 12) {
                                    Text("Find Location")
                                        .font(.headline)
                                        .frame(maxWidth: .infinity, alignment: .center)
                                    
                                    TextField("Paste QuodWords Code", text: $manualInput)
                                        .multilineTextAlignment(.center)
                                        .textFieldStyle(.roundedBorder)
                                        .autocorrectionDisabled()
                                        .textInputAutocapitalization(.characters)
                                        .focused($manualInputFocused)
                                        .submitLabel(.search)
                                        .onSubmit {
                                            resolveManualInput()
                                        }
                                }
                                
                                Divider()
                                    .padding(.vertical, 16)
                                
                                VStack(spacing: 8) {
                                    Text("Navigate To Me")
                                        .font(.headline)
                                        .frame(maxWidth: .infinity, alignment: .center)
                                    
                                    Button("Navigate To Me") {
                                        sendNavigateToMeSMS(using: fix)
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
                                    .font(.footnote.weight(.semibold))
                                    
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
                let code = QuodWordsEncoder.shortCode(from: fix.coordinate)
                Text("SHORT:\n\(code)\n\nSPELL:\n\(phoneticCode(code))")
                    .font(.body.weight(.semibold))
                    .foregroundStyle(.primary)
            }
        }
    }
    
    private struct CurrentCellHighlightOverlay: View {
        let region: MKCoordinateRegion
        let coordinate: CLLocationCoordinate2D
        
        private let originLatitude = 49.5
        private let originLongitude = -8.5
        private let projectionLatitude = 55.0
        private let metersPerDegreeLatitude = 111_320.0
        private let cellSizeMeters = 30.0
        
        private var metersPerDegreeLongitude: Double {
            metersPerDegreeLatitude * cos(projectionLatitude * .pi / 180.0)
        }
        
        var body: some View {
            GeometryReader { geo in
                Canvas { context, size in
                    guard let rect = currentCellScreenRect(size: size) else {
                        return
                    }
                    
                    var path = Path()
                    path.addRect(rect)
                    
                    context.fill(
                        path,
                        with: .color(Color.yellow.opacity(0.18))
                    )
                    
                    context.stroke(
                        path,
                        with: .color(Color.yellow.opacity(0.95)),
                        lineWidth: 3
                    )
                }
                .frame(width: geo.size.width, height: geo.size.height)
            }
        }
        
        private func currentCellScreenRect(size: CGSize) -> CGRect? {
            guard region.span.latitudeDelta > 0,
                  region.span.longitudeDelta > 0 else {
                return nil
            }
            
            let xMeters = (coordinate.longitude - originLongitude) * metersPerDegreeLongitude
            let yMeters = (coordinate.latitude - originLatitude) * metersPerDegreeLatitude
            
            let cellX = floor(xMeters / cellSizeMeters) * cellSizeMeters
            let cellY = floor(yMeters / cellSizeMeters) * cellSizeMeters
            
            let minLon = originLongitude + cellX / metersPerDegreeLongitude
            let maxLon = originLongitude + (cellX + cellSizeMeters) / metersPerDegreeLongitude
            let minLat = originLatitude + cellY / metersPerDegreeLatitude
            let maxLat = originLatitude + (cellY + cellSizeMeters) / metersPerDegreeLatitude
            
            let topLeft = screenPoint(
                latitude: maxLat,
                longitude: minLon,
                size: size
            )
            
            let bottomRight = screenPoint(
                latitude: minLat,
                longitude: maxLon,
                size: size
            )
            
            let rect = CGRect(
                x: min(topLeft.x, bottomRight.x),
                y: min(topLeft.y, bottomRight.y),
                width: abs(bottomRight.x - topLeft.x),
                height: abs(bottomRight.y - topLeft.y)
            )
            
            guard rect.maxX >= 0,
                  rect.maxY >= 0,
                  rect.minX <= size.width,
                  rect.minY <= size.height else {
                return nil
            }
            
            return rect
        }
        
        private func screenPoint(
            latitude: Double,
            longitude: Double,
            size: CGSize
        ) -> CGPoint {
            let minLon = region.center.longitude - region.span.longitudeDelta / 2.0
            let maxLat = region.center.latitude + region.span.latitudeDelta / 2.0
            
            let x = ((longitude - minLon) / region.span.longitudeDelta) * size.width
            let y = ((maxLat - latitude) / region.span.latitudeDelta) * size.height
            
            return CGPoint(x: x, y: y)
        }
    }
    
    private struct MapGridOverlay: View {
        let region: MKCoordinateRegion
        private let gridSizeMeters: CLLocationDistance = 3
        private let minimumScreenSpacing: CGFloat = 8
        
        var body: some View {
            GeometryReader { geo in
                let centerLatitudeRadians = region.center.latitude * .pi / 180
                
                let metersPerDegreeLat = 111_320.0
                let metersPerDegreeLon = 111_320.0 * cos(centerLatitudeRadians)
                
                let visibleWidthMeters = region.span.longitudeDelta * metersPerDegreeLon
                let visibleHeightMeters = region.span.latitudeDelta * metersPerDegreeLat
                
                let pointsPerMeterX = geo.size.width / max(visibleWidthMeters, 1)
                let pointsPerMeterY = geo.size.height / max(visibleHeightMeters, 1)
                
                let spacingX: CGFloat = gridSizeMeters * pointsPerMeterX
                let spacingY: CGFloat = gridSizeMeters * pointsPerMeterY
                
                let startLon = region.center.longitude - region.span.longitudeDelta / 2
                let startLat = region.center.latitude - region.span.latitudeDelta / 2
                
                let gridSizeDegreesLat = gridSizeMeters / metersPerDegreeLat
                let gridSizeDegreesLon = gridSizeMeters / metersPerDegreeLon
                
                let alignedStartLon = floor(startLon / gridSizeDegreesLon) * gridSizeDegreesLon
                let alignedStartLat = floor(startLat / gridSizeDegreesLat) * gridSizeDegreesLat
                
                if spacingX >= minimumScreenSpacing && spacingY >= minimumScreenSpacing && spacingX < 80 {
                    Path { path in
                        stride(
                            from: alignedStartLon,
                            through: startLon + region.span.longitudeDelta,
                            by: gridSizeDegreesLon
                        ).forEach { lon in
                            let x = CGFloat((lon - startLon) / region.span.longitudeDelta) * geo.size.width
                            path.move(to: CGPoint(x: x, y: 0))
                            path.addLine(to: CGPoint(x: x, y: geo.size.height))
                        }
                        
                        stride(
                            from: alignedStartLat,
                            through: startLat + region.span.latitudeDelta,
                            by: gridSizeDegreesLat
                        ).forEach { lat in
                            let y = CGFloat(1 - (lat - startLat) / region.span.latitudeDelta) * geo.size.height
                            path.move(to: CGPoint(x: 0, y: y))
                            path.addLine(to: CGPoint(x: geo.size.width, y: y))
                        }
                    }
                    .stroke(Color.black.opacity(0.28), lineWidth: 0.75)
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
    
    private func recenterOnUser() {
        if let fix = locationManager.currentFix {
            cameraPosition = .region(
                MKCoordinateRegion(
                    center: fix.coordinate,
                    span: MKCoordinateSpan(latitudeDelta: 0.005, longitudeDelta: 0.005)
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
        
        guard let coordinate = QuodWordsResolver.resolve(raw, near: locationManager.currentFix?.coordinate) else {
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
            if let coordinate = QuodWordsResolver.resolve(candidate, near: locationManager.currentFix?.coordinate) {
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
            "5": "Fife", "6": "Six", "7": "Seven", "8": "Eight", "9": "Niner"
        ]
        
        return code.uppercased()
            .compactMap { words[$0] }
            .joined(separator: " ")
    }
    
    private func speak(_ text: String) {
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-GB")
        utterance.rate = 0.5
        
        speechSynthesizer.stopSpeaking(at: .immediate)
        speechSynthesizer.speak(utterance)
    }
    
    private func sendLocation() {
        guard let fix = locationManager.currentFix else { return }
        
        let shortCode = QuodWordsEncoder.shortCode(from: fix.coordinate)
        let fullCode = QuodWordsEncoder.fullAreaCode(from: fix.coordinate)
        
        let message = """
        My QuodWords location:
        
        SHORT code: 
        \(shortCode)
        
        LONG code: 
        \(fullCode)
        """
        
        let encodedMessage =
        message.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        
        let smsURLString = "sms:?body=\(encodedMessage)"
        
        if let url = URL(string: smsURLString) {
            UIApplication.shared.open(url)
        }
    }
    
    private func sendMyLocationSMS(using fix: BeaconFix) {
        pasteStatusMessage = nil
        
        guard !emergencyPhoneNumber.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            pasteStatusMessage = "No phone number set"
            return
        }
        
        let introMessage = "I'm here"
        let shortCode = QuodWordsEncoder.shortCode(from: fix.coordinate)
        let fullCode = QuodWordsEncoder.fullAreaCode(from: fix.coordinate)
        let message = "\(introMessage)\n\nSHORT: \(shortCode)\n\nLONG: \(fullCode)"
        
        let encodedMessage =
        message.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        let cleanedNumber = cleanPhoneNumber(emergencyPhoneNumber)
        let smsURLString = "sms:\(cleanedNumber)?body=\(encodedMessage)"
        
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
    
    private func sendNavigateToMeSMS(using fix: BeaconFix) {
        pasteStatusMessage = nil
        
        guard !emergencyPhoneNumber.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            pasteStatusMessage = "No phone number set"
            return
        }
        
        let coordinate = fix.coordinate
        
        let lat = coordinate.latitude
        let lon = coordinate.longitude
        
        let mapsURL = "http://maps.apple.com/?daddr=\(lat),\(lon)"
        
        let shortCode = QuodWordsEncoder.shortCode(from: coordinate)
        let fullCode = QuodWordsEncoder.fullAreaCode(from: coordinate)

        let message = """
        NAVIGATE to ME:
        \(mapsURL)

        SHORT:
        \(shortCode)

        LONG:
        \(fullCode)
        """
        
        var allowed = CharacterSet.urlQueryAllowed
        allowed.remove(charactersIn: "&=?+")
        
        let encodedMessage =
        message.addingPercentEncoding(withAllowedCharacters: allowed) ?? ""
        
        let cleanedNumber = cleanPhoneNumber(emergencyPhoneNumber)
        let smsURLString = "sms:\(cleanedNumber)?body=\(encodedMessage)"
        
        if let url = URL(string: smsURLString) {
            UIApplication.shared.open(url)
        } else {
            pasteStatusMessage = "Could not open Messages"
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
