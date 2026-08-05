import Foundation
import CoreLocation

struct QuodWordsEncoder {

    static func encode(_ fix: BeaconFix) -> String {
        do {
            return try QuodWords.encodeFormalCode(
                for: fix.coordinate
            )
        } catch {
            return "GB-INVALID"
        }
    }

    static func shortCode(
        from coordinate: CLLocationCoordinate2D
    ) -> String {
        do {
            let cell = try QuodWords.encodeGBCoordinate(
                coordinate
            )

            return cell.code.nationalCellCode
        } catch {
            return "INVALID"
        }
    }

    static func fullAreaCode(
        from coordinate: CLLocationCoordinate2D
    ) -> String {
        do {
            return try QuodWords.encodeFormalCode(
                for: coordinate
            )
        } catch {
            return "GB-INVALID"
        }
    }
}
