#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微信小程序静态体检：配置 / 体积 / 结构 / 代码质量

用法: python3 healthcheck.py <项目路径> [<项目路径> ...]
输出: 终端可读报告 + 当前目录 healthcheck.json
"""
import json, os, re, subprocess, sys
from pathlib import Path

if len(sys.argv) < 2:
    print("用法: python3 healthcheck.py <项目路径> [<项目路径> ...]")
    sys.exit(1)

PROJECTS = {}
for a in sys.argv[1:]:
    p = Path(a).expanduser().resolve()
    PROJECTS[p.name] = p

# 不计入上传包的本地开发产物
EXCLUDE_DIRS = {".git", "node_modules", "docs", "archive", "minitest", "_archive", ".vscode", "mock", "test-data"}
CODE_EXT = {".js", ".wxml", ".wxss", ".wxs", ".json", ".ts", ".less", ".scss"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}
PAGE_EXT = {".js", ".wxml", ".wxss", ".json"}


def human(n):
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"


def dirsize(p):
    total = 0
    for f in Path(p).rglob("*"):
        if not f.is_file():
            continue
        if set(f.relative_to(p).parts[:-1]) & EXCLUDE_DIRS:
            continue
        total += f.stat().st_size
    return total


def collect(root):
    R = {"path": str(root)}
    try:
        pc = json.loads((root / "project.config.json").read_text(encoding="utf-8"))
    except Exception as e:
        pc = {}
        R["pc_err"] = str(e)
    R["appid"] = pc.get("appid")
    R["projectname"] = pc.get("projectname")
    R["libVersion"] = pc.get("libVersion")
    R["miniprogramRoot"] = pc.get("miniprogramRoot")
    R["cloudfunctionRoot"] = pc.get("cloudfunctionRoot")
    st = pc.get("setting", {})
    R["urlCheck"] = st.get("urlCheck")
    R["es6"] = st.get("es6")
    R["minified"] = st.get("minified")
    R["compileType"] = pc.get("compileType")
    R["packIgnore"] = [i.get("value") for i in pc.get("packOptions", {}).get("ignore", [])]

    try:
        app = json.loads((root / "app.json").read_text(encoding="utf-8"))
    except Exception as e:
        app = {}
        R["app_err"] = str(e)
    pages = app.get("pages", [])
    subs = app.get("subPackages", app.get("subpackages", [])) or []
    subpages = [f"{s.get('root','').strip('/')}/{p}" for s in subs for p in s.get("pages", [])]
    R["main_pages"] = pages
    R["sub_packages"] = [{"root": s.get("root"), "pages": s.get("pages")} for s in subs]
    R["total_pages"] = len(pages) + len(subpages)
    R["tabBar"] = [t.get("text") for t in app.get("tabBar", {}).get("list", [])] if "tabBar" in app else []
    R["window_title"] = app.get("window", {}).get("navigationBarTitleText")
    R["use_privacy_check"] = app.get("__usePrivacyCheck__")
    R["permission"] = list(app.get("permission", {}).keys())
    R["requiredPrivateInfos"] = app.get("requiredPrivateInfos")
    R["lazyCodeLoading"] = app.get("lazyCodeLoading")

    # 页面文件完整性
    miss, inc = [], []
    for p in list(pages) + subpages:
        for ext in PAGE_EXT:
            if not (root / f"{p}{ext}").exists():
                (miss if ext in (".js", ".wxml") else inc).append(f"{p}{ext}")
    R["missing_page_files"] = miss
    R["incomplete_page_files"] = inc

    # 孤立页面（有 wxml 但未注册）
    registered = set(list(pages) + subpages)
    orphans = []
    for w in root.rglob("*.wxml"):
        rel = str(w.relative_to(root)).replace("\\", "/")
        if set(w.relative_to(root).parts) & EXCLUDE_DIRS:
            continue
        if rel.startswith(("components/", "miniprogram_npm/", "custom-tab-bar/")):
            continue
        if rel[:-5] not in registered:
            orphans.append(rel[:-5])
    R["orphan_pages"] = sorted(orphans)

    # 体积
    R["upload_est"] = dirsize(root)
    R["git_size"] = sum(f.stat().st_size for f in (root / ".git").rglob("*") if f.is_file()) if (root / ".git").exists() else 0
    for label, d in (("node_modules_size", root / "node_modules"), ("miniprogram_npm_size", root / "miniprogram_npm")):
        R[label] = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) if d.exists() else 0

    big = []
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if set(f.relative_to(root).parts) & {".git", "node_modules"}:
            continue
        big.append((f.stat().st_size, str(f.relative_to(root))))
    big.sort(reverse=True)
    R["big_files"] = [(human(s), p) for s, p in big[:10]]

    # 图片资源
    imgs = [f.stat().st_size for f in root.rglob("*")
            if f.is_file() and f.suffix.lower() in IMG_EXT and ".git" not in f.parts and "node_modules" not in f.parts]
    R["img_count"] = len(imgs)
    R["img_total"] = human(sum(imgs))

    # 代码扫描
    scan = {"todo": 0, "console_log": 0, "placeholder": [], "secrets": [], "http": set(), "lines": 0, "files": 0,
            "privacy_api": 0}
    pat_todo = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
    pat_console = re.compile(r"console\.(log|debug)\(")
    pat_ph = re.compile(r"(yourusername|your_name|yourname|example\.com|test@|请填写|待补充|占位|替换为实际|placeholder|xxx)")
    pat_secret = re.compile(r"(appkey|app_key|secret|apikey|api_key|access_token|password)\s*[:=]\s*['\"]([A-Za-z0-9_\-]{12,})['\"]", re.I)
    pat_http = re.compile(r"https?://([A-Za-z0-9\.\-]+)")
    pat_priv = re.compile(r"wx\.(setClipboardData|chooseAddress|getLocation|chooseImage|startRecord|getClipboardData|chooseMedia|saveImageToPhotosAlbum)\(")
    skip_host = re.compile(r"(w3\.org|weixin\.qq\.com|gtimg\.com|developers\.weixin|npmjs\.org|eslint\.org|github\.com)")
    for f in root.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in CODE_EXT:
            continue
        if set(f.relative_to(root).parts) & EXCLUDE_DIRS or "miniprogram_npm" in f.parts:
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        scan["files"] += 1
        scan["lines"] += txt.count("\n") + 1
        scan["todo"] += len(pat_todo.findall(txt))
        scan["console_log"] += len(pat_console.findall(txt))
        scan["privacy_api"] += len(pat_priv.findall(txt))
        for m in pat_ph.finditer(txt):
            if len(scan["placeholder"]) < 15:
                scan["placeholder"].append(f"{f.relative_to(root)} <- {m.group(0)}")
        for m in pat_secret.finditer(txt):
            if len(scan["secrets"]) < 10:
                scan["secrets"].append(f"{f.relative_to(root)} <- {m.group(1)}=***")
        for m in pat_http.finditer(txt):
            if not skip_host.search(m.group(0)):
                scan["http"].add(m.group(1))
    R["scan"] = scan

    try:
        pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
        R["deps"] = pkg.get("dependencies", {})
    except Exception:
        R["deps"] = None

    try:
        R["git_last"] = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%ad|%s", "--date=format:%Y-%m-%d %H:%M"],
                                       capture_output=True, text=True, timeout=10).stdout.strip()
        R["git_commits"] = subprocess.run(["git", "-C", str(root), "rev-list", "--count", "HEAD"],
                                          capture_output=True, text=True, timeout=10).stdout.strip()
        s = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                           capture_output=True, text=True, timeout=10).stdout.strip()
        R["git_dirty"] = len(s.splitlines()) if s else 0
    except Exception as e:
        R["git_last"] = f"err:{e}"
    return R


out = {}
for name, root in PROJECTS.items():
    print(f"\n{'=' * 70}\n{name}\n{'=' * 70}", flush=True)
    d = collect(root)
    out[name] = d
    print(json.dumps(d, ensure_ascii=False, indent=2, default=list), flush=True)

Path("healthcheck.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=list), encoding="utf-8")
print("\n[saved] healthcheck.json")
