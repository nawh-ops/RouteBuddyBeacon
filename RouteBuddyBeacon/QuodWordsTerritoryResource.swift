import Foundation

enum QuodWordsTerritoryResourceError: Error, Equatable {
    case resourceNotFound
    case fileTooSmall
    case invalidMagic
    case unsupportedSchemaVersion(UInt16)
    case unsupportedHeaderSize(UInt16)
    case invalidTerritoryCode
    case invalidFileSize
    case invalidSpan
    case invalidCellCount
    case capacityExceeded
    case indexOutsideTerritory
    case cellOutsideTerritory
}

struct QuodWordsTerritoryRowSpan: Equatable {
    let row: Int32
    let startColumn: Int32
    let endColumn: Int32

    var cellCount: UInt64 {
        UInt64(Int64(endColumn) - Int64(startColumn) + 1)
    }
}

struct QuodWordsTerritoryMetadata: Equatable {
    let territoryCode: String
    let schemaVersion: UInt16
    let projectionEPSG: UInt32
    let originX: Double
    let originY: Double
    let cellSizeMetres: UInt32
    let spanCount: UInt64
    let cellCount: UInt64
    let maximumCodeCount: UInt32
}

struct QuodWordsTerritoryGridCell: Equatable {
    let column: Int32
    let row: Int32
}

struct QuodWordsTerritoryResource {
    static let expectedMagic = Array("QWTRSPAN".utf8)
    static let supportedSchemaVersion: UInt16 = 1
    static let expectedHeaderSize: UInt16 = 64
    static let spanRecordSize = 12

    let metadata: QuodWordsTerritoryMetadata
    let spans: [QuodWordsTerritoryRowSpan]
    private let spanStartIndices: [UInt64]

    static func bundledGB(
        bundle: Bundle = .main
    ) throws -> QuodWordsTerritoryResource {
        guard let url = bundle.url(
            forResource: "GB",
            withExtension: "qwtr"
        ) else {
            throw QuodWordsTerritoryResourceError.resourceNotFound
        }

        return try load(from: url)
    }

    static func load(
        from url: URL
    ) throws -> QuodWordsTerritoryResource {
        try parse(Data(contentsOf: url))
    }

    static func parse(
        _ data: Data
    ) throws -> QuodWordsTerritoryResource {
        guard data.count >= Int(expectedHeaderSize) else {
            throw QuodWordsTerritoryResourceError.fileTooSmall
        }

        var reader = LittleEndianReader(data: data)

        let magic = try reader.readBytes(count: 8)

        guard magic == expectedMagic else {
            throw QuodWordsTerritoryResourceError.invalidMagic
        }

        let schemaVersion = try reader.readUInt16()

        guard schemaVersion == supportedSchemaVersion else {
            throw QuodWordsTerritoryResourceError
                .unsupportedSchemaVersion(schemaVersion)
        }

        let territoryBytes = try reader.readBytes(count: 2)

        guard
            let territoryCode = String(
                bytes: territoryBytes,
                encoding: .ascii
            ),
            territoryCode.count == 2,
            territoryCode.allSatisfy({
                $0.isASCII && $0.isLetter && $0.isUppercase
            })
        else {
            throw QuodWordsTerritoryResourceError.invalidTerritoryCode
        }

        let headerSize = try reader.readUInt16()

        guard headerSize == expectedHeaderSize else {
            throw QuodWordsTerritoryResourceError
                .unsupportedHeaderSize(headerSize)
        }

        let projectionEPSG = try reader.readUInt32()
        let originX = try reader.readDouble()
        let originY = try reader.readDouble()
        let cellSizeMetres = try reader.readUInt32()
        let spanCount = try reader.readUInt64()
        let storedCellCount = try reader.readUInt64()
        let maximumCodeCount = try reader.readUInt32()

        try reader.skip(count: 6)

        let expectedFileSize =
            Int(expectedHeaderSize)
            + Int(spanCount) * spanRecordSize

        guard data.count == expectedFileSize else {
            throw QuodWordsTerritoryResourceError.invalidFileSize
        }

        var spans: [QuodWordsTerritoryRowSpan] = []
        spans.reserveCapacity(Int(spanCount))

        var spanStartIndices: [UInt64] = []
        spanStartIndices.reserveCapacity(Int(spanCount))

        var calculatedCellCount: UInt64 = 0
        var previousSpan: QuodWordsTerritoryRowSpan?

        for _ in 0..<spanCount {
            let span = QuodWordsTerritoryRowSpan(
                row: try reader.readInt32(),
                startColumn: try reader.readInt32(),
                endColumn: try reader.readInt32()
            )

            guard span.startColumn <= span.endColumn else {
                throw QuodWordsTerritoryResourceError.invalidSpan
            }

            if let previousSpan {
                guard span.row >= previousSpan.row else {
                    throw QuodWordsTerritoryResourceError.invalidSpan
                }

                if span.row == previousSpan.row {
                    guard
                        span.startColumn
                            > previousSpan.endColumn + 1
                    else {
                        throw QuodWordsTerritoryResourceError.invalidSpan
                    }
                }
            }

            spanStartIndices.append(calculatedCellCount)
            calculatedCellCount += span.cellCount
            spans.append(span)
            previousSpan = span
        }

        guard calculatedCellCount == storedCellCount else {
            throw QuodWordsTerritoryResourceError.invalidCellCount
        }

        guard storedCellCount <= UInt64(maximumCodeCount) else {
            throw QuodWordsTerritoryResourceError.capacityExceeded
        }

        let metadata = QuodWordsTerritoryMetadata(
            territoryCode: territoryCode,
            schemaVersion: schemaVersion,
            projectionEPSG: projectionEPSG,
            originX: originX,
            originY: originY,
            cellSizeMetres: cellSizeMetres,
            spanCount: spanCount,
            cellCount: storedCellCount,
            maximumCodeCount: maximumCodeCount
        )

        return QuodWordsTerritoryResource(
            metadata: metadata,
            spans: spans,
            spanStartIndices: spanStartIndices
        )
    }

    func cell(
        forIndex index: UInt64
    ) throws -> QuodWordsTerritoryGridCell {
        guard index < metadata.cellCount else {
            throw QuodWordsTerritoryResourceError
                .indexOutsideTerritory
        }

        let position = upperBound(
            spanStartIndices,
            value: index
        ) - 1

        let span = spans[position]
        let offset = index - spanStartIndices[position]

        return QuodWordsTerritoryGridCell(
            column: span.startColumn + Int32(offset),
            row: span.row
        )
    }

    func index(
        forCell cell: QuodWordsTerritoryGridCell
    ) throws -> UInt64 {
        var low = 0
        var high = spans.count

        while low < high {
            let middle = (low + high) / 2
            let span = spans[middle]

            if span.row < cell.row
                || (
                    span.row == cell.row
                    && span.startColumn <= cell.column
                )
            {
                low = middle + 1
            } else {
                high = middle
            }
        }

        let position = low - 1

        guard position >= 0 else {
            throw QuodWordsTerritoryResourceError
                .cellOutsideTerritory
        }

        let span = spans[position]

        guard
            span.row == cell.row,
            cell.column >= span.startColumn,
            cell.column <= span.endColumn
        else {
            throw QuodWordsTerritoryResourceError
                .cellOutsideTerritory
        }

        return spanStartIndices[position]
            + UInt64(Int64(cell.column) - Int64(span.startColumn))
    }

    private func upperBound(
        _ values: [UInt64],
        value: UInt64
    ) -> Int {
        var low = 0
        var high = values.count

        while low < high {
            let middle = (low + high) / 2

            if values[middle] <= value {
                low = middle + 1
            } else {
                high = middle
            }
        }

        return low
    }
}

private struct LittleEndianReader {
    let data: Data
    private(set) var offset = 0

    mutating func readBytes(
        count: Int
    ) throws -> [UInt8] {
        guard offset + count <= data.count else {
            throw QuodWordsTerritoryResourceError.fileTooSmall
        }

        let bytes = Array(data[offset..<(offset + count)])
        offset += count
        return bytes
    }

    mutating func skip(
        count: Int
    ) throws {
        _ = try readBytes(count: count)
    }

    mutating func readUInt16() throws -> UInt16 {
        let bytes = try readBytes(count: 2)

        return UInt16(bytes[0])
            | UInt16(bytes[1]) << 8
    }

    mutating func readUInt32() throws -> UInt32 {
        let bytes = try readBytes(count: 4)

        return UInt32(bytes[0])
            | UInt32(bytes[1]) << 8
            | UInt32(bytes[2]) << 16
            | UInt32(bytes[3]) << 24
    }

    mutating func readInt32() throws -> Int32 {
        Int32(bitPattern: try readUInt32())
    }

    mutating func readUInt64() throws -> UInt64 {
        let bytes = try readBytes(count: 8)
        var value: UInt64 = 0

        for (index, byte) in bytes.enumerated() {
            value |= UInt64(byte) << UInt64(index * 8)
        }

        return value
    }

    mutating func readDouble() throws -> Double {
        Double(bitPattern: try readUInt64())
    }
}
