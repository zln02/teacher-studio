#!/usr/bin/env python3
"""Headless check + contact sheet + motion GIF for deck-v2.html (Playwright, system Chrome, --mute-audio).

Usage: set PYTHONUTF8=1 && py docs/training/deck-v2-src/shoot.py [--shots DIR] [--gif] [--nogl] [--reduced]
Checks: no console errors, zero external requests, every slide renders, 3D canvases are not blank.
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
DECK = HERE.parent / "deck-v2.html"
SHEET = HERE.parent / "deck-v2-sheet.png"
GIF = HERE.parent / "deck-v2-motion.gif"
ARGS = ["--mute-audio", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


def launch(p):
    for ch in ("chrome", "msedge", None):
        try:
            return p.chromium.launch(channel=ch, args=ARGS) if ch else p.chromium.launch(args=ARGS)
        except Exception:  # noqa: BLE001
            continue
    raise SystemExit("no Chromium found")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default="")
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--nogl", action="store_true")
    ap.add_argument("--reduced", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    q = []
    if a.nogl:
        q.append("nogl=1")
    if a.reduced:
        q.append("reduced=1")
    url = DECK.as_uri() + ("?" + "&".join(q) if q else "")
    errors, external = [], []
    fails = 0
    with sync_playwright() as p:
        b = launch(p)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1,
                            reduced_motion="reduce" if a.reduced else "no-preference")
        pg = ctx.new_page()
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("request", lambda r: external.append(r.url) if not r.url.startswith(("file:", "data:", "blob:", "about:")) else None)
        pg.goto(url)
        pg.wait_for_function("window.__deck && window.__deck.state().slide === 0", timeout=20000)
        n = pg.evaluate("window.__deck.count")
        st = pg.evaluate("window.__deck.state()")
        print("slides:", n, "state:", st)
        thumbs = []
        shots = Path(a.shots) if a.shots else None
        if shots:
            shots.mkdir(parents=True, exist_ok=True)
        only = [int(x) for x in a.only.split(",") if x] if a.only else list(range(1, n + 1))
        for i in range(n):
            if i + 1 not in only:
                continue
            if i and i % 6 == 0:  # fresh page now and then: software WebGL leaks memory over long runs
                pg.goto(url)
                pg.wait_for_function("window.__deck && window.__deck.state().slide === 0", timeout=20000)
            steps = pg.evaluate(f"window.__deck.steps({i})")
            pg.evaluate(f"window.__deck.go({i}, 0)")
            for s in range(1, steps + 1):
                pg.evaluate(f"window.__deck.go({i}, {s})")
                pg.wait_for_timeout(120 if s < steps else 0)
            pg.wait_for_timeout(1500 if not a.reduced else 400)
            pg.evaluate("window.__deck.settle()")
            pg.wait_for_timeout(300)
            png = pg.screenshot(timeout=120000)
            img = Image.open(io.BytesIO(png)).convert("RGB")
            info = pg.evaluate("window.__deck.state()")
            note = ""
            if info["active"]:
                # 3D canvas not blank: variance inside the canvas area must be clearly above a flat background
                box = pg.evaluate("(function(){var c=document.querySelector('.slide.on .gl canvas'); if(!c) return null; var r=c.getBoundingClientRect(); return [r.left,r.top,r.right,r.bottom];})()")
                if not box:
                    note = "FAIL no canvas"; fails += 1
                else:
                    gl_ok = pg.evaluate("(function(){var c=document.querySelector('.slide.on .gl canvas');var g=c.getContext('webgl');return !!g && !g.isContextLost();})()")
                    crop = img.crop((int(box[0]) + 900, int(box[1]) + 150, int(box[2]) - 60, int(box[3]) - 200))
                    sd = sum(ImageStat.Stat(crop).stddev) / 3
                    note = f"3D {info['active']} gl={gl_ok} stddev={sd:.1f}"
                    if sd < 6:
                        note += " FAIL blank?"; fails += 1
            print(f"{i + 1:02d} steps={steps} {note}")
            if shots:
                img.save(shots / f"s{i + 1:02d}.png")
            thumbs.append(img.resize((480, 270), Image.LANCZOS))
        if not a.only:
            cols = 5
            rows = (len(thumbs) + cols - 1) // cols
            pad = 16
            sheet = Image.new("RGB", (cols * 480 + (cols + 1) * pad, rows * 270 + (rows + 1) * pad), (24, 19, 15))
            for k, t in enumerate(thumbs):
                sheet.paste(t, (pad + (k % cols) * (480 + pad), pad + (k // cols) * (270 + pad)))
            out = SHEET if not (a.nogl or a.reduced) else HERE / ("sheet-nogl.png" if a.nogl else "sheet-reduced.png")
            if a.nogl or a.reduced:
                out = Path(a.shots or HERE) / out.name
            sheet.save(out, optimize=True)
            print("sheet:", out)
        if a.gif:
            frames = []
            ctx2 = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
            g = ctx2.new_page()
            g.goto(DECK.as_uri())
            g.wait_for_function("window.__deck && window.__deck.state().slide === 0", timeout=20000)

            def grab(ms, every=110):
                t = 0
                while t < ms:
                    im = Image.open(io.BytesIO(g.screenshot(type="jpeg", quality=80))).convert("RGB").resize((800, 450), Image.LANCZOS)
                    frames.append(im)
                    g.wait_for_timeout(every)
                    t += every + 60
            # demo pipeline: card travels 기획 → 콘티 → 배포
            g.evaluate("window.__deck.go(8, 0)"); g.wait_for_timeout(900)
            grab(700)
            for s in (1, 2, 3, 4, 5, 6):
                g.evaluate(f"window.__deck.go(8, {s})")
                grab(800)
            # cheating pipeline: signals, focus one stage, then the wall
            g.evaluate("window.__deck.go(17, 0)"); g.wait_for_timeout(700)
            grab(1100)
            g.evaluate("window.__deck.go(17, 2)"); grab(1100)
            g.evaluate("window.__deck.go(17, 7)"); grab(1500)
            pal = [f.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
            pal[0].save(GIF, save_all=True, append_images=pal[1:], duration=170, loop=0, optimize=True)
            print("gif:", GIF, f"{GIF.stat().st_size / 1e6:.2f} MB", len(frames), "frames")
        b.close()
    print("console errors:", errors or "none")
    print("external requests:", external or "none")
    if errors or external:
        fails += 1
    print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
