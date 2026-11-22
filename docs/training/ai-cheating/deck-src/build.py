#!/usr/bin/env python3
"""Build docs/training/ai-cheating/ai-cheating-deck.html: 「AI 커닝, 미리 막기」 (skin E · 8 slides · ~10 min, optional segment).

One command (Windows):  set PYTHONUTF8=1 && py docs/training/ai-cheating/deck-src/build.py
Uses the main deck engine (docs/training/deck-v3-src/build.py --skin e: deck.css · skin-e.css · motion-e.js · fonts)
with this folder's slides-e.html (its own ac- styles are inside that file, so the main deck files stay untouched).
The old v2-look slides are kept as slides-old.html (build-old: --old).
Scope rule (README.md): no device or product names, no hiding methods, no connection steps, no evasion tips, no how-to.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = HERE.parents[1] / "deck-v3-src" / "build.py"
OUT = HERE.parent / "ai-cheating-deck.html"

if __name__ == "__main__":
    old = "--old" in sys.argv
    rest = [x for x in sys.argv[1:] if x != "--old"]
    if old:
        cmd = ["--slides", str(HERE / "slides-old.html"), "--out", str(HERE.parent / "ai-cheating-deck-old.html"),
               "--title", "AI 커닝, 이번 사건은 어떻게 이루어졌나", "--foot", "AI 커닝 이야기 · 박진영", "--agenda", "-"]
    else:
        cmd = ["--skin", "e", "--slides", str(HERE / "slides-e.html"), "--out", str(OUT),
               "--title", "AI 커닝, 미리 막기", "--foot", "AI 커닝, 미리 막기 · 박진영", "--agenda", "-"]
    raise SystemExit(subprocess.call([sys.executable, str(MAIN)] + cmd + rest))
