"""One command for everything in Teacher Studio (fast path for Claude / Codex).

Usage:
    python3 studio.py list                                   # every missile and skin
    python3 studio.py fire game/escape-room/lab --content c.json [--out file.html] [--open]
    python3 studio.py fire slides/lesson-deck/clean-keynote --content c.json --open
    python3 studio.py fire motion/subject-intro/science-neon --content c.json --mp4
    python3 studio.py check file.html
    python3 studio.py render file.html out.mp4               # needs Playwright + ffmpeg
    python3 studio.py doctor                                 # what works in this environment

Missile ids are <kind>/<missile>/<skin>; kind = game | slides | motion.
Output defaults to ~/TeacherStudio/<missile>-<skin>-<time>.html
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent  # .../skills
KINDS = {"game": "teacher-game", "slides": "teacher-slides", "motion": "teacher-motion"}
OUT_DIR = Path.home() / "TeacherStudio"


def _skill(kind: str) -> Path:
    """Locate an installed sibling skill folder by kind."""
    if kind not in KINDS:
        raise SystemExit(f"unknown kind '{kind}' (game | slides | motion)")
    path = SKILLS / KINDS[kind]
    if not (path / "SKILL.md").exists():
        raise SystemExit(f"skill '{KINDS[kind]}' is not installed next to teacher-studio ({SKILLS})")
    return path


def _run(cmd: list[str]) -> int:
    """Run a sub-command, streaming its output."""
    return subprocess.run([sys.executable, *cmd]).returncode


def cmd_list() -> None:
    """Print every installed missile as kind/missile: skins."""
    for kind, name in KINDS.items():
        base = SKILLS / name / "assets" / "missiles"
        if not base.exists():
            continue
        for m in sorted(p for p in base.iterdir() if p.is_dir()):
            skins = ", ".join(sorted(s.stem for s in (m / "skins").glob("*.json")))
            print(f"{kind}/{m.name}: {skins}")


def cmd_fire(target: str, content: Path | None, out: Path | None, open_it: bool, mp4: bool) -> None:
    """Build one missile with the teacher's content, check it, optionally open / render."""
    try:
        kind, missile, skin = target.split("/")
    except ValueError:
        raise SystemExit("target must be kind/missile/skin, e.g. game/quiz-show/tv-studio")
    skill = _skill(kind)
    out = out or OUT_DIR / f"{missile}-{skin}-{time.strftime('%m%d-%H%M%S')}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    if kind == "game":
        args = [str(skill / "scripts" / "fire.py"), "--missile", missile, "--skin", skin, "--out", str(out)]
        if content:
            args += ["--content", str(content)]
        if _run(args):
            raise SystemExit(1)
    else:
        args = [str(skill / "scripts" / "build_stage.py"), "--missile", missile, "--skin", skin, "--out", str(out)]
        if content:
            args += ["--content", str(content)]
        if _run(args) or _run([str(skill / "scripts" / "check_page.py"), str(out)]):
            raise SystemExit(1)
    print(f"READY {out}")
    if mp4:
        if kind == "game":
            print("MP4 is for slides/motion only")
        else:
            _run([str(skill / "scripts" / "render_mp4.py"), str(out), str(out.with_suffix(".mp4"))])
    if open_it:
        webbrowser.open(out.resolve().as_uri())


def cmd_check(path: Path) -> None:
    """Check a game or stage page with the shared checker."""
    raise SystemExit(_run([str(_skill("game") / "scripts" / "check_game.py"), str(path)]))


def cmd_render(page: Path, out: Path) -> None:
    """Render a stage page to MP4."""
    raise SystemExit(_run([str(_skill("motion") / "scripts" / "render_mp4.py"), str(page), str(out)]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    f = sub.add_parser("fire")
    f.add_argument("target")
    f.add_argument("--content", type=Path)
    f.add_argument("--out", type=Path)
    f.add_argument("--open", action="store_true")
    f.add_argument("--mp4", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("path", type=Path)
    r = sub.add_parser("render")
    r.add_argument("page", type=Path)
    r.add_argument("out", type=Path)
    d = sub.add_parser("doctor")
    d.add_argument("--agent", default="")
    d.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd == "list":
        cmd_list()
    elif a.cmd == "fire":
        cmd_fire(a.target, a.content, a.out, a.open, a.mp4)
    elif a.cmd == "check":
        cmd_check(a.path)
    elif a.cmd == "render":
        cmd_render(a.page, a.out)
    elif a.cmd == "doctor":
        sys.path.insert(0, str(HERE))
        from doctor import report  # noqa: E402

        info = report(a.agent)
        print(json.dumps(info, ensure_ascii=False, indent=2) if a.json else info["summary"])


if __name__ == "__main__":
    main()
