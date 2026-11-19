# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
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

# Windows consoles (cp949) cannot encode emoji/check marks: never crash on output.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding=None if _s.isatty() else "utf-8", errors="replace")

SKILLS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared" / "tools"))
try:
    import ensure  # shared/tools/ensure.py (install-on-first-need helper)
except ImportError:
    ensure = None
DOC_SKILLS = {"pptx": "PPT", "docx": "워드", "xlsx": "엑셀", "pdf": "PDF"}
CACHE = Path.home() / ".teacher-studio" / "env.json"
NAMES = {"teacher-game": "🎮 수업 게임", "teacher-slides": "🖥 수업 슬라이드", "teacher-motion": "✨ 과목 소개 영상·수업 시작 화면", "teacher-law": "⚖️ 법률 안내", "teacher-class-tools": "🧰 타이머·뽑기·모둠·대진표·점수판", "teacher-data": "📊 엑셀·CSV 분석"}


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
        channel = ensure.find_system_browser() if ensure else ""
        with sync_playwright() as pw:
            (pw.chromium.launch(channel=channel) if channel else pw.chromium.launch()).close()
        return True
    except Exception:
        return False


def official_doc_skills() -> dict:
    """Which of Claude's official document skills (pptx / docx / xlsx / pdf) are installed in this environment's skill folders."""
    home = Path.home()
    roots = [home / ".claude" / "skills", home / ".claude" / "plugins", home / ".codex" / "skills", home / ".agents" / "skills",
             Path("/mnt/skills"), Path("/mnt/user-data/skills"), SKILLS]
    found: dict = {k: False for k in DOC_SKILLS}
    for root in roots:
        if not root.exists():
            continue
        base = len(root.parts)
        for dirpath, dirs, files in os.walk(root):
            if len(Path(dirpath).parts) - base > 6:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
            name = Path(dirpath).name
            if name in DOC_SKILLS and "SKILL.md" in files:
                found[name] = True
        if all(found.values()):
            break
    return found


def _codex_network_on() -> bool:
    """Read-only check of ~/.codex/config.toml for network_access = true (never prints file contents)."""
    try:
        text = (Path.home() / ".codex" / "config.toml").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    for line in text.splitlines():
        key, _, val = line.partition("=")
        if key.strip() == "network_access" and val.split("#")[0].strip().lower() == "true":
            return True
    return False


def _prefs_line() -> str:
    """Saved first-run preferences (school level / subject / device) in one Korean line."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import prefs
        return prefs.summary()
    except Exception:
        return "확인 못 했어요"


def report(agent: str = "") -> dict:
    """Probe tools, decide capabilities, cache and return them with a Korean summary."""
    agent = agent or guess_agent()
    node = shutil.which("node")
    node_ver = subprocess.run([node, "-v"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip() if node else ""
    caps = {
        "agent": agent,
        "os": platform.system(),
        "python": sys.version.split()[0],
        "node": node_ver,
        "ffmpeg": bool(shutil.which("ffmpeg")) or bool(ensure and ensure.is_present("imageio-ffmpeg")),
        "playwright": _has_playwright(),
        "skills": sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").exists()),
    }
    preview = {"claude-app": "오른쪽 화면에 바로 떠요", "claude-code": "크롬 창으로 자동으로 열어요", "codex": "크롬 창으로 열어요"}.get(agent, "파일로 저장해 크롬으로 열어요")
    share = ("오른쪽 위 '게시(Publish)' → 링크·QR" if agent == "claude-app"
             else "파일을 학교 드라이브에 올리거나 USB로 옮겨요 (링크가 필요하면 Claude 앱에서 '게시')")
    mp4_ready = caps["playwright"] and caps["ffmpeg"]
    codex_net = _codex_network_on() if agent == "codex" else None
    if mp4_ready:
        video = "MP4 영상 파일까지 바로 만들어요"
    elif agent in ("claude-code", "codex"):
        video = "MP4는 처음 요청할 때 필요한 작은 도구(합쳐서 약 80MB, 크롬이 있으면 그걸 써요)를 설치해 드려요 (먼저 물어볼게요)"
        if agent == "codex" and not codex_net:
            video += " — 인터넷이 꺼져 있으면 먼저 켜야 해요"
    else:
        video = "영상은 화면의 🎥 버튼으로 크롬에서 녹화(.webm)해 받아요 (이 환경에선 MP4 변환 도구를 깔기 어려워요)"
    if agent == "codex":
        law = ("최신 법 확인이 가능해요" if codex_net else
               "⚠️ 인터넷이 꺼져 있어 최신 법 확인·도구 설치가 막힐 수 있어요 — ~/.codex/config.toml에 [sandbox_workspace_write] 아래 network_access = true를 넣고, 웹 검색은 --search(live)로 켜 주세요")
    elif agent == "claude-app":
        law = "공식 출처에서 최신 법을 찾아 답해요 (웹 검색이 켜져 있어야 해요)"
    else:
        law = "공식 출처에서 최신 법을 찾아 근거와 함께 답해요"
    check = "끝까지 자동으로 플레이해 보고 점검해요" if caps["playwright"] else "글자·문법 자동 점검까지 해요 (자동 플레이는 없음)"
    tools = ensure.status() if ensure else {"present": [], "on_first_need": []}
    caps["tools"] = {"present": [t["name"] for t in tools["present"]], "on_first_need": [t["name"] for t in tools["on_first_need"]],
                     "ffmpeg": tools.get("ffmpeg", ""), "browser": tools.get("browser", "")}
    caps["official_doc_skills"] = official_doc_skills()
    docs = [DOC_SKILLS[k] for k, v in caps["official_doc_skills"].items() if v]
    doc_line = (f"Claude 공식 문서 스킬({', '.join(docs)})이 있어서 파일 만들기는 그쪽에 맡기고, 디자인·구성·점검은 교사 스튜디오가 얹어요" if docs
                else "PPT·워드·엑셀·PDF 파일은 공식 문서 스킬이 안 보여서, 처음 필요할 때 작은 도구를 설치해 드려요 (먼저 물어볼게요)")
    ready = [label for name, label in NAMES.items() if name in caps["skills"]]
    lines = [
        "🎉 교사 스튜디오 준비 완료!",
        f"· 지금 쓰는 곳: {({'claude-app': 'Claude 앱/웹', 'claude-code': 'Claude Code', 'codex': 'Codex'}).get(agent, agent)}",
        f"· 바로 만들 수 있어요: {', '.join(ready) if ready else '(설치된 칸 없음)'}",
        f"· 결과 보기: {preview}",
        f"· 영상: {video}",
        f"· 점검: {check}",
        f"· 법률 안내: {law}",
        f"· 나누기: {share}",
        f"· 문서 파일: {doc_line}",
        f"· 내 설정: {_prefs_line()}  (바꾸려면 「설정 바꿔 줘」)",
        f"· 처음 필요할 때 설치되는 도구: {', '.join(caps['tools']['on_first_need']) or '없음 (모두 준비됨)'}",
        "· 준비 중: 📄 가정통신문·공문, 📊 PPT 파일, 🎬 영상 편집",
    ]
    if not caps["python"].startswith("3"):
        lines.append("⚠️ 파이썬이 없어 조립 도구 대신 Claude가 직접 파일을 써요 (느려질 수 있어요)")
    caps["capabilities"] = {"preview": preview, "share": share, "video": video, "check": check, "law": law}
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
