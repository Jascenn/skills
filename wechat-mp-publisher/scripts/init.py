#!/usr/bin/env python3
"""首次使用初始化向导"""
import os
import sys

def init_config():
    print("=" * 50)
    print("微信公众号发布 Skill - 初始化向导")
    print("=" * 50)
    print()
    
    config_dir = os.path.expanduser("~/.wechat-mp")
    config_file = os.path.join(config_dir, "config.env")
    
    if os.path.exists(config_file):
        print(f"⚠️  配置文件已存在：{config_file}")
        choice = input("是否重新配置？(y/N): ").strip().lower()
        if choice != 'y':
            print("已取消")
            return
    
    os.makedirs(config_dir, exist_ok=True)
    
    print("\n【步骤 1/5】微信公众号基础配置")
    print("-" * 50)
    appid = input("请输入 APPID: ").strip()
    secret = input("请输入 SECRET: ").strip()
    token = input("请输入 TOKEN（从后台 URL 获取）: ").strip()
    
    print("\n【步骤 2/5】封面图配置")
    print("-" * 50)
    print("封面图需要先上传到公众号素材库，获取 media_id")
    print("方法：登录公众号后台 → 素材管理 → 上传图片 → 获取 media_id")
    thumb_media_id = input("请输入封面图 media_id（可稍后配置，直接回车跳过）: ").strip()
    
    print("\n【步骤 3/5】默认作者")
    print("-" * 50)
    author = input("请输入默认作者名（可选）: ").strip()
    
    print("\n【步骤 4/5】默认标签")
    print("-" * 50)
    tags = input("请输入默认标签，逗号分隔（可选）: ").strip()
    
    print("\n【步骤 5/5】飞书 Base 配置（可选）")
    print("-" * 50)
    print("用于保存文章记录，不需要可直接回车跳过")
    base_token = input("飞书 Base Token（可选）: ").strip()
    table_id = input("飞书 Table ID（可选）: ").strip()
    
    # 写入配置
    with open(config_file, 'w') as f:
        f.write(f"WECHAT_APPID={appid}\n")
        f.write(f"WECHAT_SECRET={secret}\n")
        f.write(f"WECHAT_TOKEN={token}\n")
        f.write(f"WECHAT_THUMB_MEDIA_ID={thumb_media_id}\n")
        f.write(f"FEISHU_BASE_TOKEN={base_token}\n")
        f.write(f"FEISHU_TABLE_ID={table_id}\n")
        f.write(f"DEFAULT_AUTHOR={author}\n")
        f.write(f"DEFAULT_TAGS={tags}\n")
    
    print("\n" + "=" * 50)
    print("✅ 配置完成！")
    print("=" * 50)
    print(f"配置文件：{config_file}")
    print("\n使用方法：")
    print("  python3 mp_push.py --title '标题' --content '内容'")
    print("\n提示：")
    if not thumb_media_id:
        print("  ⚠️  未配置封面图，请稍后在配置文件中添加 WECHAT_THUMB_MEDIA_ID")

if __name__ == "__main__":
    init_config()
