import SwiftUI
import CoreLocation
import MapKit
import UIKit
import AVFoundation

struct ContentView: View {
    @State private var pasteStatusMessage: String? =
        nil

    @State private var displayedQuodWordsCode: String = ""
    @State private var displayedQuodWordsCoordinate: CLLocationCoordinate2D?
    @State private var candidateQuodWordsCode: String?
    @State private var candidateQuodWordsSince: Date?

    @State private var emergencyPhoneNumber: String =
        "07974919020"
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
    @State private var showAboutMiniGuide = false
    
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
                    
                    if let location =
                        locationManager.lastLocation {
                        CurrentCellHighlightOverlay(
                            region: currentGridRegion,
                            coordinate:
                                displayedQuodWordsCoordinate
                                    ?? location.coordinate
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
                                    
                                    displayQuodWordsCodeView(
                                        displayedQuodWordsCode.isEmpty
                                            ? QuodWordsEncoder
                                                .shortCode(from: fix.coordinate)
                                            : displayedQuodWordsCode
                                    )
                                    .font(
                                        .system(size: 50,
                                                weight: .heavy,
                                                design: .monospaced)
                                    )
                                    .lineLimit(1)
                                    .minimumScaleFactor(0.85)
                                    .padding(.vertical, 6)
                                    .padding(.bottom, 12)
                                    .onChange(of: locationManager.currentFix?.coordinate.latitude) {
                                        guard let fix = locationManager.currentFix else { return }
                                        let newCode = QuodWordsEncoder.shortCode(from: fix.coordinate)
                                        updateStableQuodWordsCode(with: newCode, coordinate: fix.coordinate)
                                    }
                                    .onChange(of: locationManager.currentFix?.coordinate.longitude) {
                                        guard let fix = locationManager.currentFix else { return }
                                        let newCode = QuodWordsEncoder.shortCode(from: fix.coordinate)
                                        updateStableQuodWordsCode(with: newCode, coordinate: fix.coordinate)
                                    }
                                    
                                    Button("Send My Location") {
                                        sendLocation()
                                    }
                                    .buttonStyle(.borderedProminent)
                                    .padding(.bottom, 12)
                                    
                                    HStack(spacing: 22) {
                                        Button("Copy") {
                                            let code = displayedQuodWordsCode.isEmpty
                                                ? QuodWordsEncoder.shortCode(from: fix.coordinate)
                                                : displayedQuodWordsCode
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
                                            let code = displayedQuodWordsCode.isEmpty
                                                ? QuodWordsEncoder.shortCode(from: fix.coordinate)
                                                : displayedQuodWordsCode
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
                                
                                VStack(alignment: .center, spacing: 12) {
                                    Text("Find Location")
                                        .font(.headline)
                                        .frame(maxWidth: .infinity, alignment: .center)
                                    
                                    TextField(
                                        "",
                                        text: $manualInput,
                                        prompt:
                                            Text(
                                                manualInputFocused
                                                    ? ""
                                                    : "Paste QuodWords Code"
                                            )
                                            .font(.body)
                                            .foregroundStyle(.blue)
                                    )
                                    .font(slashedZeroFont(size: 28))
                                    .multilineTextAlignment(.center)
                                    .textFieldStyle(.roundedBorder)
                                    .foregroundStyle(.blue)
                                    .autocorrectionDisabled()
                                    .textInputAutocapitalization(.characters)
                                    .focused($manualInputFocused)
                                    .submitLabel(.search)
                                    .onSubmit {
                                        resolveManualInput()
                                    }
                                    .frame(maxWidth: .infinity, alignment: .center)

                                    HStack(spacing: 16) {
                                        Button("Paste") {
                                            pasteQuodWordsFromClipboard()
                                        }
                                        .buttonStyle(.borderedProminent)

                                        Button("Find") {
                                            resolveManualInput()
                                        }
                                        .buttonStyle(.bordered)
                                    }
                                    .font(.footnote.weight(.semibold))
                                    .frame(maxWidth: .infinity, alignment: .center)
                                }
                                if let pasteStatusMessage {
                                    Text(pasteStatusMessage)
                                        .font(.headline)
                                        .fontWeight(.semibold)
                                        .foregroundStyle(
                                            pasteStatusMessage.lowercased().contains("invalid") ? .red : .secondary
                                        )
                                        .multilineTextAlignment(.center)
                                        .frame(maxWidth: .infinity, alignment: .center)
                                        .padding(.top, 8)
                                }
                                
                                Divider()
                                    .padding(.vertical, 16)
                                
                                VStack(spacing: 8) {
                                    Text("Navigate To Me")
                                        .font(.headline)
                                        .frame(maxWidth: .infinity, alignment: .center)
                                    
                                    Button("Share Map Link") {
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
                            if !locationManager.isPreciseLocationEnabled {
                                VStack(spacing: 8) {
                                    Text("Precise Location is off")
                                        .font(.headline)

                                    Text(
                                        "Turn on Precise Location in iPhone Settings "
                                        + "to generate an accurate QuodWords code."
                                    )
                                    .foregroundStyle(.secondary)
                                    .multilineTextAlignment(.center)
                                }
                                .padding(.horizontal)
                            } else {
                                Text("Waiting for location...")
                                    .foregroundStyle(.secondary)
                            }
                        }
                        
                        if locationManager.isPreciseLocationEnabled,
                           let errorMessage = locationManager.errorMessage {
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
            
            VStack {
                HStack {
                    Spacer()
                    
                    Button {
                        showAboutMiniGuide = true
                    } label: {
                        Image(systemName: "info.circle.fill")
                            .font(.system(size: 22, weight: .semibold))
                            .foregroundColor(.white)
                            .padding(10)
                            .background(Color.black.opacity(0.65), in: Circle())
                    }
                    .accessibilityLabel("About RouteBuddy Beacon")
                    .padding(.top, 12)
                    .padding(.trailing, 12)
                }
                
                Spacer()
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
        .onAppear {
            locationManager.startUpdatingLocation()
        }
        .sheet(isPresented: $showAboutMiniGuide) {
            AboutMiniGuideView()
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
                let code = displayedQuodWordsCode.isEmpty
                    ? QuodWordsEncoder.shortCode(from: fix.coordinate)
                    : displayedQuodWordsCode
                Text("SHORT:\n\(code)\n\nSPELL:\n\(phoneticCode(code))")
                    .font(.body.weight(.semibold))
                    .foregroundStyle(.primary)
            }
        }
    }
    
    private struct AboutMiniGuideView: View {
        @Environment(\.dismiss) private var dismiss
        
        var body: some View {
            NavigationStack {
                ScrollView {
                    VStack(alignment: .leading, spacing: 18) {
                        Text("RouteBuddy Beacon")
                            .font(.largeTitle.bold())
                        
                        Text("Beacon shows your current location and creates a QuodWords location code that can be copied, spelled, spoken, or shared with someone else.")
                            .font(.body)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text("BEACON IS NOT A NAVIGATION APP")
                                .font(.headline.bold())
                            
                            Text("It is a location and communication tool.")
                                .font(.body)
                        }
                        
                        Text("It is designed to show your current position, create a QuodWords location code, and help you share that location clearly when you are under pressure or data coverage is poor.")
                            .font(.body)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text("PRECISE LOCATION")
                                .font(.headline.bold())

                            Text(
                                "For an accurate QuodWords location, make sure "
                                + "Precise Location is turned on for Beacon "
                                + "in iPhone Settings."
                            )
                            .font(.body)
                        }
                        
                        guideSection(
                            title: "MAIN CONTROLS",
                            body: """
                            **Copy** — copies your current location code.

                            **Spell** — shows the code in NATO-style phonetic words so it can be read aloud clearly. Some numbers may be spoken in radio-style form, such as “Fife” for 5 and "Niner" for 9 to reduce confusion.

                            **Speak** — speaks the code aloud.

                            **Send My Location** — prepares a message containing your location details. You choose who to send it to.

                            **Find Location** — paste or enter a QuodWords code to move the map to that location.
                            """
                        )
                        
                        guideSection(
                            title: "MAP AND LOCATION",
                            body: """
                            Beacon needs location permission to show your live position.
                            
                            Beacon can determine and show your location without loading Apple Maps. The map background may require a data connection.
                            
                            If the map background does not load, your GPS position and QuodWords code may still be correct.
                            """
                        )
                        
                        guideSection(
                            title: "GPS ACCURACY",
                            body: """
                            Phone GPS is approximate and may move or jitter, especially near buildings, trees, steep ground, or when satellite visibility is poor.
                            
                            Near a QuodWords cell boundary, Beacon may briefly hold the displayed code to avoid rapid flickering between neighbouring cells.
                            
                            The blue position marker shows live phone movement. The highlighted QuodWords cell shows the currently displayed location code.
                            """
                        )
                        
                        guideSection(
                            title: "IMPORTANT SAFETY NOTE",
                            body: """
                            
                            QuodWords codes identify approximate location cells. They do not guarantee that a location is accessible, safe, on land, or suitable for navigation.
                            
                            Beacon is not a marine navigation, distress or rescue system.
                            
                            Do not rely on Beacon as your only navigation or emergency safety tool.
                            
                            Always use normal navigation judgement, suitable maps, and established emergency procedures.
                            """
                        )
                    }
                    .padding()
                }
                .navigationTitle("Mini Guide")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Done") {
                            dismiss()
                        }
                    }
                }
            }
        }
        
        private func guideSection(title: String, body: String) -> some View {
            VStack(alignment: .leading, spacing: 8) {
                Text(title)
                    .font(.headline.bold())
                
                VStack(alignment: .leading, spacing: 14) {
                    ForEach(
                        Array(
                            body
                                .replacingOccurrences(
                                    of: "\n[ \t]*\n",
                                    with: "\n\n",
                                    options: .regularExpression
                                )
                                .components(separatedBy: "\n\n")
                                .map {
                                    $0.trimmingCharacters(in: .whitespacesAndNewlines)
                                }
                                .filter { !$0.isEmpty }
                                .enumerated()
                        ),
                        id: \.offset
                    ) { _, paragraph in
                        Text(.init(paragraph))
                            .font(.body)
                            .foregroundStyle(.primary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
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
        manualInputFocused = false

        let pasted = UIPasteboard.general.string?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""

        guard !pasted.isEmpty else {
            pasteStatusMessage = "Clipboard empty"

            let message = pasteStatusMessage
            DispatchQueue.main.asyncAfter(deadline: DispatchTime.now() + DispatchTimeInterval.seconds(3)) {
                if pasteStatusMessage == message {
                    pasteStatusMessage = nil
                }
            }
            return
        }

        manualInput = pasted
        resolveManualInput(pasted)
    }
    
    private func resolveManualInput(_ input: String? = nil) {
        manualInputFocused = false

        let trimmed = (input ?? manualInput)
            .trimmingCharacters(in: .whitespacesAndNewlines)

        guard !trimmed.isEmpty else {
            pasteStatusMessage = "Enter a location"
            let message = pasteStatusMessage
            DispatchQueue.main.asyncAfter(deadline: DispatchTime.now() + DispatchTimeInterval.seconds(3)) {
                if pasteStatusMessage == message {
                    pasteStatusMessage = nil
                }
            }
            return
        }

        let separators = CharacterSet.whitespacesAndNewlines
            .union(.punctuationCharacters)

        let parts = trimmed
            .components(separatedBy: separators)
            .map { $0.uppercased() }
            .filter { !$0.isEmpty }

        let compactCandidate = parts.joined()

        let withoutTerritoryCandidate =
            parts.first?.count == 2
            ? parts.dropFirst().joined()
            : ""

        let candidates = Array(
            Set(parts + [
                compactCandidate,
                withoutTerritoryCandidate
            ])
        )
        .filter { !$0.isEmpty }

        for candidate in candidates {
            if let coordinate = QuodWordsResolver.resolve(
                candidate,
                near: locationManager.currentFix?.coordinate
            ) {
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

                manualInput = candidate
                pasteStatusMessage = "Location found"

                let message = pasteStatusMessage
                DispatchQueue.main.asyncAfter(deadline: DispatchTime.now() + DispatchTimeInterval.seconds(3)) {
                    if pasteStatusMessage == message {
                        pasteStatusMessage = nil
                    }
                }

                return
            }
        }

        manualInput = trimmed.uppercased()
        pasteStatusMessage = "Invalid QuodWords code"

        let message = pasteStatusMessage
        DispatchQueue.main.asyncAfter(deadline: DispatchTime.now() + DispatchTimeInterval.seconds(6)) {
            if pasteStatusMessage == message {
                pasteStatusMessage = nil
            }
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
    
    private func updateStableQuodWordsCode(with newCode: String, coordinate: CLLocationCoordinate2D) {
        if displayedQuodWordsCode.isEmpty {
            displayedQuodWordsCode = newCode
            displayedQuodWordsCoordinate = coordinate
            candidateQuodWordsCode = nil
            candidateQuodWordsSince = nil
            return
        }

        if newCode == displayedQuodWordsCode {
            candidateQuodWordsCode = nil
            candidateQuodWordsSince = nil
            return
        }

        if newCode != candidateQuodWordsCode {
            candidateQuodWordsCode = newCode
            candidateQuodWordsSince = Date()
            return
        }

        if let since = candidateQuodWordsSince,
           Date().timeIntervalSince(since) >= 3 {
            displayedQuodWordsCode = newCode
            displayedQuodWordsCoordinate = coordinate
            candidateQuodWordsCode = nil
            candidateQuodWordsSince = nil
        }
    }
    
    private func speak(_ text: String) {
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice =
            AVSpeechSynthesisVoice(language: "en-GB")
        utterance.rate = 0.5

        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
            try session.setActive(true)
        } catch {
            print("Audio session error: \(error)")
        }

        speechSynthesizer.stopSpeaking(at: .immediate)
        speechSynthesizer.speak(utterance)
    }
    
    private func sendLocation() {
        guard let fix = locationManager.currentFix else { return }
        
        let shortCode = displayedQuodWordsCode.isEmpty
            ? QuodWordsEncoder.shortCode(from: fix.coordinate)
            : displayedQuodWordsCode
        let readableShortCode = displayShortCode(shortCode)
        let fullCode =
            QuodWordsEncoder.fullAreaCode(from:
                fix.coordinate)

        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        formatter.locale = Locale(identifier: "en_GB")
        formatter.timeZone = .current

        let generatedTime = formatter.string(from: Date())
        let latitude = String(format: "%.6f", fix.coordinate.latitude)
        let longitude = String(format: "%.6f", fix.coordinate.longitude)

        let message = """
        My QuodWords location:

        SHORT code:
        \(readableShortCode)
        
        LONG code:
        \(fullCode)
        
        Latitude / Longitude:
        \(latitude), \(longitude)

        Generated:
        \(generatedTime)

        Note: QuodWords codes identify approximate location cells. Use normal navigation and emergency procedures.
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
        NAVIGATE TO ME:
        \(mapsURL)


        QUODWORDS CODE:

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
    
    private func quodWordsDisplayParts(_ code: String) -> (letters: String, digits: String, finalLetter: String)? {
        let cleaned = code.replacingOccurrences(of: " ", with: "")
        
        guard cleaned.count == 7 else {
            return nil
        }
        
        let chars = Array(cleaned)
        
        return (
            letters: String(chars[0...2]),
            digits: String(chars[3...5]),
            finalLetter: String(chars[6])
        )
    }
    
    private func displayShortCode(_ code: String) -> String {
        let compact = code
            .replacingOccurrences(of: " ", with: "")
            .replacingOccurrences(of: "-", with: "")
            .uppercased()
        
        guard compact.count == 7 else {
            return code
        }
        
        let first = compact.prefix(3)
        let middleStart = compact.index(compact.startIndex, offsetBy: 3)
        let middleEnd = compact.index(compact.startIndex, offsetBy: 6)
        let middle = compact[middleStart..<middleEnd]
        let last = compact.suffix(1)
        
        return "\(first) \(middle) \(last)"
    }
    
    private func slashedZeroFont(size: CGFloat) -> Font {
        let baseFont = UIFont.monospacedSystemFont(
            ofSize: size,
            weight: .bold
        )

        let descriptor = baseFont.fontDescriptor.addingAttributes([
            .featureSettings: [
                [
                    UIFontDescriptor.FeatureKey.type:
                        kTypographicExtrasType,
                    UIFontDescriptor.FeatureKey.selector:
                        kSlashedZeroOnSelector
                ]
            ]
        ])

        return Font(
            UIFont(
                descriptor: descriptor,
                size: size
            )
        )
    }
    
    @ViewBuilder
    private func displayQuodWordsCodeView(_ code: String) -> some View {
        if let parts = quodWordsDisplayParts(code) {
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(parts.letters)
                Text(parts.digits)
                    .font(slashedZeroFont(size: 48))
                Text(parts.finalLetter)
            }
        } else {
            Text(code)
        }
    }
}

#Preview {
    ContentView()
}
