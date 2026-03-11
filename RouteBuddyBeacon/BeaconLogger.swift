import Foundation

final class BeaconLogger {

    private static let sessionFileURL: URL = {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd_HH-mm-ss"

        let timestamp = formatter.string(from: Date())
        let filename = "beacon-log-\(timestamp).jsonl"

        return docs.appendingPathComponent(filename)
    }()

    static func log(_ message: BeaconMessage) {
        guard let json = message.json else { return }

        let line = json + "\n"

        guard let data = line.data(using: .utf8) else { return }

        if FileManager.default.fileExists(atPath: sessionFileURL.path) {
            if let handle = try? FileHandle(forWritingTo: sessionFileURL) {
                handle.seekToEndOfFile()
                handle.write(data)
                try? handle.close()
            }
        } else {
            try? data.write(to: sessionFileURL)
        }

        print("BEACON MESSAGE")
        print(json)
        print("-----------------------")
        print("LOG FILE: \(sessionFileURL.lastPathComponent)")
    }
}
