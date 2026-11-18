"""Install Teacher Studio skills for Claude Code and/or Codex, then report what works.

Usage:
    python3 scripts/setup.py --agent claude-code          # register for Claude Code (~/.claude/skills)
    python3 scripts/setup.py --agent codex                # register for Codex (~/.agents/skills)
    python3 scripts/setup.py --agent claude-code --video  # also install Playwright + Chromium for MP4 / auto-play checks
    python3 scripts/setup.py --zip                        # only build dist/*.zip for Claude app upload

Safe to run again: it replaces only folders named teacher-* in the target skills directory.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
TARGETS = {
    "claude-code": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".agents" / "skills",
}


def install(agent: str) -> Path:
    """Copy every skills/teacher-* folder into the agent's user-level skills directory."""
    dest = TARGETS[agent]
    dest.mkdir(parents=True, exist_ok=True)
    for skill in sorted(SKILLS.glob("teacher-*")):
        if not (skill / "SKILL.md").exists():
            continue
        target = dest / skill.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(skill, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"  ✓ {skill.name} → {target}")
    return dest


def install_video() -> None:
    """Install Python Playwright and its Chromium (about 150MB) for MP4 rendering and auto-play checks."""
    pip = [sys.executable, "-m", "pip", "install", "--user", "playwright"]
    if subprocess.run(pip).returncode != 0:
        subprocess.run(pip[:-2] + ["--break-system-packages", "playwright"])
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    if not shutil.which("ffmpeg"):
        print("  ⚠ ffmpeg가 없어요. Windows: winget install ffmpeg / Mac: brew install ffmpeg (설치 후 MP4 가능)")


def build_zips() -> None:
    """Zip each skill for Claude app upload (Settings > Capabilities > Skills)."""
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for skill in sorted(SKILLS.glob("teacher-*")):
        out = dist / f"{skill.name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(skill.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    z.write(f, f.relative_to(SKILLS))
        print(f"  ✓ dist/{out.name} ({out.stat().st_size // 1024} KB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", choices=sorted(TARGETS))
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--zip", action="store_true")
    a = ap.parse_args()
    if a.zip:
        build_zips()
        return
    if not a.agent:
        ap.error("--agent claude-code 또는 --agent codex 를 붙여 주세요")
    if sys.version_info < (3, 9):
        raise SystemExit("Python 3.9 이상이 필요해요")
    print("1) 스킬 등록")
    dest = install(a.agent)
    if a.video:
        print("2) 영상·자동 점검 도구 설치")
        install_video()
    print("3) 환경 확인\n")
    doctor = dest / "teacher-studio" / "scripts" / "studio.py"
    subprocess.run([sys.executable, str(doctor), "doctor", "--agent", a.agent])
    print("\n다음: 새 대화에서 「교사 스튜디오 시작」이라고 말하거나, 만들고 싶은 걸 바로 말해 보세요.")


if __name__ == "__main__":
    main()
