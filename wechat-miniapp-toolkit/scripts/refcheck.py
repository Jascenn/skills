#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引用完整性检查：组件路径、图片资源、页面路由是否可解析

用法: python3 refcheck.py <项目路径> [<项目路径> ...]
"""
import json, re, sys
from pathlib import Path

if len(sys.argv) < 2:
    print("用法: python3 refcheck.py <项目路径> [<项目路径> ...]")
    sys.exit(1)

PROJECTS = {}
for a in sys.argv[1:]:
    p = Path(a).expanduser().resolve()
    PROJECTS[p.name] = p

SKIP_TOP = {".git", "node_modules", "docs", "archive", "minitest", "_archive", "mock"}


def skip(f, root):
    return bool(set(f.relative_to(root).parts[:-1]) & SKIP_TOP)


def exists_like(t: Path):
    if t.exists():
        return True
    if t.parent.exists() and list(t.parent.glob(t.name + ".*")):
        return True
    return False


for name, root in PROJECTS.items():
    print("=" * 72)
    print(name)
    print("=" * 72)
    miss_comp, miss_img, miss_route = [], [], []

    # 1) usingComponents
    for j in root.rglob("*.json"):
        if skip(j, root):
            continue
        try:
            d = json.loads(j.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        uc = d.get("usingComponents")
        if not isinstance(uc, dict):
            continue
        for cname, cpath in uc.items():
            if not isinstance(cpath, str):
                continue
            p = cpath.strip()
            if p.startswith(("plugin://", "weui-miniprogram", "tdesign-miniprogram", "miniprogram_npm")):
                continue
            if p.startswith("/"):
                t = root / p[1:]
            elif p.startswith("~/"):
                t = root / p[2:]
            else:
                t = j.parent / p
            if not exists_like(t):
                miss_comp.append(f"{j.relative_to(root)}  ->  {cname} = {cpath}")

    # 2) 图片资源
    pat_img = re.compile(r'src\s*=\s*["\'](/[^"\']+\.(?:png|jpg|jpeg|gif|svg|webp))["\']', re.I)
    pat_bg = re.compile(r'url\(\s*["\']?(/[^"\')]+\.(?:png|jpg|jpeg|gif|svg|webp))["\']?\s*\)', re.I)
    for pat, exts in ((pat_img, (".wxml",)), (pat_bg, (".wxml", ".wxss"))):
        for ext in exts:
            for f in root.rglob(f"*{ext}"):
                if skip(f, root):
                    continue
                txt = f.read_text(encoding="utf-8", errors="ignore")
                for m in pat.finditer(txt):
                    rel = m.group(1)
                    if rel.startswith(("//", "http")):
                        continue
                    if not (root / rel.lstrip("/")).exists():
                        miss_img.append(f"{f.relative_to(root)}  ->  {rel}")

    # 3) 页面路由
    try:
        app = json.loads((root / "app.json").read_text(encoding="utf-8"))
    except Exception:
        app = {}
    pages = set(app.get("pages", []))
    for s in (app.get("subPackages", app.get("subpackages", [])) or []):
        rr = s.get("root", "").strip("/")
        for p in s.get("pages", []):
            pages.add(f"{rr}/{p}")
    pat_route = re.compile(r'(?:url|pagePath)\s*[:=]\s*["\']/(pages/[A-Za-z0-9_\-/]+)')
    for f in list(root.rglob("*.wxml")) + list(root.rglob("*.js")):
        if skip(f, root) or "miniprogram_npm" in f.parts:
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for m in pat_route.finditer(txt):
            r = m.group(1)
            if r not in pages:
                miss_route.append(f"{f.relative_to(root)}  ->  /{r}")

    def show(title, items, limit=20):
        uniq = sorted(set(items))
        print(f"\n[{title}] 共 {len(uniq)} 处")
        for i in uniq[:limit]:
            print("   x", i)
        if len(uniq) > limit:
            print(f"   ... 另有 {len(uniq) - limit} 处")

    show("组件引用失效", miss_comp)
    show("图片资源缺失", miss_img)
    show("页面路由未注册", miss_route)
    print()
