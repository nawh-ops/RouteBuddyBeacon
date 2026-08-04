import CoreLocation
import Foundation

enum QuodWordsGBTerritoryMapperError: Error, Equatable {
    case unsupportedProjection(UInt32)
    case invalidCellSize(UInt32)
    case nationalIndexNotRepresentable(UInt64)
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

    func quodWordsCode(
        for coordinate: CLLocationCoordinate2D
    ) throws -> QuodWordsCode {
        let territoryResult = try map(coordinate)

        guard
            let codeIndex = Int(
                exactly: territoryResult.nationalIndex
            )
        else {
            throw QuodWordsGBTerritoryMapperError
                .nationalIndexNotRepresentable(
                    territoryResult.nationalIndex
                )
        }

        let nationalCode =
            try QuodWords.nationalCellCode(
                from: codeIndex
            )

        return QuodWordsCode(
            territory: .gb,
            nationalCellCode: nationalCode
        )
    }

    func nationalCode(
        for coordinate: CLLocationCoordinate2D
    ) throws -> String {
        try quodWordsCode(
            for: coordinate
        ).nationalCellCode
    }

    func formalCode(
        for coordinate: CLLocationCoordinate2D
    ) throws -> String {
        try quodWordsCode(
            for: coordinate
        ).formalCode
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
