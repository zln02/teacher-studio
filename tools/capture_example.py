"""Capture a short GIF of a finished Teacher Studio page (for docs/gallery).

Usage:
    python tools/capture_example.py motion  page.html out.gif [--start 0] [--end 12] [--fps 10]
    python tools/capture_example.py slides  page.html out.gif --keys "Space*6"
    python tools/capture_example.py play    page.html out.gif --script quiz|drag

Needs Python Playwright + Pillow and an installed Chrome (or Edge); no download needed.
motion pages are stepped frame by frame via window.__stage.seek (exact, no lag);
slides/play are recorded in real time while keys/clicks are sent.
"""
from __future__ import annotations

import argparse
import io
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops

W, H = 640, 360


def launch(pw):
    """Use an installed Chrome/Edge so nothing has to be downloaded."""
    for ch in ("chrome", "msedge", None):
        try:
            return pw.chromium.launch(channel=ch) if ch else pw.chromium.launch()
        except Exception:
            continue
    raise SystemExit("no Chrome/Edge/Chromium found for Playwright")


def shot(tab) -> Image.Image:
    """One frame, downscaled."""
    img = Image.open(io.BytesIO(tab.screenshot(type="jpeg", quality=80))).convert("RGB")
    return img.resize((W, H), Image.LANCZOS)


def save_gif(frames: list[Image.Image], durations: list[int], out: Path, colors: int = 64) -> None:
    """Write an optimized GIF (shared adaptive palette, small frame diffs)."""
    merged: list[Image.Image] = []
    mdur: list[int] = []
    for f, d in zip(frames, durations):  # merge frames that did not change (idle moments cost nothing)
        if merged and ImageChops.difference(f, merged[-1]).convert("L").point(lambda v: 255 if v > 24 else 0).getbbox() is None:
            mdur[-1] += d
        else:
            merged.append(f)
            mdur.append(d)
    frames, durations = merged, mdur
    pal = [f.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=durations, loop=0, optimize=True, disposal=1)
    print(f"{out} {out.stat().st_size / 1024:.0f} KB, {len(frames)} frames, {sum(durations) / 1000:.1f}s")


def open_page(pw, page: Path):
    browser = launch(pw)
    tab = browser.new_page(viewport={"width": 1280, "height": 720})
    errors: list[str] = []
    tab.on("pageerror", lambda e: errors.append(str(e)))
    tab.goto(page.resolve().as_uri())
    tab.wait_for_timeout(1500)
    return browser, tab, errors


def do_motion(page: Path, out: Path, start: float, end: float, fps: int, colors: int = 64, segments: str = "") -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser, tab, errors = open_page(pw, page)
        tab.wait_for_function("window.__stage && window.__stage.ready", timeout=15000)
        tab.evaluate("window.__stage.manual()")
        frames = []
        for seg in (segments or f"{start}-{end}").split(","):  # e.g. "0-6,17-24" = highlight cuts
            a, b = (float(x) for x in seg.split("-"))
            t = a * 1000
            while t <= b * 1000:
                tab.evaluate(f"window.__stage.seek({t:.2f})")
                frames.append(shot(tab))
                t += 1000 / fps
        browser.close()
    print("page errors:", errors or 0)
    save_gif(frames, [int(1000 / fps)] * len(frames), out, colors)


def realtime(tab, frames, durs, ms: int) -> None:
    """Record frames for about ms milliseconds, with real timing."""
    end = time.time() + ms / 1000
    last = time.time()
    while time.time() < end:
        frames.append(shot(tab))
        now = time.time()
        durs.append(max(40, int((now - last) * 1000)))
        last = now


def do_slides(page: Path, out: Path, keys: str, colors: int = 64) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser, tab, errors = open_page(pw, page)
        frames: list[Image.Image] = []
        durs: list[int] = []
        realtime(tab, frames, durs, 900)
        for step in keys.split(","):  # "Space*6" or "Space*2@1400" (wait ms after each key)
            name, _, rest = step.partition("*")
            n, _, wait = rest.partition("@")
            for _ in range(int(n or 1)):
                tab.keyboard.press(name)
                realtime(tab, frames, durs, int(wait or 1300))
        browser.close()
    print("page errors:", errors or 0)
    save_gif(frames, durs, out, colors)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["motion", "slides", "play"])
    ap.add_argument("page", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float, default=12)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--width", type=int, default=640, help="gif width (16:9)")
    ap.add_argument("--colors", type=int, default=64)
    ap.add_argument("--segments", default="", help="motion highlight cuts, e.g. 0-6,17-24 (seconds)")
    ap.add_argument("--keys", default="Space*6")
    ap.add_argument("--script", default="")
    ap.add_argument("--content", type=Path)
    ap.add_argument("--rec", type=int, default=2, help="how many questions to record before the finale")
    a = ap.parse_args()
    global W, H
    W, H = a.width, a.width * 9 // 16
    import capture_example as _m  # the copy capture_play imports (this file runs as __main__)
    _m.W, _m.H = W, H
    if a.mode == "motion":
        do_motion(a.page, a.out, a.start, a.end, a.fps, a.colors, a.segments)
    elif a.mode == "slides":
        do_slides(a.page, a.out, a.keys, a.colors)
    else:
        from capture_play import do_play  # noqa: E402
        do_play(a.page, a.out, a.script, a.content, a.rec)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
