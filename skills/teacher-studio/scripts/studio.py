# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""One command for everything in Teacher Studio (fast path for Claude / Codex).

Usage:
    python3 studio.py list                                   # every missile and skin
    python3 studio.py fire game/escape-room/lab --content c.json [--out file.html] [--open]
    python3 studio.py fire slides/lesson-deck/clean-keynote --content c.json --open
    python3 studio.py fire motion/subject-intro/science-neon --content c.json --mp4
    python3 studio.py build game --spec spec.json [--out file.html] [--open]   # any game from a short spec
    python3 studio.py build slides --spec deck.json [--seed N] [--review DIR] [--open]  # designed slide deck from a short spec
    python3 studio.py check file.html
    python3 studio.py render file.html out.mp4 [--yes]       # finds Chrome/ffmpeg itself; --yes = installs small tools after consent
    python3 studio.py doctor                                 # what works in this environment

Missile ids are <kind>/<missile>/<skin>; kind = game | slides | motion.
Output defaults to ./TeacherStudio/<missile>-<skin>-<time>.html
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Windows consoles (cp949) cannot encode emoji/check marks: never crash on output.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding=None if _s.isatty() else "utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent  # .../skills
KINDS = {"game": "teacher-game", "slides": "teacher-slides", "motion": "teacher-motion"}
OUT_DIR = Path.cwd() / "TeacherStudio"


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


def cmd_fire(target: str, content: Path | None, out: Path | None, open_it: bool, mp4: bool) -> int:
    """Build one missile with the teacher's content, check it, optionally open / render."""
    try:
        kind, missile, skin = target.split("/")
    except ValueError:
        raise SystemExit("target must be kind/missile/skin, e.g. game/quiz-show/tv-studio")
    if mp4 and kind == "game":
        raise SystemExit("이 게임은 화면 파일로 받을 수 있어요.")
    skill = _skill(kind)
    out = out or OUT_DIR / f"{missile}-{skin}-{time.strftime('%m%d-%H%M%S')}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    if kind == "game":
        args = [str(skill / "scripts" / "fire.py"), "--missile", missile, "--skin", skin, "--out", str(out)]
        if content:
            args += ["--content", str(content)]
        check = _run(args)
    else:
        args = [str(skill / "scripts" / "build_stage.py"), "--missile", missile, "--skin", skin, "--out", str(out)]
        if content:
            args += ["--content", str(content)]
        if _run(args):
            return 1
        check = _run([str(skill / "scripts" / "check_page.py"), str(out)])
    if check not in (0, 2):
        return 1
    if mp4:
        video = out.with_suffix(".mp4")
        if _run([str(skill / "scripts" / "render_mp4.py"), str(out), str(video)]):
            print(f"NOT READY {video} (HTML created at {out})")
            return 1
        print(f"READY {video}")
    print(f"{'PARTIAL' if check == 2 else 'READY'} {out}")
    if open_it:
        webbrowser.open(out.resolve().as_uri())
    return check


def cmd_build(kind: str, spec: Path, out: Path | None, open_it: bool, extra: list[str] | None = None) -> None:
    """Build a game or a slide deck from a spec.json (tools + design tokens), check it, optionally open it."""
    if kind == "slides":
        skill = _skill("slides")
        out = out or OUT_DIR / f"deck-{spec.stem}-{time.strftime('%m%d-%H%M%S')}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        if _run([str(skill / "scripts" / "deck.py"), "--spec", str(spec), "--out", str(out)] + (extra or [])):
            raise SystemExit(1)
        if open_it:
            webbrowser.open(out.resolve().as_uri())
        return
    if kind != "game":
        raise SystemExit("build supports: game | slides")
    skill = _skill("game")
    out = out or OUT_DIR / f"game-{spec.stem}-{time.strftime('%m%d-%H%M%S')}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    rc = _run([str(skill / "scripts" / "build.py"), "--spec", str(spec), "--out", str(out)])
    if open_it and rc in (0, 2):
        webbrowser.open(out.resolve().as_uri())
    if rc:
        raise SystemExit(rc)


def cmd_check(path: Path, yes: bool = False) -> None:
    """Check a game or stage page with the shared checker."""
    raise SystemExit(_run([str(_skill("game") / "scripts" / "check_game.py"), str(path)] + (["--yes"] if yes else [])))


def cmd_render(page: Path, out: Path, yes: bool = False) -> None:
    """Render a stage page to MP4 (--yes = the teacher agreed to install the missing small tools)."""
    raise SystemExit(_run([str(_skill("motion") / "scripts" / "render_mp4.py"), str(page), str(out)] + (["--yes"] if yes else [])))


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
    b = sub.add_parser("build")
    b.add_argument("kind")
    b.add_argument("--spec", required=True, type=Path)
    b.add_argument("--out", type=Path)
    b.add_argument("--open", action="store_true")
    b.add_argument("--seed", type=int)
    b.add_argument("--review", type=Path)
    b.add_argument("--purpose", default="")
    b.add_argument("--mood", default="")
    b.add_argument("--style", default="")
    b.add_argument("--pptx", nargs="?", const="auto", help="slides: ALSO write an editable .pptx (PPT / 파워포인트 / 나중에 고칠 거예요)")
    b.add_argument("--template", type=Path, help="slides + --pptx: the teacher's own .pptx/.potx (template first)")
    b.add_argument("--yes", action="store_true", help="the teacher agreed to install the small tool (python-pptx)")
    c = sub.add_parser("check")
    c.add_argument("path", type=Path)
    c.add_argument("--yes", action="store_true", help="download the optional syntax checker")
    r = sub.add_parser("render")
    r.add_argument("page", type=Path)
    r.add_argument("out", type=Path)
    r.add_argument("--yes", action="store_true")
    d = sub.add_parser("doctor")
    d.add_argument("--agent", default="")
    d.add_argument("--json", action="store_true")
    d.add_argument("--out", type=Path)
    d.add_argument("--host-skills", nargs="*")
    for flag in ("web-search", "preview", "share"):
        d.add_argument(f"--{flag}", choices=("yes", "no", "unknown"), default="unknown")
    a = ap.parse_args()
    if a.cmd == "list":
        cmd_list()
    elif a.cmd == "fire":
        raise SystemExit(cmd_fire(a.target, a.content, a.out, a.open, a.mp4))
    elif a.cmd == "build":
        extra = []
        for flag in ("seed", "review", "purpose", "mood", "style"):
            if getattr(a, flag):
                extra += [f"--{flag}", str(getattr(a, flag))]
        if a.kind == "slides":
            if a.pptx:
                extra += ["--pptx"] + ([] if a.pptx == "auto" else [a.pptx])
            if a.template:
                extra += ["--template", str(a.template)]
            if a.yes:
                extra += ["--yes"]
        cmd_build(a.kind, a.spec, a.out, a.open, extra)
    elif a.cmd == "check":
        cmd_check(a.path, a.yes)
    elif a.cmd == "render":
        cmd_render(a.page, a.out, a.yes)
    elif a.cmd == "doctor":
        sys.path.insert(0, str(HERE))
        from doctor import report  # noqa: E402

        info = report(a.agent, output=a.out, host_skills=a.host_skills, web_search=a.web_search,
                      preview=a.preview, share=a.share)
        print(json.dumps(info, ensure_ascii=False, indent=2) if a.json else info["summary"])
        raise SystemExit(0 if info["writable"] else 1)


def _no_browser_guard() -> bool:
    """True when no browser can start here (an agent's security box). shared/tools/workdir.py then prints ONE line and makes
    every screen check below skip at once instead of waiting for each launch to fail."""
    try:
        here = Path(__file__).resolve().parent
        for d in (here, here.parent / "shared" / "tools", here.parent / "tools", here.parents[2] / "shared" / "tools"):
            if (d / "workdir.py").is_file():
                if str(d) not in sys.path:
                    sys.path.append(str(d))
                import workdir
                return workdir.guard_browser(quiet=True)  # this script rarely needs a browser: the line is printed only where one is needed
    except Exception:  # noqa: BLE001 - the guard must never stop a build
        pass
    return False


if __name__ == "__main__":
    _no_browser_guard()
    main()
