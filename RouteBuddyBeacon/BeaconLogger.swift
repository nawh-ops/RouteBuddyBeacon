import Foundation

struct BeaconLogger {

    static func log(_ message: BeaconMessage) {
        guard let json = message.json else {
            print("BeaconLogger: invalid JSON")
            return
        }

        print("----- BEACON MESSAGE -----")
        print(json)
        print("--------------------------")
    }
}
