# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Install Teacher Studio skills for Claude Code and/or Codex, then report what works.

Usage:
    python3 scripts/setup.py --agent claude-code          # register for Claude Code (~/.claude/skills)
    python3 scripts/setup.py --agent codex                # register for Codex (~/.agents/skills)
    python3 scripts/setup.py --agent claude-code --video  # also install Playwright + Chromium for MP4 / auto-play checks
    python3 scripts/setup.py --zip                        # only build dist/*.zip for Claude app upload

Safe to run again: stage and verify the full bundle before replacing any installed skill.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from typing import Callable
from pathlib import Path

# Windows consoles (cp949) cannot encode emoji/check marks: never crash on output.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding=None if _s.isatty() else "utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
SKILL_NAMES = ("teacher-studio", "teacher-game", "teacher-slides", "teacher-motion",
               "teacher-law", "teacher-class-tools", "teacher-data", "teacher-docs")
TARGETS = {
    "claude-code": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".agents" / "skills",
}


def install(agent: str, validate: Callable[[Path], None] | None = None) -> Path:
    """Stage the whole bundle and restore the old installation if activation fails."""
    dest = TARGETS[agent]
    dest.mkdir(parents=True, exist_ok=True)
    lock = dest.parent / ".teacher-studio-install.lock"
    lock.mkdir()
    try:
        _install_bundle(dest, validate)
    finally:
        lock.rmdir()
    return dest


def _install_bundle(dest: Path, validate: Callable[[Path], None] | None) -> None:
    work = Path(tempfile.mkdtemp(prefix=".teacher-studio-", dir=dest.parent))
    staged, backup = work / "new", work / "previous"
    replaced, activated = [], []
    keep_backup = False
    try:
        for name in SKILL_NAMES:
            src, copy = SKILLS / name, staged / name
            marker = src / "SKILL.md"
            if not marker.is_file() or f"name: {name}" not in marker.read_text(encoding="utf-8").splitlines():
                raise ValueError(f"설치 파일을 확인할 수 없어요 ({name}).")
            shutil.copytree(src, copy, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            if (copy / "SKILL.md").read_bytes() != marker.read_bytes():
                raise ValueError(f"설치 파일을 온전히 복사하지 못했어요 ({name}).")
        if validate:
            validate(staged)
        backup.mkdir()
        try:
            for name in SKILL_NAMES:
                target = dest / name
                if target.exists() or target.is_symlink():
                    target.rename(backup / name)
                    replaced.append(name)
                (staged / name).rename(target)
                activated.append(name)
        except BaseException:
            try:
                for name in reversed(activated):
                    (dest / name).rename(staged / name)
                for name in reversed(replaced):
                    (backup / name).rename(dest / name)
            except OSError as exc:
                keep_backup = True
                raise OSError(f"이전 설치를 옮기지 못했어요. 복구용 폴더: {backup}") from exc
            raise
    finally:
        if not keep_backup:
            shutil.rmtree(work, ignore_errors=True)
    for name in SKILL_NAMES:
        print(f"  ✓ {name} → {dest / name}")


def install_video() -> None:
    """Use the same optional tool installer as the MP4 renderer."""
    helper = ROOT / "shared" / "tools" / "ensure.py"
    for name in ("playwright", "ffmpeg"):
        subprocess.run([sys.executable, str(helper), name, "--yes"], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", choices=sorted(TARGETS))
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--zip", action="store_true")
    a = ap.parse_args()
    if a.zip:
        return subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--package-only"]).returncode
    if not a.agent:
        ap.error("--agent claude-code 또는 --agent codex 를 붙여 주세요")
    if sys.version_info < (3, 9):
        raise SystemExit("Python 3.9 이상이 필요해요")
    def validate(staged: Path) -> None:
        if a.video:
            print("영상과 자동 점검에 필요한 도구를 확인해요.", flush=True)
            install_video()
        doctor = staged / "teacher-studio" / "scripts" / "studio.py"
        subprocess.run([sys.executable, str(doctor), "doctor", "--agent", a.agent], check=True)

    try:
        install(a.agent, validate)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"설치를 마치지 못했어요. ({exc})", file=sys.stderr)
        return 1
    print("\n다음: 새 대화에서 「교사 스튜디오 시작」이라고 말하거나, 만들고 싶은 걸 바로 말해 보세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
