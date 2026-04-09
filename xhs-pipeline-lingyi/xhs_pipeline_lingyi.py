#!/usr/bin/env python3
# xhs-pipeline-lingyi — Xiaohongshu draft pipeline
# Author: Lingyi (凌一) - https://lingyi.bio
# GitHub: https://github.com/Jascenn/xhs-pipeline-lingyi
"""小红书草稿写入流水线，支持两种模式：
  A. 从飞书内容表读取（--from-feishu --record-id <id>）
  B. 直接传参（--title --content --images，可选 --record-id 回写飞书）

飞书后端（--feishu-backend）：
  lark-cli   直接调用 lark-cli（默认，Claude Code 环境）
  openclaw   通过 openclaw agent 处理
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── 配置文件 ──
CONFIG_DIR = Path.home() / ".xhs-pipeline-lingyi"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    # xiaohongshu-skills 底层库路径（必填）
    "xhs_skill_root": "",
    # 图片生成脚本路径（可选，不填则无法自动生图）
    "image_gen_script": "",
    # 飞书内容库配置（可选，不填则跳过飞书回写）
    "feishu_content_base": "",
    "feishu_content_table": "",
    # 飞书选题表配置（可选）
    "feishu_topic_base": "",
    "feishu_topic_table": "",
    # openclaw agent 名称（可选，使用 openclaw 后端时需要）
    "openclaw_agent": "",
    # 图片生成尺寸
    "image_size": "1536*2688",
    # 默认发布时间（小时）
    "default_publish_hour": 19,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def setup_wizard() -> dict:
    """首次运行引导配置。"""
    print("\n" + "="*50)
    print("欢迎使用 xhs-pipeline-lingyi！")
    print("首次运行需要配置一些参数，可选项直接回车跳过。")
    print("="*50 + "\n")

    cfg = dict(DEFAULT_CONFIG)

    # 必填：xiaohongshu-skills 路径
    default_xhs = str(Path.home() / ".openclaw/workspace/skills/xiaohongshu-skills")
    val = input(f"xiaohongshu-skills 路径 [{default_xhs}]: ").strip()
    cfg["xhs_skill_root"] = val or default_xhs

    # 可选：图片生成脚本
    default_img = str(Path.home() / ".openclaw/workspace/skills/lingyi-image-gen/scripts/generate_image.py")
    val = input(f"图片生成脚本路径（可选）[{default_img}]: ").strip()
    cfg["image_gen_script"] = val or (default_img if Path(default_img).exists() else "")

    # 可选：飞书配置
    print("\n飞书配置（可选，不填则跳过飞书回写）：")
    cfg["feishu_content_base"] = input("飞书内容库 base token: ").strip()
    if cfg["feishu_content_base"]:
        cfg["feishu_content_table"] = input("飞书内容库 table id: ").strip()
        cfg["feishu_topic_base"] = input("飞书选题表 base token（可选）: ").strip()
        if cfg["feishu_topic_base"]:
            cfg["feishu_topic_table"] = input("飞书选题表 table id: ").strip()

    # 可选：openclaw agent
    val = input("\nopenclaw agent 名称（可选，使用 openclaw 后端时需要）: ").strip()
    cfg["openclaw_agent"] = val

    save_config(cfg)
    print(f"\n配置已保存到 {CONFIG_FILE}")
    print("="*50 + "\n")
    return cfg


def check_and_load_config() -> dict:
    """加载配置，首次运行时引导配置。"""
    cfg = load_config()
    if not cfg.get("xhs_skill_root"):
        cfg = setup_wizard()
    return cfg


# ── 全局配置（运行时加载）──
_cfg: dict = {}


def get_cfg() -> dict:
    global _cfg
    if not _cfg:
        _cfg = check_and_load_config()
    return _cfg


def get_skill_root() -> Path:
    return Path(get_cfg()["xhs_skill_root"])


def get_cli_path() -> Path:
    return get_skill_root() / "scripts" / "cli.py"


def get_image_gen_script() -> Path | None:
    p = get_cfg().get("image_gen_script", "")
    return Path(p) if p and Path(p).exists() else None


def has_feishu() -> bool:
    cfg = get_cfg()
    return bool(cfg.get("feishu_content_base") and cfg.get("feishu_content_table"))


IMAGE_SIZE_DEFAULT = "1536*2688"


def build_image_prompts(title: str, content: str) -> list[str]:
    base_style = (
        "Notion-style minimalist infographic card, white background, "
        "clean black typography, hand-drawn line art decorations, "
        "information card feel, Chinese social media format, 9:16 ratio. "
    )
    return [
        f"{base_style}Cover card. Large bold Chinese title: '{title}'. "
        "Subtitle hints at the key insight. Minimal decorations, strong visual impact.",
        f"{base_style}Problem card. Highlight the pain point: {content[:200]}. "
        "Warning visual, clear Chinese text, flow or list layout.",
        f"{base_style}Solution card. Present the core solution: {content[200:400]}. "
        "Clean card with key message.",
        f"{base_style}Step-by-step tutorial card. Action steps from: {content[400:600]}. "
        "Numbered flow diagram, clear Chinese labels.",
        f"{base_style}Benefits card. Positive outcomes from: {content[600:800]}. "
        "Checkmark list, encouraging tone.",
        f"{base_style}Ending CTA card. Title: '{title}'. "
        "Warm encouraging message, minimal design.",
    ]


def generate_images(title: str, content: str, output_dir: Path, prompts: list[str] | None = None) -> list[str]:
    script = get_image_gen_script()
    if not script:
        print("未配置图片生成脚本，跳过自动生图", file=sys.stderr)
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    if not prompts:
        prompts = build_image_prompts(title, content)

    slug = re.sub(r"[^\w\-]", "-", title.lower())[:30].strip("-")
    size = get_cfg().get("image_size", IMAGE_SIZE_DEFAULT)
    paths: list[str] = []

    for i, prompt in enumerate(prompts, 1):
        out_path = output_dir / f"{i:02d}-{slug}.png"
        print(f"生成第 {i}/{len(prompts)} 张图片...")
        result = subprocess.run(
            [sys.executable, str(script), "--prompt", prompt, "--size", size, "--output", str(out_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"第 {i} 张生成失败: {result.stderr}", file=sys.stderr)
        else:
            paths.append(str(out_path))
            print(f"第 {i} 张完成: {out_path.name}")

    return paths


def default_schedule_iso(now: datetime) -> str:
    hour = get_cfg().get("default_publish_hour", 19)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if now >= target:
        target = now + timedelta(minutes=10)
        target = target.replace(second=0, microsecond=0)
    return target.isoformat(timespec="minutes")


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, cwd=get_skill_root(), text=True)
    if proc.returncode == 2:
        raise SystemExit(proc.returncode)


def extract_text(field_value) -> str:
    if isinstance(field_value, str):
        return field_value
    if isinstance(field_value, list):
        return "".join(seg.get("text", "") for seg in field_value)
    return ""


# ── lark-cli 后端 ──

def _lark_cli(*args: str) -> dict:
    result = subprocess.run(["lark-cli", *args], capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(result.stdout, file=sys.stderr)
        raise SystemExit(1)


def fetch_record_lark(record_id: str) -> dict:
    cfg = get_cfg()
    data = _lark_cli(
        "base", "+record-get",
        "--base-token", cfg["feishu_content_base"],
        "--table-id", cfg["feishu_content_table"],
        "--record-id", record_id,
    )
    if not data.get("ok"):
        print(f"飞书读取失败: {data}", file=sys.stderr)
        raise SystemExit(1)
    return data["data"]["record"]


def create_content_record_lark(title: str, content: str, schedule_at: str, images: list[str] | None = None, image_dir: str = "") -> str | None:
    cfg = get_cfg()
    if not has_feishu():
        print("未配置飞书，跳过新建记录")
        return None

    image_links = "\n".join(images) if images else ""
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    hook = lines[0] if lines else ""
    tags_line = lines[-1] if lines and lines[-1].startswith("#") else ""
    clean_content = content[:content.rfind(tags_line)].rstrip() if tags_line else content
    pain_point = lines[1] if len(lines) > 1 else ""
    action = next((l for l in reversed(lines) if not l.startswith("#")), "")
    mid_lines = [l for l in lines if not l.startswith("#") and l != hook and l != action]
    benefit = mid_lines[-1] if mid_lines else ""
    structure_lines = [l for l in lines if not l.startswith("#")]
    structure = "\n".join(f"{i+1}. {l[:40]}" for i, l in enumerate(structure_lines[:6]))
    today_ts = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)

    fields = {
        "内容标题": title,
        "封面标题": title,
        "爆款标题候选": title,
        "正文初稿": clean_content,
        "开头钩子": hook,
        "用户痛点": pain_point,
        "用户收益": benefit,
        "行动引导": action,
        "内容结构": structure,
        "标签": tags_line,
        "内容状态": "待发布",
        "内容平台": "小红书",
        "内容类型": "图文笔记",
        "图片页数": len(images) if images else 0,
        "全套配图链接": image_links,
        "图片生成状态": "已出图" if images else "待生成",
        "沉淀文档日期": today_ts,
        "图片目录": image_dir,
        "备注": f"定时发布：{schedule_at}",
    }
    data = _lark_cli(
        "base", "+record-upsert",
        "--base-token", cfg["feishu_content_base"],
        "--table-id", cfg["feishu_content_table"],
        "--json", json.dumps(fields, ensure_ascii=False),
    )
    if not data.get("ok"):
        print(f"内容表新建记录失败: {data}", file=sys.stderr)
        return None
    record_id = data.get("data", {}).get("record", {}).get("record_id_list", [None])[0]
    print(f"内容表已新建记录: {title}，record_id={record_id}")
    return record_id


def update_feishu_lark(title: str, record_id: str | None, schedule_at: str, topic_record_id: str | None = None) -> None:
    cfg = get_cfg()
    if not has_feishu():
        print("未配置飞书，跳过状态更新")
        return

    if record_id:
        data = _lark_cli(
            "base", "+record-upsert",
            "--base-token", cfg["feishu_content_base"],
            "--table-id", cfg["feishu_content_table"],
            "--record-id", record_id,
            "--json", json.dumps({"内容状态": "待发布"}, ensure_ascii=False),
        )
        if data.get("ok"):
            print(f"内容表已更新: {title} → 待发布")
        else:
            print(f"内容表更新失败: {data}", file=sys.stderr)

    if topic_record_id and cfg.get("feishu_topic_base") and cfg.get("feishu_topic_table"):
        data = _lark_cli(
            "base", "+record-upsert",
            "--base-token", cfg["feishu_topic_base"],
            "--table-id", cfg["feishu_topic_table"],
            "--record-id", topic_record_id,
            "--json", json.dumps({"选题状态": "已转内容库"}, ensure_ascii=False),
        )
        if data.get("ok"):
            print(f"选题表已更新: {title} → 已转内容库")
        else:
            print(f"选题表更新失败: {data}", file=sys.stderr)


# ── openclaw 后端 ──

def fetch_record_openclaw(record_id: str) -> dict:
    cfg = get_cfg()
    agent = cfg.get("openclaw_agent", "")
    if not agent:
        print("未配置 openclaw_agent，无法使用 openclaw 后端", file=sys.stderr)
        raise SystemExit(1)
    msg = (
        f"请读取飞书多维表格，base_token={cfg['feishu_content_base']}，"
        f"table_id={cfg['feishu_content_table']}，record_id={record_id}，"
        f"只返回以下字段的纯文本 JSON：内容标题、正文初稿、图片目录。"
    )
    result = subprocess.run(
        ["openclaw", "agent", "--agent", agent, "--message", msg, "--json"],
        capture_output=True, text=True,
    )
    try:
        outer = json.loads(result.stdout)
        reply = outer.get("reply") or outer.get("message") or outer.get("content") or ""
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    print(f"飞书读取失败: {result.stdout}", file=sys.stderr)
    raise SystemExit(1)


def update_feishu_openclaw(title: str, record_id: str | None, schedule_at: str, topic_record_id: str | None = None) -> None:
    cfg = get_cfg()
    agent = cfg.get("openclaw_agent", "")
    if not agent:
        print("未配置 openclaw_agent，跳过飞书更新", file=sys.stderr)
        return
    lines = ["小红书草稿已写入成功，请更新飞书状态："]
    if record_id:
        lines.append(
            f"1. 内容库 base={cfg['feishu_content_base']} table={cfg['feishu_content_table']} "
            f"record_id={record_id}，将「内容状态」更新为「待发布」"
        )
    if topic_record_id and cfg.get("feishu_topic_base"):
        lines.append(
            f"2. 选题表 base={cfg['feishu_topic_base']} table={cfg['feishu_topic_table']} "
            f"record_id={topic_record_id}，将「选题状态」更新为「已转内容库」"
        )
    lines.append(f"定时发布时间：{schedule_at}")
    subprocess.run(["openclaw", "agent", "--agent", agent, "--message", "\n".join(lines)], text=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="小红书草稿写入流水线 xhs-pipeline-lingyi")
    parser.add_argument("--setup", action="store_true", help="重新运行配置向导")
    parser.add_argument("--from-feishu", action="store_true", help="从飞书内容表读取内容")
    parser.add_argument("--title", help="标题（≤20字）")
    parser.add_argument("--content-file", help="正文文件路径")
    parser.add_argument("--content", help="正文内容")
    parser.add_argument("--images", nargs="+", help="图片路径或 URL 列表")
    parser.add_argument("--auto-gen-images", action="store_true", help="自动生成图片")
    parser.add_argument("--image-output-dir", help="自动生图输出目录")
    parser.add_argument("--record-id", help="飞书内容表 record_id")
    parser.add_argument("--topic-record-id", help="飞书选题表 record_id")
    parser.add_argument("--schedule-at", help="定时发布时间 ISO8601，默认今日 19:00")
    parser.add_argument("--visibility", default="", help="可见范围")
    parser.add_argument("--no-feishu-update", action="store_true", help="跳过飞书状态回写")
    parser.add_argument(
        "--feishu-backend", choices=["lark-cli", "openclaw"], default="lark-cli",
        help="飞书操作后端：lark-cli（默认）或 openclaw"
    )
    args = parser.parse_args()

    if args.setup:
        save_config(setup_wizard())
        return

    # 加载配置（首次运行自动引导）
    get_cfg()

    fetch_record = fetch_record_lark if args.feishu_backend == "lark-cli" else fetch_record_openclaw
    update_feishu = update_feishu_lark if args.feishu_backend == "lark-cli" else update_feishu_openclaw

    # ── 入口 A：从飞书读取 ──
    if args.from_feishu:
        if not args.record_id:
            print("--from-feishu 需要提供 --record-id", file=sys.stderr)
            raise SystemExit(1)
        fields = fetch_record(args.record_id)
        title = extract_text(fields.get("内容标题", ""))
        if args.title:
            title = args.title
        content = extract_text(fields.get("正文初稿", ""))
        images: list[str] = []
        image_links = extract_text(fields.get("全套配图链接", ""))
        if image_links:
            for line in image_links.strip().splitlines():
                parts = line.strip().split()
                url = next((p for p in parts if p.startswith("http")), None)
                if url:
                    images.append(url)
        if not images:
            image_dir = extract_text(fields.get("图片目录", ""))
            if image_dir:
                p = Path(image_dir)
                if p.is_dir():
                    images = sorted(str(f) for f in p.glob("*.png")) or sorted(str(f) for f in p.glob("*.jpg"))
        if not title:
            print("飞书记录缺少内容标题", file=sys.stderr)
            raise SystemExit(1)

    # ── 入口 B：直接传参 ──
    else:
        title = args.title or ""
        if not title:
            print("请提供 --title 或使用 --from-feishu 模式", file=sys.stderr)
            raise SystemExit(1)
        content = Path(args.content_file).read_text(encoding="utf-8") if args.content_file else (args.content or "")
        images = args.images or []

    # ── 自动生图 ──
    if args.auto_gen_images and not images:
        slug = re.sub(r"[^\w\-]", "-", title.lower())[:30].strip("-")
        out_dir = Path(args.image_output_dir) if args.image_output_dir else Path(f"/tmp/xhs-images/{slug}")
        print(f"开始自动生图，输出目录: {out_dir}")
        images = generate_images(title, content, out_dir)
        if not images:
            print("自动生图失败，请检查图片生成脚本配置", file=sys.stderr)
            raise SystemExit(1)

    title_file = Path("/tmp/xhs_title.txt")
    content_file = Path("/tmp/xhs_content.txt")
    title_file.write_text(title + "\n", encoding="utf-8")
    content_file.write_text(content, encoding="utf-8")

    schedule_at = args.schedule_at or default_schedule_iso(datetime.now().astimezone())

    cmd = [
        sys.executable, str(get_cli_path()), "fill-publish",
        "--title-file", str(title_file),
        "--content-file", str(content_file),
        "--schedule-at", schedule_at,
        "--original",
    ]
    if args.visibility:
        cmd += ["--visibility", args.visibility]
    if images:
        cmd += ["--images", *images]

    run(cmd)

    if not args.no_feishu_update and has_feishu():
        should_create = (not args.from_feishu) or bool(args.title)
        if should_create:
            create_content_record_lark(title, content, schedule_at, images, getattr(args, 'image_output_dir', '') or "")
        else:
            update_feishu(title, args.record_id, schedule_at, args.topic_record_id)


if __name__ == "__main__":
    main()
