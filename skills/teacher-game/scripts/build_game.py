"""Assemble a finished game from the engine without re-typing it.

Usage:
    python3 build_game.py --data game.json --logic logic.js [--css extra.css] --out game.html

- game.json : the window.GAME object (title, subtitle, theme, teams, timer, music, items, ...).
              Optional "packs": ["kenney-platformer-core"] inlines assets/packs/<name>.js.
- logic.js  : must define window.GAME_LOGIC = {...}; (a kit file from assets/kits/ works as-is).
- extra.css : optional styles appended after the engine styles (world-specific look).
The engine block is copied byte-for-byte, so never Read or retype engine.html.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ENGINE = SKILL / "assets" / "engine.html"
DATA_RE = re.compile(r"window\.GAME = \{.*?\n\};", re.S)
LOGIC_RE = re.compile(r"(/\* ===================== GAME LOGIC.*?\*/\n).*?(\n</script>\n<script>NG\.boot)", re.S)


def build(data_path: Path, logic_path: Path, out_path: Path, css_path: Path | None = None) -> int:
    """Inject data, logic, optional CSS and asset packs into the engine; return output size in bytes."""
    engine = ENGINE.read_text(encoding="utf-8")
    if not DATA_RE.search(engine) or not LOGIC_RE.search(engine):
        raise SystemExit("engine markers not found - engine.html was modified")
    data = json.loads(data_path.read_text(encoding="utf-8"))
    packs = data.pop("packs", [])
    game_js = "window.GAME = " + json.dumps(data, ensure_ascii=False, indent=2) + ";"
    logic = logic_path.read_text(encoding="utf-8").rstrip()
    html = DATA_RE.sub(lambda _: game_js, engine, count=1)
    html = LOGIC_RE.sub(lambda m: m.group(1) + logic + m.group(2), html, count=1)
    if css_path:
        html = html.replace("</style>", css_path.read_text(encoding="utf-8").rstrip() + "\n</style>", 1)
    if packs:
        pack_js = "".join(
            "<script>\n" + (SKILL / "assets" / "packs" / f"{name}.js").read_text(encoding="utf-8") + "</script>\n"
            for name in packs
        )
        html = html.replace("<!--ASSET_PACKS-->", pack_js, 1)
    title = data.get("title")
    if title:
        html = re.sub(r"<title>.*?</title>", lambda _: f"<title>{title}</title>", html, count=1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return len(html.encode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--logic", required=True, type=Path)
    ap.add_argument("--css", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    size = build(a.data, a.logic, a.out, a.css)
    print(f"built {a.out} ({size // 1024} KB) - now run: python3 {SKILL / 'scripts' / 'check_game.py'} {a.out}")


if __name__ == "__main__":
    main()
