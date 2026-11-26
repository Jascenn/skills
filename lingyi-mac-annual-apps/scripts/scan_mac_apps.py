#!/usr/bin/env python3
"""
[INPUT]: 读取本机 /Applications、~/Applications、/System/Applications 中的 .app 包、Info.plist 及 Spotlight(mdls) 使用记录；调用同目录 extract_icons.swift
[OUTPUT]: 生成结构化应用数据 JSON（apps-data.json）、完整活跃度清单 CSV（mac-apps-usage.csv）以及 256x256 高清图标 PNG 集合
[POS]: mac-annual-apps 的核心数据采集与排序引擎，同时服务于本机海报生成、Web 工具数据源与可复用 Skill
[PROTOCOL]: Update this header on change, then check GEMINI.md
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import plistlib
import re
import sqlite3
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

# ======================== 常量与分类规则 ========================

SCAN_ROOTS = [
    Path("/Applications"),
    Path.home() / "Applications",
    Path("/System/Applications"),
]

# 默认过滤的系统底层组件或卸载器（仍保留在 allApps 中，仅不自动入选推荐海报）
NOISE_PATTERNS = [
    r"uninstall",
    r"updater",
    r"helper",
    r"pluginservice",
    r"activation tool",
    r"migration assistant",
    r"boot camp",
    r"voiceover",
    r"screen sharing",
    r"bluetooth file exchange",
    r"colorSync",
    r"digital color meter",
    r"grapher",
    r"keychain access",
    r"system information",
    r"audio midi",
    r"disk utility",
    r"script editor",
    r"automator",
    r"image capture",
    r"photo booth",
    r"chess",
    r"stickies",
    r"launchpad",
    r"mission control",
    r"siri",
    r"time machine",
    r"system settings",
    r"system preferences",
    r"app store",
    r"font book",
    r"find my",
    r"home$",
    r"stocks",
    r"weather",
    r"clock",
    r"calculator",
    r"dictionary",
    r"quicktime player",
    r"textedit",
    r"preview",
    r"tv$",
    r"podcasts",
    r"books$",
    r"maps$",
    r"contacts$",
    r"facetime",
    r"messages$",
    r"mail$",
    r"photos$",
    r"reminders$",
    r"calendar$",
    r"freeform",
    r"passwords",
    r"shortcuts",
    r"tips$",
    r"iphone mirroring",
    r"activity monitor",
    r"console$",
    r"terminal$",
]

# 分类优先级与关键词映射（仅针对应用名、文件名、bundleId 匹配）
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    (
        "AI 与开发",
        [
            "claude", "codex", "chatgpt", "antigravity", "cursor", "windsurf",
            "visual studio code", "vscode", "xcode", "zed", "trae", "kiro",
            "zcode", "workbuddy", "t3 code", "t3code", "deepseek", "doubao",
            "豆包", "kimi", "yuanbao", "元宝", "cherry studio", "chatbox",
            "lm studio", "ollama", "grok", "cromma", "agenttaskpanel", "agent-task-panel",
            "warp", "ghostty", "iterm", "kaku", "alacritty", "kitty", "wezterm",
            "tabby", "docker", "orbstack", "postman", "apifox", "insomnia",
            "proxyman", "charles", "wireshark", "tableplus", "dbeaver",
            "datagrip", "navicat", "goland", "pycharm", "webstorm", "intellij",
            "android studio", "github", "fork", "sourcetree", "tower",
            "sublime", "nova", "parallels", "vmware", "utm", "wbswitch", "zswitch",
        ],
    ),
    (
        "浏览与沟通",
        [
            "chrome", "company.thebrowser", "arc browser", "dia", "comet",
            "helium", "ego lite", "ego-lite", "safari", "firefox", "edge",
            "brave", "vivaldi", "zen browser", "opera", "adspower",
            "wechat", "微信", "企业微信", "wecom", "feishu", "lark", "飞书",
            "dingtalk", "钉钉", "slack", "telegram", "ayugram", "discord",
            "whatsapp", "tencent.qq", "tencent meeting", "腾讯会议", "zoom",
            "clash", "flclash", "mihomo", "surge", "stash", "shadowrocket",
            "loon", "sing-box", "v2ray", "tailscale", "zerotier",
            "netnewswire", "reeder", "folo",
        ],
    ),
    (
        "写作与知识",
        [
            "obsidian", "notion", "miaoyan", "妙言", "typora", "bear", "craft",
            "logseq", "ulysses", "ia writer", "roam", "heptabase", "flomo",
            "cubox", "readwise", "anki", "marginnote", "zotero", "mweb",
            "refto", "today", "cron.electron", "microsoft word", "microsoft excel",
            "microsoft powerpoint", "onenote", "wps", "pages", "numbers",
            "keynote", "备忘录", "印象笔记", "evernote", "语雀", "yuque",
            "xmind", "mindnode", "weread", "微信读书", "kindle", "calibre",
            "updf", "magpie",
        ],
    ),
    (
        "效率与工具",
        [
            "raycast", "alfred", "tinycast", "1password", "bitwarden", "keepass",
            "bob", "easydict", "poptranslate", "eudic", "欧路", "deepl",
            "cleanshot", "shottr", "1capture", "pixpin", "snipaste", "xsnip",
            "ishot", "input source", "mole", "闪电说", "typeless", "wispr",
            "superwhisper", "macwhisper", "top calendar", "itsycal", "upic",
            "piclist", "picgo", "command x", "bartender", "ice", "hidden bar",
            "betterdisplay", "monitorcontrol", "rectangle", "magnet", "loop",
            "moom", "wins", "contexts", "popclip", "soundsource", "istat",
            "lulu", "yansu", "karabiner", "hammerspoon", "keyboard maestro",
            "hazel", "dropzone", "yoink", "paste", "maccy", "cleanclip",
            "alttab", "stats", "aldente", "amphetamine", "caffeine", "keka",
            "the unarchiver", "uu远程", "todesk", "sunlogin", "向日葵",
            "rustdesk", "teamviewer", "anydesk", "activitywatch", "微信输入法",
            "wetype", "rime", "squirrel", "cleanmymac", "pearcleaner",
            "appcleaner", "transmit", "cyberduck", "termius", "localsend",
        ],
    ),
    (
        "影音与创作",
        [
            "figma", "sketch", "framer", "screen studio", "loom", "obs",
            "capcut", "剪映", "jianying", "final cut", "davinci", "premiere",
            "after effects", "photoshop", "illustrator", "lightroom",
            "pixelmator", "affinity", "blender", "cinema 4d", "logic pro",
            "ableton", "spotify", "apple music", "netease", "网易云",
            "qqmusic", "qq音乐", "汽水音乐", "lx music", "yesplaymusic",
            "iina", "infuse", "vlc", "mpv", "potplayer", "bilibili",
            "哔哩哔哩", "抖音", "douyin", "youtube", "netflix", "爱奇艺",
            "腾讯视频", "优酷", "喜马拉雅", "小宇宙", "capwise", "subcast",
            "macgacha", "爱壹帆", "红果短剧",
        ],
    ),
]

APPLE_CAT_MAP = {
    "developer-tools": "AI 与开发",
    "social-networking": "浏览与沟通",
    "graphics-design": "影音与创作",
    "video": "影音与创作",
    "music": "影音与创作",
    "photography": "影音与创作",
    "entertainment": "影音与创作",
    "games": "影音与创作",
    "productivity": "效率与工具",
    "utilities": "效率与工具",
}

FOLDER_HINT_TO_CATEGORY = {
    "开发": "AI 与开发",
    "效率": "效率与工具",
    "办公": "写作与知识",
    "多媒体": "影音与创作",
}


# ======================== 辅助函数 ========================

def slugify(name: str, path_str: str) -> str:
    """生成稳定、URL/文件名安全的唯一 slug。"""
    base = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    short_hash = hashlib.md5(path_str.encode("utf-8")).hexdigest()[:6]
    return f"{base}-{short_hash}" if base else f"app-{short_hash}"


def read_info_plist(app_path: Path) -> dict[str, Any]:
    plist_path = app_path / "Contents" / "Info.plist"
    if not plist_path.exists():
        return {}
    try:
        with plist_path.open("rb") as f:
            data = plistlib.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def discover_apps() -> list[dict[str, Any]]:
    """递归发现本机已安装 .app（最多深入两层子目录）。"""
    discovered: list[dict[str, Any]] = []
    seen_realpaths: set[str] = set()

    def walk_dir(directory: Path, depth: int, folder_hint: str) -> None:
        if not directory.exists() or not directory.is_dir():
            return
        try:
            entries = sorted(directory.iterdir(), key=lambda p: p.name.lower())
        except PermissionError:
            return

        for entry in entries:
            if entry.name.startswith("."):
                continue
            if entry.suffix == ".app" and entry.is_dir():
                real_str = str(entry.resolve())
                if real_str in seen_realpaths:
                    continue
                seen_realpaths.add(real_str)

                info = read_info_plist(entry)
                raw_name = entry.stem
                bundle_id = str(info.get("CFBundleIdentifier") or "")
                display_name = (
                    str(info.get("CFBundleDisplayName") or "")
                    or str(info.get("CFBundleName") or "")
                    or raw_name
                )
                # 如果文件名含中文（如 微信.app、哔哩哔哩.app），优先保留文件名更贴近用户习惯
                if re.search(r"[\u4e00-\u9fff]", raw_name):
                    display_name = raw_name

                app_category = str(info.get("LSApplicationCategoryType") or "")
                version = str(info.get("CFBundleShortVersionString") or "")
                discovered.append(
                    {
                        "id": slugify(raw_name, real_str),
                        "name": display_name.strip(),
                        "fileName": raw_name,
                        "path": str(entry),
                        "bundleId": bundle_id,
                        "version": version,
                        "appleCategory": app_category,
                        "folderHint": folder_hint,
                        "isSystemApp": str(entry).startswith("/System/Applications"),
                    }
                )
            elif entry.is_dir() and depth < 2 and entry.name != "Utilities":
                next_hint = folder_hint or entry.name
                walk_dir(entry, depth + 1, next_hint)

    for root in SCAN_ROOTS:
        walk_dir(root, 0, "")

    return discovered


def discover_cli_tools(apps: list[dict[str, Any]]) -> None:
    """检测本机已安装的常用 AI CLI 工具（如 Claude Code），作为可选应用注入列表。"""
    import shutil

    existing_ids = {a["id"] for a in apps}
    by_bundle = {(a.get("bundleId") or "").lower(): a for a in apps}
    terminal_path = "/System/Applications/Utilities/Terminal.app"

    cli_specs = [
        {
            "id": "cli-claude-code",
            "name": "Claude Code",
            "bins": ["claude"],
            "fallback_paths": [Path.home() / ".local" / "bin" / "claude"],
            "icon_bundles": ["com.anthropic.claudefordesktop"],
            "bundleId": "cli:claude-code",
            "category": "AI 与开发",
        },
        {
            "id": "cli-codex",
            "name": "Codex CLI",
            "bins": ["codex"],
            "fallback_paths": [],
            "icon_bundles": ["com.openai.codex", "com.openai.chat"],
            "bundleId": "cli:codex",
            "category": "AI 与开发",
        },
        {
            "id": "cli-gemini",
            "name": "Gemini CLI",
            "bins": ["gemini"],
            "fallback_paths": [],
            "icon_bundles": [],
            "bundleId": "cli:gemini",
            "category": "AI 与开发",
        },
    ]

    for spec in cli_specs:
        if spec["id"] in existing_ids:
            continue
        found = any(shutil.which(b) for b in spec["bins"]) or any(
            p.is_file() for p in spec["fallback_paths"]
        )
        if not found:
            continue

        icon_app_path = terminal_path
        for bid in spec["icon_bundles"]:
            if bid in by_bundle:
                icon_app_path = by_bundle[bid]["path"]
                break

        apps.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "fileName": spec["name"],
                "path": icon_app_path,
                "bundleId": spec["bundleId"],
                "version": "",
                "appleCategory": "",
                "folderHint": "",
                "isSystemApp": False,
                "isCommandLine": True,
                "useCount": 0,
                "activeDaysRecent": 0,
                "activeDaysTotal": 0,
                "lastUsedDate": "",
                "daysSinceLastUse": None,
                "usageSeconds": 0.0,
                "usageHours": 0.0,
                "foregroundSwitches": 0,
                "score": 0.0,
                "note": "",
            }
        )


def query_spotlight_usage(apps: list[dict[str, Any]], recent_days: int) -> None:
    """批量调用 mdls 读取 Spotlight 活跃日期与使用次数，原地丰富每个应用字典。"""
    now_utc = dt.datetime.now(dt.timezone.utc)
    cutoff_utc = now_utc - dt.timedelta(days=recent_days)

    batch_size = 40
    for i in range(0, len(apps), batch_size):
        batch = apps[i : i + batch_size]
        paths = [a["path"] for a in batch]
        cmd = [
            "mdls",
            "-plist",
            "-",
            "-name",
            "kMDItemDisplayName",
            "-name",
            "kMDItemUseCount",
            "-name",
            "kMDItemLastUsedDate",
            "-name",
            "kMDItemUsedDates",
            *paths,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, check=False)
            raw = proc.stdout
            # 当批量传入多个路径时，mdls -plist - 会连续输出多个 XML plist 文档
            plist_chunks = re.findall(rb"<\?xml.*?</plist>", raw, flags=re.DOTALL)
        except Exception:
            plist_chunks = []

        # 如果数量一致直接一一对应，否则退化为单条回查
        if len(plist_chunks) == len(batch):
            parsed_list = []
            for chunk in plist_chunks:
                try:
                    parsed_list.append(plistlib.loads(chunk))
                except Exception:
                    parsed_list.append({})
        else:
            parsed_list = []
            for p in paths:
                try:
                    single = subprocess.run(
                        [
                            "mdls",
                            "-plist",
                            "-",
                            "-name",
                            "kMDItemDisplayName",
                            "-name",
                            "kMDItemUseCount",
                            "-name",
                            "kMDItemLastUsedDate",
                            "-name",
                            "kMDItemUsedDates",
                            p,
                        ],
                        capture_output=True,
                        check=False,
                    )
                    parsed_list.append(plistlib.loads(single.stdout) if single.stdout else {})
                except Exception:
                    parsed_list.append({})

        for app, meta in zip(batch, parsed_list):
            if not isinstance(meta, dict):
                meta = {}

            md_display = meta.get("kMDItemDisplayName")
            if isinstance(md_display, str) and md_display.strip():
                cleaned = md_display.strip()
                if cleaned.endswith(".app"):
                    cleaned = cleaned[:-4]
                # 仅在含中文且比当前更直观时覆盖
                if re.search(r"[\u4e00-\u9fff]", cleaned) and not re.search(r"[\u4e00-\u9fff]", app["name"]):
                    app["name"] = cleaned

            use_count = meta.get("kMDItemUseCount")
            use_count = int(use_count) if isinstance(use_count, (int, float)) else 0

            last_used = meta.get("kMDItemLastUsedDate")
            used_dates = meta.get("kMDItemUsedDates") or []

            recent_day_set: set[str] = set()
            total_day_set: set[str] = set()

            for d in used_dates:
                if isinstance(d, dt.datetime):
                    d_utc = d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
                    day_str = d_utc.astimezone().strftime("%Y-%m-%d")
                    total_day_set.add(day_str)
                    if d_utc >= cutoff_utc:
                        recent_day_set.add(day_str)

            last_used_str = ""
            days_since_last: int | None = None
            if isinstance(last_used, dt.datetime):
                lu_utc = last_used if last_used.tzinfo else last_used.replace(tzinfo=dt.timezone.utc)
                last_used_str = lu_utc.astimezone().strftime("%Y-%m-%d")
                days_since_last = max(0, (now_utc - lu_utc).days)
                if lu_utc >= cutoff_utc:
                    recent_day_set.add(last_used_str)
                total_day_set.add(last_used_str)

            active_days_recent = len(recent_day_set)
            active_days_total = len(total_day_set)

            # 计算综合活跃度评分：近 N 天活跃天数权重最高，其次是总活跃天数、使用次数和近期新鲜度
            recency_bonus = 0.0
            if days_since_last is not None:
                if days_since_last <= 7:
                    recency_bonus = 15.0
                elif days_since_last <= 30:
                    recency_bonus = 8.0
                elif days_since_last <= recent_days:
                    recency_bonus = 3.0

            score = (
                active_days_recent * 10.0
                + min(active_days_total, 120) * 0.4
                + min(use_count, 500) * 0.12
                + recency_bonus
            )

            app["useCount"] = use_count
            app["activeDaysRecent"] = active_days_recent
            app["activeDaysTotal"] = active_days_total
            app["lastUsedDate"] = last_used_str
            app["daysSinceLastUse"] = days_since_last
            app["usageSeconds"] = 0.0
            app["usageHours"] = 0.0
            app["foregroundSwitches"] = 0
            app["score"] = round(score, 2)


def query_knowledgec_usage(recent_days: int) -> tuple[dict[str, dict[str, Any]], str, dict[str, Any]]:
    """
    从 macOS 系统屏幕使用时间数据库 ~/Library/Application Support/Knowledge/knowledgeC.db
    读取近 N 天每个 bundleId 的真实前台累计使用时长、活跃天数与切换次数。
    需要终端或宿主应用具备 Full Disk Access 权限。
    """
    kc_path = Path.home() / "Library" / "Application Support" / "Knowledge" / "knowledgeC.db"
    if not kc_path.exists():
        return {}, "missing", {}

    apple_epoch = dt.datetime(2001, 1, 1, tzinfo=dt.timezone.utc)
    now_utc = dt.datetime.now(dt.timezone.utc)
    cutoff_apple = (now_utc - dt.timedelta(days=recent_days) - apple_epoch).total_seconds()
    now_apple = (now_utc + dt.timedelta(hours=2) - apple_epoch).total_seconds()

    try:
        con = sqlite3.connect(f"file:{kc_path}?mode=ro", uri=True)
        cur = con.cursor()
        rows = cur.execute(
            """
            SELECT ZVALUESTRING, ZSTARTDATE, ZENDDATE
            FROM ZOBJECT
            WHERE ZSTREAMNAME = '/app/usage'
              AND ZVALUESTRING IS NOT NULL
              AND ZSTARTDATE >= ?
              AND ZSTARTDATE <= ?
              AND ZENDDATE > ZSTARTDATE
              AND ZENDDATE <= ?
            """,
            (cutoff_apple, now_apple, now_apple),
        ).fetchall()
        con.close()
    except Exception as exc:
        return {}, f"unreadable:{exc}", {}

    stats: dict[str, dict[str, Any]] = {}
    day_sets: dict[str, set[str]] = defaultdict(set)
    min_ts: float | None = None
    max_ts: float | None = None

    for bundle_id, start_ts, end_ts in rows:
        bid = str(bundle_id).strip().lower()
        if not bid:
            continue
        dur = float(end_ts - start_ts)
        # 过滤单条异常超长记录（超过 12 小时通常是休眠边界）
        if dur <= 0 or dur > 43200:
            continue

        if min_ts is None or start_ts < min_ts:
            min_ts = start_ts
        if max_ts is None or end_ts > max_ts:
            max_ts = end_ts

        entry = stats.setdefault(
            bid,
            {"seconds": 0.0, "switches": 0, "lastTs": 0.0},
        )
        entry["seconds"] += dur
        entry["switches"] += 1
        if end_ts > entry["lastTs"]:
            entry["lastTs"] = end_ts

        day_str = (apple_epoch + dt.timedelta(seconds=start_ts)).astimezone().strftime("%Y-%m-%d")
        day_sets[bid].add(day_str)

    for bid, entry in stats.items():
        entry["activeDays"] = len(day_sets[bid])
        entry["lastUsedDate"] = (
            (apple_epoch + dt.timedelta(seconds=entry["lastTs"])).astimezone().strftime("%Y-%m-%d")
            if entry["lastTs"] > 0
            else ""
        )

    range_info: dict[str, Any] = {}
    if min_ts is not None and max_ts is not None:
        start_dt = (apple_epoch + dt.timedelta(seconds=min_ts)).astimezone()
        end_dt = (apple_epoch + dt.timedelta(seconds=max_ts)).astimezone()
        range_info = {
            "start": start_dt.strftime("%Y-%m-%d"),
            "end": end_dt.strftime("%Y-%m-%d"),
            "coveredDays": max(1, (end_dt.date() - start_dt.date()).days + 1),
        }

    return stats, ("ok" if stats else "empty"), range_info


def query_activitywatch_usage(recent_days: int) -> tuple[dict[str, dict[str, Any]], str]:
    """备选：从本机 ActivityWatch 数据库读取近 N 天窗口前台使用时长。"""
    aw_path = (
        Path.home()
        / "Library"
        / "Application Support"
        / "activitywatch"
        / "aw-server"
        / "peewee-sqlite.v2.db"
    )
    if not aw_path.exists():
        return {}, "missing"

    cutoff_iso = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=recent_days)).isoformat()
    try:
        con = sqlite3.connect(f"file:{aw_path}?mode=ro", uri=True)
        cur = con.cursor()
        buckets = cur.execute(
            "SELECT key FROM bucketmodel WHERE type = 'currentwindow' OR id LIKE 'aw-watcher-window%'"
        ).fetchall()
        if not buckets:
            con.close()
            return {}, "empty"

        stats: dict[str, dict[str, Any]] = {}
        day_sets: dict[str, set[str]] = defaultdict(set)

        for (bkey,) in buckets:
            rows = cur.execute(
                "SELECT timestamp, duration, datastr FROM eventmodel WHERE bucket_id = ? AND timestamp >= ?",
                (bkey, cutoff_iso),
            ).fetchall()
            for ts, dur, datastr in rows:
                try:
                    app_name = str(json.loads(datastr).get("app") or "").strip().lower()
                except Exception:
                    continue
                if not app_name:
                    continue
                sec = float(dur or 0)
                if sec <= 0 or sec > 43200:
                    continue
                entry = stats.setdefault(app_name, {"seconds": 0.0, "switches": 0, "lastUsedDate": ""})
                entry["seconds"] += sec
                entry["switches"] += 1
                day_str = str(ts)[:10]
                day_sets[app_name].add(day_str)
                if day_str > entry["lastUsedDate"]:
                    entry["lastUsedDate"] = day_str
        con.close()
    except Exception as exc:
        return {}, f"unreadable:{exc}"

    for app_name, entry in stats.items():
        entry["activeDays"] = len(day_sets[app_name])
    return stats, "ok" if stats else "empty"


def apply_screen_time_telemetry(apps: list[dict[str, Any]], recent_days: int) -> tuple[str, str, dict[str, Any]]:
    """
    按优先级融合真实前台使用时长：
    1. macOS Screen Time (knowledgeC.db)
    2. ActivityWatch (近 N 天有记录时)
    3. 回退到 Spotlight (mdls)
    """
    kc_stats, kc_status, kc_range = query_knowledgec_usage(recent_days)
    if kc_status == "ok" and kc_stats:
        for app in apps:
            bid = (app.get("bundleId") or "").strip().lower()
            rec = kc_stats.get(bid)
            if rec:
                sec = rec["seconds"]
                app["usageSeconds"] = round(sec, 1)
                app["usageHours"] = round(sec / 3600.0, 2)
                app["foregroundSwitches"] = rec["switches"]
                app["activeDaysRecent"] = max(app.get("activeDaysRecent", 0), rec["activeDays"])
                if rec["lastUsedDate"]:
                    app["lastUsedDate"] = rec["lastUsedDate"]
                # 以真实使用时长（分钟）为主导评分
                app["score"] = round(sec / 60.0 + rec["activeDays"] * 12.0, 2)
            else:
                app["score"] = round(app.get("score", 0) * 0.01, 2)
        span_note = (
            f"（实际库内记录：{kc_range['start']} ~ {kc_range['end']}，共 {kc_range['coveredDays']} 天）"
            if kc_range
            else ""
        )
        return "screen_time", f"macOS 屏幕使用时间{span_note}", kc_range

    aw_stats, aw_status = query_activitywatch_usage(recent_days)
    if aw_status == "ok" and aw_stats:
        for app in apps:
            keys = [app["name"].lower(), app["fileName"].lower()]
            rec = next((aw_stats[k] for k in keys if k in aw_stats), None)
            if rec:
                sec = rec["seconds"]
                app["usageSeconds"] = round(sec, 1)
                app["usageHours"] = round(sec / 3600.0, 2)
                app["foregroundSwitches"] = rec["switches"]
                app["activeDaysRecent"] = max(app.get("activeDaysRecent", 0), rec["activeDays"])
                if rec["lastUsedDate"]:
                    app["lastUsedDate"] = rec["lastUsedDate"]
                app["score"] = round(sec / 60.0 + rec["activeDays"] * 12.0, 2)
            else:
                app["score"] = round(app.get("score", 0) * 0.01, 2)
        return "activitywatch", "ActivityWatch 前台窗口时长", {}

    note = (
        "Spotlight 活跃天数（knowledgeC.db 需授予终端「完全磁盘访问权限」以读取真实使用时长）"
        if kc_status.startswith("unreadable")
        else "Spotlight 活跃天数"
    )
    return "spotlight", note, {}


def is_noise_app(app: dict[str, Any]) -> bool:
    haystack = f"{app['name']} {app['fileName']} {app['bundleId']}".lower()
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, haystack, flags=re.IGNORECASE):
            return True
    return False


def infer_category(app: dict[str, Any]) -> str:
    # 仅使用应用名称、文件名和 bundleId 匹配，避免 appleCategory 前缀 "public.app-category." 误匹配
    haystack = " ".join(
        [
            app["name"],
            app["fileName"],
            app["bundleId"],
        ]
    ).lower()

    for cat_name, keywords in CATEGORY_RULES:
        for kw in keywords:
            if len(kw) <= 3 and kw.isascii():
                if re.search(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", haystack):
                    return cat_name
            elif kw in haystack:
                return cat_name

    apple_cat = str(app.get("appleCategory") or "").lower()
    if apple_cat.startswith("public.app-category."):
        suffix = apple_cat.split("public.app-category.", 1)[1]
        if suffix in APPLE_CAT_MAP:
            return APPLE_CAT_MAP[suffix]

    hint = app.get("folderHint", "")
    if hint in FOLDER_HINT_TO_CATEGORY:
        return FOLDER_HINT_TO_CATEGORY[hint]

    return "效率与工具"


def extract_all_icons(apps: list[dict[str, Any]], icons_dir: Path) -> None:
    """调用同目录 extract_icons.swift 批量提取高清图标。"""
    swift_script = Path(__file__).resolve().parent / "extract_icons.swift"
    manifest = [{"id": a["id"], "path": a["path"]} for a in apps]

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(manifest, tmp, ensure_ascii=False)
        tmp_path = tmp.name

    try:
        proc = subprocess.run(
            ["swift", str(swift_script), tmp_path, str(icons_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.stdout:
            print(proc.stdout.strip())
        if proc.returncode != 0:
            print(f"[warn] icon extraction stderr: {proc.stderr}", file=sys.stderr)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def build_recommended_groups(apps: list[dict[str, Any]], max_apps: int) -> list[dict[str, Any]]:
    """按活跃度选出最值得展示在海报上的 Top 应用，按 bundleId 去重并均衡分组。"""
    candidates: list[dict[str, Any]] = []
    seen_bundles: set[str] = set()
    seen_names: set[str] = set()

    def try_add(app: dict[str, Any]) -> None:
        bid = (app.get("bundleId") or "").lower()
        norm_name = app["name"].strip().lower()
        if bid and bid in seen_bundles:
            return
        if norm_name in seen_names:
            return
        if bid:
            seen_bundles.add(bid)
        seen_names.add(norm_name)
        candidates.append(app)

    for a in apps:
        if not a["isNoise"] and (a["activeDaysRecent"] > 0 or a["useCount"] > 0):
            try_add(a)

    if len(candidates) < 12:
        for a in apps:
            if not a["isNoise"] and not a["isSystemApp"]:
                try_add(a)
                if len(candidates) >= max_apps:
                    break

    category_order = ["AI 与开发", "浏览与沟通", "写作与知识", "效率与工具", "影音与创作"]
    grouped: dict[str, list[str]] = {c: [] for c in category_order}
    max_per_row = 8

    picked = 0
    for app in candidates:
        if picked >= max_apps:
            break
        cat = app["category"]
        bucket = grouped.setdefault(cat, [])
        if len(bucket) >= max_per_row:
            continue
        bucket.append(app["id"])
        picked += 1

    return [
        {"id": f"cat-{idx}", "name": cat, "appIds": ids}
        for idx, (cat, ids) in enumerate(grouped.items())
        if ids
    ]


def write_csv(apps: list[dict[str, Any]], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "name",
        "category",
        "note",
        "usageHours",
        "usageSeconds",
        "foregroundSwitches",
        "activeDaysRecent",
        "activeDaysTotal",
        "useCount",
        "lastUsedDate",
        "score",
        "bundleId",
        "folderHint",
        "path",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for app in apps:
            writer.writerow({k: app.get(k, "") for k in fields})


def main() -> None:
    parser = argparse.ArgumentParser(description="扫描本机 Mac 已安装软件与真实使用时长并提取高清图标")
    parser.add_argument("--project-dir", default=".", help="输出项目根目录")
    parser.add_argument("--days", type=int, default=365, help="统计最近 N 天的使用记录（默认 365 天全年）")
    parser.add_argument("--max-apps", type=int, default=24, help="默认推荐海报入选的软件数量（默认 24）")
    parser.add_argument("--skip-icons", action="store_true", help="跳过图标提取")
    parser.add_argument("--reclassify-from", default="", help="基于已生成的 JSON 重新分类与分组，无需重复扫描 Spotlight")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    data_path = project_dir / "public" / "data" / "apps-data.json"
    icons_dir = project_dir / "public" / "icons"
    csv_path = project_dir / "output" / "mac-apps-usage.csv"

    usage_source = "spotlight"
    usage_source_label = "Spotlight 活跃天数"
    data_range: dict[str, Any] = {}

    if args.reclassify_from:
        print(f"Reclassifying apps from {args.reclassify_from}...")
        with Path(args.reclassify_from).open("r", encoding="utf-8") as f:
            prev = json.load(f)
        apps = prev.get("allApps", [])
        usage_source = prev.get("meta", {}).get("usageSource", usage_source)
        usage_source_label = prev.get("meta", {}).get("usageSourceLabel", usage_source_label)
        data_range = prev.get("meta", {}).get("dataRange", {})
    else:
        print(f"Scanning macOS applications (window: last {args.days} days)...")
        apps = discover_apps()
        query_spotlight_usage(apps, recent_days=args.days)
        usage_source, usage_source_label, data_range = apply_screen_time_telemetry(apps, recent_days=args.days)

    discover_cli_tools(apps)

    for app in apps:
        app.setdefault("usageSeconds", 0.0)
        app.setdefault("usageHours", 0.0)
        app.setdefault("foregroundSwitches", 0)
        app.setdefault("note", "")
        app["isNoise"] = is_noise_app(app)
        app["category"] = infer_category(app)
        app["iconUrl"] = f"./icons/{app['id']}.png"

    # 排序：优先按真实使用时长（usageSeconds）与综合得分降序
    apps.sort(
        key=lambda a: (
            -float(a.get("usageSeconds", 0)),
            -float(a.get("score", 0)),
            -int(a.get("activeDaysRecent", 0)),
            -int(a.get("useCount", 0)),
            a["name"].lower(),
        )
    )

    if not args.skip_icons:
        extract_all_icons(apps, icons_dir)

    recommended_groups = build_recommended_groups(apps, max_apps=args.max_apps)
    active_recent_count = sum(
        1 for a in apps if a.get("usageSeconds", 0) > 0 or a.get("activeDaysRecent", 0) > 0
    )

    payload = {
        "meta": {
            "generatedAt": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "windowDays": args.days,
            "totalInstalled": len(apps),
            "activeRecentCount": active_recent_count,
            "usageSource": usage_source,
            "usageSourceLabel": usage_source_label,
            "dataRange": data_range,
            "defaultTitle": f"{dt.datetime.now().year} 我的 Mac 常用软件",
        },
        "recommendedGroups": recommended_groups,
        "allApps": apps,
    }

    data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    write_csv(apps, csv_path)

    print(f"Usage data source:   {usage_source_label}")
    print(f"Total installed apps: {len(apps)} | Active in last {args.days}d: {active_recent_count}")
    print(f"JSON written to: {data_path}")
    print(f"CSV written to:  {csv_path}")
    print("\nTop 24 recommended apps:")
    for group in recommended_groups:
        items = []
        for aid in group["appIds"]:
            a = next(x for x in apps if x["id"] == aid)
            if a.get("usageHours", 0) > 0:
                items.append(f"{a['name']} ({a['usageHours']}h)")
            else:
                items.append(a["name"])
        print(f"  [{group['name']}] ({len(items)}): {', '.join(items)}")


if __name__ == "__main__":
    main()
