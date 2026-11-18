#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Side-by-side picture: a legacy skin (left) vs a spec-built game (right): title row + play row.

Usage: python3 tools/compare_legacy.py legacy.html spec_built.html out.png
(maintainers' tool; both files are played silently in headless Chrome and shot at 1920x1080)
"""
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

SILENT = ("(function(){try{window.speechSynthesis.speak=function(){};}catch(e){}try{var oc=AudioNode.prototype.connect;"
          "AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}catch(e){}})()")


def shots(p, path: Path) -> list[Image.Image]:
    b = None
    for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            b = p.chromium.launch(args=["--mute-audio"], **kw)
            break
        except Exception:
            continue
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.add_init_script(SILENT)
    pg.goto(path.resolve().as_uri())
    pg.wait_for_timeout(900)
    pg.evaluate("advanceTime(1500)")
    pg.wait_for_timeout(500)
    out = [Image.open(io.BytesIO(pg.screenshot())).convert("RGB")]
    pg.click("#t-start")
    pg.wait_for_timeout(3700)
    pg.evaluate("advanceTime(1500)")
    pg.wait_for_timeout(800)
    pg.wait_for_timeout(400)
    out.append(Image.open(io.BytesIO(pg.screenshot())).convert("RGB"))
    b.close()
    return out


def main() -> int:
    legacy, spec, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    with sync_playwright() as p:
        a, b = shots(p, legacy), shots(p, spec)
    tw, th = 640, 360
    sheet = Image.new("RGB", (tw * 2 + 24, (th + 28) * 2 + 24), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for col, (name, imgs) in enumerate((("LEGACY: " + legacy.stem, a), ("TOOL-BUILT: " + spec.stem, b))):
        for row, im in enumerate(imgs):
            x, y = 8 + col * (tw + 8), 8 + row * (th + 28 + 8)
            d.text((x + 4, y + 6), name + ("  (title)" if row == 0 else "  (play)"), fill=(235, 235, 240))
            sheet.paste(im.resize((tw, th)), (x, y + 28))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.quantize(colors=160, dither=Image.Dither.NONE).save(out, optimize=True)
    print(out, out.stat().st_size // 1024, "KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
