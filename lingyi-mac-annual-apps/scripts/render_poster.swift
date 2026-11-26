// [INPUT]: 命令行参数：<apps-data.json> <bg_image|auto> <icons_dir> <output.png> [title] [subtitle] [--font sans|serif] [--author <name>] [--style photo|night|minimal] [--wallpaper auto|<path>] [--no-rounded]
// [OUTPUT]: 在 output.png 生成 2400x1350 高清《年度 Mac 常用软件》海报 PNG，支持宋体/无衬线、自动桌面壁纸、渐变预设与左下角署名
// [POS]: mac-annual-apps 零依赖离线海报渲染器，基于 AppKit/CoreGraphics，供 CLI 与 Skill 一键出图
// [PROTOCOL]: Update this header on change, then check GEMINI.md

import AppKit
import CoreImage
import Foundation

struct Payload: Decodable {
    let meta: Meta
    let recommendedGroups: [GroupItem]
    let allApps: [AppRecord]
}

struct Meta: Decodable {
    let defaultTitle: String?
    let windowDays: Int?
    let totalInstalled: Int?
    let activeRecentCount: Int?
}

struct GroupItem: Decodable {
    let id: String
    let name: String
    let appIds: [String]
}

struct AppRecord: Decodable {
    let id: String
    let name: String
    let activeDaysRecent: Int?
    let usageHours: Double?
}

// ======================== CLI 参数解析 ========================

var positional: [String] = []
var fontStyle = "sans"        // sans | serif
var authorName: String? = "lingyi"
var posterStyle = "photo"     // photo | night | minimal
var wallpaperOverride: String? = nil
var roundedCard = true
var blurRadius: Double = 0.0
var showBadge = false

let rawArgs = Array(CommandLine.arguments.dropFirst())
var idx = 0
while idx < rawArgs.count {
    let arg = rawArgs[idx]
    switch arg {
    case "--font":
        if idx + 1 < rawArgs.count {
            fontStyle = rawArgs[idx + 1].lowercased()
            idx += 2
        } else {
            idx += 1
        }
    case "--author":
        if idx + 1 < rawArgs.count {
            let val = rawArgs[idx + 1].trimmingCharacters(in: .whitespacesAndNewlines)
            authorName = val.isEmpty ? nil : val
            idx += 2
        } else {
            idx += 1
        }
    case "--style":
        if idx + 1 < rawArgs.count {
            posterStyle = rawArgs[idx + 1].lowercased()
            idx += 2
        } else {
            idx += 1
        }
    case "--wallpaper":
        if idx + 1 < rawArgs.count {
            wallpaperOverride = rawArgs[idx + 1]
            idx += 2
        } else {
            idx += 1
        }
    case "--no-author":
        authorName = nil
        idx += 1
    case "--blur":
        if idx + 1 < rawArgs.count, let val = Double(rawArgs[idx + 1]) {
            blurRadius = max(0.0, min(30.0, val))
            idx += 2
        } else {
            idx += 1
        }
    case "--badge":
        showBadge = true
        idx += 1
    case "--no-rounded":
        roundedCard = false
        idx += 1
    default:
        positional.append(arg)
        idx += 1
    }
}

guard positional.count >= 4 else {
    fputs("Usage: swift render_poster.swift <apps-data.json> <bg_image|auto> <icons_dir> <output.png> [title] [subtitle] [--font sans|serif] [--author <name>] [--style photo|night|minimal] [--wallpaper auto|<path>] [--no-rounded]\n", stderr)
    exit(1)
}

let jsonURL = URL(fileURLWithPath: positional[0])
let bgArg = wallpaperOverride ?? positional[1]
let iconsDir = URL(fileURLWithPath: positional[2], isDirectory: true)
let outURL = URL(fileURLWithPath: positional[3])
let customTitle = positional.count >= 5 && !positional[4].isEmpty ? positional[4] : nil
let customSubtitle = positional.count >= 6 && !positional[5].isEmpty ? positional[5] : nil

let width: CGFloat = 2400
let height: CGFloat = 1350

// ======================== 绘制辅助函数 ========================

func applyBlur(_ image: NSImage, radius: Double) -> NSImage {
    guard radius > 0,
          let tiff = image.tiffRepresentation,
          let ciInput = CIImage(data: tiff) else {
        return image
    }
    let extent = ciInput.extent
    let clamped = ciInput.clampedToExtent()
    guard let blurFilter = CIFilter(name: "CIGaussianBlur") else { return image }
    blurFilter.setValue(clamped, forKey: kCIInputImageKey)
    blurFilter.setValue(radius * 1.6, forKey: kCIInputRadiusKey)
    guard let output = blurFilter.outputImage?.cropped(to: extent) else { return image }
    let ciContext = CIContext(options: nil)
    guard let cgImg = ciContext.createCGImage(output, from: extent) else { return image }
    return NSImage(cgImage: cgImg, size: image.size)
}

func drawCoverImage(_ image: NSImage, in rect: CGRect) {
    let imgSize = image.size
    guard imgSize.width > 0, imgSize.height > 0 else { return }
    let imgRatio = imgSize.width / imgSize.height
    let rectRatio = rect.width / rect.height

    var drawRect = rect
    if imgRatio > rectRatio {
        let newW = rect.height * imgRatio
        drawRect = CGRect(x: rect.minX + (rect.width - newW) / 2, y: rect.minY, width: newW, height: rect.height)
    } else {
        let newH = rect.width / imgRatio
        drawRect = CGRect(x: rect.minX, y: rect.minY + (rect.height - newH) / 2, width: rect.width, height: newH)
    }
    image.draw(in: drawRect, from: .zero, operation: .sourceOver, fraction: 1.0)
}

func resolveBackgroundImage(_ spec: String) -> (image: NSImage?, usedDesktopWallpaper: Bool) {
    if spec.lowercased() == "auto" {
        if let screen = NSScreen.main,
           let desktopURL = NSWorkspace.shared.desktopImageURL(for: screen),
           let img = NSImage(contentsOf: desktopURL),
           img.size.width > 0, img.size.height > 0 {
            return (img, true)
        }
        return (nil, false)
    }
    let url = URL(fileURLWithPath: spec)
    if let img = NSImage(contentsOf: url), img.size.width > 0, img.size.height > 0 {
        return (img, false)
    }
    return (nil, false)
}

func drawMinimalTealGradient(in cg: CGContext, rect: CGRect) {
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    let bgColors = [
        CGColor(red: 0.055, green: 0.145, blue: 0.200, alpha: 1.0),
        CGColor(red: 0.125, green: 0.225, blue: 0.255, alpha: 1.0),
        CGColor(red: 0.195, green: 0.310, blue: 0.295, alpha: 1.0),
    ] as CFArray
    if let grad = CGGradient(colorsSpace: colorSpace, colors: bgColors, locations: [0.0, 0.55, 1.0]) {
        cg.drawLinearGradient(
            grad,
            start: CGPoint(x: 0, y: 0),
            end: CGPoint(x: rect.width, y: rect.height),
            options: []
        )
    }
}

// ======================== 主渲染流程 ========================

do {
    let data = try Data(contentsOf: jsonURL)
    let payload = try JSONDecoder().decode(Payload.self, from: data)
    let appsById = Dictionary(uniqueKeysWithValues: payload.allApps.map { ($0.id, $0) })
    let groups = payload.recommendedGroups.filter { !$0.appIds.isEmpty }
    let title = customTitle ?? payload.meta.defaultTitle ?? "2026 我的 Mac 常用软件"

    guard let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: Int(width),
        pixelsHigh: Int(height),
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    ) else {
        fputs("Failed to create bitmap context\n", stderr)
        exit(1)
    }

    rep.size = NSSize(width: width, height: height)
    NSGraphicsContext.saveGraphicsState()
    guard let nsCtx = NSGraphicsContext(bitmapImageRep: rep) else {
        fputs("Failed to create NSGraphicsContext\n", stderr)
        exit(1)
    }
    NSGraphicsContext.current = nsCtx
    nsCtx.imageInterpolation = .high
    let cg = nsCtx.cgContext

    let fullRect = CGRect(x: 0, y: 0, width: width, height: height)

    // 外层圆角裁剪
    if roundedCard {
        let cardPath = NSBezierPath(roundedRect: fullRect, xRadius: 56, yRadius: 56)
        cardPath.addClip()
    }

    // 1. 绘制背景（支持 minimal 渐变 / 自动桌面壁纸 / 指定摄影图）
    var usedWallpaper = false
    if posterStyle == "minimal" {
        drawMinimalTealGradient(in: cg, rect: fullRect)
    } else {
        let bgResult = resolveBackgroundImage(bgArg)
        if let bgImage = bgResult.image {
            let finalBg = blurRadius > 0 ? applyBlur(bgImage, radius: blurRadius) : bgImage
            drawCoverImage(finalBg, in: fullRect)
            usedWallpaper = bgResult.usedDesktopWallpaper
        } else {
            drawMinimalTealGradient(in: cg, rect: fullRect)
        }
    }

    // 2. 左侧暗角线性渐变遮罩（保证白色文字清晰通透）
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    let scrimBoost: CGFloat = posterStyle == "night" ? 0.14 : (posterStyle == "minimal" ? -0.18 : 0.0)
    let scrimColors = [
        CGColor(red: 0.02, green: 0.03, blue: 0.04, alpha: min(0.92, max(0.25, 0.76 + scrimBoost))),
        CGColor(red: 0.02, green: 0.03, blue: 0.04, alpha: min(0.76, max(0.15, 0.42 + scrimBoost))),
        CGColor(red: 0.02, green: 0.03, blue: 0.04, alpha: min(0.45, max(0.06, 0.14 + scrimBoost * 0.5))),
    ] as CFArray
    if let grad = CGGradient(colorsSpace: colorSpace, colors: scrimColors, locations: [0.0, 0.56, 1.0]) {
        cg.drawLinearGradient(
            grad,
            start: CGPoint(x: 0, y: height / 2),
            end: CGPoint(x: width, y: height / 2),
            options: []
        )
    }

    // 底部柔和压暗
    let bottomColors = [
        CGColor(red: 0.0, green: 0.0, blue: 0.0, alpha: 0.44),
        CGColor(red: 0.0, green: 0.0, blue: 0.0, alpha: 0.0),
    ] as CFArray
    if let bGrad = CGGradient(colorsSpace: colorSpace, colors: bottomColors, locations: [0.0, 1.0]) {
        cg.drawLinearGradient(
            bGrad,
            start: CGPoint(x: width / 2, y: 0),
            end: CGPoint(x: width / 2, y: height * 0.35),
            options: []
        )
    }

    // 3. 字体配置（sans 无衬线 / serif 杂志宋体）
    let isSerif = (fontStyle == "serif")
    let titleFont = isSerif
        ? (NSFont(name: "STSongti-SC-Bold", size: 92) ?? NSFont.systemFont(ofSize: 88, weight: .bold))
        : (NSFont(name: "PingFangSC-Semibold", size: 84) ?? NSFont.systemFont(ofSize: 84, weight: .bold))
    let catFont = isSerif
        ? (NSFont(name: "STSongti-SC-Bold", size: 38) ?? NSFont.systemFont(ofSize: 36, weight: .semibold))
        : (NSFont(name: "PingFangSC-Medium", size: 34) ?? NSFont.systemFont(ofSize: 34, weight: .medium))
    let appFont = NSFont(name: "PingFangSC-Regular", size: 24) ?? NSFont.systemFont(ofSize: 24, weight: .regular)

    let padX: CGFloat = 112
    let titleShadow = NSShadow()
    titleShadow.shadowColor = NSColor(white: 0, alpha: 0.52)
    titleShadow.shadowBlurRadius = 18
    titleShadow.shadowOffset = NSSize(width: 0, height: -6)

    let titleAttrs: [NSAttributedString.Key: Any] = [
        .font: titleFont,
        .foregroundColor: NSColor(calibratedRed: 0.996, green: 0.986, blue: 0.960, alpha: 1.0),
        .shadow: titleShadow,
    ]
    let titleNS = NSString(string: title)
    titleNS.draw(at: NSPoint(x: padX, y: height - 120 - 104), withAttributes: titleAttrs)

    // 4. 自适应计算多行图标网格
    let rowCount = max(1, groups.count)
    let gridTopFromTop: CGFloat = 276
    let gridBottomFromTop: CGFloat = height - 96
    let availableH = gridBottomFromTop - gridTopFromTop

    let labelColWidth: CGFloat = 236
    let iconsStartX = padX + labelColWidth
    let iconsAreaWidth = width - iconsStartX - padX
    let maxRowItems = max(1, groups.map { $0.appIds.count }.max() ?? 1)

    let idealRowH = availableH / CGFloat(rowCount)
    let iconSize = floor(min(
        142,
        max(88, idealRowH - 68),
        max(88, (iconsAreaWidth - CGFloat(maxRowItems - 1) * 44) / CGFloat(max(maxRowItems, 6)))
    ))
    let colGap: CGFloat = maxRowItems > 1
        ? floor(min(68, max(26, (iconsAreaWidth - CGFloat(maxRowItems) * iconSize) / CGFloat(maxRowItems - 1))))
        : 60

    let textShadow = NSShadow()
    textShadow.shadowColor = NSColor(white: 0, alpha: 0.72)
    textShadow.shadowBlurRadius = 8
    textShadow.shadowOffset = NSSize(width: 0, height: -2)

    let catAttrs: [NSAttributedString.Key: Any] = [
        .font: catFont,
        .foregroundColor: NSColor(white: 1.0, alpha: 0.95),
        .shadow: textShadow,
    ]

    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = .center
    paragraph.lineBreakMode = .byTruncatingTail
    let appAttrs: [NSAttributedString.Key: Any] = [
        .font: appFont,
        .foregroundColor: NSColor(white: 1.0, alpha: 0.94),
        .paragraphStyle: paragraph,
        .shadow: textShadow,
    ]

    for (rowIdx, group) in groups.enumerated() {
        let rowCenterFromTop = gridTopFromTop + idealRowH * (CGFloat(rowIdx) + 0.5)
        let iconTopFromTop = floor(rowCenterFromTop - (iconSize + 36) / 2)
        let iconBottomY = height - iconTopFromTop - iconSize

        // 左侧分类名称
        let catSize = NSString(string: group.name).size(withAttributes: catAttrs)
        let catY = iconBottomY + (iconSize - catSize.height) / 2
        NSString(string: group.name).draw(at: NSPoint(x: padX, y: catY), withAttributes: catAttrs)

        // 右侧每行软件图标与名称
        for (colIdx, appId) in group.appIds.enumerated() {
            guard let app = appsById[appId] else { continue }
            let x = iconsStartX + CGFloat(colIdx) * (iconSize + colGap)
            let iconRect = CGRect(x: x, y: iconBottomY, width: iconSize, height: iconSize)

            cg.saveGState()
            cg.setShadow(offset: CGSize(width: 0, height: -10), blur: 22, color: CGColor(red: 0, green: 0, blue: 0, alpha: 0.45))
            let iconPath = iconsDir.appendingPathComponent("\(app.id).png")
            if let iconImg = NSImage(contentsOf: iconPath) {
                iconImg.draw(in: iconRect, from: .zero, operation: .sourceOver, fraction: 1.0)
            }
            cg.restoreGState()

            if showBadge {
                let hours = app.usageHours ?? 0.0
                let days = app.activeDaysRecent ?? 0
                let badgeText: String
                if hours >= 1.0 {
                    badgeText = hours >= 10.0 ? "\(Int(hours.rounded()))h" : String(format: "%.1fh", hours)
                } else if hours > 0.0 {
                    badgeText = "\(max(1, Int((hours * 60.0).rounded())))m"
                } else if days > 0 {
                    badgeText = "\(days)d"
                } else {
                    badgeText = ""
                }
                if !badgeText.isEmpty {
                    let badgeFont = NSFont(name: "PingFangSC-Semibold", size: 18) ?? NSFont.systemFont(ofSize: 18, weight: .semibold)
                    let badgeAttrs: [NSAttributedString.Key: Any] = [
                        .font: badgeFont,
                        .foregroundColor: NSColor(calibratedRed: 0.984, green: 0.749, blue: 0.141, alpha: 1.0),
                    ]
                    let textSize = NSString(string: badgeText).size(withAttributes: badgeAttrs)
                    let bw = textSize.width + 18
                    let bh: CGFloat = 28
                    let bx = x + iconSize - bw + 6
                    let by = iconBottomY + iconSize - bh + 6
                    let badgeRect = CGRect(x: bx, y: by, width: bw, height: bh)
                    let pill = NSBezierPath(roundedRect: badgeRect, xRadius: 14, yRadius: 14)
                    NSColor(calibratedRed: 0.06, green: 0.07, blue: 0.10, alpha: 0.88).setFill()
                    pill.fill()
                    NSColor(white: 1.0, alpha: 0.25).setStroke()
                    pill.lineWidth = 1.5
                    pill.stroke()
                    NSString(string: badgeText).draw(
                        at: NSPoint(x: bx + (bw - textSize.width) / 2, y: by + (bh - textSize.height) / 2),
                        withAttributes: badgeAttrs
                    )
                }
            }

            let labelWidth = iconSize + colGap - 10
            let labelRect = CGRect(
                x: x + iconSize / 2 - labelWidth / 2,
                y: iconBottomY - 42,
                width: labelWidth,
                height: 34
            )
            NSString(string: app.name).draw(in: labelRect, withAttributes: appAttrs)
        }
    }

    // 5. 底部左右信息栏（左下角署名 + 右下角统计/备注）
    let footerFont = NSFont(name: "PingFangSC-Regular", size: 24) ?? NSFont.systemFont(ofSize: 24, weight: .regular)
    let footerAttrs: [NSAttributedString.Key: Any] = [
        .font: footerFont,
        .foregroundColor: NSColor(white: 1.0, alpha: 0.72),
        .shadow: textShadow,
    ]

    if let author = authorName {
        let needsSpace = author.last.map { $0.isASCII && ($0.isLetter || $0.isNumber) } ?? false
        let authorLabel = author.hasSuffix("推荐") ? author : "\(author)\(needsSpace ? " " : "")的推荐"
        NSString(string: authorLabel).draw(at: NSPoint(x: padX, y: 42), withAttributes: footerAttrs)
    }

    if let sub = customSubtitle {
        let subSize = NSString(string: sub).size(withAttributes: footerAttrs)
        NSString(string: sub).draw(
            at: NSPoint(x: width - 88 - subSize.width, y: 42),
            withAttributes: footerAttrs
        )
    }

    // 内高光细边框
    if roundedCard {
        NSColor(white: 1.0, alpha: 0.14).setStroke()
        let borderPath = NSBezierPath(roundedRect: fullRect.insetBy(dx: 1, dy: 1), xRadius: 55, yRadius: 55)
        borderPath.lineWidth = 2
        borderPath.stroke()
    }

    NSGraphicsContext.restoreGraphicsState()

    try FileManager.default.createDirectory(at: outURL.deletingLastPathComponent(), withIntermediateDirectories: true)
    guard let pngData = rep.representation(using: .png, properties: [:]) else {
        fputs("Failed to encode PNG\n", stderr)
        exit(1)
    }
    try pngData.write(to: outURL)
    print("Poster rendered successfully: \(outURL.path) (\(Int(width))x\(Int(height)), font=\(fontStyle), style=\(posterStyle), desktopWallpaper=\(usedWallpaper))")
} catch {
    fputs("Error: \(error)\n", stderr)
    exit(1)
}
