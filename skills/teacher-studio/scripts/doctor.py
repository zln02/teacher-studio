# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Find out what works in this environment and say it in teacher language.

Usage: python3 doctor.py [--agent claude-app|claude-code|codex|other] [--json]
Probes the current session without installing tools or changing host settings.
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
NAMES = {"teacher-game": "🎮 수업 게임", "teacher-slides": "🖥 수업 슬라이드", "teacher-motion": "✨ 과목 소개 영상·수업 시작 화면", "teacher-law": "⚖️ 법률 안내", "teacher-class-tools": "🧰 타이머·뽑기·모둠·대진표·점수판", "teacher-data": "📊 엑셀·CSV 분석", "teacher-docs": "📄 공문·가정통신문·한글·워드·PDF"}


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


def _writable(folder: Path) -> bool:
    """Test a real write without leaving a file or creating the output directory."""
    parent = folder
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    try:
        probe = parent / f".teacher-studio-probe-{os.getpid()}"
        probe.write_bytes(b"teacher-studio")
        probe.unlink()
    except OSError:
        return False
    return True


def _command_version(executable: str, flag: str) -> str:
    try:
        result = subprocess.run([executable, flag], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=5)
        return result.stdout.strip().splitlines()[0] if result.returncode == 0 and result.stdout.strip() else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def default_output() -> Path:
    return Path.cwd() / "TeacherStudio"


def _browser_ready() -> bool:
    """Open a page using the same browser candidates as the runtime checks."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            channel = ensure.find_system_browser() if ensure else ""
            for candidate in dict.fromkeys((channel, "")):
                try:
                    browser = pw.chromium.launch(timeout=5000, **({"channel": candidate} if candidate else {}))
                    try:
                        page = browser.new_page()
                        page.set_content("<title>Teacher Studio</title>", timeout=5000)
                        return page.title() == "Teacher Studio"
                    finally:
                        browser.close()
                except Exception:
                    continue
    except Exception:
        pass
    return False


def _prefs_line() -> str:
    """Saved first-run preferences (school level / subject / device) in one Korean line."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import prefs
        return prefs.summary()
    except Exception:
        return "확인 못 했어요"


def report(agent: str = "", *, output: Path | None = None, host_skills: list[str] | None = None,
           web_search: str = "unknown", preview: str = "unknown", share: str = "unknown") -> dict:
    """Probe the shell and record explicitly confirmed host capabilities separately."""
    record_python()
    agent = agent or guess_agent()
    output = output or default_output()
    output = output.resolve()
    writable = _writable(output)
    node = shutil.which("node")
    browser = _browser_ready()
    tools = ensure.status() if ensure else {"present": [], "on_first_need": []}
    shell_network = tools.get("network")
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path and ensure and ensure.is_present("imageio-ffmpeg"):
        ffmpeg_path = ensure.ensure_ffmpeg()["path"]
    ffmpeg = bool(ffmpeg_path and _command_version(ffmpeg_path, "-version"))
    siblings = sorted(name for name in NAMES if (SKILLS / name / "SKILL.md").is_file())
    caps = {
        "agent": agent, "os": platform.system(), "python": sys.version.split()[0],
        "python_executable": sys.executable, "node": _command_version(node, "-v") if node else "",
        "output": str(output), "writable": writable, "playwright": browser, "ffmpeg": ffmpeg,
        "shell_network": shell_network, "shell_network_host": "pypi.org",
        "web_search": web_search, "preview": preview, "share": share,
        "skills": siblings, "host_skills": host_skills,
        "tools": {"present": [t["name"] for t in tools["present"]],
                  "on_first_need": [t["name"] for t in tools["on_first_need"]],
                  "ffmpeg": tools.get("ffmpeg", ""), "browser": tools.get("browser", "")},
    }
    ready = [label for name, label in NAMES.items() if name in siblings]
    docs = [label for name, label in DOC_SKILLS.items() if host_skills is not None and name in host_skills]
    confirmed = {"yes": "쓸 수 있어요", "no": "이 대화에서는 쓸 수 없어요", "unknown": "아직 확인하지 못했어요"}
    caps["summary"] = "\n".join([
        "🎉 교사 스튜디오 준비 상태",
        f"· 지금 쓰는 곳: {({'claude-app': 'Claude 앱/웹', 'claude-code': 'Claude Code', 'codex': 'Codex'}).get(agent, agent)}",
        f"· 준비된 자료 도구: {', '.join(ready) or '아직 찾지 못했어요'}",
        "· 파일 저장: " + ("선택한 위치에 파일을 저장할 수 있어요" if writable else "이 위치에 파일을 저장할 수 없어요"),
        f"· 대화에서 결과 미리 보기: {confirmed[preview]}",
        f"· 대화에서 공유 링크 만들기: {confirmed[share]}",
        "· 영상: " + ("MP4 파일을 만들 수 있어요" if browser and ffmpeg and writable else "MP4를 만들 준비가 아직 되지 않았어요"),
        "· 점검: " + ("화면을 직접 열어 점검할 수 있어요" if browser else "글자와 파일은 살펴볼 수 있어요. 실제 작동은 아직 확인하지 못했어요"),
        "· 도구를 받는 곳에 연결: " + confirmed[{True: "yes", False: "no", None: "unknown"}[shell_network]],
        f"· 대화에서 최신 출처 검색: {confirmed[web_search]}",
        f"· 이 대화에서 확인한 문서 도구: {', '.join(docs) if docs else '아직 확인한 도구가 없어요'}",
        f"· 내 설정: {_prefs_line()}  (바꾸려면 「설정 바꿔 줘」)",
    ])
    return caps


def record_python() -> str:
    """Remember this interpreter's absolute path in ~/.teacher-studio/env.json (other keys kept),
    so run.cmd / run.sh work later even when `py`/`python3` is not on PATH (e.g. a sandbox)."""
    home = Path(os.environ.get("TEACHER_STUDIO_HOME") or Path.home() / ".teacher-studio")
    cache = home / "env.json"
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    if data.get("python_path") == sys.executable:
        return sys.executable
    data["python_path"] = sys.executable
    try:
        home.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
    return sys.executable


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agent", default="")
    ap.add_argument("--out", type=Path, help="output directory to probe")
    ap.add_argument("--host-skills", nargs="*", help="skill names observed in the host's active list")
    for flag in ("web-search", "preview", "share"):
        ap.add_argument(f"--{flag}", choices=("yes", "no", "unknown"), default="unknown")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    info = report(a.agent, output=a.out, host_skills=a.host_skills, web_search=a.web_search,
                  preview=a.preview, share=a.share)
    print(json.dumps(info, ensure_ascii=False, indent=2) if a.json else info["summary"])
    return 0 if info["writable"] else 1


if __name__ == "__main__":
    sys.exit(main())
