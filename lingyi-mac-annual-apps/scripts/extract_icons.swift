// [INPUT]: 接收两个命令行参数：待提取图标的 JSON 清单路径（[{id, path}]）与输出目录路径
// [OUTPUT]: 在输出目录生成每个 .app 对应的 256x256 高清透明 PNG 图标文件（<id>.png）
// [POS]: mac-annual-apps 核心图标提取器，由 scan_mac_apps.py 调用，基于 macOS AppKit 原生还原系统图标
// [PROTOCOL]: Update this header on change, then check GEMINI.md

import AppKit
import Foundation

struct AppItem: Decodable {
    let id: String
    let path: String
}

let args = CommandLine.arguments
guard args.count >= 3 else {
    fputs("Usage: swift extract_icons.swift <manifest.json> <output_dir>\n", stderr)
    exit(1)
}

let manifestURL = URL(fileURLWithPath: args[1])
let outputDirURL = URL(fileURLWithPath: args[2], isDirectory: true)

do {
    try FileManager.default.createDirectory(at: outputDirURL, withIntermediateDirectories: true)
    let data = try Data(contentsOf: manifestURL)
    let items = try JSONDecoder().decode([AppItem].self, from: data)
    let workspace = NSWorkspace.shared
    let targetSize = NSSize(width: 256, height: 256)

    var successCount = 0
    for item in items {
        let outURL = outputDirURL.appendingPathComponent("\(item.id).png")
        let resolvedPath = URL(fileURLWithPath: item.path).resolvingSymlinksInPath().path
        let icon = workspace.icon(forFile: resolvedPath)
        icon.size = targetSize

        guard let rep = NSBitmapImageRep(
            bitmapDataPlanes: nil,
            pixelsWide: 256,
            pixelsHigh: 256,
            bitsPerSample: 8,
            samplesPerPixel: 4,
            hasAlpha: true,
            isPlanar: false,
            colorSpaceName: .deviceRGB,
            bytesPerRow: 0,
            bitsPerPixel: 0
        ) else {
            continue
        }

        rep.size = targetSize
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
        NSGraphicsContext.current?.imageInterpolation = .high
        icon.draw(in: NSRect(origin: .zero, size: targetSize),
                  from: .zero,
                  operation: .sourceOver,
                  fraction: 1.0)
        NSGraphicsContext.restoreGraphicsState()

        if let pngData = rep.representation(using: .png, properties: [:]) {
            try? pngData.write(to: outURL)
            successCount += 1
        }
    }

    print("Extracted \(successCount)/\(items.count) icons to \(outputDirURL.path)")
} catch {
    fputs("Error: \(error)\n", stderr)
    exit(1)
}
