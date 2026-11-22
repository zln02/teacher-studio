#!/usr/bin/env python3
"""Build docs/training/ai-cheating/ai-cheating-deck.html: 「AI 커닝, 미리 막기」 (skin E · 9 slides · ~11 min, optional segment).

One command (Windows):  set PYTHONUTF8=1 && py docs/training/ai-cheating/deck-src/build.py
Uses the main deck engine (docs/training/deck-v3-src/build.py --skin e: deck.css · skin-e.css · motion-e.js · fonts)
with this folder's slides-e.html (its own ac- styles and CSS motion are inside that file, so the main deck files stay untouched).
Before handing over, this script fills the illustration slots: __AC_w1__ … (illust/w1.png … → small JPEG data URI)
and __MARK_w1__ … (pen marks drawn over each picture, 400x300 box).
The old v2-look slides are kept as slides-old.html (build-old: --old).
Scope rule (README.md): no device or product names, no hiding methods, no connection steps, no evasion tips, no how-to.
Illustrations: Codex CLI image generation (codex exec, style ref deck-v3-src/illust-e/spot-wall.jpg); prompts in illust/prompts.txt.
"""
from __future__ import annotations

import base64
import io
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = HERE.parents[1] / "deck-v3-src" / "build.py"
OUT = HERE.parent / "ai-cheating-deck.html"
ILL = HERE / "illust"


def loop(cx, cy, rx, ry, seed):   # 손으로 그린 동그라미 (한 바퀴 조금 넘게)
    r = random.Random(seed)
    pts = []
    n = 22
    for i in range(n + 1):
        a = -2.2 + (math.pi * 2 + 0.5) * i / n
        g = 1 + 0.06 * i / n + r.uniform(-0.03, 0.03)
        pts.append((cx + math.cos(a) * rx * g, cy + math.sin(a) * ry * g))
    return "M" + " L".join("%.1f %.1f" % p for p in pts)


def arrow(x0, y0, x1, y1, bend=-40):
    mx, my = (x0 + x1) / 2 + bend, (y0 + y1) / 2
    ang = math.atan2(y1 - my, x1 - mx)
    h = lambda a: "%.1f %.1f" % (x1 + math.cos(a) * 22, y1 + math.sin(a) * 22)
    return "M%.1f %.1f Q%.1f %.1f %.1f %.1f M%s L%.1f %.1f L%s" % (x0, y0, mx, my, x1, y1, h(ang + 2.6), x1, y1, h(ang - 2.6))


# 펜 표시 (그림 좌표 400x300): 흔적이 보이는 자리만 짚어요
MARKS = {
    "w1": [("e-blue", loop(200, 152, 78, 58, 1))],
    "w2": [("e-red", loop(240, 54, 44, 40, 2))],
    "w3": [("e-red", loop(244, 158, 30, 24, 3)), ("e-red", arrow(336, 60, 268, 140))],
    "w4": [("e-blue", loop(186, 153, 62, 32, 4)), ("e-red", arrow(330, 60, 256, 116, 30))],
    "w5": [("e-red", loop(80, 176, 24, 20, 5)), ("e-red", loop(207, 176, 24, 20, 6)), ("e-red", loop(333, 176, 24, 20, 7))],
}


def jpeg_uri(p: Path) -> str:
    from PIL import Image
    im = Image.open(p).convert("RGB")
    im.thumbnail((640, 480))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=80, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def fill(slides: str) -> str:
    for k, marks in MARKS.items():
        src = next((p for p in (ILL / (k + ".png"), ILL / (k + ".jpg")) if p.exists()), None)
        if src is None:
            raise SystemExit(f"missing illustration {k} (illust/{k}.png) - see illust/prompts.txt")
        slides = slides.replace("__AC_%s__" % k, jpeg_uri(src))
        paths = "".join('<path class="ac-pn2 %s" pathLength="1" d="%s"/>' % (c, d) for c, d in marks)
        slides = slides.replace("__MARK_%s__" % k, paths)
    return slides


if __name__ == "__main__":
    old = "--old" in sys.argv
    rest = [x for x in sys.argv[1:] if x != "--old"]
    if old:
        cmd = ["--slides", str(HERE / "slides-old.html"), "--out", str(HERE.parent / "ai-cheating-deck-old.html"),
               "--title", "AI 커닝, 이번 사건은 어떻게 이루어졌나", "--foot", "AI 커닝 이야기 · 박진영", "--agenda", "-"]
        raise SystemExit(subprocess.call([sys.executable, str(MAIN)] + cmd + rest))
    tmp = HERE / ".slides-e.filled.html"
    tmp.write_text(fill((HERE / "slides-e.html").read_text(encoding="utf-8")), encoding="utf-8")
    try:
        cmd = ["--skin", "e", "--slides", str(tmp), "--out", str(OUT),
               "--title", "AI 커닝, 미리 막기", "--foot", "AI 커닝, 미리 막기 · 박진영", "--agenda", "-"]
        code = subprocess.call([sys.executable, str(MAIN)] + cmd + rest)
    finally:
        tmp.unlink()
    raise SystemExit(code)
