# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Copy shared runtime files into every skill that uses them, then zip each skill.

shared/ is the source of truth. Each skill must stay self-contained when zipped, so its own copy lives in
skills/<skill>/shared/ (design, fonts, tools, vendor, voice) and, for the stage skills, assets/ + scripts/.

Usage:
    python3 tools/sync_shared.py            # copy shared -> skills, then rebuild dist/*.zip
    python3 tools/sync_shared.py --check    # exit 1 if any copy differs from shared/ (also AGENTS.md vs CLAUDE.md, dist zips)
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared"
STAGE = SHARED / "stage"
STAGE_SKILLS = ("teacher-motion", "teacher-slides")

# what each skill gets under skills/<skill>/shared/  (vendor = ids from shared/vendor/manifest.json)
PLAN = {
    "teacher-game": {"design": True, "fonts": True, "tools": True, "voice": True, "assets": True, "vendor": ["confetti", "motion", "lucide", "katex", "phaser"]},
    "teacher-slides": {"design": True, "fonts": True, "tools": True, "vendor": ["anime", "motion", "chartjs", "katex", "lucide", "confetti"]},
    "teacher-motion": {"design": True, "fonts": True, "tools": True, "vendor": ["anime", "motion", "lucide", "confetti"]},
    "teacher-studio": {"design": False, "fonts": False, "tools": True, "vendor": []},
}


def _files(folder: Path) -> list[Path]:
    """All files under a folder (no caches), sorted."""
    return sorted(f for f in folder.rglob("*") if f.is_file() and "__pycache__" not in f.parts)


def expected() -> dict[Path, bytes]:
    """Every copy that must exist: destination path -> exact bytes (from shared/)."""
    out: dict[Path, bytes] = {}

    def add(src: Path, dst: Path) -> None:
        out[dst] = src.read_bytes()

    for name in STAGE_SKILLS:
        skill = ROOT / "skills" / name
        add(STAGE / "stage.html", skill / "assets" / "stage.html")
        for f in (STAGE / "vendor").iterdir():
            add(f, skill / "assets" / "vendor" / f.name)
        for f in ("build_stage.py", "render_mp4.py", "check_page.py"):
            add(STAGE / f, skill / "scripts" / f)
    for plan_skill, cfg in PLAN.items():
        base = ROOT / "skills" / plan_skill / "shared"
        if cfg["design"]:
            for f in _files(SHARED / "design"):
                add(f, base / "design" / f.relative_to(SHARED / "design"))
        if cfg["fonts"]:
            for f in _files(SHARED / "fonts"):
                add(f, base / "fonts" / f.relative_to(SHARED / "fonts"))
        if cfg["tools"]:
            for tool in ("ensure.py", "stamp.py"):
                add(SHARED / "tools" / tool, base / "tools" / tool)
        if cfg.get("assets"):  # design asset arsenal (characters, icons, colors, sfx) - see shared/assets/manifest.json
            for f in _files(SHARED / "assets"):
                if f.name != "verify_assets.py":
                    add(f, base / "assets" / f.relative_to(SHARED / "assets"))
        if cfg.get("voice"):
            add(SHARED / "voice" / "voice.js", base / "voice" / "voice.js")
        if cfg["vendor"]:
            man = json.loads((SHARED / "vendor" / "manifest.json").read_text(encoding="utf-8"))
            libs = {k: v for k, v in man["libs"].items() if k in cfg["vendor"]}
            man["libs"] = libs
            out[base / "vendor" / "manifest.json"] = json.dumps(man, ensure_ascii=False, indent=1).encode("utf-8")
            add(SHARED / "vendor" / "inline.py", base / "vendor" / "inline.py")
            for lib in libs.values():
                for f in _files(SHARED / "vendor" / lib["dir"]):
                    add(f, base / "vendor" / lib["dir"] / f.relative_to(SHARED / "vendor" / lib["dir"]))
    return out


def sync() -> None:
    """Make every skill's shared copies byte-identical to shared/."""
    for dst, data in expected().items():
        if not dst.exists() or dst.read_bytes() != data:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)


def _stage_source_in_sync() -> None:
    """The stage page checker is the game checker (one file)."""
    game = ROOT / "skills" / "teacher-game" / "scripts" / "check_game.py"
    target = STAGE / "check_page.py"
    if not target.exists() or target.read_bytes() != game.read_bytes():
        target.write_bytes(game.read_bytes())


def check() -> int:
    """Report every drifted copy; return 1 if any."""
    problems: list[str] = []
    game = (ROOT / "skills" / "teacher-game" / "scripts" / "check_game.py").read_bytes()
    if (STAGE / "check_page.py").read_bytes() != game:
        problems.append("shared/stage/check_page.py != skills/teacher-game/scripts/check_game.py")
    for dst, data in expected().items():
        rel = dst.relative_to(ROOT).as_posix()
        if not dst.exists():
            problems.append(f"missing copy: {rel}")
        elif dst.read_bytes() != data:
            problems.append(f"drifted copy: {rel} (edit shared/ and run tools/sync_shared.py)")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()[1:]
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()[1:]
    if claude != agents:
        problems.append("AGENTS.md and CLAUDE.md differ beyond the title line")
    for skill in sorted((ROOT / "skills").iterdir()):
        zpath = ROOT / "dist" / f"{skill.name}.zip"
        if not (skill / "SKILL.md").exists():
            continue
        if not zpath.exists():
            problems.append(f"missing dist/{zpath.name}")
            continue
        with zipfile.ZipFile(zpath) as z:
            names = {n for n in z.namelist() if not n.endswith("/")}
            want = {f.relative_to(skill.parent).as_posix(): f for f in _files(skill)}
            if names != set(want):
                problems.append(f"dist/{zpath.name} file list is stale ({len(names ^ set(want))} differ)")
                continue
            for n, f in want.items():
                if z.read(n) != f.read_bytes():
                    problems.append(f"dist/{zpath.name} stale: {n}")
                    break
    if problems:
        print("DRIFT:\n - " + "\n - ".join(problems))
        return 1
    print(f"sync check OK ({len(expected())} copies, AGENTS.md/CLAUDE.md, dist zips)")
    return 0


def package() -> None:
    """Zip each skill folder for upload (claude.ai Settings > Skills)."""
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for skill in sorted((ROOT / "skills").iterdir()):
        if not (skill / "SKILL.md").exists():
            continue
        out = dist / f"{skill.name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in _files(skill):
                z.write(f, f.relative_to(skill.parent))
        print(f"{out.name}: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        sys.exit(check())
    _stage_source_in_sync()
    sync()
    package()
