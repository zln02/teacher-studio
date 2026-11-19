# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Copy shared runtime files into every skill that uses them, then zip each skill.

shared/ is the source of truth. Each skill must stay self-contained when zipped, so its own copy lives in
skills/<skill>/shared/ (design, fonts, tools, vendor, voice, juice, shell) and, for the stage skills, assets/ + scripts/.

Usage:
    python3 tools/sync_shared.py            # copy shared -> skills, then rebuild dist/*.zip
    python3 tools/sync_shared.py --check    # exit 1 if any copy differs from shared/ (also AGENTS.md vs CLAUDE.md, dist zips)
"""
from __future__ import annotations

import json
import re
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
    "teacher-game": {"design": True, "fonts": True, "tools": True, "voice": True, "assets": True, "juice": True, "vendor": ["confetti", "motion", "lucide", "katex", "phaser"]},
    "teacher-slides": {"design": True, "fonts": True, "tools": True, "vendor": ["anime", "motion", "chartjs", "katex", "lucide", "confetti", "qrcodegen"]},
    "teacher-motion": {"design": True, "fonts": True, "tools": True, "vendor": ["anime", "motion", "lucide", "confetti"]},
    "teacher-studio": {"design": True, "fonts": True, "tools": True, "video_eyes": True, "vendor": []},
    "teacher-class-tools": {"design": True, "fonts": True, "tools": True, "juice": True, "vendor": []},
    "teacher-data": {"design": True, "fonts": True, "tools": True, "vendor": ["chartjs"]},
    "teacher-docs": {"design": True, "fonts": True, "tools": True, "placeholders": True, "vendor": []},
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
        for f in ("build_stage.py", "render_mp4.py", "check_page.py", "clipcheck.py"):
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
        if cfg.get("placeholders"):  # blank detector shared with teacher-slides (scripts/placeholders.py must equal shared/tools/placeholders.py)
            add(SHARED / "tools" / "placeholders.py", base / "tools" / "placeholders.py")
        if cfg.get("video_eyes"):  # local-only video frames helper (diagnose.py / ref_analyze.py)
            add(SHARED / "tools" / "video_eyes.py", base / "tools" / "video_eyes.py")
        if cfg.get("juice"):  # Game Wow kit: sound presets, particles, motion effects, lint
            for f in _files(SHARED / "juice"):
                add(f, base / "juice" / f.relative_to(SHARED / "juice"))
        if cfg.get("assets"):  # design asset arsenal (characters, icons, colors, sfx) - see shared/assets/manifest.json
            for f in _files(SHARED / "assets"):
                if f.name != "verify_assets.py":
                    add(f, base / "assets" / f.relative_to(SHARED / "assets"))
        if cfg.get("shell", True):  # shell kit (껍데기 키트): device frames, patterns, icons for previews - every skill
            for f in _files(SHARED / "shell"):
                add(f, base / "shell" / f.relative_to(SHARED / "shell"))
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
    clip = ROOT / "skills" / "teacher-game" / "scripts" / "clipcheck.py"  # imported by the checker: travels with it
    ct = STAGE / "clipcheck.py"
    if not ct.exists() or ct.read_bytes() != clip.read_bytes():
        ct.write_bytes(clip.read_bytes())


DOC_FILES = ("README.md", "README.en.md", "INSTALL.md", "MAP.md")
WORD_NUM = {"다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8}
COUNT_PATTERNS = (  # a number next to a skills / zip / folders noun
    re.compile(r"(?:스킬|zip|ZIP|폴더)\s*(\d+)\s*개"), re.compile(r"(\d+)\s*개\s*(?:스킬|zip|ZIP)"),
    re.compile(r"(?:all|the)\s+(\d+)\s+(?:teacher-\S+\s+)?skills", re.I), re.compile(r"(\d+) (?:skills|zips)", re.I),
)


def skill_count() -> int:
    return sum(1 for s in (ROOT / "skills").iterdir() if (s / "SKILL.md").exists())


def doc_count_problems() -> list[str]:
    """Docs must say as many skills/zips as skills/ has folders (INSTALL.md once said 5 while 7 existed)."""
    want = skill_count()
    files = [ROOT / f for f in DOC_FILES] + sorted((ROOT / "docs" / "training").glob("*.md"))
    out = []
    for f in files:
        if not f.exists() or f.name == "ai-cheating-research.md":
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            found = [int(m.group(1)) for pat in COUNT_PATTERNS for m in pat.finditer(line)]
            if re.search(r"스킬|zip|묶음|teacher-", line):
                found += [WORD_NUM[m.group(1)] for m in re.finditer(r"(다섯|여섯|일곱|여덟)\s*개(?:가 한 묶음|의 스킬| 스킬)", line)]
            for v in found:
                if v >= 5 and v != want:  # small numbers (3 skills, 1 skill) are other things
                    out.append(f"{f.relative_to(ROOT).as_posix()}:{n} says {v} skills/zips, skills/ has {want}")
    return out


def skill_meta_text_problems(rel: str, text: str, folder: str) -> list[str]:
    """Problems of one SKILL.md text: name = folder, description quoted if needed, >= 60 chars, says what it is for and when."""
    out = []
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return [f"{rel}: no frontmatter"]
    fm = m.group(1)
    name = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
    if not name or name.group(1) != folder:
        out.append(f"{rel}: name must be '{folder}'")
    dm = re.search(r"^description:[ 	]*(.*)$", fm, re.M)
    desc = dm.group(1).strip() if dm else ""
    quoted = len(desc) > 1 and desc[0] in "\"'" and desc[-1] == desc[0]
    if not quoted and (": " in desc or " #" in desc):
        out.append(f"{rel}: description has ': ' or ' #' but is not quoted (invalid YAML: the skill list shows the heading instead) -> wrap it in double quotes")
    body = desc[1:-1] if quoted else desc
    try:
        import yaml  # optional: when installed, the real parser must agree
        data = yaml.safe_load(fm)
        if not isinstance(data, dict) or not isinstance(data.get("description"), str):
            out.append(f"{rel}: frontmatter does not parse as YAML with a text description")
        else:
            body = data["description"]
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        out.append(f"{rel}: frontmatter is invalid YAML ({str(exc).splitlines()[0][:60]})")
    if len(body) < 60:
        out.append(f"{rel}: description is {len(body)} chars (< 60)")
    elif not re.search(r"\b(for|when|use|start here)\b|쓸 때|할 때", body, re.I):
        out.append(f"{rel}: description should say who/when it is for (e.g. 'for teachers and anyone', 'use when ...')")
    return out


def skill_meta_problems() -> list[str]:
    """Every SKILL.md must pass skill_meta_text_problems (teacher-data once showed "Teacher Studio - Data Analysis Weapon" because of an unquoted ': ')."""
    out = []
    for skill in sorted((ROOT / "skills").iterdir()):
        f = skill / "SKILL.md"
        if f.exists():
            out += skill_meta_text_problems(f.relative_to(ROOT).as_posix(), f.read_text(encoding="utf-8"), skill.name)
    return out


def check() -> int:
    """Report every drifted copy; return 1 if any."""
    problems: list[str] = []
    game = (ROOT / "skills" / "teacher-game" / "scripts" / "check_game.py").read_bytes()
    if (STAGE / "check_page.py").read_bytes() != game:
        problems.append("shared/stage/check_page.py != skills/teacher-game/scripts/check_game.py")
    if (STAGE / "clipcheck.py").read_bytes() != (ROOT / "skills" / "teacher-game" / "scripts" / "clipcheck.py").read_bytes():
        problems.append("shared/stage/clipcheck.py != skills/teacher-game/scripts/clipcheck.py")
    if (SHARED / "tools" / "placeholders.py").read_bytes() != (ROOT / "skills" / "teacher-slides" / "scripts" / "placeholders.py").read_bytes():
        problems.append("shared/tools/placeholders.py != skills/teacher-slides/scripts/placeholders.py (one blank detector for slides and docs)")
    for dst, data in expected().items():
        rel = dst.relative_to(ROOT).as_posix()
        if not dst.exists():
            problems.append(f"missing copy: {rel}")
        elif dst.read_bytes() != data:
            problems.append(f"drifted copy: {rel} (edit shared/ and run tools/sync_shared.py)")
    problems += doc_count_problems()
    problems += skill_meta_problems()
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
