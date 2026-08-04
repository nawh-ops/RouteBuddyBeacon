import CoreLocation
import Foundation

struct ETRS89LAEAPoint: Equatable {
    let x: Double
    let y: Double
}

enum ETRS89LAEAProjection {
    static let epsgCode: UInt32 = 3035

    // GRS 1980 ellipsoid.
    private static let semiMajorAxis = 6_378_137.0
    private static let inverseFlattening = 298.257_222_101

    // EPSG:3035 projection parameters.
    private static let latitudeOfOrigin = degreesToRadians(52.0)
    private static let longitudeOfOrigin = degreesToRadians(10.0)
    private static let falseEasting = 4_321_000.0
    private static let falseNorthing = 3_210_000.0

    private static let flattening = 1.0 / inverseFlattening
    private static let eccentricitySquared =
        2.0 * flattening - flattening * flattening
    private static let eccentricity = sqrt(eccentricitySquared)

    private static let qPole = authalicQ(
        latitudeRadians: .pi / 2.0
    )

    private static let authalicRadius =
        semiMajorAxis * sqrt(qPole / 2.0)

    private static let betaOrigin = asin(
        authalicQ(latitudeRadians: latitudeOfOrigin) / qPole
    )

    private static let mOrigin =
        cos(latitudeOfOrigin)
        / sqrt(
            1.0
            - eccentricitySquared
                * pow(sin(latitudeOfOrigin), 2.0)
        )

    private static let scaleFactor =
        semiMajorAxis
        * mOrigin
        / (
            authalicRadius
            * cos(betaOrigin)
        )

    static func project(
        _ coordinate: CLLocationCoordinate2D
    ) -> ETRS89LAEAPoint {
        project(
            longitude: coordinate.longitude,
            latitude: coordinate.latitude
        )
    }

    static func project(
        longitude: Double,
        latitude: Double
    ) -> ETRS89LAEAPoint {
        let longitudeRadians = degreesToRadians(longitude)
        let latitudeRadians = degreesToRadians(latitude)

        let beta = asin(
            authalicQ(latitudeRadians: latitudeRadians)
                / qPole
        )

        let longitudeDifference =
            longitudeRadians - longitudeOfOrigin

        let denominator =
            1.0
            + sin(betaOrigin) * sin(beta)
            + cos(betaOrigin)
                * cos(beta)
                * cos(longitudeDifference)

        let radialFactor =
            authalicRadius
            * sqrt(2.0 / denominator)

        let x =
            falseEasting
            + radialFactor
                * scaleFactor
                * cos(beta)
                * sin(longitudeDifference)

        let y =
            falseNorthing
            + (
                radialFactor
                / scaleFactor
            )
            * (
                cos(betaOrigin) * sin(beta)
                - sin(betaOrigin)
                    * cos(beta)
                    * cos(longitudeDifference)
            )

        return ETRS89LAEAPoint(x: x, y: y)
    }

    private static func authalicQ(
        latitudeRadians: Double
    ) -> Double {
        let sineLatitude = sin(latitudeRadians)
        let eccentricitySine =
            eccentricity * sineLatitude

        let firstTerm =
            sineLatitude
            / (
                1.0
                - eccentricitySquared
                    * sineLatitude
                    * sineLatitude
            )

        let logarithmicTerm =
            log(
                (1.0 - eccentricitySine)
                / (1.0 + eccentricitySine)
            )

        return (
            1.0 - eccentricitySquared
        ) * (
            firstTerm
            - logarithmicTerm
                / (2.0 * eccentricity)
        )
    }

    private static func degreesToRadians(
        _ degrees: Double
    ) -> Double {
        degrees * .pi / 180.0
    }
}
