#!/usr/bin/env python3
"""通用公众号推送脚本 - 支持配置化"""
import argparse
import json
import urllib.request
import os
import sys
from datetime import datetime

def load_config():
    config_file = os.path.expanduser("~/.wechat-mp/config.env")
    config = {}
    if os.path.exists(config_file):
        with open(config_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    config[key] = val
    return config

CONFIG = load_config()
APPID = CONFIG.get("WECHAT_APPID", "")
SECRET = CONFIG.get("WECHAT_SECRET", "")
THUMB_MEDIA_ID = CONFIG.get("WECHAT_THUMB_MEDIA_ID", "")
MP_TOKEN = CONFIG.get("WECHAT_TOKEN", "")
BASE_TOKEN = CONFIG.get("FEISHU_BASE_TOKEN", "")
TABLE_ID = CONFIG.get("FEISHU_TABLE_ID", "")
DEFAULT_AUTHOR = CONFIG.get("DEFAULT_AUTHOR", "")
DEFAULT_TAGS = CONFIG.get("DEFAULT_TAGS", "")

def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}"
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read().decode())["access_token"]

def push_draft(title, content, author, token):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    payload = {"articles": [{"title": title, "content": content, "author": author, "thumb_media_id": THUMB_MEDIA_ID, "show_cover_pic": 1}]}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def save_to_feishu(data):
    import subprocess
    if not BASE_TOKEN or not TABLE_ID:
        print("⚠️  未配置飞书 Base，跳过保存（可选功能）")
        return None
    cmd = ["lark-cli", "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--json", json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout).get("data", {}).get("record", {}).get("record_id_list", [None])[0]
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument("--author", default=DEFAULT_AUTHOR, help="作者名（可选）")
    parser.add_argument("--tags", default=DEFAULT_TAGS, help="标签（可选）")
    parser.add_argument("--no-feishu", action="store_true", help="跳过飞书 Base 保存")
    args = parser.parse_args()
    
    record_id = None
    if not args.no_feishu:
        print("💾 保存到飞书 Base...")
        record_id = save_to_feishu({"标题": args.title, "正文内容": args.content, "标签": args.tags, "状态": "草稿"})
    
    print("📤 推送草稿...")
    token = get_access_token()
    result = push_draft(args.title, args.content, args.author, token)
    
    if "media_id" in result:
        print(f"✅ 成功！media_id: {result['media_id']}")
        if record_id:
            save_to_feishu({"media_id": result['media_id']})
    else:
        print(f"❌ 失败：{result}")

if __name__ == "__main__":
    main()
