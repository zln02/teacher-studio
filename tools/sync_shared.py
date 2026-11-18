"""Copy shared runtime files (stage, scripts, teacher language) into every skill that uses them, then zip each skill.

Usage: python3 tests/sync_shared.py
"""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "shared" / "stage"
STAGE_SKILLS = ("teacher-motion", "teacher-slides")


def _copy(src: Path, dst: Path) -> None:
    """Write src bytes to dst only when they differ (works on dedup filesystems)."""
    data = src.read_bytes()
    if not dst.exists() or dst.read_bytes() != data:
        dst.write_bytes(data)


def sync() -> None:
    """Make every skill's shared copies byte-identical to shared/."""
    for name in STAGE_SKILLS:
        skill = ROOT / "skills" / name
        _copy(STAGE / "stage.html", skill / "assets" / "stage.html")
        for f in (STAGE / "vendor").iterdir():
            _copy(f, skill / "assets" / "vendor" / f.name)
        for f in ("build_stage.py", "render_mp4.py", "check_page.py"):
            _copy(STAGE / f, skill / "scripts" / f)
    _copy(ROOT / "skills" / "teacher-game" / "scripts" / "check_game.py", STAGE / "check_page.py")
    for name in STAGE_SKILLS:
        _copy(STAGE / "check_page.py", ROOT / "skills" / name / "scripts" / "check_page.py")


def package() -> None:
    """Zip each skill folder for upload (claude.ai Settings > Skills)."""
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for skill in sorted((ROOT / "skills").iterdir()):
        if not (skill / "SKILL.md").exists():
            continue
        out = dist / f"{skill.name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(skill.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    z.write(f, f.relative_to(skill.parent))
        print(f"{out.name}: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    sync()
    package()
