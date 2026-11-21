#!/usr/bin/env python3
"""Build docs/training/ai-cheating/ai-cheating-deck.html: the AI 커닝 deck on its own (old deck-v2 slides 22-37 → 1-16).

One command (Windows):  set PYTHONUTF8=1 && py docs/training/ai-cheating/deck-src/build.py
Uses the same engine as the main deck (docs/training/deck-v3-src/build.py: deck.css · deck.js · 3D scenes · fonts),
with this folder's slides.html. The look is still the v2 look; the motion-graphics pass and the 「원리 → 흔적」 content come later.
Scope rule (README.md): no device or product names, no hiding methods, no connection steps, no evasion tips.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = HERE.parents[1] / "deck-v3-src" / "build.py"
OUT = HERE.parent / "ai-cheating-deck.html"

if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, str(MAIN), "--slides", str(HERE / "slides.html"), "--out", str(OUT),
                                      "--title", "AI 커닝, 이번 사건은 어떻게 이루어졌나", "--foot", "AI 커닝 이야기 · 박진영", "--agenda", "-"]
                                     + sys.argv[1:]))
