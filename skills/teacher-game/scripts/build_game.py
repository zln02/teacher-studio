# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
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
import sys
from pathlib import Path
import html as _html


def _js_json(obj, **kw) -> str:
    """JSON for an inline <script>: < > & and U+2028/2029 become unicode escapes, so </script> or <!-- in text can never end the tag."""
    s = json.dumps(obj, ensure_ascii=False, **kw)
    for ch, esc in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), (chr(0x2028), "\\u2028"), (chr(0x2029), "\\u2029")):
        s = s.replace(ch, esc)
    return s

SKILL = Path(__file__).resolve().parent.parent
ENGINE = SKILL / "assets" / "engine.html"
VOICE = SKILL / "shared" / "voice" / "voice.js"
sys.path.insert(0, str(SKILL / "shared" / "tools"))
sys.path.insert(0, str(SKILL / "shared" / "fonts"))
import embed as embed_mod  # noqa: E402  (shared/fonts/embed.py)
from stamp import stamp  # noqa: E402  (shared/tools/stamp.py: invisible author mark)
DATA_RE = re.compile(r"window\.GAME = \{.*?\n\};", re.S)
LOGIC_RE = re.compile(r"(/\* ===================== GAME LOGIC.*?\*/\n).*?(\n</script>\n<script>NG\.boot)", re.S)


def _polish() -> str:
    """shared/design/system.py polish_css("game"); empty when the design folder is missing (the page still builds)."""
    for d in (SKILL / "shared" / "design", SKILL.parent.parent / "shared" / "design"):
        if (d / "system.py").exists():
            if str(d) not in sys.path:
                sys.path.insert(0, str(d))
            try:
                import system as _ds
                return _ds.polish_css("game")
            except Exception:  # noqa: BLE001
                return ""
    return ""


def build(data_path: Path, logic_path: Path, out_path: Path, css_path: Path | None = None, online: bool = False) -> int:
    """Inject data, logic, optional CSS and asset packs into the engine; return output size in bytes.
    online=False (default): the engine's Google Fonts links are removed, so the page makes no outside request (opt in with spec "online": true)."""
    engine = ENGINE.read_text(encoding="utf-8")
    if not DATA_RE.search(engine) or not LOGIC_RE.search(engine):
        raise SystemExit("engine markers not found - engine.html was modified")
    data = json.loads(data_path.read_text(encoding="utf-8"))
    packs = data.pop("packs", [])
    game_js = "window.GAME = " + _js_json(data, indent=2) + ";"
    logic = logic_path.read_text(encoding="utf-8").rstrip()
    html = DATA_RE.sub(lambda _: game_js, engine, count=1)
    html = LOGIC_RE.sub(lambda m: m.group(1) + logic + m.group(2), html, count=1)
    css = css_path.read_text(encoding="utf-8").rstrip() if css_path else ""
    if "design system polish" not in css:  # the shared finishing layer (shared/design/system.py) goes right after the engine styles, before the
        css = _polish() + "\n" + css       # missile / theme / custom CSS: the fire path and the spec path get the same matte, typeset base
    if css.strip():
        html = html.replace("</style>", css.rstrip() + "\n</style>", 1)
    if packs:
        pack_js = "".join(
            "<script>\n" + (SKILL / "assets" / "packs" / f"{name}.js").read_text(encoding="utf-8") + "</script>\n"
            for name in packs
        )
        html = html.replace("<!--ASSET_PACKS-->", pack_js, 1)
    if "<!--TS:VOICE-->" in html and VOICE.exists():
        voice_js = "<script>/* TS:VOICE */\n" + VOICE.read_text(encoding="utf-8") + "</script>"
        html = html.replace("<!--TS:VOICE-->", voice_js, 1)
    if not online:
        html = embed_mod.go_offline(html)
    html = stamp(html)
    title = data.get("title")
    if title:
        html = re.sub(r"<title>.*?</title>", lambda _: f"<title>{_html.escape(str(title))}</title>", html, count=1)
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
