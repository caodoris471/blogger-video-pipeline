#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed delivery gate; validates review evidence, not visual watermark detection."""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm"}
STAGING = Path("01_过程稿_临时资料") / "无水印待验"
DELIVERY = Path("02-Whisper转写") / "视频源文件"
REPORT = Path("01-视频清单") / "watermark_review.json"
SITES = {
    "tiksave": "https://tiksave.io/zh-cn",
    "cobalt": "https://cobalt.tools/",
    "tubedown": "https://tubedown.cn/youtube",
    "fdown": "https://fdown.net/",
}
ROUTES = {
    "tiktok": ("cobalt", "tiksave"),
    "youtube": ("cobalt", "tubedown"),
    "facebook": ("cobalt", "fdown"),
    "instagram": ("cobalt",),
    "bilibili": ("cobalt",),
    "douyin": (),
    "xhs": (),
    "kuaishou": (),
    "wxchannels": (),
}
BACKENDS = {
    "xhs": (("XHS-Downloader", "https://github.com/JoeanAmier/XHS-Downloader"),
            ("lux", "https://github.com/iawia002/lux")),
    "douyin": (("Douyin_TikTok_Download_API（本地部署）", "https://github.com/Evil0ctal/Douyin_TikTok_Download_API"),),
    "kuaishou": (("KS-Downloader", "https://github.com/JoeanAmier/KS-Downloader"),
                 ("lux", "https://github.com/iawia002/lux")),
    "wxchannels": (("wx_channels_download（现有流程，MIT + Commons Clause）", "https://github.com/ltaoo/wx_channels_download"),
                   ("res-downloader（本机嗅探备用）", "https://github.com/putyy/res-downloader")),
    "bilibili": (("yt-dlp", "https://github.com/yt-dlp/yt-dlp"),
                 ("lux", "https://github.com/iawia002/lux")),
    "youtube": (("yt-dlp", "https://github.com/yt-dlp/yt-dlp"),),
    "tiktok": (("yt-dlp（排除带水印格式）", "https://github.com/yt-dlp/yt-dlp"),
               ("Douyin_TikTok_Download_API（本地部署）", "https://github.com/Evil0ctal/Douyin_TikTok_Download_API")),
    "instagram": (("yt-dlp", "https://github.com/yt-dlp/yt-dlp"),),
    "facebook": (("yt-dlp", "https://github.com/yt-dlp/yt-dlp"),),
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def videos(directory):
    return sorted(p for p in directory.iterdir()
                  if p.is_file() and p.suffix.lower() in VIDEO_EXT) if directory.exists() else []


def load_report(root):
    report = json.loads((root / REPORT).read_text(encoding="utf-8"))
    if report.get("schema_version") != 1 or not isinstance(report.get("videos"), list):
        raise ValueError("验收清单格式无效；请先运行 init")
    return report


def initialize(root, expected_count, platform):
    """New/replaced files always start pending, including legacy delivery files."""
    path = root / REPORT
    old = load_report(root) if path.exists() else {"videos": []}
    old_by_name = {v["filename"]: v for v in old["videos"]}
    source = root / STAGING
    if not videos(source):
        source = root / DELIVERY
    items = []
    for video in videos(source):
        sha = digest(video)
        previous = old_by_name.get(video.name, {})
        if previous.get("sha256") == sha:
            items.append(previous)
        else:
            items.append({
                "filename": video.name, "sha256": sha, "platform": platform,
                "source_url": "", "provider": "", "format_id": "", "format_note": "",
                "watermark_status": "pending", "full_video_reviewed": False,
                "reviewer": "", "review_notes": "", "evidence": "",
            })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "expected_count": expected_count,
                                "videos": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已登记 {len(items)} 条，预期 {expected_count} 条；新文件均待验：{path}")


def probe(video):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "stream=codec_type:format=duration",
        "-of", "json", str(video),
    ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, check=True)
    media = json.loads(result.stdout)
    duration = float(media.get("format", {}).get("duration", 0))
    if not math.isfinite(duration) or duration <= 0 or not any(
            s.get("codec_type") == "video" for s in media.get("streams", [])):
        raise ValueError(f"不是有效完整视频：{video.name}")


def validate(root, staging=False, expected_count=None):
    report = load_report(root)
    expected = report.get("expected_count")
    if type(expected) is not int or expected <= 0:
        raise ValueError("expected_count 必须是筛选清单的正整数条数，空清单不能通过")
    if expected_count is not None and expected != expected_count:
        raise ValueError(f"筛选清单有 {expected_count} 条，验收清单却记录 {expected} 条")
    files = {p.name: p for p in videos(root / (STAGING if staging else DELIVERY))}
    items = report["videos"]
    names = [v["filename"] for v in items]
    if len(items) != expected or len(set(names)) != len(names) or set(names) != set(files):
        raise ValueError("视频数/文件名与验收清单不一致，存在缺失、重复或未登记文件")
    for item in items:
        name = item["filename"]
        if item.get("watermark_status") != "clean" or item.get("full_video_reviewed") is not True:
            raise ValueError(f"{name}：尚未全片确认无水印（禁止只凭网站文案或抽帧通过）")
        for key in ("source_url", "platform", "provider", "reviewer", "review_notes", "evidence"):
            if not str(item.get(key, "")).strip():
                raise ValueError(f"{name}：缺少 {key}")
        if not item["source_url"].startswith(("https://", "http://")):
            raise ValueError(f"{name}：缺少原始作品链接")
        format_id = str(item.get("format_id", "")).lower()
        note = str(item.get("format_note", "")).lower()
        if (item["platform"] == "tiktok" and format_id in {"download", "download_addr"}
                or "watermarked" in note or "带水印" in note):
            raise ValueError(f"{name}：来源已明确标记为带水印格式，请换源")
        sha = digest(files[name])
        if sha != item.get("sha256"):
            raise ValueError(f"{name}：文件已替换或被修改，必须重新验收")
        evidence = (root / item["evidence"]).resolve()
        if not evidence.is_relative_to(root.resolve()) or not evidence.is_file():
            raise ValueError(f"{name}：复核记录必须位于项目内且真实存在")
        if sha not in evidence.read_text(encoding="utf-8"):
            raise ValueError(f"{name}：复核记录未关联此文件的 SHA-256")
        probe(files[name])
    return files


def promote(root):
    files = validate(root, staging=True)
    target = root / DELIVERY
    target.mkdir(parents=True, exist_ok=True)
    # Preflight the whole batch before copying; never overwrite a different existing video.
    if {p.name for p in videos(target)} - set(files):
        raise ValueError("正式目录有本次清单之外的视频，请先核对项目范围")
    for name, source in files.items():
        dest = target / name
        if dest.exists() and digest(dest) != digest(source):
            raise ValueError(f"拒绝覆盖已有不同文件：{dest}")
    for name, source in files.items():
        dest = target / name
        if not dest.exists():
            shutil.copy2(source, dest)
    validate(root)
    print(f"PASS：{len(files)} 条已通过并归集到 {target}")


def require_clean(project, expected_count=None):
    """Shared by transcription entrypoints; any missing/invalid evidence blocks the run."""
    try:
        files = validate(Path(project), expected_count=expected_count)
        print(f"PASS：{len(files)} 条无水印复核记录及文件一致")
        return True
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(f"BLOCKED：无水印验收未通过：{exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="按平台列出免费工具优先路线及网站备用入口")
    plan.add_argument("--platform", choices=ROUTES, required=True)
    for command in ("init", "check", "promote"):
        child = commands.add_parser(command)
        child.add_argument("project", type=Path)
        if command == "init":
            child.add_argument("--expected-count", type=int, required=True)
            child.add_argument("--platform", choices=ROUTES, required=True)
        if command == "check":
            child.add_argument("--staging", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            print("优先本机免费工具（部署、许可证与实测状态见 references/open-source-downloaders.md）：")
            for name, url in BACKENDS[args.platform]:
                print(f"{name}: {url}")
            print("免费网站备用入口：")
            for key in ROUTES[args.platform]:
                print(f"{key}: {SITES[key]}")
            print("工具/网站路线已登记，不代表已安装或逐平台实测；下载后仍须全片复核。")
        elif args.command == "init":
            if args.expected_count <= 0:
                raise ValueError("筛选命中为 0 时只报告零命中，不建立成功验收")
            initialize(args.project.resolve(), args.expected_count, args.platform)
        elif args.command == "promote":
            promote(args.project.resolve())
        else:
            files = validate(args.project.resolve(), staging=args.staging)
            print(f"PASS：{len(files)} 条；本工具检查记录与文件，不执行视觉水印识别")
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(f"BLOCKED：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
