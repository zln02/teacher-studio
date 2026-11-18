"""Fire a missile: finished game template + skin + the teacher's content -> one playable HTML.

Usage:
    python3 fire.py --missile escape-room --skin joseon --content content.json --out game.html
    python3 fire.py --list

- assets/missiles/<missile>/logic.js, style.css : the finished, tested game (never edited per request)
- assets/missiles/<missile>/skins/<skin>.json  : world look + default texts (+ sample items)
- content.json : only what changes per class: {"title", "subtitle", "items", ...any GAME key}
                 Keys here override the skin. "world" is merged one level deep.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
MISSILES = SKILL / "assets" / "missiles"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_game import build  # noqa: E402


def list_missiles() -> None:
    """Print every missile and its skins."""
    for m in sorted(p for p in MISSILES.iterdir() if p.is_dir()):
        skins = sorted(s.stem for s in (m / "skins").glob("*.json"))
        print(f"{m.name}: {', '.join(skins)}")


def merge(skin: dict, content: dict) -> dict:
    """Overlay teacher content on the skin preset; 'world' and 'themeOverride' merge one level deep."""
    out = dict(skin)
    for key, value in content.items():
        if key in ("world", "themeOverride") and isinstance(value, dict):
            out[key] = {**skin.get(key, {}), **value}
        else:
            out[key] = value
    return out


def fire(missile: str, skin: str, content_path: Path | None, out: Path) -> None:
    """Assemble, build and check one game."""
    base = MISSILES / missile
    skin_path = base / "skins" / f"{skin}.json"
    if not skin_path.exists():
        raise SystemExit(f"unknown missile/skin: {missile}/{skin} (run --list)")
    data = json.loads(skin_path.read_text(encoding="utf-8"))
    if content_path:
        data = merge(data, json.loads(content_path.read_text(encoding="utf-8")))
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(data, tmp, ensure_ascii=False)
    css = base / "style.css"
    size = build(Path(tmp.name), base / "logic.js", out, css if css.exists() else None)
    print(f"fired {missile}/{skin} -> {out} ({size // 1024} KB)")
    result = subprocess.run([sys.executable, str(SKILL / "scripts" / "check_game.py"), str(out)], capture_output=True, text=True)
    print(result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr)
    if result.returncode:
        raise SystemExit(result.stdout)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--missile")
    ap.add_argument("--skin")
    ap.add_argument("--content", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.list:
        list_missiles()
        return
    if not (a.missile and a.skin and a.out):
        ap.error("--missile, --skin and --out are required")
    fire(a.missile, a.skin, a.content, a.out)


if __name__ == "__main__":
    main()
