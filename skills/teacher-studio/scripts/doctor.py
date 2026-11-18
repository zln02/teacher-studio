"""Find out what works in this environment and say it in teacher language.

Usage: python3 doctor.py [--agent claude-app|claude-code|codex|other] [--json]
Writes ~/.teacher-studio/env.json so later turns don't need to probe again.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SKILLS = Path(__file__).resolve().parent.parent.parent
CACHE = Path.home() / ".teacher-studio" / "env.json"
NAMES = {"teacher-game": "🎮 수업 게임", "teacher-slides": "🖥 수업 슬라이드", "teacher-motion": "✨ 과목 소개 영상·수업 시작 화면"}


def guess_agent() -> str:
    """Best guess of the host from environment hints; the agent should confirm with --agent."""
    env = os.environ
    if any(k.startswith("CODEX") for k in env):
        return "codex"
    if Path("/mnt/user-data").exists():
        return "claude-app"
    if env.get("CLAUDECODE") or any(k.startswith("CLAUDE_CODE") for k in env):
        return "claude-code"
    return "other"


def _has_playwright() -> bool:
    """True when Python Playwright and its Chromium can actually launch."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as pw:
            pw.chromium.launch().close()
        return True
    except Exception:
        return False


def report(agent: str = "") -> dict:
    """Probe tools, decide capabilities, cache and return them with a Korean summary."""
    agent = agent or guess_agent()
    node = shutil.which("node")
    node_ver = subprocess.run([node, "-v"], capture_output=True, text=True).stdout.strip() if node else ""
    caps = {
        "agent": agent,
        "os": platform.system(),
        "python": sys.version.split()[0],
        "node": node_ver,
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "playwright": _has_playwright(),
        "skills": sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").exists()),
    }
    preview = {"claude-app": "오른쪽 화면에 바로 떠요", "claude-code": "크롬 창으로 자동으로 열어요", "codex": "크롬 창으로 열어요"}.get(agent, "파일로 저장해 크롬으로 열어요")
    share = ("오른쪽 위 '게시(Publish)' → 링크·QR" if agent == "claude-app"
             else "파일을 학교 드라이브에 올리거나 USB로 옮겨요 (링크가 필요하면 Claude 앱에서 '게시')")
    video = ("MP4 영상 파일까지 바로 만들어요" if caps["playwright"] and caps["ffmpeg"]
             else "영상은 화면의 🎥 버튼으로 크롬에서 녹화해 받아요 (MP4 자동 변환은 이 환경에 없음)")
    check = "끝까지 자동으로 플레이해 보고 점검해요" if caps["playwright"] else "글자·문법 자동 점검까지 해요 (자동 플레이는 없음)"
    ready = [label for name, label in NAMES.items() if name in caps["skills"]]
    lines = [
        "🎉 교사 스튜디오 준비 완료!",
        f"· 지금 쓰는 곳: {({'claude-app': 'Claude 앱/웹', 'claude-code': 'Claude Code', 'codex': 'Codex'}).get(agent, agent)}",
        f"· 바로 만들 수 있어요: {', '.join(ready) if ready else '(설치된 칸 없음)'}",
        f"· 결과 보기: {preview}",
        f"· 영상: {video}",
        f"· 점검: {check}",
        f"· 나누기: {share}",
        "· 준비 중: 📄 가정통신문·공문, 📊 PPT 파일, 🎬 영상 편집, 🧰 수업 도구",
    ]
    if not caps["python"].startswith("3"):
        lines.append("⚠️ 파이썬이 없어 조립 도구 대신 Claude가 직접 파일을 써요 (느려질 수 있어요)")
    caps["capabilities"] = {"preview": preview, "share": share, "video": video, "check": check}
    caps["summary"] = "\n".join(lines)
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(caps, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
    return caps


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agent", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    info = report(a.agent)
    print(json.dumps(info, ensure_ascii=False, indent=2) if a.json else info["summary"])
