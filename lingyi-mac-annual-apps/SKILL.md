---
name: lingyi-mac-annual-apps
description: Scan locally installed macOS applications and rank them by real foreground usage duration (macOS Screen Time knowledgeC.db, ActivityWatch, with Spotlight fallback), extract native high-resolution .app icons, render a 2400x1350 annual Mac software showcase poster PNG, export a usage CSV, and launch a shareable interactive web editor. Use whenever the user asks to generate their "年度 Mac 常用软件" / "Mac annual apps" poster, analyze which Mac apps they spend the most time in, create a software recommendation graphic like @HiTw93 or @vista8, or share their Mac app stack.
metadata:
  author: lingyi
  version: "2.0.0"
---

# Mac Annual Apps Poster & Showcase

Automate scanning locally installed macOS `.app` bundles, ranking them by Spotlight usage frequency, extracting native `256x256` icons, rendering a `2400x1350` retina poster PNG, and optionally launching a zero-build interactive web editor for customization and sharing.

## Bundled Resources

- `scripts/scan_mac_apps.py`: Discovers installed `.app` bundles across `/Applications`, `~/Applications`, and `/System/Applications`, queries Spotlight (`mdls`) for recent active days and use counts, auto-categorizes apps, extracts icons, and writes `public/data/apps-data.json` + `output/mac-apps-usage.csv`.
- `scripts/extract_icons.swift`: Resolves symlinks and renders native `256x256` transparent PNG icons via AppKit (`NSWorkspace`). Invoked automatically by `scan_mac_apps.py`.
- `scripts/render_poster.swift`: Zero-dependency CoreGraphics/AppKit renderer that produces a `2400x1350` rounded-corner PNG poster directly from `apps-data.json`, a background photo, and extracted icons.
- `assets/night-foliage.jpg`: Default moody night-time foliage photography backdrop.
- `assets/web/`: Zero-build HTML5 Canvas 2D interactive poster editor & shareable web app (`index.html`, `styles.css`, `poster-renderer.js`, `app.js`).

## Workflow

### Step 1: Prepare a Workspace Directory

Choose an output project directory (e.g., `./mac-annual-apps` or `/Users/<user>/.gemini/antigravity/scratch/mac-annual-apps`) and copy `assets/web/*` into `<project_dir>/public/` and `assets/night-foliage.jpg` into `<project_dir>/public/backgrounds/`.

### Step 2: Scan Local Mac Apps & Foreground Usage Duration

Run the scanner script (requires macOS Full Disk Access for `~/Library/Application Support/Knowledge/knowledgeC.db` to read real Screen Time foreground duration; if unavailable, it automatically falls back to ActivityWatch and then Spotlight `mdls`):

```bash
python3 <skill_dir>/scripts/scan_mac_apps.py \
  --project-dir <project_dir> \
  --days 365 \
  --max-apps 24
```

Key flags:
- `--days <N>`: Lookback window in days (default: `365` for full year; note macOS `knowledgeC.db` retains roughly the latest ~28–30 days of detailed foreground events and reports the exact covered date range).
- `--max-apps <N>`: Number of recommended apps selected for the default poster (default: `24`).
- `--reclassify-from <json>`: Re-run categorization/grouping from an existing `apps-data.json` without re-querying Spotlight.

Outputs created:
- `<project_dir>/public/data/apps-data.json`
- `<project_dir>/public/icons/<id>.png`
- `<project_dir>/output/mac-apps-usage.csv`

### Step 3: Render the 2400x1350 Poster PNG

Render directly via Swift (zero external dependencies):

```bash
swift <skill_dir>/scripts/render_poster.swift \
  <project_dir>/public/data/apps-data.json \
  <project_dir>/public/backgrounds/night-foliage.jpg \
  <project_dir>/public/icons \
  <project_dir>/output/my-mac-apps.png \
  "2026 我的 Mac 常用软件" \
  "基于本机近 365 天活跃统计" \
  --font serif \
  --author "lingyi" \
  --style photo
```

Optional rendering flags:
- `--font sans|serif`: Switch between PingFang sans-serif (`sans`, default) and editorial Songti serif (`serif`, applied to both main heading and category labels).
- `--author "<name>"`: Prints `<name> 的推荐` at the bottom-left corner (defaults to `lingyi`; pass `--no-author` or `--author ""` to hide).
- `--style photo|night|minimal`: `photo` (default), `night` (deeper scrim), or `minimal` (deep-teal editorial gradient without backdrop photo).
- `--wallpaper auto|<path>`: Pass `auto` (or set `<bg_image>` to `auto`) to automatically read the current macOS desktop wallpaper (gracefully falls back to deep-teal gradient if unavailable).
- `--no-rounded`: Disable outer rounded corners for full-bleed output.

### Step 4: Launch the Interactive Web Editor (Optional)

To let the user interactively edit categories, swap apps from the full installed library, switch backdrops, upload a custom photo, copy a `#share=...` link, or export PNG/CSV/JSON:

```bash
python3 -m http.server 8765 --directory <project_dir>/public
```

Then direct the user to `http://localhost:8765`.

### Step 5: Publish & Revoke on MacStack · lingyi (Optional)

Only after the user previews the poster and explicitly chooses visibility (`public` or `link`), publish via:

```bash
python3 <skill_dir>/scripts/publish_share.py publish \
  --image <project_dir>/output/my-mac-apps.png \
  --data <project_dir>/public/data/apps-data.json \
  --author "lingyi" \
  --visibility public
```

To withdraw a published poster using its local receipt (`<image>.share.json`):

```bash
python3 <skill_dir>/scripts/publish_share.py revoke \
  --receipt <project_dir>/output/my-mac-apps.png.share.json
```
