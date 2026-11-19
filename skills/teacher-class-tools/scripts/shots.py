#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Contact sheet of a built classroom tool (start / in use / extra state / portrait) for design review.

Usage: python3 shots.py tool.html out.png
Needs Playwright (system Chrome is used first). Audio is muted. Nothing leaves the computer.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding=None if _s.isatty() else "utf-8", errors="replace")

SILENT_JS = ("(function(){try{if(window.AudioNode&&window.AudioDestinationNode){var oc=AudioNode.prototype.connect;"
             "AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}}catch(e){}})()")

OPEN_EDITOR = "(function(){var b=document.querySelector('#tb .btn');b.click();})()"
STEPS = {
    "timer": ["TOOL_API.step();advanceTime(%(warn)d)", "advanceTime(6000)"],
    "picker": ["TOOL_API.instant=true;TOOL_API.step();TOOL_API.step();TOOL_API.step()", OPEN_EDITOR],
    "teams": ["TOOL_API.step()", OPEN_EDITOR],
    "bracket": ["TOOL_API.instant=true;TOOL_API.step();TOOL_API.step();TOOL_API.step()", "while(TOOL_API.step()){}"],
    "scoreboard": ["TOOL_API.instant=true;TOOL_API.step();TOOL_API.step();TOOL_API.step()", OPEN_EDITOR],
}
LABELS = {"timer": ["시작 전", "끝나기 5초 전", "시간 끝", "세로 화면"], "picker": ["시작 전", "뽑은 뒤", "목록 바꾸기", "세로 화면"],
          "teams": ["시작 전", "나눈 뒤", "명단 바꾸기", "세로 화면"], "bracket": ["시작 전", "진행 중", "우승", "세로 화면"],
          "scoreboard": ["시작 전", "점수 올린 뒤", "모둠 이름 바꾸기", "세로 화면"]}


def main(src: Path, out: Path) -> int:
    from PIL import Image, ImageDraw, ImageFont
    from playwright.sync_api import sync_playwright
    html = src.read_text(encoding="utf-8")
    T = json.loads(re.search(r"window\.TOOL = (\{.*?\});</script>", html, re.S).group(1).replace("<\\/", "</"))
    tool, data = T["tool"], T["data"]
    warn = int(max(0, data.get("minutes", 5) * 60 - 5) * 1000) if tool == "timer" else 0
    shots: list[Path] = []
    td = Path(tempfile.mkdtemp())
    with sync_playwright() as p:
        b = None
        for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
            try:
                b = p.chromium.launch(args=["--mute-audio"], **kw)
                break
            except Exception:
                continue
        if b is None:
            print("FAIL no headless browser")
            return 1

        def snap(pg, name):
            f = td / name
            pg.screenshot(path=str(f))
            shots.append(f)

        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.add_init_script(SILENT_JS)
        pg.goto(src.resolve().as_uri())
        pg.wait_for_timeout(700)
        snap(pg, "0.png")
        for k, js in enumerate(STEPS[tool]):
            pg.evaluate(js % {"warn": warn} if "%(warn)d" in js else js)
            pg.wait_for_timeout(900)
            snap(pg, f"{k + 1}.png")
        pg.close()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.add_init_script(SILENT_JS)
        pg.goto(src.resolve().as_uri())
        pg.wait_for_timeout(600)
        pg.evaluate("TOOL_API.instant=true")
        pg.evaluate(STEPS[tool][0] % {"warn": warn} if "%(warn)d" in STEPS[tool][0] else STEPS[tool][0])
        if tool in ("timer", "bracket"):
            pg.evaluate(STEPS[tool][1])
        pg.wait_for_timeout(900)
        snap(pg, "p.png")
        b.close()
    W, H, pad, lab = 960, 540, 16, 34
    imgs = [Image.open(f).convert("RGB") for f in shots]
    land = [i.resize((W, H)) for i in imgs[:3]]
    port = imgs[3].resize((304, 540))
    sheet = Image.new("RGB", (W * 2 + pad * 3, (H + lab) * 2 + pad * 3), (22, 22, 26))
    d = ImageDraw.Draw(sheet)
    font = None
    for f in (r"C:\Windows\Fonts\malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"):
        if Path(f).exists():
            font = ImageFont.truetype(f, 22)
            break
    if font is None:
        font = ImageFont.load_default()
    pos = [(pad, pad), (W + 2 * pad, pad), (pad, H + lab + 2 * pad), (W + 2 * pad, H + lab + 2 * pad)]
    for k, (x, y) in enumerate(pos):
        d.text((x, y + 4), f"{T['title']} · {LABELS[tool][k]}", fill=(255, 224, 120), font=font)
        sheet.paste(land[k] if k < 3 else port, (x, y + lab))
    sheet.save(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
