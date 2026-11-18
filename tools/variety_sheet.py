#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Same request, several seeds -> one picture (title + question of each build) to show the compositions really differ.

Usage: python3 tools/variety_sheet.py spec.json out.png seed1 seed2 seed3 [--check]
Builds spec.json once per seed (scripts/build.py --seed N, check skipped unless --check), plays each silently in headless Chrome.
"""
import io
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "skills" / "teacher-game" / "scripts" / "build.py"
SILENT = ("(function(){try{window.speechSynthesis.speak=function(){};}catch(e){}try{var oc=AudioNode.prototype.connect;"
          "AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}catch(e){}})()")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    spec, out, seeds = Path(args[0]), Path(args[1]), [int(x) for x in args[2:]]
    check = "--check" in sys.argv
    tmp = Path(tempfile.mkdtemp(prefix="variety-"))
    pages = []
    for sd in seeds:
        f = tmp / f"seed{sd}.html"
        cmd = [sys.executable, str(BUILD), "--spec", str(spec), "--out", str(f), "--no-fonts", "--seed", str(sd)] + ([] if check else ["--no-check"])
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(f"seed {sd}:", (r.stdout.strip().splitlines() or ["?"])[-1][:120])
        pages.append(f)
    rows = []
    with sync_playwright() as p:
        b = None
        for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
            try:
                b = p.chromium.launch(args=["--mute-audio"], **kw)
                break
            except Exception:
                continue
        for f in pages:
            pg = b.new_page(viewport={"width": 1920, "height": 1080})
            pg.add_init_script(SILENT)
            pg.goto(f.resolve().as_uri())
            pg.wait_for_timeout(900)
            pg.evaluate("advanceTime(1500)")
            pg.wait_for_timeout(600)
            t = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            pg.click("#t-start")
            pg.wait_for_timeout(3700)
            pg.evaluate("advanceTime(1500)")
            pg.wait_for_timeout(900)
            q = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            rows.append((t, q))
            pg.close()
        b.close()
    tw, th = 640, 360
    sheet = Image.new("RGB", (tw * 2 + 24, (th + 28) * len(rows) + 8 * (len(rows) + 1)), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for i, (sd, (t, q)) in enumerate(zip(seeds, rows)):
        y = 8 + i * (th + 36)
        d.text((12, y + 6), f"design.seed={sd}  title", fill=(235, 235, 240))
        d.text((tw + 20, y + 6), f"design.seed={sd}  question", fill=(235, 235, 240))
        sheet.paste(t.resize((tw, th)), (8, y + 28))
        sheet.paste(q.resize((tw, th)), (tw + 16, y + 28))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.quantize(colors=160, dither=Image.Dither.NONE).save(out, optimize=True)
    print(out, out.stat().st_size // 1024, "KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
