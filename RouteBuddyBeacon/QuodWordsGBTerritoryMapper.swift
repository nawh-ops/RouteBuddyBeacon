import CoreLocation
import Foundation

enum QuodWordsGBTerritoryMapperError: Error, Equatable {
    case unsupportedProjection(UInt32)
    case invalidCellSize(UInt32)
}

struct QuodWordsGBTerritoryResult: Equatable {
    let coordinate: CLLocationCoordinate2D
    let projectedPoint: ETRS89LAEAPoint
    let cell: QuodWordsTerritoryGridCell
    let nationalIndex: UInt64

    static func == (
        lhs: QuodWordsGBTerritoryResult,
        rhs: QuodWordsGBTerritoryResult
    ) -> Bool {
        lhs.coordinate.latitude == rhs.coordinate.latitude
            && lhs.coordinate.longitude == rhs.coordinate.longitude
            && lhs.projectedPoint == rhs.projectedPoint
            && lhs.cell == rhs.cell
            && lhs.nationalIndex == rhs.nationalIndex
    }
}

struct QuodWordsGBTerritoryMapper {
    let resource: QuodWordsTerritoryResource

    init(
        resource: QuodWordsTerritoryResource
    ) throws {
        guard
            resource.metadata.projectionEPSG
                == ETRS89LAEAProjection.epsgCode
        else {
            throw QuodWordsGBTerritoryMapperError
                .unsupportedProjection(
                    resource.metadata.projectionEPSG
                )
        }

        guard resource.metadata.cellSizeMetres > 0 else {
            throw QuodWordsGBTerritoryMapperError
                .invalidCellSize(
                    resource.metadata.cellSizeMetres
                )
        }

        self.resource = resource
    }

    static func bundledGB(
        bundle: Bundle = .main
    ) throws -> QuodWordsGBTerritoryMapper {
        try QuodWordsGBTerritoryMapper(
            resource: QuodWordsTerritoryResource.bundledGB(
                bundle: bundle
            )
        )
    }

    func map(
        _ coordinate: CLLocationCoordinate2D
    ) throws -> QuodWordsGBTerritoryResult {
        let projectedPoint =
            ETRS89LAEAProjection.project(coordinate)

        let cell = gridCell(
            for: projectedPoint
        )

        let nationalIndex = try resource.index(
            forCell: cell
        )

        return QuodWordsGBTerritoryResult(
            coordinate: coordinate,
            projectedPoint: projectedPoint,
            cell: cell,
            nationalIndex: nationalIndex
        )
    }

    func nationalIndex(
        for coordinate: CLLocationCoordinate2D
    ) throws -> UInt64 {
        try map(coordinate).nationalIndex
    }

    func gridCell(
        for projectedPoint: ETRS89LAEAPoint
    ) -> QuodWordsTerritoryGridCell {
        let metadata = resource.metadata
        let cellSize = Double(metadata.cellSizeMetres)

        let column = Int32(
            floor(
                (projectedPoint.x - metadata.originX)
                    / cellSize
            )
        )

        let row = Int32(
            floor(
                (projectedPoint.y - metadata.originY)
                    / cellSize
            )
        )

        return QuodWordsTerritoryGridCell(
            column: column,
            row: row
        )
    }
}
