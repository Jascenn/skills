#!/usr/bin/env python3
"""
[INPUT]: 接收 CLI 子命令 publish（海报 PNG、apps-data.json、图标目录、署名、可见性）或 revoke（本地撤回凭证 receipt.json）
[OUTPUT]: 与 MacStack · lingyi 云端 API 交互，实现图标 SHA-256 去重上传、作品发布/撤回及本地凭证持久化
[POS]: lingyi-mac-annual-apps Skill 的云端分享闭环脚本，零第三方依赖（仅 Python 标准库）
[PROTOCOL]: Update this header on change, then check GEMINI.md
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_ORIGIN = os.environ.get("MACSTACK_ORIGIN", "https://mac.lingyi.tools").rstrip("/")
MAX_ICON_BYTES = 96 * 1024


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def http_json(method: str, url: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req_headers = {"user-agent": "lingyi-mac-annual-apps/2.0"}
    if body is not None:
        req_headers["content-type"] = "application/json; charset=utf-8"
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except Exception:
            data = {"ok": False, "error": raw or str(e)}
        return e.code, data


def cmd_publish(args: argparse.Namespace) -> None:
    origin = args.origin.rstrip("/")
    image_path = Path(args.image).resolve()
    data_path = Path(args.data).resolve()
    icons_dir = Path(args.icons_dir).resolve() if args.icons_dir else data_path.parent.parent / "icons"
    receipt_path = Path(str(image_path) + ".share.json")

    if not image_path.is_file():
        raise SystemExit(f"找不到海报文件：{image_path}")
    if not data_path.is_file():
        raise SystemExit(f"找不到应用清单：{data_path}")
    if receipt_path.exists() and not args.force:
        raise SystemExit(f"已存在分享凭证：{receipt_path}（如需重新发布请另存成图或加 --force）")

    poster_bytes = image_path.read_bytes()
    if len(poster_bytes) > 8 * 1024 * 1024:
        raise SystemExit("海报文件超过 8 MiB 上限")

    dataset = json.loads(data_path.read_text(encoding="utf-8"))
    apps_by_id = {a["id"]: a for a in dataset.get("allApps", [])}
    groups = dataset.get("recommendedGroups", [])

    icon_bytes_by_hash: dict[str, bytes] = {}
    app_items: list[dict[str, Any]] = []

    for g in groups:
        cat = g.get("name", "效率与工具")
        for aid in g.get("appIds", []):
            app = apps_by_id.get(aid)
            if not app:
                continue
            icon_hash = ""
            icon_file = icons_dir / f"{aid}.png"
            if icon_file.is_file():
                ib = icon_file.read_bytes()
                if 0 < len(ib) <= MAX_ICON_BYTES:
                    icon_hash = sha256_hex(ib)
                    icon_bytes_by_hash[icon_hash] = ib
            entry: dict[str, Any] = {
                "id": app.get("bundleId") or aid,
                "bundleId": app.get("bundleId") or aid,
                "name": app.get("name", aid),
                "group": cat,
                "note": (app.get("note") or "").strip(),
            }
            if icon_hash:
                entry["icon"] = icon_hash
            app_items.append(entry)

    if not app_items:
        raise SystemExit("清单中没有可发布的软件")

    icons_payload: dict[str, str] = {}
    if icon_bytes_by_hash:
        status, lookup = http_json("POST", f"{origin}/api/v1/icons/lookup", {"hashes": list(icon_bytes_by_hash.keys())})
        if status == 200 and lookup.get("ok"):
            for h in lookup.get("missing", []):
                if h in icon_bytes_by_hash:
                    icons_payload[h] = base64.b64encode(icon_bytes_by_hash[h]).decode("ascii")

    title = args.title or dataset.get("meta", {}).get("defaultTitle") or "2026 我的 Mac 常用软件"
    publish_key = secrets.token_hex(32)

    status, result = http_json(
        "POST",
        f"{origin}/api/v1/shares",
        {
            "author": args.author,
            "title": title,
            "subtitle": args.subtitle or "",
            "visibility": args.visibility,
            "apps": app_items,
            "icons": icons_payload,
            "image": base64.b64encode(poster_bytes).decode("ascii"),
        },
        headers={"idempotency-key": publish_key},
    )
    if status not in (200, 201) or not result.get("ok"):
        raise SystemExit(f"发布失败（HTTP {status}）：{result.get('error', '未知错误')}")

    receipt = {
        "origin": origin,
        "id": result["id"],
        "url": result["url"],
        "posterUrl": result.get("posterUrl", ""),
        "visibility": result.get("visibility", args.visibility),
        "removeToken": result.get("removeToken", ""),
        "createdAt": result.get("createdAt", ""),
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(receipt_path, 0o600)

    print(
        json.dumps(
            {
                "ok": True,
                "url": receipt["url"],
                "visibility": receipt["visibility"],
                "iconsUploaded": result.get("iconsUploaded", 0),
                "receipt": str(receipt_path),
            },
            ensure_ascii=False,
        )
    )


def cmd_revoke(args: argparse.Namespace) -> None:
    receipt_path = Path(args.receipt).resolve()
    if not receipt_path.is_file():
        raise SystemExit(f"找不到撤回凭证：{receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    origin = (args.origin or receipt.get("origin") or DEFAULT_ORIGIN).rstrip("/")
    share_id = receipt.get("id", "")
    token = receipt.get("removeToken", "")
    if not share_id or not token:
        raise SystemExit("撤回凭证缺少 id 或 removeToken")

    status, result = http_json(
        "DELETE",
        f"{origin}/api/v1/shares/{share_id}",
        headers={"authorization": f"Bearer {token}"},
    )
    if status != 200 or not result.get("ok"):
        raise SystemExit(f"撤回失败（HTTP {status}）：{result.get('error', '未知错误')}")

    print(json.dumps({"ok": True, "withdrawn": True, "url": receipt.get("url", "")}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="发布或撤回 MacStack · lingyi 年度软件海报")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pub = sub.add_parser("publish", help="发布海报到 MacStack · lingyi")
    p_pub.add_argument("--image", required=True, help="高清海报 PNG 路径")
    p_pub.add_argument("--data", required=True, help="apps-data.json 路径")
    p_pub.add_argument("--icons-dir", default="", help="图标目录（默认推断同项目 public/icons）")
    p_pub.add_argument("--author", default="lingyi", help="发布署名（默认 lingyi）")
    p_pub.add_argument("--title", default="", help="海报标题")
    p_pub.add_argument("--subtitle", default="", help="副标题/备注")
    p_pub.add_argument("--visibility", choices=["public", "link"], default="public", help="可见范围")
    p_pub.add_argument("--origin", default=DEFAULT_ORIGIN, help="站点地址")
    p_pub.add_argument("--force", action="store_true", help="忽略已有凭证强制重新发布")

    p_rev = sub.add_parser("revoke", help="凭本地凭证撤回已发布的作品")
    p_rev.add_argument("--receipt", required=True, help="本地 *.share.json 凭证路径")
    p_rev.add_argument("--origin", default="", help="覆盖站点地址")

    args = parser.parse_args()
    if args.cmd == "publish":
        cmd_publish(args)
    elif args.cmd == "revoke":
        cmd_revoke(args)


if __name__ == "__main__":
    main()
